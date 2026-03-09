#!/usr/bin/env python3
"""
Network activity API endpoints for comprehensive monitoring
Provides real-time activity tracking and logging for all network operations
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, and_, or_
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from models import User, AuditEvent, LoginActivity, Certificate, Payment, VerificationLog, Institution
from database import get_db
from auth import get_current_user
from utils.network_monitor import get_network_monitor

router = APIRouter(prefix="/api/network", tags=["network-activity"])

@router.get("/activity")
def get_network_activity(
    limit: int = Query(50, ge=1, le=200),
    institution_code: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    time_range: Optional[int] = Query(None, description="Hours to look back"),
    severity: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get network activity with filtering options"""
    try:
        monitor = get_network_monitor(db)
        
        activity = monitor.get_network_activity(
            limit=limit,
            institution_code=institution_code,
            event_type=event_type,
            time_range=time_range
        )
        
        # Filter by severity if provided
        if severity:
            activity = [a for a in activity if a.get('severity') == severity]
        
        return {
            "activity": activity,
            "total": len(activity),
            "filters": {
                "institution_code": institution_code,
                "event_type": event_type,
                "time_range": time_range,
                "severity": severity
            }
        }
        
    except Exception as e:
        return {
            "activity": [],
            "total": 0,
            "error": str(e)
        }

@router.get("/health")
def get_network_health(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get comprehensive network health metrics"""
    try:
        monitor = get_network_monitor(db)
        health = monitor.get_network_health()
        
        return health
        
    except Exception as e:
        return {
            "overall_status": "error",
            "error": str(e),
            "last_check": datetime.utcnow().isoformat()
        }

@router.get("/institutions/{institution_code}/summary")
def get_institution_summary(
    institution_code: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get comprehensive institution activity summary"""
    try:
        monitor = get_network_monitor(db)
        summary = monitor.get_institution_summary(institution_code)
        
        return summary
        
    except Exception as e:
        return {
            "institution_code": institution_code,
            "error": str(e)
        }

@router.get("/institutions")
def get_all_institutions_activity(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get activity summary for all institutions"""
    try:
        # Get all institutions with users
        institutions = db.query(Institution).join(User).filter(
            User.institution_code == Institution.code,
            User.is_active == True
        ).distinct().limit(limit).all()
        
        monitor = get_network_monitor(db)
        summaries = []
        
        for institution in institutions:
            summary = monitor.get_institution_summary(institution.code)
            if "error" not in summary:
                summaries.append(summary)
        
        # Sort by health score
        summaries.sort(key=lambda x: x.get("health_score", 0), reverse=True)
        
        return {
            "institutions": summaries,
            "total": len(summaries)
        }
        
    except Exception as e:
        return {
            "institutions": [],
            "total": 0,
            "error": str(e)
        }

@router.get("/users/{user_id}/activity")
def get_user_activity(
    user_id: str,
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get activity for a specific user"""
    try:
        # Check if user exists and has permission
        if current_user.role != "admin" and current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Permission denied")
        
        # Get user details
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user activities
        activities = db.query(AuditEvent).filter(
            AuditEvent.actor_user_id == user_id
        ).order_by(AuditEvent.created_at.desc()).limit(limit).all()
        
        activity_list = []
        for activity in activities:
            activity_list.append({
                "id": activity.id,
                "event_type": activity.event_type,
                "institution_code": activity.institution_code,
                "certificate_hash": activity.certificate_hash,
                "payload": activity.payload,
                "created_at": activity.created_at.isoformat(),
                "severity": monitor._get_event_severity(activity.event_type)
            })
        
        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "institution_code": user.institution_code
            },
            "activity": activity_list,
            "total": len(activity_list)
        }
        
    except Exception as e:
        return {
            "user_id": user_id,
            "activity": [],
            "total": 0,
            "error": str(e)
        }

