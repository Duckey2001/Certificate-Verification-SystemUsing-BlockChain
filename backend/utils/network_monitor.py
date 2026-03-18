#!/usr/bin/env python3
"""
Network monitoring and comprehensive logging system
Tracks all user activities, blockchain operations, and network events
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_
import json
import uuid

from models import User, AuditEvent, LoginActivity, Certificate, Payment, VerificationLog, Institution

class NetworkMonitor:
    """Comprehensive network monitoring and logging system"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log_user_activity(self, 
                         user_id: str, 
                         activity_type: str, 
                         details: Dict[str, Any],
                         institution_code: Optional[str] = None) -> str:
        """Log comprehensive user activity"""
        try:
            # Get user details
            user = self.db.query(User).filter(User.id == user_id).first()
            
            # Create audit event
            audit_event = AuditEvent(
                id=str(uuid.uuid4()),
                event_type=activity_type,
                actor_user_id=user_id,
                actor_role=user.role if user else "unknown",
                target_user_id=details.get("target_user_id"),
                institution_code=institution_code or (user.institution_code if user else None),
                certificate_hash=details.get("certificate_hash"),
                payload={
                    **details,
                    "timestamp": datetime.utcnow().isoformat(),
                    "user_agent": details.get("user_agent"),
                    "ip_address": details.get("ip_address"),
                    "session_id": details.get("session_id")
                },
                created_at=datetime.utcnow()
            )
            
            self.db.add(audit_event)
            self.db.commit()
            
            print(f"📝 Activity logged: {activity_type} by user {user_id}")
            return audit_event.id
            
        except Exception as e:
            print(f"❌ Failed to log activity: {e}")
            return None
    
    def log_blockchain_operation(self, 
                               operation_type: str,
                               certificate_hash: str,
                               transaction_id: Optional[str] = None,
                               user_id: Optional[str] = None,
                               details: Optional[Dict[str, Any]] = None) -> str:
        """Log blockchain-specific operations"""
        try:
            # Get user if provided
            user = self.db.query(User).filter(User.id == user_id).first() if user_id else None
            
            audit_event = AuditEvent(
                id=str(uuid.uuid4()),
                event_type=f"blockchain_{operation_type}",
                actor_user_id=user_id,
                actor_role=user.role if user else "system",
                institution_code=user.institution_code if user else None,
                certificate_hash=certificate_hash,
                payload={
                    "operation_type": operation_type,
                    "certificate_hash": certificate_hash,
                    "transaction_id": transaction_id,
                    "blockchain_network": details.get("network", "hardhat") if details else "hardhat",
                    "block_number": details.get("block_number") if details else None,
                    "gas_used": details.get("gas_used") if details else None,
                    "timestamp": datetime.utcnow().isoformat(),
                    **(details or {})
                },
                created_at=datetime.utcnow()
            )
            
            self.db.add(audit_event)
            self.db.commit()
            
            print(f"⛓️ Blockchain operation logged: {operation_type} for {certificate_hash[:16]}...")
            return audit_event.id
            
        except Exception as e:
            print(f"❌ Failed to log blockchain operation: {e}")
            return None
    
    def log_certificate_lifecycle(self, 
                                certificate_id: str,
                                event_type: str,
                                user_id: str,
                                details: Dict[str, Any]) -> str:
        """Log complete certificate lifecycle events"""
        try:
            # Get certificate details
            cert = self.db.query(Certificate).filter(Certificate.id == certificate_id).first()
            if not cert:
                print(f"❌ Certificate {certificate_id} not found for lifecycle logging")
                return None
            
            # Get user details
            user = self.db.query(User).filter(User.id == user_id).first()
            
            audit_event = AuditEvent(
                id=str(uuid.uuid4()),
                event_type=f"certificate_{event_type}",
                actor_user_id=user_id,
                actor_role=user.role if user else "unknown",
                target_user_id=details.get("target_user_id"),
                institution_code=cert.institution,
                certificate_hash=cert.certificate_hash,
                payload={
                    "certificate_id": certificate_id,
                    "student_name": f"{cert.student_name} {cert.student_surname}".strip(),
                    "student_id": cert.student_id,
                    "institution": cert.institution,
                    "event_type": event_type,
                    "blockchain_tx_id": cert.blockchain_tx_id,
                    "blockchain_network": cert.blockchain_network,
                    "timestamp": datetime.utcnow().isoformat(),
                    **details
                },
                created_at=datetime.utcnow()
            )
            
            self.db.add(audit_event)
            self.db.commit()
            
            print(f"📜 Certificate lifecycle logged: {event_type} for {cert.student_name}")
            return audit_event.id
            
        except Exception as e:
            print(f"❌ Failed to log certificate lifecycle: {e}")
            return None
    
    def get_network_activity(self, 
                            limit: int = 100,
                            institution_code: Optional[str] = None,
                            event_type: Optional[str] = None,
                            time_range: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get network activity with filtering options"""
        try:
            query = self.db.query(AuditEvent)
            
            # Apply filters
            if institution_code:
                query = query.filter(AuditEvent.institution_code == institution_code)
            
            if event_type:
                query = query.filter(AuditEvent.event_type == event_type)
            
            if time_range:
                cutoff_time = datetime.utcnow() - timedelta(hours=time_range)
                query = query.filter(AuditEvent.created_at >= cutoff_time)
            
            # Get results with user details
            events = query.order_by(AuditEvent.created_at.desc()).limit(limit).all()
            
            activity = []
            for event in events:
                # Get user details
                user = self.db.query(User).filter(User.id == event.actor_user_id).first()
                
                activity.append({
                    "id": event.id,
                    "event_type": event.event_type,
                    "actor_user_id": event.actor_user_id,
                    "actor_username": user.username if user else "Unknown",
                    "actor_role": event.actor_role,
                    "institution_code": event.institution_code,
                    "certificate_hash": event.certificate_hash,
                    "payload": event.payload,
                    "created_at": event.created_at.isoformat(),
                    "severity": self._get_event_severity(event.event_type)
                })
            
            return activity
            
        except Exception as e:
            print(f"❌ Failed to get network activity: {e}")
            return []
    
    def get_institution_summary(self, institution_code: str) -> Dict[str, Any]:
        """Get comprehensive institution activity summary"""
        try:
            # Get institution details
            institution = self.db.query(Institution).filter(
                Institution.code == institution_code
            ).first()
            
            if not institution:
                return {"error": "Institution not found"}
            
            # Get user counts
            total_users = self.db.query(func.count(User.id)).filter(
                User.institution_code == institution_code
            ).scalar()
            
            active_users = self.db.query(func.count(User.id)).filter(
                User.institution_code == institution_code,
                User.is_active == True
            ).scalar()
            
            # Get certificate counts
            total_certificates = self.db.query(func.count(Certificate.id)).filter(
                Certificate.institution == institution_code
            ).scalar()
            
            blockchain_certificates = self.db.query(func.count(Certificate.id)).filter(
                Certificate.institution == institution_code,
                Certificate.blockchain_tx_id.isnot(None)
            ).scalar()
            
            # Get recent activity
            recent_events = self.db.query(AuditEvent).filter(
                AuditEvent.institution_code == institution_code,
                AuditEvent.created_at >= datetime.utcnow() - timedelta(hours=24)
            ).count()
            
            # Get activity breakdown
            activity_breakdown = self.db.query(
                AuditEvent.event_type,
                func.count(AuditEvent.id).label('count')
            ).filter(
                AuditEvent.institution_code == institution_code,
                AuditEvent.created_at >= datetime.utcnow() - timedelta(days=7)
            ).group_by(AuditEvent.event_type).all()
            
            return {
                "institution": {
                    "code": institution.code,
                    "name": institution.name,
                    "role": institution.role
                },
                "users": {
                    "total": total_users,
                    "active": active_users,
                    "inactive": total_users - active_users
                },
                "certificates": {
                    "total": total_certificates,
                    "on_blockchain": blockchain_certificates,
                    "pending": total_certificates - blockchain_certificates
                },
                "activity": {
                    "recent_events_24h": recent_events,
                    "breakdown_7d": [
                        {"event_type": event.event_type, "count": event.count}
                        for event in activity_breakdown
                    ]
                },
                "health_score": self._calculate_institution_health(
                    active_users, total_certificates, blockchain_certificates, recent_events
                )
            }
            
        except Exception as e:
            print(f"❌ Failed to get institution summary: {e}")
            return {"error": str(e)}
    
    def get_network_health(self) -> Dict[str, Any]:
        """Get overall network health metrics"""
        try:
            # Get total counts
            total_users = self.db.query(func.count(User.id)).scalar()
            active_users = self.db.query(func.count(User.id)).filter(User.is_active == True).scalar()
            total_institutions = self.db.query(func.count(func.distinct(User.institution_code))).filter(
                User.institution_code.isnot(None)
            ).scalar()
            
            # Get certificate stats
            total_certificates = self.db.query(func.count(Certificate.id)).scalar()
            blockchain_certificates = self.db.query(func.count(Certificate.id)).filter(
                Certificate.blockchain_tx_id.isnot(None)
            ).scalar()
            
            # Get recent activity
            recent_activity = self.db.query(AuditEvent).filter(
                AuditEvent.created_at >= datetime.utcnow() - timedelta(hours=1)
            ).count()
            
            # Get error rate
            error_events = self.db.query(func.count(AuditEvent.id)).filter(
                AuditEvent.created_at >= datetime.utcnow() - timedelta(hours=24),
                or_(
                    AuditEvent.event_type.like('%error%'),
                    AuditEvent.event_type.like('%failed%')
                )
            ).scalar()
            
            total_events_24h = self.db.query(func.count(AuditEvent.id)).filter(
                AuditEvent.created_at >= datetime.utcnow() - timedelta(hours=24)
            ).scalar()
            
            error_rate = (error_events / total_events_24h * 100) if total_events_24h > 0 else 0
            
            return {
                "overall_status": "healthy" if recent_activity > 0 else "idle",
                "users": {
                    "total": total_users,
                    "active": active_users,
                    "inactive": total_users - active_users
                },
                "institutions": {
                    "total": total_institutions
                },
                "certificates": {
                    "total": total_certificates,
                    "on_blockchain": blockchain_certificates,
                    "blockchain_rate": (blockchain_certificates / total_certificates * 100) if total_certificates > 0 else 0
                },
                "activity": {
                    "recent_1h": recent_activity,
                    "total_24h": total_events_24h,
                    "error_rate_24h": error_rate
                },
                "health_score": self._calculate_network_health(
                    active_users, total_certificates, blockchain_certificates, error_rate
                )
            }
            
        except Exception as e:
            print(f"❌ Failed to get network health: {e}")
            return {"error": str(e)}
    
    def _get_event_severity(self, event_type: str) -> str:
        """Determine event severity for monitoring"""
        if any(keyword in event_type.lower() for keyword in ['error', 'failed', 'rejected']):
            return "high"
        elif any(keyword in event_type.lower() for keyword in ['login', 'logout', 'certificate_issued']):
            return "medium"
        else:
            return "low"
    
    def _calculate_institution_health(self, active_users: int, total_certs: int, 
                                    blockchain_certs: int, recent_activity: int) -> int:
        """Calculate institution health score (0-100)"""
        score = 0
        
        # User activity (40%)
        if active_users > 0:
            score += min(40, active_users * 10)
        
        # Certificate activity (30%)
        if total_certs > 0:
            blockchain_rate = (blockchain_certs / total_certs) * 100
            score += min(30, blockchain_rate * 0.3)
        
        # Recent activity (30%)
        if recent_activity > 0:
            score += min(30, recent_activity * 2)
        
        return min(100, score)
    
    def _calculate_network_health(self, active_users: int, total_certs: int, 
                               blockchain_certs: int, error_rate: float) -> int:
        """Calculate overall network health score (0-100)"""
        score = 0
        
        # User activity (30%)
        if active_users > 0:
            score += min(30, (active_users / 10) * 30)
        
        # Certificate activity (40%)
        if total_certs > 0:
            blockchain_rate = (blockchain_certs / total_certs) * 100
            score += min(40, blockchain_rate * 0.4)
        
        # Error rate (30%) - lower is better
        error_penalty = min(30, error_rate * 3)
        score += 30 - error_penalty
        
        return max(0, min(100, score))

# Global monitor instance
def get_network_monitor(db: Session) -> NetworkMonitor:
    """Get network monitor instance"""
    return NetworkMonitor(db)
