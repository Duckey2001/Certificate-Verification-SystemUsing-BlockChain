#!/usr/bin/env python3
"""
Simple test for OCR.space API integration
"""

import os
import sys
import tempfile
import requests
from PIL import Image, ImageDraw

# Add the backend directory to Python path
sys.path.append('/home/duckey/lgcse-project/backend')

def test_ocr_space_simple():
    """Simple test of OCR.space API"""
    print("Testing OCR.space API...")
    
    # Create a simple test image with text
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)
    
    # Add some text
    try:
        from PIL import ImageFont
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
    except:
        font = None
    
    text = "LINEO LETHALA\nDate of Birth: 04/04/2002\nCentre: LS547/140458570"
    draw.text((20, 20), text, fill='black', font=font)
    
    # Save to temporary file
    temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    img.save(temp_file.name, 'PNG')
    temp_file.close()
    
    print(f"Created test image: {temp_file.name}")
    
    # Test OCR.space API directly
    api_key = '8195ce015388957'
    url = 'https://api.ocr.space/parse/image'
    
    with open(temp_file.name, 'rb') as f:
        files = {'file': f}
        payload = {
            'apikey': api_key,
            'language': 'eng',
            'isOverlayRequired': False,
            'detectOrientation': True,
            'scale': True,
            'OCREngine': 2,
            'isTable': False
        }
        
        try:
            response = requests.post(url, files=files, data=payload, timeout=30)
            print(f"HTTP Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"API Response: {result}")
                
                if result.get('IsErroredOnProcessing', False):
                    print(f"OCR Error: {result.get('ErrorMessage', 'Unknown error')}")
                else:
                    parsed_results = result.get('ParsedResults', [])
                    if parsed_results:
                        text = parsed_results[0].get('ParsedText', '')
                        print(f"Extracted Text: {text}")
                        print(f"Text Length: {len(text)} characters")
                        return True
                    else:
                        print("No parsed results returned")
            else:
                print(f"HTTP Error: {response.text}")
                
        except Exception as e:
            print(f"Request Error: {str(e)}")
        finally:
            # Clean up
            os.unlink(temp_file.name)
    
    return False

def test_ocr_space_client():
    """Test the OCR.space client"""
    print("\nTesting OCR.space Client...")
    
    try:
        # Set environment variable
        os.environ['OCR_SPACE_API_KEY'] = '8195ce015388957'
        
        from ocr_space_client import OCRRSpaceClient
        
        client = OCRRSpaceClient('8195ce015388957')
        
        # Create a simple test image
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        text = "LINEO LETHALA\nDate of Birth: 04/04/2002\nCentre: LS547/140458570"
        draw.text((20, 20), text, fill='black')
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        img.save(temp_file.name, 'PNG')
        temp_file.close()
        
        print(f"Created test image: {temp_file.name}")
        
        # Test the client
        result = client.extract_text_from_file(temp_file.name, language='eng')
        
        print(f"Client Result:")
        print(f"  Text: {result.text[:100]}..." if len(result.text) > 100 else f"  Text: {result.text}")
        print(f"  Confidence: {result.confidence:.1f}%")
        print(f"  Processing Time: {result.processing_time:.2f}s")
        print(f"  Error: {result.error}")
        print(f"  API Used: {result.api_used}")
        
        # Clean up
        os.unlink(temp_file.name)
        
        return result.error is None and len(result.text) > 0
        
    except Exception as e:
        print(f"Client Error: {str(e)}")
        return False

def main():
    """Run simple tests"""
    print("=" * 50)
    print("Simple OCR.space API Test")
    print("=" * 50)
    
    # Test direct API call
    direct_success = test_ocr_space_simple()
    
    # Test client
    client_success = test_ocr_space_client()
    
    print("\n" + "=" * 50)
    print("RESULTS")
    print("=" * 50)
    print(f"Direct API Test: {'✓ PASSED' if direct_success else '✗ FAILED'}")
    print(f"Client Test: {'✓ PASSED' if client_success else '✗ FAILED'}")
    
    if direct_success or client_success:
        print("\n✓ OCR.space API integration is working!")
    else:
        print("\n✗ OCR.space API integration failed")

if __name__ == "__main__":
    main()
