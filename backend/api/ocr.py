from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import desc
import os
import tempfile
import json
import hashlib
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
import traceback
import logging
import re

from database import get_db
from models import User, Certificate, OCRHistory, Payment
from enhanced_lgcse_processor import EnhancedLGCSEProcessor
from multi_ocr_processor import MultiOCRProcessor
from auth import get_current_active_user

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ocr", tags=["ocr"])

# Initialize OCR processors
try:
    ocr_processor = EnhancedLGCSEProcessor()
    multi_ocr_processor = MultiOCRProcessor()
    logger.info("OCR processors initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize OCR processors: {str(e)}")
    ocr_processor = None
    multi_ocr_processor = None

@router.post("/process-certificate")
async def process_certificate(
    file: UploadFile = File(...),
    user_id: Optional[str] = Form(None),
    institution: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Process certificate with OCR and extract data
    """
    temp_file_path = None
    start_time = time.time()
    
    try:
        logger.info(f"Processing certificate: {file.filename} for user: {current_user.username}")
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf']
        if file.content_type not in allowed_types:
            raise HTTPException(
                status_code=400, 
                detail=f"File must be an image (JPEG, PNG) or PDF. Got: {file.content_type}"
            )
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # Check file size (max 10MB)
        if file_size > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
        
        # Determine file extension
        file_extension = '.pdf' if file.content_type == 'application/pdf' else '.jpg'
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        logger.info(f"Saved temporary file: {temp_file_path} (size: {file_size} bytes)")
        
        # Initialize result structure
        final_data = {
            'student_name': None,
            'student_surname': None,
            'student_id': None,
            'institution': institution or current_user.institution,
            'issue_date': None,
            'certificate_number': None,
            'certificate_hash': None,
            'examination_year': None,
            'examination_session': None,
            'centre_number': None,
            'candidate_number': None,
            'subjects': [],
            'confidence': 0,
            'extracted_text': '',
            'warnings': []
        }
        
        api_calls_made = []
        extracted_text = ""
        best_confidence = 0
        ocr_engine_used = "tesseract"
        multi_result = {}
        
        # Process with multi-OCR if available
        if multi_ocr_processor and hasattr(multi_ocr_processor, 'process_image_with_all_apis'):
            try:
                logger.info("Starting multi-OCR processing")
                multi_result = multi_ocr_processor.process_image_with_all_apis(temp_file_path, prefer_api='auto')
                logger.info(f"Multi-OCR processing complete")
                
                # Track API calls
                api_calls_made = multi_result.get('apis_used', [])
                
                # Get best result
                best_result = multi_result.get('best_result', {})
                if best_result:
                    extracted_text = best_result.get('text', '')
                    best_confidence = best_result.get('confidence', 0)
                    ocr_engine_used = best_result.get('api_name', 'tesseract')
                    logger.info(f"Best OCR result from {ocr_engine_used} with confidence {best_confidence}")
            except Exception as e:
                logger.error(f"Multi-OCR processing failed: {str(e)}")
                # Try basic OCR as fallback
                try:
                    if ocr_processor and hasattr(ocr_processor, 'extract_text_from_image'):
                        extracted_text = ocr_processor.extract_text_from_image(temp_file_path)
                        best_confidence = 50  # Default confidence for basic OCR
                        ocr_engine_used = "basic_tesseract"
                        logger.info("Basic OCR fallback successful")
                except Exception as e2:
                    logger.error(f"Basic OCR also failed: {str(e2)}")
        
        # Process with enhanced LGCSE processor
        if ocr_processor:
            try:
                logger.info("Starting enhanced LGCSE processing")
                if hasattr(ocr_processor, 'process_certificate_file_enhanced'):
                    result = ocr_processor.process_certificate_file_enhanced(temp_file_path)
                    
                    if result:
                        logger.info("Enhanced LGCSE processing complete")
                        
                        # Extract fields from result
                        extracted_fields = result.get('extracted_fields', {})
                        lgcse_data = result.get('lgcse_specific', {}).get('parsed_data', {})
                        
                        # Merge data with priority to LGCSE data for LGCSE-specific fields
                        final_data['student_name'] = (
                            lgcse_data.get('student_name') or 
                            extracted_fields.get('student_name')
                        )
                        
                        final_data['student_surname'] = (
                            lgcse_data.get('student_surname') or 
                            extracted_fields.get('student_surname')
                        )
                        
                        final_data['student_id'] = (
                            lgcse_data.get('student_id') or 
                            lgcse_data.get('candidate_number') or
                            extracted_fields.get('student_id')
                        )
                        
                        final_data['institution'] = (
                            lgcse_data.get('institution') or 
                            extracted_fields.get('institution') or 
                            final_data['institution']
                        )
                        
                        final_data['issue_date'] = (
                            lgcse_data.get('issue_date') or 
                            extracted_fields.get('issue_date')
                        )
                        
                        final_data['certificate_number'] = (
                            lgcse_data.get('certificate_number') or 
                            extracted_fields.get('certificate_number')
                        )
                        
                        final_data['certificate_hash'] = (
                            lgcse_data.get('certificate_hash') or 
                            extracted_fields.get('certificate_hash')
                        )
                        
                        final_data['examination_year'] = lgcse_data.get('examination_year')
                        final_data['examination_session'] = lgcse_data.get('examination_session')
                        final_data['centre_number'] = lgcse_data.get('centre_number')
                        final_data['candidate_number'] = lgcse_data.get('candidate_number')
                        
                        # Get subjects - try multiple sources
                        subjects = []
                        if lgcse_data.get('subjects_grades'):
                            subjects = lgcse_data.get('subjects_grades', [])
                        elif extracted_fields.get('subjects'):
                            subjects = extracted_fields.get('subjects', [])
                        
                        if subjects:
                            final_data['subjects'] = subjects
                        
                        # Update confidence
                        result_confidence = result.get('confidence_score', 0)
                        if result_confidence > best_confidence:
                            best_confidence = result_confidence
                            ocr_engine_used = "enhanced_lgcse"
            except Exception as e:
                logger.error(f"Enhanced LGCSE processing failed: {str(e)}")
        
        # If no text extracted yet, try basic extraction
        if not extracted_text and ocr_processor and hasattr(ocr_processor, 'extract_text_from_image'):
            try:
                extracted_text = ocr_processor.extract_text_from_image(temp_file_path)
                logger.info("Basic text extraction successful")
            except Exception as e:
                logger.error(f"Basic text extraction failed: {str(e)}")
        
        final_data['extracted_text'] = extracted_text[:5000] if extracted_text else ""  # Limit text length
        
        # Try to extract certificate hash from text if not found
        if not final_data['certificate_hash'] and extracted_text:
            # Look for hash pattern (64 hex chars)
            hash_pattern = r'[0-9a-f]{64}'
            hash_matches = re.findall(hash_pattern, extracted_text.lower())
            if hash_matches:
                final_data['certificate_hash'] = hash_matches[0]
                logger.info(f"Extracted certificate hash from text: {final_data['certificate_hash'][:16]}...")
        
        # Try to extract subjects from text if not found
        if not final_data['subjects'] and extracted_text and ocr_processor:
            try:
                if hasattr(ocr_processor, 'extract_subjects_from_text'):
                    subjects = ocr_processor.extract_subjects_from_text(extracted_text)
                    if subjects:
                        final_data['subjects'] = subjects
                        logger.info(f"Extracted {len(subjects)} subjects from text")
            except Exception as e:
                logger.error(f"Subject extraction failed: {str(e)}")
        
        # Set confidence
        final_data['confidence'] = best_confidence
        
        # Generate certificate hash if still not found
        if not final_data['certificate_hash'] and final_data['student_name']:
            hash_input = f"{final_data['student_name']}{final_data.get('student_id', '')}{datetime.utcnow().isoformat()}"
            final_data['certificate_hash'] = hashlib.sha256(hash_input.encode()).hexdigest()
            logger.info(f"Generated certificate hash: {final_data['certificate_hash'][:16]}...")
        
        # Generate warnings
        warnings = []
        if best_confidence < 60:
            warnings.append(f"Low confidence ({best_confidence}%) in extracted data")
        if not final_data['student_name']:
            warnings.append("Student name not found")
        if not final_data.get('student_surname'):
            warnings.append("Student surname not found")
        if not final_data['certificate_hash']:
            warnings.append("Certificate hash not found")
        if not final_data['subjects']:
            warnings.append("No subjects found")
        elif len(final_data['subjects']) < 3:
            warnings.append(f"Few subjects detected ({len(final_data['subjects'])} subjects)")
        
        final_data['warnings'] = warnings
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Save OCR history to database
        try:
            ocr_history = OCRHistory(
                user_id=current_user.id,
                filename=file.filename,
                file_size=file_size,
                mime_type=file.content_type,
                extracted_data=final_data,
                extracted_text=extracted_text[:10000] if extracted_text else None,
                extracted_fields=final_data,
                confidence=best_confidence,
                success=True,
                processing_time_ms=processing_time_ms,
                ocr_engine_used=ocr_engine_used,
                api_calls_made=api_calls_made if api_calls_made else None,
                warnings=warnings if warnings else None,
                created_at=datetime.utcnow()
            )
            
            db.add(ocr_history)
            db.commit()
            db.refresh(ocr_history)
            
            final_data['ocr_history_id'] = ocr_history.id
            logger.info(f"OCR history saved with ID: {ocr_history.id}")
            
        except Exception as e:
            logger.error(f"Failed to save OCR history: {str(e)}")
            db.rollback()
        
        # Prepare response
        response_data = final_data.copy()
        if 'extracted_text' in response_data:
            del response_data['extracted_text']  # Don't send large text to frontend
        
        return {
            'success': True,
            'data': response_data,
            'confidence': best_confidence,
            'warnings': warnings,
            'filename': file.filename,
            'ocr_history_id': final_data.get('ocr_history_id'),
            'processing_time_ms': processing_time_ms
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCR processing error: {traceback.format_exc()}")
        
        # Save failed OCR attempt to history
        try:
            failed_history = OCRHistory(
                user_id=current_user.id,
                filename=file.filename if file else "unknown",
                file_size=file_size if 'file_size' in locals() else 0,
                mime_type=file.content_type if file else None,
                success=False,
                error_message=str(e),
                created_at=datetime.utcnow()
            )
            db.add(failed_history)
            db.commit()
        except:
            pass
            
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")
    
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
                logger.info(f"Cleaned up temporary file: {temp_file_path}")
            except Exception as e:
                logger.error(f"Failed to clean up temp file: {str(e)}")

@router.post("/save-ocr-history")
async def save_ocr_history(
    history_item: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Save OCR processing history
    """
    try:
        extracted_data = history_item.get('data', {})
        
        ocr_history = OCRHistory(
            user_id=current_user.id,
            filename=history_item.get('filename'),
            file_size=history_item.get('file_size', 0),
            mime_type=history_item.get('mime_type'),
            extracted_data=extracted_data,
            extracted_text=history_item.get('extracted_text'),
            extracted_fields=extracted_data,
            confidence=history_item.get('confidence', 0),
            success=history_item.get('success', True),
            error_message=history_item.get('error'),
            processing_time_ms=history_item.get('processing_time_ms'),
            ocr_engine_used=history_item.get('ocr_engine_used'),
            api_calls_made=history_item.get('api_calls_made'),
            warnings=history_item.get('warnings'),
            created_at=datetime.utcnow()
        )
        
        db.add(ocr_history)
        db.commit()
        db.refresh(ocr_history)
        
        return {
            'success': True,
            'message': 'OCR history saved',
            'history_id': ocr_history.id
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save OCR history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save history: {str(e)}")

@router.get("/ocr-history")
async def get_ocr_history(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get OCR processing history for current user with pagination
    """
    try:
        # Get total count
        total = db.query(OCRHistory).filter(
            OCRHistory.user_id == current_user.id
        ).count()
        
        # Get paginated history
        history = db.query(OCRHistory).filter(
            OCRHistory.user_id == current_user.id
        ).order_by(
            desc(OCRHistory.created_at)
        ).offset(offset).limit(limit).all()
        
        result = []
        for item in history:
            extracted_data = item.extracted_data or {}
            
            result.append({
                'id': item.id,
                'filename': item.filename,
                'file_size': item.file_size,
                'mime_type': item.mime_type,
                'confidence': item.confidence,
                'success': item.success,
                'error': item.error_message,
                'timestamp': item.created_at.isoformat() if item.created_at else None,
                'student_name': extracted_data.get('student_name'),
                'student_surname': extracted_data.get('student_surname'),
                'certificate_number': extracted_data.get('certificate_number'),
                'certificate_hash': extracted_data.get('certificate_hash'),
                'certificate_id': item.certificate_id,
                'warnings': item.warnings,
                'processing_time_ms': item.processing_time_ms,
                'ocr_engine_used': item.ocr_engine_used
            })
        
        return {
            'success': True,
            'history': result,
            'total': total,
            'limit': limit,
            'offset': offset,
            'has_more': (offset + limit) < total
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch OCR history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")

@router.get("/ocr-history/{history_id}")
async def get_ocr_history_detail(
    history_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed OCR history entry by ID
    """
    try:
        ocr_history = db.query(OCRHistory).filter(
            OCRHistory.id == history_id,
            OCRHistory.user_id == current_user.id
        ).first()
        
        if not ocr_history:
            raise HTTPException(status_code=404, detail="OCR history not found")
        
        extracted_data = ocr_history.extracted_data or {}
        
        return {
            'success': True,
            'history': {
                'id': ocr_history.id,
                'filename': ocr_history.filename,
                'file_size': ocr_history.file_size,
                'mime_type': ocr_history.mime_type,
                'extracted_data': extracted_data,
                'extracted_text': ocr_history.extracted_text[:1000] if ocr_history.extracted_text else None,  # Truncate for response
                'confidence': ocr_history.confidence,
                'success': ocr_history.success,
                'error_message': ocr_history.error_message,
                'processing_time_ms': ocr_history.processing_time_ms,
                'ocr_engine_used': ocr_history.ocr_engine_used,
                'api_calls_made': ocr_history.api_calls_made,
                'warnings': ocr_history.warnings,
                'certificate_id': ocr_history.certificate_id,
                'created_at': ocr_history.created_at.isoformat() if ocr_history.created_at else None,
                'updated_at': ocr_history.updated_at.isoformat() if ocr_history.updated_at else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch OCR history detail: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch history detail: {str(e)}")

@router.post("/extract")
async def extract_certificate_data_simple(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Simple certificate data extraction endpoint for frontend compatibility
    """
    return await process_certificate(file, None, None, current_user, db)

@router.post("/extract-certificate-data")
async def extract_certificate_data(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    prefer_api: str = Form('auto')
):
    """
    Extract certificate data using enhanced LGCSE OCR with multi-API support
    """
    return await process_certificate(file, str(current_user.id), current_user.institution, current_user, db)

@router.post("/save-extracted-certificate")
async def save_extracted_certificate(
    certificate_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Save certificate from OCR extraction
    """
    try:
        # Validate required fields
        required_fields = ['student_name']
        missing_fields = [field for field in required_fields 
                         if not certificate_data.get(field)]
        
        if missing_fields:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )
        
        # Generate certificate hash if not provided
        certificate_hash = certificate_data.get('certificate_hash')
        if not certificate_hash:
            hash_input = f"{certificate_data.get('student_name')}{certificate_data.get('student_id', '')}{datetime.utcnow().isoformat()}"
            certificate_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        
        # Check if certificate already exists
        existing = db.query(Certificate).filter(
            Certificate.certificate_hash == certificate_hash
        ).first()
        
        if existing:
            # Update OCR history link
            if certificate_data.get('ocr_history_id'):
                ocr_history = db.query(OCRHistory).filter(
                    OCRHistory.id == certificate_data['ocr_history_id']
                ).first()
                if ocr_history:
                    ocr_history.certificate_id = existing.id
                    db.commit()
            
            return {
                'success': True,
                'message': 'Certificate already exists',
                'certificate_id': existing.id,
                'certificate_hash': existing.certificate_hash,
                'status': existing.status,
                'existing': True
            }
        
        # Extract subjects
        subjects = certificate_data.get('subjects', [])
        if isinstance(subjects, list):
            subjects_json = subjects
        else:
            subjects_json = []
        
        # Split student name into first and surname if needed
        student_name = certificate_data.get('student_name', '')
        student_surname = certificate_data.get('student_surname', '')
        
        if not student_surname and ' ' in student_name:
            parts = student_name.split(' ', 1)
            student_name = parts[0]
            student_surname = parts[1] if len(parts) > 1 else ''
        
        # Create certificate record
        new_certificate = Certificate(
            certificate_hash=certificate_hash,
            student_name=student_name,
            student_surname=student_surname,
            student_id=certificate_data.get('student_id', ''),
            examination_year=certificate_data.get('examination_year', datetime.now().year),
            subjects=subjects_json,
            issue_date=certificate_data.get('issue_date', datetime.now().strftime('%Y-%m-%d')),
            issuer_id=current_user.id,
            institution=certificate_data.get('institution', current_user.institution or ''),
            extracted_data={
                'ocr_confidence': certificate_data.get('confidence', 0),
                'extraction_method': 'lgcse_multi_ocr',
                'extracted_text': certificate_data.get('extracted_text', ''),
                'processed_by': current_user.username,
                'certificate_data': certificate_data,
                'extraction_date': datetime.utcnow().isoformat()
            },
            status="pending",
            verification_status="pending",
            payment_status="unpaid"
        )
        
        db.add(new_certificate)
        db.commit()
        db.refresh(new_certificate)
        
        # Update OCR history if exists
        if certificate_data.get('ocr_history_id'):
            ocr_history = db.query(OCRHistory).filter(
                OCRHistory.id == certificate_data['ocr_history_id']
            ).first()
            if ocr_history:
                ocr_history.certificate_id = new_certificate.id
                db.commit()
        
        logger.info(f"Certificate saved successfully with ID: {new_certificate.id}, Hash: {new_certificate.certificate_hash[:16]}...")
        
        return {
            'success': True,
            'message': 'Certificate saved successfully',
            'certificate_id': new_certificate.id,
            'certificate_hash': new_certificate.certificate_hash,
            'status': new_certificate.status,
            'existing': False
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save certificate: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to save certificate: {str(e)}")

@router.get("/ocr-status")
async def get_ocr_status(current_user: User = Depends(get_current_active_user)):
    """
    Get OCR system status and capabilities
    """
    try:
        # Check if processors are available
        ocr_available = ocr_processor is not None
        multi_ocr_available = multi_ocr_processor is not None and hasattr(multi_ocr_processor, 'get_api_status')
        
        multi_ocr_status = {}
        if multi_ocr_available:
            try:
                multi_ocr_status = multi_ocr_processor.get_api_status()
            except:
                multi_ocr_status = {}
        
        capabilities = {
            'student_name_extraction': ocr_available,
            'date_of_birth_extraction': ocr_available,
            'centre_number_extraction': ocr_available,
            'examination_year_extraction': ocr_available,
            'examination_session_extraction': ocr_available,
            'subjects_extraction': ocr_available,
            'grades_extraction': ocr_available,
            'institution_extraction': ocr_available,
            'confidence_scoring': ocr_available,
            'certificate_hash_generation': True,
            'multi_ocr_support': multi_ocr_available,
            'api_fallback': multi_ocr_available,
            'structured_data_extraction': ocr_available
        }
        
        # Count available APIs
        available_apis = []
        if multi_ocr_status:
            for api_name, status in multi_ocr_status.items():
                if isinstance(status, dict) and status.get('enabled') and api_name != 'total_apis_available':
                    available_apis.append(api_name)
        
        # Build available OCR engines list
        available_engines = []
        if ocr_available:
            available_engines.append('Tesseract with Enhanced LGCSE Processing')
        
        if multi_ocr_status.get('gemini', {}).get('enabled'):
            available_engines.append('Google Gemini API (AI-powered)')
        if multi_ocr_status.get('google_vision', {}).get('enabled'):
            available_engines.append('Google Cloud Vision API')
        if multi_ocr_status.get('kolosal', {}).get('enabled'):
            available_engines.append('Kolosal AI OCR')
        if multi_ocr_status.get('ocr_space', {}).get('enabled'):
            available_engines.append('OCR.space API')
        
        status = {
            'ocr_available': ocr_available,
            'ocr_engines': available_engines if available_engines else ['No OCR engines available'],
            'ocr_specialization': 'LGCSE Certificates - Examinations Council of Lesotho' if ocr_available else 'Not available',
            'supported_formats': ['JPEG', 'PNG', 'PDF'] if ocr_available else [],
            'capabilities': capabilities,
            'multi_ocr': {
                'enabled': multi_ocr_available,
                'available_apis': available_apis,
                'preferred_api': os.getenv('OCR_PREFERRED_API', 'auto'),
                'fallback_enabled': os.getenv('OCR_FALLBACK_ENABLED', 'true').lower() == 'true',
                'api_status': multi_ocr_status
            },
            'lgcse_specific': {
                'supports_lgcse_certificates': ocr_available,
                'examination_council_of_lesotho': ocr_available,
                'grade_recognition': ['A*', 'A', 'B', 'C', 'D', 'E', 'F', 'G'] if ocr_available else [],
                'confidence_threshold': int(os.getenv('OCR_CONFIDENCE_THRESHOLD', '70')),
                'enhanced_extraction': ocr_available,
                'multi_api_integration': multi_ocr_available
            } if ocr_available else {},
            'user_permissions': {
                'can_extract': current_user.role in ['issuer', 'admin', 'verifier'],
                'can_save': current_user.role in ['issuer', 'admin'],
                'role': current_user.role
            },
            'total_apis_available': len(available_apis)
        }
        
        return status
        
    except Exception as e:
        logger.error(f"OCR status check failed: {str(e)}")
        return {
            'ocr_available': False,
            'error': str(e),
            'user_permissions': {
                'can_extract': current_user.role in ['issuer', 'admin', 'verifier'],
                'can_save': current_user.role in ['issuer', 'admin'],
                'role': current_user.role
            }
        }

@router.get("/extraction-history")
async def get_extraction_history(
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get recent OCR extraction history for the current user
    """
    try:
        # Get OCR history from database
        ocr_history = db.query(OCRHistory).filter(
            OCRHistory.user_id == current_user.id
        ).order_by(
            desc(OCRHistory.created_at)
        ).limit(limit).all()
        
        history = []
        for item in ocr_history:
            extracted_data = item.extracted_data or {}
            
            history.append({
                'id': item.id,
                'filename': item.filename,
                'timestamp': item.created_at.isoformat() if item.created_at else None,
                'confidence': item.confidence,
                'success': item.success,
                'error': item.error_message,
                'student_name': extracted_data.get('student_name'),
                'certificate_number': extracted_data.get('certificate_number'),
                'certificate_hash': extracted_data.get('certificate_hash'),
                'certificate_id': item.certificate_id,
                'warnings': item.warnings
            })
        
        # Also get certificates created from OCR
        certificates = db.query(Certificate).filter(
            Certificate.issuer_id == current_user.id
        ).order_by(
            desc(Certificate.created_at)
        ).limit(limit).all()
        
        for cert in certificates:
            # Check if already in history
            if not any(h.get('certificate_id') == cert.id for h in history):
                extracted_data = cert.extracted_data or {}
                history.append({
                    'certificate_id': cert.id,
                    'certificate_hash': cert.certificate_hash,
                    'student_name': cert.student_name,
                    'examination_year': cert.examination_year,
                    'confidence': extracted_data.get('ocr_confidence', 0),
                    'extraction_method': extracted_data.get('extraction_method', 'unknown'),
                    'status': cert.status,
                    'timestamp': cert.created_at.isoformat() if cert.created_at else None
                })
        
        # Sort by timestamp
        history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return {
            'success': True,
            'history': history[:limit],
            'total_count': len(history)
        }
        
    except Exception as e:
        logger.error(f"Failed to get extraction history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get extraction history: {str(e)}")

@router.post("/validate-extracted-data")
async def validate_extracted_data(
    certificate_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user)
):
    """
    Validate extracted certificate data
    """
    try:
        is_valid = True
        message = "Data appears valid"
        confidence = certificate_data.get('confidence', 0)
        
        validation_details = {}
        
        # Check required fields
        required_fields = ['student_name']
        missing = [f for f in required_fields if not certificate_data.get(f)]
        if missing:
            is_valid = False
            message = f"Missing required fields: {', '.join(missing)}"
        
        # Check examination year validity
        if certificate_data.get('examination_year'):
            year = certificate_data['examination_year']
            try:
                year_int = int(year) if year else None
                if year_int:
                    current_year = datetime.now().year
                    if year_int < 2000:
                        validation_details['year_warning'] = 'Very old examination year'
                    elif year_int > current_year + 1:
                        validation_details['year_warning'] = 'Future examination year'
            except (ValueError, TypeError):
                validation_details['year_warning'] = 'Invalid year format'
        
        # Check subjects
        subjects = certificate_data.get('subjects', [])
        if subjects:
            if len(subjects) < 3:
                validation_details['subjects_warning'] = f'Few subjects detected ({len(subjects)} subjects)'
            elif len(subjects) > 10:
                validation_details['subjects_warning'] = f'Unusually many subjects ({len(subjects)} subjects)'
        
        # Check confidence
        if confidence < 60:
            validation_details['confidence_warning'] = f'Low confidence ({confidence}%)'
        
        # Check student name
        student_name = certificate_data.get('student_name', '')
        if len(student_name) < 2:
            validation_details['name_warning'] = 'Student name is too short'
        elif not any(c.isalpha() for c in student_name):
            validation_details['name_warning'] = 'Name contains no letters'
        
        # Check certificate hash
        cert_hash = certificate_data.get('certificate_hash', '')
        if cert_hash and len(cert_hash) < 32:
            validation_details['hash_warning'] = 'Certificate hash seems too short'
        elif not cert_hash:
            validation_details['hash_warning'] = 'No certificate hash found'
        
        return {
            'validation_result': {
                'is_valid': is_valid,
                'message': message,
                'confidence': confidence
            },
            'additional_validation': validation_details,
            'ready_to_save': is_valid and confidence > 60 and len(validation_details) == 0,
            'needs_review': confidence < 70 or len(validation_details) > 0,
            'can_proceed': confidence > 50  # Can proceed with manual review if needed
        }
        
    except Exception as e:
        logger.error(f"Validation failed: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")

@router.post("/retry-failed")
async def retry_failed_ocr(
    history_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Retry failed OCR processing
    """
    try:
        # Get OCR history item
        ocr_history = db.query(OCRHistory).filter(
            OCRHistory.id == history_id,
            OCRHistory.user_id == current_user.id
        ).first()
        
        if not ocr_history:
            raise HTTPException(status_code=404, detail="OCR history not found")
        
        return {
            'success': False,
            'message': 'Retry requires original file. Please upload again.',
            'original_filename': ocr_history.filename,
            'history_id': history_id,
            'suggestion': 'Use the file upload endpoint with the same file'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Retry failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Retry failed: {str(e)}")

@router.delete("/ocr-history/{history_id}")
async def delete_ocr_history(
    history_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete OCR history entry
    """
    try:
        ocr_history = db.query(OCRHistory).filter(
            OCRHistory.id == history_id,
            OCRHistory.user_id == current_user.id
        ).first()
        
        if not ocr_history:
            raise HTTPException(status_code=404, detail="OCR history not found")
        
        db.delete(ocr_history)
        db.commit()
        
        return {
            'success': True,
            'message': 'OCR history deleted successfully'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to delete OCR history: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete history: {str(e)}")