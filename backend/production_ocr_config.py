#!/usr/bin/env python3
"""
Production OCR Configuration - ECOL Optimized
Final optimized configuration for Examinations Council of Lesotho
"""

import os
import json
from typing import Dict, Any

# Production OCR Configuration
PRODUCTION_OCR_CONFIG = {
    "institution": {
        "name": "Examinations Council of Lesotho",
        "code": "ECOL",
        "type": "National Examination Board"
    },
    
    "ocr_engines": {
        "primary": "tesseract",  # Most reliable for ECOL certificates
        "secondary": "ocr_space",  # Good backup
        "tertiary": "gemini",  # Use when available
        "disabled": ["kolosal"]  # Skip due to auth issues
    },
    
    "processing": {
        "confidence_threshold": 75,  # High threshold for ECOL
        "timeout_seconds": 30,
        "max_retries": 2,
        "parallel_processing": False,  # Sequential for reliability
        "fallback_enabled": True
    },
    
    "certificate_validation": {
        "required_keywords": [
            "Examinations Council of Lesotho",
            "LGCSE",
            "Cambridge Assessment"
        ],
        "required_sections": [
            "certifies that",
            "Date of Birth",
            "Syllabus",
            "Grade"
        ],
        "supported_grades": ["A*", "A", "B", "C", "D", "E", "F", "G"],
        "certificate_types": ["LGCSE", "IGCSE"]
    },
    
    "extraction_patterns": {
        "student_name": r"certifies that.*?\\n\\s*([A-Z\\s]+)\\s*\\n",
        "date_of_birth": r"Date of Birth:\\s*(\\d{1,2}\\s+[A-Za-z]+\\s+\\d{4})",
        "candidate_number": r"Candidate Number:\\s*([A-Z0-9/]+)",
        "school": r"of\\s+([A-Z\\s]+HIGH SCHOOL)",
        "examination_session": r"examination of\\s+([A-Za-z]+\\s+(\\d{4}))",
        "certificate_number": r"Certificate Number:\\s*([A-Z0-9]+)",
        "subject_grade": r"([A-Za-z\\s]+)\\s+LGCSE\\s+([A-Z*]\\([a-z]\\))"
    },
    
    "api_priorities": {
        "reliability": {
            "tesseract": 95,      # Most reliable
            "ocr_space": 85,      # Good reliability
            "gemini": 70,         # Good but sometimes overloaded
            "google_vision": 60,  # Good if configured
            "kolosal": 20         # Last resort
        },
        "speed": {
            "tesseract": 80,       # Fast
            "ocr_space": 70,      # Moderate
            "gemini": 40,         # Slow but accurate
            "google_vision": 60,  # Moderate
            "kolosal": 50         # Moderate
        },
        "accuracy": {
            "gemini": 95,         # Most accurate when working
            "tesseract": 85,      # Good for certificates
            "ocr_space": 80,      # Good
            "google_vision": 85,  # Good
            "kolosal": 70         # Fair
        }
    },
    
    "error_handling": {
        "retry_failed_apis": True,
        "skip_on_auth_error": True,
        "log_all_errors": True,
        "fallback_to_tesseract": True,
        "minimum_confidence": 60
    },
    
    "output_format": {
        "include_raw_text": True,
        "include_confidence_scores": True,
        "include_processing_time": True,
        "include_api_comparison": True,
        "include_validation_details": True,
        "structured_data_only": False
    }
}

def apply_production_config():
    """Apply production OCR configuration"""
    
    # Set environment variables for production
    os.environ['OCR_CONFIDENCE_THRESHOLD'] = str(PRODUCTION_OCR_CONFIG['processing']['confidence_threshold'])
    os.environ['OCR_PREFERRED_API'] = PRODUCTION_OCR_CONFIG['ocr_engines']['primary']
    os.environ['OCR_FALLBACK_ENABLED'] = str(PRODUCTION_OCR_CONFIG['processing']['fallback_enabled']).lower()
    
    # Disable problematic APIs
    os.environ['KOLOSAL_ENABLED'] = 'false'
    
    print("🏛️  ECOL Production OCR Configuration Applied")
    print(f"   Institution: {PRODUCTION_OCR_CONFIG['institution']['name']}")
    print(f"   Primary OCR: {PRODUCTION_OCR_CONFIG['ocr_engines']['primary']}")
    print(f"   Confidence Threshold: {PRODUCTION_OCR_CONFIG['processing']['confidence_threshold']}%")
    print(f"   Disabled APIs: {', '.join(PRODUCTION_OCR_CONFIG['ocr_engines']['disabled'])}")
    
    return PRODUCTION_OCR_CONFIG

def get_production_status():
    """Get production OCR system status"""
    from multi_ocr_processor import MultiOCRProcessor
    
    processor = MultiOCRProcessor()
    api_status = processor.get_api_status()
    
    # Filter out disabled APIs
    active_apis = []
    for api_name, status in api_status.items():
        if api_name not in PRODUCTION_OCR_CONFIG['ocr_engines']['disabled'] and api_name != 'total_apis_available':
            active_apis.append({
                'name': api_name,
                'enabled': status['enabled'],
                'status': status['status'],
                'reliability': PRODUCTION_OCR_CONFIG['api_priorities']['reliability'].get(api_name, 0)
            })
    
    # Sort by reliability
    active_apis.sort(key=lambda x: x['reliability'], reverse=True)
    
    return {
        'production_config': PRODUCTION_OCR_CONFIG,
        'active_apis': active_apis,
        'total_active': len(active_apis),
        'primary_engine': PRODUCTION_OCR_CONFIG['ocr_engines']['primary'],
        'system_ready': len(active_apis) >= 2  # Need at least 2 working APIs
    }

def test_production_setup():
    """Test the production OCR setup"""
    print("🔧 Testing Production OCR Setup")
    print("=" * 50)
    
    # Apply production config
    config = apply_production_config()
    
    # Get status
    status = get_production_status()
    
    print(f"\\n📊 System Status:")
    print(f"   Active APIs: {status['total_active']}")
    print(f"   Primary Engine: {status['primary_engine']}")
    print(f"   System Ready: {'✅' if status['system_ready'] else '❌'}")
    
    print(f"\\n🚀 Active OCR Engines (by reliability):")
    for api in status['active_apis']:
        status_icon = "✅" if api['enabled'] else "❌"
        print(f"   {status_icon} {api['name']} - Reliability: {api['reliability']}%")
    
    # Test with sample certificate if available
    sample_cert = "./uploads/certificates/dc942112-b126-4f19-a49f-a36bc26a0b8f.jpeg"
    if os.path.exists(sample_cert):
        print(f"\\n🧪 Testing with sample certificate...")
        try:
            from ecol_ocr_processor import ECOLOCRProcessor
            processor = ECOLOCRProcessor()
            result = processor.process_ecol_certificate(sample_cert)
            
            print(f"   ✅ Test successful")
            print(f"   📊 Confidence: {result['processing_summary']['confidence']:.1f}%")
            print(f"   🏛️  ECOL Verified: {'✅' if result['ecol_verified'] else '❌'}")
            
        except Exception as e:
            print(f"   ❌ Test failed: {e}")
    
    return status

if __name__ == "__main__":
    test_production_setup()
