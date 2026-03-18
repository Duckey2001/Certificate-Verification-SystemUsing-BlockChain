from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid
import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from auth import get_current_user, require_admin, require_role
from database import get_db
from models import (
    Institution, BlockchainNode, ChaincodeDeployment, 
    NodeActivityLog, User
)

router = APIRouter(prefix="/api/blockchain-nodes", tags=["blockchain-nodes"])

# Pydantic models for request/response
class BlockchainNodeBase(BaseModel):
    node_id: str = Field(..., min_length=3, max_length=100, description="Unique node identifier")
    node_type: str = Field(..., description="Node type: peer, orderer, ca, validator")
    network_type: str = Field(..., description="Network type: fabric, ethereum, hyperledger, corda")
    url: str = Field(..., description="Node URL")
    port: int = Field(..., gt=0, le=65535, description="Node port")
    tls_enabled: bool = Field(True, description="TLS enabled")
    msp_id: Optional[str] = Field(None, description="Membership Service Provider ID")
    peer_id: Optional[str] = Field(None, description="Peer ID")
    orderer_id: Optional[str] = Field(None, description="Orderer ID")
    channel_name: Optional[str] = Field(None, description="Channel name")
    chaincode_name: Optional[str] = Field(None, description="Chaincode name")
    chaincode_version: Optional[str] = Field(None, description="Chaincode version")
    node_config: Optional[Dict[str, Any]] = Field(None, description="Additional node configuration")

    @validator('node_type')
    def validate_node_type(cls, v):
        if v not in ("peer", "orderer", "ca", "validator"):
            raise ValueError('Node type must be one of: peer, orderer, ca, validator')
        return v

    @validator('network_type')
    def validate_network_type(cls, v):
        if v not in ("fabric", "ethereum", "hyperledger", "corda"):
            raise ValueError('Network type must be one of: fabric, ethereum, hyperledger, corda')
        return v

class BlockchainNodeCreate(BlockchainNodeBase):
    institution_id: int = Field(..., description="Institution ID")
    chaincode_path: Optional[str] = Field(None, description="Chaincode path")
    tls_cert_path: Optional[str] = Field(None, description="TLS certificate path")
    tls_key_path: Optional[str] = Field(None, description="TLS key path")
    ca_cert_path: Optional[str] = Field(None, description="CA certificate path")

class BlockchainNodeUpdate(BaseModel):
    node_id: Optional[str] = None
    node_type: Optional[str] = None
    network_type: Optional[str] = None
    url: Optional[str] = None
    port: Optional[int] = None
    tls_enabled: Optional[bool] = None
    msp_id: Optional[str] = None
    peer_id: Optional[str] = None
    orderer_id: Optional[str] = None
    channel_name: Optional[str] = None
    chaincode_name: Optional[str] = None
    chaincode_version: Optional[str] = None
    chaincode_path: Optional[str] = None
    tls_cert_path: Optional[str] = None
    tls_key_path: Optional[str] = None
    ca_cert_path: Optional[str] = None
    node_config: Optional[Dict[str, Any]] = None
    status: Optional[str] = None

    @validator('node_type')
    def validate_node_type(cls, v):
        if v is not None and v not in ("peer", "orderer", "ca", "validator"):
            raise ValueError('Node type must be one of: peer, orderer, ca, validator')
        return v

    @validator('network_type')
    def validate_network_type(cls, v):
        if v is not None and v not in ("fabric", "ethereum", "hyperledger", "corda"):
            raise ValueError('Network type must be one of: fabric, ethereum, hyperledger, corda')
        return v

    @validator('status')
    def validate_status(cls, v):
        if v is not None and v not in ("inactive", "active", "syncing", "error", "maintenance"):
            raise ValueError('Status must be one of: inactive, active, syncing, error, maintenance')
        return v

class BlockchainNodeResponse(BaseModel):
    id: int
    node_id: str
    institution_id: int
    institution_code: str
    institution_name: str
    node_type: str
    network_type: str
    url: str
    port: int
    tls_enabled: bool
    msp_id: Optional[str]
    peer_id: Optional[str]
    orderer_id: Optional[str]
    channel_name: Optional[str]
    chaincode_name: Optional[str]
    chaincode_version: Optional[str]
    chaincode_installed: bool
    chaincode_instantiated: bool
    status: str
    last_heartbeat: Optional[datetime]
    last_sync_at: Optional[datetime]
    block_height: int
    network_height: int
    node_config: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    installed_at: Optional[datetime]

