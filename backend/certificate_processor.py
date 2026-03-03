#!/usr/bin/env python3
"""
LGCSE Certificate Processor with OCR and validation
Integrated with user authentication and payment tracking
"""

import hashlib
import json
import re
import uuid
from typing import Dict, Optional, List, Tuple, Any
from datetime import datetime
from PIL import Image
import pdf2image
import pytesseract
from fastapi import HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from models import User, Payment, VerificationLog, Certificate, Institution

class OCRDependencyError(Exception):
    """Custom exception for OCR dependency issues"""
    def __init__(self, message: str, hint: str = None):
        self.message = message
        self.hint = hint
        super().__init__(message)

class CertificateProcessor:
    def __init__(self, db: Session = None, current_user: User = None):
        """
        Initialize Certificate Processor with optional database session and user
        """
        self.db = db
        self.current_user = current_user
        
        # Check OCR dependencies
        try:
            # Test Tesseract availability
            pytesseract.get_tesseract_version()
        except Exception as e:
            raise OCRDependencyError(
                "OCR engine not available",
                "Please install Tesseract OCR: apt-get install tesseract-ocr"
            )
        
        # LGCSE specific keywords and patterns
        self.lgcse_keywords = [
            "LGCSE", "Lesotho General Certificate of Secondary Education",
            "Examination Council of Lesotho", "E.COL.", "LEVEL 1", "LEVEL 2", 
            "LEVEL 3", "LEVEL 4", "GRADE A*", "GRADE A", "GRADE B", "GRADE C",
            "GRADE D", "GRADE E", "GRADE F", "GRADE G", "SUBJECTS REPORTED",
            "CERTIFICATE NUMBER", "STUDENT NUMBER", "DATE OF BIRTH",
            "INSTITUTION", "DATE OF ISSUE", "CANDIDATE NUMBER", "SEAT NUMBER"
        ]
        
        # Institution patterns for LGCSE
        self.lgcse_institutions = [
            "HIGH SCHOOL", "SECONDARY SCHOOL", "COMMUNITY HIGH SCHOOL",
            "SENIOR SECONDARY", "JUNIOR SECONDARY", "COMPREHENSIVE SCHOOL"
        ]
        
        # Subject patterns for LGCSE
        self.lgcse_subjects = [
            "ENGLISH LANGUAGE", "ENGLISH LIT", "LITERATURE IN ENGLISH",
            "SESOTHO", "MATHEMATICS", "PHYSICAL SCIENCE", "BIOLOGY",
            "CHEMISTRY", "PHYSICS", "ACCOUNTING", "ECONOMICS", "BUSINESS STUDIES",
            "HISTORY", "GEOGRAPHY", "RELIGIOUS STUDIES", "DEVELOPMENT STUDIES",
            "AGRICULTURE", "COMPUTER STUDIES", "DESIGN AND TECHNOLOGY",
            "FASHION AND FABRICS", "FOOD AND NUTRITION", "ART", "MUSIC"
        ]
    
    def check_payment_required(self, user: User = None) -> Tuple[bool, Optional[Dict]]:
        """
        Check if user needs to make a payment for certificate verification
        Returns: (payment_required, payment_details)
        """
        if not user:
            return True, {
                "required": True,
                "message": "Please login to verify certificates",
                "amount": 5.00,
                "currency": "LSL"
            }
        
        # Check if user has recent successful payments (e.g., within last 24 hours)
        if self.db:
            recent_payment = self.db.query(Payment).filter(
                Payment.payer_user_id == user.id,
                Payment.status == "CONFIRMED",
                Payment.confirmed_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)
            ).first()
            
            if recent_payment:
                return False, {
                    "payment_id": recent_payment.id,
                    "message": "Payment already verified today"
                }
        
        return True, {
            "required": True,
            "amount": 5.00,
            "currency": "LSL",
            "message": "Payment required for certificate verification"
        }
    
    async def process_uploaded_file(self, file: UploadFile) -> Tuple[str, str]:
        """
        Process uploaded file and save temporarily
        Returns: (file_path, file_extension)
        """
        # Generate unique filename
        file_extension = file.filename.split('.')[-1].lower()
        file_path = f"/tmp/certificate_{uuid.uuid4()}.{file_extension}"
        
        # Save file
        content = await file.read()
        with open(file_path, 'wb') as f:
            f.write(content)
        
        return file_path, file_extension
    
    def extract_text_from_image(self, image_path: str) -> str:
        """Extract text from image using OCR"""
        try:
            # Configure Tesseract for better LGCSE certificate recognition
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789:.()/- '
            text = pytesseract.image_to_string(Image.open(image_path), config=custom_config)
            return text
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error extracting text from image: {str(e)}")
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using OCR"""
        try:
            images = pdf2image.convert_from_path(pdf_path)
            text = ""
            for image in images:
                # Configure Tesseract for better LGCSE certificate recognition
                custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789:.()/- '
                text += pytesseract.image_to_string(image, config=custom_config)
            return text
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error extracting text from PDF: {str(e)}")
    
    def validate_lgcse_certificate(self, text: str) -> tuple[bool, str, Dict]:
        """
        Validate if the document is an LGCSE certificate
        Returns: (is_valid, error_message, confidence_scores)
        """
        text_upper = text.upper()
        confidence = {
            "keyword_match": 0,
            "certificate_number": 0,
            "student_number": 0,
            "grading_system": 0,
            "institution_match": 0,
            "overall": 0
        }
        
        # Check for LGCSE keywords
        lgcse_matches = sum(1 for keyword in self.lgcse_keywords if keyword in text_upper)
        confidence["keyword_match"] = min(100, (lgcse_matches / len(self.lgcse_keywords)) * 100)
        
        if lgcse_matches < 5:
            return False, f"Document does not appear to be an LGCSE certificate. Found only {lgcse_matches} LGCSE keywords.", confidence
        
        # Check for certificate number pattern (LGCSE format)
        cert_patterns = [
            r'(?:CERTIFICATE\s+NUMBER|CERT\s+NO\.?|CERT\s+NUMBER)[:\s]*([A-Z]{2,3}[-]?\d{7,})',
            r'(?:CERTIFICATE\s+NUMBER|CERT\s+NO\.?)[:\s]*([A-Z]{2}\d{2,}/\d{4,})',
            r'(?:CERTIFICATE\s+NUMBER|CERT\s+NO\.?)[:\s]*([A-Z]{3}\d{6,})'
        ]
        
        cert_found = False
        for pattern in cert_patterns:
            if re.search(pattern, text_upper):
                cert_found = True
                confidence["certificate_number"] = 100
                break
        
        if not cert_found:
            confidence["certificate_number"] = 0
            return False, "No valid LGCSE certificate number found.", confidence
        
        # Check for student number pattern
        student_patterns = [
            r'(?:STUDENT\s+NUMBER|STUDENT\s+NO\.?|CANDIDATE\s+NUMBER)[:\s]*([A-Z]{2,}\d{6,})',
            r'(?:STUDENT\s+NUMBER|CANDIDATE\s+NUMBER)[:\s]*(\d{8,})'
        ]
        
        student_found = False
        for pattern in student_patterns:
            if re.search(pattern, text_upper):
                student_found = True
                confidence["student_number"] = 100
                break
        
        if not student_found:
            confidence["student_number"] = 50  # Partial confidence if not found
        
        # Check for LGCSE grading levels
        grading_patterns = [
            r'LEVEL\s+[1-4]',
            r'GRADE\s+[A-G](\*?)',
            r'A\*',
            r'SUBJECTS\s+REPORTED'
        ]
        
        grading_matches = sum(1 for pattern in grading_patterns if re.search(pattern, text_upper))
        confidence["grading_system"] = min(100, (grading_matches / len(grading_patterns)) * 100)
        
        # Check for institution
        institution_matches = sum(1 for inst in self.lgcse_institutions if inst in text_upper)
        confidence["institution_match"] = min(100, institution_matches * 20)  # 20% per match
        
        # Calculate overall confidence
        weights = {
            "keyword_match": 0.3,
            "certificate_number": 0.25,
            "student_number": 0.15,
            "grading_system": 0.2,
            "institution_match": 0.1
        }
        
        confidence["overall"] = sum(confidence[k] * weights[k] for k in weights.keys())
        
        is_valid = confidence["overall"] >= 60  # 60% confidence threshold
        
        if is_valid:
            return True, "Valid LGCSE certificate detected.", confidence
        else:
            return False, f"Low confidence in LGCSE certificate detection ({confidence['overall']:.1f}%). Please verify manually.", confidence
    
    def parse_certificate_text(self, text: str) -> dict:
        """Parse LGCSE certificate text to extract structured data"""
        text_upper = text.upper()
        text_lines = text.split('\n')
        
        # Initialize with default values
        data = {
            "student_name": "",
            "student_number": "",
            "certificate_numbers": [],
            "date_of_birth": "",
            "institution": "",
            "grades": {},
            "subjects": [],
            "date_of_issue": "",
            "subjects_reported": 0,
            "examination_year": "",
            "examination_session": "",
            "issuer_code": "ECOL",  # Default issuer
            "full_results": []
        }
        
        # Extract student name (multiple patterns for LGCSE certificates)
        name_patterns = [
            r'NAME[:\s]*([A-Z\s\']+?)(?:\n|STUDENT|CANDIDATE|DATE)',
            r'CANDIDATE[:\s]*([A-Z\s\']+?)(?:\n|STUDENT|DATE)',
            r'([A-Z\s\']{8,})\s+(?:STUDENT|CANDIDATE)\s+NUMBER',
            r'EXAMINATION\s+COUNCIL\s+OF\s+LESOTHO\s+([A-Z\s\']+?)\s+HAS',
            r'LESOTHO\s+GENERAL\s+CERTIFICATE\s+OF\s+SECONDARY\s+EDUCATION\s+([A-Z\s\']+?)\s+HAS'
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, text_upper)
            if match:
                name = match.group(1).strip()
                # Clean up name - remove extra spaces and capitalize properly
                name = ' '.join(name.split())
                name_parts = name.split()
                name = ' '.join([part.capitalize() for part in name_parts])
                data["student_name"] = name
                break
        
        # If name not found, try to find by common patterns in text lines
        if not data["student_name"]:
            for i, line in enumerate(text_lines):
                if "NAME" in line.upper() and i + 1 < len(text_lines):
                    possible_name = text_lines[i + 1].strip()
                    if len(possible_name.split()) >= 2:  # At least first and last name
                        data["student_name"] = possible_name
                        break
        
        # Extract student/candidate number
        student_patterns = [
            r'(?:STUDENT|CANDIDATE)\s+NUMBER[:\s]*([A-Z0-9]{6,15})',
            r'(?:STUDENT|CANDIDATE)\s+NO\.?[:\s]*([A-Z0-9]{6,15})',
            r'REGISTRATION\s+NUMBER[:\s]*([A-Z0-9]{6,15})'
        ]
        
        for pattern in student_patterns:
            match = re.search(pattern, text_upper)
            if match:
                data["student_number"] = match.group(1)
                break
        
        # Extract certificate numbers
        cert_patterns = [
            r'(?:CERTIFICATE\s+NUMBER|CERT\s+NO\.?|CERT\s+NUMBER)[:\s]*([A-Z]{2,3}[-]?\d{7,})',
            r'(?:CERTIFICATE\s+NUMBER|CERT\s+NO\.?)[:\s]*([A-Z]{2}\d{2,}/\d{4,})',
            r'(?:CERTIFICATE\s+NUMBER|CERT\s+NO\.?)[:\s]*([A-Z]{3}\d{6,})'
        ]
        
        for pattern in cert_patterns:
            cert_matches = re.findall(pattern, text_upper)
            if cert_matches:
                data["certificate_numbers"] = list(set(cert_matches))
                break
        
        # Extract date of birth
        dob_patterns = [
            r'DATE\s+OF\s+BIRTH[:\s]*(\d{1,2}\s+(?:JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER|\w+)\s+\d{4})',
            r'BORN[:\s]*(\d{1,2}\s+(?:JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER|\w+)\s+\d{4})',
            r'D\.O\.B\.[:\s]*(\d{1,2}\s+(?:JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER|\w+)\s+\d{4})',
            r'DATE\s+OF\s+BIRTH[:\s]*(\d{2}[/-]\d{2}[/-]\d{4})',
            r'BORN[:\s]*(\d{2}[/-]\d{2}[/-]\d{4})'
        ]
        
        for pattern in dob_patterns:
            match = re.search(pattern, text_upper)
            if match:
                data["date_of_birth"] = match.group(1)
                break
        
        # Extract institution/school
        institution_patterns = [
            r'INSTITUTION[:\s]*([A-Z\s]+?)(?:\n|DATE|STUDENT|CANDIDATE|SCHOOL)',
            r'SCHOOL[:\s]*([A-Z\s]+?)(?:\n|DATE|STUDENT|CANDIDATE)',
            r'([A-Z\s]+(?:HIGH|SECONDARY|COMMUNITY|COMPREHENSIVE)\s+SCHOOL)',
            r'ATTENDED[:\s]*([A-Z\s]+?)(?:\n|DATE|STUDENT)'
        ]
        
        for pattern in institution_patterns:
            match = re.search(pattern, text_upper)
            if match:
                institution = match.group(1).strip()
                # Clean up institution name
                institution = ' '.join(institution.split())
                data["institution"] = institution.title()
                break
        
        # Extract subjects and grades
        subject_grades = {}
        full_results = []
        
        # Look for subject listings
        in_results_section = False
        for line in text_lines:
            line_upper = line.upper().strip()
            
            # Check if we're in the results section
            if any(keyword in line_upper for keyword in ["SUBJECTS REPORTED", "RESULTS", "GRADES", "PERFORMANCE"]):
                in_results_section = True
                continue
            
            if in_results_section:
                # Try to find subject-grade pairs
                for subject in self.lgcse_subjects:
                    if subject in line_upper:
                        # Look for grade in the same line
                        grade_match = re.search(r'([A-G]\*?)', line_upper)
                        if grade_match:
                            grade = grade_match.group(1)
                            subject_grades[subject.title()] = {
                                "grade": grade,
                                "level": self._extract_level(line_upper)
                            }
                            
                            full_results.append({
                                "subject": subject.title(),
                                "grade": grade,
                                "level": self._extract_level(line_upper)
                            })
                            break
        
        data["grades"] = subject_grades
        data["full_results"] = full_results
        data["subjects"] = list(subject_grades.keys())
        
        # Extract date of issue
        issue_patterns = [
            r'DATE\s+OF\s+ISSUE[:\s]*(\d{1,2}\s+(?:JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER|\w+)\s+\d{4})',
            r'ISSUED[:\s]*(\d{1,2}\s+(?:JANUARY|FEBRUARY|MARCH|APRIL|MAY|JUNE|JULY|AUGUST|SEPTEMBER|OCTOBER|NOVEMBER|DECEMBER|\w+)\s+\d{4})',
            r'DATE\s+OF\s+ISSUE[:\s]*(\d{2}[/-]\d{2}[/-]\d{4})',
            r'ISSUED[:\s]*(\d{2}[/-]\d{2}[/-]\d{4})'
        ]
        
        for pattern in issue_patterns:
            match = re.search(pattern, text_upper)
            if match:
                data["date_of_issue"] = match.group(1)
                # Extract examination year from issue date
                year_match = re.search(r'(\d{4})', match.group(1))
                if year_match:
                    data["examination_year"] = year_match.group(1)
                break
        
        # Extract examination session
        session_match = re.search(r'(NOVEMBER|MAY|JUNE|OCTOBER|DECEMBER)\s+(\d{4})', text_upper)
        if session_match:
            data["examination_session"] = f"{session_match.group(1)} {session_match.group(2)}"
            if not data["examination_year"]:
                data["examination_year"] = session_match.group(2)
        
        # Count subjects reported
        subjects_reported_match = re.search(r'SUBJECTS\s+REPORTED[:\s]*(\d+)', text_upper)
        if subjects_reported_match:
            data["subjects_reported"] = int(subjects_reported_match.group(1))
        else:
            data["subjects_reported"] = len(data["grades"])
        
        return data
    
    def _extract_level(self, text: str) -> str:
        """Extract level from text"""
        level_match = re.search(r'LEVEL\s+([1-4])', text.upper())
        if level_match:
            return f"LEVEL {level_match.group(1)}"
        return ""
    
    def generate_certificate_hash(self, certificate_data: dict) -> str:
        """Generate SHA-256 hash from LGCSE certificate data"""
        # Create a consistent string representation for LGCSE certificates
        data_string = (
            f"{certificate_data['student_name']}|"
            f"{certificate_data['student_number']}|"
            f"{'|'.join(sorted(certificate_data['certificate_numbers']))}|"
            f"{certificate_data['date_of_birth']}|"
            f"{certificate_data['institution']}|"
            f"{certificate_data['examination_year']}|"
            f"{certificate_data['examination_session']}|"
            f"{json.dumps(certificate_data['grades'], sort_keys=True)}"
        )
        return hashlib.sha256(data_string.encode('utf-8')).hexdigest()
    
    def process_certificate_file(self, file_path: str, user: User = None) -> dict:
        """Process certificate file and return structured data for form auto-fill"""
        # Extract text based on file type
        if file_path.lower().endswith('.pdf'):
            text = self.extract_text_from_pdf(file_path)
        else:
            text = self.extract_text_from_image(file_path)
        
        # Parse certificate data
        certificate_data = self.parse_certificate_text(text)
        
        # Convert to form-friendly format
        return {
            "student_name": certificate_data.get("student_name", ""),
            "student_id": certificate_data.get("student_number", ""),
            "institution": certificate_data.get("institution", ""),
            "issue_date": certificate_data.get("date_of_issue", ""),
            "examination_year": certificate_data.get("examination_year", ""),
            "examination_session": certificate_data.get("examination_session", ""),
            "subjects": certificate_data.get("subjects", []),
            "full_results": certificate_data.get("full_results", []),
            "certificate_numbers": certificate_data.get("certificate_numbers", [])
        }
    
    def _extract_overall_grade(self, grades: dict) -> str:
        """Extract overall grade from grades dictionary"""
        if not grades:
            return ""
        
        # Count grade frequencies
        grade_counts = {}
        for subject_data in grades.values():
            grade = subject_data.get("grade", "")
            grade_counts[grade] = grade_counts.get(grade, 0) + 1
        
        # Return most common grade
        if grade_counts:
            return max(grade_counts, key=grade_counts.get)
        return ""
    
    async def process_certificate_with_payment(
        self, 
        file: UploadFile, 
        user: User,
        db: Session
    ) -> dict:
        """
        Process certificate with payment verification
        """
        # Check payment requirement
        payment_required, payment_info = self.check_payment_required(user)
        
        if payment_required:
            # Check if user has any pending payment
            pending_payment = db.query(Payment).filter(
                Payment.payer_user_id == user.id,
                Payment.status == "PENDING"
            ).first()
            
            if pending_payment:
                raise HTTPException(
                    status_code=402,
                    detail={
                        "message": "You have a pending payment. Please complete it first.",
                        "payment_id": pending_payment.id,
                        "amount": pending_payment.amount,
                        "currency": pending_payment.currency
                    }
                )
            
            raise HTTPException(
                status_code=402,
                detail={
                    "message": "Payment required for certificate verification",
                    "amount": payment_info.get("amount", 5.00),
                    "currency": payment_info.get("currency", "LSL")
                }
            )
        
        # Process the certificate
        return await self.process_certificate(file, user, db)
    
    async def process_certificate(
        self, 
        file: UploadFile,
        user: User = None,
        db: Session = None
    ) -> dict:
        """
        Process certificate file and return structured data with validation
        Integrated with database for logging and tracking
        """
        # Save uploaded file temporarily
        file_path, file_extension = await self.process_uploaded_file(file)
        
        try:
            # Extract text based on file type
            if file_extension == 'pdf':
                text = self.extract_text_from_pdf(file_path)
            else:
                text = self.extract_text_from_image(file_path)
            
            # Validate if it's an LGCSE certificate
            is_valid, validation_message, confidence = self.validate_lgcse_certificate(text)
            
            # Parse certificate data
            certificate_data = self.parse_certificate_text(text)
            
            # Generate hash
            certificate_hash = self.generate_certificate_hash(certificate_data)
            
            # Check if certificate exists in database
            existing_certificate = None
            if db:
                existing_certificate = db.query(Certificate).filter(
                    Certificate.hash == certificate_hash
                ).first()
            
            # Log verification attempt if user is authenticated
            if db and user:
                verification_log = VerificationLog(
                    id=str(uuid.uuid4()),
                    hash=certificate_hash,
                    verifier_code=user.institution_code if user.institution_code else "PUBLIC",
                    certificate_id=existing_certificate.id if existing_certificate else None,
                    verified=is_valid and confidence["overall"] >= 60,
                    message=validation_message,
                    issuer_code=existing_certificate.issuer_code if existing_certificate else None,
                    created_at=datetime.utcnow()
                )
                db.add(verification_log)
                db.commit()
            
            return {
                "certificate_data": certificate_data,
                "certificate_hash": certificate_hash,
                "validation": {
                    "is_lgcse": is_valid,
                    "confidence": confidence,
                    "message": validation_message,
                    "subjects_found": len(certificate_data["grades"]),
                    "certificate_numbers_found": len(certificate_data["certificate_numbers"]),
                    "in_database": existing_certificate is not None
                }
            }
            
        finally:
            # Clean up temporary file
            import os
            if os.path.exists(file_path):
                os.remove(file_path)