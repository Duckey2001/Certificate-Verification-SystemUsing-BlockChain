#!/usr/bin/env python3
"""
Update blockchain nodes with correct names and setup deployment system
"""

import os
import sys
import psycopg2
from datetime import datetime

# Database connection
DATABASE_URL = "postgresql://diploma_admin:Thlony57620256@localhost:5432/diploma_verification"

def update_blockchain_nodes():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    try:
        print("Updating blockchain nodes with correct names...")
        
        # Clear existing nodes (delete in correct order due to foreign keys)
        cursor.execute("DELETE FROM node_activity_logs")
        cursor.execute("DELETE FROM chaincode_deployments")
        cursor.execute("DELETE FROM blockchain_nodes")
        
        # Insert correct nodes with ECOL as main issuer
        nodes = [
            # ECOL - Main Issuer (Primary node)
            ("NODE_ECOL_001", 1, "peer", "fabric", "https://peer0.ecol.example.com", 7051, 
             True, "/etc/hyperledger/fabric/tls/server.crt", "/etc/hyperledger/fabric/tls/server.key", "/etc/hyperledger/fabric/tls/ca.crt",
             "EcolOrgMSP", "peer0.ecol.example.com", "orderer.example.com", 
             None, None, "{}", "certificate_chaincode", "1.0.0", "/opt/gopath/src/github.com/chaincode/certificate",
             False, False, "lgcse-channel", "inactive", None, None, 0, 0, "{}", None, "/opt/gopath/src/github.com/hyperledger/fabric/.build/bin/configtxlator",
             "/opt/gopath/src/github.com/hyperledger/fabric/.build/bin/cryptogen", datetime.utcnow(), datetime.utcnow(), None),
            
            # Limkokwing - Verifier
            ("NODE_LIMKOKWING_001", 2, "peer", "fabric", "https://peer0.limkokwing.example.com", 9051,
             True, "/etc/hyperledger/fabric/tls/server.crt", "/etc/hyperledger/fabric/tls/server.key", "/etc/hyperledger/fabric/tls/ca.crt",
             "LimkokwingOrgMSP", "peer0.limkokwing.example.com", "orderer.example.com",
             None, None, "{}", "certificate_chaincode", "1.0.0", "/opt/gopath/src/github.com/chaincode/certificate",
             False, False, "lgcse-channel", "inactive", None, None, 0, 0, "{}", None, "/opt/gopath/src/github.com/hyperledger/fabric/.build/bin/configtxlator",
             "/opt/gopath/src/github.com/hyperledger/fabric/.build/bin/cryptogen", datetime.utcnow(), datetime.utcnow(), None),
            
            # Botho - Verifier
            ("NODE_BOTHO_001", 3, "peer", "fabric", "https://peer0.botho.example.com", 11051,
             True, "/etc/hyperledger/fabric/tls/server.crt", "/etc/hyperledger/fabric/tls/server.key", "/etc/hyperledger/fabric/tls/ca.crt",
             "BothoOrgMSP", "peer0.botho.example.com", "orderer.example.com",
             None, None, "{}", "certificate_chaincode", "1.0.0", "/opt/gopath/src/github.com/chaincode/certificate",
             False, False, "lgcse-channel", "inactive", None, None, 0, 0, "{}", None, "/opt/gopath/src/github.com/hyperledger/fabric/.build/bin/configtxlator",
             "/opt/gopath/src/github.com/hyperledger/fabric/.build/bin/cryptogen", datetime.utcnow(), datetime.utcnow(), None),
            
            # NUL - Verifier
            ("NODE_NUL_001", 4, "peer", "fabric", "https://peer0.nul.example.com", 12051,
             True, "/etc/hyperledger/fabric/tls/server.crt", "/etc/hyperledger/fabric/tls/server.key", "/etc/hyperledger/fabric/tls/ca.crt",
             "NulOrgMSP", "peer0.nul.example.com", "orderer.example.com",
             None, None, "{}", "certificate_chaincode", "1.0.0", "/opt/gopath/src/github.com/chaincode/certificate",
             False, False, "lgcse-channel", "inactive", None, None, 0, 0, "{}", None, "/opt/gopath/src/github.com/hyperledger/fabric/.build/bin/configtxlator",
             "/opt/gopath/src/github.com/hyperledger/fabric/.build/bin/cryptogen", datetime.utcnow(), datetime.utcnow(), None),
            
            # Orderer
            ("NODE_ORDERER_001", 5, "orderer", "fabric", "https://orderer.example.com", 7050,
             True, "/etc/hyperledger/fabric/tls/server.crt", "/etc/hyperledger/fabric/tls/server.key", "/etc/hyperledger/fabric/tls/ca.crt",
             "OrdererMSP", None, "orderer.example.com",
             None, None, "{}", "certificate_chaincode", "1.0.0", "/opt/gopath/src/github.com/chaincode/certificate",
             False, False, "lgcse-channel", "inactive", None, None, 0, 0, "{}", None, "/opt/gopath/src/github.com/hyperledger/fabric/.build/bin/configtxlator",
             "/opt/gopath/src/github.com/hyperledger/fabric/.build/bin/cryptogen", datetime.utcnow(), datetime.utcnow(), None)
        ]
        
        for node in nodes:
            cursor.execute("""
                INSERT INTO blockchain_nodes (
                    node_id, institution_id, node_type, network_type, url, port, tls_enabled,
                    tls_cert_path, tls_key_path, ca_cert_path, msp_id, peer_id, orderer_id,
                    node_public_key, node_private_key, node_certificates, chaincode_name,
                    chaincode_version, chaincode_path, chaincode_installed, chaincode_instantiated,
                    channel_name, status, last_heartbeat, last_sync_at, block_height,
                    network_height, node_config, genesis_block, configtxlator_path,
                    cryptogen_path, created_at, updated_at, installed_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, node)
        
        conn.commit()
        print("✓ Updated blockchain nodes with correct names")
        
        # Update institution mapping
        cursor.execute("UPDATE institutions SET code = 'ECOL' WHERE code = 'MOE'")
        cursor.execute("UPDATE institutions SET code = 'LIMKOKWING' WHERE code = 'LU'")
        cursor.execute("UPDATE institutions SET code = 'BOTHO' WHERE code = 'NUL'")
        cursor.execute("INSERT INTO institutions (code, name, role, created_at, updated_at) VALUES ('NUL', 'National University of Lesotho', 'VERIFIER', %s, %s) ON CONFLICT (code) DO NOTHING", 
                     (datetime.utcnow(), datetime.utcnow()))
        
        conn.commit()
        print("✓ Updated institution codes")
        
        # Print node summary
        cursor.execute("""
            SELECT bn.node_id, i.code, i.name, i.role, bn.node_type, bn.status 
            FROM blockchain_nodes bn 
            LEFT JOIN institutions i ON bn.institution_id = i.id 
            ORDER BY bn.node_type, i.code
        """)
        
        nodes = cursor.fetchall()
        print("\n📋 Blockchain Nodes Summary:")
        print("Node ID               | Institution | Role        | Type   | Status")
        print("-" * 80)
        for node in nodes:
            print(f"{node[0]:<20} | {node[1]:<11} | {node[3]:<11} | {node[4]:<6} | {node[5]}")
        
        print(f"\nTotal nodes: {len(nodes)}")
        print("✓ ECOL configured as main issuer node")
        print("✓ Limkokwing, Botho, NUL configured as verifier nodes")
        print("✓ Orderer node ready for network coordination")
        
    except Exception as e:
        print(f"❌ Error updating nodes: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    update_blockchain_nodes()
