#!/usr/bin/env python3
"""
Test script for Gemini API integration with LGCSE Certificate Verification System
"""

import os
import sys
import json
import tempfile
import time
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, '/home/duckey/lgcse-project/backend')

def test_gemini_client():
    """Test the Gemini OCR client directly"""
    print("=" * 60)
    print("Testing Gemini API Client Integration")
    print("=" * 60)
    
    try:
        from gemini_ocr_client import GeminiOCRClient, get_gemini_client
        
        # Check if API key is configured
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("❌ GEMINI_API_KEY not found in environment variables")
            return False
        
        print(f"✅ Gemini API Key found: {api_key[:20]}...")
        
        # Initialize client
        client = get_gemini_client()
        print("✅ Gemini client initialized successfully")
        
        # Get API info
        api_info = client.get_api_info()
        print(f"✅ API Info: {json.dumps(api_info, indent=2)}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import Gemini client: {e}")
        return False
    except Exception as e:
        print(f"❌ Failed to initialize Gemini client: {e}")
        return False

def test_multi_ocr_processor():
    """Test the MultiOCRProcessor with Gemini integration"""
    print("\n" + "=" * 60)
    print("Testing MultiOCRProcessor with Gemini")
    print("=" * 60)
    
    try:
        from multi_ocr_processor import MultiOCRProcessor
        
        # Initialize processor
        processor = MultiOCRProcessor()
        print("✅ MultiOCRProcessor initialized successfully")
        
        # Check API status
        api_status = processor.get_api_status()
        print(f"✅ API Status: {json.dumps(api_status, indent=2)}")
        
        # Check if Gemini is enabled
        if api_status['gemini']['enabled']:
            print("✅ Gemini API is enabled in MultiOCRProcessor")
        else:
            print("❌ Gemini API is not enabled in MultiOCRProcessor")
            return False
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import MultiOCRProcessor: {e}")
        return False
    except Exception as e:
        print(f"❌ Failed to initialize MultiOCRProcessor: {e}")
        return False

def test_gemini_with_sample_image():
    """Test Gemini OCR with a sample certificate image"""
    print("\n" + "=" * 60)
    print("Testing Gemini OCR with Sample Image")
    print("=" * 60)
    
    try:
        from gemini_ocr_client import get_gemini_client
        from PIL import Image, ImageDraw, ImageFont
        
        # Create a sample certificate image for testing
        print("📝 Creating sample certificate image...")
        
        # Create a simple certificate image
        img = Image.new('RGB', (800, 600), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try to use a basic font, fallback to default if not available
        try:
            font_large = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 24)
            font_medium = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 18)
            font_small = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 14)
        except:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        # Draw certificate content
        draw.text((50, 50), "Examinations Council of Lesotho", fill='black', font=font_large)
        draw.text((50, 100), "LGCSE Certificate", fill='black', font=font_medium)
        draw.text((50, 150), "Student Name: John Doe", fill='black', font=font_small)
        draw.text((50, 180), "Student ID: LGCSE2023001", fill='black', font=font_small)
        draw.text((50, 210), "Examination Year: 2023", fill='black', font=font_small)
        draw.text((50, 240), "Centre Number: 001", fill='black', font=font_small)
        
        draw.text((50, 290), "Subjects and Grades:", fill='black', font=font_medium)
        draw.text((50, 320), "Mathematics - A", fill='black', font=font_small)
        draw.text((50, 345), "English - B", fill='black', font=font_small)
        draw.text((50, 370), "Science - A*", fill='black', font=font_small)
        draw.text((50, 395), "Geography - C", fill='black', font=font_small)
        
        draw.text((50, 450), "Certificate Number: LGCSE/2023/001", fill='black', font=font_small)
        draw.text((50, 480), "Issue Date: 15 June 2023", fill='black', font=font_small)
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            img.save(temp_file.name, 'PNG')
            temp_image_path = temp_file.name
        
        print(f"✅ Sample certificate image created: {temp_image_path}")
        
        # Test Gemini OCR
        print("🔍 Processing with Gemini API...")
        client = get_gemini_client()
        
        start_time = time.time()
        result = client.extract_certificate_data_structured(temp_image_path)
        processing_time = time.time() - start_time
        
        print(f"⏱️  Processing time: {processing_time:.2f} seconds")
        
        if result.error:
            print(f"❌ Gemini API error: {result.error}")
            return False
        else:
            print(f"✅ Gemini API success!")
            print(f"📄 Extracted text ({len(result.text)} chars):")
            print("-" * 40)
            print(result.text[:500] + "..." if len(result.text) > 500 else result.text)
            print("-" * 40)
            print(f"🎯 Confidence: {result.confidence:.1f}%")
            
            if result.structured_data:
                print(f"📋 Structured data:")
                print(json.dumps(result.structured_data, indent=2))
        
        # Clean up
        os.unlink(temp_image_path)
        return True
        
    except Exception as e:
        print(f"❌ Failed to test Gemini with sample image: {e}")
        return False

