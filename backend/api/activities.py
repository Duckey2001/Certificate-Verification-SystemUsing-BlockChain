from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, timedelta

from database import get_db
from models import User, Certificate
from auth import get_current_active_user

router = APIRouter(prefix="/api/activities", tags=["activities"])

@router.get("/recent")
async def get_recent_activities(
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get recent certificate activities for the dashboard
    """
    try:
        # Get recent certificates from database
        certificates = db.query(Certificate).order_by(
            Certificate.created_at.desc()
        ).limit(limit).all()
        
        activities = []
        for cert in certificates:
            # Determine status based on certificate data
            status = "issued" if cert.status == "verified" else "pending"
            
            activity = {
                "id": cert.id,
                "student_name": cert.student_name,
                "certificate_number": cert.certificate_hash[:16] if cert.certificate_hash else f"CERT{cert.id:06d}",
                "issue_date": cert.created_at.strftime("%Y-%m-%d") if cert.created_at else datetime.now().strftime("%Y-%m-%d"),
                "status": status,
                "institution": cert.institution or "Unknown Institution",
                "examination_year": cert.examination_year
            }
            activities.append(activity)
        
        # Return empty array if no certificates found (no mock data)
        return activities
        
    except Exception as e:
        # Log error and return empty array
        print(f"Error in get_recent_activities: {e}")
        return []

@router.get("/stats")
async def get_activity_stats(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get activity statistics for dashboard
    """
    try:
        total_certificates = db.query(Certificate).count()
        pending_certificates = db.query(Certificate).filter(Certificate.status == "pending_verification").count()
        verified_certificates = db.query(Certificate).filter(Certificate.status == "verified").count()
        
        # Get recent activity (last 7 days)
        seven_days_ago = datetime.now() - timedelta(days=7)
        recent_activity = db.query(Certificate).filter(
            Certificate.created_at >= seven_days_ago
        ).count()
        
        return {
            "total_certificates": total_certificates,
            "pending_certificates": pending_certificates,
            "verified_certificates": verified_certificates,
            "recent_activity": recent_activity,
            "verification_rate": round((verified_certificates / total_certificates * 100) if total_certificates > 0 else 0, 2)
        }
        
    except Exception as e:
        # Log error and return zero stats
        print(f"Error in get_activity_stats: {e}")
        return {
            "total_certificates": 0,
            "pending_certificates": 0,
            "verified_certificates": 0,
            "recent_activity": 0,
            "verification_rate": 0.0
        }
