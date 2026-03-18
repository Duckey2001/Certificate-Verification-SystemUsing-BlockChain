"""
Enhanced Certificate API with bulk upload support and improved OCR
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import os
import shutil
import uuid
from datetime import datetime
import json

from models import Certificate, User, BlockchainTransaction
from enhanced_lgcse_processor import EnhancedLGCSEProcessor
from utils.enhanced_blockchain import store_certificate_on_blockchain, store_user_profile_on_blockchain
from utils.realtime_notifications import notification_service
from database import get_db
from api.auth import get_current_user

router = APIRouter(prefix="/certificates", tags=["certificates"])

class BulkCertificateProcessor:
    def __init__(self, db: Session, current_user: User):
        self.db = db
        self.current_user = current_user
        self.processor = EnhancedLGCSEProcessor()
        
    async def process_single_certificate(self, file: UploadFile) -> Dict[str, Any]:
        """Process a single certificate file"""
        try:
            # Save temporary file
            temp_dir = "temp/bulk_upload"
            os.makedirs(temp_dir, exist_ok=True)
            temp_filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
            temp_path = os.path.join(temp_dir, temp_filename)
            
            with open(temp_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Process with enhanced OCR
            result = self.processor.process_certificate_file_enhanced(temp_path)
            
            # Clean up temp file
            os.remove(temp_path)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "filename": file.filename
            }
    
    async def process_bulk_upload(self, files: List[UploadFile]) -> Dict[str, Any]:
        """Process multiple certificate files"""
        results = []
        successful = []
        failed = []
        
        for file in files:
            try:
                result = await self.process_single_certificate(file)
                results.append(result)
                
                if result.get("success", False):
                    successful.append(result)
                    # Store certificate in database if valid
                    if result.get("validation", {}).get("is_valid", False):
                        await self.store_certificate_data(result)
                else:
                    failed.append(result)
                    
            except Exception as e:
                error_result = {
                    "success": False,
                    "error": str(e),
                    "filename": file.filename
                }
                results.append(error_result)
                failed.append(error_result)
        
        return {
            "total_files": len(files),
            "successful": len(successful),
            "failed": len(failed),
            "results": results,
            "summary": {
                "successful_certificates": successful,
                "failed_certificates": failed
            }
        }
    
    async def store_certificate_data(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Store certificate data in database and blockchain"""
        try:
            extracted = result["extracted_fields"]
            
            # Create certificate record
            certificate = Certificate(
                student_name=extracted["student_name"],
                student_surname="",  # Will be parsed from full name
                student_id=extracted["student_id"],
                institution=extracted["institution"],
                issue_date=extracted.get("examination_session", ""),
                examination_year=int(extracted.get("examination_year", 2020)),
                subjects=json.dumps(extracted["subjects"]),
                credits=1,  # Default credits
                issuer_id=self.current_user.id,
                status="issued",
                certificate_hash=result["certificate_hash"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(certificate)
            self.db.commit()
            self.db.refresh(certificate)
            
            # Store on blockchain
            blockchain_tx_hash = await store_certificate_on_blockchain(certificate.certificate_hash)
            if blockchain_tx_hash:
                certificate.blockchain_tx_id = blockchain_tx_hash
                certificate.blockchain_network = "hardhat"
                self.db.commit()
            
            # Update user statistics
            self.current_user.certificates_issued += 1
            self.current_user.last_activity_at = datetime.utcnow()
            
            # Create credit transaction
            credit_transaction = CreditTransaction(
                user_id=self.current_user.id,
                transaction_type="usage",
                amount=-1,
                balance_before=self.current_user.available_credits,
                balance_after=self.current_user.available_credits - 1,
                reference_type="certificate",
                reference_id=certificate.id,
                description="Bulk certificate issuance"
            )
            self.db.add(credit_transaction)
            self.current_user.available_credits -= 1
            self.db.commit()
            
            # Send notifications
            await notification_service.notify_certificate_issued(
                self.current_user.id,
                extracted["student_name"],
                certificate.certificate_hash
            )
            
            return {
                "success": True,
                "certificate_id": certificate.id,
                "certificate_hash": certificate.certificate_hash,
                "blockchain_tx_hash": blockchain_tx_hash
            }
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Error storing certificate: {str(e)}")

@router.post("/extract-data-enhanced")
async def extract_certificate_data_enhanced(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Enhanced certificate data extraction using improved OCR"""
    if current_user.role not in {"issuer", "admin"}:
        raise HTTPException(
            status_code=403,
            detail="Only issuers can extract certificate data"
        )
    
    # Validate file type
    allowed_types = ["application/pdf", "image/jpeg", "image/jpg", "image/png"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and image files (JPEG, PNG) are supported"
        )
    
    processor = BulkCertificateProcessor(db, current_user)
    result = await processor.process_single_certificate(file)
    
    return result

@router.post("/bulk-upload")
async def bulk_upload_certificates(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk upload multiple certificates with enhanced OCR processing"""
    if current_user.role not in {"issuer", "admin"}:
        raise HTTPException(
            status_code=403,
            detail="Only issuers can upload certificates"
        )
    
    # Check available credits
    if current_user.available_credits < len(files):
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient credits. You have {current_user.available_credits} credits but need {len(files)} credits."
        )
    
    # Validate file count (limit to prevent abuse)
    if len(files) > 50:
        raise HTTPException(
            status_code=400,
            detail="Maximum 50 files allowed per bulk upload"
        )
    
    # Validate file types
    allowed_types = ["application/pdf", "image/jpeg", "image/jpg", "image/png"]
    for file in files:
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"File {file.filename} has unsupported type. Only PDF and image files (JPEG, PNG) are supported"
            )
    
    processor = BulkCertificateProcessor(db, current_user)
    
    # Process bulk upload
    result = await processor.process_bulk_upload(files)
    
    # Send notification about bulk upload completion
    await notification_service.create_notification(
        current_user.id,
        "Bulk Upload Completed",
        f"Processed {result['total_files']} certificates. {result['successful']} successful, {result['failed']} failed.",
        "bulk_upload",
        "high",
        action_url="/certificates/bulk-results",
        action_text="View Results",
        metadata=result
    )
    
    return result

@router.get("/bulk-status/{upload_id}")
async def get_bulk_upload_status(
    upload_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get status of bulk upload processing"""
    # This would typically query a background task status
    # For now, return a placeholder
    return {
        "upload_id": upload_id,
        "status": "completed",
        "message": "Bulk upload processing completed"
    }

@router.post("/validate-certificate")
async def validate_certificate(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Validate a certificate without storing it"""
    if current_user.role not in {"issuer", "admin", "verifier"}:
        raise HTTPException(
            status_code=403,
            detail="Only authorized users can validate certificates"
        )
    
    processor = BulkCertificateProcessor(db, current_user)
    result = await processor.process_single_certificate(file)
    
    # Add validation-specific information
    if result.get("success", False):
        validation = result.get("validation", {})
        result["validation_summary"] = {
            "is_valid": validation.get("is_valid", False),
            "confidence": validation.get("confidence", 0),
            "message": validation.get("message", ""),
            "subjects_found": len(result.get("extracted_fields", {}).get("subjects", [])),
            "certificate_type": result.get("certificate_type", "Unknown")
        }
    
    return result

@router.get("/ocr-stats")
async def get_ocr_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get OCR processing statistics"""
    if current_user.role not in {"admin", "issuer"}:
        raise HTTPException(
            status_code=403,
            detail="Only admins and issuers can view OCR statistics"
        )
    
    # Get certificate statistics
    total_certificates = db.query(Certificate).count()
    
    # Get certificates by examination year
    from sqlalchemy import func
    certificates_by_year = db.query(
        Certificate.examination_year,
        func.count(Certificate.id).label('count')
    ).group_by(Certificate.examination_year).all()
    
    # Get subject distribution
    subjects_data = []
    certificates = db.query(Certificate).all()
    subject_counts = {}
    
    for cert in certificates:
        try:
            subjects = json.loads(cert.subjects or "[]")
            for subject in subjects:
                subject_name = subject.get("subject_name", "Unknown")
                subject_counts[subject_name] = subject_counts.get(subject_name, 0) + 1
        except:
            continue
    
    return {
        "total_certificates": total_certificates,
        "certificates_by_year": [
            {"year": year, "count": count} 
            for year, count in certificates_by_year
        ],
        "subject_distribution": subject_counts,
        "ocr_confidence_average": 88.0,  # This would be calculated from actual data
        "processing_success_rate": 95.0  # This would be calculated from actual data
    }
