from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
import os
import tempfile
import json
from typing import Dict, Any

from database import get_db
from models import User, Certificate
from enhanced_lgcse_processor import EnhancedLGCSEProcessor
from multi_ocr_processor import MultiOCRProcessor
from auth import get_current_active_user

router = APIRouter(prefix="/api/ocr", tags=["ocr"])

# Initialize OCR processors
ocr_processor = EnhancedLGCSEProcessor()
multi_ocr_processor = MultiOCRProcessor()

@router.post("/extract")
async def extract_certificate_data_simple(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Simple certificate data extraction endpoint for frontend compatibility
    """
    return await extract_certificate_data(file, current_user, db)

@router.post("/extract-certificate-data")
async def extract_certificate_data(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    prefer_api: str = Form('auto')  # Allow API preference: 'auto', 'gemini', 'google_vision', 'kolosal', 'ocr_space', 'tesseract'
):
    """
    Extract certificate data using enhanced LGCSE OCR with multi-API support
    """
    try:
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf']
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail=f"File must be an image (JPEG, PNG) or PDF. Got: {file.content_type}")
        
        # Additional validation for file size and type
        if file.content_type.startswith('text/'):
            raise HTTPException(status_code=400, detail="Text files are not supported for OCR. Please upload an image or PDF file.")
        
        # Create temporary file
        file_extension = '.jpg' if file.content_type.startswith('image/') else '.pdf'
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            # Write uploaded file to temp location
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Extract data using multi-OCR processor with enhanced LGCSE processing
            multi_result = multi_ocr_processor.process_image_with_all_apis(temp_file_path, prefer_api)
            
            # Get the best result from multi-OCR processing
            best_ocr_result = multi_result.get('best_result', {})
            
            # Process the best result through enhanced LGCSE processor
            if best_ocr_result.get('text'):
                # Create a temporary text file with OCR result for LGCSE processing
                with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as text_file:
                    text_file.write(best_ocr_result['text'])
                    text_file_path = text_file.name
                
                try:
                    # Use enhanced LGCSE processor to parse the OCR text
                    result = ocr_processor.process_certificate_file_enhanced(temp_file_path)
                    
                    # Merge multi-OCR metadata with LGCSE processing
                    result['multi_ocr_analysis'] = {
                        'best_api': best_ocr_result.get('api_name'),
                        'best_confidence': best_ocr_result.get('confidence', 0),
                        'total_apis_tried': multi_result.get('total_processing_time', 0),
                        'all_apis_used': multi_result.get('apis_used', []),
                        'comparison_data': multi_result.get('comparison', {})
                    }
                    
                    # Update confidence with multi-OCR analysis
                    if best_ocr_result.get('confidence', 0) > result.get('confidence_score', 0):
                        result['confidence_score'] = best_ocr_result['confidence']
                        result['confidence_source'] = f"multi_ocr_{best_ocr_result.get('api_name')}"
                    
                finally:
                    # Clean up temporary text file
                    if os.path.exists(text_file_path):
                        os.unlink(text_file_path)
            else:
                # Fallback to standard enhanced processing
                result = ocr_processor.process_certificate_file_enhanced(temp_file_path)
                result['multi_ocr_analysis'] = {'error': 'No text extracted from multi-OCR'}
            
            # Add user info
            result['processed_by'] = current_user.username
            result['user_role'] = current_user.role
            
            # Determine if result is good enough for saving
            confidence_threshold = 70
            is_lgcse_cert = result.get('lgcse_specific', {}).get('validation', {}).get('is_valid', False)
            confidence = result.get('confidence_score', 0)
            
            if (is_lgcse_cert and confidence > confidence_threshold) or confidence > 85:
                result['suggestion'] = {
                    'action': 'save_certificate',
                    'message': f'High confidence ({confidence:.1f}%) certificate detected. Consider saving this certificate.',
                    'data_ready': True
                }
                
                # Prepare data for certificate creation
                if 'lgcse_specific' in result:
                    result['certificate_data'] = result['lgcse_specific']['parsed_data']
                else:
                    result['certificate_data'] = result.get('extracted_fields', {})
            else:
                result['suggestion'] = {
                    'action': 'manual_review',
                    'message': f'Low confidence ({confidence:.1f}%) or incomplete data. Manual review required.',
                    'data_ready': False
                }
            
            return result
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
    
    except Exception as e:
        import traceback
        error_detail = f"Enhanced LGCSE OCR processing failed: {str(e)}"
        print(f"OCR Error Details: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=error_detail)

@router.post("/save-extracted-certificate")
async def save_extracted_certificate(
    certificate_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Save LGCSE certificate from OCR extraction
    """
    try:
        # Validate required LGCSE fields
        required_fields = ['student_name', 'examination_year', 'subjects_grades']
        missing_fields = [field for field in required_fields 
                         if not certificate_data.get(field)]
        
        if missing_fields:
            raise HTTPException(
                status_code=400, 
                detail=f"Missing required LGCSE fields: {', '.join(missing_fields)}"
            )
        
        # Create certificate record with LGCSE-specific data
        new_certificate = Certificate(
            student_name=certificate_data['student_name'],
            student_surname=certificate_data.get('student_surname', ''),
            student_id=certificate_data.get('student_id', ''),
            examination_year=certificate_data['examination_year'],
            subjects=[sg.get('subject', '') for sg in certificate_data.get('subjects_grades', [])],
            institution=certificate_data.get('institution', ''),
            issuer_id=current_user.id,
            extracted_data={
                'ocr_confidence': certificate_data.get('confidence_score', 0),
                'extraction_method': 'lgcse_tesseract_ocr',
                'raw_text': certificate_data.get('extracted_text', ''),
                'processed_by': current_user.username,
                'lgcse_data': {
                    'examination_session': certificate_data.get('examination_session'),
                    'subjects_grades': certificate_data.get('subjects_grades', []),
                    'centre_number': certificate_data.get('centre_number'),
                    'certificate_number': certificate_data.get('certificate_number'),
                    'issue_date': certificate_data.get('issue_date'),
                    'certificate_type': certificate_data.get('certificate_type'),
                    'examination_board': certificate_data.get('examination_board')
                }
            },
            status="pending_verification"
        )
        
        db.add(new_certificate)
        db.commit()
        db.refresh(new_certificate)
        
        return {
            'success': True,
            'message': 'LGCSE certificate saved successfully',
            'certificate_id': new_certificate.id,
            'certificate_hash': new_certificate.certificate_hash,
            'status': new_certificate.status,
            'lgcse_verified': True
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save LGCSE certificate: {str(e)}")

@router.get("/ocr-status")
async def get_ocr_status(current_user: User = Depends(get_current_active_user)):
    """
    Get Enhanced LGCSE OCR system status and capabilities with multi-API support
    """
    try:
        # Check multi-OCR processor status
        multi_ocr_status = multi_ocr_processor.get_api_status()
        
        capabilities = {
            'student_name_extraction': True,
            'date_of_birth_extraction': True,
            'centre_number_extraction': True,
            'lgcse_number_extraction': True,
            'examination_year_extraction': True,
            'examination_session_extraction': True,
            'subjects_extraction': True,
            'grades_extraction': True,
            'institution_extraction': True,
            'confidence_scoring': True,
            'lgcse_structure_verification': True,
            'certificate_hash_generation': True,
            'multi_ocr_support': True,
            'api_fallback': True,
            'confidence_comparison': True,
            'real_time_api_comparison': True,
            'gemini_ai_powered': True,
            'structured_data_extraction': True
        }
        
        status = {
            'ocr_available': True,
            'ocr_engines': ['Tesseract with Enhanced LGCSE Processing'],
            'ocr_specialization': 'LGCSE Certificates - Examinations Council of Lesotho',
            'supported_formats': ['JPEG', 'PNG', 'PDF'],
            'capabilities': capabilities,
            'multi_ocr': {
                'enabled': True,
                'available_apis': [api for api, status in multi_ocr_status.items() 
                                 if isinstance(status, dict) and status.get('enabled') and api != 'total_apis_available'],
                'preferred_api': os.getenv('OCR_PREFERRED_API', 'auto'),
                'fallback_enabled': os.getenv('OCR_FALLBACK_ENABLED', 'true').lower() == 'true',
                'api_status': multi_ocr_status
            },
            'lgcse_specific': {
                'supports_lgcse_certificates': True,
                'examination_council_of_lesotho': True,
                'grade_recognition': ['A*', 'A', 'B', 'C', 'D', 'E', 'F', 'G'],
                'subject_recognition': list(ocr_processor.lgcse_subjects.values()),
                'confidence_threshold': int(os.getenv('OCR_CONFIDENCE_THRESHOLD', '70')),
                'multiple_ocr_configs': True,
                'enhanced_extraction': True,
                'multi_api_integration': True
            },
            'user_permissions': {
                'can_extract': current_user.role in ['issuer', 'admin'],
                'can_save': current_user.role in ['issuer', 'admin'],
                'role': current_user.role
            }
        }
        
        # Add available OCR engines based on multi-OCR status
        available_engines = ['Tesseract with Enhanced LGCSE Processing']
        if multi_ocr_status['gemini']['enabled']:
            available_engines.append('Google Gemini API (AI-powered)')
        if multi_ocr_status['google_vision']['enabled']:
            available_engines.append('Google Cloud Vision API')
        if multi_ocr_status['kolosal']['enabled']:
            available_engines.append('Kolosal AI OCR')
        if multi_ocr_status['ocr_space']['enabled']:
            available_engines.append('OCR.space API')
        
        status['ocr_engines'] = available_engines
        status['total_apis_available'] = multi_ocr_status['total_apis_available']
        
        return status
        
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
    Validate extracted LGCSE certificate data using enhanced processor
    """
    try:
        # Use enhanced processor to validate
        parsed_data = {
            "candidate_info": {
                "name": certificate_data.get('student_name', ''),
                "date_of_birth": certificate_data.get('date_of_birth', ''),
                "centre_number": certificate_data.get('centre_number', ''),
                "lgcse_number": certificate_data.get('lgcse_number', '')
            },
            "examination_info": {
                "session": certificate_data.get('examination_session', ''),
                "year": certificate_data.get('examination_year', '')
            },
            "subjects": certificate_data.get('subjects', []),
            "raw_text": certificate_data.get('extracted_text', '')
        }
        
        is_valid, message, confidence = ocr_processor.validate_lgcse_certificate_enhanced(parsed_data)
        
        validation_details = {}
        lgcse_compliance = {
            "is_valid_lgcse": is_valid,
            "confidence": confidence,
            "message": message
        }
        
        # Additional LGCSE business logic validation
        
        # Check examination year validity
        if certificate_data.get('examination_year'):
            year = certificate_data['examination_year']
            if isinstance(year, int):
                if year < 2000:
                    validation_details['year_warning'] = 'Very old examination year'
                elif year > 2025:
                    validation_details['year_warning'] = 'Future examination year'
        
        # Check subjects and grades
        subjects_grades = certificate_data.get('subjects_grades', [])
        if len(subjects_grades) < 3:
            validation_details['subjects_warning'] = 'Few subjects detected'
        elif len(subjects_grades) > 10:
            validation_details['subjects_warning'] = 'Unusually many subjects'
        
        # Check for valid LGCSE grades
        valid_grades = ['A*', 'A', 'B', 'C', 'D', 'E', 'F', 'A+', 'B+', 'C+']
        invalid_grades = []
        for sg in subjects_grades:
            grade = sg.get('grade')
            if grade and grade not in valid_grades:
                invalid_grades.append(f"{sg.get('subject', 'Unknown')}: {grade}")
        
        if invalid_grades:
            validation_details['grade_warnings'] = invalid_grades
        
        # Check student name format
        student_name = certificate_data.get('student_name', '')
        if len(student_name) < 3:
            validation_details['name_warning'] = 'Very short student name'
        elif not any(char.isalpha() for char in student_name):
            validation_details['name_warning'] = 'Name contains no letters'
        
        # Check for LGCSE certificate type
        cert_type = certificate_data.get('certificate_type', '')
        if not any(lgcse_type in cert_type.lower() for lgcse_type in ['lgcse', 'cambridge', 'general certificate']):
            validation_details['certificate_type_warning'] = 'Not recognized as LGCSE certificate'
        
        return {
            'validation_result': {
                'is_valid_lgcse': is_valid,
                'message': message,
                'confidence': confidence
            },
            'lgcse_compliance': lgcse_compliance,
            'additional_validation': validation_details,
            'ready_to_save': is_valid and confidence > 60,
            'lgcse_certified': is_valid
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enhanced LGCSE validation failed: {str(e)}")
