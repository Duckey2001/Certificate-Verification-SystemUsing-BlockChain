"""
Real-time notification service for CertiVert system
Handles WebSocket connections and broadcasts notifications to all connected clients
"""

import asyncio
import json
from datetime import datetime
from typing import List, Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User, Notification, SystemActivity

class NotificationManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.user_connections: Dict[int, Set[str]] = {}  # user_id -> connection_ids
        
    async def connect(self, websocket: WebSocket, user_id: int, connection_id: str):
        """Connect a new WebSocket client"""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        
        if user_id not in self.user_connections:
            self.user_connections[user_id] = set()
        self.user_connections[user_id].add(connection_id)
        
        print(f"✅ User {user_id} connected with connection {connection_id}")
        
        # Send unread notifications
        await self.send_unread_notifications(user_id, connection_id)
    
    def disconnect(self, connection_id: str):
        """Disconnect a WebSocket client"""
        if connection_id in self.active_connections:
            # Remove from user connections
            for user_id, connections in self.user_connections.items():
                if connection_id in connections:
                    connections.remove(connection_id)
                    if not connections:
                        del self.user_connections[user_id]
                    break
            
            del self.active_connections[connection_id]
            print(f"❌ Connection {connection_id} disconnected")
    
    async def send_unread_notifications(self, user_id: int, connection_id: str):
        """Send all unread notifications to a newly connected user"""
        db = SessionLocal()
        try:
            unread_notifications = db.query(Notification).filter(
                Notification.user_id == user_id,
                Notification.is_read == False
            ).order_by(Notification.created_at.desc()).limit(20).all()
            
            for notification in unread_notifications:
                await self.send_notification_to_connection(
                    connection_id, 
                    {
                        "type": "notification",
                        "data": {
                            "id": notification.id,
                            "title": notification.title,
                            "message": notification.message,
                            "notification_type": notification.notification_type,
                            "priority": notification.priority,
                            "action_url": notification.action_url,
                            "action_text": notification.action_text,
                            "created_at": notification.created_at.isoformat(),
                            "metadata": notification.metadata
                        }
                    }
                )
        except Exception as e:
            print(f"❌ Error sending unread notifications: {e}")
        finally:
            db.close()
    
    async def send_notification_to_connection(self, connection_id: str, message: dict):
        """Send a message to a specific connection"""
        if connection_id in self.active_connections:
            websocket = self.active_connections[connection_id]
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                print(f"❌ Error sending to connection {connection_id}: {e}")
                self.disconnect(connection_id)
    
    async def send_to_user(self, user_id: int, message: dict):
        """Send a message to all connections for a specific user"""
        if user_id in self.user_connections:
            for connection_id in self.user_connections[user_id].copy():
                await self.send_notification_to_connection(connection_id, message)
    
    async def broadcast_to_all(self, message: dict):
        """Broadcast a message to all connected clients"""
        for connection_id in list(self.active_connections.keys()):
            await self.send_notification_to_connection(connection_id, message)
    
    async def broadcast_to_role(self, role: str, message: dict):
        """Broadcast a message to all users with a specific role"""
        db = SessionLocal()
        try:
            users_with_role = db.query(User).filter(User.role == role).all()
            for user in users_with_role:
                await self.send_to_user(user.id, message)
        except Exception as e:
            print(f"❌ Error broadcasting to role {role}: {e}")
        finally:
            db.close()

