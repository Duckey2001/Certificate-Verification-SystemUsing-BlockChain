#!/usr/bin/env python3
"""
Certificate Issuance and Blockchain Verification Script
Check if certificates are issued and stored on blockchain
"""

import os
import sys
import json
import sqlite3
import requests
from pathlib import Path

# Add paths
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'blockchain'))

def check_database_certificates():
    """Check certificates in database"""
    print("🗄️  DATABASE CERTIFICATE STATUS")
    print("=" * 50)
    
    db_path = os.path.join(os.path.dirname(__file__), 'certivert.db')
    
    if not os.path.exists(db_path):
        print("❌ Database file not found")
        return []
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT COUNT(*) FROM certificates')
        total = cursor.fetchone()[0]
        print(f"📊 Total Certificates: {total}")
        
        cursor.execute('''
            SELECT id, student_name, student_surname, student_id, examination_year,
                   subjects, status, certificate_hash, blockchain_tx_id, 
                   blockchain_network, created_at, extracted_data
            FROM certificates 
            ORDER BY created_at DESC
        ''')
        
        certs = cursor.fetchall()
        
        certificates = []
        for cert in certs:
            cert_id, name, surname, student_id, year, subjects, status, 
            cert_hash, tx_id, network, created, extracted_data = cert
            
            cert_info = {
                'id': cert_id,
                'student_name': f"{name} {surname}".strip(),
                'student_id': student_id,
                'examination_year': year,
                'status': status,
                'certificate_hash': cert_hash,
                'blockchain_tx_id': tx_id,
                'blockchain_network': network,
                'created_at': created,
                'subjects': json.loads(subjects) if subjects else [],
                'extracted_data': json.loads(extracted_data) if extracted_data else {}
            }
            certificates.append(cert_info)
        
        # Display certificates
        for i, cert in enumerate(certificates, 1):
            print(f"\\n📜 Certificate #{i}")
            print(f"   Student: {cert['student_name']}")
            print(f"   ID: {cert['student_id']}")
            print(f"   Year: {cert['examination_year']}")
            print(f"   Status: {cert['status']}")
            print(f"   Hash: {cert['certificate_hash'][:16]}...")
            print(f"   Blockchain TX: {cert['blockchain_tx_id'] or 'Not on blockchain'}")
            print(f"   Network: {cert['blockchain_network'] or 'Not specified'}")
            print(f"   Subjects: {len(cert['subjects'])}")
            print(f"   Created: {cert['created_at']}")
        
        conn.close()
        return certificates
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        conn.close()
        return []

def check_blockchain_status():
    """Check blockchain network status"""
    print("\\n⛓️  BLOCKCHAIN NETWORK STATUS")
    print("=" * 50)
    
    # Check deployment file
    deployment_file = os.path.join(os.path.dirname(__file__), '..', 'blockchain', 'deployment-localhost.json')
    
    if os.path.exists(deployment_file):
        with open(deployment_file, 'r') as f:
            deployment = json.load(f)
        
        print(f"🌐 Network: {deployment['network']}")
        print(f"📅 Deployed: {deployment['timestamp']}")
        print(f"👤 Deployer: {deployment['deployer']}")
        print(f"📋 Contracts:")
        for name, address in deployment['contracts'].items():
            print(f"   {name}: {address}")
    else:
        print("❌ No deployment file found")
    
    # Check if Hardhat node is running
    try:
        response = requests.get('http://localhost:8545', timeout=5)
        if response.status_code == 200:
            print("✅ Hardhat node running")
        else:
            print("⚠️  Hardhat node responding but unexpected status")
    except:
        print("❌ Hardhat node not running")
    
    return deployment_file

def verify_certificates_on_blockchain(certificates):
    """Verify certificates on blockchain"""
    print("\\n🔍 BLOCKCHAIN VERIFICATION")
    print("=" * 50)
    
    if not certificates:
        print("❌ No certificates to verify")
        return
    
    # Load deployment info
    deployment_file = os.path.join(os.path.dirname(__file__), '..', 'blockchain', 'deployment-localhost.json')
    
    if not os.path.exists(deployment_file):
        print("❌ Cannot verify - no blockchain deployment")
        return
    
    with open(deployment_file, 'r') as f:
        deployment = json.load(f)
    
    contract_address = deployment['contracts']['CertificateRegistry']
    
    print(f"📋 Verifying against CertificateRegistry: {contract_address}")
    
    # For each certificate, check if it's on blockchain
    for cert in certificates:
        print(f"\\n🔍 Verifying Certificate #{cert['id']}")
        
        if not cert['blockchain_tx_id']:
            print("   ❌ No blockchain transaction ID")
            continue
        
        print(f"   📜 Hash: {cert['certificate_hash'][:16]}...")
        print(f"   🔗 TX: {cert['blockchain_tx_id']}")
        print(f"   🌐 Network: {cert['blockchain_network']}")
        
        # Try to verify using web3 if available
        try:
            from web3 import Web3
            
            # Connect to Hardhat
            w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
            
            if w3.is_connected():
                # Check transaction
                try:
                    tx = w3.eth.get_transaction(cert['blockchain_tx_id'])
                    print(f"   ✅ Transaction found on blockchain")
                    print(f"   📊 Block: {tx.blockNumber}")
                    print(f"   👤 From: {tx['from']}")
                    print(f"   📍 To: {tx['to']}")
                    
                    # Get transaction receipt
                    receipt = w3.eth.get_transaction_receipt(cert['blockchain_tx_id'])
                    print(f"   📈 Gas Used: {receipt.gasUsed}")
                    print(f"   ✅ Status: {'Success' if receipt.status == 1 else 'Failed'}")
                    
                except Exception as e:
                    print(f"   ⚠️  Transaction verification failed: {e}")
            else:
                print("   ❌ Cannot connect to blockchain")
                
        except ImportError:
            print("   ⚠️  Web3 not available - cannot verify on blockchain")
        except Exception as e:
            print(f"   ❌ Verification error: {e}")

