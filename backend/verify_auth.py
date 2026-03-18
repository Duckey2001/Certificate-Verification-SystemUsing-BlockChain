#!/usr/bin/env python3
"""
Simple Authentication Verification Script

This script verifies that the authentication system is properly configured
and provides instructions for testing registration and login.
"""

import os
import sys

def check_files():
    """Check if required files exist"""
    print("🔍 Checking required files...")
    
    required_files = [
        "api/auth.py",
        "models.py", 
        "database.py",
        "main.py"
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
        else:
            print(f"   ✅ {file}")
    
    if missing_files:
        print(f"   ❌ Missing files: {missing_files}")
        return False
    else:
        print("   ✅ All required files exist")
        return True

def check_database_file():
    """Check database configuration"""
    print("🗄️ Checking database configuration...")
    
    try:
        with open("database.py", "r") as f:
            content = f.read()
            
        if "sqlite" in content.lower():
            print("   ✅ SQLite database configured")
        elif "postgresql" in content.lower():
            print("   ✅ PostgreSQL database configured")
        else:
            print("   ⚠️ Database type not clearly identified")
        
        if "SessionLocal" in content:
            print("   ✅ Session factory configured")
        else:
            print("   ❌ Session factory not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to read database.py: {e}")
        return False

def check_auth_file():
    """Check authentication configuration"""
    print("🔐 Checking authentication configuration...")
    
    try:
        with open("api/auth.py", "r") as f:
            content = f.read()
        
        required_elements = [
            "register",
            "login", 
            "logout",
            "verify_token",
            "create_access_token",
            "get_current_user"
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in content:
                missing_elements.append(element)
            else:
                print(f"   ✅ {element} function found")
        
        if missing_elements:
            print(f"   ❌ Missing authentication functions: {missing_elements}")
            return False
        else:
            print("   ✅ All required authentication functions found")
        
        # Check for JWT configuration
        if "jwt" in content.lower() and "SECRET_KEY" in content:
            print("   ✅ JWT configuration found")
        else:
            print("   ❌ JWT configuration not found")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to read api/auth.py: {e}")
        return False

def check_models_file():
    """Check models configuration"""
    print("📋 Checking models configuration...")
    
    try:
        with open("models.py", "r") as f:
            content = f.read()
        
        required_models = [
            "User",
            "Session",
            "LoginActivity",
            "Institution"
        ]
        
        missing_models = []
        for model in required_models:
            if f"class {model}" not in content:
                missing_models.append(model)
            else:
                print(f"   ✅ {model} model found")
        
        if missing_models:
            print(f"   ❌ Missing models: {missing_models}")
            return False
        else:
            print("   ✅ All required models found")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to read models.py: {e}")
        return False

def check_environment():
    """Check environment variables"""
    print("🌍 Checking environment...")
    
    env_vars = {
        "SECRET_KEY": os.getenv("SECRET_KEY", "certivert-dev-secret"),
        "DATABASE_URL": os.getenv("DATABASE_URL", "sqlite:///./certivert.db")
    }
    
    for var, value in env_vars.items():
        if value:
            print(f"   ✅ {var}: {value[:50]}{'...' if len(value) > 50 else ''}")
        else:
            print(f"   ⚠️ {var}: Not set")
    
    return True

def create_test_instructions():
    """Create testing instructions"""
    print("\n📝 Authentication Testing Instructions")
    print("=" * 50)
    
    print("\n🚀 To start the backend server:")
    print("   cd backend")
    print("   python main.py")
    print("   # or")
    print("   uvicorn main:app --host 0.0.0.0 --port 8000")
    
    print("\n🧪 To test registration:")
    print("   curl -X POST http://localhost:8000/api/auth/register \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{")
    print("       \"username\": \"testuser\",")
    print("       \"email\": \"testuser@example.com\",")
    print("       \"password\": \"TestPassword123!\",")
    print("       \"role\": \"issuer\",")
    print("       \"institution_code\": \"ECOL\"")
    print("     }'")
    
    print("\n🔐 To test login:")
    print("   curl -X POST http://localhost:8000/api/auth/login \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{")
    print("       \"username\": \"testuser\",")
    print("       \"password\": \"TestPassword123!\"")
    print("     }'")
    
    print("\n🔍 To test token verification:")
    print("   # First get the token from login response")
    print("   curl -X GET http://localhost:8000/api/auth/verify \\")
    print("     -H 'Authorization: Bearer YOUR_TOKEN_HERE'")
    
    print("\n👤 To test user profile:")
    print("   curl -X GET http://localhost:8000/api/auth/me \\")
    print("     -H 'Authorization: Bearer YOUR_TOKEN_HERE'")
    
    print("\n🚪 To test logout:")
    print("   curl -X POST http://localhost:8000/api/auth/logout \\")
    print("     -H 'Authorization: Bearer YOUR_TOKEN_HERE'")
    
    print("\n📋 Expected Response Format:")
    print("   Registration/Login Response:")
    print("   {")
    print("     \"success\": true,")
    print("     \"access_token\": \"jwt_token_here\",")
    print("     \"token_type\": \"bearer\",")
    print("     \"user\": {")
    print("       \"id\": \"user_id\",")
    print("       \"username\": \"testuser\",")
    print("       \"email\": \"testuser@example.com\",")
    print("       \"role\": \"issuer\",")
    print("       \"institution\": {")
    print("         \"code\": \"ECOL\",")
    print("         \"name\": \"Ecol University\",")
    print("         \"role\": \"issuer\"")
    print("       }")
    print("     }")
    print("   }")
    
    print("\n🔧 Common Issues and Solutions:")
    print("   1. 'User already exists' - Use a different username/email")
    print("   2. 'Invalid credentials' - Check username and password")
    print("   3. 'Could not validate credentials' - Check token is valid")
    print("   4. 'Institution not found' - Use valid institution code (ECOL, LIMKOWING, BOTHO, NUL)")
    print("   5. 'Database error' - Check database connection and permissions")
    
    print("\n📚 Default Institutions:")
    print("   - ECOL: Ecol University (issuer)")
    print("   - LIMKOWING: Limkokwing University (verifier)")
    print("   - BOTHO: Botho University (verifier)")
    print("   - NUL: National University of Lesotho (verifier)")

def main():
    """Run authentication verification"""
    print("🔍 Authentication System Verification")
    print("=" * 50)
    
    # Check all components
    checks = [
        ("Files", check_files),
        ("Database", check_database_file),
        ("Authentication", check_auth_file),
        ("Models", check_models_file),
        ("Environment", check_environment)
    ]
    
    all_passed = True
    for name, check_func in checks:
        print(f"\n{name}:")
        if not check_func():
            all_passed = False
    
    if all_passed:
        print("\n✅ All checks passed! Authentication system is properly configured.")
        create_test_instructions()
    else:
        print("\n❌ Some checks failed. Please fix the issues above.")
        print("\n🔧 Common fixes:")
        print("   1. Install required dependencies: pip install fastapi sqlalchemy passlib python-jose bcrypt")
        print("   2. Ensure all required files exist in the correct locations")
        print("   3. Check database configuration in database.py")
        print("   4. Verify environment variables are set")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
