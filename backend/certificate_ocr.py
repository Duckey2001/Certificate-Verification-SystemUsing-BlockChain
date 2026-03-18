import os
import pytesseract
from PIL import Image
import cv2
import numpy as np
import re
from typing import Dict, Optional, List, Tuple
import json
from dataclasses import dataclass
from datetime import datetime

@dataclass
class CertificateField:
    """Data class for certificate field configuration"""
    patterns: List[str]
    required: bool = False
    post_process: Optional[callable] = None
    validation: Optional[callable] = None

class CertificateOCR:
    """
    Enhanced OCR-based certificate data extraction using Tesseract
    """
    
    def __init__(self, tesseract_path: Optional[str] = None):
        # Set Tesseract path if provided
        if tesseract_path and os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        else:
            # Try common paths
            common_paths = [
                '/usr/bin/tesseract',
                '/usr/local/bin/tesseract',
                'C:\\Program Files\\Tesseract-OCR\\tesseract.exe',
                'C:\\Program Files (x86)\\Tesseract-OCR\\tesseract.exe'
            ]
            for path in common_paths:
                if os.path.exists(path):
                    pytesseract.pytesseract.tesseract_cmd = path
                    break
        
        self._init_patterns()
    
    def _init_patterns(self):
        """Initialize patterns with better organization"""
        self.fields = {
            'student_name': CertificateField(
                patterns=[
                    r'(?:Student|Candidate|Name|Pupil)(?:\s*Name)?[\s:]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
                    r'To Whom It May Concern:?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
                    r'This\s+(?:is to|certifies?\s+that)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',
                    r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})'  # Fallback: 2-4 word name
                ],
                required=True,
                post_process=lambda x: self._clean_name(x)
            ),
            
            'student_surname': CertificateField(
                patterns=[
                    r'(?:Surname|Last Name|Family Name)[\s:]+([A-Z][a-z]+)',
                    r'Surname:?\s*([A-Z][a-z]+)',
                    r'([A-Z][a-z]+)$'  # Last word might be surname
                ],
                post_process=lambda x: x.title().strip()
            ),
            
            'student_id': CertificateField(
                patterns=[
                    r'(?:Student ID|Candidate (?:No|Number)|Examination No|ID Number)[\s:]+([A-Z0-9]{5,20})',
                    r'ID:?\s*([A-Z0-9]{5,20})',
                    r'No\.?:?\s*([A-Z0-9]{5,20})',
                    r'Registration\s+(?:No|Number)[\s:]+([A-Z0-9]{5,20})'
                ],
                post_process=lambda x: x.upper().strip()
            ),
            
            'examination_year': CertificateField(
                patterns=[
                    r'(?:Year|Examination Year|Session|Date|Class of)[\s:]+(\d{4})',
                    r'(?:20|19)\d{2}',  # Direct year match
                    r'(\d{4})\s*(?:Examination|Session|Year)'
                ],
                required=True,
                post_process=self._validate_year,
                validation=lambda x: isinstance(x, int) and 1990 <= x <= datetime.now().year + 5
            ),
            
            'institution': CertificateField(
                patterns=[
                    r'(?:School|Institution|College|Centre|Center)[\s:]+([A-Z][A-Za-z\s&\'-]+)',
                    r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+(?:High School|Secondary School|College|Academy)))',
                    r'Ministry of Education[^\n]*'
                ],
                post_process=lambda x: x.strip()
            ),
            
            'certificate_type': CertificateField(
                patterns=[
                    r'((?:General Certificate|IGCSE|GCSE|National Certificate|Diploma)[^\n]*)',
                    r'(Cambridge|Edexcel|AQA|OCR|WJEC)[\s-]+(?:International)?[\s-]*(?:GCSE|A-?Level)',
                    r'Certificate of (?:Secondary|Primary) Education'
                ],
                post_process=lambda x: x.strip()
            ),
            
            'exam_board': CertificateField(
                patterns=[
                    r'(Cambridge|Edexcel|AQA|OCR|WJEC|CCEA|SQA)',
                    r'(Ministry of Education|Department of Education)'
                ]
            ),
            
            'grades_summary': CertificateField(
                patterns=[
                    r'(?:Grades?|Results?|Performance)[\s:]+([A-Z\s,]+)',
                    r'Overall Grade:?\s*([A-Z][+-]?)'
                ]
            )
        }
        
        # Common subjects for validation
        self.common_subjects = [
            'Mathematics', 'English Language', 'English Literature',
            'Biology', 'Chemistry', 'Physics', 'Combined Science',
            'History', 'Geography', 'Economics', 'Business Studies',
            'Computer Science', 'Information Technology',
            'Art & Design', 'Music', 'Physical Education',
            'Religious Studies', 'French', 'German', 'Spanish',
            'Accounting', 'Commerce', 'Additional Mathematics'
        ]
        
        # Subject-grade pattern
        self.subject_grade_pattern = re.compile(
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+([A-Z][+-]?|\d{1,3}(?:%)?)',
            re.IGNORECASE
        )
    
    def preprocess_image(self, image_path: str) -> Tuple[np.ndarray, Dict]:
        """
        Enhanced image preprocessing with multiple techniques
        Returns preprocessed image and preprocessing metadata
        """
        metadata = {'techniques_applied': []}
        
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not read image: {image_path}")
        
        # Get original dimensions
        height, width = img.shape[:2]
        metadata['original_size'] = f"{width}x{height}"
        
        # Resize if too small (helps OCR)
        if width < 1000:
            scale = 1000 / width
            new_width = int(width * scale)
            new_height = int(height * scale)
            img = cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            metadata['techniques_applied'].append('resized')
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        metadata['techniques_applied'].append('grayscale')
        
        # Apply adaptive thresholding
        binary = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        metadata['techniques_applied'].append('adaptive_threshold')
        
        # Noise removal
        denoised = cv2.medianBlur(binary, 3)
        metadata['techniques_applied'].append('median_blur')
        
        # Morphological operations to enhance text
        kernel = np.ones((2, 2), np.uint8)
        processed = cv2.morphologyEx(denoised, cv2.MORPH_CLOSE, kernel)
        processed = cv2.morphologyEx(processed, cv2.MORPH_OPEN, kernel)
        metadata['techniques_applied'].append('morphological_ops')
        
        # Deskew if needed
        coords = np.column_stack(np.where(processed > 0))
        if len(coords) > 0:
            angle = cv2.minAreaRect(coords)[-1]
            if angle < -45:
                angle = -(90 + angle)
            else:
                angle = -angle
            
            if abs(angle) > 0.5:
                (h, w) = processed.shape[:2]
                center = (w // 2, h // 2)
                M = cv2.getRotationMatrix2D(center, angle, 1.0)
                processed = cv2.warpAffine(processed, M, (w, h),
                                          flags=cv2.INTER_CUBIC,
                                          borderMode=cv2.BORDER_REPLICATE)
                metadata['techniques_applied'].append('deskewed')
                metadata['skew_angle'] = angle
        
        return processed, metadata
    
    def extract_text_with_confidence(self, image: np.ndarray) -> Tuple[str, float]:
        """
        Extract text with confidence scores using multiple OCR configurations
        """
        all_texts = []
        confidences = []
        
        # Try different page segmentation modes
        psm_modes = [3, 4, 6, 11, 12]  # Different PSM values for different layouts
        
        for psm in psm_modes:
            try:
                # Convert to PIL Image
                pil_img = Image.fromarray(image)
                
                # Configure Tesseract
                config = f'--oem 3 --psm {psm} -l eng --dpi 300'
                
                # Get data including confidence
                data = pytesseract.image_to_data(pil_img, config=config, output_type=pytesseract.Output.DICT)
                
                # Extract text and calculate confidence
                text_parts = []
                conf_parts = []
                
                for i, text in enumerate(data['text']):
                    if text.strip() and int(data['conf'][i]) > 30:  # Filter low confidence
                        text_parts.append(text)
                        conf_parts.append(float(data['conf'][i]))
                
                if text_parts:
                    all_texts.append(' '.join(text_parts))
                    confidences.append(np.mean(conf_parts) if conf_parts else 0)
                    
            except Exception:
                continue
        
        # Combine results
        if all_texts:
            # Weight by confidence
            total_conf = sum(confidences)
            if total_conf > 0:
                weighted_texts = [text * (conf/total_conf) for text, conf in zip(all_texts, confidences)]
                final_text = ' '.join([str(t) for t in weighted_texts if t])
            else:
                final_text = ' '.join(all_texts)
            
            avg_confidence = np.mean(confidences) if confidences else 0
            return final_text, avg_confidence
        else:
            return "", 0.0
    
    def extract_field(self, text: str, field_name: str) -> Optional[str]:
        """
        Enhanced field extraction with context awareness
        """
        if field_name not in self.fields:
            return None
        
        field_config = self.fields[field_name]
        
        # Try each pattern
        for pattern in field_config.patterns:
            # Look for pattern with context (within reasonable distance)
            matches = list(re.finditer(pattern, text, re.IGNORECASE | re.MULTILINE))
            
            for match in matches:
                if match.groups():
                    # Return the first capturing group
                    value = match.group(1).strip()
                else:
                    value = match.group(0).strip()
                
                # Apply post-processing if defined
                if field_config.post_process:
                    value = field_config.post_process(value)
                
                # Validate if defined
                if field_config.validation and not field_config.validation(value):
                    continue
                
                return value
        
        return None
    
    def extract_subjects_with_grades(self, text: str) -> List[Dict[str, str]]:
        """
        Extract subjects and their corresponding grades
        """
        subjects_with_grades = []
        
        # Look for subject-grade pairs
        lines = text.split('\n')
        for line in lines:
            # Skip header/footer lines
            if any(word in line.lower() for word in ['page', 'subject', 'grade', 'result']):
                continue
            
            # Look for subject-grade pattern
            matches = self.subject_grade_pattern.findall(line)
            for subject, grade in matches:
                subject = subject.strip()
                grade = grade.strip()
                
                # Validate subject
                if self._is_valid_subject(subject):
                    subjects_with_grades.append({
                        'subject': subject,
                        'grade': grade
                    })
        
        # If no grades found, just extract subjects
        if not subjects_with_grades:
            for subject in self.common_subjects:
                if subject.lower() in text.lower():
                    subjects_with_grades.append({
                        'subject': subject,
                        'grade': None
                    })
        
        return subjects_with_grades
    
    def _is_valid_subject(self, subject: str) -> bool:
        """Validate if text is likely a subject name"""
        subject_lower = subject.lower()
        
        # Check against common subjects
        for common in self.common_subjects:
            if common.lower() in subject_lower or subject_lower in common.lower():
                return True
        
        # Check for common subject patterns
        if re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*$', subject):
            # Avoid common non-subject words
            non_subjects = ['total', 'average', 'result', 'summary', 'candidate']
            if subject_lower not in non_subjects:
                return True
        
        return False
    
    def extract_certificate_data(self, image_path: str) -> Dict:
        """
        Main method to extract all certificate data
        """
        try:
            # Preprocess image
            processed_img, preprocess_metadata = self.preprocess_image(image_path)
            
            # Extract text with confidence
            text, ocr_confidence = self.extract_text_with_confidence(processed_img)
            
            if not text:
                return {
                    'error': 'No text extracted from image',
                    'extraction_method': 'tesseract_ocr',
                    'confidence_score': 0,
                    'preprocessing': preprocess_metadata
                }
            
            # Extract all fields
            data = {
                'student_name': self.extract_field(text, 'student_name'),
                'student_surname': self.extract_field(text, 'student_surname'),
                'student_id': self.extract_field(text, 'student_id'),
                'examination_year': self.extract_field(text, 'examination_year'),
                'institution': self.extract_field(text, 'institution'),
                'certificate_type': self.extract_field(text, 'certificate_type'),
                'exam_board': self.extract_field(text, 'exam_board'),
                'grades_summary': self.extract_field(text, 'grades_summary'),
                'subjects_with_grades': self.extract_subjects_with_grades(text),
                'raw_text': text[:500] + '...' if len(text) > 500 else text,
                'extraction_method': 'tesseract_ocr',
                'ocr_confidence': ocr_confidence,
                'preprocessing': preprocess_metadata
            }
            
            # Calculate overall confidence
            data['confidence_score'] = self._calculate_overall_confidence(data, ocr_confidence)
            
            # Verify structure
            data['verification'] = self.verify_certificate_structure(data)
            
            # Clean up None values
            data = {k: v for k, v in data.items() if v is not None}
            
            return data
            
        except Exception as e:
            return {
                'error': str(e),
                'extraction_method': 'tesseract_ocr',
                'confidence_score': 0
            }
    
    def _clean_name(self, name: str) -> str:
        """Clean and format name"""
        # Remove extra spaces
        name = ' '.join(name.split())
        
        # Capitalize properly
        name = name.title()
        
        # Handle common prefixes
        prefixes = ['Mc', 'Mac', 'O\'', 'D\'']
        for prefix in prefixes:
            if prefix.lower() in name.lower():
                idx = name.lower().find(prefix.lower())
                if idx >= 0:
                    name = name[:idx] + prefix + name[idx + len(prefix):].capitalize()
        
        return name.strip()
    
    def _validate_year(self, year_str: str) -> Optional[int]:
        """Validate and convert year"""
        try:
            year = int(re.search(r'\d{4}', year_str).group())
            if 1900 <= year <= datetime.now().year + 5:
                return year
        except (ValueError, AttributeError):
            pass
        return None
    
    def _calculate_overall_confidence(self, data: Dict, ocr_confidence: float) -> float:
        """Calculate overall confidence score"""
        confidence = ocr_confidence * 0.4  # Base confidence from OCR
        
        # Add confidence from extracted fields
        required_fields_present = 0
        total_required = sum(1 for field, config in self.fields.items() 
                            if config.required)
        
        for field, config in self.fields.items():
            if config.required and data.get(field):
                required_fields_present += 1
        
        if total_required > 0:
            confidence += (required_fields_present / total_required) * 30
        
        # Add confidence from subjects
        if data.get('subjects_with_grades'):
            subject_count = len(data['subjects_with_grades'])
            confidence += min(subject_count * 5, 20)  # Max 20 from subjects
        
        # Add confidence from year validity
        if data.get('examination_year'):
            year = data['examination_year']
            if isinstance(year, int) and 2010 <= year <= datetime.now().year:
                confidence += 10
        
        return min(confidence, 100.0)
    
    def verify_certificate_structure(self, data: Dict) -> Dict:
        """Enhanced structure verification"""
        verification = {
            'is_valid': False,
            'missing_required': [],
            'issues': [],
            'warnings': [],
            'quality_score': 0
        }
        
        # Check required fields
        for field, config in self.fields.items():
            if config.required and not data.get(field):
                verification['missing_required'].append(field)
        
        # Check subjects
        subjects_data = data.get('subjects_with_grades', [])
        if len(subjects_data) < 3:
            verification['issues'].append('Insufficient subjects extracted')
        elif len(subjects_data) > 15:
            verification['warnings'].append('Unusually high number of subjects')
        
        # Check student name format
        if data.get('student_name'):
            name_parts = data['student_name'].split()
            if len(name_parts) < 2:
                verification['issues'].append('Student name may be incomplete')
        
        # Calculate quality score
        quality_score = 100
        
        # Deduct for missing required fields
        quality_score -= len(verification['missing_required']) * 20
        
        # Deduct for issues
        quality_score -= len(verification['issues']) * 15
        
        # Deduct for warnings
        quality_score -= len(verification['warnings']) * 5
        
        verification['quality_score'] = max(0, quality_score)
        verification['is_valid'] = (len(verification['missing_required']) == 0 
                                   and verification['quality_score'] >= 50)
        
        return verification
    
    def extract_multiple_certificates(self, image_paths: List[str]) -> List[Dict]:
        """Extract data from multiple certificates"""
        results = []
        for path in image_paths:
            try:
                result = self.extract_certificate_data(path)
                result['image_path'] = path
                results.append(result)
            except Exception as e:
                results.append({
                    'image_path': path,
                    'error': str(e),
                    'confidence_score': 0
                })
        return results


# Example usage with testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract data from certificate images')
    parser.add_argument('image_path', help='Path to certificate image')
    parser.add_argument('--output', '-o', help='Output JSON file path')
    parser.add_argument('--verbose', '-v', action='store_true', help='Show detailed output')
    
    args = parser.parse_args()
    
    # Initialize OCR
    ocr = CertificateOCR()
    
    # Extract data
    print(f"Processing: {args.image_path}")
    result = ocr.extract_certificate_data(args.image_path)
    
    # Display results
    if args.verbose:
        print(json.dumps(result, indent=2, default=str))
    else:
        # Show summary
        print(f"Confidence Score: {result.get('confidence_score', 0):.1f}%")
        print(f"Student: {result.get('student_name', 'N/A')}")
        print(f"Year: {result.get('examination_year', 'N/A')}")
        print(f"Subjects Found: {len(result.get('subjects_with_grades', []))}")
        print(f"Valid Structure: {result.get('verification', {}).get('is_valid', False)}")
    
    # Save to file if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"Results saved to: {args.output}")