class ChaincodeDeploymentBase(BaseModel):
    chaincode_name: str = Field(..., min_length=2, max_length=100)
    chaincode_version: str = Field(..., min_length=1, max_length=20)
    chaincode_path: str = Field(..., min_length=1, max_length=500)
    chaincode_language: str = Field("go", description="Chaincode language: go, java, node")
    channel_name: Optional[str] = Field(None, description="Channel name")
    init_required: bool = Field(True, description="Initialization required")
    init_args: Optional[List[str]] = Field(None, description="Initialization arguments")
    endorsement_policy: Optional[Dict[str, Any]] = Field(None, description="Endorsement policy")
    collection_config: Optional[Dict[str, Any]] = Field(None, description="Private data collections")

    @validator('chaincode_language')
    def validate_chaincode_language(cls, v):
        if v not in ("go", "java", "node"):
            raise ValueError('Chaincode language must be one of: go, java, node')
        return v

class ChaincodeDeploymentCreate(ChaincodeDeploymentBase):
    node_id: int = Field(..., description="Node ID")
    institution_id: int = Field(..., description="Institution ID")

class ChaincodeDeploymentResponse(BaseModel):
    id: int
    deployment_id: str
    node_id: int
    institution_id: int
    chaincode_name: str
    chaincode_version: str
    chaincode_path: str
    chaincode_language: str
    channel_name: Optional[str]
    init_required: bool
    init_args: Optional[List[str]]
    endorsement_policy: Optional[Dict[str, Any]]
    collection_config: Optional[Dict[str, Any]]
    status: str
    install_tx_id: Optional[str]
    instantiate_tx_id: Optional[str]
    package_id: Optional[str]
    error_message: Optional[str]
    retry_count: int
    max_retries: int
    created_at: datetime
    updated_at: datetime
    installed_at: Optional[datetime]
    instantiated_at: Optional[datetime]

class NodeActivityLogResponse(BaseModel):
    id: int
    node_id: int
    institution_id: int
    activity_type: str
    activity_message: str
    activity_data: Optional[Dict[str, Any]]
    status_before: Optional[str]
    status_after: Optional[str]
    block_height_before: Optional[int]
    block_height_after: Optional[int]
    error_code: Optional[str]
    error_message: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    triggered_by: Optional[int]
    created_at: datetime

# Blockchain Node endpoints
@router.get("", response_model=List[BlockchainNodeResponse])
def list_blockchain_nodes(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    institution_id: Optional[int] = Query(None, description="Filter by institution ID"),
    node_type: Optional[str] = Query(None, description="Filter by node type"),
    network_type: Optional[str] = Query(None, description="Filter by network type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page")
):
    """List all blockchain nodes with filtering and pagination"""
    
    query = db.query(BlockchainNode).join(Institution)
    
    if institution_id:
        query = query.filter(BlockchainNode.institution_id == institution_id)
    
    if node_type:
        query = query.filter(BlockchainNode.node_type == node_type)
    
    if network_type:
        query = query.filter(BlockchainNode.network_type == network_type)
    
    if status:
        query = query.filter(BlockchainNode.status == status)
    
    offset = (page - 1) * limit
    nodes = query.order_by(BlockchainNode.created_at.desc()).offset(offset).limit(limit).all()
    
    result = []
    for node in nodes:
        result.append({
            "id": node.id,
            "node_id": node.node_id,
            "institution_id": node.institution_id,
            "institution_code": node.institution.code,
            "institution_name": node.institution.name,
            "node_type": node.node_type,
            "network_type": node.network_type,
            "url": node.url,
            "port": node.port,
            "tls_enabled": node.tls_enabled,
            "msp_id": node.msp_id,
            "peer_id": node.peer_id,
            "orderer_id": node.orderer_id,
            "channel_name": node.channel_name,
            "chaincode_name": node.chaincode_name,
            "chaincode_version": node.chaincode_version,
            "chaincode_installed": node.chaincode_installed,
            "chaincode_instantiated": node.chaincode_instantiated,
            "status": node.status,
            "last_heartbeat": node.last_heartbeat,
            "last_sync_at": node.last_sync_at,
            "block_height": node.block_height,
            "network_height": node.network_height,
            "node_config": node.node_config,
            "created_at": node.created_at,
            "updated_at": node.updated_at,
            "installed_at": node.installed_at
        })
    
    return result

