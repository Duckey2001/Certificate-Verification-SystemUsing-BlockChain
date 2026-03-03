import React, { useState, useRef } from 'react';

const CertificateScanner = ({ onScan, onClose }) => {
  const [scanning, setScanning] = useState(false);
  const [image, setImage] = useState(null);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setImage(e.target.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleScan = async () => {
    if (!image) {
      setError('Please upload an image first');
      return;
    }

    setScanning(true);
    setError('');

    try {
      // Simulate OCR processing
      await new Promise(resolve => setTimeout(resolve, 3000));

      // Mock scanned data - replace with actual OCR implementation
      const mockScannedData = {
        certificateNumber: 'LN150014229',
        candidateNumber: 'L5683/100298290',
        fullName: 'MOTLATSI MAHLOMOLA',
        dateOfBirth: '1997-10-17',
        examType: 'LGCSE',
        examSession: '2015-11',
        subjects: [
          { subject: 'Mathematics', grade: 'B(b)' },
          { subject: 'Biology', grade: 'C(c)' }
        ]
      };

      if (onScan) {
        onScan(mockScannedData);
      }
    } catch (err) {
      setError('Failed to scan certificate. Please try again.');
    } finally {
      setScanning(false);
    }
  };

  const handleReset = () => {
    setImage(null);
    setError('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-900">Certificate Scanner</h3>
        {onClose && (
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Upload Area */}
      <div className="mb-4">
        <div 
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer hover:border-blue-500 transition-colors ${
            image ? 'border-green-500 bg-green-50' : 'border-gray-300'
          }`}
          onClick={() => fileInputRef.current?.click()}
        >
          {image ? (
            <div className="space-y-2">
              <svg className="h-12 w-12 mx-auto text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
              </svg>
              <p className="text-sm text-green-600">Image uploaded successfully!</p>
              <p className="text-xs text-gray-500">Click to change image</p>
            </div>
          ) : (
            <div className="space-y-2">
              <svg className="h-12 w-12 mx-auto text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <p className="text-sm text-gray-600">Click to upload certificate image</p>
              <p className="text-xs text-gray-500">Supported: JPG, PNG, PDF (Max 5MB)</p>
            </div>
          )}
          <input
            ref={fileInputRef}
            type="file"
            accept="image/*,.pdf"
            onChange={handleFileUpload}
            className="hidden"
          />
        </div>
      </div>

      {/* Image Preview */}
      {image && (
        <div className="mb-4">
          <img src={image} alt="Certificate" className="max-h-48 mx-auto rounded-lg shadow-sm" />
        </div>
      )}

      {/* Actions */}
      <div className="flex space-x-2">
        {image && (
          <>
            <button
              onClick={handleScan}
              disabled={scanning}
              className="flex-1 py-2 px-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors"
            >
              {scanning ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Scanning...
                </span>
              ) : (
                'Scan Certificate'
              )}
            </button>
            <button
              onClick={handleReset}
              disabled={scanning}
              className="py-2 px-4 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 disabled:opacity-50 transition-colors"
            >
              Reset
            </button>
          </>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Instructions */}
      <div className="mt-4 text-xs text-gray-500 border-t pt-4">
        <p className="font-medium mb-1">Tips for better scanning:</p>
        <ul className="list-disc list-inside space-y-1">
          <li>Ensure good lighting and clear image</li>
          <li>Position the certificate straight</li>
          <li>Make sure all text is readable</li>
          <li>Avoid shadows and glare</li>
        </ul>
      </div>
    </div>
  );
};

export default CertificateScanner;