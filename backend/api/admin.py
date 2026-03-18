from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from database import get_db
from models import User, Certificate, VerificationRequest, Payment
from api.enhanced_auth import get_current_user_enhanced

router = APIRouter(prefix="/api/admin", tags=["admin"])

@router.get("/system-stats")
async def get_system_stats(
    current_user: User = Depends(get_current_user_enhanced),
    db: Session = Depends(get_db)
):
    """Get system statistics for admin dashboard"""
    
    # Check if user is admin
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Total counts
        total_users = db.query(User).count()
        total_certificates = db.query(Certificate).count()
        total_verifications = db.query(VerificationRequest).count()
        total_payments = db.query(Payment).count()
        
        # Recent activity (last 24 hours)
        day_ago = datetime.utcnow() - timedelta(days=1)
        recent_users = db.query(User).filter(User.created_at > day_ago).count()
        recent_certs = db.query(Certificate).filter(Certificate.created_at > day_ago).count()
        
        # Active users (logged in last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        from models import LoginActivity
        active_users = db.query(LoginActivity).filter(
            LoginActivity.created_at > week_ago,
            LoginActivity.status == "success"
        ).distinct(LoginActivity.user_id).count()
        
        # Pending approvals
        pending_approvals = db.query(User).filter(User.role == "pending_issuer").count()
        
        # Revenue
        month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        revenue_month = db.query(func.sum(Payment.amount)).filter(
            Payment.created_at >= month_start,
            Payment.status == "confirmed"
        ).scalar() or 0.0
        
        return {
            "total_users": total_users,
            "total_certificates": total_certificates,
            "total_verifications": total_verifications,
            "total_payments": total_payments,
            "recent_users": recent_users,
            "recent_certificates": recent_certs,
            "active_users": active_users,
            "pending_approvals": pending_approvals,
            "revenue_month": float(revenue_month),
            "revenue_today": 0.0,  # You can implement this later
            "success_rate": 95.5  # Mock value
        }
    except Exception as e:
        print(f"Error fetching system stats: {e}")
        return {
            "total_users": 0,
            "total_certificates": 0,
            "total_verifications": 0,
            "total_payments": 0,
            "recent_users": 0,
            "recent_certificates": 0,
            "active_users": 0,
            "pending_approvals": 0,
            "revenue_month": 0.0,
            "revenue_today": 0.0,
            "success_rate": 0.0
        }

@router.get("/system-health")
async def get_system_health(
    current_user: User = Depends(get_current_user_enhanced)
):
    """Get system health status"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return {
        "status": "healthy",
        "database": "connected",
        "api": "operational",
        "blockchain": "connected",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@router.get("/dashboard-charts")
async def get_dashboard_charts(
    current_user: User = Depends(get_current_user_enhanced),
    days: int = 7
):
    """Get chart data for admin dashboard"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Return mock chart data for now
    return {
        "activity": {
            "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "datasets": [
                {
                    "label": "Certificates",
                    "data": [12, 19, 3, 5, 2, 3, 9],
                    "backgroundColor": "rgba(59, 130, 246, 0.2)",
                    "borderColor": "rgb(59, 130, 246)"
                },
                {
                    "label": "Verifications",
                    "data": [8, 15, 7, 12, 9, 5, 11],
                    "backgroundColor": "rgba(16, 185, 129, 0.2)",
                    "borderColor": "rgb(16, 185, 129)"
                }
            ]
        },
        "payments": {
            "labels": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
            "datasets": [
                {
                    "label": "Amount (LSL)",
                    "data": [250, 450, 200, 380, 520, 180, 430],
                    "backgroundColor": "rgba(245, 158, 11, 0.2)",
                    "borderColor": "rgb(245, 158, 11)"
                }
            ]
        },
        "blockchain": {
            "blocks": 1250,
            "transactions": 3450,
            "nodes": 5
        }
    }

@router.get("/recent-alerts")
async def get_recent_alerts(
    current_user: User = Depends(get_current_user_enhanced)
):
    """Get recent system alerts"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return [
        {
            "id": "1",
            "message": "System started successfully",
            "severity": "info",
            "timestamp": datetime.utcnow().isoformat(),
            "source": "system"
        }
    ]

@router.get("/notifications")
async def get_notifications(
    current_user: User = Depends(get_current_user_enhanced)
):
    """Get user notifications"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return []

@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(get_current_user_enhanced)
):
    """Mark notification as read"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return {"status": "success"}

@router.post("/notifications/read-all")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user_enhanced)
):
    """Mark all notifications as read"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return {"status": "success"}

