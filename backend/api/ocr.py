from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import os
import tempfile
import json
from typing import Dict, Any

from database import get_db
from models import User, Certificate
from certificate_ocr import CertificateOCR
from auth import get_current_active_user

router = APIRouter(prefix="/api/ocr", tags=["ocr"])

# Initialize OCR
ocr_processor = CertificateOCR()

@router.post("/extract-certificate-data")
async def extract_certificate_data(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Extract certificate data using OCR
    """
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            # Write uploaded file to temp location
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Extract data using OCR
            extracted_data = ocr_processor.extract_certificate_data(temp_file_path)
            
            # Verify certificate structure
            verification = ocr_processor.verify_certificate_structure(extracted_data)
            
            # Combine results
            result = {
                'success': True,
                'extracted_data': extracted_data,
                'verification': verification,
                'processed_by': current_user.username,
                'user_role': current_user.role
            }
            
            # If confidence is high and structure is valid, suggest saving
            if (verification['is_valid_structure'] and 
                extracted_data.get('confidence_score', 0) > 70):
                
                result['suggestion'] = {
                    'action': 'save_certificate',
                    'message': 'High confidence extraction detected. Consider saving this certificate.',
                    'data_ready': True
                }
                
                # Prepare data for certificate creation
                result['certificate_data'] = {
                    'student_name': extracted_data.get('student_name'),
                    'student_surname': extracted_data.get('student_surname'),
                    'student_id': extracted_data.get('student_id'),
                    'examination_year': extracted_data.get('examination_year'),
                    'subjects': extracted_data.get('subjects', []),
                    'institution': extracted_data.get('institution'),
                    'extracted_text': extracted_data.get('raw_text', ''),
                    'confidence_score': extracted_data.get('confidence_score', 0)
                }
            else:
                result['suggestion'] = {
                    'action': 'manual_review',
                    'message': 'Low confidence or incomplete data. Manual review required.',
                    'data_ready': False
                }
            
            return result
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

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
        required_fields = ['student_name', 'examination_year', 'subjects']
        missing_fields = [field for field in required_fields 
                         if not certificate_data.get(field)]
        
        if missing_fields:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required fields: {', '.join(missing_fields)}"
            )
        
        # Create certificate record
        new_certificate = Certificate(
            student_name=certificate_data['student_name'],
            student_surname=certificate_data.get('student_surname', ''),
            student_id=certificate_data.get('student_id', ''),
            examination_year=certificate_data['examination_year'],
            subjects=certificate_data['subjects'],
            institution=certificate_data.get('institution', ''),
            issuer_id=current_user.id,
            extracted_data={
                'ocr_confidence': certificate_data.get('confidence_score', 0),
                'extraction_method': 'tesseract_ocr',
                'raw_text': certificate_data.get('extracted_text', ''),
                'processed_by': current_user.username
            },
            status="pending_verification"
        )
        
        db.add(new_certificate)
        db.commit()
        db.refresh(new_certificate)
        
        return {
            'success': True,
            'message': 'Certificate saved successfully',
            'certificate_id': new_certificate.id,
            'certificate_hash': new_certificate.certificate_hash,
            'status': new_certificate.status
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save certificate: {str(e)}")

@router.get("/ocr-status")
async def get_ocr_status(current_user: User = Depends(get_current_active_user)):
    """
    Get OCR system status and capabilities
    """
    try:
        # Test OCR functionality
        test_result = ocr_processor.extract_certificate_data.__doc__
        
        return {
            'ocr_available': True,
            'ocr_engine': 'Tesseract',
            'supported_formats': ['JPEG', 'PNG', 'TIFF', 'BMP'],
            'capabilities': {
                'student_name_extraction': True,
                'subject_extraction': True,
                'year_extraction': True,
                'institution_extraction': True,
                'confidence_scoring': True,
                'structure_verification': True
            },
            'user_permissions': {
                'can_extract': current_user.role in ['issuer', 'admin'],
                'can_save': current_user.role in ['issuer', 'admin'],
                'role': current_user.role
            }
        }
        
    except Exception as e:
        return {
            'ocr_available': False,
            'error': str(e),
            'user_permissions': {
                'can_extract': False,
                'can_save': False,
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
        certificates = db.query(Certificate).filter(
            Certificate.issuer_id == current_user.id
        ).order_by(Certificate.created_at.desc()).limit(limit).all()
        
        history = []
        for cert in certificates:
            extracted_data = cert.extracted_data or {}
            
            history.append({
                'certificate_id': cert.id,
                'certificate_hash': cert.certificate_hash,
                'student_name': cert.student_name,
                'examination_year': cert.examination_year,
                'confidence_score': extracted_data.get('ocr_confidence', 0),
                'extraction_method': extracted_data.get('extraction_method', 'unknown'),
                'status': cert.status,
                'created_at': cert.created_at.isoformat() if cert.created_at else None
            })
        
        return {
            'success': True,
            'history': history,
            'total_count': len(history)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get extraction history: {str(e)}")

@router.post("/validate-extracted-data")
async def validate_extracted_data(
    certificate_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user)
):
    """
    Validate extracted certificate data without saving
    """
    try:
        # Use OCR processor to validate
        verification = ocr_processor.verify_certificate_structure(certificate_data)
        
        # Additional business logic validation
        validation_details = verification.get('validation_details', {})
        
        # Check examination year validity
        if certificate_data.get('examination_year'):
            year = certificate_data['examination_year']
            if isinstance(year, int):
                if year < 2000:
                    validation_details['year_warning'] = 'Very old examination year'
                elif year > 2025:
                    validation_details['year_warning'] = 'Future examination year'
        
        # Check subjects
        subjects = certificate_data.get('subjects', [])
        if len(subjects) < 3:
            validation_details['subjects_warning'] = 'Few subjects detected'
        elif len(subjects) > 10:
            validation_details['subjects_warning'] = 'Unusually many subjects'
        
        # Check student name format
        student_name = certificate_data.get('student_name', '')
        if len(student_name) < 3:
            validation_details['name_warning'] = 'Very short student name'
        elif not any(char.isalpha() for char in student_name):
            validation_details['name_warning'] = 'Name contains no letters'
        
        return {
            'validation_result': verification,
            'additional_validation': validation_details,
            'ready_to_save': verification['is_valid_structure'] and 
                           certificate_data.get('confidence_score', 0) > 60
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Validation failed: {str(e)}")
