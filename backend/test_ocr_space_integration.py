#!/usr/bin/env python3
"""
Test script for OCR.space API integration with certificate processing
"""

import os
import sys
import json
import tempfile
import requests
from PIL import Image, ImageDraw, ImageFont
import time

# Add the backend directory to Python path
sys.path.append('/home/duckey/lgcse-project/backend')

def create_test_certificate_image():
    """Create a test certificate image for testing OCR APIs"""
    
    # Create a blank white image
    img = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(img)
    
    # Try to use a basic font
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 24)
        font_text = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except:
        font_title = ImageFont.load_default()
        font_text = ImageFont.load_default()
        font_small = ImageFont.load_default()
    
    # Draw certificate content
    draw.text((50, 30), "EXAMINATIONS COUNCIL OF LESOTHO", fill='black', font=font_title)
    draw.text((250, 70), "LGCSE STATEMENT OF RESULTS", fill='black', font=font_title)
    
    draw.text((50, 120), "Candidate Name:", fill='black', font=font_text)
    draw.text((200, 120), "LINEO LETHALA", fill='black', font=font_text)
    
    draw.text((50, 150), "Date of Birth:", fill='black', font=font_text)
    draw.text((200, 150), "04/04/2002", fill='black', font=font_text)
    
    draw.text((50, 180), "Centre/Candidate Number:", fill='black', font=font_text)
    draw.text((300, 180), "LS547/140458570", fill='black', font=font_text)
    
    draw.text((50, 210), "Centre Name:", fill='black', font=font_text)
    draw.text((200, 210), "MAKHAOLA HIGH SCHOOL QACHA'S NEK", fill='black', font=font_text)
    
    draw.text((50, 240), "Session:", fill='black', font=font_text)
    draw.text((150, 240), "November 2019", fill='black', font=font_text)
    
    draw.text((50, 280), "LGCSE Number: 127246", fill='black', font=font_text)
    
    # Table header
    draw.text((50, 320), "Qualification", fill='black', font=font_small)
    draw.text((200, 320), "Syllabus Code", fill='black', font=font_small)
    draw.text((320, 320), "Syllabus Title", fill='black', font=font_small)
    draw.text((550, 320), "Result", fill='black', font=font_small)
    
    # Sample results
    subjects = [
        ("LGCSE", "0175", "ENGLISH LANGUAGE", "D"),
        ("LGCSE", "0176", "SESOTHO", "D"),
        ("LGCSE", "0178", "MATHEMATICS", "E"),
        ("LGCSE", "0179", "AGRICULTURE", "C"),
        ("LGCSE", "0180", "BIOLOGY", "D"),
        ("LGCSE", "0181", "PHYSICAL SCIENCE", "C"),
        ("LGCSE", "0182", "DEVELOPMENT STUDIES", "D"),
        ("LGCSE", "0187", "ACCOUNTING", "D")
    ]
    
    y_pos = 340
    for qual, code, title, result in subjects:
        draw.text((50, y_pos), qual, fill='black', font=font_small)
        draw.text((200, y_pos), code, fill='black', font=font_small)
        draw.text((320, y_pos), title, fill='black', font=font_small)
        draw.text((550, y_pos), result, fill='black', font=font_small)
        y_pos += 25
    
    # Save to temporary file
    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    img.save(temp_file.name, 'PNG')
    temp_file.close()
    
    return temp_file.name

def test_ocr_space_direct():
    """Test OCR.space API directly"""
    print("Testing OCR.space API directly...")
    
    # Set the API key
    os.environ['OCR_SPACE_API_KEY'] = '8195ce015388957'
    
    try:
        from ocr_space_client import OCRRSpaceClient
        
        client = OCRRSpaceClient('8195ce015388957')
        
        # Create test image
        test_image_path = create_test_certificate_image()
        print(f"Created test image: {test_image_path}")
        
        # Test OCR.space
        result = client.extract_text_from_file(test_image_path, language='eng')
        
        print(f"OCR.space Result:")
        print(f"  Text length: {len(result.text)} chars")
        print(f"  Confidence: {result.confidence:.1f}%")
        print(f"  Processing time: {result.processing_time:.2f}s")
        print(f"  Error: {result.error}")
        print(f"  API used: {result.api_used}")
        
        if result.text:
            print(f"  Extracted text preview: {result.text[:200]}...")
        
        # Clean up
        os.unlink(test_image_path)
        
        return result
        
    except Exception as e:
        print(f"Error testing OCR.space directly: {str(e)}")
        return None

def test_multi_api_processor():
    """Test the multi-API processor"""
    print("\nTesting Multi-API Processor...")
    
    try:
        from ocr_space_client import get_multi_api_processor
        
        # Set environment variable
        os.environ['OCR_SPACE_API_KEY'] = '8195ce015388957'
        
        processor = get_multi_api_processor()
        
        # Create test image
        test_image_path = create_test_certificate_image()
        print(f"Created test image: {test_image_path}")
        
        # Test multi-API extraction
        result = processor.extract_certificate_data_enhanced(test_image_path, prefer_api='auto')
        
        print(f"Multi-API Result:")
        print(f"  Best API: {result.get('ocr_api_used', 'unknown')}")
        print(f"  Confidence: {result.get('confidence_score', 0):.1f}%")
        print(f"  Processing time: {result.get('processing_time', 0):.2f}s")
        print(f"  Student name: {result.get('student_name', 'N/A')}")
        print(f"  Exam year: {result.get('examination_year', 'N/A')}")
        print(f"  Subjects found: {len(result.get('subjects_with_grades', []))}")
        
        # Show comparison
        if 'ocr_comparison' in result:
            comp = result['ocr_comparison']
            print(f"  OCR.space better: {comp.get('ocr_space_better', False)}")
            print(f"  Confidence difference: {comp.get('confidence_difference', 0):.1f}%")
        
        # Clean up
        os.unlink(test_image_path)
        
        return result
        
    except Exception as e:
        print(f"Error testing multi-API processor: {str(e)}")
        return None

