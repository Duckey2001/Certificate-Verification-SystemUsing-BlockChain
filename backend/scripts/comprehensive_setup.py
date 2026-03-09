#!/usr/bin/env python3
"""
Comprehensive setup script for CertiVert system.
Generates proper credentials, creates users, and initializes the database.
"""

import os
import sys
import random
import string
from datetime import datetime, timedelta
from passlib.context import CryptContext

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import engine, SessionLocal
from models import (
    Base, User, Institution, Notification, SystemActivity, 
    CreditTransaction, BlockchainTransaction
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def generate_password(length=12):
    """Generate secure random password"""
    chars = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(chars) for _ in range(length))

def generate_phone_number():
    """Generate Lesotho phone number"""
    return f"+266{random.randint(10000000, 99999999)}"

def generate_wallet_address():
    """Generate mock blockchain wallet address"""
    return "0x" + ''.join(random.choice(string.hexdigits.lower()) for _ in range(40))

def create_tables():
    """Create all database tables"""
    print("🔧 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created successfully")

def create_institutions():
    """Create default institutions"""
    print("🏛️ Setting up institutions...")
    db = SessionLocal()
    try:
        institutions = [
            {
                "code": "ECL001",
                "name": "Ecol",
                "role": "ISSUER"
            },
            {
                "code": "LNU001", 
                "name": "National University of Lesotho",
                "role": "ISSUER"
            },
            {
                "code": "MOT001",
                "name": "Ministry of Education",
                "role": "VERIFIER"
            },
            {
                "code": "EXM001",
                "name": "Examination Council",
                "role": "VERIFIER"
            }
        ]
        
        for inst_data in institutions:
            existing = db.query(Institution).filter(Institution.code == inst_data["code"]).first()
            if not existing:
                inst = Institution(**inst_data)
                db.add(inst)
                print(f"✅ Created institution: {inst_data['name']}")
        
        db.commit()
        print("✅ Institutions setup complete")
        
    except Exception as e:
        print(f"❌ Error creating institutions: {e}")
        db.rollback()
    finally:
        db.close()

def create_system_users():
    """Create system users with proper credentials"""
    print("👥 Creating system users...")
    db = SessionLocal()
    try:
        # Admin user
        admin_password = generate_password()
        admin_user = {
            "username": "admin",
            "email": "admin@certivert.com",
            "password_hash": pwd_context.hash(admin_password),
            "role": "admin",
            "first_name": "System",
            "last_name": "Administrator",
            "is_active": True,
            "is_verified": True,
            "available_credits": 1000,
            "blockchain_wallet_address": generate_wallet_address(),
            "institution_code": None
        }
        
        existing_admin = db.query(User).filter(User.username == "admin").first()
        if not existing_admin:
            admin = User(**admin_user)
            db.add(admin)
            db.flush()
            print(f"✅ Created admin user: admin@certivert.com")
            print(f"🔑 Admin password: {admin_password}")
        
        # Ecol Issuer
        issuer_password = generate_password()
        issuer_user = {
            "username": "issuer_ecol",
            "email": "issuer@ecol.ac.ls",
            "password_hash": pwd_context.hash(issuer_password),
            "role": "issuer",
            "first_name": "Ecol",
            "last_name": "Issuer",
            "phone_number": generate_phone_number(),
            "is_active": True,
            "is_verified": True,
            "available_credits": 150,
            "certificates_issued": 24,
            "ocr_scans_today": 3,
            "blockchain_wallet_address": generate_wallet_address(),
            "institution_code": "ECL001"
        }
        
        existing_issuer = db.query(User).filter(User.email == "issuer@ecol.ac.ls").first()
        if not existing_issuer:
            issuer = User(**issuer_user)
            db.add(issuer)
            db.flush()
            print(f"✅ Created issuer: issuer@ecol.ac.ls")
            print(f"🔑 Issuer password: {issuer_password}")
        
        # Sample Verifier
        verifier_password = generate_password()
        verifier_user = {
            "username": "verifier_mot",
            "email": "verifier@mot.gov.ls",
            "password_hash": pwd_context.hash(verifier_password),
            "role": "verifier",
            "first_name": "Ministry",
            "last_name": "Verifier",
            "phone_number": generate_phone_number(),
            "is_active": True,
            "is_verified": True,
            "available_credits": 200,
            "certificates_verified": 45,
            "blockchain_wallet_address": generate_wallet_address(),
            "institution_code": "MOT001"
        }
        
        existing_verifier = db.query(User).filter(User.email == "verifier@mot.gov.ls").first()
        if not existing_verifier:
            verifier = User(**verifier_user)
            db.add(verifier)
            db.flush()
            print(f"✅ Created verifier: verifier@mot.gov.ls")
            print(f"🔑 Verifier password: {verifier_password}")
        
        db.commit()
        
        # Create credit transactions for initial credits
        users = db.query(User).all()
        for user in users:
            if user.available_credits > 0:
                credit_tx = CreditTransaction(
                    user_id=user.id,
                    transaction_type="bonus",
                    amount=user.available_credits,
                    balance_before=0,
                    balance_after=user.available_credits,
                    description="Initial credit allocation",
                    metadata_json={"source": "system_setup"}
                )
                db.add(credit_tx)
        
        db.commit()
        print("✅ System users created successfully")
        
    except Exception as e:
        print(f"❌ Error creating users: {e}")
        db.rollback()
    finally:
        db.close()

