#!/usr/bin/env python3
"""
Simple OCR Test Web Interface
Allows users to upload certificate images and test OCR functionality
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import os
import tempfile
import json
import time
from multi_ocr_processor import MultiOCRProcessor
from enhanced_lgcse_processor import EnhancedLGCSEProcessor
import uvicorn

app = FastAPI(title="OCR Test Interface")

# Initialize OCR processors
multi_processor = MultiOCRProcessor()
lgcse_processor = EnhancedLGCSEProcessor()

@app.get("/", response_class=HTMLResponse)
async def upload_form():
    """Simple upload form"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>LGCSE Certificate OCR Test</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
            .upload-area { border: 2px dashed #ccc; padding: 40px; text-align: center; margin: 20px 0; }
            .upload-area:hover { border-color: #007bff; }
            .result { background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }
            .success { background: #d4edda; border: 1px solid #c3e6cb; }
            .error { background: #f8d7da; border: 1px solid #f5c6cb; }
            .loading { display: none; text-align: center; margin: 20px 0; }
            .confidence { font-weight: bold; color: #007bff; }
            .engine { font-weight: bold; color: #28a745; }
            table { width: 100%; border-collapse: collapse; margin: 10px 0; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
        </style>
    </head>
    <body>
        <h1>🔍 LGCSE Certificate OCR Test</h1>
        <p>Upload a certificate image to test the OCR system with multiple engines.</p>
        
        <div class="upload-area" ondrop="dropHandler(event);" ondragover="allowDrop(event);">
            <p>📷 Drop certificate image here or click to select</p>
            <input type="file" id="fileInput" accept="image/*" style="display: none;" onchange="handleFileSelect(event);">
            <button onclick="document.getElementById('fileInput').click()">Choose File</button>
        </div>
        
        <div class="loading" id="loading">
            <p>⏳ Processing... This may take up to 30 seconds...</p>
        </div>
        
        <div id="result"></div>
        
        <script>
            function allowDrop(ev) {
                ev.preventDefault();
            }
            
            function dropHandler(ev) {
                ev.preventDefault();
                const files = ev.dataTransfer.files;
                if (files.length > 0) {
                    uploadFile(files[0]);
                }
            }
            
            function handleFileSelect(ev) {
                const files = ev.target.files;
                if (files.length > 0) {
                    uploadFile(files[0]);
                }
            }
            
            async function uploadFile(file) {
                if (!file.type.startsWith('image/')) {
                    alert('Please upload an image file');
                    return;
                }
                
                const formData = new FormData();
                formData.append('file', file);
                
                document.getElementById('loading').style.display = 'block';
                document.getElementById('result').innerHTML = '';
                
                try {
                    const response = await fetch('/test-ocr', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const result = await response.json();
                    displayResult(result);
                } catch (error) {
                    document.getElementById('result').innerHTML = 
                        '<div class="result error">❌ Error: ' + error.message + '</div>';
                } finally {
                    document.getElementById('loading').style.display = 'none';
                }
            }
            
            function displayResult(result) {
                const resultDiv = document.getElementById('result');
                
                if (result.error) {
                    resultDiv.innerHTML = '<div class="result error">❌ Error: ' + result.error + '</div>';
                    return;
                }
                
                let html = '<div class="result success">';
                html += '<h2>✅ OCR Results</h2>';
                
                // Best result summary
                if (result.best_result) {
                    html += '<h3>🏆 Best Performing Engine</h3>';
                    html += '<p><span class="engine">' + result.best_result.engine + '</span> - ';
                    html += 'Confidence: <span class="confidence">' + result.best_result.confidence.toFixed(1) + '%</span></p>';
                    html += '<p>Processing time: ' + result.best_result.processing_time.toFixed(2) + 's</p>';
                    
                    if (result.best_result.text) {
                        html += '<h3>📄 Extracted Text</h3>';
                        html += '<div style="background: white; padding: 15px; border: 1px solid #ddd; border-radius: 5px; max-height: 300px; overflow-y: auto;">';
                        html += '<pre style="white-space: pre-wrap; font-family: monospace; font-size: 12px;">' + 
                                escapeHtml(result.best_result.text) + '</pre>';
                        html += '</div>';
                    }
                }
                
                // All engines comparison
                if (result.all_results && result.all_results.length > 0) {
                    html += '<h3>📊 All Engines Comparison</h3>';
                    html += '<table>';
                    html += '<tr><th>Engine</th><th>Confidence</th><th>Time</th><th>Words</th><th>Status</th></tr>';
                    
                    result.all_results.forEach(engine_result => {
                        const status = engine_result.success ? '✅ Success' : '❌ Failed';
                        const confidence = engine_result.success ? engine_result.confidence.toFixed(1) + '%' : 'N/A';
                        const time = engine_result.processing_time ? engine_result.processing_time.toFixed(2) + 's' : 'N/A';
                        const words = engine_result.word_count || 'N/A';
                        
                        html += '<tr>';
                        html += '<td>' + engine_result.engine + '</td>';
                        html += '<td>' + confidence + '</td>';
                        html += '<td>' + time + '</td>';
                        html += '<td>' + words + '</td>';
                        html += '<td>' + status + '</td>';
                        html += '</tr>';
                    });
                    
                    html += '</table>';
                }
                
                // Certificate analysis
                if (result.certificate_analysis) {
                    html += '<h3>🎓 Certificate Analysis</h3>';
                    html += '<ul>';
                    html += '<li>LGCSE Keywords detected: ' + (result.certificate_analysis.has_lgcse_keywords ? '✅ Yes' : '❌ No') + '</li>';
                    html += '<li>Subject/Grade pattern: ' + (result.certificate_analysis.has_subject_grade_pattern ? '✅ Yes' : '❌ No') + '</li>';
                    html += '<li>Year pattern: ' + (result.certificate_analysis.has_year_pattern ? '✅ Yes' : '❌ No') + '</li>';
                    html += '<li>Candidate info: ' + (result.certificate_analysis.has_candidate_info ? '✅ Yes' : '❌ No') + '</li>';
                    html += '<li>Total words: ' + result.certificate_analysis.word_count + '</li>';
                    html += '</ul>';
                }
                
                html += '</div>';
                resultDiv.innerHTML = html;
            }
            
            function escapeHtml(text) {
                const map = {
                    '&': '&amp;',
                    '<': '&lt;',
                    '>': '&gt;',
                    '"': '&quot;',
                    "'": '&#039;'
                };
                return text.replace(/[&<>"']/g, m => map[m]);
            }
        </script>
    </body>
    </html>
    """

@app.post("/test-ocr")
async def test_ocr(file: UploadFile = File(...)):
    """Test OCR with uploaded file"""
    try:
        # Validate file type
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Test all OCR engines
            results = []
            
            # Test Tesseract
            try:
                from test_ocr_comprehensive import test_tesseract_ocr
                tesseract_result = test_tesseract_ocr(temp_file_path)
                results.append(tesseract_result)
            except Exception as e:
                results.append({'success': False, 'error': str(e), 'engine': 'Tesseract'})
            
            # Test OCR.space
            try:
                from test_ocr_comprehensive import test_ocr_space_api
                ocr_space_result = test_ocr_space_api(temp_file_path)
                results.append(ocr_space_result)
            except Exception as e:
                results.append({'success': False, 'error': str(e), 'engine': 'OCR.space'})
            
            # Test Multi-OCR
            try:
                multi_result = multi_processor.process_image_with_all_apis(temp_file_path)
                best_result = multi_result.get('best_result', {})
                
                results.append({
                    'success': True,
                    'engine': 'Multi-OCR Processor',
                    'confidence': best_result.get('confidence', 0),
                    'processing_time': multi_result.get('total_processing_time', 0),
                    'text': best_result.get('text', ''),
                    'word_count': len(best_result.get('text', '').split()),
                    'best_api': best_result.get('api_name'),
                    'apis_tried': multi_result.get('apis_used', [])
                })
            except Exception as e:
                results.append({'success': False, 'error': str(e), 'engine': 'Multi-OCR Processor'})
            
            # Find best result
            successful_results = [r for r in results if r.get('success', False)]
            best_result = max(successful_results, key=lambda x: x.get('confidence', 0)) if successful_results else None
            
            # Analyze certificate content
            certificate_analysis = None
            if best_result and best_result.get('text'):
                import re
                text = best_result['text']
                certificate_analysis = {
                    'word_count': len(text.split()),
                    'char_count': len(text),
                    'line_count': len(text.split('\\n')),
                    'has_lgcse_keywords': any(keyword in text.upper() for keyword in [
                        'LGCSE', 'EXAMINATIONS COUNCIL', 'LESOTHO', 'STATEMENT OF RESULTS',
                        'CANDIDATE NAME', 'CENTRE NUMBER', 'SUBJECT', 'GRADE'
                    ]),
                    'has_subject_grade_pattern': bool(re.search(r'[A-Z]+\\s+[A*ABCDEF]', text, re.IGNORECASE)),
                    'has_year_pattern': bool(re.search(r'20\\d{2}', text)),
                    'has_candidate_info': bool(re.search(r'(candidate|student|name)', text, re.IGNORECASE))
                }
            
            return {
                'success': True,
                'best_result': best_result,
                'all_results': results,
                'certificate_analysis': certificate_analysis,
                'summary': {
                    'total_engines_tested': len(results),
                    'successful_engines': len(successful_results),
                    'best_engine': best_result.get('engine') if best_result else None
                }
            }
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={'error': f'OCR processing failed: {str(e)}'}
        )

if __name__ == "__main__":
    print("🚀 Starting OCR Test Server...")
    print("📱 Open http://localhost:8000 in your browser")
    print("📷 Upload certificate images to test OCR functionality")
    uvicorn.run(app, host="0.0.0.0", port=8000)