def test_enhanced_lgcse_processor():
    """Test the enhanced LGCSE processor with multi-API support"""
    print("\nTesting Enhanced LGCSE Processor with Multi-API...")
    
    try:
        from enhanced_lgcse_processor import EnhancedLGCSEProcessor
        
        # Set environment variable
        os.environ['OCR_SPACE_API_KEY'] = '8195ce015388957'
        
        processor = EnhancedLGCSEProcessor()
        
        # Create test image
        test_image_path = create_test_certificate_image()
        print(f"Created test image: {test_image_path}")
        
        # Test enhanced processing with multi-API
        result = processor.process_certificate_file_with_multi_api(test_image_path, prefer_api='auto')
        
        print(f"Enhanced LGCSE Multi-API Result:")
        print(f"  Extraction method: {result.get('extraction_method', 'unknown')}")
        print(f"  Confidence: {result.get('confidence_score', 0):.1f}%")
        
        if 'lgcse_specific' in result:
            lgcse = result['lgcse_specific']
            parsed = lgcse.get('parsed_data', {})
            validation = lgcse.get('validation', {})
            
            print(f"  LGCSE Valid: {validation.get('is_valid', False)}")
            print(f"  LGCSE Message: {validation.get('message', 'N/A')}")
            print(f"  Student: {parsed.get('candidate_info', {}).get('name', 'N/A')}")
            print(f"  Centre: {parsed.get('candidate_info', {}).get('centre_number', 'N/A')}")
            print(f"  Subjects: {len(parsed.get('subjects', []))}")
        
        # Show OCR comparison if available
        if 'ocr_comparison' in result:
            comp = result['ocr_comparison']
            print(f"  OCR.space used: {comp.get('ocr_space_better', False)}")
        
        # Clean up
        os.unlink(test_image_path)
        
        return result
        
    except Exception as e:
        print(f"Error testing enhanced LGCSE processor: {str(e)}")
        return None

def test_api_status():
    """Test API status endpoint functionality"""
    print("\nTesting API Status...")
    
    try:
        # Set environment variable
        os.environ['OCR_SPACE_API_KEY'] = '8195ce015388957'
        
        # Check if OCR.space is available
        ocr_space_available = bool(os.getenv('OCR_SPACE_API_KEY'))
        
        print(f"  OCR.space API Key configured: {ocr_space_available}")
        print(f"  API Key: {os.getenv('OCR_SPACE_API_KEY', 'Not set')}")
        
        # Test import
        try:
            from ocr_space_client import get_multi_api_processor
            processor = get_multi_api_processor()
            print(f"  Multi-API processor: Available")
        except Exception as e:
            print(f"  Multi-API processor: Error - {str(e)}")
        
        # Test enhanced processor
        try:
            from enhanced_lgcse_processor import EnhancedLGCSEProcessor
            lgcse_proc = EnhancedLGCSEProcessor()
            has_multi_api = hasattr(lgcse_proc, 'process_certificate_file_with_multi_api')
            print(f"  Enhanced LGCSE processor: Available, Multi-API: {has_multi_api}")
        except Exception as e:
            print(f"  Enhanced LGCSE processor: Error - {str(e)}")
        
    except Exception as e:
        print(f"Error testing API status: {str(e)}")

def main():
    """Run all tests"""
    print("=" * 60)
    print("OCR.space API Integration Test Suite")
    print("=" * 60)
    
    # Test API status first
    test_api_status()
    
    # Test OCR.space directly
    ocr_space_result = test_ocr_space_direct()
    
    # Test multi-API processor
    multi_api_result = test_multi_api_processor()
    
    # Test enhanced LGCSE processor
    lgcse_result = test_enhanced_lgcse_processor()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    print(f"OCR.space Direct Test: {'✓ PASSED' if ocr_space_result and not ocr_space_result.error else '✗ FAILED'}")
    print(f"Multi-API Processor Test: {'✓ PASSED' if multi_api_result else '✗ FAILED'}")
    print(f"Enhanced LGCSE Processor Test: {'✓ PASSED' if lgcse_result else '✗ FAILED'}")
    
    if ocr_space_result:
        print(f"\nOCR.space Performance:")
        print(f"  Confidence: {ocr_space_result.confidence:.1f}%")
        print(f"  Processing Time: {ocr_space_result.processing_time:.2f}s")
    
    if multi_api_result:
        print(f"\nMulti-API Performance:")
        print(f"  Best API: {multi_api_result.get('ocr_api_used', 'unknown')}")
        print(f"  Overall Confidence: {multi_api_result.get('confidence_score', 0):.1f}%")
        
        if 'ocr_comparison' in multi_api_result:
            comp = multi_api_result['ocr_comparison']
            if comp.get('ocr_space_better'):
                print(f"  ✓ OCR.space provided better results")
            else:
                print(f"  ✓ Tesseract provided better or equal results")
    
    if lgcse_result and 'lgcse_specific' in lgcse_result:
        validation = lgcse_result['lgcse_specific']['validation']
        print(f"\nLGCSE Processing:")
        print(f"  Certificate Valid: {validation.get('is_valid', False)}")
        print(f"  Validation Message: {validation.get('message', 'N/A')}")
        print(f"  Extraction Method: {lgcse_result.get('extraction_method', 'unknown')}")
    
    print("\n" + "=" * 60)
    print("OCR.space API integration test completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()
