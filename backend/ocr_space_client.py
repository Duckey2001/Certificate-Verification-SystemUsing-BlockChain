import os
import requests
import json
import base64
from typing import Dict, Optional, List, Tuple
from PIL import Image
import io
import tempfile
import cv2
import numpy as np
from dataclasses import dataclass
from datetime import datetime

@dataclass
class OCRResult:
    """Data class for OCR results"""
    text: str
    confidence: float
    processing_time: float
    api_used: str
    error: Optional[str] = None

class OCRRSpaceClient:
    """
    OCR.space API client for enhanced certificate text extraction
    """
    
    def __init__(self, api_key: str, api_url: str = "https://api.ocr.space/parse/image"):
        self.api_key = api_key
        self.api_url = api_url
        self.session = requests.Session()
        self.session.headers.update({
            'apikey': api_key,
            'Content-Type': 'application/x-www-form-urlencoded'
        })
    
    def extract_text_from_file(self, file_path: str, language: str = 'eng') -> OCRResult:
        """
        Extract text from image file using OCR.space API
        """
        try:
            start_time = time.time()
            
            # Prepare file for upload with proper content type
            file_mime_type = 'image/png' if file_path.lower().endswith('.png') else 'image/jpeg'
            
            with open(file_path, 'rb') as f:
                files = {'file': (os.path.basename(file_path), f.read(), file_mime_type)}
                
                # OCR.space API parameters
                payload = {
                    'apikey': self.api_key,
                    'language': language,
                    'isOverlayRequired': False,
                    'detectOrientation': True,
                    'scale': True,
                    'OCREngine': 2,  # Use OCR Engine 2 for better accuracy
                    'isTable': False,
                    'isCreateSearchablePdf': False,
                    'isSearchablePdfHideTextLayer': True,
                    'filetype': 'auto'  # Auto-detect file type
                }
                
                # Use regular requests session without pre-set headers
                response = requests.post(
                    self.api_url,
                    files=files,
                    data=payload,
                    timeout=30
                )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('IsErroredOnProcessing', False):
                    error_message = result.get('ErrorMessage', 'Unknown OCR.space error')
                    return OCRResult("", 0.0, processing_time, "ocr_space", error_message)
                
                # Extract text from parsed results
                parsed_text = result.get('ParsedResults', [])
                if parsed_text:
                    text = parsed_text[0].get('ParsedText', '')
                    text_overlay = parsed_text[0].get('TextOverlay', {})
                    
                    # Calculate average confidence from text overlay if available
                    confidence = 0.0
                    if text_overlay and 'Lines' in text_overlay:
                        confidences = []
                        for line in text_overlay['Lines']:
                            if 'Words' in line:
                                for word in line['Words']:
                                    if 'Confidence' in word:
                                        confidences.append(float(word['Confidence']))
                        
                        if confidences:
                            confidence = np.mean(confidences)
                    else:
                        # Fallback confidence estimation
                        confidence = min(95.0, len(text) * 0.5) if text else 0.0
                    
                    return OCRResult(text, confidence, processing_time, "ocr_space")
                else:
                    return OCRResult("", 0.0, processing_time, "ocr_space", "No parsed results returned")
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                return OCRResult("", 0.0, processing_time, "ocr_space", error_msg)
                
        except requests.exceptions.Timeout:
            return OCRResult("", 0.0, 0.0, "ocr_space", "Request timeout")
        except requests.exceptions.RequestException as e:
            return OCRResult("", 0.0, 0.0, "ocr_space", f"Request error: {str(e)}")
        except Exception as e:
            return OCRResult("", 0.0, 0.0, "ocr_space", f"Unexpected error: {str(e)}")
    
    def extract_text_from_base64(self, base64_data: str, language: str = 'eng') -> OCRResult:
        """
        Extract text from base64 encoded image data
        """
        try:
            start_time = time.time()
            
            # Prepare payload for base64
            payload = {
                'base64Image': f'data:image/png;base64,{base64_data}',
                'language': language,
                'isOverlayRequired': False,
                'detectOrientation': True,
                'scale': True,
                'OCREngine': 2,
                'isTable': False,
                'isCreateSearchablePdf': False,
                'isSearchablePdfHideTextLayer': True,
                'timeout': 30
            }
            
            response = self.session.post(
                self.api_url,
                data=payload,
                timeout=30
            )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                if result.get('IsErroredOnProcessing', False):
                    error_message = result.get('ErrorMessage', 'Unknown OCR.space error')
                    return OCRResult("", 0.0, processing_time, "ocr_space", error_message)
                
                parsed_text = result.get('ParsedResults', [])
                if parsed_text:
                    text = parsed_text[0].get('ParsedText', '')
                    
                    # Calculate confidence
                    confidence = min(95.0, len(text) * 0.5) if text else 0.0
                    
                    return OCRResult(text, confidence, processing_time, "ocr_space")
                else:
                    return OCRResult("", 0.0, processing_time, "ocr_space", "No parsed results returned")
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                return OCRResult("", 0.0, processing_time, "ocr_space", error_msg)
                
        except Exception as e:
            return OCRResult("", 0.0, 0.0, "ocr_space", f"Error: {str(e)}")

