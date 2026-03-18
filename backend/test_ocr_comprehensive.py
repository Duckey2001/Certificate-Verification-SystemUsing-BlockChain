#!/usr/bin/env python3
"""
Comprehensive OCR Test Script for LGCSE Certificate Verification System
Tests all available OCR APIs and provides detailed status information
"""

import os
import sys
import json
import time
import requests
import re
from typing import Dict, Any, Optional
from PIL import Image
import pytesseract

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def load_environment():
    """Load environment variables from .env.test"""
    from dotenv import load_dotenv
    load_dotenv('.env.test')
    print("✓ Environment loaded from .env.test")

def test_tesseract_ocr(image_path: str) -> Dict[str, Any]:
    """Test Tesseract OCR functionality"""
    print("\n=== Testing Tesseract OCR ===")
    try:
        # Open image
        image = Image.open(image_path)
        
        # Perform OCR
        start_time = time.time()
        text = pytesseract.image_to_string(image)
        processing_time = time.time() - start_time
        
        # Get detailed data with confidence
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        
        # Calculate average confidence
        confidences = [conf for conf in data['conf'] if conf > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        result = {
            'success': True,
            'text': text,
            'confidence': avg_confidence,
            'processing_time': processing_time,
            'word_count': len([w for w in data['text'] if w.strip()]),
            'engine': 'Tesseract'
        }
        
        print(f"✓ Tesseract working - Confidence: {avg_confidence:.1f}%")
        return result
        
    except Exception as e:
        print(f"✗ Tesseract failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'engine': 'Tesseract'
        }

def test_ocr_space_api(image_path: str) -> Dict[str, Any]:
    """Test OCR.space API functionality"""
    print("\n=== Testing OCR.space API ===")
    try:
        api_key = os.getenv('OCR_SPACE_API_KEY')
        api_url = os.getenv('OCR_SPACE_API_URL', 'https://api.ocr.space/parse/image')
        
        if not api_key:
            raise Exception("OCR_SPACE_API_KEY not found in environment")
        
        with open(image_path, 'rb') as image_file:
            files = {'file': image_file}
            data = {
                'apikey': api_key,
                'language': 'eng',
                'isOverlayRequired': 'true',
                'detectOrientation': 'true',
                'scale': 'true',
                'OCREngine': 2
            }
            
            start_time = time.time()
            response = requests.post(api_url, files=files, data=data, timeout=30)
            processing_time = time.time() - start_time
        
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}: {response.text}")
        
        result = response.json()
        
        if result.get('IsErroredOnProcessing', False):
            raise Exception(result.get('ErrorMessage', 'Unknown processing error'))
        
        parsed_results = result.get('ParsedResults', [])
        if not parsed_results:
            raise Exception("No parsed results returned")
        
        parsed_result = parsed_results[0]
        extracted_text = parsed_result.get('ParsedText', '')
        
        # Calculate confidence from overlay data
        text_overlay = parsed_result.get('TextOverlay', {})
        lines = text_overlay.get('Lines', [])
        words_confidence = []
        
        for line in lines:
            for word in line.get('Words', []):
                conf = word.get('Confidence', 0)
                if conf > 0:
                    words_confidence.append(conf)
        
        avg_confidence = sum(words_confidence) / len(words_confidence) if words_confidence else 80
        
        api_result = {
            'success': True,
            'text': extracted_text,
            'confidence': avg_confidence,
            'processing_time': processing_time,
            'word_count': len(words_confidence),
            'engine': 'OCR.space',
            'raw_response': result
        }
        
        print(f"✓ OCR.space working - Confidence: {avg_confidence:.1f}%")
        return api_result
        
    except Exception as e:
        print(f"✗ OCR.space failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'engine': 'OCR.space'
        }

