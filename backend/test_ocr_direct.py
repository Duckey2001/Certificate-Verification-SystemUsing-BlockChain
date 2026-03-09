#!/usr/bin/env python3
"""
Direct test of OCR functionality without API
"""

import os
import sys
sys.path.append('/home/duckey/lgcse-project/backend')

from enhanced_lgcse_processor import EnhancedLGCSEProcessor

def test_ocr_direct():
    """Test OCR directly with the processor"""
    
    # Test file path
    test_file_path = "/home/duckey/lgcse-project/backend/uploads/certificates/dc942112-b126-4f19-a49f-a36bc26a0b8f.jpeg"
    
    try:
        print(f"🔍 Testing OCR directly with: {test_file_path}")
        
        # Initialize the processor
        processor = EnhancedLGCSEProcessor()
        
        # Process the certificate
        result = processor.process_certificate_file_enhanced(test_file_path)
        
        print("✅ OCR Processing Successful!")
        print(f"📋 Result: {result}")
        
        # Check if we have extracted data
        if "extracted_fields" in result:
            print("\n🎯 Extracted Fields:")
            for key, value in result["extracted_fields"].items():
                print(f"  {key}: {value}")
        
        if "validation" in result:
            print(f"\n📈 Validation Confidence: {result['validation'].get('confidence', 'N/A')}")
            
        return result
        
    except FileNotFoundError:
        print(f"❌ Test file not found: {test_file_path}")
        return None
    except Exception as e:
        print(f"❌ Error during OCR test: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    test_ocr_direct()
