#!/usr/bin/env python3
"""
Test script for certificate OCR and hash generation
"""

import hashlib
import json
import pytesseract
from PIL import Image
import pdf2image
import re

class CertificateProcessor:
    def __init__(self):
        pass
    
    def extract_text_from_image(self, image_path: str) -> str:
        """Extract text from image using OCR"""
        try:
            text = pytesseract.image_to_string(Image.open(image_path))
            return text
        except Exception as e:
            print(f"Error extracting text: {e}")
            return ""
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using OCR"""
        try:
            images = pdf2image.convert_from_path(pdf_path)
            text = ""
            for image in images:
                text += pytesseract.image_to_string(image)
            return text
        except Exception as e:
            print(f"Error extracting PDF text: {e}")
            return ""
    
    def parse_certificate_text(self, text: str) -> dict:
        """Parse certificate text to extract structured data"""
        data = {
            "student_name": "Test Student",
            "student_number": "TEST123456",
            "certificate_numbers": ["TEST001", "TEST002"],
            "date_of_birth": "01 January 2000",
            "institution": "Test University",
            "grades": {"MAT": {"grade": "A", "level": "LEVEL 2"}},
            "date_of_issue": "01 July 2023",
            "subjects_reported": 7
        }
        
        # Simple parsing logic - you can expand this based on actual certificate format
        if "NAME:" in text:
            lines = text.split('\n')
            for line in lines:
                if "NAME:" in line:
                    data["student_name"] = line.split("NAME:")[1].strip()
                elif "STUDENT NUMBER:" in line:
                    data["student_number"] = line.split("STUDENT NUMBER:")[1].strip()
                elif "INSTITUTION:" in line:
                    data["institution"] = line.split("INSTITUTION:")[1].strip()
        
        return data
    
    def generate_certificate_hash(self, certificate_data: dict) -> str:
        """Generate SHA-256 hash from certificate data"""
        # Create a consistent string representation
        data_string = (
            f"{certificate_data['student_name']}|"
            f"{certificate_data['student_number']}|"
            f"{'|'.join(sorted(certificate_data['certificate_numbers']))}|"
            f"{certificate_data['date_of_birth']}|"
            f"{json.dumps(certificate_data['grades'], sort_keys=True)}|"
            f"{certificate_data['institution']}"
        )
        return hashlib.sha256(data_string.encode('utf-8')).hexdigest()

def main():
    """Test the certificate processor"""
    print("🔍 Testing Certificate Processor")
    print("=" * 50)
    
    processor = CertificateProcessor()
    
    # Test with sample data
    test_data = {
        "student_name": "BOKANG JOHANNES LETSAPO",
        "student_number": "LS675/140453626",
        "certificate_numbers": ["LN2100014388", "LM2100099810"],
        "date_of_birth": "03 March 2001",
        "institution": "LANCER'S GAP HIGH SCHOOL BEREA",
        "grades": {
            "MAT": {"grade": "D", "level": "LEVEL 2"},
            "ENG": {"grade": "D", "level": "LEVEL 2"},
            "SET": {"grade": "D", "level": "LEVEL 2"},
            "SES": {"grade": "D", "level": "LEVEL 2"},
            "SCI": {"grade": "D", "level": "LEVEL 2"},
            "AGR": {"grade": "D", "level": "LEVEL 2"},
            "ICT": {"grade": "D", "level": "LEVEL 2"}
        },
        "date_of_issue": "19 July 2022",
        "subjects_reported": 7
    }
    
    # Generate hash
    certificate_hash = processor.generate_certificate_hash(test_data)
    
    print(f"📝 Student: {test_data['student_name']}")
    print(f"📚 Student Number: {test_data['student_number']}")
    print(f"🎓 Institution: {test_data['institution']}")
    print(f"📅 Issue Date: {test_data['date_of_issue']}")
    print(f"📊 Subjects: {test_data['subjects_reported']} subjects")
    print("\n🔐 Generated Certificate Hash:")
    print(f"Hash: {certificate_hash}")
    print(f"Hash Length: {len(certificate_hash)} characters")
    print(f"Hash Type: SHA-256")
    
    # Test consistency
    hash2 = processor.generate_certificate_hash(test_data)
    print(f"\n✅ Hash consistency check: {certificate_hash == hash2}")
    
    # Test with modified data
    modified_data = test_data.copy()
    modified_data["student_name"] = "DIFFERENT NAME"
    different_hash = processor.generate_certificate_hash(modified_data)
    print(f"✅ Different data produces different hash: {certificate_hash != different_hash}")

if __name__ == "__main__":
    main()
