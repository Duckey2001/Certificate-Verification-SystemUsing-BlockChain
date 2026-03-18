#!/usr/bin/env python3
"""
ECOL-Optimized OCR Configuration
Optimized for Examinations Council of Lesotho certificate processing
"""

import os
import json
from typing import Dict, Any, List
from multi_ocr_processor import MultiOCRProcessor
from enhanced_lgcse_processor import EnhancedLGCSEProcessor

class ECOLOCRProcessor:
    """
    ECOL-Optimized OCR Processor
    Specialized for Lesotho General Certificate of Secondary Education (LGCSE)
    """
    
    def __init__(self):
        """Initialize ECOL-optimized processor"""
        self.multi_processor = MultiOCRProcessor()
        self.lgcse_processor = EnhancedLGCSEProcessor()
        
        # ECOL-specific configuration
        self.ecol_config = {
            'institution': 'Examinations Council of Lesotho',
            'certificate_types': ['LGCSE', 'IGCSE'],
            'examination_board': 'Cambridge Assessment International Education',
            'supported_grades': ['A*', 'A', 'B', 'C', 'D', 'E', 'F', 'G'],
            'confidence_threshold': 75,  # Higher threshold for ECOL
            'preferred_apis': ['tesseract', 'ocr_space'],  # Most reliable for ECOL
            'skip_unreliable_apis': True
        }
    
    def process_ecol_certificate(self, image_path: str, prefer_api: str = 'ecol_optimized') -> Dict[str, Any]:
        """
        Process ECOL certificate with optimized settings
        """
        print("🔍 Processing ECOL Certificate...")
        print(f"   Institution: {self.ecol_config['institution']}")
        print(f"   Certificate Types: {', '.join(self.ecol_config['certificate_types'])}")
        
        # Use optimized API order
        if prefer_api == 'ecol_optimized':
            prefer_api = 'tesseract'  # Start with most reliable
        
        # Process with multi-OCR
        multi_result = self.multi_processor.process_image_with_all_apis(image_path, prefer_api)
        
        # Get best result
        best_result = multi_result.get('best_result', {})
        
        # Process through ECOL-optimized LGCSE processor
        lgcse_result = None
        try:
            lgcse_result = self.lgcse_processor.process_certificate_file_enhanced(image_path)
        except Exception as e:
            print(f"⚠️  LGCSE processor issue: {e}")
        
        # Combine results with ECOL context
        ecol_result = {
            'ecol_verified': True,
            'institution': self.ecol_config['institution'],
            'processing_summary': {
                'best_engine': best_result.get('api_name'),
                'confidence': best_result.get('confidence', 0),
                'processing_time': multi_result.get('total_processing_time', 0),
                'apis_used': multi_result.get('apis_used', [])
            },
            'extracted_data': {
                'raw_text': best_result.get('text', ''),
                'student_info': self._extract_student_info(best_result.get('text', '')),
                'examination_info': self._extract_examination_info(best_result.get('text', '')),
                'subjects_grades': self._extract_subjects_grades(best_result.get('text', ''))
            },
            'validation': self._validate_ecol_certificate(best_result.get('text', '')),
            'lgcse_analysis': lgcse_result if lgcse_result else None,
            'recommendations': self._generate_recommendations(best_result, lgcse_result)
        }
        
        return ecol_result
    
    def _extract_student_info(self, text: str) -> Dict[str, Any]:
        """Extract student information from OCR text"""
        import re
        
        student_info = {
            'name': None,
            'date_of_birth': None,
            'candidate_number': None,
            'centre_number': None,
            'school': None
        }
        
        # Extract student name (usually after "certifies that")
        name_match = re.search(r'certifies that.*?\\n\\s*([A-Z\\s]+)\\s*\\n', text, re.IGNORECASE)
        if name_match:
            student_info['name'] = name_match.group(1).strip()
        
        # Extract date of birth
        dob_match = re.search(r'Date of Birth:\\s*(\\d{1,2}\\s+[A-Za-z]+\\s+\\d{4})', text)
        if dob_match:
            student_info['date_of_birth'] = dob_match.group(1)
        
        # Extract candidate number
        candidate_match = re.search(r'Candidate Number:\\s*([A-Z0-9/]+)', text)
        if candidate_match:
            student_info['candidate_number'] = candidate_match.group(1)
        
        # Extract centre number
        centre_match = re.search(r'of\\s+([A-Z\\s]+HIGH SCHOOL)', text)
        if centre_match:
            student_info['school'] = centre_match.group(1).strip()
        
        return student_info
    
    def _extract_examination_info(self, text: str) -> Dict[str, Any]:
        """Extract examination information"""
        import re
        
        exam_info = {
            'examination_year': None,
            'examination_session': None,
            'certificate_type': None,
            'certificate_number': None
        }
        
        # Extract examination year and session
        year_session_match = re.search(r'examination of\\s+([A-Za-z]+\\s+(\\d{4}))', text, re.IGNORECASE)
        if year_session_match:
            exam_info['examination_session'] = year_session_match.group(1)
            exam_info['examination_year'] = year_session_match.group(2)
        
        # Extract certificate type
        if 'LGCSE' in text:
            exam_info['certificate_type'] = 'Lesotho General Certificate of Secondary Education'
        elif 'IGCSE' in text:
            exam_info['certificate_type'] = 'International General Certificate of Secondary Education'
        
        # Extract certificate number
        cert_match = re.search(r'Certificate Number:\\s*([A-Z0-9]+)', text)
        if cert_match:
            exam_info['certificate_number'] = cert_match.group(1)
        
        return exam_info
    
    def _extract_subjects_grades(self, text: str) -> List[Dict[str, str]]:
        """Extract subjects and grades"""
        import re
        
        subjects_grades = []
        
        # Look for subject-grade patterns
        # Pattern: Subject Name LGCSE Grade(A)
        subject_grade_pattern = r'([A-Za-z\\s]+)\\s+LGCSE\\s+([A-Z*]\\([a-z]\\))'
        matches = re.findall(subject_grade_pattern, text)
        
        for subject, grade in matches:
            subjects_grades.append({
                'subject': subject.strip(),
                'grade': grade,
                'level': 'LGCSE'
            })
        
        # Alternative pattern: Subject | Grade
        alt_pattern = r'([A-Za-z\\s]+)\\s+\\|\\s+([A-Z*])'
        alt_matches = re.findall(alt_pattern, text)
        
        for subject, grade in alt_matches:
            if grade in self.ecol_config['supported_grades']:
                subjects_grades.append({
                    'subject': subject.strip(),
                    'grade': grade,
                    'level': 'LGCSE'
                })
        
        return subjects_grades
    
    def _validate_ecol_certificate(self, text: str) -> Dict[str, Any]:
        """Validate ECOL certificate"""
        validation = {
            'is_ecol_certificate': False,
            'confidence_score': 0,
            'validation_checks': {},
            'issues': []
        }
        
        # Check for ECOL keywords
        ecol_keywords = ['Examinations Council of Lesotho', 'LGCSE', 'Cambridge Assessment']
        keyword_count = sum(1 for keyword in ecol_keywords if keyword.lower() in text.lower())
        
        validation['validation_checks']['ecol_keywords'] = {
            'found': keyword_count,
            'required': 2,
            'passed': keyword_count >= 2
        }
        
        # Check for required sections
        required_sections = ['certifies that', 'Date of Birth', 'Syllabus', 'Grade']
        section_count = sum(1 for section in required_sections if section.lower() in text.lower())
        
        validation['validation_checks']['required_sections'] = {
            'found': section_count,
            'required': 3,
            'passed': section_count >= 3
        }
        
        # Check for valid grades
        valid_grades_found = any(grade in text for grade in self.ecol_config['supported_grades'])
        validation['validation_checks']['valid_grades'] = {
            'found': valid_grades_found,
            'required': True,
            'passed': valid_grades_found
        }
        
        # Calculate overall confidence
        passed_checks = sum(1 for check in validation['validation_checks'].values() if check['passed'])
        total_checks = len(validation['validation_checks'])
        validation['confidence_score'] = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
        
        # Determine if it's a valid ECOL certificate
        validation['is_ecol_certificate'] = (
            validation['confidence_score'] >= self.ecol_config['confidence_threshold'] and
            validation['validation_checks']['ecol_keywords']['passed']
        )
        
        # Identify issues
        if not validation['validation_checks']['ecol_keywords']['passed']:
            validation['issues'].append('Missing ECOL keywords')
        if not validation['validation_checks']['required_sections']['passed']:
            validation['issues'].append('Missing required certificate sections')
        if not validation['validation_checks']['valid_grades']['passed']:
            validation['issues'].append('No valid ECOL grades found')
        
        return validation
    
    def _generate_recommendations(self, best_result: Dict[str, Any], lgcse_result: Dict[str, Any]) -> List[str]:
        """Generate processing recommendations"""
        recommendations = []
        
        confidence = best_result.get('confidence', 0)
        
        if confidence >= 90:
            recommendations.append('✅ Excellent quality - Ready for automatic processing')
        elif confidence >= 80:
            recommendations.append('✅ Good quality - Suitable for verification')
        elif confidence >= 70:
            recommendations.append('⚠️  Fair quality - Manual review recommended')
        else:
            recommendations.append('❌ Poor quality - Rescan recommended')
        
        # Check if LGCSE processing succeeded
        if lgcse_result and lgcse_result.get('confidence_score', 0) > 80:
            recommendations.append('🎓 LGCSE structure verified - Certificate ready for blockchain storage')
        elif lgcse_result:
            recommendations.append('🔍 LGCSE structure detected - Additional validation may be needed')
        else:
            recommendations.append('⚠️  LGCSE structure not clearly identified')
        
        return recommendations
    
    def get_ecol_status(self) -> Dict[str, Any]:
        """Get ECOL processor status"""
        return {
            'ecol_processor': {
                'status': 'active',
                'institution': self.ecol_config['institution'],
                'specialization': 'LGCSE Certificates',
                'supported_certificate_types': self.ecol_config['certificate_types'],
                'confidence_threshold': self.ecol_config['confidence_threshold']
            },
            'ocr_engines': self.multi_processor.get_api_status(),
            'lgcse_processor': {
                'status': 'active',
                'specialization': 'LGCSE Certificate Parsing'
            }
        }

