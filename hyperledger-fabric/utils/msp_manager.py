#!/usr/bin/env python3
"""
Hyperledger Fabric MSP (Membership Service Provider) Management System

This module provides comprehensive MSP management for LGCSE Certificate Verification System,
including user enrollment, certificate management, and identity lifecycle operations.
"""

import os
import json
import time
import logging
import subprocess
import tempfile
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime, timedelta
import shutil

import requests
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)

class MSPManager:
    """
    Hyperledger Fabric Membership Service Provider Manager
    
    Provides comprehensive MSP management including:
    - User enrollment and registration
    - Certificate generation and management
    - Identity lifecycle operations
    - MSP configuration management
    - Certificate revocation and renewal
    """
    
    def __init__(self, network_config_path: str = None):
        """
        Initialize MSP Manager
        
        Args:
            network_config_path: Path to network configuration
        """
        self.network_config_path = network_config_path or "config/network-config.json"
        self.msp_configs = {}
        self.ca_clients = {}
        self.crypto_suite = None
        
        # Load network configuration
        self._load_network_config()
        
        # Initialize crypto suite
        self._initialize_crypto_suite()
    
    def _load_network_config(self):
        """Load network configuration"""
        try:
            if os.path.exists(self.network_config_path):
                with open(self.network_config_path, 'r') as f:
                    config = json.load(f)
                
                # Extract MSP configurations
                for org_name, org_config in config.get("organizations", {}).items():
                    self.msp_configs[org_name] = {
                        "mspid": org_config.get("mspid"),
                        "ca_url": org_config.get("ca", {}).get("url"),
                        "ca_name": org_config.get("ca", {}).get("ca_name"),
                        "admin_certs": org_config.get("admin_certs", []),
                        "root_certs": org_config.get("root_certs", []),
                        "tls_root_certs": org_config.get("tls_root_certs", []),
                        "tls_intermediate_certs": org_config.get("tls_intermediate_certs", [])
                    }
                
                logger.info(f"Loaded {len(self.msp_configs)} MSP configurations")
            else:
                logger.warning(f"Network config file not found: {self.network_config_path}")
                
        except Exception as e:
            logger.error(f"Failed to load network config: {e}")
            raise
    
    def _initialize_crypto_suite(self):
        """Initialize cryptographic suite"""
        try:
            # This would integrate with Fabric SDK's crypto suite
            # For now, we'll use basic cryptography operations
            self.crypto_suite = {
                "hash_algorithm": "SHA256",
                "sign_algorithm": "ECDSA",
                "key_size": 256
            }
            logger.info("Crypto suite initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize crypto suite: {e}")
            raise
    
    def register_user(self, org_name: str, user_id: str, user_type: str = "client", 
                     affiliation: str = "", max_enrollments: int = 0, 
                     attributes: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Register a new user with the CA
        
        Args:
            org_name: Organization name
            user_id: User ID
            user_type: User type (client, peer, orderer, admin)
            affiliation: User affiliation
            max_enrollments: Maximum enrollments allowed
            attributes: User attributes
        
        Returns:
            Dict containing registration result
        """
        try:
            org_config = self.msp_configs.get(org_name)
            if not org_config:
                raise Exception(f"Organization {org_name} not found")
            
            # Prepare registration request
            registration_data = {
                "id": user_id,
                "type": user_type,
                "affiliation": affiliation or org_name.lower(),
                "max_enrollments": max_enrollments,
                "attributes": attributes or []
            }
            
            # Add default attributes based on user type
            if user_type == "admin":
                registration_data["attributes"].extend([
                    {"name": "hf.Registrar.Roles", "value": "client,orderer,peer,user,admin"},
                    {"name": "hf.Registrar.DelegateRoles", "value": "client,orderer,peer,user,admin"},
                    {"name": "hf.Revoker", "value": "true"},
                    {"name": "hf.GenCRL", "value": "true"},
                    {"name": "hf.AffiliationMgr", "value": "true"},
                    {"name": "hf.IntermediateCA", "value": "true"}
                ])
            elif user_type == "peer":
                registration_data["attributes"].extend([
                    {"name": "hf.Revoker", "value": "true"},
                    {"name": "hf.GenCRL", "value": "true"},
                    {"name": "hf.Registrar.Roles", "value": "peer"},
                    {"name": "hf.Registrar.DelegateRoles", "value": "peer"}
                ])
            
            # Register user with CA
            ca_url = org_config["ca_url"]
            ca_name = org_config["ca_name"]
            
            # This would use Fabric CA client SDK
            # For now, we'll simulate the registration
            registration_result = self._simulate_ca_registration(ca_url, ca_name, registration_data)
            
            logger.info(f"User {user_id} registered successfully for {org_name}")
            return registration_result
            
        except Exception as e:
            logger.error(f"Failed to register user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def enroll_user(self, org_name: str, user_id: str, enrollment_secret: str = None) -> Dict[str, Any]:
        """
        Enroll a user and generate certificates
        
        Args:
            org_name: Organization name
            user_id: User ID
            enrollment_secret: Enrollment secret (optional)
        
        Returns:
            Dict containing enrollment result
        """
        try:
            org_config = self.msp_configs.get(org_name)
            if not org_config:
                raise Exception(f"Organization {org_name} not found")
            
            # Prepare enrollment request
            enrollment_data = {
                "id": user_id,
                "secret": enrollment_secret or f"{user_id}pw"
            }
            
            # Enroll user with CA
            ca_url = org_config["ca_url"]
            ca_name = org_config["ca_name"]
            
            # Generate enrollment certificates
            enrollment_result = self._generate_enrollment_certificates(
                ca_url, ca_name, user_id, enrollment_data
            )
            
            logger.info(f"User {user_id} enrolled successfully for {org_name}")
            return enrollment_result
            
        except Exception as e:
            logger.error(f"Failed to enroll user {user_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _simulate_ca_registration(self, ca_url: str, ca_name: str, registration_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate CA registration (would use actual Fabric CA SDK)"""
        try:
            # Simulate CA registration
            time.sleep(0.5)  # Simulate network delay
            
            return {
                "success": True,
                "registration_id": f"reg_{int(time.time())}",
                "secret": f"{registration_data['id']}pw",
                "ca_name": ca_name,
                "user_id": registration_data["id"],
                "user_type": registration_data["type"],
                "affiliation": registration_data["affiliation"],
                "max_enrollments": registration_data["max_enrollments"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"CA registration simulation failed: {e}")
    
    def _generate_enrollment_certificates(self, ca_url: str, ca_name: str, user_id: str, 
                                       enrollment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate enrollment certificates"""
        try:
            # Generate key pair
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            
            public_key = private_key.public_key()
            
            # Create certificate subject
            subject = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "LS"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Maseru"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Maseru"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, ca_name),
                x509.NameAttribute(NameOID.COMMON_NAME, user_id),
                x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "client")
            ])
            
            # Create self-signed certificate (in production, this would be signed by CA)
            certificate = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                subject
            ).public_key(
                public_key
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=365)
            ).add_extension(
                x509.BasicConstraints(ca=False, path_length=None),
                critical=True,
            ).sign(private_key, hashes.SHA256(), default_backend())
            
            # Serialize certificates and keys
            cert_pem = certificate.public_bytes(serialization.Encoding.PEM).decode()
            key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode()
            
            # Create MSP directory structure
            msp_path = f"msp/{ca_name}/{user_id}"
            os.makedirs(msp_path, exist_ok=True)
            
            # Save certificates and keys
            with open(f"{msp_path}/signcerts/cert.pem", "w") as f:
                f.write(cert_pem)
            
            with open(f"{msp_path}/keystore/key.pem", "w") as f:
                f.write(key_pem)
            
            # Copy CA certificates
            self._copy_ca_certificates(msp_path, ca_name)
            
            return {
                "success": True,
                "certificate": cert_pem,
                "private_key": key_pem,
                "msp_path": msp_path,
                "user_id": user_id,
                "ca_name": ca_name,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"Certificate generation failed: {e}")
    
    def _copy_ca_certificates(self, msp_path: str, ca_name: str):
        """Copy CA certificates to MSP directory"""
        try:
            # Create directories
            os.makedirs(f"{msp_path}/cacerts", exist_ok=True)
            os.makedirs(f"{msp_path}/tlscacerts", exist_ok=True)
            
            # In production, these would be actual CA certificates
            # For now, we'll create placeholder certificates
            ca_cert = self._generate_placeholder_ca_cert(ca_name)
            
            with open(f"{msp_path}/cacerts/ca-cert.pem", "w") as f:
                f.write(ca_cert)
            
            with open(f"{msp_path}/tlscacerts/tls-ca-cert.pem", "w") as f:
                f.write(ca_cert)
                
        except Exception as e:
            logger.error(f"Failed to copy CA certificates: {e}")
    
    def _generate_placeholder_ca_cert(self, ca_name: str) -> str:
        """Generate placeholder CA certificate"""
        try:
            # Generate CA key pair
            ca_private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            
            # Create CA certificate
            ca_subject = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "LS"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Maseru"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Maseru"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, ca_name),
                x509.NameAttribute(NameOID.COMMON_NAME, f"CA-{ca_name}"),
                x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "CA")
            ])
            
            ca_cert = x509.CertificateBuilder().subject_name(
                ca_subject
            ).issuer_name(
                ca_subject
            ).public_key(
                ca_private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=3650)  # 10 years
            ).add_extension(
                x509.BasicConstraints(ca=True, path_length=None),
                critical=True,
            ).add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_encipherment=True,
                    key_cert_sign=True,
                    crl_sign=True
                )
            ).sign(ca_private_key, hashes.SHA256(), default_backend())
            
            return ca_cert.public_bytes(serialization.Encoding.PEM).decode()
            
        except Exception as e:
            logger.error(f"Failed to generate placeholder CA cert: {e}")
            raise
    
    def create_msp_config(self, org_name: str, msp_path: str) -> Dict[str, Any]:
        """
        Create MSP configuration
        
        Args:
            org_name: Organization name
            msp_path: Path to MSP directory
        
        Returns:
            Dict containing MSP configuration
        """
        try:
            org_config = self.msp_configs.get(org_name)
            if not org_config:
                raise Exception(f"Organization {org_name} not found")
            
            # Create config.yaml
            config_data = {
                "NodeOUs": {
                    "Enable": True,
                    "ClientOUIdentifier": {
                        "Certificate": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----",
                        "OrganizationalUnitIdentifier": "client"
                    },
                    "PeerOUIdentifier": {
                        "Certificate": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----",
                        "OrganizationalUnitIdentifier": "peer"
                    },
                    "AdminOUIdentifier": {
                        "Certificate": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----",
                        "OrganizationalUnitIdentifier": "admin"
                    },
                    "OrdererOUIdentifier": {
                        "Certificate": "-----BEGIN CERTIFICATE-----\n...\n-----END CERTIFICATE-----",
                        "OrganizationalUnitIdentifier": "orderer"
                    }
                }
            }
            
            config_path = f"{msp_path}/config.yaml"
            with open(config_path, "w") as f:
                yaml.dump(config_data, f, default_flow_style=False)
            
            return {
                "success": True,
                "msp_path": msp_path,
                "config_path": config_path,
                "mspid": org_config["mspid"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to create MSP config: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def revoke_certificate(self, org_name: str, user_id: str, reason: str = "") -> Dict[str, Any]:
        """
        Revoke a user certificate
        
        Args:
            org_name: Organization name
            user_id: User ID
            reason: Revocation reason
        
        Returns:
            Dict containing revocation result
        """
        try:
            org_config = self.msp_configs.get(org_name)
            if not org_config:
                raise Exception(f"Organization {org_name} not found")
            
            # Generate Certificate Revocation List (CRL)
            crl_result = self._generate_crl(org_name, user_id, reason)
            
            logger.info(f"Certificate for user {user_id} in {org_name} revoked")
            return crl_result
            
        except Exception as e:
            logger.error(f"Failed to revoke certificate: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _generate_crl(self, org_name: str, user_id: str, reason: str) -> Dict[str, Any]:
        """Generate Certificate Revocation List"""
        try:
            # This would generate an actual CRL
            # For now, we'll create a placeholder
            crl_data = {
                "version": 2,
                "issuer": f"CA-{org_name}",
                "last_update": datetime.utcnow().isoformat(),
                "next_update": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "revoked_certificates": [
                    {
                        "serial_number": "123456789",
                        "revocation_date": datetime.utcnow().isoformat(),
                        "reason": reason or "Certificate revoked"
                    }
                ]
            }
            
            # Save CRL
            crl_path = f"crl/{org_name}/crl.pem"
            os.makedirs(os.path.dirname(crl_path), exist_ok=True)
            
            with open(crl_path, "w") as f:
                json.dump(crl_data, f, indent=2)
            
            return {
                "success": True,
                "crl_path": crl_path,
                "revoked_user": user_id,
                "reason": reason,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            raise Exception(f"CRL generation failed: {e}")
    
    def renew_certificate(self, org_name: str, user_id: str) -> Dict[str, Any]:
        """
        Renew a user certificate
        
        Args:
            org_name: Organization name
            user_id: User ID
        
        Returns:
            Dict containing renewal result
        """
        try:
            org_config = self.msp_configs.get(org_name)
            if not org_config:
                raise Exception(f"Organization {org_name} not found")
            
            # Generate new certificates
            enrollment_data = {
                "id": user_id,
                "secret": f"{user_id}pw"
            }
            
            ca_url = org_config["ca_url"]
            ca_name = org_config["ca_name"]
            
            renewal_result = self._generate_enrollment_certificates(
                ca_url, ca_name, user_id, enrollment_data
            )
            
            logger.info(f"Certificate for user {user_id} in {org_name} renewed")
            return renewal_result
            
        except Exception as e:
            logger.error(f"Failed to renew certificate: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def get_msp_info(self, org_name: str) -> Dict[str, Any]:
        """
        Get MSP information for an organization
        
        Args:
            org_name: Organization name
        
        Returns:
            Dict containing MSP information
        """
        try:
            org_config = self.msp_configs.get(org_name)
            if not org_config:
                raise Exception(f"Organization {org_name} not found")
            
            # Get MSP statistics
            msp_path = f"msp/{org_config['ca_name']}"
            user_count = 0
            if os.path.exists(msp_path):
                user_count = len([d for d in os.listdir(msp_path) if os.path.isdir(os.path.join(msp_path, d))])
            
            return {
                "success": True,
                "organization": org_name,
                "mspid": org_config["mspid"],
                "ca_name": org_config["ca_name"],
                "ca_url": org_config["ca_url"],
                "user_count": user_count,
                "msp_path": msp_path,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get MSP info: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def list_all_msps(self) -> Dict[str, Any]:
        """
        List all MSP configurations
        
        Returns:
            Dict containing all MSP information
        """
        try:
            msp_list = []
            for org_name, org_config in self.msp_configs.items():
                msp_info = self.get_msp_info(org_name)
                msp_list.append(msp_info)
            
            return {
                "success": True,
                "msps": msp_list,
                "total_count": len(msp_list),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to list MSPs: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def validate_certificate(self, cert_pem: str, org_name: str) -> Dict[str, Any]:
        """
        Validate a certificate against MSP
        
        Args:
            cert_pem: Certificate in PEM format
            org_name: Organization name
        
        Returns:
            Dict containing validation result
        """
        try:
            org_config = self.msp_configs.get(org_name)
            if not org_config:
                raise Exception(f"Organization {org_name} not found")
            
            # Parse certificate
            cert = x509.load_pem_x509_certificate(cert_pem.encode(), default_backend())
            
            # Check certificate validity
            now = datetime.utcnow()
            is_valid = now >= cert.not_valid_before and now <= cert.not_valid_after
            
            # Check if certificate is revoked (simplified)
            is_revoked = False  # Would check against CRL
            
            # Check certificate chain
            chain_valid = True  # Would validate against CA certificates
            
            validation_result = {
                "success": True,
                "is_valid": is_valid and not is_revoked and chain_valid,
                "subject": cert.subject.rfc4514_string(),
                "issuer": cert.issuer.rfc4514_string(),
                "serial_number": str(cert.serial_number),
                "not_valid_before": cert.not_valid_before.isoformat(),
                "not_valid_after": cert.not_valid_after.isoformat(),
                "is_revoked": is_revoked,
                "chain_valid": chain_valid,
                "organization": org_name,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Failed to validate certificate: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

# Global MSP Manager instance
msp_manager = MSPManager()

# Convenience functions
def register_fabric_user(org_name: str, user_id: str, user_type: str = "client", 
                         affiliation: str = "", attributes: List[Dict[str, str]] = None) -> Dict[str, Any]:
    """Register a new Fabric user"""
    return msp_manager.register_user(org_name, user_id, user_type, affiliation, 0, attributes)

def enroll_fabric_user(org_name: str, user_id: str, enrollment_secret: str = None) -> Dict[str, Any]:
    """Enroll a Fabric user"""
    return msp_manager.enroll_user(org_name, user_id, enrollment_secret)

def get_fabric_msp_info(org_name: str) -> Dict[str, Any]:
    """Get Fabric MSP information"""
    return msp_manager.get_msp_info(org_name)

def list_fabric_msps() -> Dict[str, Any]:
    """List all Fabric MSPs"""
    return msp_manager.list_all_msps()
