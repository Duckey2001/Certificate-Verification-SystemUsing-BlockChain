"""
WebSocket API endpoints for real-time notifications and updates
"""

import json
import uuid
from typing import Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from api.auth import get_current_user
from database import get_db
from models import User
from utils.realtime_notifications import notification_manager, notification_service
from utils.realtime_processing import websocket_endpoint, realtime_service

router = APIRouter(prefix="/ws", tags=["websocket"])

@router.websocket("/processing")
async def processing_websocket(
    websocket: WebSocket,
    session_id: Optional[str] = None
):
    """
    WebSocket endpoint for real-time certificate processing updates
    
    Clients can connect to receive live updates during bulk certificate processing.
    
    Message types from server:
    - connection_established: Initial connection confirmation
    - batch_started: New batch processing started
    - processing_update: Individual file processing update
    - batch_completed: Batch processing completed
    - stats_response: Response to stats request
    - pong: Response to ping message
    
    Message types from client:
    - get_stats: Request current statistics
    - ping: Keep-alive message
    
    Example client usage:
    ```
    const ws = new WebSocket('ws://localhost:8000/ws/processing?session_id=my_session');
    
    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        console.log('Received:', data);
        
        if (data.type === 'processing_update') {
            // Update UI with processing progress
            updateProgress(data.update, data.session_stats);
        }
    };
    
    // Request current stats
    ws.send(JSON.stringify({ type: 'get_stats' }));
    
    // Keep connection alive
    setInterval(() => {
        ws.send(JSON.stringify({ type: 'ping' }));
    }, 30000);
    ```
    """
    await websocket_endpoint(websocket, session_id)

