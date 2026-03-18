import os
import requests
import json
import base64
from typing import Dict, Optional, List, Tuple
from PIL import Image
import io
import tempfile
from dataclasses import dataclass
from datetime import datetime
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class GeminiOCRResult:
    """Data class for Gemini OCR results"""
    text: str
    confidence: float
    processing_time: float
    api_used: str
    error: Optional[str] = None
    structured_data: Optional[Dict] = None

class GeminiOCRClient:
    """
    Google Gemini API client for enhanced certificate text extraction and analysis
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
        self.session = requests.Session()
        
    def extract_text_from_file(self, file_path: str, prompt: str = None) -> GeminiOCRResult:
        """
        Extract text from image file using Gemini API with vision capabilities
        """
        try:
            start_time = time.time()
            
            # Default prompt for certificate OCR
            if prompt is None:
                prompt = """
                Please extract all text from this certificate image accurately. 
                Pay special attention to:
                - Student names and identification numbers
                - Examination years and dates
                - Subject names and grades
                - Institution names and logos
                - Certificate numbers and reference codes
                
                Format the output clearly with proper spacing and line breaks.
                Preserve the original layout and structure as much as possible.
                """
            
            # Read and encode image
            with open(file_path, 'rb') as f:
                image_data = f.read()
                base64_image = base64.b64encode(image_data).decode('utf-8')
                
                # Get image mime type
                if file_path.lower().endswith('.png'):
                    mime_type = 'image/png'
                elif file_path.lower().endswith('.jpg') or file_path.lower().endswith('.jpeg'):
                    mime_type = 'image/jpeg'
                else:
                    mime_type = 'image/jpeg'  # Default
                
            # Prepare Gemini API request
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            },
                            {
                                "inline_data": {
                                    "mime_type": mime_type,
                                    "data": base64_image
                                }
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.1,  # Low temperature for accurate text extraction
                    "topK": 32,
                    "topP": 0.95,
                    "maxOutputTokens": 4096
                },
                "safetySettings": [
                    {
                        "category": "HARM_CATEGORY_HARASSMENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_HATE_SPEECH", 
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    },
                    {
                        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                    }
                ]
            }
            
            # Make API request
            headers = {
                'Content-Type': 'application/json',
                'x-goog-api-key': self.api_key
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            
            processing_time = time.time() - start_time
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract text from Gemini response
                if 'candidates' in result and len(result['candidates']) > 0:
                    candidate = result['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        text_parts = candidate['content']['parts']
                        extracted_text = ''
                        for part in text_parts:
                            if 'text' in part:
                                extracted_text += part['text']
                        
                        # Calculate confidence based on response quality
                        confidence = self._calculate_gemini_confidence(result, extracted_text)
                        
                        # Extract structured data if possible
                        structured_data = self._extract_structured_data(extracted_text)
                        
                        return GeminiOCRResult(
                            text=extracted_text.strip(),
                            confidence=confidence,
                            processing_time=processing_time,
                            api_used="gemini",
                            structured_data=structured_data
                        )
                    else:
                        return GeminiOCRResult("", 0.0, processing_time, "gemini", "No text content in response")
                else:
                    return GeminiOCRResult("", 0.0, processing_time, "gemini", "No candidates in response")
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"Gemini API error: {error_msg}")
                return GeminiOCRResult("", 0.0, processing_time, "gemini", error_msg)
                
        except requests.exceptions.Timeout:
            return GeminiOCRResult("", 0.0, 0.0, "gemini", "Request timeout")
        except requests.exceptions.RequestException as e:
            return GeminiOCRResult("", 0.0, 0.0, "gemini", f"Request error: {str(e)}")
        except Exception as e:
            logger.error(f"Gemini API unexpected error: {str(e)}")
            return GeminiOCRResult("", 0.0, 0.0, "gemini", f"Unexpected error: {str(e)}")
    
    def extract_certificate_data_structured(self, file_path: str) -> GeminiOCRResult:
        """
        Extract structured certificate data using Gemini's understanding capabilities
        """
        try:
            start_time = time.time()
            
            # Specialized prompt for structured certificate data extraction
            structured_prompt = """
            Analyze this certificate image and extract the following information in JSON format:
            
            {
                "student_name": "full student name",
                "student_surname": "student surname", 
                "student_id": "student identification number",
                "examination_year": "year of examination",
                "institution": "issuing institution name",
                "certificate_type": "type of certificate",
                "exam_board": "examining board",
                "subjects": [
                    {
                        "name": "subject name",
                        "grade": "grade achieved"
                    }
                ],
                "certificate_number": "certificate/reference number",
                "issue_date": "date of issue",
                "raw_text": "extract all text as fallback"
            }
            
            Pay close attention to accuracy and fill in as many fields as possible.
            If a field is not found, use null or empty string.
            For subjects, extract all visible subjects with their grades.
            """
            
            # Get the structured result
            result = self.extract_text_from_file(file_path, structured_prompt)
            
            if result.text:
                try:
                    # Try to parse JSON from the response
                    json_start = result.text.find('{')
                    json_end = result.text.rfind('}') + 1
                    
                    if json_start != -1 and json_end > json_start:
                        json_str = result.text[json_start:json_end]
                        structured_data = json.loads(json_str)
                        
                        result.structured_data = structured_data
                        result.confidence = min(95.0, result.confidence + 10)  # Bonus for successful structuring
                        
                except json.JSONDecodeError:
                    # If JSON parsing fails, try to extract structured data manually
                    result.structured_data = self._extract_structured_data(result.text)
            
            return result
            
        except Exception as e:
            return GeminiOCRResult("", 0.0, 0.0, "gemini", f"Structured extraction error: {str(e)}")
    
    def _calculate_gemini_confidence(self, result: Dict, extracted_text: str) -> float:
        """Calculate confidence score based on Gemini response quality"""
        base_confidence = 85.0  # Start with good baseline for Gemini
        
        # Check for finish reason
        if 'candidates' in result and len(result['candidates']) > 0:
            candidate = result['candidates'][0]
            finish_reason = candidate.get('finishReason', 'STOP')
            
            if finish_reason == 'STOP':
                base_confidence += 5.0  # Complete response
            elif finish_reason == 'MAX_TOKENS':
                base_confidence -= 10.0  # Cut off response
            elif finish_reason in ['SAFETY', 'RECITATION', 'OTHER']:
                base_confidence -= 20.0  # Problematic response
        
        # Text quality factors
        text_length = len(extracted_text.strip())
        
        if text_length == 0:
            return 0.0
        elif text_length < 50:
            base_confidence *= 0.5  # Very short text
        elif text_length > 2000:
            base_confidence *= 1.1  # Good amount of text
        
        # Check for certificate-specific keywords
        certificate_keywords = ['certificate', 'examination', 'student', 'grade', 'subject', 'year']
        keyword_count = sum(1 for keyword in certificate_keywords if keyword.lower() in extracted_text.lower())
        
        if keyword_count >= 3:
            base_confidence += 5.0  # Likely certificate content
        
        # Check for structured patterns (names, numbers, dates)
        import re
        patterns = {
            'name': r'[A-Z][a-z]+ [A-Z][a-z]+',
            'year': r'\b(19|20)\d{2}\b',
            'grade': r'\b[ABCDEF][+-]?\b|\b\d{1,3}%?\b'
        }
        
        pattern_matches = sum(1 for pattern in patterns.values() if re.search(pattern, extracted_text))
        if pattern_matches >= 2:
            base_confidence += 3.0
        
        return min(base_confidence, 98.0)  # Cap at 98%
    
    def _extract_structured_data(self, text: str) -> Dict:
        """Extract structured data from raw text using pattern matching"""
        structured = {}
        
        import re
        
        # Extract student name (look for "Name:" patterns or capitalized names)
        name_patterns = [
            r'Name[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)',
            r'Student[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)',
            r'([A-Z][a-z]+ [A-Z][a-z]+)\s+(?:ID|Student|Candidate)'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                structured['student_name'] = match.group(1).strip()
                break
        
        # Extract examination year
        year_match = re.search(r'\b(19|20)\d{2}\b', text)
        if year_match:
            structured['examination_year'] = int(year_match.group(1))
        
        # Extract student ID
        id_patterns = [
            r'ID[:\s]+([A-Z0-9]+)',
            r'Student ID[:\s]+([A-Z0-9]+)',
            r'Candidate[:\s]+([A-Z0-9]+)'
        ]
        
        for pattern in id_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                structured['student_id'] = match.group(1).strip()
                break
        
        # Extract subjects and grades
        subject_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*[:\-]?\s*([ABCDEF][+-]?|\d{1,3}%?)'
        subjects = re.findall(subject_pattern, text)
        
        if subjects:
            structured['subjects'] = [{'name': subj.strip(), 'grade': grade.strip()} for subj, grade in subjects]
        
        # Extract institution
        institution_patterns = [
            r'(University|College|School|Institute|Academy)\s+of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\s+(University|College|School|Institute|Academy))'
        ]
        
        for pattern in institution_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                structured['institution'] = match.group(0).strip()
                break
        
        return structured
    
    def get_api_info(self) -> Dict:
        """Get Gemini API information and capabilities"""
        return {
            'api_name': 'gemini',
            'model': 'gemini-2.5-flash',
            'capabilities': [
                'multimodal_vision',
                'structured_data_extraction',
                'high_accuracy_text_recognition',
                'certificate_specific_analysis',
                'context_understanding'
            ],
            'features': [
                'supports_multiple_image_formats',
                'natural_language_processing',
                'json_structured_output',
                'high_confidence_accuracy',
                'contextual_text_extraction'
            ],
            'limits': {
                'max_image_size': '20MB',
                'max_output_tokens': 4096,
                'timeout': 60
            }
        }

# Global instance for use in the application
_gemini_client = None

def get_gemini_client() -> GeminiOCRClient:
    """Get or create the global Gemini OCR client"""
    global _gemini_client
    
    if _gemini_client is None:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        _gemini_client = GeminiOCRClient(api_key)
    
    return _gemini_client

def extract_certificate_data_with_gemini(file_path: str, structured: bool = True) -> Dict:
    """
    Convenience function for Gemini certificate extraction
    """
    try:
        client = get_gemini_client()
        
        if structured:
            result = client.extract_certificate_data_structured(file_path)
        else:
            result = client.extract_text_from_file(file_path)
        
        return {
            'text': result.text,
            'confidence': result.confidence,
            'processing_time': result.processing_time,
            'api_used': result.api_used,
            'error': result.error,
            'structured_data': result.structured_data,
            'raw_response': result.__dict__
        }
        
    except Exception as e:
        return {
            'error': f'Gemini extraction failed: {str(e)}',
            'confidence': 0,
            'api_used': 'gemini',
            'processing_time': 0
        }
