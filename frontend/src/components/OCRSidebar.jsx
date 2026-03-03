import React, { useState } from 'react';

const OCRSidebar = ({ isOpen, onClose, onScanComplete }) => {
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  const [error, setError] = useState('');

  const handleScan = async () => {
    setScanning(true);
    setError('');
    
    try {
      // Simulate OCR scanning - replace with actual OCR implementation
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const mockResult = {
        certificateNumber: 'LN150014229',
        candidateNumber: 'L5683/100298290',
        fullName: 'MOTLATSI MAHLOMOLA',
        examType: 'LGCSE',
        examSession: '2015-11',
        subjects: [
          { subject: 'Mathematics', grade: 'B(b)' },
          { subject: 'Biology', grade: 'C(c)' }
        ]
      };
      
      setScanResult(mockResult);
      if (onScanComplete) {
        onScanComplete(mockResult);
      }
    } catch (err) {
      setError('Failed to scan document. Please try again.');
    } finally {
      setScanning(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-white shadow-xl transform transition-transform duration-300 ease-in-out z-40 overflow-y-auto">
      <div className="p-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold text-gray-900">OCR Scanner</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Scan Area */}
        <div className="mb-6">
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
            {scanning ? (
              <div className="space-y-3">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
                <p className="text-sm text-gray-600">Scanning document...</p>
              </div>
            ) : scanResult ? (
              <div className="text-green-600">
                <svg className="h-12 w-12 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                </svg>
                <p className="text-sm font-medium">Scan Complete!</p>
              </div>
            ) : (
              <div>
                <svg className="h-12 w-12 mx-auto mb-2 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 9a2 2 0 012-2h.93a2 2 0 001.664-.89l.812-1.22A2 2 0 0110.07 4h3.86a2 2 0 011.664.89l.812 1.22A2 2 0 0018.07 7H19a2 2 0 012 2v9a2 2 0 01-2 2H5a2 2 0 01-2-2V9z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M15 13a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
                <p className="text-sm text-gray-600 mb-2">Upload certificate image</p>
                <p className="text-xs text-gray-500">Supported formats: JPG, PNG, PDF</p>
              </div>
            )}
          </div>
        </div>

        {/* Scan Button */}
        {!scanResult && (
          <button
            onClick={handleScan}
            disabled={scanning}
            className="w-full py-3 px-4 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
          >
            {scanning ? 'Scanning...' : 'Start Scan'}
          </button>
        )}

        {/* Error Message */}
        {error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {/* Scan Result */}
        {scanResult && (
          <div className="mt-6">
            <h3 className="font-semibold text-gray-900 mb-3">Scanned Information</h3>
            <div className="space-y-2 bg-gray-50 p-4 rounded-lg">
              <div>
                <label className="text-xs text-gray-500">Certificate Number</label>
                <p className="text-sm font-medium">{scanResult.certificateNumber}</p>
              </div>
              <div>
                <label className="text-xs text-gray-500">Candidate Number</label>
                <p className="text-sm font-medium">{scanResult.candidateNumber}</p>
              </div>
              <div>
                <label className="text-xs text-gray-500">Full Name</label>
                <p className="text-sm font-medium">{scanResult.fullName}</p>
              </div>
              <div>
                <label className="text-xs text-gray-500">Exam</label>
                <p className="text-sm font-medium">{scanResult.examType} - {scanResult.examSession}</p>
              </div>
            </div>

            <button
              onClick={() => setScanResult(null)}
              className="mt-4 w-full py-2 px-4 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Scan Another
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default OCRSidebar;