# Test function
def test_ecol_processor(image_path: str):
    """Test ECOL processor with certificate image"""
    print("🏛️  ECOL OCR Processor Test")
    print("=" * 50)
    
    processor = ECOLOCRProcessor()
    
    # Show status
    status = processor.get_ecol_status()
    print(f"📋 Status: {status['ecol_processor']['status']}")
    print(f"🏛️  Institution: {status['ecol_processor']['institution']}")
    print(f"🎓 Specialization: {status['ecol_processor']['specialization']}")
    
    # Process certificate
    result = processor.process_ecol_certificate(image_path)
    
    # Show results
    print(f"\\n📊 Processing Results:")
    print(f"   Best Engine: {result['processing_summary']['best_engine']}")
    print(f"   Confidence: {result['processing_summary']['confidence']:.1f}%")
    print(f"   ECOL Verified: {'✅' if result['ecol_verified'] else '❌'}")
    
    # Show extracted info
    if result['extracted_data']['student_info']['name']:
        print(f"\\n👤 Student: {result['extracted_data']['student_info']['name']}")
    
    if result['extracted_data']['examination_info']['examination_year']:
        print(f"📅 Examination: {result['extracted_data']['examination_info']['examination_session']}")
    
    if result['extracted_data']['subjects_grades']:
        print(f"\\n📚 Subjects ({len(result['extracted_data']['subjects_grades'])}):")
        for sg in result['extracted_data']['subjects_grades'][:5]:  # Show first 5
            print(f"   • {sg['subject']}: {sg['grade']}")
    
    # Show validation
    validation = result['validation']
    print(f"\\n🔍 Validation:")
    print(f"   ECOL Certificate: {'✅' if validation['is_ecol_certificate'] else '❌'}")
    print(f"   Confidence Score: {validation['confidence_score']:.1f}%")
    
    if validation['issues']:
        print(f"   Issues: {', '.join(validation['issues'])}")
    
    # Show recommendations
    print(f"\\n💡 Recommendations:")
    for rec in result['recommendations']:
        print(f"   {rec}")
    
    return result

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        test_ecol_processor(image_path)
    else:
        print("Usage: python ecol_ocr_processor.py <certificate_image_path>")
