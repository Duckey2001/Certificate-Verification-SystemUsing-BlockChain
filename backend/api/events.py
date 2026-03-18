import asyncio
import json
import logging
from typing import AsyncGenerator, Optional, List, Dict, Any
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

from database import get_db
from models import AuditEvent, User, Payment, VerificationLog, Certificate
from auth import get_current_user, get_optional_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/events", tags=["events"])

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.user_connections: Dict[str, List[WebSocket]] = {}  # user_id -> websockets

    async def connect(self, websocket: WebSocket, user_id: Optional[str] = None):
        await websocket.accept()
        self.active_connections.append(websocket)
        if user_id:
            if user_id not in self.user_connections:
                self.user_connections[user_id] = []
            self.user_connections[user_id].append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket, user_id: Optional[str] = None):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if user_id and user_id in self.user_connections:
            if websocket in self.user_connections[user_id]:
                self.user_connections[user_id].remove(websocket)
            if not self.user_connections[user_id]:
                del self.user_connections[user_id]
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting message: {e}")
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

    async def send_to_user(self, user_id: str, message: dict):
        """Send message to specific user"""
        if user_id in self.user_connections:
            disconnected = []
            for connection in self.user_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to user {user_id}: {e}")
                    disconnected.append(connection)
            
            # Clean up disconnected clients
            for conn in disconnected:
                self.disconnect(conn, user_id)

manager = ConnectionManager()

def _format_sse(data: dict) -> str:
    """Format data as Server-Sent Event"""
    try:
        return f"data: {json.dumps(data, default=str)}\n\n"
    except Exception as e:
        logger.error(f"Error formatting SSE: {e}")
        return f"data: {json.dumps({'error': 'Failed to format event'})}\n\n"

def _create_event_payload(event: AuditEvent) -> dict:
    """Create standardized event payload"""
    return {
        "id": event.id,
        "event_type": event.event_type,
        "actor_user_id": event.actor_user_id,
        "actor_role": event.actor_role,
        "target_user_id": event.target_user_id,
        "certificate_hash": event.certificate_hash,
        "verification_request_id": event.verification_request_id,
        "payment_id": event.payment_id,
        "payload": event.payload,
        "created_at": event.created_at.isoformat() if event.created_at else None,
        "severity": event.severity or "info"
    }

