#!/usr/bin/env python3
"""
Create sample certificate images for testing blockchain upload
"""

import os
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
import textwrap

def create_sample_certificate(student_name, student_id, year, subjects, output_path):
    """Create a sample LGCSE certificate image"""
    
    # Create image (A4 size at 300 DPI)
    width, height = 2480, 3508
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a nice font, fallback to default
    try:
        title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
        header_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 36)
        normal_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    except:
        title_font = ImageFont.load_default()
        header_font = ImageFont.load_default()
        normal_font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Draw border
    draw.rectangle([50, 50, width-50, height-50], outline='#2C3E50', width=3)
    draw.rectangle([70, 70, width-70, height-70], outline='#3498DB', width=1)
    
    # Draw header
    draw.text((width//2, 150), "EXAMINATION COUNCIL OF LESOTHO", 
              fill='#2C3E50', font=title_font, anchor='mt')
    draw.text((width//2, 220), "LESOTHO GENERAL CERTIFICATE OF SECONDARY EDUCATION", 
              fill='#34495E', font=header_font, anchor='mt')
    
    # Draw decorative line
    draw.line([200, 280, width-200, 280], fill='#3498DB', width=2)
    
    # Certificate text
    cert_text = "This is to certify that"
    draw.text((width//2, 350), cert_text, fill='#2C3E50', font=normal_font, anchor='mt')
    
    # Student name (prominent)
    draw.text((width//2, 420), student_name.upper(), 
              fill='#2C3E50', font=title_font, anchor='mt')
    
    # Student ID
    id_text = f"Student ID: {student_id}"
    draw.text((width//2, 500), id_text, fill='#34495E', font=normal_font, anchor='mt')
    
    # Examination details
    exam_text = f"has successfully completed the LGCSE examination in {year}"
    draw.text((width//2, 580), exam_text, fill='#2C3E50', font=normal_font, anchor='mt')
    
    # Subjects section
    draw.text((300, 700), "SUBJECTS AND GRADES:", fill='#2C3E50', font=header_font, anchor='lt')
    
    # Draw subjects
    y_pos = 760
    for subject, grade in subjects:
        subject_text = f"{subject}: {grade}"
        draw.text((350, y_pos), subject_text, fill='#34495E', font=normal_font, anchor='lt')
        y_pos += 40
    
    # Credits
    credits = len(subjects) * 2
    credits_text = f"Total Credits: {credits}"
    draw.text((350, y_pos + 40), credits_text, fill='#2C3E50', font=normal_font, anchor='lt')
    
    # Issue date
    issue_date = datetime.now().strftime("%d %B %Y")
    date_text = f"Issued on: {issue_date}"
    draw.text((width//2, height - 400), date_text, fill='#34495E', font=normal_font, anchor='mt')
    
    # Signature lines
    draw.line([400, height - 250, 800, height - 250], fill='#2C3E50', width=1)
    draw.text((600, height - 230), "Chief Examiner", fill='#7F8C8D', font=small_font, anchor='mt')
    
    draw.line([width - 800, height - 250, width - 400, height - 250], fill='#2C3E50', width=1)
    draw.text((width - 600, height - 230), "Director", fill='#7F8C8D', font=small_font, anchor='mt')
    
    # Certificate number
    cert_number = f"LGCSE/{year}/{student_id[-4:]}"
    draw.text((width - 200, height - 100), f"No: {cert_number}", 
              fill='#95A5A6', font=small_font, anchor='rt')
    
    # Watermark/background pattern
    for i in range(0, width, 100):
        for j in range(0, height, 100):
            draw.text((i+50, j+50), "ECL", fill='#E8F4F8', font=small_font, anchor='mt')
    
    # Save image
    img.save(output_path, 'JPEG', quality=95)
    print(f"✅ Created certificate: {output_path}")

def create_sample_certificates():
    """Create multiple sample certificates for testing"""
    
    # Sample student data
    students = [
        {
            "name": "Mokhehi Moletsane",
            "id": "STU2024001",
            "year": 2024,
            "subjects": [
                ("Mathematics", "A"),
                ("English Language", "B"),
                ("Biology", "B"),
                ("Chemistry", "C"),
                ("Physics", "C"),
                ("Geography", "B")
            ]
        },
        {
            "name": "Tumelo Radebe",
            "id": "STU2024002", 
            "year": 2024,
            "subjects": [
                ("Mathematics", "B"),
                ("English Language", "A"),
                ("History", "A"),
                ("Business Studies", "B"),
                ("Accounting", "C"),
                ("Economics", "B")
            ]
        },
        {
            "name": "Kabelo Mosotho",
            "id": "STU2024003",
            "year": 2023,
            "subjects": [
                ("Mathematics", "C"),
                ("English Language", "B"),
                ("Science", "C"),
                ("Geography", "B"),
                ("History", "C"),
                ("Agriculture", "B")
            ]
        }
    ]
    
    # Create certificates directory
    cert_dir = "/home/duckey/lgcse-project/sample_certificates"
    os.makedirs(cert_dir, exist_ok=True)
    
    # Generate certificates
    certificate_paths = []
    for i, student in enumerate(students, 1):
        output_path = f"{cert_dir}/certificate_{i:02d}_{student['id']}.jpg"
        create_sample_certificate(
            student["name"],
            student["id"], 
            student["year"],
            student["subjects"],
            output_path
        )
        certificate_paths.append(output_path)
    
    return certificate_paths

if __name__ == "__main__":
    print("🎓 Creating sample LGCSE certificates...")
    paths = create_sample_certificates()
    print(f"\n✅ Created {len(paths)} sample certificates:")
    for path in paths:
        print(f"   📄 {path}")
    print(f"\n🚀 Ready to process with:")
    print(f"   python process_certificates_to_blockchain.py --images {' '.join(paths)} --batch")
