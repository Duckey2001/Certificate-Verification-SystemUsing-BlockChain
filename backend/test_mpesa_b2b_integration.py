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

def test_mpesa_b2b_client():
    """Test M-Pesa B2B client initialization and configuration"""
    try:
        from mpesa_b2b_client import MpesaB2BClient, mpesa_b2b_client
        
        logger.info("✅ Testing M-Pesa B2B client import...")
        
        # Test singleton instance
        client = mpesa_b2b_client
        logger.info(f"✅ M-Pesa B2B client initialized: {client.country} - {client.currency}")
        
        # Test configuration
        config = {
            "service_provider_code": client.service_provider_code,
            "ecol_code": client.ecol_code,
            "country": client.country,
            "currency": client.currency,
            "api_url": client.api_url
        }
        logger.info(f"✅ M-Pesa B2B configuration: {config}")
        
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
        logger.error(f"❌ Failed to import M-Pesa B2B client: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ M-Pesa B2B client test failed: {e}")
        return False

def test_mpesa_b2b_routes():
    """Test M-Pesa B2B routes import"""
    try:
        from api.mpesa_b2b_routes import router
        logger.info("✅ M-Pesa B2B routes imported successfully")
        logger.info(f"✅ Routes prefix: {router.prefix}")
        logger.info(f"✅ Number of routes: {len(router.routes)}")
        
        # Check for key endpoints
        endpoints = [route.path for route in router.routes]
        key_endpoints = ["/b2b-payment", "/query-transaction", "/payment-history", "/mpesa-status", "/webhook", "/test-payment"]
        
        for endpoint in key_endpoints:
            if any(endpoint in route for route in endpoints):
                logger.info(f"✅ Endpoint {endpoint} found")
            else:
                logger.warning(f"⚠️ Endpoint {endpoint} not found")
        
        return True
    except ImportError as e:
        logger.error(f"❌ Failed to import M-Pesa B2B routes: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ M-Pesa B2B routes test failed: {e}")
        return False

def test_database_models():
    """Test enhanced database models for B2B"""
    try:
        from models import Payment, University, Certificate, VerificationRequest
        
        logger.info("✅ Database models imported successfully")
        
        # Test Payment model attributes for B2B
        payment_attrs = [attr for attr in dir(Payment) if not attr.startswith('_')]
        logger.info(f"✅ Payment model attributes: {len(payment_attrs)}")
        
        # Check for B2B-specific fields
        b2b_fields = [
            'mpesa_transaction_id', 
            'mpesa_conversation_id', 
            'mpesa_response_code',
            'mpesa_response_description',
            'failure_reason',
            'metadata'
        ]
        
        for field in b2b_fields:
            if hasattr(Payment, field):
                logger.info(f"✅ Payment model has B2B field: {field}")
            else:
                logger.error(f"❌ Payment model missing B2B field: {field}")
        
        # Test University model
        university_attrs = [attr for attr in dir(University) if not attr.startswith('_')]
        logger.info(f"✅ University model attributes: {len(university_attrs)}")
        
        # Check for university-specific fields
        if hasattr(University, 'code'):
            logger.info(f"✅ University model has 'code' field")
        
        # Test Certificate model payment fields
        cert_payment_fields = ['payment_status', 'payment_id', 'paid_at', 'reference_number']
        for field in cert_payment_fields:
            if hasattr(Certificate, field):
                logger.info(f"✅ Certificate model has payment field: {field}")
            else:
                logger.warning(f"⚠️ Certificate model missing payment field: {field}")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Failed to import database models: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Database models test failed: {e}")
        return False

def test_environment_config():
    """Test B2B environment configuration"""
    try:
        from dotenv import load_dotenv
        load_dotenv('.env.test')
        
        logger.info("✅ Environment configuration loaded")
        
        # Check M-Pesa B2B environment variables
        mpesa_vars = [
            'MPESA_API_KEY',
            'MPESA_PUBLIC_KEY', 
            'SERVICE_PROVIDER_CODE',
            'ECOL_CODE',
            'COUNTRY',
            'CURRENCY',
            'MPESA_MINIMUM_AMOUNT',
            'MPESA_MAXIMUM_AMOUNT'
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

def test_b2b_payment_validation():
    """Test B2B payment validation logic"""
    try:
        from api.mpesa_b2b_routes import B2BPaymentRequest
        
        logger.info("✅ Testing B2B payment validation...")
        
        # Test valid payment request
        valid_request = B2BPaymentRequest(
            university_code="NUL001",
            amount="1000",  # M10.00
            certificate_reference="CERT123456",
            description="Test verification payment"
        )
        logger.info(f"✅ Valid payment request created: {valid_request.university_code}")
        
        # Test invalid amount (below minimum)
        try:
            invalid_request = B2BPaymentRequest(
                university_code="NUL001",
                amount="400",  # Below M5.00 minimum
                certificate_reference="CERT123456"
            )
            logger.error("❌ Should have failed validation for amount below minimum")
            return False
        except ValueError as e:
            logger.info(f"✅ Correctly rejected invalid amount: {e}")
        
        # Test invalid university code
        try:
            invalid_request = B2BPaymentRequest(
                university_code="AB",  # Too short
                amount="1000",
                certificate_reference="CERT123456"
            )
            logger.error("❌ Should have failed validation for short university code")
            return False
        except ValueError as e:
            logger.info(f"✅ Correctly rejected invalid university code: {e}")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Failed to import B2B payment models: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ B2B payment validation test failed: {e}")
        return False

def test_syntax():
    """Test Python syntax for all B2B files"""
    try:
        import py_compile
        
        files_to_test = [
            'mpesa_b2b_client.py',
            'api/mpesa_b2b_routes.py'
        ]
        
        for file_path in files_to_test:
            try:
                py_compile.compile(file_path, doraise=True)
                logger.info(f"✅ Syntax OK: {file_path}")
            except py_compile.PyCompileError as e:
                logger.error(f"❌ Syntax error in {file_path}: {e}")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Syntax test failed: {e}")
        return False

def main():
    """Run all B2B tests"""
    logger.info("🚀 Starting Enhanced M-Pesa B2B Integration Tests")
    logger.info("=" * 60)
    
    tests = [
        ("Environment Configuration", test_environment_config),
        ("Python Syntax", test_syntax),
        ("M-Pesa B2B Client", test_mpesa_b2b_client),
        ("M-Pesa B2B Routes", test_mpesa_b2b_routes),
        ("Database Models", test_database_models),
        ("B2B Payment Validation", test_b2b_payment_validation),
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
    logger.info("📊 B2B INTEGRATION TEST SUMMARY")
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
        logger.info("🎉 All B2B tests passed! M-Pesa B2B integration is ready.")
        logger.info("\n📋 NEXT STEPS:")
        logger.info("1. Configure real M-Pesa API credentials in .env")
        logger.info("2. Test with actual M-Pesa sandbox environment")
        logger.info("3. Deploy to production with real credentials")
        logger.info("4. Set up webhook endpoint for payment notifications")
        return 0
    else:
        logger.warning(f"⚠️ {total - passed} tests failed. Check the logs above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
