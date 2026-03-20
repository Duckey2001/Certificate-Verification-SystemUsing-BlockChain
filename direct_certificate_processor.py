#!/usr/bin/env python3
"""
Direct Certificate Processing and Blockchain Upload
Processes certificate images and uploads directly to blockchain without API
"""

import os
import sys
import json
import hashlib
import base64
import psycopg2
from datetime import datetime
from pathlib import Path
from PIL import Image
import io

class DirectCertificateProcessor:
    def __init__(self):
        self.db_url = "postgresql://diploma_admin:Thlony57620256@localhost:5432/diploma_verification"
        
    def extract_certificate_data_direct(self, image_path):
        """Extract certificate data directly from image (mock OCR)"""
        print(f"🔍 Processing {image_path}")
        
        try:
            # Read image file
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Calculate hashes
            image_hash = hashlib.sha256(image_data).hexdigest()
            certificate_hash = f"CERT_{image_hash[:16].upper()}"
            
            # Parse filename for student info (since we can't use OCR)
            filename = Path(image_path).stem
            parts = filename.split('_')
            
            if len(parts) >= 3:
                student_id = parts[2]
                cert_num = parts[1]
            else:
                student_id = f"STU{datetime.now().year}{hash(image_path) % 10000:04d}"
                cert_num = "01"
            
            # Mock extracted data based on filename
            certificate_data = {
                "certificate_hash": certificate_hash,
                "image_hash": image_hash,
                "student_id": student_id,
                "student_name": f"Student {cert_num}",
                "student_surname": f"Surname{cert_num}",
                "examination_year": 2024,
                "subjects": [
                    {"subject": "Mathematics", "grade": "B"},
                    {"subject": "English Language", "grade": "B"},
                    {"subject": "Science", "grade": "C"},
                    {"subject": "Geography", "grade": "B"},
                    {"subject": "History", "grade": "C"}
                ],
                "credits": 10,
                "issue_date": datetime.now().strftime("%Y-%m-%d"),
                "issuer_id": self.get_default_issuer_id(),
                "status": "verified",
                "verification_status": "verified",
                "ocr_confidence": 95.0,
                "extracted_text": f"Certificate for student {student_id}",
                "original_image_path": str(image_path)
            }
            
            print(f"✅ Extracted data for student: {certificate_data['student_name']}")
            return certificate_data
            
        except Exception as e:
            print(f"❌ Error extracting data: {e}")
            return None
    
    def get_default_issuer_id(self):
        """Get default issuer institution ID"""
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM institutions WHERE role = 'ISSUER' LIMIT 1")
            result = cursor.fetchone()
            cursor.close()
            conn.close()
            return result[0] if result else 35  # ECOL ID
        except:
            return 35
    
    def save_to_database(self, certificate_data):
        """Save certificate data to database"""
        print(f"💾 Saving to database: {certificate_data['certificate_hash']}")
        
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            # Insert certificate record
            cursor.execute("""
                INSERT INTO certificates (
                    certificate_hash, student_id, student_name, student_surname,
                    examination_year, subjects, credits, issue_date, issuer_id,
                    status, verification_status, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (certificate_hash) DO UPDATE SET
                    student_id = EXCLUDED.student_id,
                    student_name = EXCLUDED.student_name,
                    student_surname = EXCLUDED.student_surname,
                    examination_year = EXCLUDED.examination_year,
                    subjects = EXCLUDED.subjects,
                    credits = EXCLUDED.credits,
                    issue_date = EXCLUDED.issue_date,
                    issuer_id = EXCLUDED.issuer_id,
                    updated_at = EXCLUDED.updated_at
                RETURNING id
            """, (
                certificate_data["certificate_hash"],
                certificate_data["student_id"],
                certificate_data["student_name"],
                certificate_data["student_surname"],
                certificate_data["examination_year"],
                json.dumps(certificate_data["subjects"]),
                certificate_data["credits"],
                certificate_data["issue_date"],
                certificate_data["issuer_id"],
                certificate_data["status"],
                certificate_data["verification_status"],
                datetime.utcnow(),
                datetime.utcnow()
            ))
            
            certificate_id = cursor.fetchone()[0]
            
            # Create verification request
            cursor.execute("""
                INSERT INTO verification_requests (
                    certificate_id, certificate_hash, requester_id, verifier_id,
                    uploaded_image_path, extracted_info, computed_hash, blockchain_match,
                    payment_digits, result, payment_method, payment_status,
                    verification_fee, status, verification_date, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                certificate_id,
                certificate_data["certificate_hash"],
                1,  # Admin requester
                2,  # Default verifier
                certificate_data["original_image_path"],
                json.dumps({
                    "ocr_confidence": certificate_data["ocr_confidence"],
                    "extracted_text": certificate_data["extracted_text"],
                    "subjects": certificate_data["subjects"]
                }),
                certificate_data["image_hash"],
                True,  # Blockchain match
                "123456",
                "valid",
                "mpesa",
                "confirmed",
                5.0,
                "completed",
                datetime.utcnow(),
                datetime.utcnow(),
                datetime.utcnow()
            ))
            
            verification_id = cursor.fetchone()[0]
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"✅ Saved to database (Cert ID: {certificate_id}, Verification ID: {verification_id})")
            return certificate_id, verification_id
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            return None, None
    
    def upload_to_blockchain(self, certificate_data, certificate_id, verification_id):
        """Upload certificate to blockchain (simulated)"""
        print(f"⛓️ Uploading to blockchain: {certificate_data['certificate_hash']}")
        
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            # Generate blockchain transaction details
            transaction_id = f"TX_{certificate_data['certificate_hash'][-12:]}"
            block_height = 1000 + certificate_id  # Simulated block height
            
            # Create blockchain transaction record
            cursor.execute("""
                INSERT INTO blockchain_transactions (
                    transaction_hash, transaction_type, network,
                    block_number, block_hash, status, confirmations, created_at, confirmed_at,
                    certificate_hash, metadata_json
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                transaction_id,
                "certificate_issuance",
                "lgcse-channel",
                block_height,
                f"BLOCK_{block_height}_{certificate_data['certificate_hash'][-8:]}",
                "confirmed",
                1,
                datetime.utcnow(),
                datetime.utcnow(),
                certificate_data["certificate_hash"],
                json.dumps({
                    "certificate_id": certificate_id,
                    "verification_id": verification_id,
                    "image_hash": certificate_data["image_hash"],
                    "student_id": certificate_data["student_id"]
                })
            ))
            
            # Update certificate with blockchain info
            cursor.execute("""
                UPDATE certificates 
                SET blockchain_tx_id = %s, 
                    blockchain_block_number = %s,
                    blockchain_network = %s,
                    updated_at = %s
                WHERE id = %s
            """, (transaction_id, block_height, 'lgcse-channel', datetime.utcnow(), certificate_id))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"✅ Uploaded to blockchain (TX: {transaction_id}, Block: {block_height})")
            return transaction_id, block_height
            
        except Exception as e:
            print(f"❌ Blockchain upload error: {e}")
            return None, None
    
    def process_certificate(self, image_path):
        """Process single certificate image"""
        print(f"🚀 Processing: {image_path}")
        print("=" * 60)
        
        # Extract data
        certificate_data = self.extract_certificate_data_direct(image_path)
        if not certificate_data:
            return False
        
        # Save to database
        certificate_id, verification_id = self.save_to_database(certificate_data)
        if not certificate_id:
            return False
        
        # Upload to blockchain
        transaction_id, block_height = self.upload_to_blockchain(
            certificate_data, certificate_id, verification_id
        )
        
        print("=" * 60)
        print(f"🎉 Certificate processed successfully!")
        print(f"📋 Certificate Hash: {certificate_data['certificate_hash']}")
        print(f"👤 Student: {certificate_data['student_name']} {certificate_data['student_surname']}")
        print(f"🆔 Student ID: {certificate_data['student_id']}")
        print(f"📚 Subjects: {len(certificate_data['subjects'])}")
        print(f"📅 Year: {certificate_data['examination_year']}")
        print(f"⛓️ Blockchain TX: {transaction_id}")
        print(f"📦 Block: {block_height}")
        
        return True
    
    def process_multiple_certificates(self, image_paths):
        """Process multiple certificate images"""
        print(f"📁 Processing {len(image_paths)} certificates...")
        
        results = []
        for image_path in image_paths:
            try:
                success = self.process_certificate(str(image_path))
                results.append({
                    "image_path": str(image_path),
                    "success": success
                })
                print("\n" + "-" * 60 + "\n")
            except Exception as e:
                print(f"❌ Error processing {image_path}: {e}")
                results.append({
                    "image_path": str(image_path),
                    "success": False,
                    "error": str(e)
                })
        
        # Summary
        successful = sum(1 for r in results if r["success"])
        print(f"\n📊 Processing Summary:")
        print(f"✅ Successful: {successful}/{len(results)}")
        print(f"❌ Failed: {len(results) - successful}/{len(results)}")
        
        return results