class NotificationService:
    def __init__(self, manager: NotificationManager):
        self.manager = manager
    
    async def create_notification(
        self, 
        user_id: int, 
        title: str, 
        message: str, 
        notification_type: str,
        priority: str = "medium",
        action_url: str = None,
        action_text: str = None,
        metadata: dict = None
    ):
        """Create a new notification and send it to the user"""
        db = SessionLocal()
        try:
            # Create notification in database
            notification = Notification(
                user_id=user_id,
                title=title,
                message=message,
                notification_type=notification_type,
                priority=priority,
                action_url=action_url,
                action_text=action_text,
                metadata=metadata
            )
            db.add(notification)
            db.commit()
            db.refresh(notification)
            
            # Send real-time notification
            await self.manager.send_to_user(user_id, {
                "type": "notification",
                "data": {
                    "id": notification.id,
                    "title": notification.title,
                    "message": notification.message,
                    "notification_type": notification.notification_type,
                    "priority": notification.priority,
                    "action_url": notification.action_url,
                    "action_text": notification.action_text,
                    "created_at": notification.created_at.isoformat(),
                    "metadata": notification.metadata
                }
            })
            
            return notification
        except Exception as e:
            print(f"❌ Error creating notification: {e}")
            db.rollback()
            return None
        finally:
            db.close()
    
    async def create_system_activity(
        self,
        activity_type: str,
        title: str,
        description: str = None,
        actor_user_id: int = None,
        target_user_id: int = None,
        institution_code: str = None,
        certificate_hash: str = None,
        verification_request_id: int = None,
        payment_id: int = None,
        status: str = "success",
        ip_address: str = None,
        metadata: dict = None,
        impact_score: int = 1
    ):
        """Create a system activity and broadcast to relevant users"""
        db = SessionLocal()
        try:
            # Get actor details
            actor_name = None
            actor_role = None
            if actor_user_id:
                actor = db.query(User).filter(User.id == actor_user_id).first()
                if actor:
                    actor_name = actor.username
                    actor_role = actor.role
            
            # Create activity in database
            activity = SystemActivity(
                activity_type=activity_type,
                actor_user_id=actor_user_id,
                actor_role=actor_role,
                actor_name=actor_name,
                target_user_id=target_user_id,
                institution_code=institution_code,
                certificate_hash=certificate_hash,
                verification_request_id=verification_request_id,
                payment_id=payment_id,
                title=title,
                description=description,
                status=status,
                ip_address=ip_address,
                metadata=metadata,
                impact_score=impact_score
            )
            db.add(activity)
            db.commit()
            db.refresh(activity)
            
            # Broadcast to admin users
            await self.manager.broadcast_to_role("admin", {
                "type": "system_activity",
                "data": {
                    "id": activity.id,
                    "activity_type": activity.activity_type,
                    "actor_name": activity.actor_name,
                    "actor_role": activity.actor_role,
                    "title": activity.title,
                    "description": activity.description,
                    "status": activity.status,
                    "institution_code": activity.institution_code,
                    "impact_score": activity.impact_score,
                    "created_at": activity.created_at.isoformat(),
                    "metadata": activity.metadata
                }
            })
            
            # Send notification to target user if specified
            if target_user_id:
                await self.create_notification(
                    target_user_id,
                    title,
                    description or title,
                    activity_type,
                    "medium",
                    metadata=metadata
                )
            
            return activity
        except Exception as e:
            print(f"❌ Error creating system activity: {e}")
            db.rollback()
            return None
        finally:
            db.close()
    
    async def notify_certificate_issued(self, issuer_id: int, student_name: str, certificate_hash: str):
        """Notify when a certificate is issued"""
        # Notify all verifiers
        await self.manager.broadcast_to_role("verifier", {
            "type": "certificate_issued",
            "data": {
                "issuer_id": issuer_id,
                "student_name": student_name,
                "certificate_hash": certificate_hash,
                "message": f"New certificate issued for {student_name}",
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        # Create system activity
        await self.create_system_activity(
            activity_type="certificate_issue",
            title=f"New certificate issued for {student_name}",
            description=f"LGCSE certificate issued for {student_name}",
            actor_user_id=issuer_id,
            certificate_hash=certificate_hash,
            metadata={"student_name": student_name, "certificate_hash": certificate_hash},
            impact_score=7
        )
    
    async def notify_certificate_verified(self, verifier_id: int, certificate_hash: str, result: str):
        """Notify when a certificate is verified"""
        # Notify all issuers
        await self.manager.broadcast_to_role("issuer", {
            "type": "certificate_verified",
            "data": {
                "verifier_id": verifier_id,
                "certificate_hash": certificate_hash,
                "result": result,
                "message": f"Certificate verification {result}",
                "timestamp": datetime.utcnow().isoformat()
            }
        })
        
        # Create system activity
        await self.create_system_activity(
            activity_type="verification",
            title=f"Certificate verification {result}",
            description=f"Certificate verification completed with result: {result}",
            actor_user_id=verifier_id,
            certificate_hash=certificate_hash,
            metadata={"certificate_hash": certificate_hash, "result": result},
            impact_score=5
        )
    
    async def notify_payment_received(self, user_id: int, amount: float, method: str):
        """Notify when payment is received"""
        await self.create_notification(
            user_id,
            f"Payment of M{amount} received",
            f"Your {method} payment of M{amount} has been confirmed and credits added to your account.",
            "payment",
            "high",
            action_url="/credits",
            action_text="View Credits",
            metadata={"amount": amount, "method": method}
        )
        
        # Create system activity
        await self.create_system_activity(
            activity_type="payment",
            title=f"Payment of M{amount} received",
            description=f"{method} payment received for credit purchase",
            target_user_id=user_id,
            metadata={"amount": amount, "method": method},
            impact_score=6
        )

# Global instances
notification_manager = NotificationManager()
notification_service = NotificationService(notification_manager)