@router.post("", response_model=BlockchainNodeResponse)
def create_blockchain_node(
    payload: BlockchainNodeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create a new blockchain node"""
    
    # Check if institution exists
    institution = db.query(Institution).filter(Institution.id == payload.institution_id).first()
    if not institution:
        raise HTTPException(status_code=404, detail="Institution not found")
    
    # Check if node ID already exists
    existing = db.query(BlockchainNode).filter(BlockchainNode.node_id == payload.node_id).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Node with ID '{payload.node_id}' already exists")
    
    # Create new node
    node = BlockchainNode(
        node_id=payload.node_id,
        institution_id=payload.institution_id,
        node_type=payload.node_type,
        network_type=payload.network_type,
        url=payload.url,
        port=payload.port,
        tls_enabled=payload.tls_enabled,
        msp_id=payload.msp_id,
        peer_id=payload.peer_id,
        orderer_id=payload.orderer_id,
        channel_name=payload.channel_name,
        chaincode_name=payload.chaincode_name,
        chaincode_version=payload.chaincode_version,
        chaincode_path=payload.chaincode_path,
        tls_cert_path=payload.tls_cert_path,
        tls_key_path=payload.tls_key_path,
        ca_cert_path=payload.ca_cert_path,
        node_config=payload.node_config,
        status="inactive",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(node)
    db.commit()
    db.refresh(node)
    
    # Log activity
    log_activity(db, node.id, node.institution_id, "create", 
                f"Blockchain node {node.node_id} created", 
                {"node_type": node.node_type, "network_type": node.network_type},
                triggered_by=current_user.id)
    
    return {
        "id": node.id,
        "node_id": node.node_id,
        "institution_id": node.institution_id,
        "institution_code": institution.code,
        "institution_name": institution.name,
        "node_type": node.node_type,
        "network_type": node.network_type,
        "url": node.url,
        "port": node.port,
        "tls_enabled": node.tls_enabled,
        "msp_id": node.msp_id,
        "peer_id": node.peer_id,
        "orderer_id": node.orderer_id,
        "channel_name": node.channel_name,
        "chaincode_name": node.chaincode_name,
        "chaincode_version": node.chaincode_version,
        "chaincode_installed": node.chaincode_installed,
        "chaincode_instantiated": node.chaincode_instantiated,
        "status": node.status,
        "last_heartbeat": node.last_heartbeat,
        "last_sync_at": node.last_sync_at,
        "block_height": node.block_height,
        "network_height": node.network_height,
        "node_config": node.node_config,
        "created_at": node.created_at,
        "updated_at": node.updated_at,
        "installed_at": node.installed_at
    }

@router.get("/{node_id}", response_model=BlockchainNodeResponse)
def get_blockchain_node(
    node_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Get blockchain node by ID"""
    
    node = db.query(BlockchainNode).filter(BlockchainNode.node_id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Blockchain node not found")
    
    return {
        "id": node.id,
        "node_id": node.node_id,
        "institution_id": node.institution_id,
        "institution_code": node.institution.code,
        "institution_name": node.institution.name,
        "node_type": node.node_type,
        "network_type": node.network_type,
        "url": node.url,
        "port": node.port,
        "tls_enabled": node.tls_enabled,
        "msp_id": node.msp_id,
        "peer_id": node.peer_id,
        "orderer_id": node.orderer_id,
        "channel_name": node.channel_name,
        "chaincode_name": node.chaincode_name,
        "chaincode_version": node.chaincode_version,
        "chaincode_installed": node.chaincode_installed,
        "chaincode_instantiated": node.chaincode_instantiated,
        "status": node.status,
        "last_heartbeat": node.last_heartbeat,
        "last_sync_at": node.last_sync_at,
        "block_height": node.block_height,
        "network_height": node.network_height,
        "node_config": node.node_config,
        "created_at": node.created_at,
        "updated_at": node.updated_at,
        "installed_at": node.installed_at
    }

@router.put("/{node_id}", response_model=BlockchainNodeResponse)
def update_blockchain_node(
    node_id: str,
    payload: BlockchainNodeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Update blockchain node"""
    
    node = db.query(BlockchainNode).filter(BlockchainNode.node_id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Blockchain node not found")
    
    # Store old status for activity log
    old_status = node.status
    
    # Update fields
    update_data = payload.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(node, field):
            setattr(node, field, value)
    
    node.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(node)
    
    # Log activity if status changed
    if 'status' in update_data and old_status != node.status:
        log_activity(db, node.id, node.institution_id, "status_change",
                    f"Node status changed from {old_status} to {node.status}",
                    {"old_status": old_status, "new_status": node.status},
                    status_before=old_status, status_after=node.status,
                    triggered_by=current_user.id)
    
    return {
        "id": node.id,
        "node_id": node.node_id,
        "institution_id": node.institution_id,
        "institution_code": node.institution.code,
        "institution_name": node.institution.name,
        "node_type": node.node_type,
        "network_type": node.network_type,
        "url": node.url,
        "port": node.port,
        "tls_enabled": node.tls_enabled,
        "msp_id": node.msp_id,
        "peer_id": node.peer_id,
        "orderer_id": node.orderer_id,
        "channel_name": node.channel_name,
        "chaincode_name": node.chaincode_name,
        "chaincode_version": node.chaincode_version,
        "chaincode_installed": node.chaincode_installed,
        "chaincode_instantiated": node.chaincode_instantiated,
        "status": node.status,
        "last_heartbeat": node.last_heartbeat,
        "last_sync_at": node.last_sync_at,
        "block_height": node.block_height,
        "network_height": node.network_height,
        "node_config": node.node_config,
        "created_at": node.created_at,
        "updated_at": node.updated_at,
        "installed_at": node.installed_at
    }

@router.delete("/{node_id}")
def delete_blockchain_node(
    node_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Delete blockchain node"""
    
    node = db.query(BlockchainNode).filter(BlockchainNode.node_id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Blockchain node not found")
    
    # Log activity before deletion
    log_activity(db, node.id, node.institution_id, "delete",
                f"Blockchain node {node.node_id} deleted",
                {"node_type": node.node_type, "network_type": node.network_type},
                triggered_by=current_user.id)
    
    db.delete(node)
    db.commit()
    
    return {"message": f"Blockchain node {node_id} deleted successfully"}

# Chaincode Deployment endpoints
@router.get("/{node_id}/deployments", response_model=List[ChaincodeDeploymentResponse])
def list_chaincode_deployments(
    node_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """List chaincode deployments for a node"""
    
    node = db.query(BlockchainNode).filter(BlockchainNode.node_id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Blockchain node not found")
    
    query = db.query(ChaincodeDeployment).filter(ChaincodeDeployment.node_id == node.id)
    
    if status:
        query = query.filter(ChaincodeDeployment.status == status)
    
    offset = (page - 1) * limit
    deployments = query.order_by(ChaincodeDeployment.created_at.desc()).offset(offset).limit(limit).all()
    
    return [
        {
            "id": d.id,
            "deployment_id": d.deployment_id,
            "node_id": d.node_id,
            "institution_id": d.institution_id,
            "chaincode_name": d.chaincode_name,
            "chaincode_version": d.chaincode_version,
            "chaincode_path": d.chaincode_path,
            "chaincode_language": d.chaincode_language,
            "channel_name": d.channel_name,
            "init_required": d.init_required,
            "init_args": d.init_args,
            "endorsement_policy": d.endorsement_policy,
            "collection_config": d.collection_config,
            "status": d.status,
            "install_tx_id": d.install_tx_id,
            "instantiate_tx_id": d.instantiate_tx_id,
            "package_id": d.package_id,
            "error_message": d.error_message,
            "retry_count": d.retry_count,
            "max_retries": d.max_retries,
            "created_at": d.created_at,
            "updated_at": d.updated_at,
            "installed_at": d.installed_at,
            "instantiated_at": d.instantiated_at
        }
        for d in deployments
    ]

@router.post("/{node_id}/deployments", response_model=ChaincodeDeploymentResponse)
def create_chaincode_deployment(
    node_id: str,
    payload: ChaincodeDeploymentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """Create and deploy chaincode to a node"""
    
    node = db.query(BlockchainNode).filter(BlockchainNode.node_id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Blockchain node not found")
    
    # Generate deployment ID
    deployment_id = f"DEPLOY_{node_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    
    # Create deployment record
    deployment = ChaincodeDeployment(
        deployment_id=deployment_id,
        node_id=node.id,
        institution_id=payload.institution_id,
        chaincode_name=payload.chaincode_name,
        chaincode_version=payload.chaincode_version,
        chaincode_path=payload.chaincode_path,
        chaincode_language=payload.chaincode_language,
        channel_name=payload.channel_name,
        init_required=payload.init_required,
        init_args=payload.init_args,
        endorsement_policy=payload.endorsement_policy,
        collection_config=payload.collection_config,
        status="pending",
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(deployment)
    db.commit()
    db.refresh(deployment)
    
    # Start background deployment task
    background_tasks.add_task(deploy_chaincode_background, deployment.id, db)
    
    # Log activity
    log_activity(db, node.id, node.institution_id, "deploy",
                f"Chaincode deployment {deployment_id} initiated",
                {"chaincode_name": payload.chaincode_name, "chaincode_version": payload.chaincode_version},
                triggered_by=current_user.id)
    
    return {
        "id": deployment.id,
        "deployment_id": deployment.deployment_id,
        "node_id": deployment.node_id,
        "institution_id": deployment.institution_id,
        "chaincode_name": deployment.chaincode_name,
        "chaincode_version": deployment.chaincode_version,
        "chaincode_path": deployment.chaincode_path,
        "chaincode_language": deployment.chaincode_language,
        "channel_name": deployment.channel_name,
        "init_required": deployment.init_required,
        "init_args": deployment.init_args,
        "endorsement_policy": deployment.endorsement_policy,
        "collection_config": deployment.collection_config,
        "status": deployment.status,
        "install_tx_id": deployment.install_tx_id,
        "instantiate_tx_id": deployment.instantiate_tx_id,
        "package_id": deployment.package_id,
        "error_message": deployment.error_message,
        "retry_count": deployment.retry_count,
        "max_retries": deployment.max_retries,
        "created_at": deployment.created_at,
        "updated_at": deployment.updated_at,
        "installed_at": deployment.installed_at,
        "instantiated_at": deployment.instantiated_at
    }

# Node status and activity endpoints
@router.get("/{node_id}/status")
def get_node_status(
    node_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed node status including recent activity"""
    
    node = db.query(BlockchainNode).filter(BlockchainNode.node_id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Blockchain node not found")
    
    # Get recent activity
    recent_activity = db.query(NodeActivityLog).filter(
        NodeActivityLog.node_id == node.id
    ).order_by(NodeActivityLog.created_at.desc()).limit(10).all()
    
    # Get deployment status
    latest_deployment = db.query(ChaincodeDeployment).filter(
        ChaincodeDeployment.node_id == node.id
    ).order_by(ChaincodeDeployment.created_at.desc()).first()
    
    return {
        "node": {
            "id": node.id,
            "node_id": node.node_id,
            "status": node.status,
            "block_height": node.block_height,
            "network_height": node.network_height,
            "last_heartbeat": node.last_heartbeat,
            "last_sync_at": node.last_sync_at,
            "chaincode_installed": node.chaincode_installed,
            "chaincode_instantiated": node.chaincode_instantiated
        },
        "latest_deployment": {
            "deployment_id": latest_deployment.deployment_id,
            "chaincode_name": latest_deployment.chaincode_name,
            "chaincode_version": latest_deployment.chaincode_version,
            "status": latest_deployment.status,
            "created_at": latest_deployment.created_at
        } if latest_deployment else None,
        "recent_activity": [
            {
                "activity_type": activity.activity_type,
                "activity_message": activity.activity_message,
                "status_before": activity.status_before,
                "status_after": activity.status_after,
                "created_at": activity.created_at
            }
            for activity in recent_activity
        ]
    }

@router.get("/{node_id}/activity", response_model=List[NodeActivityLogResponse])
def get_node_activity(
    node_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
    activity_type: Optional[str] = Query(None, description="Filter by activity type"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """Get activity log for a node"""
    
    node = db.query(BlockchainNode).filter(BlockchainNode.node_id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Blockchain node not found")
    
    query = db.query(NodeActivityLog).filter(NodeActivityLog.node_id == node.id)
    
    if activity_type:
        query = query.filter(NodeActivityLog.activity_type == activity_type)
    
    offset = (page - 1) * limit
    activities = query.order_by(NodeActivityLog.created_at.desc()).offset(offset).limit(limit).all()
    
    return [
        {
            "id": a.id,
            "node_id": a.node_id,
            "institution_id": a.institution_id,
            "activity_type": a.activity_type,
            "activity_message": a.activity_message,
            "activity_data": a.activity_data,
            "status_before": a.status_before,
            "status_after": a.status_after,
            "block_height_before": a.block_height_before,
            "block_height_after": a.block_height_after,
            "error_code": a.error_code,
            "error_message": a.error_message,
            "ip_address": a.ip_address,
            "user_agent": a.user_agent,
            "triggered_by": a.triggered_by,
            "created_at": a.created_at
        }
        for a in activities
    ]

@router.post("/{node_id}/heartbeat")
def update_node_heartbeat(
    node_id: str,
    heartbeat_data: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update node heartbeat and status"""
    
    node = db.query(BlockchainNode).filter(BlockchainNode.node_id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Blockchain node not found")
    
    # Update heartbeat and status
    old_block_height = node.block_height
    node.last_heartbeat = datetime.utcnow()
    node.status = heartbeat_data.get("status", node.status)
    node.block_height = heartbeat_data.get("block_height", node.block_height)
    node.network_height = heartbeat_data.get("network_height", node.network_height)
    node.updated_at = datetime.utcnow()
    
    db.commit()
    
    # Log heartbeat if block height changed
    if old_block_height != node.block_height:
        log_activity(db, node.id, node.institution_id, "heartbeat",
                    f"Node heartbeat - block height updated from {old_block_height} to {node.block_height}",
                    {"block_height": node.block_height, "network_height": node.network_height},
                    block_height_before=old_block_height, block_height_after=node.block_height)
    
    return {
        "message": "Heartbeat updated successfully",
        "node_id": node.node_id,
        "status": node.status,
        "block_height": node.block_height,
        "last_heartbeat": node.last_heartbeat
    }

# Helper functions
def log_activity(db: Session, node_id: int, institution_id: int, activity_type: str, 
                message: str, activity_data: Optional[Dict[str, Any]] = None,
                status_before: Optional[str] = None, status_after: Optional[str] = None,
                block_height_before: Optional[int] = None, block_height_after: Optional[int] = None,
                triggered_by: Optional[int] = None):
    """Log node activity"""
    
    activity = NodeActivityLog(
        node_id=node_id,
        institution_id=institution_id,
        activity_type=activity_type,
        activity_message=message,
        activity_data=activity_data,
        status_before=status_before,
        status_after=status_after,
        block_height_before=block_height_before,
        block_height_after=block_height_after,
        triggered_by=triggered_by,
        created_at=datetime.utcnow()
    )
    
    db.add(activity)
    db.commit()

async def deploy_chaincode_background(deployment_id: int, db: Session):
    """Background task for chaincode deployment"""
    
    deployment = db.query(ChaincodeDeployment).filter(ChaincodeDeployment.id == deployment_id).first()
    if not deployment:
        return
    
    node = db.query(BlockchainNode).filter(BlockchainNode.id == deployment.node_id).first()
    if not node:
        return
    
    try:
        # Update status to installing
        deployment.status = "installing"
        deployment.updated_at = datetime.utcnow()
        db.commit()
        
        # Simulate chaincode installation (in real implementation, this would interact with Fabric SDK)
        await asyncio.sleep(5)
        
        # Update status to instantiating
        deployment.status = "instantiating"
        deployment.install_tx_id = f"INSTALL_TX_{deployment_id}_{int(datetime.utcnow().timestamp())}"
        deployment.installed_at = datetime.utcnow()
        deployment.updated_at = datetime.utcnow()
        db.commit()
        
        # Simulate chaincode instantiation
        await asyncio.sleep(3)
        
        # Mark as completed
        deployment.status = "active"
        deployment.instantiate_tx_id = f"INSTANTIATE_TX_{deployment_id}_{int(datetime.utcnow().timestamp())}"
        deployment.instantiated_at = datetime.utcnow()
        deployment.updated_at = datetime.utcnow()
        
        # Update node status
        node.chaincode_installed = True
        node.chaincode_instantiated = True
        node.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Log successful deployment
        log_activity(db, node.id, node.institution_id, "deploy",
                    f"Chaincode deployment {deployment.deployment_id} completed successfully",
                    {"deployment_id": deployment.deployment_id, "chaincode_name": deployment.chaincode_name})
        
    except Exception as e:
        # Handle deployment failure
        deployment.status = "failed"
        deployment.error_message = str(e)
        deployment.retry_count += 1
        deployment.updated_at = datetime.utcnow()
        
        db.commit()
        
        # Log deployment failure
        log_activity(db, node.id, node.institution_id, "error",
                    f"Chaincode deployment {deployment.deployment_id} failed: {str(e)}",
                    {"deployment_id": deployment.deployment_id, "error": str(e)},
                    error_code="DEPLOYMENT_FAILED", error_message=str(e))