@router.get("/pending-users")
async def get_pending_users(
    current_user: User = Depends(get_current_user_enhanced),
    db: Session = Depends(get_db)
):
    """Get users pending approval"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    pending = db.query(User).filter(User.role == "pending_issuer").limit(10).all()
    
    return [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "institution": user.institution,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }
        for user in pending
    ]

@router.get("/system-logs")
async def get_system_logs(
    current_user: User = Depends(get_current_user_enhanced),
    db: Session = Depends(get_db),
    limit: int = 50,
    page: int = 1
):
    """Get system logs for admin"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Mock system logs data for now
        # In a real implementation, you would query from a logs table
        mock_logs = [
            {
                "id": 1,
                "event_type": "certificate_verified",
                "actor_username": current_user.username,
                "actor_role": current_user.role,
                "institution_code": "DEMO",
                "certificate_hash": "0x1234567890abcdef",
                "created_at": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
                "severity": "low",
                "payload": {
                    "student_name": "John Doe",
                    "certificate_id": "CERT001"
                }
            },
            {
                "id": 2,
                "event_type": "certificate_issued",
                "actor_username": "system",
                "actor_role": "system",
                "institution_code": "DEMO",
                "certificate_hash": "0xabcdef1234567890",
                "created_at": (datetime.utcnow() - timedelta(hours=4)).isoformat(),
                "severity": "low",
                "payload": {
                    "student_name": "Jane Smith",
                    "certificate_id": "CERT002"
                }
            },
            {
                "id": 3,
                "event_type": "payment_confirmed",
                "actor_username": "system",
                "actor_role": "system",
                "institution_code": None,
                "certificate_hash": None,
                "created_at": (datetime.utcnow() - timedelta(hours=6)).isoformat(),
                "severity": "medium",
                "payload": {
                    "amount": 25.00,
                    "payment_method": "mpesa"
                }
            },
            {
                "id": 4,
                "event_type": "user_registered",
                "actor_username": "new_user",
                "actor_role": "pending_issuer",
                "institution_code": "SCHOOL1",
                "certificate_hash": None,
                "created_at": (datetime.utcnow() - timedelta(hours=8)).isoformat(),
                "severity": "low",
                "payload": {
                    "email": "newuser@example.com"
                }
            },
            {
                "id": 5,
                "event_type": "bulk_upload",
                "actor_username": current_user.username,
                "actor_role": current_user.role,
                "institution_code": "DEMO",
                "certificate_hash": None,
                "created_at": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                "severity": "medium",
                "payload": {
                    "count": 50,
                    "file": "certificates_batch_1.csv"
                }
            }
        ]
        
        # Apply pagination
        start = (page - 1) * limit
        end = start + limit
        paginated_logs = mock_logs[start:end]
        
        return {
            "logs": paginated_logs,
            "total": len(mock_logs),
            "page": page,
            "limit": limit,
            "pages": (len(mock_logs) + limit - 1) // limit
        }
    except Exception as e:
        print(f"Error fetching system logs: {e}")
        return {
            "logs": [],
            "total": 0,
            "page": page,
            "limit": limit,
            "pages": 0
        }

@router.get("/institutions")
async def get_institutions(
    current_user: User = Depends(get_current_user_enhanced),
    db: Session = Depends(get_db)
):
    """Get all institutions for admin"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Get unique institutions from users
        institutions = db.query(User.institution).filter(
            User.institution.isnot(None),
            User.institution != ""
        ).distinct().all()
        
        # Format institution data
        institution_list = []
        for i, inst_name in enumerate(institutions):
            inst_name = inst_name[0] if isinstance(inst_name, tuple) else inst_name
            if inst_name:
                # Get user count for this institution
                user_count = db.query(User).filter(User.institution == inst_name).count()
                
                # Get certificate count for this institution
                cert_count = db.query(Certificate).filter(Certificate.institution == inst_name).count()
                
                institution_list.append({
                    "id": i + 1,
                    "name": inst_name,
                    "code": inst_name.upper().replace(" ", "_")[:8],
                    "user_count": user_count,
                    "certificate_count": cert_count,
                    "status": "active",
                    "created_at": datetime.utcnow().isoformat()
                })
        
        # Add some demo institutions if none exist
        if not institution_list:
            institution_list = [
                {
                    "id": 1,
                    "name": "Demo High School",
                    "code": "DEMO_HS",
                    "user_count": 5,
                    "certificate_count": 120,
                    "status": "active",
                    "created_at": datetime.utcnow().isoformat()
                },
                {
                    "id": 2,
                    "name": "Test Academy",
                    "code": "TEST_AC",
                    "user_count": 3,
                    "certificate_count": 85,
                    "status": "active",
                    "created_at": datetime.utcnow().isoformat()
                }
            ]
        
        return institution_list
    except Exception as e:
        print(f"Error fetching institutions: {e}")
        return []

@router.get("/export")
async def export_data(
    tab: str,
    format: str = 'csv',
    current_user: User = Depends(get_current_user_enhanced)
):
    """Export data"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return {"message": f"Exporting {tab} as {format}"}