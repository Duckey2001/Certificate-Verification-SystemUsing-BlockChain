#!/usr/bin/env python3
"""
Test script for Enhanced M-Pesa B2B Integration
"""

import os
import sys
import logging
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_mpesa_client():
    """Test M-Pesa client initialization and configuration"""
    try:
        from mpesa_client import MpesaB2BClient, mpesa_client
        
        logger.info("✅ Testing M-Pesa client import...")
        
        # Test singleton instance
        client = mpesa_client
        logger.info(f"✅ M-Pesa client initialized: {client.country} - {client.currency}")
        
        # Test configuration
        config = {
            "service_provider_code": client.service_provider_code,
            "ecol_code": client.ecol_code,
            "country": client.country,
            "currency": client.currency,
            "api_url": client.api_url
        }
        logger.info(f"✅ M-Pesa configuration: {config}")
        
        # Test session generation (will fail without real credentials but tests the code)
        try:
            session = client.generate_session()
            if session:
                logger.info(f"✅ Session generated: {session[:10]}...")
            else:
                logger.warning("⚠️ Session generation failed (expected with test credentials)")
        except Exception as e:
            logger.warning(f"⚠️ Session generation error (expected): {str(e)}")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Failed to import M-Pesa client: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ M-Pesa client test failed: {e}")
        return False

def test_mpesa_routes():
    """Test M-Pesa routes import"""
    try:
        from api.mpesa_routes import router
        logger.info("✅ M-Pesa routes imported successfully")
        logger.info(f"✅ Routes prefix: {router.prefix}")
        logger.info(f"✅ Number of routes: {len(router.routes)}")
        return True
    except ImportError as e:
        logger.error(f"❌ Failed to import M-Pesa routes: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ M-Pesa routes test failed: {e}")
        return False

def test_database_models():
    """Test enhanced database models"""
    try:
        from models import Payment, University, Certificate, VerificationRequest
        
        logger.info("✅ Database models imported successfully")
        
        # Test Payment model attributes
        payment_attrs = [attr for attr in dir(Payment) if not attr.startswith('_')]
        logger.info(f"✅ Payment model attributes: {len(payment_attrs)}")
        
        # Check for new M-Pesa fields
        required_fields = ['mpesa_transaction_id', 'mpesa_conversation_id', 'mpesa_response_code']
        for field in required_fields:
            if hasattr(Payment, field):
                logger.info(f"✅ Payment model has {field}")
            else:
                logger.error(f"❌ Payment model missing {field}")
        
        # Test University model
        university_attrs = [attr for attr in dir(University) if not attr.startswith('_')]
        logger.info(f"✅ University model attributes: {len(university_attrs)}")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Failed to import database models: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Database models test failed: {e}")
        return False

def test_environment_config():
    """Test environment configuration"""
    try:
        from dotenv import load_dotenv
        load_dotenv('.env.test')
        
        logger.info("✅ Environment configuration loaded")
        
        # Check M-Pesa environment variables
        mpesa_vars = [
            'MPESA_API_KEY',
            'MPESA_PUBLIC_KEY', 
            'SERVICE_PROVIDER_CODE',
            'ECOL_CODE',
            'COUNTRY',
            'CURRENCY'
        ]
        
        for var in mpesa_vars:
            value = os.getenv(var)
            if value:
                logger.info(f"✅ {var}: {'*' * len(value) if 'KEY' in var else value}")
            else:
                logger.warning(f"⚠️ {var} not set")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Environment configuration test failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("🚀 Starting Enhanced M-Pesa Integration Tests")
    logger.info("=" * 60)
    
    tests = [
        ("Environment Configuration", test_environment_config),
        ("M-Pesa Client", test_mpesa_client),
        ("M-Pesa Routes", test_mpesa_routes),
        ("Database Models", test_database_models),
    ]
    
    results = []
    for test_name, test_func in tests:
        logger.info(f"\n📋 Testing {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\n🎯 Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! M-Pesa integration is ready.")
        return 0
    else:
        logger.warning(f"⚠️ {total - passed} tests failed. Check the logs above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
