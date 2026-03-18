import os
import json
import base64
import requests
import tempfile
from typing import Dict, Any, List, Optional, Tuple
try:
    from google.cloud import vision
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False
    vision = None
import pytesseract
from PIL import Image
import io
import time
import logging

# Import Gemini OCR client
try:
    from gemini_ocr_client import GeminiOCRClient, get_gemini_client
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    GeminiOCRClient = None
    get_gemini_client = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiOCRProcessor:
    """
    Multi-OCR processor that integrates multiple OCR services:
    1. Google Gemini API (AI-powered with vision)
    2. Google Cloud Vision API
    3. Kolosal AI API  
    4. OCR.space API
    5. Tesseract OCR (fallback)
    """
    
    def __init__(self):
        self.gemini_enabled = bool(os.getenv('GEMINI_API_KEY')) and GEMINI_AVAILABLE
        self.google_vision_enabled = bool(os.getenv('GOOGLE_CLOUD_VISION_API_KEY')) and GOOGLE_VISION_AVAILABLE
        self.kolosal_enabled = True  # No API key required
        self.ocr_space_enabled = bool(os.getenv('OCR_SPACE_API_KEY'))
        self.tesseract_enabled = True
        
        # API endpoints
        self.kolosal_api_url = "https://api.kolosal.ai/ocr"
        self.ocr_space_api_url = os.getenv('OCR_SPACE_API_URL', 'https://api.ocr.space/parse/image')
        
        # Initialize clients
        self.gemini_client = None
        self.google_vision_client = None
        
        # Initialize Gemini client if API key is available
        if self.gemini_enabled:
            try:
                self.gemini_client = get_gemini_client()
                logger.info("Gemini API client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Gemini client: {e}")
                self.gemini_enabled = False
        
        # Initialize Google Vision client if API key is available
        if self.google_vision_enabled:
            try:
                self.google_vision_client = vision.ImageAnnotatorClient()
                logger.info("Google Cloud Vision API client initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Google Vision client: {e}")
                self.google_vision_enabled = False
    
    def process_image_with_all_apis(self, image_path: str, prefer_api: str = 'auto') -> Dict[str, Any]:
        """
        Process image using multiple OCR APIs and return the best result
        """
        results = {}
        api_order = self._get_api_order(prefer_api)
        
        for api_name in api_order:
            try:
                start_time = time.time()
                result = self._process_with_api(api_name, image_path)
                processing_time = time.time() - start_time
                
                if result:
                    result['processing_time'] = processing_time
                    result['api_name'] = api_name
                    results[api_name] = result
                    logger.info(f"{api_name} processing completed in {processing_time:.2f}s")
                
            except Exception as e:
                logger.error(f"Error processing with {api_name}: {e}")
                results[api_name] = {
                    'error': str(e),
                    'api_name': api_name,
                    'processing_time': 0
                }
        
        # Select best result based on confidence and quality
        best_result = self._select_best_result(results)
        
        return {
            'best_result': best_result,
            'all_results': results,
            'apis_used': list(results.keys()),
            'total_processing_time': sum(r.get('processing_time', 0) for r in results.values()),
            'comparison': self._compare_results(results)
        }
    
    def _get_api_order(self, prefer_api: str) -> List[str]:
        """Get the order of APIs to try based on preference and reliability"""
        available_apis = []
        
        # Prioritize working APIs
        if self.tesseract_enabled:
            available_apis.append('tesseract')  # Most reliable
        if self.ocr_space_enabled:
            available_apis.append('ocr_space')  # Working well
        if self.gemini_enabled:
            available_apis.append('gemini')  # Good but sometimes overloaded
        if self.google_vision_enabled:
            available_apis.append('google_vision')  # Good if configured
        if self.kolosal_enabled:
            available_apis.append('kolosal')  # Last resort (auth issues)
        
        if prefer_api == 'auto':
            return available_apis
        elif prefer_api in available_apis:
            # Put preferred API first, then others
            other_apis = [api for api in available_apis if api != prefer_api]
            return [prefer_api] + other_apis
        else:
            return available_apis
    
    def _process_with_api(self, api_name: str, image_path: str) -> Optional[Dict[str, Any]]:
        """Process image with specific OCR API"""
        if api_name == 'gemini':
            return self._process_with_gemini(image_path)
        elif api_name == 'google_vision':
            return self._process_with_google_vision(image_path)
        elif api_name == 'kolosal':
            return self._process_with_kolosal(image_path)
        elif api_name == 'ocr_space':
            return self._process_with_ocr_space(image_path)
        elif api_name == 'tesseract':
            return self._process_with_tesseract(image_path)
        else:
            raise ValueError(f"Unknown API: {api_name}")
    
    def _process_with_gemini(self, image_path: str) -> Dict[str, Any]:
        """Process with Google Gemini API"""
        if not self.gemini_client:
            raise Exception("Gemini client not initialized")
        
        try:
            # Use structured extraction for certificates
            result = self.gemini_client.extract_certificate_data_structured(image_path)
            
            if result.error:
                raise Exception(f"Gemini API error: {result.error}")
            
            # Extract words for compatibility (Gemini doesn't provide word-level data)
            words = []
            text_lines = result.text.split('\n')
            for line_num, line in enumerate(text_lines):
                words_in_line = line.split()
                for word in words_in_line:
                    words.append({
                        'text': word,
                        'confidence': result.confidence / 100,  # Convert to decimal
                        'bounding_box': {
                            'line': line_num,
                            'position': line.find(word) if word in line else 0
                        }
                    })
            
            return {
                'text': result.text,
                'confidence': result.confidence,
                'words': words,
                'structured_data': result.structured_data,
                'raw_response': result.__dict__
            }
            
        except Exception as e:
            raise Exception(f"Gemini processing failed: {str(e)}")
    
    def _process_with_google_vision(self, image_path: str) -> Dict[str, Any]:
        """Process with Google Cloud Vision API"""
        if not self.google_vision_client:
            raise Exception("Google Vision client not initialized")
        
        with open(image_path, 'rb') as image_file:
            content = image_file.read()
        
        image = vision.Image(content=content)
        response = self.google_vision_client.text_detection(image=image)
        
        if response.error.message:
            raise Exception(f"Google Vision API error: {response.error.message}")
        
        texts = response.text_annotations
        if not texts:
            return {
                'text': '',
                'confidence': 0,
                'words': [],
                'raw_response': {}
            }
        
        full_text = texts[0].description
        words = []
        total_confidence = 0
        word_count = 0
        
        for text in texts[1:]:  # Skip the first one (full text)
            word_info = {
                'text': text.description,
                'confidence': text.confidence if hasattr(text, 'confidence') else 0.95,
                'bounding_box': {
                    'vertices': [
                        {'x': vertex.x, 'y': vertex.y} for vertex in text.bounding_poly.vertices
                    ]
                }
            }
            words.append(word_info)
            total_confidence += word_info['confidence']
            word_count += 1
        
        avg_confidence = total_confidence / word_count if word_count > 0 else 0
        
        return {
            'text': full_text,
            'confidence': avg_confidence * 100,  # Convert to percentage
            'words': words,
            'raw_response': vision.TextAnnotation.to_dict(response.text_annotations[0]) if response.text_annotations else {}
        }
    
    def _process_with_kolosal(self, image_path: str) -> Dict[str, Any]:
        """Process with Kolosal AI OCR API"""
        with open(image_path, 'rb') as image_file:
            files = {'file': image_file}
            data = {
                'language': 'auto',
                'output_format': 'json'
            }
            
            response = requests.post(
                self.kolosal_api_url,
                files=files,
                data=data,
                timeout=30
            )
        
        if response.status_code != 200:
            raise Exception(f"Kolosal API error: {response.status_code} - {response.text}")
        
        result = response.json()
        
        # Extract text and confidence from Kolosal response
        extracted_text = result.get('text', '')
        confidence = result.get('confidence', 85)  # Default confidence if not provided
        
        # Parse words if available
        words = []
        if 'words' in result:
            for word_data in result['words']:
                words.append({
                    'text': word_data.get('text', ''),
                    'confidence': word_data.get('confidence', 0.9),
                    'bounding_box': word_data.get('bounding_box', {})
                })
        
        return {
            'text': extracted_text,
            'confidence': confidence,
            'words': words,
            'raw_response': result
        }
    
    def _process_with_ocr_space(self, image_path: str) -> Dict[str, Any]:
        """Process with OCR.space API"""
        with open(image_path, 'rb') as image_file:
            files = {'file': image_file}
            data = {
                'apikey': os.getenv('OCR_SPACE_API_KEY'),
                'language': 'eng',
                'isOverlayRequired': 'true',
                'detectOrientation': 'true',
                'scale': 'true',
                'OCREngine': 2
            }
            
            response = requests.post(
                self.ocr_space_api_url,
                files=files,
                data=data,
                timeout=30
            )
        
        if response.status_code != 200:
            raise Exception(f"OCR.space API error: {response.status_code} - {response.text}")
        
        result = response.json()
        
        if result.get('IsErroredOnProcessing', False):
            raise Exception(f"OCR.space processing error: {result.get('ErrorMessage', 'Unknown error')}")
        
        parsed_results = result.get('ParsedResults', [])
        if not parsed_results:
            return {
                'text': '',
                'confidence': 0,
                'words': [],
                'raw_response': result
            }
        
        parsed_result = parsed_results[0]
        extracted_text = parsed_result.get('ParsedText', '')
        
        # Extract words with confidence
        words = []
        text_overlay = parsed_result.get('TextOverlay', {}).get('Lines', [])
        
        for line in text_overlay:
            for word_info in line.get('Words', []):
                words.append({
                    'text': word_info.get('WordText', ''),
                    'confidence': word_info.get('Confidence', 0) / 100,  # Convert to decimal
                    'bounding_box': {
                        'left': word_info.get('Left', 0),
                        'top': word_info.get('Top', 0),
                        'width': word_info.get('Width', 0),
                        'height': word_info.get('Height', 0)
                    }
                })
        
        # Calculate average confidence
        avg_confidence = sum(w['confidence'] for w in words) / len(words) if words else 0.8
        
        return {
            'text': extracted_text,
            'confidence': avg_confidence * 100,  # Convert to percentage
            'words': words,
            'raw_response': result
        }
    
    def _process_with_tesseract(self, image_path: str) -> Dict[str, Any]:
        """Process with Tesseract OCR"""
        image = Image.open(image_path)
        
        # Get detailed data
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        
        # Extract text and confidence
        words = []
        text_parts = []
        confidences = []
        
        for i in range(len(data['text'])):
            text = data['text'][i].strip()
            if text:
                confidence = data['conf'][i]
                if confidence > 0:  # Valid confidence
                    words.append({
                        'text': text,
                        'confidence': confidence / 100,  # Convert to decimal
                        'bounding_box': {
                            'left': data['left'][i],
                            'top': data['top'][i],
                            'width': data['width'][i],
                            'height': data['height'][i]
                        }
                    })
                    text_parts.append(text)
                    confidences.append(confidence)
        
        full_text = ' '.join(text_parts)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 70
        
        return {
            'text': full_text,
            'confidence': avg_confidence,
            'words': words,
            'raw_response': data
        }
    
    def _select_best_result(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Select the best OCR result based on confidence and text quality"""
        if not results:
            return {
                'text': '',
                'confidence': 0,
                'api_name': 'none',
                'error': 'No results available'
            }
        
        # Filter out results with errors
        valid_results = {k: v for k, v in results.items() if 'error' not in v}
        
        if not valid_results:
            # Return the first error result if no valid results
            return list(results.values())[0]
        
        # Score each result based on confidence and text quality
        scored_results = []
        for api_name, result in valid_results.items():
            score = self._calculate_result_score(result)
            scored_results.append((score, api_name, result))
        
        # Sort by score (highest first) and return the best
        scored_results.sort(key=lambda x: x[0], reverse=True)
        best_score, best_api, best_result = scored_results[0]
        
        best_result['selection_score'] = best_score
        best_result['selected_as_best'] = True
        best_result['total_apis_tried'] = len(results)
        
        return best_result
    
    def _calculate_result_score(self, result: Dict[str, Any]) -> float:
        """Calculate a score for the OCR result"""
        base_score = result.get('confidence', 0)
        
        # Text quality factors
        text = result.get('text', '')
        text_length = len(text.strip())
        
        # Penalize very short or very long texts
        if text_length < 10:
            base_score *= 0.5
        elif text_length > 5000:
            base_score *= 0.8
        
        # Bonus for structured text (multiple lines, proper spacing)
        lines = text.split('\n')
        if len(lines) > 3:
            base_score *= 1.1
        
        # Bonus for words with good confidence
        words = result.get('words', [])
        if words:
            word_confidences = [w.get('confidence', 0) for w in words]
            avg_word_conf = sum(word_confidences) / len(word_confidences)
            base_score = (base_score + avg_word_conf * 100) / 2
        
        # API preference bonus
        api_name = result.get('api_name', '')
        if api_name == 'gemini':
            base_score *= 1.15  # Gemini is most advanced with AI understanding
        elif api_name == 'google_vision':
            base_score *= 1.1  # Google Vision is usually very accurate
        elif api_name == 'kolosal':
            base_score *= 1.05  # Kolosal AI is good with blurry docs
        
        return min(base_score, 100)  # Cap at 100
    
    def _compare_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Compare results from different APIs"""
        comparison = {
            'confidence_ranking': [],
            'text_length_comparison': {},
            'word_count_comparison': {},
            'processing_time_comparison': {}
        }
        
        valid_results = {k: v for k, v in results.items() if 'error' not in v}
        
        # Rank by confidence
        confidence_ranking = sorted(
            [(api, result.get('confidence', 0)) for api, result in valid_results.items()],
            key=lambda x: x[1],
            reverse=True
        )
        comparison['confidence_ranking'] = confidence_ranking
        
        # Compare text lengths
        for api, result in valid_results.items():
            text_length = len(result.get('text', '').strip())
            comparison['text_length_comparison'][api] = text_length
            
            word_count = len(result.get('words', []))
            comparison['word_count_comparison'][api] = word_count
            
            processing_time = result.get('processing_time', 0)
            comparison['processing_time_comparison'][api] = processing_time
        
        return comparison
    
    def get_api_status(self) -> Dict[str, Any]:
        """Get the status of all OCR APIs"""
        return {
            'gemini': {
                'enabled': self.gemini_enabled,
                'status': 'active' if self.gemini_client else 'inactive',
                'features': ['ai_powered_vision', 'structured_data_extraction', 'certificate_analysis', 'high_accuracy']
            },
            'google_vision': {
                'enabled': self.google_vision_enabled,
                'status': 'active' if self.google_vision_client else 'inactive',
                'features': ['text_detection', 'document_text', 'high_accuracy']
            },
            'kolosal': {
                'enabled': self.kolosal_enabled,
                'status': 'active',
                'features': ['auto_language_detection', 'no_api_key_required', 'blurry_document_support']
            },
            'ocr_space': {
                'enabled': self.ocr_space_enabled,
                'status': 'active' if self.ocr_space_enabled else 'inactive',
                'features': ['multi_language', 'overlay_support', 'confidence_scoring']
            },
            'tesseract': {
                'enabled': self.tesseract_enabled,
                'status': 'active',
                'features': ['open_source', 'multiple_languages', 'offline_processing']
            },
            'total_apis_available': sum([
                self.gemini_enabled,
                self.google_vision_enabled,
                self.kolosal_enabled,
                self.ocr_space_enabled,
                self.tesseract_enabled
            ])
        }