@router.get("/certificates/{certificate_hash}/history")
def get_certificate_history(
    certificate_hash: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get complete history for a certificate"""
    try:
        # Get certificate details
        cert = db.query(Certificate).filter(
            Certificate.certificate_hash == certificate_hash
        ).first()
        
        if not cert:
            raise HTTPException(status_code=404, detail="Certificate not found")
        
        # Check permission
        if (current_user.role != "admin" and 
            current_user.institution_code != cert.institution):
            raise HTTPException(status_code=403, detail="Permission denied")
        
        # Get all audit events for this certificate
        events = db.query(AuditEvent).filter(
            AuditEvent.certificate_hash == certificate_hash
        ).order_by(AuditEvent.created_at.asc()).all()
        
        history = []
        for event in events:
            # Get user details
            actor_user = db.query(User).filter(User.id == event.actor_user_id).first()
            
            history.append({
                "id": event.id,
                "event_type": event.event_type,
                "actor": {
                    "id": event.actor_user_id,
                    "username": actor_user.username if actor_user else "Unknown",
                    "role": event.actor_role
                },
                "institution_code": event.institution_code,
                "payload": event.payload,
                "created_at": event.created_at.isoformat()
            })
        
        return {
            "certificate": {
                "id": cert.id,
                "hash": cert.certificate_hash,
                "student_name": f"{cert.student_name} {cert.student_surname}".strip(),
                "student_id": cert.student_id,
                "institution": cert.institution,
                "status": cert.status,
                "blockchain_tx_id": cert.blockchain_tx_id,
                "created_at": cert.created_at.isoformat()
            },
            "history": history,
            "total_events": len(history)
        }
        
    except Exception as e:
        return {
            "certificate_hash": certificate_hash,
            "history": [],
            "total_events": 0,
            "error": str(e)
        }

@router.get("/real-time")
def get_real_time_activity(
    since: Optional[str] = Query(None, description="ISO datetime to get activity since"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get real-time activity since a specific time"""
    try:
        # Default to last 5 minutes if no time provided
        if not since:
            since = (datetime.utcnow() - timedelta(minutes=5)).isoformat()
        
        since_time = datetime.fromisoformat(since.replace('Z', '+00:00'))
        
        # Get recent activities
        activities = db.query(AuditEvent).filter(
            AuditEvent.created_at >= since_time
        ).order_by(AuditEvent.created_at.desc()).limit(limit).all()
        
        real_time_activity = []
        for activity in activities:
            # Get user details
            actor_user = db.query(User).filter(User.id == activity.actor_user_id).first()
            
            real_time_activity.append({
                "id": activity.id,
                "event_type": activity.event_type,
                "actor": {
                    "id": activity.actor_user_id,
                    "username": actor_user.username if actor_user else "Unknown",
                    "role": activity.actor_role
                },
                "institution_code": activity.institution_code,
                "certificate_hash": activity.certificate_hash,
                "payload": activity.payload,
                "created_at": activity.created_at.isoformat(),
                "severity": get_network_monitor(db)._get_event_severity(activity.event_type)
            })
        
        return {
            "activity": real_time_activity,
            "since": since,
            "total": len(real_time_activity),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        return {
            "activity": [],
            "since": since,
            "total": 0,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/statistics")
def get_network_statistics(
    time_range: int = Query(24, description="Hours to look back"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get comprehensive network statistics"""
    try:
        cutoff_time = datetime.utcnow() - timedelta(hours=time_range)
        
        # Get event statistics
        event_stats = db.query(
            AuditEvent.event_type,
            func.count(AuditEvent.id).label('count')
        ).filter(
            AuditEvent.created_at >= cutoff_time
        ).group_by(AuditEvent.event_type).all()
        
        # Get institution statistics
        institution_stats = db.query(
            AuditEvent.institution_code,
            func.count(AuditEvent.id).label('count')
        ).filter(
            AuditEvent.created_at >= cutoff_time,
            AuditEvent.institution_code.isnot(None)
        ).group_by(AuditEvent.institution_code).order_by(desc('count')).limit(10).all()
        
        # Get user statistics
        user_stats = db.query(
            AuditEvent.actor_user_id,
            func.count(AuditEvent.id).label('count')
        ).filter(
            AuditEvent.created_at >= cutoff_time
        ).group_by(AuditEvent.actor_user_id).order_by(desc('count')).limit(10).all()
        
        # Get hourly activity
        hourly_activity = db.query(
            func.date_trunc('hour', AuditEvent.created_at).label('hour'),
            func.count(AuditEvent.id).label('count')
        ).filter(
            AuditEvent.created_at >= cutoff_time
        ).group_by('hour').order_by('hour').all()
        
        return {
            "time_range_hours": time_range,
            "total_events": sum(stat.count for stat in event_stats),
            "event_breakdown": [
                {"event_type": stat.event_type, "count": stat.count}
                for stat in event_stats
            ],
            "top_institutions": [
                {"institution_code": stat.institution_code, "count": stat.count}
                for stat in institution_stats
            ],
            "top_users": [
                {"user_id": stat.actor_user_id, "count": stat.count}
                for stat in user_stats
            ],
            "hourly_activity": [
                {"hour": stat.hour.isoformat(), "count": stat.count}
                for stat in hourly_activity
            ]
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "time_range_hours": time_range
        }