def create_sample_activities():
    """Create sample system activities"""
    print("📊 Creating sample activities...")
    db = SessionLocal()
    try:
        activities = [
            {
                "activity_type": "certificate_issue",
                "actor_user_id": 2,  # Ecol issuer
                "actor_role": "issuer",
                "actor_name": "issuer_ecol",
                "title": "New certificate issued for John Doe",
                "description": "LGCSE certificate issued for John Doe in Mathematics",
                "status": "success",
                "impact_score": 7,
                "metadata_json": {"student_name": "John Doe", "certificate_type": "LGCSE"}
            },
            {
                "activity_type": "verification",
                "actor_user_id": 3,  # MOT verifier
                "actor_role": "verifier", 
                "actor_name": "verifier_mot",
                "title": "Certificate verified by Verifier",
                "description": "Certificate verification completed successfully",
                "status": "success",
                "impact_score": 5,
                "metadata_json": {"verification_method": "hash"}
            },
            {
                "activity_type": "payment",
                "title": "Payment of M300 received",
                "description": "M-Pesa payment received for credit purchase",
                "status": "success",
                "impact_score": 6,
                "metadata_json": {"amount": 300, "method": "mpesa"}
            },
            {
                "activity_type": "bulk_upload",
                "actor_user_id": 2,  # Ecol issuer
                "actor_role": "issuer",
                "actor_name": "issuer_ecol",
                "title": "Bulk upload of 5 certificates",
                "description": "Bulk certificate upload completed",
                "status": "success",
                "impact_score": 8,
                "metadata_json": {"count": 5, "upload_type": "bulk"}
            }
        ]
        
        for activity_data in activities:
            activity = SystemActivity(**activity_data)
            db.add(activity)
        
        db.commit()
        print("✅ Sample activities created")
        
    except Exception as e:
        print(f"❌ Error creating activities: {e}")
        db.rollback()
    finally:
        db.close()

def create_notifications():
    """Create initial notifications"""
    print("🔔 Creating notifications...")
    db = SessionLocal()
    try:
        users = db.query(User).all()
        
        for user in users:
            # Welcome notification
            welcome_notif = Notification(
                user_id=user.id,
                title="Welcome to CertiVert!",
                message="Your account has been successfully created. Start issuing or verifying certificates now.",
                notification_type="system",
                priority="medium",
                action_url="/dashboard",
                action_text="Go to Dashboard"
            )
            db.add(welcome_notif)
            
            # Role-specific notifications
            if user.role == "issuer":
                issuer_notif = Notification(
                    user_id=user.id,
                    title="Ready to Issue Certificates",
                    message=f"You have {user.available_credits} credits available for issuing certificates.",
                    notification_type="certificate_issued",
                    priority="high",
                    action_url="/certificates/issue",
                    action_text="Issue Certificate"
                )
                db.add(issuer_notif)
            elif user.role == "verifier":
                verifier_notif = Notification(
                    user_id=user.id,
                    title="Ready to Verify Certificates",
                    message="Start verifying certificates using the verification portal.",
                    notification_type="verified",
                    priority="medium",
                    action_url="/verify",
                    action_text="Verify Certificate"
                )
                db.add(verifier_notif)
        
        db.commit()
        print("✅ Notifications created")
        
    except Exception as e:
        print(f"❌ Error creating notifications: {e}")
        db.rollback()
    finally:
        db.close()

def verify_setup():
    """Verify the complete setup"""
    print("\n🔍 Verifying complete setup...")
    db = SessionLocal()
    try:
        # Check counts
        user_count = db.query(User).count()
        institution_count = db.query(Institution).count()
        activity_count = db.query(SystemActivity).count()
        notification_count = db.query(Notification).count()
        
        print(f"👥 Users: {user_count}")
        print(f"🏛️ Institutions: {institution_count}")
        print(f"📊 Activities: {activity_count}")
        print(f"🔔 Notifications: {notification_count}")
        
        # Show user credentials
        users = db.query(User).all()
        print("\n👤 User Credentials:")
        print("-" * 50)
        for user in users:
            print(f"📧 {user.email}")
            print(f"👤 {user.role.upper()}")
            print(f"💰 Credits: {user.available_credits}")
            print(f"🏛️ Institution: {user.institution_code}")
            print("-" * 50)
        
        print("✅ Setup verification complete")
        
    except Exception as e:
        print(f"❌ Verification error: {e}")
    finally:
        db.close()

def main():
    """Main setup function"""
    print("🚀 CertiVert Comprehensive System Setup")
    print("=" * 60)
    
    # Create tables
    create_tables()
    
    # Create institutions
    create_institutions()
    
    # Create system users
    create_system_users()
    
    # Create sample activities
    create_sample_activities()
    
    # Create notifications
    create_notifications()
    
    # Verify setup
    verify_setup()
    
    print("\n🎉 Comprehensive setup complete!")
    print("🌐 You can now login at: http://localhost:3000/login")
    print("\n📋 Default Credentials:")
    print("   Admin: admin@certivert.com (check generated password above)")
    print("   Issuer: issuer@ecol.ac.ls (check generated password above)")
    print("   Verifier: verifier@mot.gov.ls (check generated password above)")

if __name__ == "__main__":
    main()