@router.websocket("/admin-monitor")
async def admin_monitor_websocket(
    websocket: WebSocket,
    token: str
):
    """
    WebSocket endpoint for admin monitoring of all processing activities
    
    Admin-only endpoint that provides real-time monitoring of all certificate
    processing activities across the system.
    
    Requires valid authentication token from an admin user.
    """
    # Verify admin authentication
    try:
        # Simple token verification - in production, use proper JWT validation
        from database import SessionLocal
        db = SessionLocal()
        try:
            # For now, we'll use a simple approach - in production, validate JWT token
            # This is a placeholder for proper authentication
            if token != "admin_token_placeholder":
                await websocket.close(code=4003, reason="Invalid admin token")
                return
        finally:
            db.close()
    except Exception as e:
        await websocket.close(code=4001, reason="Authentication failed")
        return
    
    # Connect as admin monitor
    import time
    session_id = f"admin_monitor_{int(time.time())}"
    await realtime_service.connect(websocket, session_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "get_global_stats":
                stats = await realtime_service.get_real_time_stats()
                await realtime_service.send_message(session_id, {
                    "type": "global_stats_response",
                    "stats": stats,
                    "timestamp": datetime.utcnow().isoformat()
                })
            elif message.get("type") == "get_active_sessions":
                active_sessions = list(realtime_service.processing_sessions.keys())
                session_summaries = []
                
                for sid in active_sessions[:10]:  # Limit to 10 sessions
                    summary = realtime_service.get_session_summary(sid)
                    if summary:
                        session_summaries.append(summary)
                
                await realtime_service.send_message(session_id, {
                    "type": "active_sessions_response",
                    "sessions": session_summaries,
                    "timestamp": datetime.utcnow().isoformat()
                })
            elif message.get("type") == "ping":
                await realtime_service.send_message(session_id, {
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
    except WebSocketDisconnect:
        realtime_service.disconnect(session_id)
    except Exception as e:
        print(f"Admin monitor WebSocket error: {e}")
        realtime_service.disconnect(session_id)

@router.websocket("/notifications/{user_id}")
async def websocket_notifications(
    websocket: WebSocket, 
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time notifications
    Connect: ws://localhost:8000/ws/notifications/{user_id}
    """
    # Verify user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        await websocket.close(code=4004, reason="User not found")
        return
    
    # Generate unique connection ID
    connection_id = str(uuid.uuid4())
    
    try:
        await notification_manager.connect(websocket, user_id, connection_id)
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                await handle_websocket_message(websocket, user_id, message)
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"❌ Error handling WebSocket message: {e}")
                break
                
    except WebSocketDisconnect:
        pass
    finally:
        notification_manager.disconnect(connection_id)

async def handle_websocket_message(websocket: WebSocket, user_id: int, message: dict):
    """Handle incoming WebSocket messages"""
    message_type = message.get("type")
    
    if message_type == "mark_notification_read":
        # Mark notification as read
        notification_id = message.get("notification_id")
        if notification_id:
            await mark_notification_read(user_id, notification_id)
    
    elif message_type == "get_notifications":
        # Send recent notifications
        await send_recent_notifications(websocket, user_id)
    
    elif message_type == "ping":
        # Respond to ping with pong
        await websocket.send_text(json.dumps({"type": "pong"}))
    
    elif message_type == "get_user_stats":
        # Send user statistics
        await send_user_stats(websocket, user_id)

async def mark_notification_read(user_id: int, notification_id: int):
    """Mark a notification as read"""
    from database import SessionLocal
    from models import Notification
    
    db = SessionLocal()
    try:
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        
        if notification and not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            db.commit()
            
            # Send confirmation back to user
            await notification_manager.send_to_user(user_id, {
                "type": "notification_marked_read",
                "data": {"notification_id": notification_id}
            })
    except Exception as e:
        print(f"❌ Error marking notification as read: {e}")
    finally:
        db.close()

async def send_recent_notifications(websocket: WebSocket, user_id: int):
    """Send recent notifications to user"""
    from database import SessionLocal
    from models import Notification
    
    db = SessionLocal()
    try:
        notifications = db.query(Notification).filter(
            Notification.user_id == user_id
        ).order_by(Notification.created_at.desc()).limit(20).all()
        
        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                "id": notification.id,
                "title": notification.title,
                "message": notification.message,
                "notification_type": notification.notification_type,
                "priority": notification.priority,
                "is_read": notification.is_read,
                "action_url": notification.action_url,
                "action_text": notification.action_text,
                "created_at": notification.created_at.isoformat(),
                "metadata": notification.metadata
            })
        
        await websocket.send_text(json.dumps({
            "type": "notifications_list",
            "data": notifications_data
        }))
    except Exception as e:
        print(f"❌ Error sending notifications: {e}")
    finally:
        db.close()

async def send_user_stats(websocket: WebSocket, user_id: int):
    """Send user statistics"""
    from database import SessionLocal
    from models import User, Notification, Certificate, VerificationRequest
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return
        
        # Get unread notifications count
        unread_count = db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).count()
        
        # Get certificates issued/verified counts
        certificates_issued = db.query(Certificate).filter(
            Certificate.issuer_id == user_id
        ).count()
        
        certificates_verified = db.query(VerificationRequest).filter(
            VerificationRequest.verifier_id == user_id
        ).count()
        
        stats = {
            "unread_notifications": unread_count,
            "available_credits": user.available_credits,
            "certificates_issued": certificates_issued,
            "certificates_verified": certificates_verified,
            "role": user.role,
            "is_verified": user.is_verified
        }
        
        await websocket.send_text(json.dumps({
            "type": "user_stats",
            "data": stats
        }))
    except Exception as e:
        print(f"❌ Error sending user stats: {e}")
    finally:
        db.close()

@router.get("/test-connection")
async def test_websocket_connection():
    """Test endpoint to verify WebSocket router is working"""
    return {"message": "WebSocket endpoint is available at /ws/notifications/{user_id}"}

# Helper function to send notifications from other parts of the application
async def notify_all_users(title: str, message: str, notification_type: str = "system"):
    """Send a notification to all connected users"""
    await notification_manager.broadcast_to_all({
        "type": "broadcast_notification",
        "data": {
            "title": title,
            "message": message,
            "notification_type": notification_type,
            "timestamp": datetime.utcnow().isoformat()
        }
    })

# Export for use in other modules
__all__ = [
    "websocket_notifications",
    "notify_all_users",
    "notification_manager",
    "notification_service"
]
