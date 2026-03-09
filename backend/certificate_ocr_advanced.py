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
    Advanced OCR-based certificate data extraction for LGCSE certificates
    """
    
    def __init__(self):
        # Set Tesseract path if needed
        self.tesseract_path = '/usr/bin/tesseract'
        if os.path.exists(self.tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_path
        
        # LGCSE-specific patterns for Lesotho certificates
        self.lgcse_patterns = {
            # Student identification
            'student_name': [
                r'(?:Name|Student Name|Candidate Name):\s*([A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
                r'Name:\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
                r'Candidate:\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
                r'To Whom It May Concern:\s*([A-Z][a-z]+\s+[A-Z][a-z]+)'
            ],
            'student_surname': [
                r'(?:Surname|Last Name|Family Name):\s*([A-Z][a-z]+)',
                r'Surname:\s*([A-Z][a-z]+)',
                r'([A-Z][a-z]+),\s+[A-Z][a-z]+\s+[A-Z]'
            ],
            'student_id': [
                r'(?:Student ID|Candidate No|Examination No|Centre No):\s*([A-Z0-9]{6,12})',
                r'ID:\s*([A-Z0-9]{6,12})',
                r'No\.:\s*([A-Z0-9]{6,12})',
                r'Centre\s+Number:\s*([A-Z0-9]{6,12})'
            ],
            
            # Examination details
            'examination_year': [
                r'(?:Year|Examination Year|Date of Examination):\s*(20\d{2})',
                r'(?:LGCSE|Cambridge IGCSE)\s+(20\d{2})',
                r'Examination\s+Year:\s*(20\d{2})',
                r'(20\d{2})\s*Examination'
            ],
            'examination_session': [
                r'(?:Session|Term):\s*(May|June|October|November|Winter|Summer)',
                r'(May|June|October|November)\s+20\d{2}',
                r'(Winter|Summer)\s+Session'
            ],
            
            # Subjects and grades
            'subjects': [
                r'(?:Subjects|Courses|Subjects Taken):\s*([A-Za-z,\s]+)',
                r'Subjects:\s*([A-Z][a-z]+(?:,\s*[A-Z][a-z]+)*)',
                r'(Mathematics|English Language|English Literature|Biology|Chemistry|Physics|Combined Science|History|Geography|Economics|Business Studies|Computer Studies|Information Technology|Art & Design|Music|Physical Education|Religious Studies|French|German|Spanish|Accounting|Agriculture|Food Science|Technical Drawing)'
            ],
            'grades': [
                r'(?:Grade|Result|Achievement):\s*([A\*-F\+]{1,3})',
                r'([A\*\+]{1,2}|[A-F][\+]?)\s+(?:Mathematics|English|Biology|Chemistry|Physics)',
                r'Grade\s+([A\*-F\+]{1,3})'
            ],
            
            # Institution information
            'institution': [
                r'(?:School|Institution|College|Centre):\s*([A-Za-z\s]+(?:High School|College|Institution|Centre))',
                r'([A-Za-z\s]+(?:High School|College|Institution|Centre))',
                r'Examination\s+Centre:\s*([A-Za-z\s]+)'
            ],
            'centre_number': [
                r'(?:Centre Number|School Code|Institution Code):\s*([A-Z0-9]{4,8})',
                r'Centre\s+No\.:\s*([A-Z0-9]{4,8})'
            ],
            
            # Certificate details
            'certificate_number': [
                r'(?:Certificate No|Serial No|Reference No):\s*([A-Z0-9]{8,20})',
                r'Certificate\s+Number:\s*([A-Z0-9]{8,20})',
                r'Ref\.:\s*([A-Z0-9]{8,20})'
            ],
            'issue_date': [
                r'(?:Issue Date|Date Issued|Awarded):\s*(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+20\d{2})',
                r'(?:Date|Awarded):\s*(\d{1,2}\s+\w+\s+20\d{2})',
                r'(\d{1,2}/\d{1,2}/20\d{2})'
            ],
            
            # Certificate type
            'certificate_type': [
                r'(?:General Certificate of Secondary Education|LGCSE|Cambridge IGCSE|Ordinary Level)',
                r'(LGCSE|Cambridge IGCSE|O-Level)',
                r'General Certificate'
            ],
            
            # Examination board
            'examination_board': [
                r'(?:Examination Council|Board|Authority):\s*(Examination Council of Lesotho|Cambridge International Examinations|Ecol)',
                r'(Examination Council of Lesotho|Cambridge|Ecol)',
                r'Issued by:\s*([A-Za-z\s]+)'
            ]
        }
    
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """
        Advanced image preprocessing for better OCR accuracy
        """
        try:
            # Read image
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not read image: {image_path}")
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Noise reduction
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(denoised)
            
            # Adaptive thresholding
            binary = cv2.adaptiveThreshold(
                enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                cv2.THRESH_BINARY, 11, 2
            )
            
            # Morphological operations
            kernel = np.ones((2,2), np.uint8)
            processed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
            
            return processed
            
        except Exception as e:
            raise Exception(f"Image preprocessing failed: {str(e)}")
    
    def extract_text(self, image_path: str) -> str:
        """
        Extract text using multiple Tesseract configurations
        """
        try:
            # Preprocess image
            processed_img = self.preprocess_image(image_path)
            
            # Convert to PIL Image
            pil_img = Image.fromarray(processed_img)
            
            # Multiple configurations for better results
            configs = [
                r'--oem 3 --psm 6 -l eng',  # Default
                r'--oem 3 --psm 4 -l eng',  # Single column
                r'--oem 3 --psm 1 -l eng',  # Sparse text
            ]
            
            all_texts = []
            for config in configs:
                try:
                    text = pytesseract.image_to_string(pil_img, config=config)
                    if text.strip():
                        all_texts.append(text.strip())
                except:
                    continue
            
            # Combine and deduplicate
            if all_texts:
                # Use the longest text as primary
                primary_text = max(all_texts, key=len)
                return primary_text
            else:
                # Fallback to default config
                return pytesseract.image_to_string(pil_img, config='--oem 3 --psm 6 -l eng').strip()
                
        except Exception as e:
            raise Exception(f"OCR extraction failed: {str(e)}")
    
    def extract_field(self, text: str, field_name: str) -> Optional[str]:
        """
        Extract specific field using LGCSE-specific patterns
        """
        if field_name not in self.lgcse_patterns:
            return None
        
        patterns = self.lgcse_patterns[field_name]
        
        for pattern in patterns:
            try:
                match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
                if match:
                    # For patterns with groups, return the most specific match
                    if match.groups():
                        return match.groups()[-1].strip()
                    else:
                        return match.group(0).strip()
            except:
                continue
        
        return None
    
    def extract_subjects_and_grades(self, text: str) -> List[Dict]:
        """
        Extract subjects with their corresponding grades
        """
        subjects_grades = []
        
        # Common LGCSE subjects
        lgcse_subjects = [
            'Mathematics', 'English Language', 'English Literature',
            'Biology', 'Chemistry', 'Physics', 'Combined Science',
            'History', 'Geography', 'Economics', 'Business Studies',
            'Computer Studies', 'Information Technology',
            'Art & Design', 'Music', 'Physical Education',
            'Religious Studies', 'French', 'German', 'Spanish',
            'Accounting', 'Agriculture', 'Food Science', 'Technical Drawing'
        ]
        
        # Find subjects in text
        for subject in lgcse_subjects:
            if subject.lower() in text.lower():
                # Look for grade near the subject
                subject_pattern = rf'{subject}[^A-F]*([A\*\+]*[A-F][A\*\+]*)'
                grade_match = re.search(subject_pattern, text, re.IGNORECASE)
                
                grade = grade_match.group(1) if grade_match else None
                
                subjects_grades.append({
                    'subject': subject,
                    'grade': grade,
                    'level': 'O-Level' if 'O-Level' in text or 'LGCSE' in text else 'Unknown'
                })
        
        return subjects_grades
    
    def extract_certificate_data(self, image_path: str) -> Dict:
        """
        Extract comprehensive certificate data from LGCSE certificate
        """
        try:
            # Extract text
            text = self.extract_text(image_path)
            
            # Extract all fields
            data = {
                # Student information
                'student_name': self.extract_field(text, 'student_name'),
                'student_surname': self.extract_field(text, 'student_surname'),
                'student_id': self.extract_field(text, 'student_id'),
                
                # Examination details
                'examination_year': self.extract_field(text, 'examination_year'),
                'examination_session': self.extract_field(text, 'examination_session'),
                'certificate_type': self.extract_field(text, 'certificate_type'),
                'examination_board': self.extract_field(text, 'examination_board'),
                
                # Institution information
                'institution': self.extract_field(text, 'institution'),
                'centre_number': self.extract_field(text, 'centre_number'),
                
                # Certificate details
                'certificate_number': self.extract_field(text, 'certificate_number'),
                'issue_date': self.extract_field(text, 'issue_date'),
                
                # Subjects and grades
                'subjects_grades': self.extract_subjects_and_grades(text),
                
                # Raw data
                'raw_text': text,
                'extraction_method': 'lgcse_tesseract_ocr',
                'confidence_score': self._calculate_confidence(text, data)
            }
            
            # Clean and validate data
            data = self._clean_extracted_data(data)
            
            return data
            
        except Exception as e:
            return {
                'error': str(e),
                'extraction_method': 'lgcse_tesseract_ocr',
                'raw_text': '',
                'confidence_score': 0
            }
    
    def _calculate_confidence(self, text: str, data: Dict) -> float:
        """
        Calculate confidence score based on LGCSE certificate characteristics
        """
        if not text:
            return 0.0
        
        confidence = 0.0
        
        # Check for LGCSE-specific keywords
        lgcse_keywords = [
            'LGCSE', 'General Certificate of Secondary Education',
            'Examination Council of Lesotho', 'ECOL', 'Cambridge IGCSE',
            'certificate', 'examination', 'candidate', 'subject', 'grade'
        ]
        
        keyword_count = sum(1 for keyword in lgcse_keywords 
                          if keyword.lower() in text.lower())
        confidence += (keyword_count / len(lgcse_keywords)) * 30
        
        # Check for required fields
        required_fields = ['student_name', 'examination_year', 'subjects_grades']
        present_fields = sum(1 for field in required_fields if data.get(field))
        confidence += (present_fields / len(required_fields)) * 25
        
        # Check for valid year
        if data.get('examination_year'):
            try:
                year = int(data['examination_year'])
                if 2000 <= year <= 2030:
                    confidence += 15
            except:
                pass
        
        # Check for subjects
        subjects = data.get('subjects_grades', [])
        if len(subjects) >= 5:
            confidence += 15
        elif len(subjects) >= 3:
            confidence += 10
        
        # Check for institution
        if data.get('institution'):
            confidence += 10
        
        # Text quality
        if len(text) > 200:
            confidence += 5
        
        return min(confidence, 100.0)
    
    def _clean_extracted_data(self, data: Dict) -> Dict:
        """
        Clean and validate extracted certificate data
        """
        # Clean student name
        if data.get('student_name'):
            name = data['student_name'].title().strip()
            # Remove extra spaces
            data['student_name'] = re.sub(r'\s+', ' ', name)
        
        # Clean student surname
        if data.get('student_surname'):
            surname = data['student_surname'].title().strip()
            data['student_surname'] = re.sub(r'\s+', ' ', surname)
        
        # Clean student ID
        if data.get('student_id'):
            data['student_id'] = data['student_id'].upper().strip()
        
        # Clean examination year
        if data.get('examination_year'):
            try:
                year = int(data['examination_year'])
                if 2000 <= year <= 2030:
                    data['examination_year'] = year
                else:
                    data['examination_year'] = None
            except ValueError:
                data['examination_year'] = None
        
        # Clean institution
        if data.get('institution'):
            institution = data['institution'].title().strip()
            data['institution'] = re.sub(r'\s+', ' ', institution)
        
        # Clean certificate number
        if data.get('certificate_number'):
            data['certificate_number'] = data['certificate_number'].upper().strip()
        
        # Parse issue date
        if data.get('issue_date'):
            try:
                # Try different date formats
                date_formats = ['%d %B %Y', '%d/%m/%Y', '%d-%m-%Y']
                for fmt in date_formats:
                    try:
                        from datetime import datetime
                        parsed_date = datetime.strptime(data['issue_date'], fmt)
                        data['issue_date'] = parsed_date.strftime('%Y-%m-%d')
                        break
                    except:
                        continue
            except:
                pass
        
        # Clean subjects and grades
        if data.get('subjects_grades'):
            cleaned_subjects = []
            for subject_grade in data['subjects_grades']:
                if subject_grade.get('subject'):
                    cleaned_subjects.append({
                        'subject': subject_grade['subject'].title().strip(),
                        'grade': subject_grade.get('grade', '').upper().strip() if subject_grade.get('grade') else None,
                        'level': subject_grade.get('level', 'O-Level')
                    })
            data['subjects_grades'] = cleaned_subjects
        
        return data
    
    def verify_lgcse_structure(self, data: Dict) -> Dict:
        """
        Verify if extracted data matches LGCSE certificate structure
        """
        verification = {
            'is_valid_lgcse': False,
            'missing_required_fields': [],
            'confidence_score': data.get('confidence_score', 0),
            'validation_details': {},
            'lgcse_compliance': {}
        }
        
        # Required LGCSE fields
        required_fields = ['student_name', 'examination_year', 'subjects_grades']
        
        for field in required_fields:
            if not data.get(field):
                verification['missing_required_fields'].append(field)
                verification['validation_details'][field] = 'Missing required field'
            else:
                verification['validation_details'][field] = 'Present'
        
        # LGCSE-specific checks
        lgcse_checks = {}
        
        # Check certificate type
        if data.get('certificate_type'):
            cert_type = data['certificate_type'].lower()
            if any(lgcse_type in cert_type for lgcse_type in ['lgcse', 'cambridge igcse', 'general certificate']):
                lgcse_checks['certificate_type'] = 'Valid LGCSE certificate type'
            else:
                lgcse_checks['certificate_type'] = 'Unusual certificate type'
        else:
            lgcse_checks['certificate_type'] = 'Certificate type not found'
        
        # Check examination board
        if data.get('examination_board'):
            board = data['examination_board'].lower()
            if any(ecol_board in board for ecol_board in ['examination council of lesotho', 'ecol', 'cambridge']):
                lgcse_checks['examination_board'] = 'Valid examination board'
            else:
                lgcse_checks['examination_board'] = 'Unusual examination board'
        else:
            lgcse_checks['examination_board'] = 'Examination board not found'
        
        # Check subjects
        subjects = data.get('subjects_grades', [])
        if len(subjects) >= 5:
            lgcse_checks['subjects_count'] = 'Adequate number of subjects'
        elif len(subjects) >= 3:
            lgcse_checks['subjects_count'] = 'Minimum subjects met'
        else:
            lgcse_checks['subjects_count'] = 'Insufficient subjects'
        
        # Check grades
        graded_subjects = [s for s in subjects if s.get('grade')]
        if len(graded_subjects) >= 3:
            lgcse_checks['grades'] = 'Adequate grade information'
        else:
            lgcse_checks['grades'] = 'Limited grade information'
        
        verification['lgcse_compliance'] = lgcse_checks
        
        # Overall validation
        if (len(verification['missing_required_fields']) == 0 and 
            data.get('confidence_score', 0) > 60 and
            len(subjects) >= 3):
            verification['is_valid_lgcse'] = True
        
        return verification

# Example usage
if __name__ == "__main__":
    ocr = CertificateOCR()
    
    # Test with an LGCSE certificate image
    image_path = "lgcse_certificate_sample.jpg"
    if os.path.exists(image_path):
        result = ocr.extract_certificate_data(image_path)
        print(json.dumps(result, indent=2))
        
        # Verify LGCSE structure
        verification = ocr.verify_lgcse_structure(result)
        print("\n=== LGCSE Verification ===")
        print(json.dumps(verification, indent=2))
    else:
        print(f"LGCSE certificate image not found: {image_path}")
        print("Please provide a real LGCSE certificate image for testing.")