@router.get("/stream")
async def stream_events(
    since_id: int = Query(0, ge=0, description="Last seen event ID"),
    event_types: Optional[List[str]] = Query(None, description="Filter by event types"),
    poll_interval_ms: int = Query(1000, ge=250, le=10000, description="Polling interval in milliseconds"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user)
):
    """
    Server-Sent Events stream of AuditEvent rows.
    
    Clients can pass since_id to resume from last seen event id.
    Event types can be filtered using the event_types parameter.
    """
    async def event_generator() -> AsyncGenerator[str, None]:
        last_id = since_id
        # Send initial connection message
        yield _format_sse({
            "type": "connection",
            "status": "connected",
            "since_id": since_id,
            "user": current_user.username if current_user else "anonymous",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        while True:
            try:
                # Build query
                query = db.query(AuditEvent).filter(AuditEvent.id > last_id)
                
                # Apply event type filter
                if event_types:
                    query = query.filter(AuditEvent.event_type.in_(event_types))
                
                # Apply user role filter (admins see all, others see relevant events)
                if current_user and current_user.role != "admin":
                    # Non-admins see events related to them or their institution
                    query = query.filter(
                        (AuditEvent.actor_user_id == current_user.id) |
                        (AuditEvent.target_user_id == current_user.id)
                    )
                
                # Get new events
                events = query.order_by(AuditEvent.id.asc()).limit(100).all()
                
                for event in events:
                    last_id = event.id
                    payload = _create_event_payload(event)
                    
                    # Add context based on event type
                    if event.certificate_hash:
                        # Fetch additional certificate info if needed
                        pass
                    
                    yield _format_sse(payload)
                
                # Send heartbeat every 30 seconds
                if last_id == since_id:
                    yield _format_sse({
                        "type": "heartbeat",
                        "timestamp": datetime.utcnow().isoformat()
                    })
                
                await asyncio.sleep(poll_interval_ms / 1000.0)
                
            except Exception as e:
                logger.error(f"Error in event stream: {e}")
                yield _format_sse({
                    "type": "error",
                    "message": "Stream error, reconnecting...",
                    "error": str(e)
                })
                await asyncio.sleep(5)  # Wait before retrying

    return StreamingResponse(
        event_generator(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable proxy buffering
        }
    )

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time events
    """
    await manager.connect(websocket)
    
    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connection",
            "status": "connected",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for messages from client (with timeout)
                data = await asyncio.wait_for(
                    websocket.receive_json(), 
                    timeout=30.0
                )
                
                # Handle client messages
                if data.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
                elif data.get("type") == "subscribe":
                    # Handle subscription to specific event types
                    event_types = data.get("event_types", [])
                    await websocket.send_json({
                        "type": "subscribed",
                        "event_types": event_types
                    })
                    
            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                await websocket.send_json({"type": "heartbeat"})
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                await websocket.send_json({
                    "type": "error",
                    "message": str(e)
                })
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@router.get("/history")
async def get_event_history(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get paginated event history"""
    
    # Build query
    query = db.query(AuditEvent)
    
    # Apply filters
    if event_type:
        query = query.filter(AuditEvent.event_type == event_type)
    
    if user_id:
        query = query.filter(
            (AuditEvent.actor_user_id == user_id) | 
            (AuditEvent.target_user_id == user_id)
        )
    
    if start_date:
        query = query.filter(AuditEvent.created_at >= start_date)
    
    if end_date:
        query = query.filter(AuditEvent.created_at <= end_date)
    
    # Role-based filtering
    if current_user.role != "admin":
        # Non-admins see only events related to them
        query = query.filter(
            (AuditEvent.actor_user_id == current_user.id) |
            (AuditEvent.target_user_id == current_user.id)
        )
    
    # Get total count
    total = query.count()
    
    # Get paginated results
    events = query.order_by(AuditEvent.id.desc()).offset(offset).limit(limit).all()
    
    return {
        "events": [_create_event_payload(event) for event in events],
        "total": total,
        "offset": offset,
        "limit": limit
    }

@router.get("/stats")
async def get_event_stats(
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get event statistics"""
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Build base query
    query = db.query(AuditEvent).filter(AuditEvent.created_at >= cutoff_date)
    
    # Role-based filtering
    if current_user.role != "admin":
        query = query.filter(
            (AuditEvent.actor_user_id == current_user.id) |
            (AuditEvent.target_user_id == current_user.id)
        )
    
    # Get counts by event type
    type_counts = query.group_by(AuditEvent.event_type).with_entities(
        AuditEvent.event_type, func.count(AuditEvent.id)
    ).all()
    
    # Get daily counts
    daily_counts = db.query(
        func.date(AuditEvent.created_at).label('date'),
        func.count(AuditEvent.id).label('count')
    ).filter(AuditEvent.created_at >= cutoff_date)
    
    if current_user.role != "admin":
        daily_counts = daily_counts.filter(
            (AuditEvent.actor_user_id == current_user.id) |
            (AuditEvent.target_user_id == current_user.id)
        )
    
    daily_counts = daily_counts.group_by(
        func.date(AuditEvent.created_at)
    ).order_by(func.date(AuditEvent.created_at)).all()
    
    return {
        "period_days": days,
        "total_events": sum(count for _, count in type_counts),
        "by_type": {event_type: count for event_type, count in type_counts},
        "daily_totals": [
            {"date": str(date), "count": count}
            for date, count in daily_counts
        ]
    }

@router.get("/types")
async def get_event_types(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of all event types"""
    
    event_types = db.query(AuditEvent.event_type).distinct().all()
    return [et[0] for et in event_types]

# Function to broadcast events (can be called from other modules)
async def broadcast_event(event: AuditEvent):
    """Broadcast an event to all connected clients"""
    payload = _create_event_payload(event)
    
    # Broadcast to all
    await manager.broadcast(payload)
    
    # Send to specific user if applicable
    if event.target_user_id:
        await manager.send_to_user(event.target_user_id, payload)
    if event.actor_user_id and event.actor_user_id != event.target_user_id:
        await manager.send_to_user(event.actor_user_id, payload)

# Background task to clean up old events (can be scheduled)
async def cleanup_old_events(days_to_keep: int = 30, db: Session = Depends(get_db)):
    """Delete events older than specified days"""
    cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
    
    deleted = db.query(AuditEvent).filter(
        AuditEvent.created_at < cutoff_date
    ).delete()
    
    db.commit()
    logger.info(f"Cleaned up {deleted} old events")
    return deleted

# Example of how to create and broadcast events
def create_audit_event(
    db: Session,
    event_type: str,
    actor_user_id: Optional[str] = None,
    actor_role: Optional[str] = None,
    target_user_id: Optional[str] = None,
    certificate_hash: Optional[str] = None,
    verification_request_id: Optional[int] = None,
    payment_id: Optional[str] = None,
    payload: Optional[Dict] = None,
    severity: str = "info"
) -> AuditEvent:
    """Create an audit event and broadcast it"""
    
    event = AuditEvent(
        id=str(uuid.uuid4()),
        event_type=event_type,
        actor_user_id=actor_user_id,
        actor_role=actor_role,
        target_user_id=target_user_id,
        certificate_hash=certificate_hash,
        verification_request_id=verification_request_id,
        payment_id=payment_id,
        payload=payload,
        severity=severity,
        created_at=datetime.utcnow()
    )
    
    db.add(event)
    db.commit()
    db.refresh(event)
    
    # Schedule broadcast (don't await to avoid blocking)
    asyncio.create_task(broadcast_event(event))
    
    return event