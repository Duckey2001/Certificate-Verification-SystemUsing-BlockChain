#!/usr/bin/env python3
"""
Hyperledger Fabric Cross-Organization Channel Management System

This module provides comprehensive multi-channel management for the LGCSE Certificate
Verification System, including channel creation, governance, cross-channel communication,
and inter-organization data sharing.
"""

import os
import json
import time
import logging
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import tempfile
import shutil

logger = logging.getLogger(__name__)

class ChannelType(Enum):
    """Channel types for different use cases"""
    CERTIFICATE_VERIFICATION = "certificate_verification"
    INSTITUTION_GOVERNANCE = "institution_governance"
    AUDIT_COMPLIANCE = "audit_compliance"
    RESEARCH_ANALYTICS = "research_analytics"
    EMERGENCY_RESPONSE = "emergency_response"
    CROSS_BORDER = "cross_border"

class ChannelStatus(Enum):
    """Channel status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    SUSPENDED = "suspended"
    ARCHIVED = "archived"

class ChannelManager:
    """
    Comprehensive Channel Management System for Hyperledger Fabric
    
    Provides:
    - Multi-channel architecture management
    - Cross-channel communication protocols
    - Channel governance and lifecycle management
    - Inter-organization data sharing
    - Channel upgrade procedures
    """
    
    def __init__(self, network_config_path: str = None):
        """
        Initialize Channel Manager
        
        Args:
            network_config_path: Path to network configuration
        """
        self.network_config_path = network_config_path or "config/network-config.json"
        self.channel_configs = {}
        self.channel_policies = {}
        self.cross_channel_policies = {}
        self.channel_registry = {}
        
        # Load configuration
        self._load_channel_config()
        self._initialize_channel_registry()
    
    def _load_channel_config(self):
        """Load channel management configuration"""
        try:
            config_path = "config/channel_config.json"
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
                
                self.channel_configs = config.get("channels", {})
                self.channel_policies = config.get("policies", {})
                self.cross_channel_policies = config.get("cross_channel_policies", {})
                
                logger.info(f"Loaded channel configuration from {config_path}")
            else:
                # Create default configuration
                self._create_default_channel_config()
                
        except Exception as e:
            logger.error(f"Failed to load channel config: {e}")
            raise
    
    def _create_default_channel_config(self):
        """Create default channel configuration"""
        try:
            default_config = {
                "channels": {
                    "lgcse-certificate-channel": {
                        "name": "lgcse-certificate-channel",
                        "type": "certificate_verification",
                        "description": "Primary channel for certificate issuance and verification",
                        "organizations": ["EcolOrgMSP", "LimkokwingOrgMSP", "BothoOrgMSP", "NulOrgMSP"],
                        "consortium": "LGCSEConsortium",
                        "orderers": ["orderer.example.com"],
                        "status": "active",
                        "created_at": datetime.utcnow().isoformat(),
                        "policies": {
                            "readers": {
                                "rule": "ANY Readers"
                            },
                            "writers": {
                                "rule": "ANY Writers"
                            },
                            "admins": {
                                "rule": "MAJORITY Admins"
                            }
                        },
                        "capabilities": {
                            "application": "V2_0",
                            "channel": "V2_0"
                        }
                    },
                    "lgcse-governance-channel": {
                        "name": "lgcse-governance-channel",
                        "type": "institution_governance",
                        "description": "Channel for institutional governance and policy management",
                        "organizations": ["EcolOrgMSP", "LimkokwingOrgMSP", "BothoOrgMSP", "NulOrgMSP"],
                        "consortium": "LGCSEConsortium",
                        "orderers": ["orderer.example.com"],
                        "status": "active",
                        "created_at": datetime.utcnow().isoformat(),
                        "policies": {
                            "readers": {
                                "rule": "ANY Readers"
                            },
                            "writers": {
                                "rule": "MAJORITY Admins"
                            },
                            "admins": {
                                "rule": "MAJORITY Admins"
                            }
                        },
                        "capabilities": {
                            "application": "V2_0",
                            "channel": "V2_0"
                        }
                    },
                    "lgcse-audit-channel": {
                        "name": "lgcse-audit-channel",
                        "type": "audit_compliance",
                        "description": "Channel for audit trails and compliance reporting",
                        "organizations": ["EcolOrgMSP", "LimkokwingOrgMSP", "BothoOrgMSP", "NulOrgMSP"],
                        "consortium": "LGCSEConsortium",
                        "orderers": ["orderer.example.com"],
                        "status": "active",
                        "created_at": datetime.utcnow().isoformat(),
                        "policies": {
                            "readers": {
                                "rule": "ANY Admins"
                            },
                            "writers": {
                                "rule": "ANY Admins"
                            },
                            "admins": {
                                "rule": "MAJORITY Admins"
                            }
                        },
                        "capabilities": {
                            "application": "V2_0",
                            "channel": "V2_0"
                        }
                    },
                    "lgcse-analytics-channel": {
                        "name": "lgcse-analytics-channel",
                        "type": "research_analytics",
                        "description": "Channel for research data and analytics",
                        "organizations": ["EcolOrgMSP", "LimkokwingOrgMSP", "BothoOrgMSP", "NulOrgMSP"],
                        "consortium": "LGCSEConsortium",
                        "orderers": ["orderer.example.com"],
                        "status": "inactive",
                        "created_at": datetime.utcnow().isoformat(),
                        "policies": {
                            "readers": {
                                "rule": "ANY Readers"
                            },
                            "writers": {
                                "rule": "MAJORITY Admins"
                            },
                            "admins": {
                                "rule": "MAJORITY Admins"
                            }
                        },
                        "capabilities": {
                            "application": "V2_0",
                            "channel": "V2_0"
                        }
                    }
                },
                "policies": {
                    "channel_creation": {
                        "required_roles": ["admin"],
                        "min_orgs": 2,
                        "approval_required": True
                    },
                    "channel_update": {
                        "required_roles": ["admin"],
                        "min_approvals": 2,
                        "voting_period": "24h"
                    },
                    "channel_deletion": {
                        "required_roles": ["admin"],
                        "min_approvals": 3,
                        "grace_period": "7d"
                    }
                },
                "cross_channel_policies": {
                    "data_sharing": {
                        "allowed_channels": ["lgcse-certificate-channel", "lgcse-governance-channel"],
                        "data_types": ["certificate_metadata", "verification_results"],
                        "access_control": "role_based",
                        "audit_required": True
                    },
                    "event_propagation": {
                        "source_channels": ["lgcse-certificate-channel"],
                        "target_channels": ["lgcse-audit-channel"],
                        "event_types": ["certificate_issued", "certificate_verified", "certificate_revoked"],
                        "propagation_delay": "5s"
                    }
                }
            }
            
            # Save default configuration
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(default_config, f, indent=2)
            
            self.channel_configs = default_config["channels"]
            self.channel_policies = default_config["policies"]
            self.cross_channel_policies = default_config["cross_channel_policies"]
            
            logger.info("Created default channel configuration")
            
        except Exception as e:
            logger.error(f"Failed to create default channel config: {e}")
            raise
    
    def _initialize_channel_registry(self):
        """Initialize channel registry for tracking"""
        try:
            self.channel_registry = {
                "total_channels": len(self.channel_configs),
                "active_channels": 0,
                "inactive_channels": 0,
                "channel_types": {},
                "organizations": set(),
                "last_updated": datetime.utcnow().isoformat()
            }
            
            # Count channels by status and type
            for channel_name, channel_config in self.channel_configs.items():
                status = channel_config.get("status", "inactive")
                channel_type = channel_config.get("type", "unknown")
                organizations = channel_config.get("organizations", [])
                
                if status == "active":
                    self.channel_registry["active_channels"] += 1
                else:
                    self.channel_registry["inactive_channels"] += 1
                
                if channel_type not in self.channel_registry["channel_types"]:
                    self.channel_registry["channel_types"][channel_type] = 0
                self.channel_registry["channel_types"][channel_type] += 1
                
                self.channel_registry["organizations"].update(organizations)
            
            logger.info("Channel registry initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize channel registry: {e}")
            raise
    
    def create_channel(self, channel_name: str, channel_type: ChannelType, 
                      organizations: List[str], description: str = "", 
                      creator_org: str = None, policies: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Create a new channel
        
        Args:
            channel_name: Channel name
            channel_type: Channel type
            organizations: Participating organizations
            description: Channel description
            creator_org: Creator organization
            policies: Channel policies
        
        Returns:
            Dict containing channel creation result
        """
        try:
            # Validate channel creation permissions
            if not self._validate_channel_creation(creator_org, organizations):
                return {
                    "success": False,
                    "error": "Channel creation validation failed"
                }
            
            # Check if channel already exists
            if channel_name in self.channel_configs:
                return {
                    "success": False,
                    "error": f"Channel {channel_name} already exists"
                }
            
            # Create channel configuration
            channel_config = {
                "name": channel_name,
                "type": channel_type.value,
                "description": description or f"Channel for {channel_type.value}",
                "organizations": organizations,
                "consortium": "LGCSEConsortium",
                "orderers": ["orderer.example.com"],
                "status": "inactive",
                "created_at": datetime.utcnow().isoformat(),
                "created_by": creator_org,
                "policies": policies or self._get_default_policies(channel_type),
                "capabilities": {
                    "application": "V2_0",
                    "channel": "V2_0"
                },
                "chaincodes": [],
                "block_height": 0,
                "last_block_hash": ""
            }
            
            # Add to channel configurations
            self.channel_configs[channel_name] = channel_config
            
            # Update registry
            self._update_channel_registry()
            
            # Generate channel artifacts
            artifacts = self._generate_channel_artifacts(channel_name, channel_config)
            
            # Save configuration
            self._save_channel_config()
            
            logger.info(f"Channel {channel_name} created successfully")
            
            return {
                "success": True,
                "channel_name": channel_name,
                "channel_id": f"channel_{int(time.time())}",
                "artifacts": artifacts,
                "config": channel_config,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to create channel: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _validate_channel_creation(self, creator_org: str, organizations: List[str]) -> bool:
        """Validate channel creation permissions"""
        try:
            # Check minimum organization requirement
            if len(organizations) < 2:
                logger.error("Channel creation requires at least 2 organizations")
                return False
            
            # Check if creator org is in the list
            if creator_org and creator_org not in organizations:
                logger.error("Creator organization must be a channel participant")
                return False
            
            # Check organization validity
            valid_orgs = ["EcolOrgMSP", "LimkokwingOrgMSP", "BothoOrgMSP", "NulOrgMSP"]
            for org in organizations:
                if org not in valid_orgs:
                    logger.error(f"Invalid organization: {org}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Channel creation validation failed: {e}")
            return False
    
    def _get_default_policies(self, channel_type: ChannelType) -> Dict[str, Any]:
        """Get default policies for channel type"""
        try:
            if channel_type == ChannelType.CERTIFICATE_VERIFICATION:
                return {
                    "readers": {"rule": "ANY Readers"},
                    "writers": {"rule": "ANY Writers"},
                    "admins": {"rule": "MAJORITY Admins"}
                }
            elif channel_type == ChannelType.INSTITUTION_GOVERNANCE:
                return {
                    "readers": {"rule": "ANY Readers"},
                    "writers": {"rule": "MAJORITY Admins"},
                    "admins": {"rule": "MAJORITY Admins"}
                }
            elif channel_type == ChannelType.AUDIT_COMPLIANCE:
                return {
                    "readers": {"rule": "ANY Admins"},
                    "writers": {"rule": "ANY Admins"},
                    "admins": {"rule": "MAJORITY Admins"}
                }
            elif channel_type == ChannelType.RESEARCH_ANALYTICS:
                return {
                    "readers": {"rule": "ANY Readers"},
                    "writers": {"rule": "MAJORITY Admins"},
                    "admins": {"rule": "MAJORITY Admins"}
                }
            else:
                return {
                    "readers": {"rule": "ANY Readers"},
                    "writers": {"rule": "ANY Writers"},
                    "admins": {"rule": "MAJORITY Admins"}
                }
                
        except Exception as e:
            logger.error(f"Failed to get default policies: {e}")
            return {}
    
    def _generate_channel_artifacts(self, channel_name: str, channel_config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate channel artifacts"""
        try:
            artifacts = {}
            
            # Generate channel configuration transaction
            config_tx = self._generate_channel_config_tx(channel_name, channel_config)
            artifacts["config_tx"] = config_tx
            
            # Generate anchor peer updates
            anchor_updates = {}
            for org in channel_config["organizations"]:
                anchor_update = self._generate_anchor_peer_update(channel_name, org)
                anchor_updates[org] = anchor_update
            artifacts["anchor_updates"] = anchor_updates
            
            # Generate genesis block
            genesis_block = self._generate_genesis_block(channel_name, channel_config)
            artifacts["genesis_block"] = genesis_block
            
            return artifacts
            
        except Exception as e:
            logger.error(f"Failed to generate channel artifacts: {e}")
            raise
    
    def _generate_channel_config_tx(self, channel_name: str, channel_config: Dict[str, Any]) -> str:
        """Generate channel configuration transaction"""
        try:
            # This would generate actual Fabric channel configuration transaction
            # For now, return a placeholder
            config_tx = {
                "channel_id": channel_name,
                "config_update": {
                    "channel_id": channel_name,
                    "read_set": {},
                    "write_set": {
                        "groups": {
                            "Application": {
                                "groups": {}
                            },
                            "Orderer": {
                                "groups": {}
                            }
                        },
                        "values": {
                            "Channel": {
                                "mod_policy": "Admins",
                                "value": {
                                    "version": "1",
                                    "ordering": "etcdraft"
                                }
                            }
                        }
                    }
                }
            }
            
            return json.dumps(config_tx, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to generate channel config tx: {e}")
            raise
    
    def _generate_anchor_peer_update(self, channel_name: str, org: str) -> str:
        """Generate anchor peer update for organization"""
        try:
            # This would generate actual Fabric anchor peer update
            anchor_update = {
                "channel_id": channel_name,
                "config_update": {
                    "channel_id": channel_name,
                    "read_set": {},
                    "write_set": {
                        "groups": {
                            "Application": {
                                "groups": {
                                    org: {
                                        "mod_policy": "Admins",
                                        "value": {
                                            "anchor_peers": [
                                                {
                                                    "host": f"peer0.{org.lower().replace('orgmsp', '')}.example.com",
                                                    "port": 7051
                                                }
                                            ]
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            
            return json.dumps(anchor_update, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to generate anchor peer update: {e}")
            raise
    
    def _generate_genesis_block(self, channel_name: str, channel_config: Dict[str, Any]) -> str:
        """Generate genesis block for channel"""
        try:
            # This would generate actual Fabric genesis block
            genesis_block = {
                "channel_id": channel_name,
                "block_number": 0,
                "data_hash": hashlib.sha256(f"{channel_name}_genesis".encode()).hexdigest(),
                "previous_hash": "",
                "timestamp": int(time.time()),
                "transactions": [],
                "metadata": {
                    "channel_config": channel_config
                }
            }
            
            return json.dumps(genesis_block, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to generate genesis block: {e}")
            raise
    
    def update_channel(self, channel_name: str, updates: Dict[str, Any], 
                     requesting_org: str = None) -> Dict[str, Any]:
        """
        Update channel configuration
        
        Args:
            channel_name: Channel name
            updates: Configuration updates
            requesting_org: Requesting organization
        
        Returns:
            Dict containing update result
        """
        try:
            # Check if channel exists
            if channel_name not in self.channel_configs:
                return {
                    "success": False,
                    "error": f"Channel {channel_name} not found"
                }
            
            # Validate update permissions
            if not self._validate_channel_update(channel_name, requesting_org, updates):
                return {
                    "success": False,
                    "error": "Channel update validation failed"
                }
            
            # Apply updates
            current_config = self.channel_configs[channel_name]
            old_config = current_config.copy()
            
            for key, value in updates.items():
                if key in ["name", "type", "organizations", "consortium"]:
                    # These require special handling
                    continue
                current_config[key] = value
            
            current_config["updated_at"] = datetime.utcnow().isoformat()
            current_config["updated_by"] = requesting_org
            
            # Generate update transaction
            update_tx = self._generate_channel_update_tx(channel_name, old_config, current_config)
            
            # Save configuration
            self._save_channel_config()
            
            logger.info(f"Channel {channel_name} updated successfully")
            
            return {
                "success": True,
                "channel_name": channel_name,
                "update_tx": update_tx,
                "old_config": old_config,
                "new_config": current_config,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to update channel: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _validate_channel_update(self, channel_name: str, requesting_org: str, updates: Dict[str, Any]) -> bool:
        """Validate channel update permissions"""
        try:
            # Check if requesting org is channel member
            channel_config = self.channel_configs[channel_name]
            if requesting_org and requesting_org not in channel_config["organizations"]:
                logger.error(f"Organization {requesting_org} is not a channel member")
                return False
            
            # Check update policies
            update_policy = self.channel_policies.get("channel_update", {})
            required_roles = update_policy.get("required_roles", ["admin"])
            
            # In production, this would check actual user roles
            # For now, assume admin role for demonstration
            return True
            
        except Exception as e:
            logger.error(f"Channel update validation failed: {e}")
            return False
    
    def _generate_channel_update_tx(self, channel_name: str, old_config: Dict[str, Any], 
                                  new_config: Dict[str, Any]) -> str:
        """Generate channel update transaction"""
        try:
            update_tx = {
                "channel_id": channel_name,
                "config_update": {
                    "channel_id": channel_name,
                    "read_set": {
                        "groups": {},
                        "values": {}
                    },
                    "write_set": {
                        "groups": {},
                        "values": {}
                    }
                },
                "old_config": old_config,
                "new_config": new_config,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return json.dumps(update_tx, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to generate channel update tx: {e}")
            raise
    
    def delete_channel(self, channel_name: str, requesting_org: str = None, 
                     force: bool = False) -> Dict[str, Any]:
        """
        Delete a channel
        
        Args:
            channel_name: Channel name
            requesting_org: Requesting organization
            force: Force deletion without approvals
        
        Returns:
            Dict containing deletion result
        """
        try:
            # Check if channel exists
            if channel_name not in self.channel_configs:
                return {
                    "success": False,
                    "error": f"Channel {channel_name} not found"
                }
            
            # Validate deletion permissions
            if not force and not self._validate_channel_deletion(channel_name, requesting_org):
                return {
                    "success": False,
                    "error": "Channel deletion validation failed"
                }
            
            # Archive channel data before deletion
            archive_result = self._archive_channel_data(channel_name)
            
            # Remove from configuration
            channel_config = self.channel_configs.pop(channel_name)
            
            # Update registry
            self._update_channel_registry()
            
            # Save configuration
            self._save_channel_config()
            
            logger.info(f"Channel {channel_name} deleted successfully")
            
            return {
                "success": True,
                "channel_name": channel_name,
                "archived_data": archive_result,
                "deleted_config": channel_config,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to delete channel: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _validate_channel_deletion(self, channel_name: str, requesting_org: str) -> bool:
        """Validate channel deletion permissions"""
        try:
            # Check if requesting org is channel member
            channel_config = self.channel_configs[channel_name]
            if requesting_org and requesting_org not in channel_config["organizations"]:
                logger.error(f"Organization {requesting_org} is not a channel member")
                return False
            
            # Check deletion policies
            deletion_policy = self.channel_policies.get("channel_deletion", {})
            required_roles = deletion_policy.get("required_roles", ["admin"])
            min_approvals = deletion_policy.get("min_approvals", 3)
            
            # In production, this would check actual approvals
            # For now, assume admin role and sufficient approvals
            return True
            
        except Exception as e:
            logger.error(f"Channel deletion validation failed: {e}")
            return False
    
    def _archive_channel_data(self, channel_name: str) -> Dict[str, Any]:
        """Archive channel data before deletion"""
        try:
            archive_dir = f"archives/channels/{channel_name}_{int(time.time())}"
            os.makedirs(archive_dir, exist_ok=True)
            
            channel_config = self.channel_configs[channel_name]
            
            # Archive channel configuration
            with open(f"{archive_dir}/channel_config.json", 'w') as f:
                json.dump(channel_config, f, indent=2)
            
            # Archive channel artifacts
            artifacts = self._generate_channel_artifacts(channel_name, channel_config)
            with open(f"{archive_dir}/artifacts.json", 'w') as f:
                json.dump(artifacts, f, indent=2)
            
            return {
                "archive_dir": archive_dir,
                "archived_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to archive channel data: {e}")
            raise
    
    def join_channel(self, channel_name: str, organization: str) -> Dict[str, Any]:
        """
        Join an organization to a channel
        
        Args:
            channel_name: Channel name
            organization: Organization to join
        
        Returns:
            Dict containing join result
        """
        try:
            # Check if channel exists
            if channel_name not in self.channel_configs:
                return {
                    "success": False,
                    "error": f"Channel {channel_name} not found"
                }
            
            # Check if organization is already a member
            channel_config = self.channel_configs[channel_name]
            if organization in channel_config["organizations"]:
                return {
                    "success": False,
                    "error": f"Organization {organization} is already a channel member"
                }
            
            # Add organization to channel
            channel_config["organizations"].append(organization)
            channel_config["updated_at"] = datetime.utcnow().isoformat()
            
            # Generate join transaction
            join_tx = self._generate_join_tx(channel_name, organization)
            
            # Update anchor peers
            anchor_update = self._generate_anchor_peer_update(channel_name, organization)
            
            # Save configuration
            self._save_channel_config()
            
            logger.info(f"Organization {organization} joined channel {channel_name}")
            
            return {
                "success": True,
                "channel_name": channel_name,
                "organization": organization,
                "join_tx": join_tx,
                "anchor_update": anchor_update,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to join channel: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_join_tx(self, channel_name: str, organization: str) -> str:
        """Generate channel join transaction"""
        try:
            join_tx = {
                "channel_id": channel_name,
                "config_update": {
                    "channel_id": channel_name,
                    "read_set": {},
                    "write_set": {
                        "groups": {
                            "Application": {
                                "groups": {
                                    organization: {
                                        "mod_policy": "Admins",
                                        "value": {
                                            "policies": self._get_default_policies(ChannelType.CERTIFICATE_VERIFICATION),
                                            "version": "1"
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "organization": organization,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return json.dumps(join_tx, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to generate join tx: {e}")
            raise
    
    def leave_channel(self, channel_name: str, organization: str) -> Dict[str, Any]:
        """
        Remove an organization from a channel
        
        Args:
            channel_name: Channel name
            organization: Organization to remove
        
        Returns:
            Dict containing leave result
        """
        try:
            # Check if channel exists
            if channel_name not in self.channel_configs:
                return {
                    "success": False,
                    "error": f"Channel {channel_name} not found"
                }
            
            # Check if organization is a member
            channel_config = self.channel_configs[channel_name]
            if organization not in channel_config["organizations"]:
                return {
                    "success": False,
                    "error": f"Organization {organization} is not a channel member"
                }
            
            # Check minimum organization requirement
            if len(channel_config["organizations"]) <= 2:
                return {
                    "success": False,
                    "error": "Cannot leave channel - minimum organization requirement not met"
                }
            
            # Remove organization from channel
            channel_config["organizations"].remove(organization)
            channel_config["updated_at"] = datetime.utcnow().isoformat()
            
            # Generate leave transaction
            leave_tx = self._generate_leave_tx(channel_name, organization)
            
            # Save configuration
            self._save_channel_config()
            
            logger.info(f"Organization {organization} left channel {channel_name}")
            
            return {
                "success": True,
                "channel_name": channel_name,
                "organization": organization,
                "leave_tx": leave_tx,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to leave channel: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _generate_leave_tx(self, channel_name: str, organization: str) -> str:
        """Generate channel leave transaction"""
        try:
            leave_tx = {
                "channel_id": channel_name,
                "config_update": {
                    "channel_id": channel_name,
                    "read_set": {
                        "groups": {
                            "Application": {
                                "groups": {
                                    organization: {}
                                }
                            }
                        }
                    },
                    "write_set": {}
                },
                "organization": organization,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return json.dumps(leave_tx, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to generate leave tx: {e}")
            raise
    
    def enable_cross_channel_communication(self, source_channel: str, target_channel: str, 
                                        data_types: List[str], policies: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Enable cross-channel communication
        
        Args:
            source_channel: Source channel name
            target_channel: Target channel name
            data_types: Data types to share
            policies: Communication policies
        
        Returns:
            Dict containing communication setup result
        """
        try:
            # Validate channels exist
            if source_channel not in self.channel_configs:
                return {
                    "success": False,
                    "error": f"Source channel {source_channel} not found"
                }
            
            if target_channel not in self.channel_configs:
                return {
                    "success": False,
                    "error": f"Target channel {target_channel} not found"
                }
            
            # Create cross-channel bridge configuration
            bridge_config = {
                "source_channel": source_channel,
                "target_channel": target_channel,
                "data_types": data_types,
                "policies": policies or {
                    "access_control": "role_based",
                    "encryption": "required",
                    "audit_required": True,
                    "propagation_delay": "5s"
                },
                "status": "active",
                "created_at": datetime.utcnow().isoformat()
            }
            
            # Add to cross-channel policies
            bridge_id = f"bridge_{source_channel}_{target_channel}_{int(time.time())}"
            self.cross_channel_policies[bridge_id] = bridge_config
            
            # Save configuration
            self._save_channel_config()
            
            logger.info(f"Cross-channel communication enabled: {source_channel} -> {target_channel}")
            
            return {
                "success": True,
                "bridge_id": bridge_id,
                "source_channel": source_channel,
                "target_channel": target_channel,
                "data_types": data_types,
                "config": bridge_config,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to enable cross-channel communication: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_channel_list(self, status: ChannelStatus = None, channel_type: ChannelType = None) -> Dict[str, Any]:
        """
        Get list of channels with optional filtering
        
        Args:
            status: Filter by status
            channel_type: Filter by type
        
        Returns:
            Dict containing channel list
        """
        try:
            channels = []
            
            for channel_name, channel_config in self.channel_configs.items():
                # Apply filters
                if status and channel_config.get("status") != status.value:
                    continue
                
                if channel_type and channel_config.get("type") != channel_type.value:
                    continue
                
                channel_info = {
                    "name": channel_name,
                    "type": channel_config.get("type"),
                    "description": channel_config.get("description"),
                    "status": channel_config.get("status"),
                    "organizations": channel_config.get("organizations"),
                    "created_at": channel_config.get("created_at"),
                    "updated_at": channel_config.get("updated_at"),
                    "block_height": channel_config.get("block_height", 0),
                    "chaincodes": channel_config.get("chaincodes", [])
                }
                
                channels.append(channel_info)
            
            return {
                "success": True,
                "channels": channels,
                "total_count": len(channels),
                "filters": {
                    "status": status.value if status else None,
                    "type": channel_type.value if channel_type else None
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get channel list: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_channel_details(self, channel_name: str) -> Dict[str, Any]:
        """
        Get detailed channel information
        
        Args:
            channel_name: Channel name
        
        Returns:
            Dict containing channel details
        """
        try:
            if channel_name not in self.channel_configs:
                return {
                    "success": False,
                    "error": f"Channel {channel_name} not found"
                }
            
            channel_config = self.channel_configs[channel_name]
            
            # Get channel statistics
            stats = self._get_channel_statistics(channel_name)
            
            # Get cross-channel bridges
            bridges = []
            for bridge_id, bridge_config in self.cross_channel_policies.items():
                if bridge_config["source_channel"] == channel_name or bridge_config["target_channel"] == channel_name:
                    bridges.append({
                        "bridge_id": bridge_id,
                        "source_channel": bridge_config["source_channel"],
                        "target_channel": bridge_config["target_channel"],
                        "data_types": bridge_config["data_types"],
                        "status": bridge_config["status"]
                    })
            
            return {
                "success": True,
                "channel": channel_config,
                "statistics": stats,
                "cross_channel_bridges": bridges,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get channel details: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_channel_statistics(self, channel_name: str) -> Dict[str, Any]:
        """Get channel statistics"""
        try:
            # This would query actual channel statistics
            # For now, return placeholder statistics
            return {
                "block_height": 0,
                "transaction_count": 0,
                "active_chaincodes": 0,
                "peer_count": 4,
                "last_block_time": None,
                "channel_size": "0 MB",
                "transaction_rate": "0 tx/s"
            }
            
        except Exception as e:
            logger.error(f"Failed to get channel statistics: {e}")
            return {}
    
    def _update_channel_registry(self):
        """Update channel registry"""
        try:
            self.channel_registry["total_channels"] = len(self.channel_configs)
            self.channel_registry["active_channels"] = 0
            self.channel_registry["inactive_channels"] = 0
            self.channel_registry["channel_types"] = {}
            self.channel_registry["organizations"] = set()
            self.channel_registry["last_updated"] = datetime.utcnow().isoformat()
            
            for channel_name, channel_config in self.channel_configs.items():
                status = channel_config.get("status", "inactive")
                channel_type = channel_config.get("type", "unknown")
                organizations = channel_config.get("organizations", [])
                
                if status == "active":
                    self.channel_registry["active_channels"] += 1
                else:
                    self.channel_registry["inactive_channels"] += 1
                
                if channel_type not in self.channel_registry["channel_types"]:
                    self.channel_registry["channel_types"][channel_type] = 0
                self.channel_registry["channel_types"][channel_type] += 1
                
                self.channel_registry["organizations"].update(organizations)
            
        except Exception as e:
            logger.error(f"Failed to update channel registry: {e}")
    
    def _save_channel_config(self):
        """Save channel configuration to file"""
        try:
            config = {
                "channels": self.channel_configs,
                "policies": self.channel_policies,
                "cross_channel_policies": self.cross_channel_policies
            }
            
            config_path = "config/channel_config.json"
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save channel config: {e}")
            raise

# Global channel manager instance
channel_manager = ChannelManager()

# Convenience functions
def create_fabric_channel(channel_name: str, channel_type: str, organizations: List[str], 
                         description: str = "", creator_org: str = None) -> Dict[str, Any]:
    """Create a new Fabric channel"""
    return channel_manager.create_channel(channel_name, ChannelType(channel_type), organizations, description, creator_org)

def update_fabric_channel(channel_name: str, updates: Dict[str, Any], requesting_org: str = None) -> Dict[str, Any]:
    """Update Fabric channel configuration"""
    return channel_manager.update_channel(channel_name, updates, requesting_org)

def get_fabric_channels(status: str = None, channel_type: str = None) -> Dict[str, Any]:
    """Get list of Fabric channels"""
    status_enum = ChannelStatus(status) if status else None
    type_enum = ChannelType(channel_type) if channel_type else None
    return channel_manager.get_channel_list(status_enum, type_enum)
