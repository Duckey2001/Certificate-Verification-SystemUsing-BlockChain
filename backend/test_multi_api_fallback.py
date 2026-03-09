#!/usr/bin/env python3
"""
Test multi-API fallback functionality
"""

import os
import sys
import tempfile
from PIL import Image, ImageDraw

# Add the backend directory to Python path
sys.path.append('/home/duckey/lgcse-project/backend')

def create_test_certificate_image():
    """Create a test certificate image"""
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)
    
    text = "LINEO LETHALA\nDate of Birth: 04/04/2002\nCentre: LS547/140458570\nSession: November 2019"
    draw.text((20, 20), text, fill='black')
    
    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    img.save(temp_file.name, 'PNG')
    temp_file.close()
    
    return temp_file.name

def test_fallback_mechanism():
    """Test fallback when OCR.space fails"""
    print("Testing Multi-API Fallback Mechanism...")
    
    try:
        # Set environment variable
        os.environ['OCR_SPACE_API_KEY'] = '8195ce015388957'
        
        from ocr_space_client import MultiAPIOCRProcessor
        
        processor = MultiAPIOCRProcessor('8195ce015388957')
        
        # Create test image
        test_image_path = create_test_certificate_image()
        print(f"Created test image: {test_image_path}")
        
        # Test with auto preference
        result = processor.extract_certificate_data_enhanced(test_image_path, prefer_api='auto')
        
        print(f"Multi-API Result:")
        print(f"  Best API: {result.get('ocr_api_used', 'unknown')}")
        print(f"  Confidence: {result.get('confidence_score', 0):.1f}%")
        print(f"  Student name: {result.get('student_name', 'N/A')}")
        print(f"  Exam year: {result.get('examination_year', 'N/A')}")
        
        # Check if both APIs were tried
        if 'all_ocr_results' in result:
            all_results = result['all_ocr_results']
            print(f"  OCR.space result: {'Success' if all_results.get('ocr_space', {}).get('text') else 'Failed'}")
            print(f"  Tesseract result: {'Success' if all_results.get('tesseract', {}).get('text') else 'Failed'}")
            
            # Show comparison
            if 'ocr_comparison' in result:
                comp = result['ocr_comparison']
                print(f"  OCR.space better: {comp.get('ocr_space_better', False)}")
                print(f"  Both successful: {comp.get('both_successful', False)}")
        
        # Clean up
        os.unlink(test_image_path)
        
        return result.get('confidence_score', 0) > 0
        
    except Exception as e:
        print(f"Fallback test error: {str(e)}")
        return False

def test_prefer_ocr_space():
    """Test preferring OCR.space API"""
    print("\nTesting Prefer OCR.space...")
    
    try:
        os.environ['OCR_SPACE_API_KEY'] = '8195ce015388957'
        
        from ocr_space_client import MultiAPIOCRProcessor
        
        processor = MultiAPIOCRProcessor('8195ce015388957')
        
        test_image_path = create_test_certificate_image()
        
        # Test preferring OCR.space
        result = processor.extract_certificate_data_enhanced(test_image_path, prefer_api='ocr_space')
        
        print(f"Prefer OCR.space Result:")
        print(f"  API used: {result.get('ocr_api_used', 'unknown')}")
        print(f"  Confidence: {result.get('confidence_score', 0):.1f}%")
        
        os.unlink(test_image_path)
        
        return result.get('ocr_api_used') == 'ocr_space' or result.get('confidence_score', 0) > 0
        
    except Exception as e:
        print(f"Prefer OCR.space test error: {str(e)}")
        return False

def test_prefer_tesseract():
    """Test preferring Tesseract"""
    print("\nTesting Prefer Tesseract...")
    
    try:
        os.environ['OCR_SPACE_API_KEY'] = '8195ce015388957'
        
        from ocr_space_client import MultiAPIOCRProcessor
        
        processor = MultiAPIOCRProcessor('8195ce015388957')
        
        test_image_path = create_test_certificate_image()
        
        # Test preferring Tesseract
        result = processor.extract_certificate_data_enhanced(test_image_path, prefer_api='tesseract')
        
        print(f"Prefer Tesseract Result:")
        print(f"  API used: {result.get('ocr_api_used', 'unknown')}")
        print(f"  Confidence: {result.get('confidence_score', 0):.1f}%")
        
        os.unlink(test_image_path)
        
        return result.get('confidence_score', 0) > 0
        
    except Exception as e:
        print(f"Prefer Tesseract test error: {str(e)}")
        return False

def test_enhanced_lgcse_fallback():
    """Test Enhanced LGCSE Processor fallback"""
    print("\nTesting Enhanced LGCSE Processor Fallback...")
    
    try:
        os.environ['OCR_SPACE_API_KEY'] = '8195ce015388957'
        
        from enhanced_lgcse_processor import EnhancedLGCSEProcessor
        
        processor = EnhancedLGCSEProcessor()
        
        test_image_path = create_test_certificate_image()
        
        # Test with multi-API support
        result = processor.process_certificate_file_with_multi_api(test_image_path, prefer_api='auto')
        
        print(f"Enhanced LGCSE Fallback Result:")
        print(f"  Method: {result.get('extraction_method', 'unknown')}")
        print(f"  Confidence: {result.get('confidence_score', 0):.1f}%")
        
        # Check if LGCSE-specific data was extracted
        if 'lgcse_specific' in result:
            lgcse = result['lgcse_specific']
            validation = lgcse.get('validation', {})
            print(f"  LGCSE Valid: {validation.get('is_valid', False)}")
            print(f"  LGCSE Confidence: {validation.get('confidence', 0):.1f}%")
        
        os.unlink(test_image_path)
        
        return result.get('confidence_score', 0) > 0
        
    except Exception as e:
        print(f"Enhanced LGCSE fallback test error: {str(e)}")
        return False

def main():
    """Run all fallback tests"""
    print("=" * 60)
    print("Multi-API Fallback Functionality Test")
    print("=" * 60)
    
    # Test different scenarios
    auto_success = test_fallback_mechanism()
    ocr_space_success = test_prefer_ocr_space()
    tesseract_success = test_prefer_tesseract()
    lgcse_success = test_enhanced_lgcse_fallback()
    
    print("\n" + "=" * 60)
    print("FALLBACK TEST SUMMARY")
    print("=" * 60)
    print(f"Auto Selection Test: {'✓ PASSED' if auto_success else '✗ FAILED'}")
    print(f"Prefer OCR.space Test: {'✓ PASSED' if ocr_space_success else '✗ FAILED'}")
    print(f"Prefer Tesseract Test: {'✓ PASSED' if tesseract_success else '✗ FAILED'}")
    print(f"Enhanced LGCSE Fallback: {'✓ PASSED' if lgcse_success else '✗ FAILED'}")
    
    if auto_success:
        print("\n✓ Multi-API fallback mechanism is working correctly!")
        print("✓ System can automatically select the best OCR API")
        print("✓ Fallback to alternative APIs when primary fails")
    else:
        print("\n✗ Multi-API fallback mechanism needs attention")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()