def test_gemini_api(image_path: str) -> Dict[str, Any]:
    """Test Google Gemini API functionality"""
    print("\n=== Testing Google Gemini API ===")
    try:
        from gemini_ocr_client import get_gemini_client
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise Exception("GEMINI_API_KEY not found in environment")
        
        client = get_gemini_client()
        
        start_time = time.time()
        result = client.extract_certificate_data_structured(image_path)
        processing_time = time.time() - start_time
        
        if result.error:
            raise Exception(f"Gemini API error: {result.error}")
        
        api_result = {
            'success': True,
            'text': result.text,
            'confidence': result.confidence,
            'processing_time': processing_time,
            'word_count': len(result.text.split()),
            'engine': 'Google Gemini',
            'structured_data': result.structured_data,
            'raw_response': result.__dict__
        }
        
        print(f"✓ Gemini working - Confidence: {result.confidence:.1f}%")
        return api_result
        
    except Exception as e:
        print(f"✗ Gemini failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'engine': 'Google Gemini'
        }

def test_multi_ocr_processor(image_path: str) -> Dict[str, Any]:
    """Test the Multi-OCR Processor"""
    print("\n=== Testing Multi-OCR Processor ===")
    try:
        from multi_ocr_processor import MultiOCRProcessor
        
        processor = MultiOCRProcessor()
        
        # Get API status
        status = processor.get_api_status()
        print(f"Available APIs: {status['total_apis_available']}")
        
        start_time = time.time()
        result = processor.process_image_with_all_apis(image_path, prefer_api='auto')
        processing_time = time.time() - start_time
        
        best_result = result.get('best_result', {})
        
        multi_result = {
            'success': True,
            'best_engine': best_result.get('api_name'),
            'best_confidence': best_result.get('confidence', 0),
            'text': best_result.get('text', ''),
            'processing_time': processing_time,
            'apis_tried': result.get('apis_used', []),
            'comparison': result.get('comparison', {}),
            'all_results': result.get('all_results', {}),
            'engine': 'Multi-OCR Processor'
        }
        
        print(f"✓ Multi-OCR working - Best: {best_result.get('api_name')} ({best_result.get('confidence', 0):.1f}%)")
        return multi_result
        
    except Exception as e:
        print(f"✗ Multi-OCR failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'engine': 'Multi-OCR Processor'
        }

def test_enhanced_lgcse_processor(image_path: str) -> Dict[str, Any]:
    """Test the Enhanced LGCSE Processor"""
    print("\n=== Testing Enhanced LGCSE Processor ===")
    try:
        from enhanced_lgcse_processor import EnhancedLGCSEProcessor
        
        processor = EnhancedLGCSEProcessor()
        
        start_time = time.time()
        result = processor.process_certificate_file_enhanced(image_path)
        processing_time = time.time() - start_time
        
        lgcse_result = {
            'success': True,
            'confidence': result.get('confidence_score', 0),
            'processing_time': processing_time,
            'lgcse_specific': result.get('lgcse_specific', {}),
            'extracted_fields': result.get('extracted_fields', {}),
            'validation': result.get('validation', {}),
            'engine': 'Enhanced LGCSE Processor'
        }
        
        print(f"✓ Enhanced LGCSE working - Confidence: {lgcse_result['confidence']:.1f}%")
        return lgcse_result
        
    except Exception as e:
        print(f"✗ Enhanced LGCSE failed: {e}")
        return {
            'success': False,
            'error': str(e),
            'engine': 'Enhanced LGCSE Processor'
        }

def analyze_certificate_content(text: str) -> Dict[str, Any]:
    """Analyze extracted text for certificate characteristics"""
    analysis = {
        'word_count': len(text.split()),
        'char_count': len(text),
        'line_count': len(text.split('\n')),
        'has_lgcse_keywords': any(keyword in text.upper() for keyword in [
            'LGCSE', 'EXAMINATIONS COUNCIL', 'LESOTHO', 'STATEMENT OF RESULTS',
            'CANDIDATE NAME', 'CENTRE NUMBER', 'SUBJECT', 'GRADE'
        ]),
        'has_subject_grade_pattern': bool(re.search(r'[A-Z]+\s+[A*ABCDEF]', text, re.IGNORECASE)),
        'has_year_pattern': bool(re.search(r'20\d{2}', text)),
        'has_candidate_info': bool(re.search(r'(candidate|student|name)', text, re.IGNORECASE))
    }
    
    return analysis

