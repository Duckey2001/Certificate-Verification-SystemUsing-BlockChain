import hashlib
import json
import re
import shutil
from typing import Dict, Any, Optional, Tuple

import pytesseract
from PIL import Image
import pdf2image
import os


class OCRDependencyError(Exception):
    """Raised when OCR dependencies (tesseract, poppler) are missing or misconfigured."""

    def __init__(self, message: str, hint: str = ""):
        super().__init__(message)
        self.hint = hint


class NonLGCSECertificateError(Exception):
    """Raised when the uploaded document does not look like an LGCSE certificate."""


def _check_tesseract() -> None:
    """Check if tesseract is available; raise OCRDependencyError if not."""
    tesseract_path = shutil.which("tesseract")
    if not tesseract_path:
        raise OCRDependencyError(
            "Tesseract OCR is not installed or not on PATH.",
            hint="Install: Ubuntu/Debian: sudo apt install tesseract-ocr. Mac: brew install tesseract.",
        )
    try:
        pytesseract.get_tesseract_version()
    except Exception as e:
        raise OCRDependencyError(
            f"Tesseract could not be invoked: {e}",
            hint="Verify tesseract is installed and pytesseract can find it.",
        )


def _check_poppler() -> None:
    """Check if poppler (for pdf2image) is available."""
    pdfinfo_path = shutil.which("pdfinfo") or shutil.which("pdftoppm")
    if not pdfinfo_path:
        try:
            pdf2image.pdf2image.pdfinfo_from_path
        except AttributeError:
            pass
        raise OCRDependencyError(
            "Poppler (pdfinfo/pdftoppm) is not installed or not on PATH.",
            hint="Install: Ubuntu/Debian: sudo apt install poppler-utils. Mac: brew install poppler.",
        )


def _normalize_for_hash(value: str) -> str:
    """Normalize string for consistent hashing: trim, collapse whitespace, lower case where appropriate."""
    if not value or not isinstance(value, str):
        return ""
    s = " ".join(value.split()).strip()
    return s