class MultiAPIOCRProcessor:
    """
    Multi-API OCR processor that uses both Tesseract and OCR.space
    with intelligent fallback and confidence comparison
    """
    
    def __init__(self, ocr_space_api_key: str):
        self.ocr_space_client = OCRRSpaceClient(ocr_space_api_key)
        self.tesseract_processor = None  # Will be initialized when needed
        
    def _initialize_tesseract(self):
        """Initialize Tesseract processor if not already done"""
        if self.tesseract_processor is None:
            from certificate_ocr import CertificateOCR
            self.tesseract_processor = CertificateOCR()
    
    def extract_text_with_multiple_apis(self, file_path: str, prefer_api: str = 'auto') -> Dict:
        """
        Extract text using multiple APIs and return the best result
        """
        results = {}
        
        # Try OCR.space first (usually better accuracy)
        try:
            ocr_space_result = self.ocr_space_client.extract_text_from_file(file_path)
            results['ocr_space'] = {
                'text': ocr_space_result.text,
                'confidence': ocr_space_result.confidence,
                'processing_time': ocr_space_result.processing_time,
                'error': ocr_space_result.error
            }
        except Exception as e:
            results['ocr_space'] = {
                'text': '',
                'confidence': 0.0,
                'processing_time': 0.0,
                'error': str(e)
            }
        
        # Try Tesseract as fallback
        try:
            self._initialize_tesseract()
            
            # Preprocess image for Tesseract
            processed_img, _ = self.tesseract_processor.preprocess_image(file_path)
            tesseract_text, tesseract_confidence = self.tesseract_processor.extract_text_with_confidence(processed_img)
            
            results['tesseract'] = {
                'text': tesseract_text,
                'confidence': tesseract_confidence,
                'processing_time': 0.0,  # Not tracked in original implementation
                'error': None
            }
        except Exception as e:
            results['tesseract'] = {
                'text': '',
                'confidence': 0.0,
                'processing_time': 0.0,
                'error': str(e)
            }
        
        # Determine best result
        best_result = self._select_best_result(results, prefer_api)
        
        return {
            'best_result': best_result,
            'all_results': results,
            'comparison': {
                'ocr_space_better': results['ocr_space']['confidence'] > results['tesseract']['confidence'],
                'confidence_difference': abs(results['ocr_space']['confidence'] - results['tesseract']['confidence']),
                'both_successful': len([r for r in results.values() if r['text'] and not r['error']]) == 2
            }
        }
    
    def _select_best_result(self, results: Dict, prefer_api: str) -> Dict:
        """
        Select the best OCR result based on confidence and preferences
        """
        # Filter out failed results
        successful_results = {k: v for k, v in results.items() if v['text'] and not v['error']}
        
        if not successful_results:
            # Return the result with least severe error
            return min(results.values(), key=lambda x: (1 if x['error'] else 0, -x['confidence']))
        
        if prefer_api == 'ocr_space' and 'ocr_space' in successful_results:
            return successful_results['ocr_space']
        elif prefer_api == 'tesseract' and 'tesseract' in successful_results:
            return successful_results['tesseract']
        else:
            # Auto-select based on confidence
            return max(successful_results.values(), key=lambda x: x['confidence'])
    
    def extract_certificate_data_enhanced(self, file_path: str, prefer_api: str = 'auto') -> Dict:
        """
        Enhanced certificate data extraction using multiple APIs
        """
        try:
            # Get OCR results from multiple APIs
            ocr_results = self.extract_text_with_multiple_apis(file_path, prefer_api)
            best_ocr = ocr_results['best_result']
            
            if not best_ocr['text']:
                return {
                    'error': 'No text extracted from any OCR API',
                    'ocr_results': ocr_results,
                    'confidence_score': 0
                }
            
            # Use Tesseract processor for field extraction (it has better patterns)
            self._initialize_tesseract()
            
            # Extract structured data using the best OCR text
            extracted_data = {
                'student_name': self.tesseract_processor.extract_field(best_ocr['text'], 'student_name'),
                'student_surname': self.tesseract_processor.extract_field(best_ocr['text'], 'student_surname'),
                'student_id': self.tesseract_processor.extract_field(best_ocr['text'], 'student_id'),
                'examination_year': self.tesseract_processor.extract_field(best_ocr['text'], 'examination_year'),
                'institution': self.tesseract_processor.extract_field(best_ocr['text'], 'institution'),
                'certificate_type': self.tesseract_processor.extract_field(best_ocr['text'], 'certificate_type'),
                'exam_board': self.tesseract_processor.extract_field(best_ocr['text'], 'exam_board'),
                'grades_summary': self.tesseract_processor.extract_field(best_ocr['text'], 'grades_summary'),
                'subjects_with_grades': self.tesseract_processor.extract_subjects_with_grades(best_ocr['text']),
                'raw_text': best_ocr['text'][:500] + '...' if len(best_ocr['text']) > 500 else best_ocr['text'],
                'extraction_method': f"multi_api_{best_ocr.get('api_used', 'unknown')}",
                'ocr_confidence': best_ocr['confidence'],
                'processing_time': best_ocr['processing_time'],
                'ocr_api_used': best_ocr.get('api_used', 'unknown')
            }
            
            # Add OCR comparison data
            extracted_data['ocr_comparison'] = ocr_results['comparison']
            extracted_data['all_ocr_results'] = ocr_results['all_results']
            
            # Calculate overall confidence
            extracted_data['confidence_score'] = self.tesseract_processor._calculate_overall_confidence(
                extracted_data, best_ocr['confidence']
            )
            
            # Verify structure
            extracted_data['verification'] = self.tesseract_processor.verify_certificate_structure(extracted_data)
            
            # Clean up None values
            extracted_data = {k: v for k, v in extracted_data.items() if v is not None}
            
            return extracted_data
            
        except Exception as e:
            return {
                'error': f'Enhanced multi-API extraction failed: {str(e)}',
                'confidence_score': 0,
                'extraction_method': 'multi_api_failed'
            }

# Import time for processing time measurement
import time

# Global instance for use in the application
_multi_api_processor = None

def get_multi_api_processor() -> MultiAPIOCRProcessor:
    """Get or create the global multi-api OCR processor"""
    global _multi_api_processor
    
    if _multi_api_processor is None:
        api_key = os.getenv('OCR_SPACE_API_KEY')
        if not api_key:
            raise ValueError("OCR_SPACE_API_KEY environment variable not set")
        
        _multi_api_processor = MultiAPIOCRProcessor(api_key)
    
    return _multi_api_processor

def extract_certificate_data_multi_api(file_path: str, prefer_api: str = 'auto') -> Dict:
    """
    Convenience function for multi-API certificate extraction
    """
    processor = get_multi_api_processor()
    return processor.extract_certificate_data_enhanced(file_path, prefer_api)
