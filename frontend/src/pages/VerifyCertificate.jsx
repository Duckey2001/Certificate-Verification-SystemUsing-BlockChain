import React, { useState } from 'react';
import pdfProcessor from '../services/pdfProcessor';
import { certificateApi } from '../api';

const VerifyCertificate = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [verificationResult, setVerificationResult] = useState(null);
  const [extractedData, setExtractedData] = useState(null);
  const [error, setError] = useState('');
  const [certificateHash, setCertificateHash] = useState('');
  const [verificationMode, setVerificationMode] = useState('file'); // 'file' or 'hash'

  const handleFileChange = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedFile(file);
      setVerificationResult(null);
      setExtractedData(null);
      setError('');
    }
  };

  const handleVerify = async () => {
    if (!selectedFile && !certificateHash.trim()) {
      setError('Please select a file or enter a certificate hash');
      return;
    }

    setIsProcessing(true);
    setError('');

    try {
      let processedData = null;

      // If file is selected, process it with PDF.js first
      if (selectedFile) {
        const pdfResult = await pdfProcessor.processCertificate(selectedFile);
        
        if (pdfResult.success) {
          setExtractedData(pdfResult.data);
          processedData = pdfResult.data;
        } else {
          throw new Error(pdfResult.error);
        }
      }

      // Now verify against backend
      const formData = new FormData();
      
      if (selectedFile) {
        formData.append('file', selectedFile);
      }
      
      if (certificateHash.trim()) {
        formData.append('certificate_hash', certificateHash.trim());
      }

      const response = await certificateApi.verifyCertificate(formData);
      
      setVerificationResult({
        isValid: response.verified || response.valid,
        blockchain: response.blockchain_verified || true,
        message: response.verified ? '✅ VALID CERTIFICATE' : '❌ INVALID CERTIFICATE',
        details: response,
        extractedData: processedData
      });
      
      console.log('Verification Result:', response);
      console.log('Extracted Data:', processedData);
      
    } catch (error) {
      console.error('Verification Error:', error);
      setError(error.message || 'Error processing certificate');
      setVerificationResult({
        isValid: false,
        blockchain: false,
        message: '❌ Error processing certificate',
        error: error.message
      });
    } finally {
      setIsProcessing(false);
    }
  };

  const generateVerificationId = () => {
    return 'VER-' + Math.random().toString(36).substr(2, 9).toUpperCase();
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-12 px-4">
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-blue-600 to-indigo-600 px-8 py-6">
            <h1 className="text-3xl font-bold text-white">Verify Certificate</h1>
            <p className="text-blue-100 mt-2">Upload a certificate or enter hash to verify authenticity</p>
          </div>

          <div className="p-8">
            {/* Verification Method Selection */}
            <div className="mb-8">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Verification Method</h3>
              <div className="flex space-x-4 mb-6">
                <button
                  onClick={() => setVerificationMode('file')}
                  className={`px-6 py-3 rounded-lg font-medium transition-all ${
                    verificationMode === 'file'
                      ? 'bg-blue-600 text-white shadow-lg'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  📄 Upload Certificate
                </button>
                <button
                  onClick={() => setVerificationMode('hash')}
                  className={`px-6 py-3 rounded-lg font-medium transition-all ${
                    verificationMode === 'hash'
                      ? 'bg-blue-600 text-white shadow-lg'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  🔗 Certificate Hash
                </button>
                <button
                  onClick={() => setVerificationMode('both')}
                  className={`px-6 py-3 rounded-lg font-medium transition-all ${
                    verificationMode === 'both'
                      ? 'bg-blue-600 text-white shadow-lg'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  🔄 Both Methods
                </button>
              </div>
            </div>

            {/* File Upload Section */}
            {(verificationMode === 'file' || verificationMode === 'both') && (
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Certificate File
                </label>
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center hover:border-blue-400 transition-colors">
                  <input
                    type="file"
                    accept=".pdf,.jpg,.jpeg,.png"
                    onChange={handleFileChange}
                    className="hidden"
                    id="file-upload"
                  />
                  <label htmlFor="file-upload" className="cursor-pointer">
                    <div className="text-gray-400 mb-2">
                      <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                      </svg>
                    </div>
                    <span className="text-blue-600 font-medium">Click to upload</span>
                    <span className="text-gray-500"> or drag and drop</span>
                    <p className="text-xs text-gray-400 mt-2">PDF, JPG, PNG up to 10MB</p>
                  </label>
                </div>
                {selectedFile && (
                  <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                    <div className="flex items-center">
                      <svg className="h-5 w-5 text-green-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <span className="text-green-700 font-medium">{selectedFile.name}</span>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Hash Input Section */}
            {(verificationMode === 'hash' || verificationMode === 'both') && (
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Certificate Hash
                </label>
                <input
                  type="text"
                  value={certificateHash}
                  onChange={(e) => setCertificateHash(e.target.value)}
                  placeholder="0x1234567890abcdef..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            )}

            {/* Error Message */}
            {error && (
              <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-center">
                  <svg className="h-5 w-5 text-red-500 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <span className="text-red-700">{error}</span>
                </div>
              </div>
            )}

            {/* Verify Button */}
            <button
              onClick={handleVerify}
              disabled={(!selectedFile && !certificateHash.trim()) || isProcessing}
              className="w-full py-4 px-6 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold rounded-lg shadow-lg hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
            >
              {isProcessing ? (
                <div className="flex items-center justify-center">
                  <svg className="animate-spin h-5 w-5 mr-3" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  Processing...
                </div>
              ) : (
                'Verify Certificate'
              )}
            </button>
          </div>
        </div>

        {/* Verification Result */}
        {verificationResult && (
          <div className="mt-8 bg-white rounded-2xl shadow-xl overflow-hidden">
            <div className={`px-8 py-6 ${
              verificationResult.isValid ? 'bg-gradient-to-r from-green-600 to-green-700' : 'bg-gradient-to-r from-red-600 to-red-700'
            }`}>
              <h2 className="text-2xl font-bold text-white">Verification Result</h2>
            </div>
            
            <div className="p-8">
              <div className={`p-6 rounded-lg mb-6 ${
                verificationResult.isValid ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
              }`}>
                <div className="flex items-center">
                  <span className="text-3xl mr-4">{verificationResult.isValid ? '✅' : '❌'}</span>
                  <div>
                    <h3 className={`text-xl font-semibold ${
                      verificationResult.isValid ? 'text-green-800' : 'text-red-800'
                    }`}>
                      {verificationResult.message}
                    </h3>
                    <p className={`text-sm mt-1 ${
                      verificationResult.isValid ? 'text-green-600' : 'text-red-600'
                    }`}>
                      Blockchain: {verificationResult.blockchain ? '✅ Verified' : '❌ Not Verified'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Certificate Details */}
              {extractedData && (
                <div className="bg-gray-50 rounded-lg p-6">
                  <h3 className="text-lg font-semibold text-gray-800 mb-4">Extracted Certificate Details</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="bg-white p-4 rounded-lg border border-gray-200">
                      <label className="text-sm font-medium text-gray-500">Student Name</label>
                      <p className="text-lg font-semibold text-gray-800">
                        {extractedData.studentName || 'Not extracted'}
                      </p>
                    </div>

                    <div className="bg-white p-4 rounded-lg border border-gray-200">
                      <label className="text-sm font-medium text-gray-500">Student ID</label>
                      <p className="text-lg font-semibold text-gray-800">
                        {extractedData.studentId || 'Not extracted'}
                      </p>
                    </div>

                    <div className="bg-white p-4 rounded-lg border border-gray-200">
                      <label className="text-sm font-medium text-gray-500">Institution</label>
                      <p className="text-lg font-semibold text-gray-800">
                        {extractedData.institution || 'Not extracted'}
                      </p>
                    </div>

                    <div className="bg-white p-4 rounded-lg border border-gray-200">
                      <label className="text-sm font-medium text-gray-500">Issue Date</label>
                      <p className="text-lg font-semibold text-gray-800">
                        {extractedData.issueDate || 'Not extracted'}
                      </p>
                    </div>

                    <div className="bg-white p-4 rounded-lg border border-gray-200">
                      <label className="text-sm font-medium text-gray-500">Certificate Number</label>
                      <p className="text-lg font-semibold text-gray-800">
                        {extractedData.certificateNumber || 'Not extracted'}
                      </p>
                    </div>

                    {extractedData.subjects && extractedData.subjects.length > 0 && (
                      <div className="bg-white p-4 rounded-lg border border-gray-200 md:col-span-2">
                        <label className="text-sm font-medium text-gray-500 block mb-2">Subjects</label>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                          {extractedData.subjects.map((subject, index) => (
                            <div key={index} className="bg-blue-50 px-3 py-2 rounded text-sm">
                              <span className="font-medium">{subject.name}</span>: 
                              <span className="ml-1 font-bold text-blue-600">{subject.grade}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Verification ID */}
              <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="flex justify-between items-center">
                  <label className="text-sm font-medium text-blue-700">Verification ID</label>
                  <span className="font-mono text-blue-900 font-bold">
                    {generateVerificationId()}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VerifyCertificate;