def _normalize_certificate_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize certificate fields before hashing to reduce false mismatches."""
    result = data.copy()
    # Normalize text fields
    for key in ("student_name", "student_number", "date_of_birth", "institution", "date_of_issue"):
        if key in result and result[key]:
            result[key] = _normalize_for_hash(str(result[key]))
    # Normalize certificate_numbers list
    if "certificate_numbers" in result and result["certificate_numbers"]:
        result["certificate_numbers"] = sorted(_normalize_for_hash(str(n)) for n in result["certificate_numbers"] if n)
    else:
        result["certificate_numbers"] = []
    # Ensure grades is a dict with sorted keys for consistent JSON
    if "grades" not in result or not result["grades"]:
        result["grades"] = {}
    return result


def _is_lgcse_certificate(text: str) -> bool:
    """
    Heuristic check to decide if the OCR text looks like an LGCSE certificate.
    We look for strong LGCSE-specific keywords to avoid hashing arbitrary documents.
    """
    if not text:
        return False

    lowered = text.lower()
    keywords = [
        "lgcse",
        "lesotho general certificate of secondary education",
        "examinations council of lesotho",
    ]
    return any(k in lowered for k in keywords)


class CertificateProcessor:
    def __init__(self, tesseract_path: str = None, skip_dependency_check: bool = False):
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        if not skip_dependency_check:
            _check_tesseract()

    def extract_text_from_image(self, image_path: str) -> str:
        """Extract text from image using OCR"""
        try:
            text = pytesseract.image_to_string(Image.open(image_path))
            return text
        except Exception as e:
            print(f"Error extracting text: {e}")
            return ""
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract text from PDF using OCR"""
        _check_poppler()
        try:
            images = pdf2image.convert_from_path(pdf_path)
            text = ""
            for image in images:
                text += pytesseract.image_to_string(image)
            return text
        except Exception as e:
            print(f"Error extracting PDF text: {e}")
            return ""
    
    def parse_certificate_text(self, text: str) -> Dict[str, Any]:
        """Parse LGCSE certificate text to extract structured data"""
        data = {
            "student_name": "",
            "student_number": "",
            "certificate_numbers": [],
            "date_of_birth": "",
            "institution": "",
            "grades": {},
            "date_of_issue": "",
            "subjects_reported": 0
        }
        
        # Patterns for LGCSE certificates
        patterns = {
            "name": r"NAME:\s*(.+)",
            "student_number": r"STUDENT NUMBER:\s*(.+)",
            "certificate_numbers": r"CERTIFICATE NUMBER(S)?:\s*(.+)",
            "date_of_birth": r"DATE OF BIRTH:\s*(.+)",
            "institution": r"(?:SCHOOL|INSTITUTION|CENTER):\s*(.+)",
            "issue_date": r"DATE OF ISSUE:\s*(.+)"
        }
        
        # Extract basic fields
        for field, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if field == "certificate_numbers":
                    numbers = match.group(1).strip()
                    if "," in numbers:
                        data[field] = [n.strip() for n in numbers.split(",")]
                    else:
                        data[field] = [numbers]
                else:
                    data[field] = match.group(1).strip()
        
        # Extract grades - LGCSE specific pattern
        grade_pattern = r"([A-Z]+[0-9]*)\s+([A-D])\s+(LEVEL\s+\d+|[A-Z]+)"
        grade_matches = re.findall(grade_pattern, text)
        
        for subject_code, grade, level in grade_matches:
            data["grades"][subject_code] = {
                "grade": grade,
                "level": level
            }
        
        # Count subjects
        subjects_pattern = r"(\d+)\s+subjects reported"
        subjects_match = re.search(subjects_pattern, text)
        if subjects_match:
            data["subjects_reported"] = int(subjects_match.group(1))
        else:
            data["subjects_reported"] = len(data["grades"])
        
        return data
    
    def _compute_extraction_confidence(self, data: Dict[str, Any]) -> float:
        """Compute confidence 0.0-1.0 based on how many key fields were extracted."""
        keys = ("student_name", "student_number", "certificate_numbers", "date_of_birth", "institution", "date_of_issue")
        filled = 0
        for k in keys:
            v = data.get(k)
            if v and (not isinstance(v, list) or len(v) > 0):
                filled += 1
        grades = data.get("grades") or {}
        if grades:
            filled += 1
        return filled / 7.0

    def generate_certificate_hash(self, certificate_data: Dict[str, Any]) -> str:
        """Generate SHA-256 hash from certificate data (expects normalized data)."""
        grades_json = json.dumps(certificate_data.get("grades", {}), sort_keys=True)
        
        data_string = (
            f"{certificate_data.get('student_name', '')}|"
            f"{certificate_data.get('student_number', '')}|"
            f"{'|'.join(sorted(certificate_data.get('certificate_numbers', [])))}|"
            f"{certificate_data.get('date_of_birth', '')}|"
            f"{grades_json}|"
            f"{certificate_data.get('institution', '')}|"
            f"{certificate_data.get('date_of_issue', '')}"
        )
        
        return hashlib.sha256(data_string.encode('utf-8')).hexdigest()
    
    def process_certificate_file(self, file_path: str) -> Dict[str, Any]:
        """Process a certificate file and extract data with hash"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Extract text based on file type
        if file_path.lower().endswith('.pdf'):
            text = self.extract_text_from_pdf(file_path)
        else:
            text = self.extract_text_from_image(file_path)

        if not text.strip():
            raise ValueError("No text could be extracted from the certificate")

        # Only proceed for LGCSE-like certificates
        if not _is_lgcse_certificate(text):
            raise NonLGCSECertificateError(
                "The uploaded document does not appear to be an LGCSE certificate and will not be verified."
            )

        # Parse the certificate text
        certificate_data = self.parse_certificate_text(text)
        certificate_data = _normalize_certificate_data(certificate_data)

        # Generate hash from normalized data
        certificate_data["certificate_hash"] = self.generate_certificate_hash(certificate_data)
        certificate_data["raw_text"] = text[:1000]  # Store first 1000 chars for reference
        certificate_data["extraction_confidence"] = round(self._compute_extraction_confidence(certificate_data), 2)

        return certificate_data
