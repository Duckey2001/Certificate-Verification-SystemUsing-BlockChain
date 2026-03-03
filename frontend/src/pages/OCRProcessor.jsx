import React, { useState, useRef, useEffect } from 'react';
import { certificateApi } from '../api';
import { useAuth } from '../contexts/AuthContext';

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
  const [activeTab, setActiveTab] = useState('extracted'); // 'extracted', 'preview', 'validation'
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const fileInputRef = useRef(null);

  // Load processing history
  useEffect(() => {
    if (user) {
      loadProcessingHistory();
    }
  }, [user]);

  const loadProcessingHistory = async () => {
    try {
      const history = await certificateApi.getOcrProcessingHistory();
      setHistory(history || []);
    } catch (error) {
      console.error('Failed to load history:', error);
    }
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      // Check file type
      const allowedTypes = ['image/jpeg', 'image/jpg', 'image/png', 'application/pdf'];
      const fileExtension = file.name.split('.').pop().toLowerCase();
      const validExtensions = ['jpg', 'jpeg', 'png', 'pdf'];
      
      if (!allowedTypes.includes(file.type) && !validExtensions.includes(fileExtension)) {
        setError('Please select a valid image (JPG, PNG) or PDF file');
        return;
      }
      
      // Check file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        setError('File size must be less than 10MB');
        return;
      }
      
      setSelectedFile(file);
      setError('');
      setSuccess('');
      setExtractedData(null);
      setConfidence(null);
      setValidationResult(null);
      
      // Create preview URL for images
      if (file.type.startsWith('image/')) {
        const url = URL.createObjectURL(file);
        setPreviewUrl(url);
      } else {
        setPreviewUrl(null);
      }
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

    const formData = new FormData();
    formData.append('file', selectedFile);

    try {
      const response = await certificateApi.extractCertificateData(formData);

      setExtractedData(response.data);
      setConfidence(response.data.validation?.confidence?.overall || null);
      setValidationResult(response.data.validation);
      setSuccess('Certificate processed successfully!');
      
      // Refresh history
      await loadProcessingHistory();
      
      // Auto switch to extracted tab
      setActiveTab('extracted');
      
    } catch (error) {
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
    }
  };

  const handleClear = () => {
    setSelectedFile(null);
    setExtractedData(null);
    setPreviewUrl(null);
    setConfidence(null);
    setValidationResult(null);
    setError('');
    setSuccess('');
    setActiveTab('extracted');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleCopyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setSuccess('Copied to clipboard!');
    setTimeout(() => setSuccess(''), 2000);
  };

  const getConfidenceColor = (score) => {
    if (!score) return 'text-gray-500';
    if (score >= 80) return 'text-green-600';
    if (score >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getConfidenceBadge = (score) => {
    if (!score) return null;
    if (score >= 80) return 'bg-green-100 text-green-800';
    if (score >= 60) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const renderExtractedData = () => {
    if (!extractedData) return null;

    const data = extractedData.certificate_data || extractedData.form_data || extractedData;
    const validation = extractedData.validation || {};

    return (
      <div className="bg-white rounded-lg shadow-md p-6 mt-6">
        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="flex -mb-px space-x-8">
            <button
              onClick={() => setActiveTab('extracted')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'extracted'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Extracted Data
            </button>
            <button
              onClick={() => setActiveTab('preview')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'preview'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Certificate Preview
            </button>
            <button
              onClick={() => setActiveTab('validation')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'validation'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Validation Details
            </button>
          </nav>
        </div>

        {/* Extracted Data Tab */}
        {activeTab === 'extracted' && (
          <div>
            {/* Confidence Score */}
            {confidence && (
              <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-gray-700">Overall Confidence:</span>
                  <span className={`text-lg font-bold ${getConfidenceColor(confidence)}`}>
                    {confidence.toFixed(1)}%
                  </span>
                </div>
                <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div 
                    className={`h-2 rounded-full ${
                      confidence >= 80 ? 'bg-green-500' :
                      confidence >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                    }`}
                    style={{ width: `${confidence}%` }}
                  />
                </div>
              </div>
            )}

            {/* Student Information */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                  <svg className="w-4 h-4 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  Student Information
                </h4>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-500">Full Name:</span>
                    <div className="flex items-center">
                      <span className="font-medium text-gray-800 mr-2">{data.student_name || data.full_name || 'Not found'}</span>
                      {data.student_name && (
                        <button
                          onClick={() => handleCopyToClipboard(data.student_name)}
                          className="text-gray-400 hover:text-gray-600"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                          </svg>
                        </button>
                      )}
                    </div>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-xs text-gray-500">Student ID:</span>
                    <span className="font-medium text-gray-800">{data.student_id || data.candidate_number || 'Not found'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-xs text-gray-500">Date of Birth:</span>
                    <span className="font-medium text-gray-800">{data.date_of_birth || 'Not found'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-xs text-gray-500">Institution:</span>
                    <span className="font-medium text-gray-800">{data.institution || data.school || 'Not found'}</span>
                  </div>
                </div>
              </div>
              
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                  <svg className="w-4 h-4 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                  Certificate Information
                </h4>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-xs text-gray-500">Issue Date:</span>
                    <span className="font-medium text-gray-800">{data.issue_date || data.date_of_issue || 'Not found'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-xs text-gray-500">Exam Session:</span>
                    <span className="font-medium text-gray-800">{data.examination_session || data.exam_session || 'Not found'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-xs text-gray-500">Certificate Number:</span>
                    <span className="font-medium text-gray-800">
                      {Array.isArray(data.certificate_numbers) 
                        ? data.certificate_numbers.join(', ') 
                        : data.certificate_number || 'Not found'}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Subjects and Grades */}
            {data.grades && Object.keys(data.grades).length > 0 && (
              <div className="mb-6">
                <h4 className="text-sm font-semibold text-gray-700 mb-3 flex items-center">
                  <svg className="w-4 h-4 mr-2 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                  Subjects and Grades
                </h4>
                <div className="bg-gray-50 rounded-lg overflow-hidden">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-100">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Subject</th>
                        <th className="px-4 py-2 text-center text-xs font-medium text-gray-600 uppercase">Grade</th>
                        <th className="px-4 py-2 text-center text-xs font-medium text-gray-600 uppercase">Level</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {Object.entries(data.grades).map(([subject, details], idx) => (
                        <tr key={idx} className="hover:bg-gray-100">
                          <td className="px-4 py-2 text-sm text-gray-800">{subject}</td>
                          <td className="px-4 py-2 text-sm text-center font-medium">{details.grade || 'N/A'}</td>
                          <td className="px-4 py-2 text-sm text-center text-gray-600">{details.level || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                {data.subjects_reported && (
                  <p className="mt-2 text-xs text-gray-500">Subjects Reported: {data.subjects_reported}</p>
                )}
              </div>
            )}

            {/* Full Results Array */}
            {data.full_results && data.full_results.length > 0 && (
              <div className="mb-6">
                <h4 className="text-sm font-semibold text-gray-700 mb-3">Detailed Results</h4>
                <div className="bg-gray-50 rounded-lg overflow-hidden">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-100">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-gray-600 uppercase">Subject</th>
                        <th className="px-4 py-2 text-center text-xs font-medium text-gray-600 uppercase">Grade</th>
                        <th className="px-4 py-2 text-center text-xs font-medium text-gray-600 uppercase">Level</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {data.full_results.map((result, idx) => (
                        <tr key={idx} className="hover:bg-gray-100">
                          <td className="px-4 py-2 text-sm text-gray-800">{result.subject}</td>
                          <td className="px-4 py-2 text-sm text-center font-medium">{result.grade}</td>
                          <td className="px-4 py-2 text-sm text-center text-gray-600">{result.level || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* Certificate Hash */}
            {extractedData.certificate_hash && (
              <div className="mt-4 p-3 bg-gray-100 rounded-lg">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-gray-600">Certificate Hash:</span>
                  <div className="flex items-center">
                    <code className="text-xs bg-white px-2 py-1 rounded mr-2">
                      {extractedData.certificate_hash}
                    </code>
                    <button
                      onClick={() => handleCopyToClipboard(extractedData.certificate_hash)}
                      className="text-gray-400 hover:text-gray-600"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Preview Tab */}
        {activeTab === 'preview' && (
          <div>
            {extractedData.display_html ? (
              <div 
                className="certificate-preview"
                dangerouslySetInnerHTML={{ __html: extractedData.display_html }}
              />
            ) : (
              <div className="text-center py-8 text-gray-500">
                No preview available for this certificate
              </div>
            )}
          </div>
        )}

        {/* Validation Tab */}
        {activeTab === 'validation' && validationResult && (
          <div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Confidence Scores */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="text-sm font-semibold text-gray-700 mb-3">Confidence Scores</h4>
                <div className="space-y-3">
                  {validationResult.confidence && Object.entries(validationResult.confidence).map(([key, value]) => (
                    <div key={key}>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-gray-600 capitalize">{key.replace('_', ' ')}:</span>
                        <span className={`font-medium ${getConfidenceColor(value)}`}>{value.toFixed(1)}%</span>
                      </div>
                      <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
                        <div 
                          className={`h-1.5 rounded-full ${
                            value >= 80 ? 'bg-green-500' :
                            value >= 60 ? 'bg-yellow-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${value}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Validation Status */}
              <div className="bg-gray-50 p-4 rounded-lg">
                <h4 className="text-sm font-semibold text-gray-700 mb-3">Validation Status</h4>
                <div className="space-y-2">
                  <div className="flex items-center">
                    <span className={`w-2 h-2 rounded-full mr-2 ${
                      validationResult.is_lgcse ? 'bg-green-500' : 'bg-red-500'
                    }`}></span>
                    <span className="text-sm text-gray-600">LGCSE Certificate:</span>
                    <span className={`ml-2 text-sm font-medium ${
                      validationResult.is_lgcse ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {validationResult.is_lgcse ? 'Yes' : 'No'}
                    </span>
                  </div>
                  <div className="flex items-center">
                    <span className="w-2 h-2 bg-blue-500 rounded-full mr-2"></span>
                    <span className="text-sm text-gray-600">Subjects Found:</span>
                    <span className="ml-2 text-sm font-medium">{validationResult.subjects_found || 0}</span>
                  </div>
                  <div className="flex items-center">
                    <span className="w-2 h-2 bg-purple-500 rounded-full mr-2"></span>
                    <span className="text-sm text-gray-600">Certificate Numbers:</span>
                    <span className="ml-2 text-sm font-medium">{validationResult.certificate_numbers_found || 0}</span>
                  </div>
                  <div className="flex items-center">
                    <span className="w-2 h-2 bg-yellow-500 rounded-full mr-2"></span>
                    <span className="text-sm text-gray-600">In Database:</span>
                    <span className={`ml-2 text-sm font-medium ${
                      validationResult.in_database ? 'text-green-600' : 'text-gray-500'
                    }`}>
                      {validationResult.in_database ? 'Yes' : 'No'}
                    </span>
                  </div>
                </div>
                {validationResult.message && (
                  <div className="mt-3 p-2 bg-blue-50 rounded">
                    <p className="text-xs text-blue-800">{validationResult.message}</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  const renderHistory = () => {
    if (!showHistory || history.length === 0) return null;

    return (
      <div className="bg-white rounded-lg shadow-md p-6 mt-6">
        <h3 className="text-lg font-semibold mb-4 text-gray-800">Recent Processing History</h3>
        <div className="space-y-3">
          {history.map((item, idx) => (
            <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                  <span className="text-blue-600">📄</span>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-800">{item.filename}</p>
                  <p className="text-xs text-gray-500">{new Date(item.processed_at).toLocaleString()}</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                {item.confidence && (
                  <span className={`text-xs font-medium px-2 py-1 rounded-full ${
                    item.confidence >= 80 ? 'bg-green-100 text-green-800' :
                    item.confidence >= 60 ? 'bg-yellow-100 text-yellow-800' :
                    'bg-red-100 text-red-800'
                  }`}>
                    {item.confidence.toFixed(0)}%
                  </span>
                )}
                <button
                  onClick={() => setExtractedData(item.data)}
                  className="text-sm text-blue-600 hover:text-blue-800"
                >
                  View
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-8">
      <div className="max-w-6xl mx-auto px-4">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-2 bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
            OCR Certificate Processor
          </h1>
          <p className="text-gray-600">Upload LGCSE certificates for intelligent data extraction and validation</p>
          {!user && (
            <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg inline-block">
              <p className="text-sm text-yellow-800">Please login to process certificates</p>
            </div>
          )}
        </div>

        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          <div className="px-6 py-4 bg-gradient-to-r from-blue-600 to-purple-600">
            <h2 className="text-lg font-semibold text-white flex items-center">
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              Upload Certificate
            </h2>
          </div>
          
          <div className="p-6">
            {/* File Upload Section */}
            <div className="mb-6">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Certificate File
              </label>
              <div className="relative border-2 border-dashed border-gray-300 rounded-xl p-6 text-center hover:border-blue-500 transition-colors">
                <input
                  type="file"
                  ref={fileInputRef}
                  onChange={handleFileSelect}
                  accept=".pdf,.jpg,.jpeg,.png,image/jpeg,image/jpg,image/png,application/pdf"
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  disabled={processing}
                />
                <div className="space-y-2">
                  <div className="text-4xl mb-2">📄</div>
                  <p className="text-gray-600">Drag and drop or click to select</p>
                  <p className="text-sm text-gray-400">Supported: PDF, JPEG, PNG (Max 10MB)</p>
                </div>
              </div>
            </div>

            {/* Selected File Info */}
            {selectedFile && (
              <div className="mb-6 p-4 bg-blue-50 rounded-xl">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <svg className="h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                      </svg>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-blue-900">{selectedFile.name}</p>
                      <p className="text-sm text-blue-700">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                    </div>
                  </div>
                  <button
                    onClick={handleClear}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                {previewUrl && (
                  <div className="mt-3">
                    <img 
                      src={previewUrl} 
                      alt="Preview" 
                      className="max-h-48 rounded-lg border border-blue-200"
                    />
                  </div>
                )}
              </div>
            )}

            {/* Error and Success Messages */}
            {error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-xl">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-red-800">{error}</p>
                  </div>
                </div>
              </div>
            )}

            {success && (
              <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-xl animate-slideDown">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <p className="text-sm text-green-800">{success}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Process Button */}
            <div className="flex items-center justify-between">
              <button
                onClick={handleUpload}
                disabled={!selectedFile || processing || !user}
                className="inline-flex items-center px-6 py-3 border border-transparent text-base font-medium rounded-xl text-white bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-105"
              >
                {processing ? (
                  <>
                    <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Processing... {confidence ? `${confidence.toFixed(0)}%` : ''}
                  </>
                ) : (
                  <>
                    <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Extract Certificate Data
                  </>
                )}
              </button>

              {user && history.length > 0 && (
                <button
                  onClick={() => setShowHistory(!showHistory)}
                  className="text-sm text-gray-600 hover:text-gray-800 flex items-center"
                >
                  <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
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

      {/* Styles */}
      <style jsx>{`
        @keyframes slideDown {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .animate-slideDown {
          animation: slideDown 0.3s ease-out;
        }
        
        .certificate-preview {
          font-family: 'Times New Roman', serif;
        }
      `}</style>
    </div>
  );
};

export default OCRProcessor;