def main():
    """Main test function"""
    print("🔍 LGCSE Certificate OCR System Test")
    print("=" * 50)
    
    # Load environment
    load_environment()
    
    # Check if test image provided
    if len(sys.argv) < 2:
        print("Usage: python test_ocr_comprehensive.py <image_path>")
        print("\nAvailable test images in the project:")
        
        # Look for test images
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.pdf')):
                    if 'test' in root.lower() or 'test' in file.lower():
                        print(f"  - {os.path.join(root, file)}")
        
        print("\nPlease provide an image path to test OCR functionality.")
        return
    
    image_path = sys.argv[1]
    
    # Check if image exists
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return
    
    print(f"📷 Testing with image: {image_path}")
    
    # Get image info
    try:
        with Image.open(image_path) as img:
            print(f"   Image size: {img.size}")
            print(f"   Image format: {img.format}")
    except Exception as e:
        print(f"   Error reading image: {e}")
        return
    
    # Test all OCR engines
    results = []
    
    # 1. Test Tesseract
    results.append(test_tesseract_ocr(image_path))
    
    # 2. Test OCR.space
    results.append(test_ocr_space_api(image_path))
    
    # 3. Test Gemini
    results.append(test_gemini_api(image_path))
    
    # 4. Test Multi-OCR Processor
    results.append(test_multi_ocr_processor(image_path))
    
    # 5. Test Enhanced LGCSE Processor
    results.append(test_enhanced_lgcse_processor(image_path))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 OCR TEST SUMMARY")
    print("=" * 50)
    
    successful_tests = [r for r in results if r.get('success', False)]
    failed_tests = [r for r in results if not r.get('success', False)]
    
    print(f"✅ Successful tests: {len(successful_tests)}")
    print(f"❌ Failed tests: {len(failed_tests)}")
    
    if successful_tests:
        print("\n🏆 BEST PERFORMING OCR ENGINE:")
        best = max(successful_tests, key=lambda x: x.get('confidence', 0))
        print(f"   Engine: {best['engine']}")
        print(f"   Confidence: {best.get('confidence', 0):.1f}%")
        print(f"   Processing time: {best.get('processing_time', 0):.2f}s")
        print(f"   Word count: {best.get('word_count', 0)}")
        
        # Analyze content
        if 'text' in best:
            analysis = analyze_certificate_content(best['text'])
            print(f"\n📋 CONTENT ANALYSIS:")
            print(f"   Words: {analysis['word_count']}")
            print(f"   Lines: {analysis['line_count']}")
            print(f"   LGCSE keywords detected: {'Yes' if analysis['has_lgcse_keywords'] else 'No'}")
            print(f"   Subject/Grade pattern: {'Yes' if analysis['has_subject_grade_pattern'] else 'No'}")
            print(f"   Year pattern: {'Yes' if analysis['has_year_pattern'] else 'No'}")
    
    if failed_tests:
        print("\n❌ FAILED TESTS:")
        for test in failed_tests:
            print(f"   {test['engine']}: {test.get('error', 'Unknown error')}")
    
    # Save detailed results
    output_file = 'ocr_test_results.json'
    with open(output_file, 'w') as f:
        json.dump({
            'test_image': image_path,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'results': results,
            'summary': {
                'successful_count': len(successful_tests),
                'failed_count': len(failed_tests),
                'best_engine': max(successful_tests, key=lambda x: x.get('confidence', 0))['engine'] if successful_tests else None
            }
        }, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {output_file}")

if __name__ == "__main__":
    main()
