#!/usr/bin/env python3
"""
Simple OCR Test Script - Run directly with certificate image
Usage: python simple_ocr_test.py <path_to_certificate_image>
"""

import os
import sys
import json
import time
import tempfile
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def load_environment():
    """Load environment variables"""
    from dotenv import load_dotenv
    load_dotenv('.env.test')
    print("✓ Environment loaded")

def test_certificate_image(image_path):
    """Test OCR on certificate image"""
    print(f"\n🔍 Testing OCR on: {image_path}")
    print("=" * 60)
    
    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return
    
    # Load environment
    load_environment()
    
    # Test results
    results = []
    
    # 1. Test Tesseract
    print("\n📷 Testing Tesseract OCR...")
    try:
        from PIL import Image
        import pytesseract
        
        image = Image.open(image_path)
        start_time = time.time()
        text = pytesseract.image_to_string(image)
        processing_time = time.time() - start_time
        
        # Get detailed data with confidence
        data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        confidences = [conf for conf in data['conf'] if conf > 0]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        tesseract_result = {
            'engine': 'Tesseract',
            'success': True,
            'confidence': avg_confidence,
            'processing_time': processing_time,
            'word_count': len([w for w in data['text'] if w.strip()]),
            'text': text
        }
        results.append(tesseract_result)
        print(f"✅ Tesseract: {avg_confidence:.1f}% confidence, {processing_time:.2f}s")
        
    except Exception as e:
        print(f"❌ Tesseract failed: {e}")
        results.append({'engine': 'Tesseract', 'success': False, 'error': str(e)})
    
    # 2. Test OCR.space
    print("\n🌐 Testing OCR.space API...")
    try:
        import requests
        
        api_key = os.getenv('OCR_SPACE_API_KEY')
        api_url = os.getenv('OCR_SPACE_API_URL', 'https://api.ocr.space/parse/image')
        
        if api_key:
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
            
            if response.status_code == 200:
                result = response.json()
                if not result.get('IsErroredOnProcessing', False):
                    parsed_results = result.get('ParsedResults', [])
                    if parsed_results:
                        parsed_result = parsed_results[0]
                        extracted_text = parsed_result.get('ParsedText', '')
                        
                        # Calculate confidence
                        text_overlay = parsed_result.get('TextOverlay', {})
                        lines = text_overlay.get('Lines', [])
                        words_confidence = []
                        
                        for line in lines:
                            for word in line.get('Words', []):
                                conf = word.get('Confidence', 0)
                                if conf > 0:
                                    words_confidence.append(conf)
                        
                        avg_confidence = sum(words_confidence) / len(words_confidence) if words_confidence else 80
                        
                        ocr_space_result = {
                            'engine': 'OCR.space',
                            'success': True,
                            'confidence': avg_confidence,
                            'processing_time': processing_time,
                            'word_count': len(words_confidence),
                            'text': extracted_text
                        }
                        results.append(ocr_space_result)
                        print(f"✅ OCR.space: {avg_confidence:.1f}% confidence, {processing_time:.2f}s")
                    else:
                        print("❌ OCR.space: No parsed results")
                else:
                    print(f"❌ OCR.space: {result.get('ErrorMessage', 'Processing error')}")
            else:
                print(f"❌ OCR.space: HTTP {response.status_code}")
        else:
            print("❌ OCR.space: No API key")
            
    except Exception as e:
        print(f"❌ OCR.space failed: {e}")
        results.append({'engine': 'OCR.space', 'success': False, 'error': str(e)})
    
    # 3. Test Multi-OCR Processor
    print("\n🔄 Testing Multi-OCR Processor...")
    try:
        from multi_ocr_processor import MultiOCRProcessor
        
        processor = MultiOCRProcessor()
        start_time = time.time()
        multi_result = processor.process_image_with_all_apis(image_path, prefer_api='auto')
        processing_time = time.time() - start_time
        
        best_result = multi_result.get('best_result', {})
        
        multi_processor_result = {
            'engine': 'Multi-OCR Processor',
            'success': True,
            'confidence': best_result.get('confidence', 0),
            'processing_time': processing_time,
            'best_api': best_result.get('api_name'),
            'apis_tried': multi_result.get('apis_used', []),
            'text': best_result.get('text', ''),
            'comparison': multi_result.get('comparison', {})
        }
        results.append(multi_processor_result)
        print(f"✅ Multi-OCR: Best {best_result.get('api_name')} at {best_result.get('confidence', 0):.1f}%, {processing_time:.2f}s")
        
    except Exception as e:
        print(f"❌ Multi-OCR failed: {e}")
        results.append({'engine': 'Multi-OCR Processor', 'success': False, 'error': str(e)})
    
    # Show results
    print("\n" + "=" * 60)
    print("📊 OCR RESULTS SUMMARY")
    print("=" * 60)
    
    successful_results = [r for r in results if r.get('success', False)]
    failed_results = [r for r in results if not r.get('success', False)]
    
    print(f"✅ Successful: {len(successful_results)}")
    print(f"❌ Failed: {len(failed_results)}")
    
    if successful_results:
        print("\n🏆 BEST PERFORMING ENGINE:")
        best = max(successful_results, key=lambda x: x.get('confidence', 0))
        print(f"   Engine: {best['engine']}")
        print(f"   Confidence: {best.get('confidence', 0):.1f}%")
        print(f"   Time: {best.get('processing_time', 0):.2f}s")
        print(f"   Words: {best.get('word_count', 0)}")
        
        # Show extracted text
        if best.get('text'):
            print(f"\n📄 EXTRACTED TEXT:")
            print("-" * 40)
            print(best['text'][:500] + ("..." if len(best['text']) > 500 else ""))
            print("-" * 40)
            
            # Analyze for LGCSE patterns
            text = best['text']
            print(f"\n🔍 CERTIFICATE ANALYSIS:")
            print(f"   LGCSE keywords: {'✅' if any(kw in text.upper() for kw in ['LGCSE', 'EXAMINATIONS COUNCIL', 'LESOTHO']) else '❌'}")
            print(f"   Subject/Grade pattern: {'✅' if any(subject in text.upper() for subject in ['ENGLISH', 'MATHEMATICS', 'SCIENCE']) else '❌'}")
            print(f"   Year pattern: {'✅' if any('20' in word for word in text.split()) else '❌'}")
            print(f"   Student name: {'✅' if 'NAME' in text.upper() else '❌'}")
    
    if failed_results:
        print(f"\n❌ FAILED ENGINES:")
        for result in failed_results:
            print(f"   {result['engine']}: {result.get('error', 'Unknown error')}")
    
    # Save results
    output_file = 'simple_ocr_results.json'
    with open(output_file, 'w') as f:
        json.dump({
            'image_path': image_path,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'results': results,
            'best_engine': max(successful_results, key=lambda x: x.get('confidence', 0))['engine'] if successful_results else None
        }, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: {output_file}")
    return results

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("🔍 Simple OCR Test Script")
        print("=" * 40)
        print("Usage: python simple_ocr_test.py <path_to_certificate_image>")
        print("\nExamples:")
        print("  python simple_ocr_test.py my_certificate.jpg")
        print("  python simple_ocr_test.py ./uploads/certificates/image.jpeg")
        print("  python simple_ocr_test.py /path/to/certificate.png")
        
        # Look for available images
        print(f"\n📁 Available images in current directory:")
        for ext in ['*.jpg', '*.jpeg', '*.png']:
            for file in Path('.').glob(ext):
                print(f"   - {file}")
        
        print(f"\n📁 Available images in uploads directory:")
        uploads_dir = Path('./uploads/certificates')
        if uploads_dir.exists():
            for file in uploads_dir.glob('*'):
                if file.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                    print(f"   - {file}")
        
        return
    
    image_path = sys.argv[1]
    test_certificate_image(image_path)

if __name__ == "__main__":
    main()
