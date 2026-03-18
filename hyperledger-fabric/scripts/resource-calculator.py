#!/usr/bin/env python3
"""
Resource Calculator for Hyperledger Fabric Deployment

This module calculates system resources and recommends optimal deployment
configurations based on available hardware resources.
"""

import os
import psutil
import json
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class SystemResources:
    """System resource information"""
    cpu_cores: int
    total_memory_gb: float
    available_memory_gb: float
    total_disk_gb: float
    available_disk_gb: float
    cpu_usage_percent: float
    memory_usage_percent: float

@dataclass
class DeploymentProfile:
    """Deployment configuration profile"""
    name: str
    description: str
    min_cpu_cores: int
    min_memory_gb: float
    min_disk_gb: float
    organizations: List[str]
    orderers: int
    peers_per_org: int
    cas: int
    couchdb_instances: int
    monitoring: bool
    estimated_memory_gb: float
    estimated_cpu_cores: int
    resource_level: str  # minimal, standard, full

class ResourceCalculator:
    """Calculate system resources and recommend deployment configurations"""
    
    def __init__(self):
        self.profiles = self._create_deployment_profiles()
    
    def get_system_resources(self) -> SystemResources:
        """Get current system resource information"""
        try:
            # CPU information
            cpu_cores = psutil.cpu_count(logical=False)  # Physical cores
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Memory information
            memory = psutil.virtual_memory()
            total_memory_gb = memory.total / (1024**3)
            available_memory_gb = memory.available / (1024**3)
            memory_usage = memory.percent
            
            # Disk information
            disk = psutil.disk_usage('/')
            total_disk_gb = disk.total / (1024**3)
            available_disk_gb = disk.free / (1024**3)
            
            return SystemResources(
                cpu_cores=cpu_cores,
                total_memory_gb=total_memory_gb,
                available_memory_gb=available_memory_gb,
                total_disk_gb=total_disk_gb,
                available_disk_gb=available_disk_gb,
                cpu_usage_percent=cpu_usage,
                memory_usage_percent=memory_usage
            )
            
        except Exception as e:
            logger.error(f"Failed to get system resources: {e}")
            raise
    
    def _create_deployment_profiles(self) -> List[DeploymentProfile]:
        """Create predefined deployment profiles"""
        return [
            # Minimal deployment - for testing on limited resources
            DeploymentProfile(
                name="minimal",
                description="Minimal deployment for testing (1 organization)",
                min_cpu_cores=2,
                min_memory_gb=4,
                min_disk_gb=10,
                organizations=["EcolOrgMSP"],
                orderers=1,
                peers_per_org=1,
                cas=2,  # 1 orderer CA + 1 org CA
                couchdb_instances=1,
                monitoring=False,
                estimated_memory_gb=2.5,
                estimated_cpu_cores=2,
                resource_level="minimal"
            ),
            
            # Standard deployment - for development
            DeploymentProfile(
                name="standard",
                description="Standard deployment for development (2 organizations)",
                min_cpu_cores=4,
                min_memory_gb=8,
                min_disk_gb=20,
                organizations=["EcolOrgMSP", "LimkokwingOrgMSP"],
                orderers=1,
                peers_per_org=1,
                cas=3,  # 1 orderer CA + 2 org CAs
                couchdb_instances=2,
                monitoring=True,
                estimated_memory_gb=5.0,
                estimated_cpu_cores=3,
                resource_level="standard"
            ),
            
            # Full deployment - for production
            DeploymentProfile(
                name="full",
                description="Full enterprise deployment (4 organizations)",
                min_cpu_cores=8,
                min_memory_gb=16,
                min_disk_gb=50,
                organizations=["EcolOrgMSP", "LimkokwingOrgMSP", "BothoOrgMSP", "NulOrgMSP"],
                orderers=3,
                peers_per_org=1,
                cas=5,  # 1 orderer CA + 4 org CAs
                couchdb_instances=4,
                monitoring=True,
                estimated_memory_gb=12.0,
                estimated_cpu_cores=6,
                resource_level="full"
            ),
            
            # High-performance deployment
            DeploymentProfile(
                name="high-performance",
                description="High-performance deployment with multiple peers per org",
                min_cpu_cores=12,
                min_memory_gb=24,
                min_disk_gb=80,
                organizations=["EcolOrgMSP", "LimkokwingOrgMSP", "BothoOrgMSP", "NulOrgMSP"],
                orderers=3,
                peers_per_org=2,
                cas=5,
                couchdb_instances=8,
                monitoring=True,
                estimated_memory_gb=20.0,
                estimated_cpu_cores=10,
                resource_level="full"
            ),
            
            # Custom deployment
            DeploymentProfile(
                name="custom",
                description="Custom deployment configuration",
                min_cpu_cores=2,
                min_memory_gb=4,
                min_disk_gb=10,
                organizations=["EcolOrgMSP"],
                orderers=1,
                peers_per_org=1,
                cas=2,
                couchdb_instances=1,
                monitoring=False,
                estimated_memory_gb=2.5,
                estimated_cpu_cores=2,
                resource_level="custom"
            )
        ]
    
    def get_available_profiles(self, resources: SystemResources) -> List[DeploymentProfile]:
        """Get deployment profiles that fit available resources"""
        available_profiles = []
        
        for profile in self.profiles:
            if (resources.cpu_cores >= profile.min_cpu_cores and
                resources.available_memory_gb >= profile.min_memory_gb and
                resources.available_disk_gb >= profile.min_disk_gb):
                available_profiles.append(profile)
        
        return available_profiles
    
    def calculate_resource_usage(self, profile: DeploymentProfile, num_orgs: int = None) -> Dict[str, float]:
        """Calculate detailed resource usage for a profile"""
        if num_orgs is None:
            num_orgs = len(profile.organizations)
        
        # Calculate resource requirements
        total_peers = num_orgs * profile.peers_per_org
        total_cas = 1 + num_orgs  # 1 orderer CA + org CAs
        total_couchdb = num_orgs * profile.peers_per_org
        
        # Memory calculations (approximate)
        peer_memory = 0.8 * total_peers  # ~800MB per peer
        orderer_memory = 0.5 * profile.orderers  # ~500MB per orderer
        ca_memory = 0.3 * total_cas  # ~300MB per CA
        couchdb_memory = 0.4 * total_couchdb  # ~400MB per CouchDB
        monitoring_memory = 1.5 if profile.monitoring else 0  # ~1.5GB for monitoring stack
        
        total_memory = peer_memory + orderer_memory + ca_memory + couchdb_memory + monitoring_memory
        
        # CPU calculations (approximate)
        peer_cpu = 0.5 * total_peers  # ~0.5 cores per peer
        orderer_cpu = 0.3 * profile.orderers  # ~0.3 cores per orderer
        ca_cpu = 0.2 * total_cas  # ~0.2 cores per CA
        couchdb_cpu = 0.3 * total_couchdb  # ~0.3 cores per CouchDB
        monitoring_cpu = 1.0 if profile.monitoring else 0  # ~1 core for monitoring
        
        total_cpu = peer_cpu + orderer_cpu + ca_cpu + couchdb_cpu + monitoring_cpu
        
        # Disk calculations (approximate)
        peer_disk = 2.0 * total_peers  # ~2GB per peer
        orderer_disk = 1.0 * profile.orderers  # ~1GB per orderer
        ca_disk = 0.5 * total_cas  # ~500MB per CA
        couchdb_disk = 1.0 * total_couchdb  # ~1GB per CouchDB
        logs_disk = 2.0  # ~2GB for logs
        
        total_disk = peer_disk + orderer_disk + ca_disk + couchdb_disk + logs_disk
        
        return {
            "memory_gb": total_memory,
            "cpu_cores": total_cpu,
            "disk_gb": total_disk,
            "total_peers": total_peers,
            "total_cas": total_cas,
            "total_couchdb": total_couchdb
        }
    
    def get_resource_recommendation(self, resources: SystemResources) -> Dict[str, any]:
        """Get resource-based deployment recommendation"""
        available_profiles = self.get_available_profiles(resources)
        
        if not available_profiles:
            return {
                "can_deploy": False,
                "message": "Insufficient resources for any deployment profile",
                "recommendation": "Upgrade your system resources (minimum: 2 CPU cores, 4GB RAM, 10GB disk)",
                "available_resources": {
                    "cpu_cores": resources.cpu_cores,
                    "memory_gb": f"{resources.available_memory_gb:.1f}",
                    "disk_gb": f"{resources.available_disk_gb:.1f}"
                }
            }
        
        # Find the best profile (highest resource level that fits)
        best_profile = None
        best_score = 0
        
        for profile in available_profiles:
            # Score based on resource utilization
            cpu_utilization = profile.estimated_cpu_cores / resources.cpu_cores
            memory_utilization = profile.estimated_memory_gb / resources.available_memory_gb
            
            # Prefer higher resource utilization but not too high (>80%)
            if cpu_utilization <= 0.8 and memory_utilization <= 0.8:
                score = cpu_utilization + memory_utilization
                if score > best_score:
                    best_score = score
                    best_profile = profile
        
        if not best_profile:
            # Fallback to minimal profile if available
            best_profile = min(available_profiles, key=lambda p: p.estimated_memory_gb)
        
        resource_usage = self.calculate_resource_usage(best_profile)
        
        return {
            "can_deploy": True,
            "recommended_profile": best_profile.name,
            "recommended_profile_info": {
                "name": best_profile.name,
                "description": best_profile.description,
                "organizations": best_profile.organizations,
                "resource_level": best_profile.resource_level
            },
            "resource_usage": resource_usage,
            "resource_utilization": {
                "cpu_percent": (resource_usage["cpu_cores"] / resources.cpu_cores) * 100,
                "memory_percent": (resource_usage["memory_gb"] / resources.available_memory_gb) * 100,
                "disk_percent": (resource_usage["disk_gb"] / resources.available_disk_gb) * 100
            },
            "available_alternatives": [
                {
                    "name": p.name,
                    "description": p.description,
                    "estimated_memory": p.estimated_memory_gb,
                    "estimated_cpu": p.estimated_cpu_cores
                }
                for p in available_profiles
            ],
            "system_resources": {
                "cpu_cores": resources.cpu_cores,
                "memory_gb": f"{resources.total_memory_gb:.1f}",
                "disk_gb": f"{resources.total_disk_gb:.1f}",
                "cpu_usage": f"{resources.cpu_usage_percent:.1f}%",
                "memory_usage": f"{resources.memory_usage_percent:.1f}%"
            }
        }
    
    def create_custom_profile(self, name: str, organizations: List[str], peers_per_org: int = 1,
                            orderers: int = 1, monitoring: bool = True) -> DeploymentProfile:
        """Create a custom deployment profile"""
        num_orgs = len(organizations)
        
        # Calculate resource requirements
        total_peers = num_orgs * peers_per_org
        total_cas = 1 + num_orgs
        total_couchdb = total_peers
        
        # Estimate resource requirements
        estimated_memory = (0.8 * total_peers) + (0.5 * orderers) + (0.3 * total_cas) + (0.4 * total_couchdb) + (1.5 if monitoring else 0)
        estimated_cpu = (0.5 * total_peers) + (0.3 * orderers) + (0.2 * total_cas) + (0.3 * total_couchdb) + (1.0 if monitoring else 0)
        
        return DeploymentProfile(
            name=name,
            description=f"Custom deployment with {num_orgs} organizations, {peers_per_org} peers per org",
            min_cpu_cores=max(2, int(estimated_cpu)),
            min_memory_gb=max(4, estimated_memory + 2),  # Add buffer
            min_disk_gb=max(10, total_peers * 3),  # ~3GB per peer
            organizations=organizations,
            orderers=orderers,
            peers_per_org=peers_per_org,
            cas=total_cas,
            couchdb_instances=total_couchdb,
            monitoring=monitoring,
            estimated_memory_gb=estimated_memory,
            estimated_cpu_cores=estimated_cpu,
            resource_level="custom"
        )

def main():
    """Main function for testing"""
    calculator = ResourceCalculator()
    
    # Get system resources
    resources = calculator.get_system_resources()
    print("System Resources:")
    print(f"  CPU Cores: {resources.cpu_cores}")
    print(f"  Memory: {resources.total_memory_gb:.1f}GB total, {resources.available_memory_gb:.1f}GB available")
    print(f"  Disk: {resources.total_disk_gb:.1f}GB total, {resources.available_disk_gb:.1f}GB available")
    print(f"  CPU Usage: {resources.cpu_usage_percent:.1f}%")
    print(f"  Memory Usage: {resources.memory_usage_percent:.1f}%")
    
    # Get recommendation
    recommendation = calculator.get_resource_recommendation(resources)
    print(f"\nRecommendation: {recommendation['recommended_profile']}")
    print(f"Description: {recommendation['recommended_profile_info']['description']}")
    print(f"Resource Usage: {recommendation['resource_usage']}")

if __name__ == "__main__":
    main()
