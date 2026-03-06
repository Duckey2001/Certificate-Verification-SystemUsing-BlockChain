import os
import pytesseract
from PIL import Image
import cv2
import numpy as np
import re
from typing import Dict, Optional, List
import json

class CertificateOCR:
    """
    OCR-based certificate data extraction using Tesseract
    """
    
    def __init__(self):
        # Set Tesseract path if needed
        self.tesseract_path = '/usr/bin/tesseract'
        if os.path.exists(self.tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
        
        # Define patterns for certificate fields
        self.patterns = {
            'student_name': [
                r'(?:Name|Student|Candidate):\s*([A-Za-z\s]+)',
                r'([A-Z][a-z]+\s+[A-Z][a-z]+)',
                r'To Whom It May Concern:\s*([A-Za-z\s]+)'
            ],
            'student_surname': [
                r'(?:Surname|Last Name):\s*([A-Za-z\s]+)',
                r'([A-Z][a-z]+)\s+(?:[A-Z][a-z]+\s+)?([A-Z][a-z]+)'
            ],
            'student_id': [
                r'(?:Student ID|Candidate No|Examination No):\s*([A-Z0-9]+)',
                r'ID:\s*([A-Z0-9]+)',
                r'No\.:\s*([A-Z0-9]+)'
            ],
            'examination_year': [
                r'(?:Year|Examination Year|Date):\s*(\d{4})',
                r'(\d{4})\s*(?:Examination|Year)',
                r'Class\s+of\s+(\d{4})'
            ],
            'subjects': [
                r'(?:Subjects|Courses):\s*([A-Za-z,\s]+)',
                r'([A-Z][a-z]+(?:,\s*[A-Z][a-z]+)*)',
                r'(?:Mathematics|English|Science|Biology|Chemistry|Physics|History|Geography)'
            ],
            'institution': [
                r'(?:School|Institution|College):\s*([A-Za-z\s]+)',
                r'([A-Z][a-z]+\s+(?:High School|College|Institution))',
                r'([A-Z][a-z]+\s+[A-Z][a-z]+\s+School)'
            ],
            'certificate_type': [
                r'(?:Certificate|Diploma|Transcript)',
                r'General Certificate of Secondary Education',
                r'Cambridge IGCSE'
            ]
        }
    
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """
        Preprocess image for better OCR accuracy
        """
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Apply threshold to get binary image
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Noise removal
        denoised = cv2.medianBlur(binary, 3)
        
        # Dilation for better text recognition
        kernel = np.ones((1, 1), np.uint8)
        dilated = cv2.dilate(denoised, kernel, iterations=1)
        
        return dilated
    
    def extract_text(self, image_path: str) -> str:
        """
        Extract text from image using Tesseract OCR
        """
        try:
            # Preprocess image
            processed_img = self.preprocess_image(image_path)
            
            # Convert PIL Image
            pil_img = Image.fromarray(processed_img)
            
            # Configure Tesseract for better results
            custom_config = r'--oem 3 --psm 6 -l eng'
            
            # Extract text
            text = pytesseract.image_to_string(pil_img, config=custom_config)
            
            return text.strip()
            
        except Exception as e:
            raise Exception(f"OCR extraction failed: {str(e)}")
    
    def extract_field(self, text: str, field_name: str) -> Optional[str]:
        """
        Extract specific field using regex patterns
        """
        if field_name not in self.patterns:
            return None
        
        patterns = self.patterns[field_name]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # For patterns with groups, return the last group (most specific)
                if match.groups():
                    return match.groups()[-1].strip()
                else:
                    return match.group(0).strip()
        
        return None
    
    def extract_subjects(self, text: str) -> List[str]:
        """
        Extract subjects from certificate text
        """
        subjects_text = self.extract_field(text, 'subjects')
        
        if subjects_text:
            # Split by common delimiters
            subjects = re.split(r'[,;]\s*', subjects_text)
            # Clean and filter
            subjects = [s.strip() for s in subjects if s.strip() and len(s) > 2]
            return subjects
        
        # Fallback: look for common subject names
        common_subjects = [
            'Mathematics', 'English Language', 'English Literature',
            'Biology', 'Chemistry', 'Physics', 'Combined Science',
            'History', 'Geography', 'Economics', 'Business Studies',
            'Computer Science', 'Information Technology',
            'Art & Design', 'Music', 'Physical Education',
            'Religious Studies', 'Modern Languages', 'French', 'German', 'Spanish'
        ]
        
        found_subjects = []
        for subject in common_subjects:
            if subject.lower() in text.lower():
                found_subjects.append(subject)
        
        return found_subjects
    
    def extract_certificate_data(self, image_path: str) -> Dict:
        """
        Extract all certificate data from image
        """
        try:
            # Extract text
            text = self.extract_text(image_path)
            
            # Extract fields
            data = {
                'student_name': self.extract_field(text, 'student_name'),
                'student_surname': self.extract_field(text, 'student_surname'),
                'student_id': self.extract_field(text, 'student_id'),
                'examination_year': self.extract_field(text, 'examination_year'),
                'subjects': self.extract_subjects(text),
                'institution': self.extract_field(text, 'institution'),
                'certificate_type': self.extract_field(text, 'certificate_type'),
                'raw_text': text,
                'extraction_method': 'tesseract_ocr',
                'confidence_score': self._calculate_confidence(text)
            }
            
            # Clean and validate data
            data = self._clean_extracted_data(data)
            
            return data
            
        except Exception as e:
            return {
                'error': str(e),
                'extraction_method': 'tesseract_ocr',
                'raw_text': '',
                'confidence_score': 0
            }
    
    def _calculate_confidence(self, text: str) -> float:
        """
        Calculate confidence score based on extracted text quality
        """
        if not text:
            return 0.0
        
        # Basic confidence calculation
        confidence = 0.0
        
        # Check for certificate keywords
        certificate_keywords = [
            'certificate', 'examination', 'student', 'candidate',
            'subject', 'grade', 'pass', 'fail', 'merit', 'distinction'
        ]
        
        keyword_count = sum(1 for keyword in certificate_keywords 
                          if keyword.lower() in text.lower())
        confidence += (keyword_count / len(certificate_keywords)) * 30
        
        # Check for year patterns
        year_matches = len(re.findall(r'\b(19|20)\d{2}\b', text))
        if year_matches > 0:
            confidence += 20
        
        # Check for name patterns
        name_matches = len(re.findall(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b', text))
        if name_matches > 0:
            confidence += 20
        
        # Text length contribution
        if len(text) > 100:
            confidence += 20
        elif len(text) > 50:
            confidence += 10
        
        # Check for subject patterns
        subject_keywords = ['mathematics', 'english', 'science', 'history', 'geography']
        subject_count = sum(1 for subject in subject_keywords 
                           if subject.lower() in text.lower())
        confidence += (subject_count / len(subject_keywords)) * 10
        
        return min(confidence, 100.0)
    
    def _clean_extracted_data(self, data: Dict) -> Dict:
        """
        Clean and validate extracted data
        """
        # Clean student name
        if data.get('student_name'):
            data['student_name'] = data['student_name'].title().strip()
        
        # Clean student surname
        if data.get('student_surname'):
            data['student_surname'] = data['student_surname'].title().strip()
        
        # Clean student ID
        if data.get('student_id'):
            data['student_id'] = data['student_id'].upper().strip()
        
        # Clean examination year
        if data.get('examination_year'):
            try:
                year = int(data['examination_year'])
                if 1900 <= year <= 2030:
                    data['examination_year'] = year
                else:
                    data['examination_year'] = None
            except ValueError:
                data['examination_year'] = None
        
        # Clean institution
        if data.get('institution'):
            data['institution'] = data['institution'].title().strip()
        
        # Clean subjects
        if data.get('subjects'):
            subjects = [s.title().strip() for s in data['subjects'] if s.strip()]
            data['subjects'] = list(set(subjects))  # Remove duplicates
        
        return data
    
    def verify_certificate_structure(self, data: Dict) -> Dict:
        """
        Verify if extracted data matches expected certificate structure
        """
        verification = {
            'is_valid_structure': False,
            'missing_fields': [],
            'confidence_score': data.get('confidence_score', 0),
            'validation_details': {}
        }
        
        # Required fields for LGCSE certificate
        required_fields = ['student_name', 'examination_year', 'subjects']
        
        for field in required_fields:
            if not data.get(field):
                verification['missing_fields'].append(field)
                verification['validation_details'][field] = 'Missing required field'
            else:
                verification['validation_details'][field] = 'Present'
        
        # Check if we have enough data
        if len(verification['missing_fields']) == 0:
            verification['is_valid_structure'] = True
        
        # Additional checks
        if data.get('subjects') and len(data['subjects']) >= 3:
            verification['validation_details']['subjects'] = 'Adequate number of subjects'
        elif data.get('subjects'):
            verification['validation_details']['subjects'] = 'Limited subjects'
        
        if data.get('examination_year'):
            year = data['examination_year']
            if isinstance(year, int) and 2015 <= year <= 2025:
                verification['validation_details']['examination_year'] = 'Valid year range'
            else:
                verification['validation_details']['examination_year'] = 'Unusual year'
        
        return verification

# Example usage
if __name__ == "__main__":
    ocr = CertificateOCR()
    
    # Test with an image
    image_path = "certificate_sample.jpg"
    if os.path.exists(image_path):
        result = ocr.extract_certificate_data(image_path)
        print(json.dumps(result, indent=2))
    else:
        print(f"Test image not found: {image_path}")
