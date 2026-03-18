#!/usr/bin/env python3
"""
Enhanced Statistics API for Certificate Processing
Provides comprehensive processing metrics and analytics
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

from models import Certificate, User, AuditEvent, Payment
from database import get_db
from auth import get_current_user
from utils.realtime_processing import realtime_service

router = APIRouter(prefix="/statistics", tags=["statistics"])

@router.get("/processing-overview")
async def get_processing_overview(
    days: int = Query(30, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive processing overview statistics"""
    
    if current_user.role not in {"admin", "issuer"}:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get certificate processing statistics
        cert_stats = db.query(
            func.count(Certificate.id).label('total_certificates'),
            func.count(func.distinct(Certificate.issuer_id)).label('unique_issuers'),
            func.avg(Certificate.credits).label('avg_credits'),
            func.count(func.distinct(Certificate.institution)).label('unique_institutions')
        ).filter(
            Certificate.created_at >= start_date
        ).first()
        
        # Get processing trends (daily)
        daily_stats = db.query(
            func.date(Certificate.created_at).label('date'),
            func.count(Certificate.id).label('count'),
            func.avg(Certificate.credits).label('avg_credits')
        ).filter(
            Certificate.created_at >= start_date
        ).group_by(
            func.date(Certificate.created_at)
        ).order_by('date').all()
        
        # Get top issuers
        top_issuers = db.query(
            User.username,
            func.count(Certificate.id).label('certificates_issued')
        ).join(
            Certificate, User.id == Certificate.issuer_id
        ).filter(
            Certificate.created_at >= start_date
        ).group_by(
            User.id, User.username
        ).order_by(
            desc('certificates_issued')
        ).limit(10).all()
        
        # Get blockchain statistics
        blockchain_stats = db.query(
            func.count(Certificate.id).label('total_on_blockchain'),
            func.count(func.distinct(Certificate.blockchain_network)).label('networks_used')
        ).filter(
            and_(
                Certificate.created_at >= start_date,
                Certificate.blockchain_tx_id.isnot(None)
            )
        ).first()
        
        # Get real-time stats from service
        realtime_stats = await realtime_service.get_real_time_stats()
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "overview": {
                "total_certificates": cert_stats.total_certificates or 0,
                "unique_issuers": cert_stats.unique_issuers or 0,
                "unique_institutions": cert_stats.unique_institutions or 0,
                "average_credits_per_certificate": float(cert_stats.avg_credits or 0),
                "certificates_on_blockchain": blockchain_stats.total_on_blockchain or 0,
                "blockchain_networks_used": blockchain_stats.networks_used or 0
            },
            "daily_trends": [
                {
                    "date": stat.date.isoformat(),
                    "certificates_processed": stat.count,
                    "average_credits": float(stat.avg_credits or 0)
                }
                for stat in daily_stats
            ],
            "top_issuers": [
                {
                    "username": issuer.username,
                    "certificates_issued": issuer.certificates_issued
                }
                for issuer in top_issuers
            ],
            "realtime_stats": realtime_stats,
            "processing_methods": {
                "enhanced_ocr_processed": realtime_stats.get("global_stats", {}).get("enhanced_processed", 0),
                "fallback_ocr_processed": realtime_stats.get("global_stats", {}).get("fallback_processed", 0),
                "average_confidence": realtime_stats.get("global_stats", {}).get("average_confidence", 0.0)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch processing overview: {str(e)}")

@router.get("/ocr-performance")
async def get_ocr_performance_stats(
    days: int = Query(7, le=90, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed OCR performance statistics"""
    
    if current_user.role not in {"admin", "issuer"}:
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get certificates with extracted data for OCR analysis
        certificates = db.query(Certificate).filter(
            Certificate.created_at >= start_date,
            Certificate.extracted_data.isnot(None)
        ).all()
        
        # Analyze OCR performance
        enhanced_count = 0
        fallback_count = 0
        confidence_scores = []
        processing_times = []
        subject_extraction_stats = {
            "total_subjects": 0,
            "successful_extractions": 0,
            "average_subjects_per_certificate": 0
        }
        
        for cert in certificates:
            extracted_data = cert.extracted_data or {}
            
            # Determine processing method
            processing_method = extracted_data.get("processing_method", "unknown")
            if processing_method == "enhanced_ocr":
                enhanced_count += 1
            elif processing_method == "fallback_ocr":
                fallback_count += 1
            
            # Extract confidence scores
            validation = extracted_data.get("validation", {})
            if validation.get("confidence"):
                confidence_scores.append(validation["confidence"])
            
            # Analyze subject extraction
            enhanced_data = extracted_data.get("enhanced_data", {})
            subjects = enhanced_data.get("subjects", [])
            if subjects:
                subject_extraction_stats["total_subjects"] += len(subjects)
                subject_extraction_stats["successful_extractions"] += 1
        
        # Calculate averages
        total_processed = enhanced_count + fallback_count
        if subject_extraction_stats["successful_extractions"] > 0:
            subject_extraction_stats["average_subjects_per_certificate"] = (
                subject_extraction_stats["total_subjects"] / subject_extraction_stats["successful_extractions"]
            )
        
        # Get real-time OCR stats
        realtime_stats = await realtime_service.get_real_time_stats()
        global_stats = realtime_stats.get("global_stats", {})
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "processing_methods": {
                "enhanced_ocr": {
                    "count": enhanced_count,
                    "percentage": (enhanced_count / total_processed * 100) if total_processed > 0 else 0
                },
                "fallback_ocr": {
                    "count": fallback_count,
                    "percentage": (fallback_count / total_processed * 100) if total_processed > 0 else 0
                }
            },
            "confidence_analysis": {
                "average_confidence": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0,
                "highest_confidence": max(confidence_scores) if confidence_scores else 0,
                "lowest_confidence": min(confidence_scores) if confidence_scores else 0,
                "total_samples": len(confidence_scores)
            },
            "subject_extraction": subject_extraction_stats,
            "realtime_performance": {
                "total_processed": global_stats.get("total_processed", 0),
                "successful": global_stats.get("successful", 0),
                "failed": global_stats.get("failed", 0),
                "duplicates": global_stats.get("duplicates_found", 0),
                "average_processing_confidence": global_stats.get("average_confidence", 0),
                "enhanced_processed": global_stats.get("enhanced_processed", 0),
                "fallback_processed": global_stats.get("fallback_processed", 0)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch OCR performance: {str(e)}")

@router.get("/issuer-performance")
async def get_issuer_performance(
    issuer_id: Optional[int] = Query(None, description="Specific issuer ID (admin only)"),
    days: int = Query(30, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get issuer-specific performance statistics"""
    
    # Non-admin users can only see their own stats
    if current_user.role != "admin":
        issuer_id = current_user.id
    elif issuer_id is None:
        raise HTTPException(status_code=400, detail="Issuer ID required for admin users")
    
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get issuer information
        issuer = db.query(User).filter(User.id == issuer_id).first()
        if not issuer:
            raise HTTPException(status_code=404, detail="Issuer not found")
        
        # Get issuer's certificate statistics
        cert_stats = db.query(
            func.count(Certificate.id).label('total_certificates'),
            func.sum(Certificate.credits).label('total_credits'),
            func.avg(Certificate.credits).label('avg_credits'),
            func.count(func.distinct(Certificate.institution)).label('unique_institutions')
        ).filter(
            and_(
                Certificate.issuer_id == issuer_id,
                Certificate.created_at >= start_date
            )
        ).first()
        
        # Get daily processing trends for this issuer
        daily_stats = db.query(
            func.date(Certificate.created_at).label('date'),
            func.count(Certificate.id).label('count'),
            func.sum(Certificate.credits).label('total_credits')
        ).filter(
            and_(
                Certificate.issuer_id == issuer_id,
                Certificate.created_at >= start_date
            )
        ).group_by(
            func.date(Certificate.created_at)
        ).order_by('date').all()
        
        # Get OCR method breakdown for this issuer
        issuer_certs = db.query(Certificate).filter(
            and_(
                Certificate.issuer_id == issuer_id,
                Certificate.created_at >= start_date,
                Certificate.extracted_data.isnot(None)
            )
        ).all()
        
        enhanced_count = 0
        fallback_count = 0
        confidence_scores = []
        
        for cert in issuer_certs:
            extracted_data = cert.extracted_data or {}
            processing_method = extracted_data.get("processing_method", "unknown")
            
            if processing_method == "enhanced_ocr":
                enhanced_count += 1
            elif processing_method == "fallback_ocr":
                fallback_count += 1
            
            validation = extracted_data.get("validation", {})
            if validation.get("confidence"):
                confidence_scores.append(validation["confidence"])
        
        # Get institution breakdown
        institution_stats = db.query(
            Certificate.institution,
            func.count(Certificate.id).label('certificate_count'),
            func.sum(Certificate.credits).label('total_credits')
        ).filter(
            and_(
                Certificate.issuer_id == issuer_id,
                Certificate.created_at >= start_date
            )
        ).group_by(
            Certificate.institution
        ).order_by(
            desc('certificate_count')
        ).limit(10).all()
        
        return {
            "issuer_info": {
                "id": issuer.id,
                "username": issuer.username,
                "role": issuer.role,
                "certificates_issued": issuer.certificates_issued
            },
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            },
            "performance_summary": {
                "total_certificates": cert_stats.total_certificates or 0,
                "total_credits": cert_stats.total_credits or 0,
                "average_credits_per_certificate": float(cert_stats.avg_credits or 0),
                "unique_institutions": cert_stats.unique_institutions or 0
            },
            "processing_methods": {
                "enhanced_ocr": enhanced_count,
                "fallback_ocr": fallback_count,
                "enhanced_percentage": (enhanced_count / (enhanced_count + fallback_count) * 100) if (enhanced_count + fallback_count) > 0 else 0
            },
            "confidence_analysis": {
                "average_confidence": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0,
                "total_certificates_with_confidence": len(confidence_scores)
            },
            "daily_trends": [
                {
                    "date": stat.date.isoformat(),
                    "certificates_processed": stat.count,
                    "total_credits": stat.total_credits or 0
                }
                for stat in daily_stats
            ],
            "top_institutions": [
                {
                    "institution": stat.institution or "Unknown",
                    "certificate_count": stat.certificate_count,
                    "total_credits": stat.total_credits or 0
                }
                for stat in institution_stats
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch issuer performance: {str(e)}")

@router.get("/realtime-session")
async def get_realtime_session_stats(
    session_id: str = Query(..., description="Real-time processing session ID"),
    current_user: User = Depends(get_current_user)
):
    """Get statistics for a specific real-time processing session"""
    
    if current_user.role not in {"admin", "issuer"}:
        raise HTTPException(status_code=403, detail="Access denied")
    
    session_summary = realtime_service.get_session_summary(session_id)
    if not session_summary:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session_summary

@router.get("/system-health")
async def get_system_health_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get system health and performance statistics"""
    
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Get database statistics
        db_stats = {
            "total_certificates": db.query(func.count(Certificate.id)).scalar(),
            "total_users": db.query(func.count(User.id)).scalar(),
            "certificates_today": db.query(func.count(Certificate.id)).filter(
                func.date(Certificate.created_at) == func.current_date()
            ).scalar(),
            "active_issuers": db.query(func.count(func.distinct(Certificate.issuer_id))).scalar()
        }
        
        # Get blockchain health
        blockchain_health = {
            "certificates_on_blockchain": db.query(func.count(Certificate.id)).filter(
                Certificate.blockchain_tx_id.isnot(None)
            ).scalar(),
            "blockchain_success_rate": 0  # Would need to calculate from audit logs
        }
        
        # Get real-time service health
        realtime_stats = await realtime_service.get_real_time_stats()
        global_stats = realtime_stats.get("global_stats", {})
        
        service_health = {
            "active_connections": len(realtime_service.active_connections),
            "total_processed_realtime": global_stats.get("total_processed", 0),
            "average_confidence": global_stats.get("average_confidence", 0),
            "enhanced_ocr_usage": (global_stats.get("enhanced_processed", 0) / max(1, global_stats.get("total_processed", 1))) * 100
        }
        
        # Calculate overall health score
        health_score = 0
        if db_stats["total_certificates"] > 0:
            health_score += 25
        if blockchain_health["certificates_on_blockchain"] > 0:
            health_score += 25
        if service_health["average_confidence"] > 70:
            health_score += 25
        if service_health["enhanced_ocr_usage"] > 50:
            health_score += 25
        
        return {
            "health_score": health_score,
            "database": db_stats,
            "blockchain": blockchain_health,
            "realtime_service": service_health,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch system health: {str(e)}")
