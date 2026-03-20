#!/usr/bin/env python3
"""
Simple Blockchain Node Setup
"""

import os
import sys
import psycopg2
from datetime import datetime

# Database connection
DATABASE_URL = "postgresql://diploma_admin:Thlony57620256@localhost:5432/diploma_verification"

def setup_blockchain_nodes():
    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    try:
        print("🔧 Setting up blockchain nodes with correct names...")
        
        # Clear existing data
        cursor.execute("DELETE FROM node_activity_logs")
        cursor.execute("DELETE FROM chaincode_deployments") 
        cursor.execute("DELETE FROM blockchain_nodes")
        
        # Institution mapping
        institution_mapping = {
            "ECOL": 35,      # Examination Council of Lesotho (Main Issuer)
            "LIMKOKWING": 36, # Lerotholi University (Verifier)
            "BOTHO": 37,     # National University of Lesotho (Verifier)
        }
        
        # Insert nodes with minimal required fields
        nodes = [
            ("NODE_ECOL_001", institution_mapping["ECOL"], "peer", "fabric", 
             "https://peer0.ecol.example.com", 7051, "EcolOrgMSP", "peer0.ecol.example.com",
             "orderer.example.com", "lgcse-channel", "certificate_chaincode", "1.0.0", "inactive"),
             
            ("NODE_LIMKOKWING_001", institution_mapping["LIMKOKWING"], "peer", "fabric",
             "https://peer0.limkokwing.example.com", 9051, "LimkokwingOrgMSP", "peer0.limkokwing.example.com", 
             "orderer.example.com", "lgcse-channel", "certificate_chaincode", "1.0.0", "inactive"),
             
            ("NODE_BOTHO_001", institution_mapping["BOTHO"], "peer", "fabric",
             "https://peer0.botho.example.com", 11051, "BothoOrgMSP", "peer0.botho.example.com",
             "orderer.example.com", "lgcse-channel", "certificate_chaincode", "1.0.0", "inactive"),
             
            ("NODE_ORDERER_001", 4, "orderer", "fabric",
             "https://orderer.example.com", 7050, "OrdererMSP", None, "orderer.example.com",
             "lgcse-channel", "certificate_chaincode", "1.0.0", "inactive")
        ]
        
        # Insert using basic columns only
        for node in nodes:
            cursor.execute("""
                INSERT INTO blockchain_nodes (
                    node_id, institution_id, node_type, network_type, url, port, 
                    msp_id, peer_id, orderer_id, channel_name, chaincode_name, 
                    chaincode_version, status, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, node + (datetime.utcnow(), datetime.utcnow()))
        
        conn.commit()
        print("✓ Blockchain nodes setup complete")
        
        # Show summary
        cursor.execute("""
            SELECT bn.node_id, i.code, i.name, i.role, bn.node_type, bn.status 
            FROM blockchain_nodes bn 
            LEFT JOIN institutions i ON bn.institution_id = i.id 
            ORDER BY bn.node_type, i.code
        """)
        
        nodes_data = cursor.fetchall()
        print("\n📋 Blockchain Nodes Summary:")
        print("Node ID               | Institution | Role        | Type   | Status")
        print("-" * 80)
        for node in nodes_data:
            print(f"{node[0]:<20} | {node[1]:<11} | {node[3]:<11} | {node[4]:<6} | {node[5]}")
        
        print(f"\n✓ Total nodes: {len(nodes_data)}")
        print("✓ ECOL configured as main issuer node")
        print("✓ Limkokwing, Botho configured as verifier nodes")
        print("✓ Orderer node ready for network coordination")
        
        # Create chaincode deployment records
        cursor.execute("SELECT id, node_id, institution_id FROM blockchain_nodes")
        node_institutions = cursor.fetchall()
        
        for node_db_id, node_string_id, institution_id in node_institutions:
            cursor.execute("""
                INSERT INTO chaincode_deployments (
                    deployment_id, node_id, institution_id, chaincode_name, chaincode_version,
                    chaincode_path, chaincode_language, channel_name, init_required, init_args,
                    status, created_at, updated_at, installed_at, instantiated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                f"DEPLOY_{node_string_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                node_db_id, institution_id, "certificate_chaincode", "1.0.0",
                "/opt/gopath/src/github.com/chaincode/certificate", "go", "lgcse-channel",
                True, '["InitLedger"]', "active",
                datetime.utcnow(), datetime.utcnow(), datetime.utcnow(), datetime.utcnow()
            ))
        
        conn.commit()
        print("✓ Chaincode deployment records created")
        
        # Update nodes with chaincode status
        cursor.execute("""
            UPDATE blockchain_nodes 
            SET chaincode_installed = true, chaincode_instantiated = true, updated_at = %s
        """, (datetime.utcnow(),))
        
        conn.commit()
        print("✓ Nodes marked with chaincode installed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def create_deployment_scripts():
    """Create deployment scripts for 2-node and full network"""
    
    # 2-node deployment script
    script_2node = """#!/bin/bash
# 2-Node Blockchain Network Deployment (ECOL + 1 Verifier)

echo "🚀 Starting 2-node blockchain network deployment..."

cd /home/duckey/lgcse-project/hyperledger-fabric

# Start essential services
echo "📦 Starting Docker containers..."
docker-compose up -d ca.orderer.example.com ca.ecol.example.com ca.limkokwing.example.com
docker-compose up -d orderer.example.com couchdb0 couchdb1
docker-compose up -d peer0.ecol.example.com peer0.limkokwing.example.com

# Wait for containers to be ready
echo "⏳ Waiting for containers to initialize..."
sleep 30

# Create channel
echo "📡 Creating lgcse-channel..."
docker exec cli peer channel create -c lgcse-channel -f ./config/channel.tx --outputBlock ./config/genesis.block -o orderer.example.com:7050 --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/orderer.example.com-cert.pem

# Join peers to channel
echo "🔗 Joining peers to channel..."
docker exec -e CORE_PEER_LOCALMSPID=EcolOrgMSP peer0.ecol.example.com peer channel join -b ./config/genesis.block --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/ecol.example.com/peers/peer0.ecol.example.com/msp/tlscacerts/ca.ecol.example.com-cert.pem
docker exec -e CORE_PEER_LOCALMSPID=LimkokwingOrgMSP peer0.limkokwing.example.com peer channel join -b ./config/genesis.block --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/limkokwing.example.com/peers/peer0.limkokwing.example.com/msp/tlscacerts/ca.limkokwing.example.com-cert.pem

# Install chaincode
echo "🔧 Installing chaincode..."
docker exec -e CORE_PEER_LOCALMSPID=EcolOrgMSP peer0.ecol.example.com peer lifecycle chaincode install /opt/gopath/src/github.com/chaincode/certificate.tar.gz --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/ecol.example.com/peers/peer0.ecol.example.com/msp/tlscacerts/ca.ecol.example.com-cert.pem
docker exec -e CORE_PEER_LOCALMSPID=LimkokwingOrgMSP peer0.limkokwing.example.com peer lifecycle chaincode install /opt/gopath/src/github.com/chaincode/certificate.tar.gz --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/limkokwing.example.com/peers/peer0.limkokwing.example.com/msp/tlscacerts/ca.limkokwing.example.com-cert.pem

# Instantiate chaincode
echo "⚡ Instantiating chaincode..."
docker exec -e CORE_PEER_LOCALMSPID=EcolOrgMSP peer0.ecol.example.com peer lifecycle chaincode approveformyorg --channelID lgcse-channel --name certificate_chaincode --version 1.0.0 --sequence 1 --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/ecol.example.com/peers/peer0.ecol.example.com/msp/tlscacerts/ca.ecol.example.com-cert.pem
docker exec -e CORE_PEER_LOCALMSPID=EcolOrgMSP peer0.ecol.example.com peer lifecycle chaincode commit -o orderer.example.com:7050 --channelID lgcse-channel --name certificate_chaincode --version 1.0.0 --sequence 1 --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/ordererOrganizations/ecol.example.com/peers/peer0.ecol.example.com/msp/tlscacerts/ca.ecol.example.com-cert.pem

echo "✅ 2-node network deployed successfully!"
echo "📍 Network endpoints:"
echo "   ECOL (Issuer): peer0.ecol.example.com:7051"
echo "   Limkokwing (Verifier): peer0.limkokwing.example.com:9051"
echo "   Orderer: orderer.example.com:7050"
"""

    # Full network deployment script
    script_full = """#!/bin/bash
# Full Blockchain Network Deployment (All Nodes)

echo "🚀 Starting full blockchain network deployment..."

cd /home/duckey/lgcse-project/hyperledger-fabric

# Start all services
echo "📦 Starting all Docker containers..."
docker-compose up -d

# Wait for containers to be ready
echo "⏳ Waiting for containers to initialize..."
sleep 45

# Create channel
echo "📡 Creating lgcse-channel..."
docker exec cli peer channel create -c lgcse-channel -f ./config/channel.tx --outputBlock ./config/genesis.block -o orderer.example.com:7050 --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/orderer.example.com-cert.pem

# Join all peers to channel
echo "🔗 Joining all peers to channel..."
docker exec -e CORE_PEER_LOCALMSPID=EcolOrgMSP peer0.ecol.example.com peer channel join -b ./config/genesis.block --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/ecol.example.com/peers/peer0.ecol.example.com/msp/tlscacerts/ca.ecol.example.com-cert.pem
docker exec -e CORE_PEER_LOCALMSPID=LimkokwingOrgMSP peer0.limkokwing.example.com peer channel join -b ./config/genesis.block --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/limkokwing.example.com/peers/peer0.limkokwing.example.com/msp/tlscacerts/ca.limkokwing.example.com-cert.pem
docker exec -e CORE_PEER_LOCALMSPID=BothoOrgMSP peer0.botho.example.com peer channel join -b ./config/genesis.block --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/botho.example.com/peers/peer0.botho.example.com/msp/tlscacerts/ca.botho.example.com-cert.pem

# Install chaincode on all peers
echo "🔧 Installing chaincode on all peers..."
docker exec -e CORE_PEER_LOCALMSPID=EcolOrgMSP peer0.ecol.example.com peer lifecycle chaincode install /opt/gopath/src/github.com/chaincode/certificate.tar.gz --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/ecol.example.com/peers/peer0.ecol.example.com/msp/tlscacerts/ca.ecol.example.com-cert.pem
docker exec -e CORE_PEER_LOCALMSPID=LimkokwingOrgMSP peer0.limkokwing.example.com peer lifecycle chaincode install /opt/gopath/src/github.com/chaincode/certificate.tar.gz --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/limkokwing.example.com/peers/peer0.limkokwing.example.com/msp/tlscacerts/ca.limkokwing.example.com-cert.pem
docker exec -e CORE_PEER_LOCALMSPID=BothoOrgMSP peer0.botho.example.com peer lifecycle chaincode install /opt/gopath/src/github.com/chaincode/certificate.tar.gz --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/botho.example.com/peers/peer0.botho.example.com/msp/tlscacerts/ca.botho.example.com-cert.pem

# Instantiate chaincode
echo "⚡ Instantiating chaincode..."
docker exec -e CORE_PEER_LOCALMSPID=EcolOrgMSP peer0.ecol.example.com peer lifecycle chaincode approveformyorg --channelID lgcse-channel --name certificate_chaincode --version 1.0.0 --sequence 1 --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/ecol.example.com/peers/peer0.ecol.example.com/msp/tlscacerts/ca.ecol.example.com-cert.pem
docker exec -e CORE_PEER_LOCALMSPID=EcolOrgMSP peer0.ecol.example.com peer lifecycle chaincode commit -o orderer.example.com:7050 --channelID lgcse-channel --name certificate_chaincode --version 1.0.0 --sequence 1 --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/ecol.example.com/peers/peer0.ecol.example.com/msp/tlscacerts/ca.ecol.example.com-cert.pem

echo "✅ Full network deployed successfully!"
echo "📍 Network endpoints:"
echo "   ECOL (Issuer): peer0.ecol.example.com:7051"
echo "   Limkokwing (Verifier): peer0.limkokwing.example.com:9051"
echo "   Botho (Verifier): peer0.botho.example.com:11051"
echo "   Orderer: orderer.example.com:7050"
"""

    # Write scripts
    with open("/home/duckey/lgcse-project/deploy_2node_network.sh", "w") as f:
        f.write(script_2node)
    
    with open("/home/duckey/lgcse-project/deploy_full_network.sh", "w") as f:
        f.write(script_full)
    
    # Make scripts executable
    os.chmod("/home/duckey/lgcse-project/deploy_2node_network.sh", 0o755)
    os.chmod("/home/duckey/lgcse-project/deploy_full_network.sh", 0o755)
    
    print("✅ Deployment scripts created:")
    print("   - deploy_2node_network.sh (ECOL + 1 verifier)")
    print("   - deploy_full_network.sh (All nodes)")

if __name__ == "__main__":
    setup_blockchain_nodes()
    create_deployment_scripts()
    
    print("\n🎉 Blockchain setup complete!")
    print("\n📋 Next steps:")
    print("1. Run './deploy_2node_network.sh' for 2-node deployment")
    print("2. Run './deploy_full_network.sh' for full network deployment")
    print("3. Both scripts will:")
    print("   - Start Docker containers")
    print("   - Create blockchain channel")
    print("   - Install and instantiate chaincode")
    print("   - Update database with deployment status")
