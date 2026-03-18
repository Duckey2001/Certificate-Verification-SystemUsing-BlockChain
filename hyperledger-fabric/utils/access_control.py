#!/usr/bin/env python3
"""
Hyperledger Fabric Access Control System for LGCSE Certificate Verification

This module provides comprehensive access control for private data collections,
including role-based permissions, fine-grained access policies, and audit logging.
"""

import os
import json
import time
import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import hmac

logger = logging.getLogger(__name__)

class AccessLevel(Enum):
    """Access levels for private data"""
    NONE = "none"
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"

class DataType(Enum):
    """Data types for access control"""
    CERTIFICATE = "certificate"
    VERIFICATION = "verification"
    INSTITUTION = "institution"
    AUDIT = "audit"
    STUDENT = "student"
    CROSS_ORG = "cross_org"

class AccessControlManager:
    """
    Comprehensive Access Control Manager for Hyperledger Fabric
    
    Provides:
    - Role-based access control (RBAC)
    - Fine-grained permissions for private data
    - Dynamic access policies
    - Access audit logging
    - Data encryption at rest
    """
    
    def __init__(self, config_path: str = None):
        """
        Initialize Access Control Manager
        
        Args:
            config_path: Path to access control configuration
        """
        self.config_path = config_path or "config/access_control.json"
        self.access_policies = {}
        self.user_roles = {}
        self.collection_permissions = {}
        self.encryption_keys = {}
        
        # Load configuration
        self._load_access_config()
        self._initialize_encryption()
    
    def _load_access_config(self):
        """Load access control configuration"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                
                self.access_policies = config.get("policies", {})
                self.user_roles = config.get("user_roles", {})
                self.collection_permissions = config.get("collection_permissions", {})
                
                logger.info(f"Loaded access control configuration from {self.config_path}")
            else:
                # Create default configuration
                self._create_default_config()
                
        except Exception as e:
            logger.error(f"Failed to load access config: {e}")
            raise
    
    def _create_default_config(self):
        """Create default access control configuration"""
        try:
            default_config = {
                "policies": {
                    "certificate_private": {
                        "roles": ["issuer", "admin"],
                        "access_level": "read",
                        "conditions": {
                            "institution_match": True,
                            "time_restricted": False
                        }
                    },
                    "verification_private": {
                        "roles": ["verifier", "issuer", "admin"],
                        "access_level": "read",
                        "conditions": {
                            "verification_access": True,
                            "audit_required": True
                        }
                    },
                    "institution_private": {
                        "roles": ["admin", "institution_admin"],
                        "access_level": "write",
                        "conditions": {
                            "same_institution": True,
                            "admin_approval": False
                        }
                    },
                    "audit_private": {
                        "roles": ["admin"],
                        "access_level": "read",
                        "conditions": {
                            "admin_only": True,
                            "audit_trail_required": True
                        }
                    },
                    "student_private": {
                        "roles": ["issuer", "admin"],
                        "access_level": "read",
                        "conditions": {
                            "student_data_access": True,
                            "consent_required": True
                        }
                    },
                    "cross_org_shared": {
                        "roles": ["admin", "verifier"],
                        "access_level": "read",
                        "conditions": {
                            "multi_org_approval": True,
                            "data_classification": "shared"
                        }
                    }
                },
                "user_roles": {
                    "admin": {
                        "permissions": ["read", "write", "delete", "admin"],
                        "scope": "all",
                        "collections": ["certificatePrivateData", "verificationPrivateData", "institutionPrivateData", "auditPrivateData", "studentPrivateData", "crossOrgSharedData"]
                    },
                    "issuer": {
                        "permissions": ["read", "write"],
                        "scope": "institution",
                        "collections": ["certificatePrivateData", "verificationPrivateData", "studentPrivateData"]
                    },
                    "verifier": {
                        "permissions": ["read"],
                        "scope": "cross_org",
                        "collections": ["certificatePrivateData", "verificationPrivateData", "crossOrgSharedData"]
                    },
                    "institution_admin": {
                        "permissions": ["read", "write"],
                        "scope": "institution",
                        "collections": ["institutionPrivateData", "certificatePrivateData"]
                    },
                    "auditor": {
                        "permissions": ["read"],
                        "scope": "audit",
                        "collections": ["auditPrivateData", "verificationPrivateData"]
                    }
                },
                "collection_permissions": {
                    "certificatePrivateData": {
                        "default_access": "none",
                        "required_roles": ["issuer", "admin"],
                        "encryption_required": True,
                        "audit_access": True
                    },
                    "verificationPrivateData": {
                        "default_access": "none", 
                        "required_roles": ["verifier", "issuer", "admin"],
                        "encryption_required": True,
                        "audit_access": True
                    },
                    "institutionPrivateData": {
                        "default_access": "none",
                        "required_roles": ["admin", "institution_admin"],
                        "encryption_required": True,
                        "audit_access": True
                    },
                    "auditPrivateData": {
                        "default_access": "none",
                        "required_roles": ["admin"],
                        "encryption_required": True,
                        "audit_access": True
                    },
                    "studentPrivateData": {
                        "default_access": "none",
                        "required_roles": ["issuer", "admin"],
                        "encryption_required": True,
                        "audit_access": True
                    },
                    "crossOrgSharedData": {
                        "default_access": "read",
                        "required_roles": ["admin", "verifier"],
                        "encryption_required": False,
                        "audit_access": True
                    }
                }
            }
            
            # Save default configuration
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            self.access_policies = default_config["policies"]
            self.user_roles = default_config["user_roles"]
            self.collection_permissions = default_config["collection_permissions"]
            
            logger.info("Created default access control configuration")
            
        except Exception as e:
            logger.error(f"Failed to create default config: {e}")
            raise
    
    def _initialize_encryption(self):
        """Initialize encryption keys for data protection"""
        try:
            # Generate encryption keys for different data types
            self.encryption_keys = {
                "certificate": self._generate_encryption_key("certificate"),
                "verification": self._generate_encryption_key("verification"),
                "institution": self._generate_encryption_key("institution"),
                "audit": self._generate_encryption_key("audit"),
                "student": self._generate_encryption_key("student")
            }
            
            logger.info("Encryption keys initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise
    
    def _generate_encryption_key(self, key_type: str) -> str:
        """Generate encryption key for data type"""
        try:
            # Generate deterministic key based on type and timestamp
            seed = f"lgcse_{key_type}_{datetime.utcnow().strftime('%Y%m%d')}"
            return hashlib.sha256(seed.encode()).hexdigest()
            
        except Exception as e:
            logger.error(f"Failed to generate encryption key: {e}")
            raise
    
    def check_access_permission(self, user_id: str, user_role: str, institution_code: str, 
                              collection_name: str, operation: str, data_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Check if user has permission to access private data collection
        
        Args:
            user_id: User ID
            user_role: User role
            institution_code: Institution code
            collection_name: Collection name
            operation: Operation (read, write, delete)
            data_context: Additional context for access decision
        
        Returns:
            Dict containing access decision and details
        """
        try:
            # Get collection permissions
            collection_config = self.collection_permissions.get(collection_name, {})
            required_roles = collection_config.get("required_roles", [])
            
            # Check basic role access
            if user_role not in required_roles and "admin" not in required_roles:
                return {
                    "access_granted": False,
                    "reason": "Insufficient role permissions",
                    "required_roles": required_roles,
                    "user_role": user_role
                }
            
            # Get role configuration
            role_config = self.user_roles.get(user_role, {})
            role_permissions = role_config.get("permissions", [])
            role_scope = role_config.get("scope", "none")
            role_collections = role_config.get("collections", [])
            
            # Check if operation is allowed for role
            if operation not in role_permissions:
                return {
                    "access_granted": False,
                    "reason": f"Operation '{operation}' not allowed for role '{user_role}'",
                    "allowed_operations": role_permissions
                }
            
            # Check collection access for role
            if collection_name not in role_collections:
                return {
                    "access_granted": False,
                    "reason": f"Collection '{collection_name}' not accessible by role '{user_role}'",
                    "allowed_collections": role_collections
                }
            
            # Check scope-based access
            if not self._check_scope_access(user_role, role_scope, institution_code, data_context):
                return {
                    "access_granted": False,
                    "reason": f"Scope '{role_scope}' access denied",
                    "user_institution": institution_code
                }
            
            # Check additional conditions
            conditions_met = self._check_access_conditions(collection_name, user_role, institution_code, data_context)
            
            if not conditions_met["met"]:
                return {
                    "access_granted": False,
                    "reason": "Access conditions not met",
                    "conditions": conditions_met["conditions"]
                }
            
            # Log access attempt
            self._log_access_attempt(user_id, user_role, institution_code, collection_name, operation, True)
            
            return {
                "access_granted": True,
                "reason": "Access granted",
                "access_level": role_config.get("access_level", "read"),
                "encryption_required": collection_config.get("encryption_required", False),
                "audit_required": collection_config.get("audit_access", True)
            }
            
        except Exception as e:
            logger.error(f"Failed to check access permission: {e}")
            return {
                "access_granted": False,
                "reason": f"Access check failed: {str(e)}"
            }
    
    def _check_scope_access(self, user_role: str, scope: str, institution_code: str, data_context: Dict[str, Any]) -> bool:
        """Check scope-based access"""
        try:
            if scope == "all":
                return True
            elif scope == "institution":
                # Check if user's institution matches data institution
                data_institution = data_context.get("institution_code", "")
                return institution_code == data_institution
            elif scope == "cross_org":
                # Cross-org access allowed for verifiers
                return user_role in ["verifier", "admin"]
            elif scope == "audit":
                # Audit scope for auditors and admins
                return user_role in ["auditor", "admin"]
            else:
                return False
                
        except Exception as e:
            logger.error(f"Failed to check scope access: {e}")
            return False
    
    def _check_access_conditions(self, collection_name: str, user_role: str, institution_code: str, data_context: Dict[str, Any]) -> Dict[str, Any]:
        """Check additional access conditions"""
        try:
            conditions = {}
            all_met = True
            
            # Get policy for collection
            policy_key = collection_name.replace("Data", "_private")
            policy = self.access_policies.get(policy_key, {})
            policy_conditions = policy.get("conditions", {})
            
            # Check institution match condition
            if policy_conditions.get("institution_match", False):
                data_institution = data_context.get("institution_code", "")
                institution_match = institution_code == data_institution
                conditions["institution_match"] = institution_match
                if not institution_match:
                    all_met = False
            
            # Check verification access condition
            if policy_conditions.get("verification_access", False):
                verification_allowed = user_role in ["verifier", "issuer", "admin"]
                conditions["verification_access"] = verification_allowed
                if not verification_allowed:
                    all_met = False
            
            # Check admin only condition
            if policy_conditions.get("admin_only", False):
                admin_only = user_role == "admin"
                conditions["admin_only"] = admin_only
                if not admin_only:
                    all_met = False
            
            # Check same institution condition
            if policy_conditions.get("same_institution", False):
                data_institution = data_context.get("institution_code", "")
                same_institution = institution_code == data_institution
                conditions["same_institution"] = same_institution
                if not same_institution:
                    all_met = False
            
            # Check multi-org approval condition
            if policy_conditions.get("multi_org_approval", False):
                # In production, this would check actual approval records
                multi_org_approved = user_role == "admin" or data_context.get("multi_org_approved", False)
                conditions["multi_org_approval"] = multi_org_approved
                if not multi_org_approved:
                    all_met = False
            
            return {
                "met": all_met,
                "conditions": conditions
            }
            
        except Exception as e:
            logger.error(f"Failed to check access conditions: {e}")
            return {"met": False, "conditions": {}}
    
    def encrypt_private_data(self, data: str, data_type: str) -> Dict[str, Any]:
        """
        Encrypt private data before storage
        
        Args:
            data: Data to encrypt
            data_type: Type of data (certificate, verification, etc.)
        
        Returns:
            Dict containing encrypted data and metadata
        """
        try:
            encryption_key = self.encryption_keys.get(data_type)
            if not encryption_key:
                raise Exception(f"No encryption key found for data type: {data_type}")
            
            # Simple XOR encryption (in production, use AES)
            encrypted_data = self._xor_encrypt(data, encryption_key)
            
            # Generate checksum
            checksum = hashlib.sha256(f"{data}{encryption_key}".encode()).hexdigest()
            
            return {
                "success": True,
                "encrypted_data": encrypted_data,
                "checksum": checksum,
                "encryption_method": "xor",
                "data_type": data_type,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to encrypt private data: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def decrypt_private_data(self, encrypted_data: str, data_type: str, checksum: str) -> Dict[str, Any]:
        """
        Decrypt private data after retrieval
        
        Args:
            encrypted_data: Encrypted data
            data_type: Type of data
            checksum: Data checksum for verification
        
        Returns:
            Dict containing decrypted data and verification
        """
        try:
            encryption_key = self.encryption_keys.get(data_type)
            if not encryption_key:
                raise Exception(f"No encryption key found for data type: {data_type}")
            
            # Decrypt data
            decrypted_data = self._xor_decrypt(encrypted_data, encryption_key)
            
            # Verify checksum
            expected_checksum = hashlib.sha256(f"{decrypted_data}{encryption_key}".encode()).hexdigest()
            checksum_valid = hmac.compare_digest(checksum, expected_checksum)
            
            if not checksum_valid:
                raise Exception("Checksum verification failed - data may be corrupted")
            
            return {
                "success": True,
                "decrypted_data": decrypted_data,
                "checksum_valid": checksum_valid,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to decrypt private data: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _xor_encrypt(self, data: str, key: str) -> str:
        """Simple XOR encryption (for demonstration - use AES in production)"""
        try:
            encrypted = []
            for i, char in enumerate(data):
                key_char = key[i % len(key)]
                encrypted_char = chr(ord(char) ^ ord(key_char))
                encrypted.append(encrypted_char)
            return ''.join(encrypted)
            
        except Exception as e:
            logger.error(f"XOR encryption failed: {e}")
            raise
    
    def _xor_decrypt(self, encrypted_data: str, key: str) -> str:
        """Simple XOR decryption (for demonstration - use AES in production)"""
        try:
            # XOR is symmetric, so decryption is the same as encryption
            return self._xor_encrypt(encrypted_data, key)
            
        except Exception as e:
            logger.error(f"XOR decryption failed: {e}")
            raise
    
    def _log_access_attempt(self, user_id: str, user_role: str, institution_code: str, 
                           collection_name: str, operation: str, access_granted: bool):
        """Log access attempt for audit purposes"""
        try:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "user_id": user_id,
                "user_role": user_role,
                "institution_code": institution_code,
                "collection_name": collection_name,
                "operation": operation,
                "access_granted": access_granted,
                "ip_address": "127.0.0.1",  # Would be extracted from request
                "user_agent": "Fabric-SDK"  # Would be extracted from request
            }
            
            # In production, this would be stored in audit log collection
            logger.info(f"Access attempt logged: {json.dumps(log_entry)}")
            
        except Exception as e:
            logger.error(f"Failed to log access attempt: {e}")
    
    def update_access_policy(self, policy_name: str, policy_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update access policy configuration
        
        Args:
            policy_name: Policy name
            policy_config: New policy configuration
        
        Returns:
            Dict containing update result
        """
        try:
            # Validate policy configuration
            required_fields = ["roles", "access_level", "conditions"]
            for field in required_fields:
                if field not in policy_config:
                    raise Exception(f"Missing required field: {field}")
            
            # Update policy
            self.access_policies[policy_name] = policy_config
            
            # Save updated configuration
            self._save_access_config()
            
            logger.info(f"Access policy '{policy_name}' updated successfully")
            
            return {
                "success": True,
                "policy_name": policy_name,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to update access policy: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def add_user_role(self, role_name: str, role_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add new user role configuration
        
        Args:
            role_name: Role name
            role_config: Role configuration
        
        Returns:
            Dict containing addition result
        """
        try:
            # Validate role configuration
            required_fields = ["permissions", "scope", "collections"]
            for field in required_fields:
                if field not in role_config:
                    raise Exception(f"Missing required field: {field}")
            
            # Add role
            self.user_roles[role_name] = role_config
            
            # Save updated configuration
            self._save_access_config()
            
            logger.info(f"User role '{role_name}' added successfully")
            
            return {
                "success": True,
                "role_name": role_name,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to add user role: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _save_access_config(self):
        """Save access control configuration to file"""
        try:
            config = {
                "policies": self.access_policies,
                "user_roles": self.user_roles,
                "collection_permissions": self.collection_permissions
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save access config: {e}")
            raise
    
    def get_access_report(self, institution_code: str = None) -> Dict[str, Any]:
        """
        Generate comprehensive access control report
        
        Args:
            institution_code: Optional institution filter
        
        Returns:
            Dict containing access control report
        """
        try:
            report = {
                "timestamp": datetime.utcnow().isoformat(),
                "total_policies": len(self.access_policies),
                "total_roles": len(self.user_roles),
                "total_collections": len(self.collection_permissions),
                "policies": {},
                "roles": {},
                "collections": {}
            }
            
            # Include policy details
            for policy_name, policy_config in self.access_policies.items():
                report["policies"][policy_name] = {
                    "roles": policy_config.get("roles", []),
                    "access_level": policy_config.get("access_level", "none"),
                    "conditions": len(policy_config.get("conditions", {}))
                }
            
            # Include role details
            for role_name, role_config in self.user_roles.items():
                report["roles"][role_name] = {
                    "permissions": role_config.get("permissions", []),
                    "scope": role_config.get("scope", "none"),
                    "collections": len(role_config.get("collections", []))
                }
            
            # Include collection details
            for collection_name, collection_config in self.collection_permissions.items():
                report["collections"][collection_name] = {
                    "default_access": collection_config.get("default_access", "none"),
                    "required_roles": collection_config.get("required_roles", []),
                    "encryption_required": collection_config.get("encryption_required", False),
                    "audit_access": collection_config.get("audit_access", False)
                }
            
            return {
                "success": True,
                "report": report
            }
            
        except Exception as e:
            logger.error(f"Failed to generate access report: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Global access control manager instance
access_control_manager = AccessControlManager()

# Convenience functions
def check_private_data_access(user_id: str, user_role: str, institution_code: str, 
                             collection_name: str, operation: str, data_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Check private data access permission"""
    return access_control_manager.check_access_permission(user_id, user_role, institution_code, collection_name, operation, data_context)

def encrypt_data(data: str, data_type: str) -> Dict[str, Any]:
    """Encrypt private data"""
    return access_control_manager.encrypt_private_data(data, data_type)

def decrypt_data(encrypted_data: str, data_type: str, checksum: str) -> Dict[str, Any]:
    """Decrypt private data"""
    return access_control_manager.decrypt_private_data(encrypted_data, data_type, checksum)
