#!/usr/bin/env python3
"""
Create sample data for dashboard testing - SQL version
"""

import os
import sys
from datetime import datetime, timedelta
import psycopg2
from passlib.context import CryptContext

# Database connection
DATABASE_URL = "postgresql://diploma_admin:Thlony57620256@localhost:5432/diploma_verification"

# Password context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_sample_data():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    try:
        print("Creating sample data for dashboards...")
        
        # Create institutions
        institutions = [
            ("MOE", "Ministry of Education", "ISSUER"),
            ("ECOL", "Examination Council of Lesotho", "ISSUER"),
            ("LU", "Lerotholi University", "VERIFIER"),
            ("NUL", "National University of Lesotho", "VERIFIER"),
        ]
        
        for code, name, role in institutions:
            cursor.execute("SELECT id FROM institutions WHERE code = %s", (code,))
            if cursor.fetchone() is None:
                cursor.execute(
                    "INSERT INTO institutions (code, name, role, created_at, updated_at) VALUES (%s, %s, %s, %s, %s)",
                    (code, name, role, datetime.utcnow(), datetime.utcnow())
                )
        
        conn.commit()
        print("✓ Created institutions")
        
        # Create users
        users = [
            ("admin", "admin@certivert.com", "admin", None, "System", "Administrator"),
            ("issuer1", "issuer@ecol.org", "issuer", "ECOL", "Certificate", "Issuer"),
            ("verifier1", "verifier@nul.ac.ls", "verifier", "NUL", "Certificate", "Verifier"),
            ("student1", "student@example.com", "pending", None, "John", "Student"),
        ]
        
        user_ids = {}
        for username, email, role, inst_code, first_name, last_name in users:
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone() is None:
                password_hash = pwd_context.hash(username + "123")
                cursor.execute(
                    """
                    INSERT INTO users (username, email, password_hash, role, institution_code, 
                                     first_name, last_name, is_active, is_verified, 
                                     certificates_issued, certificates_verified, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (username, email, password_hash, role, inst_code, first_name, last_name,
                     True, True, 0, 0, datetime.utcnow(), datetime.utcnow())
                )
                user_ids[username] = cursor.fetchone()[0]
            else:
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                user_ids[username] = cursor.fetchone()[0]
        
        conn.commit()
        print("✓ Created users")
        
        # Create sample certificates
        certificates = []
        for i in range(10):
            cert_date = datetime.utcnow() - timedelta(days=i*3)
            cursor.execute(
                """
                INSERT INTO certificates (certificate_hash, student_id, student_name, student_surname,
                                         examination_year, subjects, credits, issue_date, issuer_id,
                                         status, verification_status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (f"cert_hash_{i:03d}", f"STU{2023000 + i}", f"Student {i+1}", f"Surname{i+1}",
                 2023, '[{"subject": "Mathematics", "grade": "A"}, {"subject": "English", "grade": "B"}, {"subject": "Science", "grade": "C"}]',
                 6, cert_date.strftime("%Y-%m-%d"), user_ids["issuer1"],
                 "verified" if i % 2 == 0 else "pending",
                 "completed" if i % 2 == 0 else "pending",
                 cert_date, cert_date)
            )
            certificates.append(cursor.fetchone()[0])
        
        conn.commit()
        print("✓ Created certificates")
        
        # Create verification requests
        verifications = []
        for i in range(8):
            verif_date = datetime.utcnow() - timedelta(days=i*2)
            cursor.execute(
                """
                INSERT INTO verification_requests (certificate_id, certificate_hash, requester_id, verifier_id,
                                                  uploaded_image_path, extracted_info, computed_hash, blockchain_match,
                                                  payment_digits, result, payment_method, payment_status, verification_fee,
                                                  status, verification_date, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (certificates[i] if i < len(certificates) else None,
                 f"cert_hash_{i:03d}" if i < len(certificates) else f"hash_{i}",
                 user_ids["admin"], user_ids["verifier1"], 
                 f"/uploads/certificate_{i}.jpg",
                 '{"student_name": "Sample Student", "examination_year": 2023}',
                 f"computed_hash_{i}",
                 True if i % 2 == 0 else False,
                 "123456",
                 "valid" if i % 2 == 0 else "pending",
                 "mpesa", "confirmed" if i % 2 == 0 else "pending", 5.0,
                 "completed" if i % 2 == 0 else "pending",
                 verif_date if i % 2 == 0 else None,
                 verif_date, verif_date)
            )
            verifications.append(cursor.fetchone()[0])
        
        conn.commit()
        print("✓ Created verification requests")
        
        # Create payments
        for i, verification_id in enumerate(verifications):
            if i % 2 == 0:  # Only for confirmed payments
                verif_date = datetime.utcnow() - timedelta(days=i*2)
                cursor.execute(
                    """
                    INSERT INTO payments (id, verification_request_id, payer_user_id, method,
                                         reference, amount, currency, status, mpesa_transaction_id,
                                         confirmed_at, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (f"pay_{2023000 + i}", verification_id, user_ids["admin"], "mpesa_b2b",
                     f"REF{2023000 + i}", 5.0, "LSL", "confirmed", f"MPESA{2023000 + i}",
                     verif_date, verif_date)
                )
        
        conn.commit()
        print("✓ Created payments")
        
        # Create audit events
        event_types = [
            "user_registration", "certificate_issued", "verification_completed",
            "payment_completed", "user_login", "admin_login", "system_error",
            "certificate_revoked", "security_alert", "user_logout"
        ]
        
        for i in range(20):
            event_date = datetime.utcnow() - timedelta(hours=i*2)
            cursor.execute(
                """
                INSERT INTO audit_events (event_type, actor_user_id, actor_role,
                                        certificate_hash, verification_request_id,
                                        payload, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (event_types[i % len(event_types)],
                 user_ids["admin"] if i % 3 == 0 else user_ids["issuer1"],
                 "admin" if i % 3 == 0 else "issuer",
                 f"cert_hash_{i % len(certificates)}" if i < len(certificates) else None,
                 verifications[i % len(verifications)] if i < len(verifications) else None,
                 f'{{"message": "Sample event {i+1}", "details": "Event details for {event_types[i % len(event_types)]}"}}',
                 event_date)
            )
        
        conn.commit()
        print("✓ Created audit events")
        
        # Create notifications
        notification_types = [
            "certificate_issued", "verified", "payment", "system",
            "user_registered", "verification_completed", "payment_failed"
        ]
        
        for i in range(15):
            notif_date = datetime.utcnow() - timedelta(hours=i*3)
            cursor.execute(
                """
                INSERT INTO notifications (user_id, title, message, notification_type,
                                         priority, is_read, created_at, read_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (user_ids["admin"], f"Notification {i+1}",
                 f"This is a sample notification for {notification_types[i % len(notification_types)]}",
                 notification_types[i % len(notification_types)],
                 "high" if i % 4 == 0 else "medium" if i % 2 == 0 else "low",
                 False if i < 5 else True,
                 notif_date, notif_date if i >= 5 else None)
            )
        
        conn.commit()
        print("✓ Created notifications")
        
        # Create system activities
        activity_types = [
            "login", "certificate_issue", "verification", "payment",
            "user_registration", "admin_action", "system_backup"
        ]
        
        for i in range(25):
            activity_date = datetime.utcnow() - timedelta(hours=i)
            actor_user = user_ids["admin"] if i % 3 == 0 else user_ids["issuer1"] if i % 3 == 1 else user_ids["verifier1"]
            actor_role = "admin" if i % 3 == 0 else "issuer" if i % 3 == 1 else "verifier"
            actor_name = "System Administrator" if i % 3 == 0 else "Certificate Issuer" if i % 3 == 1 else "Certificate Verifier"
            
            cursor.execute(
                """
                INSERT INTO system_activities (activity_type, actor_user_id, actor_role, actor_name,
                                             institution_code, certificate_hash, verification_request_id,
                                             title, description, status, impact_score, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (activity_types[i % len(activity_types)], actor_user, actor_role, actor_name,
                 "ECOL" if i % 3 == 1 else None,
                 f"cert_hash_{i % len(certificates)}" if i < len(certificates) else None,
                 verifications[i % len(verifications)] if i < len(verifications) else None,
                 f"Activity {i+1}", f"Sample system activity for {activity_types[i % len(activity_types)]}",
                 "success" if i % 5 != 0 else "failed", (i % 10) + 1, activity_date)
            )
        
        conn.commit()
        print("✓ Created system activities")
        
        print("\n🎉 Sample data created successfully!")
        print("\n📊 Dashboard Summary:")
        print(f"   Users: 4")
        print(f"   Institutions: 4")
        print(f"   Certificates: 10")
        print(f"   Verifications: 8")
        print(f"   Payments: 4")
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
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_sample_data()
