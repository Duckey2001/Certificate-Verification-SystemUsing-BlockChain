#!/usr/bin/env python3
"""
Test OCR endpoint without authentication - temporary for debugging
"""

from fastapi import APIRouter, UploadFile, File
import sys
import os

# Add the backend path to import modules
sys.path.append('/home/duckey/lgcse-project/backend')

from enhanced_lgcse_processor import EnhancedLGCSEProcessor
import shutil
import uuid

# Create a temporary router for testing
test_router = APIRouter(prefix="/test", tags=["test"])

@test_router.post("/ocr-extract")
async def test_ocr_extract(file: UploadFile = File(...)):
    """Test OCR extraction without authentication"""
    
    # Validate file type
    allowed_types = ["application/pdf", "image/jpeg", "image/jpg", "image/png"]
    if file.content_type not in allowed_types:
        return {"error": "Only PDF and image files (JPEG, PNG) are supported"}
    
    # Save temporary file
    temp_dir = "temp/ocr"
    os.makedirs(temp_dir, exist_ok=True)
    temp_filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
    temp_path = os.path.join(temp_dir, temp_filename)
    
    try:
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Use Enhanced LGCSE Processor
        processor = EnhancedLGCSEProcessor()
        extracted_data = processor.process_certificate_file_enhanced(temp_path)
        
        # Clean up temp file
        os.remove(temp_path)
        
        return {
            "success": True,
            "message": "OCR processing completed",
            "data": extracted_data
        }
        
    except Exception as e:
        # Clean up temp file if it exists
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        return {
            "success": False,
            "error": f"OCR processing failed: {str(e)}"
        }

if __name__ == "__main__":
    import uvicorn
    from fastapi import FastAPI
    
    app = FastAPI(title="OCR Test API")
    app.include_router(test_router)
    
    print("🚀 Starting OCR Test Server on http://localhost:8001")
    print("📡 Test endpoint: POST http://localhost:8001/test/ocr-extract")
    print("🔍 No authentication required")
    
    uvicorn.run(app, host="0.0.0.0", port=8001, reload=True)
