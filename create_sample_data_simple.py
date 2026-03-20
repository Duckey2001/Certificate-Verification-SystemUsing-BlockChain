#!/usr/bin/env python3
"""
Create sample data for dashboard testing - simplified version
"""

import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from passlib.context import CryptContext

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://diploma_admin:Thlony57620256@localhost:5432/diploma_verification")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Import models directly
sys.path.append('/home/duckey/lgcse-project/backend')
from models import Base, User, Certificate, VerificationRequest, Payment, AuditEvent, Institution, Notification, SystemActivity

def create_sample_data():
    db = SessionLocal()
    
    try:
        print("Creating sample data for dashboards...")
        
        # Create tables if they don't exist
        Base.metadata.create_all(bind=engine)
        print("✓ Database tables ready")
        
        # Create institutions
        institutions = [
            Institution(code="MOE", name="Ministry of Education", role="ISSUER"),
            Institution(code="ECOL", name="Examination Council of Lesotho", role="ISSUER"),
            Institution(code="LU", name="Lerotholi University", role="VERIFIER"),
            Institution(code="NUL", name="National University of Lesotho", role="VERIFIER"),
        ]
        
        for inst in institutions:
            existing = db.query(Institution).filter(Institution.code == inst.code).first()
            if not existing:
                db.add(inst)
        
        db.commit()
        print("✓ Created institutions")
        
        # Create users
        users = [
            {
                "username": "admin",
                "email": "admin@certivert.com",
                "password": "admin123",
                "role": "admin",
                "institution_code": None,
                "first_name": "System",
                "last_name": "Administrator"
            },
            {
                "username": "issuer1",
                "email": "issuer@ecol.org",
                "password": "issuer123",
                "role": "issuer",
                "institution_code": "ECOL",
                "first_name": "Certificate",
                "last_name": "Issuer"
            },
            {
                "username": "verifier1",
                "email": "verifier@nul.ac.ls",
                "password": "verifier123",
                "role": "verifier",
                "institution_code": "NUL",
                "first_name": "Certificate",
                "last_name": "Verifier"
            },
            {
                "username": "student1",
                "email": "student@example.com",
                "password": "student123",
                "role": "pending",
                "institution_code": None,
                "first_name": "John",
                "last_name": "Student"
            }
        ]
        
        created_users = []
        for user_data in users:
            existing = db.query(User).filter(User.email == user_data["email"]).first()
            if not existing:
                user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    password_hash=pwd_context.hash(user_data["password"]),
                    role=user_data["role"],
                    institution_code=user_data["institution_code"],
                    first_name=user_data["first_name"],
                    last_name=user_data["last_name"],
                    is_active=True,
                    is_verified=True,
                    certificates_issued=0,
                    certificates_verified=0
                )
                db.add(user)
                created_users.append(user)
        
        db.commit()
        print("✓ Created users")
        
        # Get the created users for relationships
        admin_user = db.query(User).filter(User.email == "admin@certivert.com").first()
        issuer_user = db.query(User).filter(User.email == "issuer@ecol.org").first()
        verifier_user = db.query(User).filter(User.email == "verifier@nul.ac.ls").first()
        
        # Create sample certificates
        certificates = []
        for i in range(10):
            cert_date = datetime.utcnow() - timedelta(days=i*3)
            cert = Certificate(
                certificate_hash=f"cert_hash_{i:03d}",
                student_id=f"STU{2023000 + i}",
                student_name=f"Student {i+1}",
                student_surname=f"Surname{i+1}",
                examination_year=2023,
                subjects=[
                    {"subject": "Mathematics", "grade": "A"},
                    {"subject": "English", "grade": "B"},
                    {"subject": "Science", "grade": "C"}
                ],
                credits=6,
                issue_date=cert_date.strftime("%Y-%m-%d"),
                issuer_id=issuer_user.id,
                status="verified" if i % 2 == 0 else "pending",
                verification_status="completed" if i % 2 == 0 else "pending",
                created_at=cert_date
            )
            certificates.append(cert)
            db.add(cert)
        
        db.commit()
        print("✓ Created certificates")
        
        # Create verification requests
        verifications = []
        for i in range(8):
            verif_date = datetime.utcnow() - timedelta(days=i*2)
            verification = VerificationRequest(
                certificate_id=certificates[i].id if i < len(certificates) else None,
                certificate_hash=certificates[i].certificate_hash if i < len(certificates) else f"hash_{i}",
                requester_id=admin_user.id,
                verifier_id=verifier_user.id,
                payment_method="mpesa",
                payment_status="confirmed" if i % 2 == 0 else "pending",
                verification_fee=5.0,
                status="completed" if i % 2 == 0 else "pending",
                result="valid" if i % 2 == 0 else None,
                verification_date=verif_date if i % 2 == 0 else None,
                created_at=verif_date
            )
            verifications.append(verification)
            db.add(verification)
        
        db.commit()
        print("✓ Created verification requests")
        
        # Create payments
        payments = []
        for i, verification in enumerate(verifications):
            if verification.payment_status == "confirmed":
                payment = Payment(
                    verification_request_id=verification.id,
                    payer_user_id=verification.requester_id,
                    method="mpesa_b2b",
                    reference=f"REF{2023000 + i}",
                    amount=5.0,
                    status="confirmed",
                    mpesa_transaction_id=f"MPESA{2023000 + i}",
                    confirmed_at=verification.verification_date,
                    created_at=verification.created_at
                )
                payments.append(payment)
                db.add(payment)
        
        db.commit()
        print("✓ Created payments")
        
        # Create audit events
        event_types = [
            "user_registration", "certificate_issued", "verification_completed",
            "payment_completed", "user_login", "admin_login", "system_error",
            "certificate_revoked", "security_alert", "user_logout"
        ]
        
        for i in range(20):
            event_date = datetime.utcnow() - timedelta(hours=i*2)
            event = AuditEvent(
                event_type=event_types[i % len(event_types)],
                actor_user_id=admin_user.id if i % 3 == 0 else issuer_user.id,
                actor_role=admin_user.role if i % 3 == 0 else issuer_user.role,
                certificate_hash=certificates[i % len(certificates)].certificate_hash if i < len(certificates) else None,
                verification_request_id=verifications[i % len(verifications)].id if i < len(verifications) else None,
                payload={"message": f"Sample event {i+1}", "details": f"Event details for {event_types[i % len(event_types)]}"},
                created_at=event_date
            )
            db.add(event)
        
        db.commit()
        print("✓ Created audit events")
        
        # Create notifications
        notification_types = [
            "certificate_issued", "verified", "payment", "system",
            "user_registered", "verification_completed", "payment_failed"
        ]
        
        for i in range(15):
            notif_date = datetime.utcnow() - timedelta(hours=i*3)
            notification = Notification(
                user_id=admin_user.id,
                title=f"Notification {i+1}",
                message=f"This is a sample notification for {notification_types[i % len(notification_types)]}",
                notification_type=notification_types[i % len(notification_types)],
                priority="high" if i % 4 == 0 else "medium" if i % 2 == 0 else "low",
                is_read=False if i < 5 else True,
                created_at=notif_date,
                read_at=notif_date if i >= 5 else None
            )
            db.add(notification)
        
        db.commit()
        print("✓ Created notifications")
        
        # Create system activities
        activity_types = [
            "login", "certificate_issue", "verification", "payment",
            "user_registration", "admin_action", "system_backup"
        ]
        
        for i in range(25):
            activity_date = datetime.utcnow() - timedelta(hours=i)
            activity = SystemActivity(
                activity_type=activity_types[i % len(activity_types)],
                actor_user_id=admin_user.id if i % 3 == 0 else issuer_user.id if i % 3 == 1 else verifier_user.id,
                actor_role=admin_user.role if i % 3 == 0 else issuer_user.role if i % 3 == 1 else verifier_user.role,
                actor_name=f"{admin_user.first_name} {admin_user.last_name}" if i % 3 == 0 else f"{issuer_user.first_name} {issuer_user.last_name}" if i % 3 == 1 else f"{verifier_user.first_name} {verifier_user.last_name}",
                institution_code=issuer_user.institution_code if i % 3 == 1 else None,
                certificate_hash=certificates[i % len(certificates)].certificate_hash if i < len(certificates) else None,
                verification_request_id=verifications[i % len(verifications)].id if i < len(verifications) else None,
                payment_id=payments[i % len(payments)].id if i < len(payments) and payments[i % len(payments)] else None,
                title=f"Activity {i+1}",
                description=f"Sample system activity for {activity_types[i % len(activity_types)]}",
                status="success" if i % 5 != 0 else "failed",
                impact_score=(i % 10) + 1,
                created_at=activity_date
            )
            db.add(activity)
        
        db.commit()
        print("✓ Created system activities")
        
        print("\n🎉 Sample data created successfully!")
        print("\n📊 Dashboard Summary:")
        print(f"   Users: {len(created_users) + 1}")
        print(f"   Institutions: 4")
        print(f"   Certificates: {len(certificates)}")
        print(f"   Verifications: {len(verifications)}")
        print(f"   Payments: {len(payments)}")
        print(f"   Audit Events: 20")
        print(f"   Notifications: 15")
        print(f"   System Activities: 25")
        
        print("\n🔑 Login Credentials:")
        print("   Admin: admin@certivert.com / admin123")
        print("   Issuer: issuer@ecol.org / issuer123")
        print("   Verifier: verifier@nul.ac.ls / verifier123")
        print("   Student: student@example.com / student123")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_data()
