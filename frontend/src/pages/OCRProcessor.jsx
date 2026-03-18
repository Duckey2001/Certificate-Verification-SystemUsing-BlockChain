import React, { useState, useRef, useEffect, useCallback } from 'react';
import { certificateApi } from '../api';
import { useAuth } from '../contexts/AuthContext';
import './OCRProcessor.css';

const OCRProcessor = () => {
  const { user } = useAuth();
  const [selectedFile, setSelectedFile] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [extractedData, setExtractedData] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [previewUrl, setPreviewUrl] = useState(null);
  const [confidence, setConfidence] = useState(null);
  const [validationResult, setValidationResult] = useState(null);
  const [activeTab, setActiveTab] = useState('extracted');
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [extractionProgress, setExtractionProgress] = useState(0);
  const [selectedHistoryItem, setSelectedHistoryItem] = useState(null);
  const [expandedSections, setExpandedSections] = useState({
    studentInfo: true,
    certificateInfo: true,
    subjects: true,
    validation: true,
    rawData: false
  });
  
  const fileInputRef = useRef(null);
  const dropZoneRef = useRef(null);

  // Load processing history
  useEffect(() => {
    if (user) {
      loadProcessingHistory();
    }
  }, [user]);

  // Cleanup preview URLs
  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  const loadProcessingHistory = async () => {
    try {
      const history = await certificateApi.getOcrProcessingHistory();
      setHistory(history || []);
    } catch (error) {
      console.error('Failed to load history:', error);
    }
  };

  const validateFile = (file) => {
    // Check file type
    const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf'];
    const fileExtension = file.name.split('.').pop().toLowerCase();
    const validExtensions = ['jpg', 'jpeg', 'png', 'pdf'];
    
    if (!allowedTypes.includes(file.type) && !validExtensions.includes(fileExtension)) {
      throw new Error('Please select a valid image (JPG, PNG) or PDF file');
    }
    
    // Check file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      throw new Error('File size must be less than 10MB');
    }
    
    return true;
  };

  const handleFile = (file) => {
    try {
      validateFile(file);
      
      setSelectedFile(file);
      setError('');
      setSuccess('');
      setExtractedData(null);
      setConfidence(null);
      setValidationResult(null);
      setExtractionProgress(0);
      
      // Create preview URL for images
      if (file.type.startsWith('image/')) {
        if (previewUrl) {
          URL.revokeObjectURL(previewUrl);
        }
        const url = URL.createObjectURL(file);
        setPreviewUrl(url);
      } else {
        setPreviewUrl(null);
      }
    } catch (err) {
      setError(err.message);
    }
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      handleFile(file);
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select a file first');
      return;
    }

    if (!user) {
      setError('Please login to process certificates');
      return;
    }

    setProcessing(true);
    setError('');
    setSuccess('');
    setExtractionProgress(0);

    const formData = new FormData();
    formData.append('file', selectedFile);

    // Simulate progress for better UX
    const progressInterval = setInterval(() => {
      setExtractionProgress(prev => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + 10;
      });
    }, 300);

    try {
      const response = await certificateApi.extractCertificateData(formData);
      
      clearInterval(progressInterval);
      setExtractionProgress(100);

      // Process response data
      const data = response.data;
      const certificateData = data.certificate_data || data.form_data || data;
      
      setExtractedData(certificateData);
      setConfidence(data.validation?.confidence?.overall || certificateData.confidence_score || null);
      setValidationResult(data.validation || certificateData.verification);
      setSuccess('Certificate processed successfully!');
      
      // Refresh history
      await loadProcessingHistory();
      
      // Auto switch to extracted tab
      setActiveTab('extracted');
      
      // Auto-expand sections with data
      setExpandedSections({
        studentInfo: true,
        certificateInfo: true,
        subjects: true,
        validation: true,
        rawData: false
      });
      
    } catch (error) {
      clearInterval(progressInterval);
      console.error('Upload error:', error);
      if (error.response?.data?.detail) {
        setError(error.response.data.detail);
      } else if (error.message) {
        setError(error.message);
      } else {
        setError('Failed to process certificate. Please try again.');
      }
    } finally {
      setProcessing(false);
      setTimeout(() => setExtractionProgress(0), 1000);
    }
  };

  const handleClear = () => {
    setSelectedFile(null);
    setExtractedData(null);
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
      setPreviewUrl(null);
    }
    setConfidence(null);
    setValidationResult(null);
    setError('');
    setSuccess('');
    setActiveTab('extracted');
    setExtractionProgress(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleCopyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      setSuccess('Copied to clipboard!');
      setTimeout(() => setSuccess(''), 2000);
    } catch (err) {
      setError('Failed to copy to clipboard');
    }
  };

  const handleExportJSON = () => {
    if (!extractedData) return;
    
    const dataStr = JSON.stringify(extractedData, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,'+ encodeURIComponent(dataStr);
    
    const exportFileDefaultName = `certificate-data-${new Date().toISOString().slice(0,10)}.json`;
    
    const linkElement = document.createElement('a');
    linkElement.setAttribute('href', dataUri);
    linkElement.setAttribute('download', exportFileDefaultName);
    linkElement.click();
  };

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const getConfidenceColor = (score) => {
    if (!score && score !== 0) return 'text-gray-500';
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getConfidenceBadge = (score) => {
    if (!score && score !== 0) return 'bg-gray-100 text-gray-800';
    if (score >= 80) return 'bg-green-100 text-green-800';
    if (score >= 60) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const getConfidenceIcon = (score) => {
    if (!score && score !== 0) return '❓';
    if (score >= 80) return '✅';
    if (score >= 60) return '⚠️';
    return '❌';
  };

  const renderFileInfo = () => {
    if (!selectedFile) return null;

    return (
      <div className="file-info animate-slideDown">
        <div className="file-info-header">
          <div className="file-icon">
            {selectedFile.type.startsWith('image/') ? '🖼️' : '📄'}
          </div>
          <div className="file-details">
            <div className="file-name">{selectedFile.name}</div>
            <div className="file-meta">
              <span className="file-size">{(selectedFile.size / 1024).toFixed(1)} KB</span>
              <span className="file-type">{selectedFile.type || 'Unknown'}</span>
            </div>
          </div>
          <button
            onClick={handleClear}
            className="file-remove-btn"
            aria-label="Remove file"
          >
            ✕
          </button>
        </div>
        
        {previewUrl && (
          <div className="file-preview">
            <img 
              src={previewUrl} 
              alt="Preview" 
              className="preview-image"
              onClick={() => window.open(previewUrl, '_blank')}
            />
          </div>
        )}
      </div>
    );
  };

  const renderProgress = () => {
    if (!processing && extractionProgress === 0) return null;

    return (
      <div className="progress-container animate-slideDown">
        <div className="progress-header">
          <span className="progress-label">
            {extractionProgress < 100 ? 'Processing...' : 'Processing Complete!'}
          </span>
          <span className="progress-percentage">{extractionProgress}%</span>
        </div>
        <div className="progress-bar">
          <div 
            className="progress-fill"
            style={{ width: `${extractionProgress}%` }}
          />
        </div>
        <div className="progress-status">
          {extractionProgress < 30 && 'Preprocessing image...'}
          {extractionProgress >= 30 && extractionProgress < 60 && 'Extracting text...'}
          {extractionProgress >= 60 && extractionProgress < 90 && 'Analyzing data...'}
          {extractionProgress >= 90 && extractionProgress < 100 && 'Finalizing results...'}
          {extractionProgress === 100 && '✅ Done!'}
        </div>
      </div>
    );
  };

  const renderConfidenceIndicator = () => {
    if (!confidence && confidence !== 0) return null;

    return (
      <div className={`confidence-indicator ${getConfidenceBadge(confidence)}`}>
        <span className="confidence-icon">{getConfidenceIcon(confidence)}</span>
        <span className="confidence-value">{confidence.toFixed(1)}%</span>
        <span className="confidence-label">Confidence</span>
      </div>
    );
  };

  const renderExtractedData = () => {
    if (!extractedData) return null;

    const data = extractedData;

    return (
      <div className="extracted-data-container animate-slideUp">
        <div className="extracted-data-header">
          <h3>Extracted Certificate Data</h3>
          <div className="header-actions">
            {renderConfidenceIndicator()}
            <button
              onClick={handleExportJSON}
              className="export-btn"
              title="Export as JSON"
            >
              📥 Export
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="tabs-container">
          <button
            className={`tab-btn ${activeTab === 'extracted' ? 'active' : ''}`}
            onClick={() => setActiveTab('extracted')}
          >
            📋 Extracted Data
          </button>
          <button
            className={`tab-btn ${activeTab === 'preview' ? 'active' : ''}`}
            onClick={() => setActiveTab('preview')}
            disabled={!data.display_html}
          >
            👁️ Preview
          </button>
          <button
            className={`tab-btn ${activeTab === 'validation' ? 'active' : ''}`}
            onClick={() => setActiveTab('validation')}
          >
            ✓ Validation
          </button>
          <button
            className={`tab-btn ${activeTab === 'raw' ? 'active' : ''}`}
            onClick={() => setActiveTab('raw')}
          >
            📄 Raw Data
          </button>
        </div>

        {/* Tab Content */}
        <div className="tab-content">
          {activeTab === 'extracted' && (
            <div className="extracted-tab">
              {/* Student Information */}
              <div className="data-section">
                <div 
                  className="section-header"
                  onClick={() => toggleSection('studentInfo')}
                >
                  <span className="section-icon">{expandedSections.studentInfo ? '▼' : '▶'}</span>
                  <h4>Student Information</h4>
                  {(data.student_name || data.full_name) && (
                    <span className="section-badge">✓</span>
                  )}
                </div>
                
                {expandedSections.studentInfo && (
                  <div className="section-content">
                    <div className="data-grid">
                      <DataField 
                        label="Full Name" 
                        value={data.student_name || data.full_name}
                        onCopy={handleCopyToClipboard}
                      />
                      <DataField 
                        label="Student ID" 
                        value={data.student_id || data.candidate_number}
                        onCopy={handleCopyToClipboard}
                      />
                      <DataField 
                        label="Date of Birth" 
                        value={data.date_of_birth}
                      />
                      <DataField 
                        label="Institution" 
                        value={data.institution || data.school}
                      />
                      {data.student_surname && (
                        <DataField 
                          label="Surname" 
                          value={data.student_surname}
                        />
                      )}
                    </div>
                  </div>
                )}
              </div>

              {/* Certificate Information */}
              <div className="data-section">
                <div 
                  className="section-header"
                  onClick={() => toggleSection('certificateInfo')}
                >
                  <span className="section-icon">{expandedSections.certificateInfo ? '▼' : '▶'}</span>
                  <h4>Certificate Information</h4>
                  {(data.examination_year || data.certificate_type) && (
                    <span className="section-badge">✓</span>
                  )}
                </div>
                
                {expandedSections.certificateInfo && (
                  <div className="section-content">
                    <div className="data-grid">
                      <DataField 
                        label="Certificate Type" 
                        value={data.certificate_type}
                      />
                      <DataField 
                        label="Examination Year" 
                        value={data.examination_year}
                      />
                      <DataField 
                        label="Exam Board" 
                        value={data.exam_board}
                      />
                      <DataField 
                        label="Certificate Number" 
                        value={Array.isArray(data.certificate_numbers) 
                          ? data.certificate_numbers.join(', ') 
                          : data.certificate_number}
                        onCopy={handleCopyToClipboard}
                      />
                      <DataField 
                        label="Issue Date" 
                        value={data.issue_date || data.date_of_issue}
                      />
                      <DataField 
                        label="Exam Session" 
                        value={data.examination_session || data.exam_session}
                      />
                    </div>
                  </div>
                )}
              </div>

              {/* Subjects and Grades */}
              {(data.subjects_with_grades?.length > 0 || data.grades || data.full_results) && (
                <div className="data-section">
                  <div 
                    className="section-header"
                    onClick={() => toggleSection('subjects')}
                  >
                    <span className="section-icon">{expandedSections.subjects ? '▼' : '▶'}</span>
                    <h4>Subjects & Grades</h4>
                    <span className="section-count">
                      {data.subjects_with_grades?.length || 
                       Object.keys(data.grades || {}).length || 
                       data.full_results?.length || 0} subjects
                    </span>
                  </div>
                  
                  {expandedSections.subjects && (
                    <div className="section-content">
                      {data.subjects_with_grades?.length > 0 && (
                        <SubjectsTable subjects={data.subjects_with_grades} />
                      )}
                      
                      {data.grades && Object.keys(data.grades).length > 0 && (
                        <GradesTable grades={data.grades} />
                      )}
                      
                      {data.full_results?.length > 0 && (
                        <ResultsTable results={data.full_results} />
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* Certificate Hash */}
              {data.certificate_hash && (
                <div className="hash-container">
                  <span className="hash-label">Certificate Hash:</span>
                  <code className="hash-value">{data.certificate_hash}</code>
                  <button
                    onClick={() => handleCopyToClipboard(data.certificate_hash)}
                    className="hash-copy-btn"
                    title="Copy hash"
                  >
                    📋
                  </button>
                </div>
              )}
            </div>
          )}

          {activeTab === 'preview' && (
            <div className="preview-tab">
              {extractedData.display_html ? (
                <div 
                  className="certificate-preview"
                  dangerouslySetInnerHTML={{ __html: extractedData.display_html }}
                />
              ) : (
                <div className="preview-placeholder">
                  <span className="placeholder-icon">👁️</span>
                  <p>No preview available for this certificate</p>
                </div>
              )}
            </div>
          )}

          {activeTab === 'validation' && (
            <div className="validation-tab">
              {validationResult && (
                <ValidationDetails 
                  validation={validationResult}
                  confidence={confidence}
                  getConfidenceColor={getConfidenceColor}
                />
              )}
            </div>
          )}

          {activeTab === 'raw' && (
            <div className="raw-tab">
              <pre className="raw-json">
                {JSON.stringify(extractedData, null, 2)}
              </pre>
              <button
                onClick={() => handleCopyToClipboard(JSON.stringify(extractedData, null, 2))}
                className="copy-raw-btn"
              >
                📋 Copy Raw Data
              </button>
            </div>
          )}
        </div>
      </div>
    );
  };

  const renderHistory = () => {
    if (!showHistory || history.length === 0) return null;

    return (
      <div className="history-container animate-slideUp">
        <h3>Recent Processing History</h3>
        <div className="history-list">
          {history.map((item, idx) => (
            <div 
              key={idx} 
              className={`history-item ${selectedHistoryItem === idx ? 'selected' : ''}`}
              onClick={() => {
                setSelectedHistoryItem(idx);
                setExtractedData(item.data);
                setConfidence(item.confidence);
              }}
            >
              <div className="history-item-icon">
                {item.file_type?.startsWith('image/') ? '🖼️' : '📄'}
              </div>
              <div className="history-item-details">
                <div className="history-item-name">{item.filename}</div>
                <div className="history-item-meta">
                  <span className="history-item-date">
                    {new Date(item.processed_at).toLocaleString()}
                  </span>
                  {item.confidence && (
                    <span className={`history-item-confidence ${getConfidenceBadge(item.confidence)}`}>
                      {item.confidence.toFixed(0)}%
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="ocr-processor">
      <div className="processor-header">
        <h1>OCR Certificate Processor</h1>
        <p className="subtitle">Upload LGCSE certificates for intelligent data extraction and validation</p>
        {!user && (
          <div className="login-warning">
            ⚠️ Please login to process certificates
          </div>
        )}
      </div>

      <div className="processor-card">
        <div className="card-header">
          <h2>Upload Certificate</h2>
        </div>
        
        <div className="card-body">
          {/* File Upload Zone */}
          <div 
            ref={dropZoneRef}
            className={`upload-zone ${dragActive ? 'drag-active' : ''} ${selectedFile ? 'has-file' : ''}`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleFileSelect}
              accept=".pdf,.jpg,.jpeg,.png,image/jpeg,image/jpg,image/png,application/pdf"
              className="file-input"
              disabled={processing}
            />
            
            {!selectedFile ? (
              <div className="upload-placeholder">
                <div className="upload-icon">📄</div>
                <p className="upload-text">Drag & drop or click to select</p>
                <p className="upload-hint">Supported: PDF, JPEG, PNG (Max 10MB)</p>
              </div>
            ) : (
              renderFileInfo()
            )}
          </div>

          {/* Progress Indicator */}
          {renderProgress()}

          {/* Error/Success Messages */}
          {error && (
            <div className="message error">
              <span className="message-icon">❌</span>
              <span className="message-text">{error}</span>
              <button className="message-close" onClick={() => setError('')}>✕</button>
            </div>
          )}

          {success && (
            <div className="message success">
              <span className="message-icon">✅</span>
              <span className="message-text">{success}</span>
              <button className="message-close" onClick={() => setSuccess('')}>✕</button>
            </div>
          )}

          {/* Action Buttons */}
          <div className="action-buttons">
            <button
              onClick={handleUpload}
              disabled={!selectedFile || processing || !user}
              className="btn btn-primary"
            >
              {processing ? (
                <>
                  <span className="spinner" />
                  Processing...
                </>
              ) : (
                <>
                  <span className="btn-icon">🔍</span>
                  Extract Certificate Data
                </>
              )}
            </button>

            {user && history.length > 0 && (
              <button
                onClick={() => setShowHistory(!showHistory)}
                className="btn btn-secondary"
              >
                <span className="btn-icon">{showHistory ? '📋' : '📜'}</span>
                {showHistory ? 'Hide' : 'Show'} History
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Extracted Data Display */}
      {renderExtractedData()}

      {/* Processing History */}
      {renderHistory()}
    </div>
  );
};

// Helper Components

const DataField = ({ label, value, onCopy }) => {
  if (!value && value !== 0) return null;
  
  return (
    <div className="data-field">
      <span className="data-label">{label}:</span>
      <div className="data-value-container">
        <span className="data-value">{String(value)}</span>
        {onCopy && (
          <button
            onClick={() => onCopy(String(value))}
            className="data-copy-btn"
            title={`Copy ${label}`}
          >
            📋
          </button>
        )}
      </div>
    </div>
  );
};

const SubjectsTable = ({ subjects }) => (
  <table className="subjects-table">
    <thead>
      <tr>
        <th>Subject</th>
        <th>Grade</th>
      </tr>
    </thead>
    <tbody>
      {subjects.map((item, idx) => (
        <tr key={idx}>
          <td>{item.subject || item}</td>
          <td className="grade-cell">{item.grade || '—'}</td>
        </tr>
      ))}
    </tbody>
  </table>
);

const GradesTable = ({ grades }) => (
  <table className="subjects-table">
    <thead>
      <tr>
        <th>Subject</th>
        <th>Grade</th>
        <th>Level</th>
      </tr>
    </thead>
    <tbody>
      {Object.entries(grades).map(([subject, details], idx) => (
        <tr key={idx}>
          <td>{subject}</td>
          <td className="grade-cell">{details.grade || 'N/A'}</td>
          <td>{details.level || '-'}</td>
        </tr>
      ))}
    </tbody>
  </table>
);

const ResultsTable = ({ results }) => (
  <table className="subjects-table">
    <thead>
      <tr>
        <th>Subject</th>
        <th>Grade</th>
        <th>Level</th>
      </tr>
    </thead>
    <tbody>
      {results.map((result, idx) => (
        <tr key={idx}>
          <td>{result.subject}</td>
          <td className="grade-cell">{result.grade}</td>
          <td>{result.level || '-'}</td>
        </tr>
      ))}
    </tbody>
  </table>
);

const ValidationDetails = ({ validation, confidence, getConfidenceColor }) => {
  if (!validation) return null;

  return (
    <div className="validation-details">
      {/* Confidence Scores */}
      {validation.confidence && (
        <div className="validation-section">
          <h5>Confidence Scores</h5>
          <div className="confidence-grid">
            {Object.entries(validation.confidence).map(([key, value]) => (
              <div key={key} className="confidence-item">
                <span className="confidence-item-label">
                  {key.replace(/_/g, ' ')}:
                </span>
                <span className={`confidence-item-value ${getConfidenceColor(value)}`}>
                  {value.toFixed(1)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Validation Status */}
      <div className="validation-section">
        <h5>Validation Status</h5>
        <div className="status-grid">
          <StatusItem 
            label="LGCSE Certificate" 
            value={validation.is_lgcse ? '✓ Yes' : '✗ No'}
            status={validation.is_lgcse ? 'success' : 'error'}
          />
          <StatusItem 
            label="Subjects Found" 
            value={validation.subjects_found || 0}
          />
          <StatusItem 
            label="Certificate Numbers" 
            value={validation.certificate_numbers_found || 0}
          />
          <StatusItem 
            label="In Database" 
            value={validation.in_database ? '✓ Yes' : '✗ No'}
            status={validation.in_database ? 'success' : 'warning'}
          />
        </div>
      </div>

      {/* Missing Fields */}
      {validation.missing_required?.length > 0 && (
        <div className="validation-section warning">
          <h5>Missing Required Fields</h5>
          <ul className="missing-fields-list">
            {validation.missing_required.map((field, idx) => (
              <li key={idx}>{field.replace(/_/g, ' ')}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Issues */}
      {validation.issues?.length > 0 && (
        <div className="validation-section error">
          <h5>Issues Found</h5>
          <ul className="issues-list">
            {validation.issues.map((issue, idx) => (
              <li key={idx}>{issue}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Warnings */}
      {validation.warnings?.length > 0 && (
        <div className="validation-section warning">
          <h5>Warnings</h5>
          <ul className="warnings-list">
            {validation.warnings.map((warning, idx) => (
              <li key={idx}>{warning}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Quality Score */}
      {validation.quality_score !== undefined && (
        <div className="quality-score">
          <span className="quality-label">Quality Score:</span>
          <span className={`quality-value ${
            validation.quality_score >= 80 ? 'excellent' :
            validation.quality_score >= 60 ? 'good' :
            validation.quality_score >= 40 ? 'fair' : 'poor'
          }`}>
            {validation.quality_score}/100
          </span>
        </div>
      )}

      {/* Validation Message */}
      {validation.message && (
        <div className="validation-message">
          {validation.message}
        </div>
      )}
    </div>
  );
};

const StatusItem = ({ label, value, status = 'neutral' }) => (
  <div className={`status-item status-${status}`}>
    <span className="status-label">{label}:</span>
    <span className="status-value">{value}</span>
  </div>
);

export default OCRProcessor;