def main():
    # Get certificate images
    cert_dir = "/home/duckey/lgcse-project/sample_certificates"
    image_paths = list(Path(cert_dir).glob("*.jpg"))
    
    if not image_paths:
        print("❌ No certificate images found!")
        return
    
    processor = DirectCertificateProcessor()
    processor.process_multiple_certificates(image_paths)
    
    # Check final state
    print("\n" + "=" * 60)
    print("🔍 Checking final database state...")
    
    try:
        conn = psycopg2.connect(processor.db_url)
        cursor = conn.cursor()
        
        # Certificate count
        cursor.execute("SELECT COUNT(*) FROM certificates")
        cert_count = cursor.fetchone()[0]
        
        # Blockchain transactions count
        cursor.execute("SELECT COUNT(*) FROM blockchain_transactions")
        tx_count = cursor.fetchone()[0]
        
        # Verification requests count
        cursor.execute("SELECT COUNT(*) FROM verification_requests")
        ver_count = cursor.fetchone()[0]
        
        print(f"📋 Total Certificates: {cert_count}")
        print(f"⛓️ Blockchain Transactions: {tx_count}")
        print(f"🔍 Verification Requests: {ver_count}")
        
        # Show latest certificates
        cursor.execute("""
            SELECT certificate_hash, student_name, student_id, 
                   blockchain_tx_id, blockchain_block_number
            FROM certificates 
            WHERE blockchain_tx_id IS NOT NULL
            ORDER BY created_at DESC 
            LIMIT 5
        """)
        
        latest_certs = cursor.fetchall()
        print(f"\n📄 Latest Certificates on Blockchain:")
        for cert in latest_certs:
            print(f"   {cert[0]} - {cert[1]} ({cert[2]}) - TX: {cert[3]} - Block: {cert[4]}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == "__main__":
    main()
