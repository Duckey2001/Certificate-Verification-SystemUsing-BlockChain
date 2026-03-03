#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.certificate_processor import CertificateProcessor

def main():
    """Test certificate hash generation"""
    print("🔍 Testing Certificate Hash Generation")
    print("=" * 50)
    
    processor = CertificateProcessor()
    
    # Test data from your certificates
    test_data = {
        "student_name": "BOKANG JOHANNES LETSAPO",
        "student_number": "LS675/140453626",
        "certificate_numbers": ["LN2100014388", "LM2100099810"],
        "date_of_birth": "03 March 2001",
        "institution": "LANCER'S GAP HIGH SCHOOL BEREA",
        "grades": {
            "History": {"level": "LGCSEC", "grade": "A(a)"},
            "Sesotho": {"level": "LGCSEC", "grade": "A(a)"},
            "Agriculture": {"level": "LGCSEC", "grade": "B(b)"},
            "Physical Science": {"level": "LGCSEC", "grade": "B(b)"},
            "Mathematics": {"level": "LGCSEC", "grade": "C(c)"},
            "English Language": {"level": "LGCSEC", "grade": "D(d)"},
            "Business Studies": {"level": "IGCSEC", "grade": "C(c)"}
        },
        "date_of_issue": "19 July 2022",
        "subjects_reported": 7
    }
    
    print("📝 Certificate Data:")
    print(f"• Student: {test_data['student_name']}")
    print(f"• Student Number: {test_data['student_number']}")
    print(f"• Certificate Numbers: {', '.join(test_data['certificate_numbers'])}")
    print(f"• Institution: {test_data['institution']}")
    print(f"• Subjects: {len(test_data['grades'])} subjects")
    print(f"• Date of Issue: {test_data['date_of_issue']}")
    
    # Generate hash
    certificate_hash = processor.generate_certificate_hash(test_data)
    
    print(f"\n🔐 Generated Certificate Hash:")
    print(f"Hash: {certificate_hash}")
    print(f"Hash Length: {len(certificate_hash)} characters")
    print(f"Hash Type: SHA-256")
    
    # Test that same data produces same hash
    same_hash = processor.generate_certificate_hash(test_data)
    print(f"\n✅ Hash consistency check: {certificate_hash == same_hash}")
    
    # Test with modified data
    modified_data = test_data.copy()
    modified_data["student_name"] = "MODIFIED NAME"
    modified_hash = processor.generate_certificate_hash(modified_data)
    print(f"✅ Different data produces different hash: {certificate_hash != modified_hash}")
    
    return certificate_hash

if __name__ == "__main__":
    main()