def test_multi_ocr_with_gemini():
    """Test MultiOCRProcessor with Gemini preference"""
    print("\n" + "=" * 60)
    print("Testing MultiOCRProcessor with Gemini Preference")
    print("=" * 60)
    
    try:
        from multi_ocr_processor import MultiOCRProcessor
        from PIL import Image, ImageDraw
        
        # Create a simple test image
        img = Image.new('RGB', (600, 400), color='white')
        draw = ImageDraw.Draw(img)
        
        # Draw text
        draw.text((50, 50), "Test Certificate", fill='black')
        draw.text((50, 100), "Student: Jane Smith", fill='black')
        draw.text((50, 150), "Year: 2023", fill='black')
        draw.text((50, 200), "Mathematics - A", fill='black')
        draw.text((50, 250), "Science - B", fill='black')
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            img.save(temp_file.name, 'PNG')
            temp_image_path = temp_file.name
        
        print(f"✅ Test image created: {temp_image_path}")
        
        # Test with Gemini preference
        processor = MultiOCRProcessor()
        
        print("🔍 Testing with 'gemini' preference...")
        start_time = time.time()
        result = processor.process_image_with_all_apis(temp_image_path, prefer_api='gemini')
        processing_time = time.time() - start_time
        
        print(f"⏱️  Total processing time: {processing_time:.2f} seconds")
        
        # Check results
        best_result = result.get('best_result', {})
        apis_used = result.get('apis_used', [])
        
        print(f"✅ APIs used: {apis_used}")
        print(f"🏆 Best API: {best_result.get('api_name', 'unknown')}")
        print(f"🎯 Best confidence: {best_result.get('confidence', 0):.1f}%")
        
        if best_result.get('api_name') == 'gemini':
            print("✅ Gemini was selected as the best API!")
        else:
            print(f"⚠️  Another API ({best_result.get('api_name')}) was selected as better")
        
        # Show comparison
        comparison = result.get('comparison', {})
        confidence_ranking = comparison.get('confidence_ranking', [])
        if confidence_ranking:
            print("📊 Confidence ranking:")
            for api, confidence in confidence_ranking:
                print(f"   {api}: {confidence:.1f}%")
        
        # Clean up
        os.unlink(temp_image_path)
        return True
        
    except Exception as e:
        print(f"❌ Failed to test MultiOCR with Gemini: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 Starting Gemini API Integration Tests")
    print("📍 LGCSE Certificate Verification System")
    print("=" * 60)
    
    # Load environment variables
    env_path = '/home/duckey/lgcse-project/backend/.env.test'
    if os.path.exists(env_path):
        print(f"📁 Loading environment from: {env_path}")
        with open(env_path, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
        print("✅ Environment variables loaded")
    else:
        print(f"⚠️  Environment file not found: {env_path}")
    
    # Run tests
    tests = [
        ("Gemini Client", test_gemini_client),
        ("MultiOCR Processor", test_multi_ocr_processor),
        ("Gemini OCR with Sample", test_gemini_with_sample_image),
        ("MultiOCR with Gemini", test_multi_ocr_with_gemini),
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n🧪 Running test: {test_name}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test '{test_name}' failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 Test Results Summary")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:.<30} {status}")
        if result:
            passed += 1
    
    print(f"\n📊 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Gemini API integration is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the configuration and error messages above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
