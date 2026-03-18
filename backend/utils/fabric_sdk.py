"""
Hyperledger Fabric SDK Integration for LGCSE Certificate Verification System

This module provides comprehensive integration with Hyperledger Fabric blockchain network,
including certificate issuance, verification, and management operations.
"""

import os
import json
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path

from hfc.fabric import Client
from hfc.util.keyval_store import FileKeyValueStore
from hfc.util.crypto import crypto
from hfc.protos.common import common_pb2
from hfc.protos.peer import proposal_pb2, peer_pb2
from google.protobuf import timestamp_pb2

from sqlalchemy.orm import Session
from database import SessionLocal
from models import (
    Institution, BlockchainNode, ChaincodeDeployment, 
    Certificate, VerificationRequest, NodeActivityLog
)

logger = logging.getLogger(__name__)

class FabricSDKManager:
    """
    Hyperledger Fabric SDK Manager for LGCSE Certificate Verification
    
    Provides comprehensive blockchain operations including:
    - Certificate issuance and verification
    - Channel and chaincode management
    - Institution node management
    - Private data collections
    - Network monitoring
    """
    
    def __init__(self, network_config: str = None):
        """
        Initialize Fabric SDK Manager
        
        Args:
            network_config: Path to network configuration file
        """
        self.network_config = network_config or os.path.join(
            os.path.dirname(__file__), 
            "../../hyperledger-fabric/config/connection-profile.json"
        )
        self.client = None
        self.channel = None
        self.chaincode = "certificate-chaincode"
        self.channel_name = "lgcse-channel"
        self.orgs = ["EcolOrgMSP", "LimkokwingOrgMSP", "BothoOrgMSP", "NulOrgMSP"]
        self.peers = {
            "EcolOrgMSP": "peer0.ecol.example.com",
            "LimkokwingOrgMSP": "peer0.limkokwing.example.com", 
            "BothoOrgMSP": "peer0.botho.example.com",
            "NulOrgMSP": "peer0.nul.example.com"
        }
        
        # Initialize SDK
        self._initialize_sdk()
    
    def _initialize_sdk(self):
        """Initialize Fabric SDK client"""
        try:
            # Create client
            self.client = Client(net_id="lgcse-network")
            
            # Load network configuration
            if os.path.exists(self.network_config):
                self.client.load_from_file(self.network_config)
            else:
                # Create default configuration
                self._create_default_config()
            
            # Create user key value store
            self.client.new_user(
                user_id="admin",
                org_name="EcolOrgMSP",
                store_path="/tmp/fabric-client-kvs"
            )
            
            logger.info("Fabric SDK initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Fabric SDK: {e}")
            raise
    
    def _create_default_config(self):
        """Create default network configuration"""
        config = {
            "name": "lgcse-network",
            "version": "1.0",
            "client": {
                "organization": "EcolOrgMSP",
                "connection": {
                    "timeout": {
                        "peer": {
                            "endorser": "300",
                            "eventHub": "300",
                            "eventReg": "300"
                        },
                        "orderer": "300"
                    }
                }
            },
            "organizations": {
                "EcolOrgMSP": {
                    "mspid": "EcolOrgMSP",
                    "peers": ["peer0.ecol.example.com"],
                    "certificateAuthorities": ["ca.ecol.example.com"]
                },
                "LimkokwingOrgMSP": {
                    "mspid": "LimkokwingOrgMSP", 
                    "peers": ["peer0.limkokwing.example.com"],
                    "certificateAuthorities": ["ca.limkokwing.example.com"]
                },
                "BothoOrgMSP": {
                    "mspid": "BothoOrgMSP",
                    "peers": ["peer0.botho.example.com"],
                    "certificateAuthorities": ["ca.botho.example.com"]
                },
                "NulOrgMSP": {
                    "mspid": "NulOrgMSP",
                    "peers": ["peer0.nul.example.com"],
                    "certificateAuthorities": ["ca.nul.example.com"]
                }
            },
            "orderers": {
                "orderer.example.com": {
                    "url": "grpcs://localhost:7050",
                    "tlsCACerts": {
                        "pem": "-----BEGIN CERTIFICATE-----\n...-----END CERTIFICATE-----"
                    },
                    "grpcOptions": {
                        "ssl-target-name-override": "orderer.example.com"
                    }
                }
            },
            "peers": {
                "peer0.ecol.example.com": {
                    "url": "grpcs://localhost:7051",
                    "tlsCACerts": {
                        "pem": "-----BEGIN CERTIFICATE-----\n...-----END CERTIFICATE-----"
                    },
                    "grpcOptions": {
                        "ssl-target-name-override": "peer0.ecol.example.com"
                    }
                },
                "peer0.limkokwing.example.com": {
                    "url": "grpcs://localhost:9051",
                    "tlsCACerts": {
                        "pem": "-----BEGIN CERTIFICATE-----\n...-----END CERTIFICATE-----"
                    },
                    "grpcOptions": {
                        "ssl-target-name-override": "peer0.limkokwing.example.com"
                    }
                },
                "peer0.botho.example.com": {
                    "url": "grpcs://localhost:11051",
                    "tlsCACerts": {
                        "pem": "-----BEGIN CERTIFICATE-----\n...-----END CERTIFICATE-----"
                    },
                    "grpcOptions": {
                        "ssl-target-name-override": "peer0.botho.example.com"
                    }
                },
                "peer0.nul.example.com": {
                    "url": "grpcs://localhost:12051",
                    "tlsCACerts": {
                        "pem": "-----BEGIN CERTIFICATE-----\n...-----END CERTIFICATE-----"
                    },
                    "grpcOptions": {
                        "ssl-target-name-override": "peer0.nul.example.com"
                    }
                }
            },
            "certificateAuthorities": {
                "ca.ecol.example.com": {
                    "url": "https://localhost:8054",
                    "caName": "ca-ecol",
                    "tlsCACerts": {
                        "pem": "-----BEGIN CERTIFICATE-----\n...-----END CERTIFICATE-----"
                    },
                    "httpOptions": {
                        "verify": False
                    }
                },
                "ca.limkokwing.example.com": {
                    "url": "https://localhost:9054",
                    "caName": "ca-limkokwing",
                    "tlsCACerts": {
                        "pem": "-----BEGIN CERTIFICATE-----\n...-----END CERTIFICATE-----"
                    },
                    "httpOptions": {
                        "verify": False
                    }
                },
                "ca.botho.example.com": {
                    "url": "https://localhost:10054",
                    "caName": "ca-botho",
                    "tlsCACerts": {
                        "pem": "-----BEGIN CERTIFICATE-----\n...-----END CERTIFICATE-----"
                    },
                    "httpOptions": {
                        "verify": False
                    }
                },
                "ca.nul.example.com": {
                    "url": "https://localhost:11054",
                    "caName": "ca-nul",
                    "tlsCACerts": {
                        "pem": "-----BEGIN CERTIFICATE-----\n...-----END CERTIFICATE-----"
                    },
                    "httpOptions": {
                        "verify": False
                    }
                }
            },
            "channels": {
                "lgcse-channel": {
                    "orderers": ["orderer.example.com"],
                    "peers": {
                        "peer0.ecol.example.com": {
                            "endorsingPeer": True,
                            "chaincodeQuery": True,
                            "ledgerQuery": True,
                            "eventSource": True
                        },
                        "peer0.limkokwing.example.com": {
                            "endorsingPeer": True,
                            "chaincodeQuery": True,
                            "ledgerQuery": True,
                            "eventSource": True
                        },
                        "peer0.botho.example.com": {
                            "endorsingPeer": True,
                            "chaincodeQuery": True,
                            "ledgerQuery": True,
                            "eventSource": True
                        },
                        "peer0.nul.example.com": {
                            "endorsingPeer": True,
                            "chaincodeQuery": True,
                            "ledgerQuery": True,
                            "eventSource": True
                        }
                    }
                }
            }
        }
        
        # Save configuration
        os.makedirs(os.path.dirname(self.network_config), exist_ok=True)
        with open(self.network_config, 'w') as f:
            json.dump(config, f, indent=2)
    
    def connect_to_channel(self) -> bool:
        """Connect to the LGCSE channel"""
        try:
            if not self.channel:
                self.channel = self.client.get_channel(self.channel_name)
            
            # Initialize channel
            self.channel.initialize()
            logger.info(f"Connected to channel {self.channel_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to channel: {e}")
            return False
    
    def issue_certificate(self, certificate_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Issue a new certificate on the blockchain
        
        Args:
            certificate_data: Certificate information including:
                - certificateHash: Unique certificate hash
                - studentId: Student ID
                - studentName: Student name
                - studentSurname: Student surname
                - examinationYear: Examination year
                - subjects: List of subjects with grades
                - credits: Total credits
                - issueDate: Issue date
                - issuer: Issuer name
                - institutionCode: Institution code
                - privateData: Encrypted private data (optional)
        
        Returns:
            Dict containing transaction details
        """
        try:
            # Connect to channel
            if not self.connect_to_channel():
                raise Exception("Failed to connect to channel")
            
            # Prepare arguments
            args = [
                certificate_data["certificateHash"],
                certificate_data["studentId"],
                certificate_data["studentName"],
                certificate_data["studentSurname"],
                str(certificate_data["examinationYear"]),
                json.dumps(certificate_data["subjects"]),
                str(certificate_data["credits"]),
                certificate_data["issueDate"],
                certificate_data["issuer"],
                certificate_data["institutionCode"],
                certificate_data.get("privateData", "")
            ]
            
            # Create and submit transaction
            transient_map = {
                "certificate": json.dumps(certificate_data).encode()
            }
            
            # Get endorsing peers (all organizations)
            endorsing_peers = []
            for org in self.orgs:
                peer = self.channel.get_peer(self.peers[org])
                endorsing_peers.append(peer)
            
            # Create proposal
            proposal = self.channel.create_tx_proposal(
                chaincode_id=self.chaincode,
                fcn="IssueCertificate",
                args=args,
                transient_map=transient_map
            )
            
            # Send proposal to endorsing peers
            proposal_responses = self.channel.send_tx_proposal(
                proposal, peers=endorsing_peers
            )
            
            # Check proposal responses
            for response in proposal_responses:
                if response.response.status != 200:
                    raise Exception(f"Proposal failed: {response.response.message}")
            
            # Create transaction
            tx = self.channel.create_tx(proposal_responses)
            
            # Send transaction to orderer
            tx_response = self.channel.send_tx(tx)
            
            if tx_response.status != 200:
                raise Exception(f"Transaction failed: {tx_response.info}")
            
            # Wait for transaction commit
            time.sleep(3)
            
            result = {
                "success": True,
                "transaction_id": tx_response.tx_id,
                "block_number": tx_response.block_number,
                "status": "issued",
                "timestamp": datetime.utcnow().isoformat(),
                "certificate_hash": certificate_data["certificateHash"]
            }
            
            logger.info(f"Certificate {certificate_data['certificateHash']} issued successfully")
            return result
            
        except Exception as e:
            logger.error(f"Failed to issue certificate: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def verify_certificate(self, verification_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify a certificate on the blockchain
        
        Args:
            verification_data: Verification information including:
                - certificateHash: Certificate hash to verify
                - verifierId: Verifier ID
                - verifierName: Verifier name
                - institutionCode: Institution code
                - verificationMethod: Verification method
                - ipAddress: IP address
                - userAgent: User agent
                - verificationData: Additional verification data
        
        Returns:
            Dict containing verification result
        """
        try:
            # Connect to channel
            if not self.connect_to_channel():
                raise Exception("Failed to connect to channel")
            
            # Prepare arguments
            args = [
                verification_data["certificateHash"],
                verification_data["verifierId"],
                verification_data["verifierName"],
                verification_data["institutionCode"],
                verification_data["verificationMethod"],
                verification_data["ipAddress"],
                verification_data["userAgent"],
                verification_data.get("verificationData", "")
            ]
            
            # Create and submit transaction
            transient_map = {
                "verification": json.dumps(verification_data).encode()
            }
            
            # Get endorsing peers
            endorsing_peers = []
            for org in self.orgs:
                peer = self.channel.get_peer(self.peers[org])
                endorsing_peers.append(peer)
            
            # Create proposal
            proposal = self.channel.create_tx_proposal(
                chaincode_id=self.chaincode,
                fcn="VerifyCertificate",
                args=args,
                transient_map=transient_map
            )
            
            # Send proposal to endorsing peers
            proposal_responses = self.channel.send_tx_proposal(
                proposal, peers=endorsing_peers
            )
            
            # Check proposal responses
            for response in proposal_responses:
                if response.response.status != 200:
                    raise Exception(f"Proposal failed: {response.response.message}")
            
            # Create transaction
            tx = self.channel.create_tx(proposal_responses)
            
            # Send transaction to orderer
            tx_response = self.channel.send_tx(tx)
            
            if tx_response.status != 200:
                raise Exception(f"Transaction failed: {tx_response.info}")
            
            # Wait for transaction commit
            time.sleep(3)
            
            result = {
                "success": True,
                "transaction_id": tx_response.tx_id,
                "block_number": tx_response.block_number,
                "status": "verified",
                "timestamp": datetime.utcnow().isoformat(),
                "certificate_hash": verification_data["certificateHash"]
            }
            
            logger.info(f"Certificate {verification_data['certificateHash']} verified successfully")
            return result
            
        except Exception as e:
            logger.error(f"Failed to verify certificate: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_certificate(self, certificate_hash: str) -> Dict[str, Any]:
        """
        Get certificate details from blockchain
        
        Args:
            certificate_hash: Certificate hash to retrieve
        
        Returns:
            Dict containing certificate details
        """
        try:
            # Connect to channel
            if not self.connect_to_channel():
                raise Exception("Failed to connect to channel")
            
            # Query certificate
            response = self.channel.query_by_chaincode(
                chaincode_id=self.chaincode,
                fcn="GetCertificate",
                args=[certificate_hash],
                target_peer=self.channel.get_peer(self.peers["EcolOrgMSP"])
            )
            
            if response.status != 200:
                raise Exception(f"Query failed: {response.message}")
            
            certificate_data = json.loads(response.payload)
            
            result = {
                "success": True,
                "certificate": certificate_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get certificate: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_certificate_private_data(self, certificate_hash: str) -> Dict[str, Any]:
        """
        Get private data for a certificate
        
        Args:
            certificate_hash: Certificate hash
        
        Returns:
            Dict containing private certificate data
        """
        try:
            # Connect to channel
            if not self.connect_to_channel():
                raise Exception("Failed to connect to channel")
            
            # Query private data
            response = self.channel.query_by_chaincode(
                chaincode_id=self.chaincode,
                fcn="GetCertificatePrivateData",
                args=[certificate_hash],
                target_peer=self.channel.get_peer(self.peers["EcolOrgMSP"]),
                collection="certificatePrivateData"
            )
            
            if response.status != 200:
                raise Exception(f"Query failed: {response.message}")
            
            private_data = json.loads(response.payload)
            
            result = {
                "success": True,
                "private_data": private_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get certificate private data: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_verification_history(self, certificate_hash: str) -> Dict[str, Any]:
        """
        Get verification history for a certificate
        
        Args:
            certificate_hash: Certificate hash
        
        Returns:
            Dict containing verification history
        """
        try:
            # Connect to channel
            if not self.connect_to_channel():
                raise Exception("Failed to connect to channel")
            
            # Query verification history
            response = self.channel.query_by_chaincode(
                chaincode_id=self.chaincode,
                fcn="GetVerificationHistory",
                args=[certificate_hash],
                target_peer=self.channel.get_peer(self.peers["EcolOrgMSP"])
            )
            
            if response.status != 200:
                raise Exception(f"Query failed: {response.message}")
            
            verification_history = json.loads(response.payload)
            
            result = {
                "success": True,
                "verification_history": verification_history,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get verification history: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_all_certificates(self) -> Dict[str, Any]:
        """
        Get all certificates from blockchain
        
        Returns:
            Dict containing all certificates
        """
        try:
            # Connect to channel
            if not self.connect_to_channel():
                raise Exception("Failed to connect to channel")
            
            # Query all certificates
            response = self.channel.query_by_chaincode(
                chaincode_id=self.chaincode,
                fcn="GetAllCertificates",
                args=[],
                target_peer=self.channel.get_peer(self.peers["EcolOrgMSP"])
            )
            
            if response.status != 200:
                raise Exception(f"Query failed: {response.message}")
            
            certificates = json.loads(response.payload)
            
            result = {
                "success": True,
                "certificates": certificates,
                "count": len(certificates),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get all certificates: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_institution(self, institution_code: str) -> Dict[str, Any]:
        """
        Get institution details from blockchain
        
        Args:
            institution_code: Institution code
        
        Returns:
            Dict containing institution details
        """
        try:
            # Connect to channel
            if not self.connect_to_channel():
                raise Exception("Failed to connect to channel")
            
            # Query institution
            response = self.channel.query_by_chaincode(
                chaincode_id=self.chaincode,
                fcn="GetInstitution",
                args=[institution_code],
                target_peer=self.channel.get_peer(self.peers["EcolOrgMSP"])
            )
            
            if response.status != 200:
                raise Exception(f"Query failed: {response.message}")
            
            institution_data = json.loads(response.payload)
            
            result = {
                "success": True,
                "institution": institution_data,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get institution: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_network_statistics(self) -> Dict[str, Any]:
        """
        Get network-wide statistics
        
        Returns:
            Dict containing network statistics
        """
        try:
            # Connect to channel
            if not self.connect_to_channel():
                raise Exception("Failed to connect to channel")
            
            # Query network statistics
            response = self.channel.query_by_chaincode(
                chaincode_id=self.chaincode,
                fcn="GetNetworkStatistics",
                args=[],
                target_peer=self.channel.get_peer(self.peers["EcolOrgMSP"])
            )
            
            if response.status != 200:
                raise Exception(f"Query failed: {response.message}")
            
            statistics = json.loads(response.payload)
            
            result = {
                "success": True,
                "statistics": statistics,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get network statistics: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def revoke_certificate(self, revocation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Revoke a certificate on the blockchain
        
        Args:
            revocation_data: Revocation information including:
                - certificateHash: Certificate hash to revoke
                - reason: Revocation reason
                - revokedBy: Who revoked it
                - institutionCode: Institution code
        
        Returns:
            Dict containing revocation result
        """
        try:
            # Connect to channel
            if not self.connect_to_channel():
                raise Exception("Failed to connect to channel")
            
            # Prepare arguments
            args = [
                revocation_data["certificateHash"],
                revocation_data["reason"],
                revocation_data["revokedBy"],
                revocation_data["institutionCode"]
            ]
            
            # Create and submit transaction
            transient_map = {
                "revocation": json.dumps(revocation_data).encode()
            }
            
            # Get endorsing peers
            endorsing_peers = []
            for org in self.orgs:
                peer = self.channel.get_peer(self.peers[org])
                endorsing_peers.append(peer)
            
            # Create proposal
            proposal = self.channel.create_tx_proposal(
                chaincode_id=self.chaincode,
                fcn="RevokeCertificate",
                args=args,
                transient_map=transient_map
            )
            
            # Send proposal to endorsing peers
            proposal_responses = self.channel.send_tx_proposal(
                proposal, peers=endorsing_peers
            )
            
            # Check proposal responses
            for response in proposal_responses:
                if response.response.status != 200:
                    raise Exception(f"Proposal failed: {response.response.message}")
            
            # Create transaction
            tx = self.channel.create_tx(proposal_responses)
            
            # Send transaction to orderer
            tx_response = self.channel.send_tx(tx)
            
            if tx_response.status != 200:
                raise Exception(f"Transaction failed: {tx_response.info}")
            
            # Wait for transaction commit
            time.sleep(3)
            
            result = {
                "success": True,
                "transaction_id": tx_response.tx_id,
                "block_number": tx_response.block_number,
                "status": "revoked",
                "timestamp": datetime.utcnow().isoformat(),
                "certificate_hash": revocation_data["certificateHash"]
            }
            
            logger.info(f"Certificate {revocation_data['certificateHash']} revoked successfully")
            return result
            
        except Exception as e:
            logger.error(f"Failed to revoke certificate: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_audit_logs(self, event_type: str = "", institution_code: str = "", 
                      certificate_hash: str = "", limit: int = 100) -> Dict[str, Any]:
        """
        Get audit logs with optional filtering
        
        Args:
            event_type: Filter by event type
            institution_code: Filter by institution code
            certificate_hash: Filter by certificate hash
            limit: Maximum number of logs to return
        
        Returns:
            Dict containing audit logs
        """
        try:
            # Connect to channel
            if not self.connect_to_channel():
                raise Exception("Failed to connect to channel")
            
            # Prepare arguments
            args = [
                event_type,
                institution_code,
                certificate_hash,
                str(limit)
            ]
            
            # Query audit logs
            response = self.channel.query_by_chaincode(
                chaincode_id=self.chaincode,
                fcn="GetAuditLogs",
                args=args,
                target_peer=self.channel.get_peer(self.peers["EcolOrgMSP"])
            )
            
            if response.status != 200:
                raise Exception(f"Query failed: {response.message}")
            
            audit_logs = json.loads(response.payload)
            
            result = {
                "success": True,
                "audit_logs": audit_logs,
                "count": len(audit_logs),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to get audit logs: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def check_channel_health(self) -> Dict[str, Any]:
        """
        Check the health of the Fabric channel
        
        Returns:
            Dict containing channel health status
        """
        try:
            # Connect to channel
            if not self.connect_to_channel():
                return {
                    "success": False,
                    "error": "Failed to connect to channel",
                    "timestamp": datetime.utcnow().isoformat()
                }
            
            # Get channel info
            channel_info = self.channel.query_info()
            
            # Get block height
            block_height = channel_info.height
            
            # Check peer connectivity
            peer_status = {}
            for org in self.orgs:
                try:
                    peer = self.channel.get_peer(self.peers[org])
                    response = self.channel.query_by_chaincode(
                        chaincode_id=self.chaincode,
                        fcn="GetAllInstitutions",
                        args=[],
                        target_peer=peer
                    )
                    peer_status[org] = "connected" if response.status == 200 else "disconnected"
                except Exception:
                    peer_status[org] = "error"
            
            result = {
                "success": True,
                "channel_name": self.channel_name,
                "block_height": block_height,
                "peer_status": peer_status,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to check channel health: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

# Global Fabric SDK instance
fabric_sdk = FabricSDKManager()

# Convenience functions for common operations
def issue_certificate_on_blockchain(certificate_data: Dict[str, Any]) -> Dict[str, Any]:
    """Issue certificate on blockchain"""
    return fabric_sdk.issue_certificate(certificate_data)

def verify_certificate_on_blockchain(verification_data: Dict[str, Any]) -> Dict[str, Any]:
    """Verify certificate on blockchain"""
    return fabric_sdk.verify_certificate(verification_data)

def get_certificate_from_blockchain(certificate_hash: str) -> Dict[str, Any]:
    """Get certificate from blockchain"""
    return fabric_sdk.get_certificate(certificate_hash)

def get_network_stats() -> Dict[str, Any]:
    """Get network statistics"""
    return fabric_sdk.get_network_statistics()

def check_fabric_health() -> Dict[str, Any]:
    """Check Fabric network health"""
    return fabric_sdk.check_channel_health()