def check_frontend_integration():
    """Check frontend integration status"""
    print("\\n🖥️  FRONTEND INTEGRATION STATUS")
    print("=" * 50)
    
    frontend_dir = os.path.join(os.path.dirname(__file__), '..', 'frontend')
    
    if os.path.exists(frontend_dir):
        print(f"📁 Frontend directory: {frontend_dir}")
        
        # Check for key frontend files
        key_files = [
            'src/App.js',
            'src/App.jsx',
            'package.json',
            'src/api/certificates.js',
            'src/components/CertificateVerification.js'
        ]
        
        for file_path in key_files:
            full_path = os.path.join(frontend_dir, file_path)
            if os.path.exists(full_path):
                print(f"   ✅ {file_path}")
            else:
                print(f"   ❌ {file_path}")
        
        # Check if frontend server can be started
        try:
            package_json = os.path.join(frontend_dir, 'package.json')
            if os.path.exists(package_json):
                with open(package_json, 'r') as f:
                    package = json.load(f)
                
                scripts = package.get('scripts', {})
                print(f"\\n📜 Available scripts:")
                for script, command in scripts.items():
                    print(f"   {script}: {command}")
        
        except Exception as e:
            print(f"❌ Error checking frontend: {e}")
    else:
        print("❌ Frontend directory not found")

def generate_certificate_summary(certificates):
    """Generate summary of certificate issuance"""
    print("\\n📊 CERTIFICATE ISSUANCE SUMMARY")
    print("=" * 50)
    
    if not certificates:
        print("❌ No certificates issued")
        return
    
    # Count certificates by status
    status_counts = {}
    year_counts = {}
    blockchain_count = 0
    
    for cert in certificates:
        status = cert['status']
        year = cert['examination_year']
        
        status_counts[status] = status_counts.get(status, 0) + 1
        year_counts[year] = year_counts.get(year, 0) + 1
        
        if cert['blockchain_tx_id']:
            blockchain_count += 1
    
    print(f"📈 Total Issued: {len(certificates)}")
    print(f"⛓️  On Blockchain: {blockchain_count}/{len(certificates)}")
    print(f"📊 Blockchain Rate: {(blockchain_count/len(certificates)*100):.1f}%")
    
    print(f"\\n📋 By Status:")
    for status, count in status_counts.items():
        print(f"   {status}: {count}")
    
    print(f"\\n📅 By Year:")
    for year, count in sorted(year_counts.items()):
        print(f"   {year}: {count}")
    
    # Show recent activity
    print(f"\\n⏰ Recent Activity:")
    for cert in certificates[:3]:  # Show last 3
        print(f"   {cert['created_at']}: {cert['student_name']} ({cert['status']})")

def main():
    """Main verification function"""
    print("🔍 CERTIFICATE ISSUANCE & BLOCKCHAIN VERIFICATION")
    print("=" * 60)
    
    # 1. Check database certificates
    certificates = check_database_certificates()
    
    # 2. Check blockchain status
    blockchain_status = check_blockchain_status()
    
    # 3. Verify certificates on blockchain
    verify_certificates_on_blockchain(certificates)
    
    # 4. Check frontend integration
    check_frontend_integration()
    
    # 5. Generate summary
    generate_certificate_summary(certificates)
    
    print("\\n🎯 RECOMMENDATIONS FOR FRONTEND:")
    print("=" * 50)
    
    if certificates:
        print("✅ Certificates are issued and stored in database")
        
        if any(cert['blockchain_tx_id'] for cert in certificates):
            print("✅ Some certificates are on blockchain")
            print("💡 Frontend should:")
            print("   - Display certificate verification status")
            print("   - Show blockchain transaction links")
            print("   - Allow search by certificate hash")
            print("   - Display student details and subjects")
        else:
            print("⚠️  No certificates on blockchain")
            print("💡 Frontend should:")
            print("   - Show database certificate status")
            print("   - Indicate pending blockchain storage")
    else:
        print("❌ No certificates issued")
        print("💡 Frontend should:")
        print("   - Show certificate issuance interface")
        print("   - Guide users through certificate upload")
    
    print("\\n🚀 NEXT STEPS:")
    print("1. Ensure Hardhat blockchain node is running")
    print("2. Test certificate issuance from frontend")
    print("3. Implement certificate verification UI")
    print("4. Add blockchain transaction viewing")

if __name__ == "__main__":
    main()
