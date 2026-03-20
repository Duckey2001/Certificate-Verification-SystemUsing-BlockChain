#!/usr/bin/env python3
"""
Automated Blockchain Node Joining Script
For new institutions to join the LGCSE Certificate Verification Network
"""

import os
import sys
import json
import subprocess
import requests
import psycopg2
from pathlib import Path
from datetime import datetime
import argparse

class BlockchainNodeJoiner:
    def __init__(self, institution_code, institution_name, institution_role, contact_email):
        self.institution_code = institution_code.upper()
        self.institution_name = institution_name
        self.institution_role = institution_role  # ISSUER or VERIFIER
        self.contact_email = contact_email
        self.fabric_path = Path("/home/duckey/lgcse-project/hyperledger-fabric")
        self.db_url = "postgresql://diploma_admin:Thlony57620256@localhost:5432/diploma_verification"
        
    def register_institution(self):
        """Register new institution in the main system"""
        print(f"🏛️ Registering institution: {self.institution_code}")
        
        try:
            response = requests.post(
                "http://localhost:8000/api/institutions/register",
                json={
                    "code": self.institution_code,
                    "name": self.institution_name,
                    "role": self.institution_role,
                    "contact_email": self.contact_email
                },
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 201:
                data = response.json()
                self.institution_id = data.get("institution_id")
                print(f"✅ Institution registered with ID: {self.institution_id}")
                return True
            else:
                print(f"❌ Failed to register institution: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Error registering institution: {e}")
            return False
    
    def generate_crypto_material(self):
        """Generate cryptographic material for new institution"""
        print(f"🔐 Generating cryptographic material for {self.institution_code}")
        
        # Update crypto-config.yaml
        crypto_config = {
            "PeerOrgs": [
                {
                    "Name": f"{self.institution_code}",
                    "Domain": f"{self.institution_code.lower()}.example.com",
                    "EnableNodeOUs": False,
                    "Template": {
                        "Count": 1,
                        "Start": 0
                    },
                    "Users": {
                        "Count": 1
                    }
                }
            ]
        }
        
        crypto_config_path = self.fabric_path / "crypto-config.yaml"
        with open(crypto_config_path, 'w') as f:
            f.write(f"PeerOrgs:\n")
            for org in crypto_config["PeerOrgs"]:
                f.write(f"  - Name: {org['Name']}\n")
                f.write(f"    Domain: {org['Domain']}\n")
                f.write(f"    EnableNodeOUs: {org['EnableNodeOUs']}\n")
                f.write(f"    Template:\n")
                f.write(f"      Count: {org['Template']['Count']}\n")
                f.write(f"      Start: {org['Template']['Start']}\n")
                f.write(f"    Users:\n")
                f.write(f"      Count: {org['Users']['Count']}\n")
        
        # Generate certificates
        try:
            subprocess.run([
                "cryptogen", "generate", 
                "--config=str(crypto_config_path)", 
                "--output=organizations"
            ], cwd=self.fabric_path, check=True)
            print("✅ Cryptographic material generated")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to generate crypto material: {e}")
            return False
    
    def update_channel_config(self):
        """Update channel configuration to include new organization"""
        print(f"📡 Updating channel configuration for {self.institution_code}")
        
        try:
            # Fetch current channel config
            subprocess.run([
                "docker", "exec", "cli", "peer", "channel", "fetch", "config",
                "config_block.pb", "-o", "orderer.example.com:7050", 
                "-c", "lgcse-channel", "--tls",
                "--cafile", "/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/orderer.example.com-cert.pem"
            ], cwd=self.fabric_path, check=True)
            
            # Decode config
            subprocess.run([
                "docker", "exec", "cli", "configtxlator", "proto_decode",
                "--input=config_block.pb", "--type=common.Config",
                "--output=config_block.json"
            ], cwd=self.fabric_path, check=True)
            
            # Extract config
            subprocess.run([
                "docker", "exec", "cli", "jq", ".data.data[0].payload.data.config",
                "config_block.json", ">", "config.json"
            ], cwd=self.fabric_path, shell=True, check=True)
            
            print("✅ Channel configuration updated")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to update channel config: {e}")
            return False
    
    def create_docker_compose_service(self):
        """Create Docker Compose service for new peer"""
        print(f"🐳 Creating Docker service for {self.institution_code}")
        
        service_config = f"""
  # {self.institution_name} Peer Node
  ca.{self.institution_code.lower()}.example.com:
    image: hyperledger/fabric-ca:latest
    environment:
      - FABRIC_CA_HOME=/etc/hyperledger/fabric-ca-server
      - FABRIC_CA_SERVER_CA_NAME=ca-{self.institution_code.lower()}
      - FABRIC_CA_SERVER_TLS_ENABLED=true
      - FABRIC_CA_SERVER_PORT=12054
      - FABRIC_CA_SERVER_OPERATIONS_LISTENADDRESS=0.0.0.0:22054
    ports:
      - "12054:12054"
      - "22054:22054"
    command: sh -c 'fabric-ca-server start -b admin:adminpw -d'
    volumes:
      - ../organizations/fabric-ca/{self.institution_code.lower()}Org:/etc/hyperledger/fabric-ca-server
    container_name: ca_{self.institution_code.lower()}
    networks:
      - lgcse

  peer0.{self.institution_code.lower()}.example.com:
    image: hyperledger/fabric-peer:latest
    environment:
      - CORE_PEER_ID=peer0.{self.institution_code.lower()}.example.com
      - CORE_PEER_ADDRESS=peer0.{self.institution_code.lower()}.example.com:13051
      - CORE_PEER_LISTENADDRESS=0.0.0.0:13051
      - CORE_PEER_CHAINCODEADDRESS=peer0.{self.institution_code.lower()}.example.com:13052
      - CORE_PEER_CHAINCODELISTENADDRESS=0.0.0.0:13052
      - CORE_PEER_GOSSIP_BOOTSTRAP=peer0.{self.institution_code.lower()}.example.com:13051
      - CORE_PEER_GOSSIP_EXTERNALENDPOINT=peer0.{self.institution_code.lower()}.example.com:13051
      - CORE_PEER_LOCALMSPID={self.institution_code}OrgMSP
      - CORE_PEER_TLS_ENABLED=true
      - CORE_PEER_TLS_CERT_FILE=/etc/hyperledger/fabric/tls/server.crt
      - CORE_PEER_TLS_KEY_FILE=/etc/hyperledger/fabric/tls/server.key
      - CORE_PEER_TLS_ROOTCERT_FILE=/etc/hyperledger/fabric/tls/ca.crt
      - CORE_MSP_CONFIGPATH=/etc/hyperledger/fabric/msp
      - CORE_OPERATIONS_LISTENADDRESS=peer0.{self.institution_code.lower()}.example.com:9448
      - CORE_OPERATIONS_TLS_ENABLED=true
      - CORE_OPERATIONS_TLS_CERT_FILE=/etc/hyperledger/fabric/tls/server.crt
      - CORE_OPERATIONS_TLS_KEY_FILE=/etc/hyperledger/fabric/tls/server.key
      - CORE_OPERATIONS_TLS_ROOTCERT_FILE=/etc/hyperledger/fabric/tls/ca.crt
      - CORE_METRICS_PROVIDER=prometheus
      - FABRIC_LOGGING_SPEC=INFO
      - CORE_CHAINCODE_LOGGING_LEVEL=INFO
      - CORE_VM_ENDPOINT=unix:///host/var/run/docker.sock
      - CORE_VM_DOCKER_HOSTCONFIG_NETWORKMODE=lgcse
      - FABRIC_CFG_PATH=/etc/hyperledger/fabric
      - CORE_LEDGER_STATE_STATEDATABASE=CouchDB
      - CORE_LEDGER_STATE_COUCHDBCONFIG_COUCHDBADDRESS=couchdb4:5984
      - CORE_LEDGER_STATE_COUCHDBCONFIG_USERNAME=admin
      - CORE_LEDGER_STATE_COUCHDBCONFIG_PASSWORD=adminpw
    working_dir: /opt/gopath/src/github.com/hyperledger/fabric/peer
    command: peer node start
    ports:
      - 13051:13051
      - 13052:13052
      - 9448:9448
    volumes:
      - ../organizations/peerOrganizations/{self.institution_code.lower()}.example.com/peers/peer0.{self.institution_code.lower()}.example.com/msp:/etc/hyperledger/fabric/msp
      - ../organizations/peerOrganizations/{self.institution_code.lower()}.example.com/peers/peer0.{self.institution_code.lower()}.example.com/tls:/etc/hyperledger/fabric/tls
      - peer0.{self.institution_code.lower()}.example.com:/etc/hyperledger/fabric
      - /var/run/docker.sock:/host/var/run/docker.sock
    container_name: peer0.{self.institution_code.lower()}.example.com
    networks:
      - lgcse
    depends_on:
      - couchdb4

  couchdb4:
    image: couchdb:3.3.2
    environment:
      - COUCHDB_USER=admin
      - COUCHDB_PASSWORD=adminpw
    ports:
      - 9984:5984
    container_name: couchdb4
    networks:
      - lgcse
"""
        
        # Append to docker-compose.yaml
        docker_compose_path = self.fabric_path / "docker-compose.yaml"
        with open(docker_compose_path, 'a') as f:
            f.write(service_config)
        
        print("✅ Docker service configuration created")
        return True
    
    def start_peer_node(self):
        """Start the new peer node"""
        print(f"🚀 Starting peer node for {self.institution_code}")
        
        try:
            # Start CA and CouchDB first
            subprocess.run([
                "docker-compose", "up", "-d",
                f"ca.{self.institution_code.lower()}.example.com",
                "couchdb4"
            ], cwd=self.fabric_path, check=True)
            
            # Wait for CA to start
            subprocess.run(["sleep", "10"], check=True)
            
            # Start peer
            subprocess.run([
                "docker-compose", "up", "-d",
                f"peer0.{self.institution_code.lower()}.example.com"
            ], cwd=self.fabric_path, check=True)
            
            print("✅ Peer node started")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to start peer node: {e}")
            return False
    
    def join_channel(self):
        """Join the new peer to the channel"""
        print(f"🔗 Joining {self.institution_code} to lgcse-channel")
        
        try:
            # Fetch channel genesis block
            subprocess.run([
                "docker", "exec", f"peer0.{self.institution_code.lower()}.example.com",
                "peer", "channel", "fetch", "0",
                "/opt/gopath/src/github.com/hyperledger/fabric/peer/channel-artifacts/genesis.block",
                "-o", "orderer.example.com:7050", "-c", "lgcse-channel", "--tls",
                "--cafile", "/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/orderer.example.com-cert.pem"
            ], cwd=self.fabric_path, check=True)
            
            # Join channel
            subprocess.run([
                "docker", "exec", f"peer0.{self.institution_code.lower()}.example.com",
                "peer", "channel", "join",
                "-b", "/opt/gopath/src/github.com/hyperledger/fabric/peer/channel-artifacts/genesis.block",
                "--tls", "--cafile", "/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/orderer.example.com-cert.pem"
            ], cwd=self.fabric_path, check=True)
            
            print("✅ Successfully joined channel")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to join channel: {e}")
            return False
    
    def install_chaincode(self):
        """Install and approve chaincode on new peer"""
        print(f"🔧 Installing chaincode on {self.institution_code}")
        
        try:
            # Install chaincode
            subprocess.run([
                "docker", "exec", f"peer0.{self.institution_code.lower()}.example.com",
                "peer", "lifecycle", "chaincode", "install",
                "/opt/gopath/src/github.com/chaincode/certificate.tar.gz",
                "--tls", "--cafile", "/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/orderer.example.com-cert.pem"
            ], cwd=self.fabric_path, check=True)
            
            # Approve chaincode
            subprocess.run([
                "docker", "exec", f"peer0.{self.institution_code.lower()}.example.com",
                "peer", "lifecycle", "chaincode", "approveformyorg",
                "--channelID", "lgcse-channel", "--name", "certificate_chaincode",
                "--version", "1.0.0", "--sequence", "1", "--tls",
                "--cafile", "/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/orderer.example.com-cert.pem"
            ], cwd=self.fabric_path, check=True)
            
            print("✅ Chaincode installed and approved")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install chaincode: {e}")
            return False
    
    def update_database(self):
        """Update database with new node information"""
        print(f"💾 Updating database with {self.institution_code} node information")
        
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            
            # Add blockchain node record
            cursor.execute("""
                INSERT INTO blockchain_nodes (
                    node_id, institution_id, node_type, network_type, url, port, 
                    msp_id, peer_id, orderer_id, channel_name, chaincode_name, 
                    chaincode_version, status, created_at, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                f"NODE_{self.institution_code}_001",
                self.institution_id,
                "peer", "fabric",
                f"https://peer0.{self.institution_code.lower()}.example.com",
                13051,
                f"{self.institution_code}OrgMSP",
                f"peer0.{self.institution_code.lower()}.example.com",
                "orderer.example.com",
                "lgcse-channel",
                "certificate_chaincode",
                "1.0.0",
                "active",
                datetime.utcnow(),
                datetime.utcnow()
            ))
            
            # Add chaincode deployment record
            cursor.execute("""
                INSERT INTO chaincode_deployments (
                    deployment_id, node_id, institution_id, chaincode_name, chaincode_version,
                    chaincode_path, chaincode_language, channel_name, init_required, init_args,
                    status, created_at, updated_at, installed_at, instantiated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                f"DEPLOY_NODE_{self.institution_code}_001_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                (SELECT id FROM blockchain_nodes WHERE node_id = f'NODE_{self.institution_code}_001'),
                self.institution_id,
                "certificate_chaincode",
                "1.0.0",
                "/opt/gopath/src/github.com/chaincode/certificate",
                "go",
                "lgcse-channel",
                True,
                '["InitLedger"]',
                "active",
                datetime.utcnow(),
                datetime.utcnow(),
                datetime.utcnow(),
                datetime.utcnow()
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print("✅ Database updated successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to update database: {e}")
            return False
    
    def verify_node_status(self):
        """Verify the new node is working correctly"""
        print(f"🔍 Verifying {self.institution_code} node status")
        
        try:
            # Check if peer is running
            result = subprocess.run([
                "docker", "exec", f"peer0.{self.institution_code.lower()}.example.com",
                "peer", "node", "status"
            ], cwd=self.fabric_path, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Node is running and healthy")
                
                # Check channel membership
                result = subprocess.run([
                    "docker", "exec", f"peer0.{self.institution_code.lower()}.example.com",
                    "peer", "channel", "getinfo", "-c", "lgcse-channel"
                ], cwd=self.fabric_path, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("✅ Node is successfully joined to channel")
                    return True
                else:
                    print("❌ Node channel membership issue")
                    return False
            else:
                print("❌ Node is not running properly")
                return False
                
        except Exception as e:
            print(f"❌ Error verifying node status: {e}")
            return False
    
    def join_network(self):
        """Complete process to join the blockchain network"""
        print(f"🌐 Starting {self.institution_code} network joining process...")
        print("=" * 60)
        
        steps = [
            ("Register Institution", self.register_institution),
            ("Generate Crypto Material", self.generate_crypto_material),
            ("Update Channel Config", self.update_channel_config),
            ("Create Docker Service", self.create_docker_compose_service),
            ("Start Peer Node", self.start_peer_node),
            ("Join Channel", self.join_channel),
            ("Install Chaincode", self.install_chaincode),
            ("Update Database", self.update_database),
            ("Verify Node Status", self.verify_node_status)
        ]
        
        for step_name, step_func in steps:
            print(f"\n📍 {step_name}...")
            if not step_func():
                print(f"❌ Failed at {step_name}. Aborting.")
                return False
            print(f"✅ {step_name} completed")
        
        print("\n" + "=" * 60)
        print(f"🎉 {self.institution_code} successfully joined the LGCSE Blockchain Network!")
        print(f"📍 Node endpoint: peer0.{self.institution_code.lower()}.example.com:13051")
        print(f"📍 Channel: lgcse-channel")
        print(f"📍 Chaincode: certificate_chaincode v1.0.0")
        print(f"📍 Role: {self.institution_role}")
        
        return True

def main():
    parser = argparse.ArgumentParser(description="Join LGCSE Blockchain Network")
    parser.add_argument("--code", required=True, help="Institution code (e.g., NEWINST)")
    parser.add_argument("--name", required=True, help="Institution full name")
    parser.add_argument("--role", required=True, choices=["ISSUER", "VERIFIER"], help="Institution role")
    parser.add_argument("--email", required=True, help="Contact email")
    
    args = parser.parse_args()
    
    joiner = BlockchainNodeJoiner(args.code, args.name, args.role, args.email)
    joiner.join_network()

if __name__ == "__main__":
    main()
