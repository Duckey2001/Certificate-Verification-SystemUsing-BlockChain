import React, { useState } from 'react';
import { FiCheck, FiX, FiRefreshCw, FiEye, FiFileText, FiLoader } from 'react-icons/fi';

const OCRSidebar = ({ 
  displayHtml, 
  extractedData, 
  confidence, 
  onClose, 
  onClear, 
  onAccept, 
  onRetry,
  isLoading = false 
}) => {
  const [showRawData, setShowRawData] = useState(false);

  if (!displayHtml && !isLoading) return null;

  return (
    <div className="fixed inset-y-0 right-0 w-96 bg-white shadow-xl transform transition-transform duration-300 ease-in-out z-40 overflow-y-auto">
      <div className="p-6">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-bold text-gray-900">
            {isLoading ? 'Processing Certificate...' : 'Extracted Certificate Data'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
            disabled={isLoading}
          >
            <FiX className="h-6 w-6" />
          </button>
        </div>

        {/* Loading State */}
        {isLoading && (
          <div className="flex flex-col items-center justify-center py-12">
            <FiLoader className="h-12 w-12 text-blue-600 animate-spin mb-4" />
            <p className="text-gray-600 text-center">Extracting certificate data using OCR...</p>
            <p className="text-sm text-gray-500 mt-2">This may take a few moments</p>
          </div>
        )}

        {/* Extracted Data Display */}
        {!isLoading && displayHtml && (
          <>
            {/* Confidence Score */}
            <div className={`mb-6 p-4 rounded-lg ${
              confidence > 80 ? 'bg-green-50 border border-green-200' :
              confidence > 60 ? 'bg-yellow-50 border border-yellow-200' :
              'bg-red-50 border border-red-200'
            }`}>
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">
                  {confidence > 80 ? 'High Confidence' :
                   confidence > 60 ? 'Medium Confidence' : 'Low Confidence'}
                </span>
                <span className={`text-lg font-bold ${
                  confidence > 80 ? 'text-green-600' :
                  confidence > 60 ? 'text-yellow-600' : 'text-red-600'
                }`}>
                  {confidence}%
                </span>
              </div>
            </div>

            {/* Extracted Data Display */}
            <div className="mb-6">
              <div className="flex items-center justify-between mb-3">
                <h3 className="font-semibold text-gray-900">Certificate Information</h3>
                <button
                  onClick={() => setShowRawData(!showRawData)}
                  className="text-sm text-blue-600 hover:text-blue-800 flex items-center gap-1"
                >
                  <FiEye className="h-4 w-4" />
                  {showRawData ? 'Formatted View' : 'Raw Data'}
                </button>
              </div>
              
              {showRawData ? (
                <div className="bg-gray-50 p-4 rounded-lg text-sm">
                  <pre className="whitespace-pre-wrap text-xs">
                    {JSON.stringify(extractedData, null, 2)}
                  </pre>
                </div>
              ) : (
                <div 
                  className="bg-gray-50 p-4 rounded-lg max-h-96 overflow-y-auto"
                  dangerouslySetInnerHTML={{ __html: displayHtml }}
                />
              )}
            </div>

            {/* Action Buttons */}
            <div className="space-y-3">
              <button
                onClick={onAccept}
                disabled={isLoading}
                className="w-full py-3 px-4 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
              >
                <FiCheck className="h-5 w-5" />
                Accept & Use Data
              </button>
              
              <button
                onClick={onRetry}
                disabled={isLoading}
                className="w-full py-3 px-4 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
              >
                <FiRefreshCw className="h-5 w-5" />
                Retry Scan
              </button>
              
              <button
                onClick={onClear}
                disabled={isLoading}
                className="w-full py-3 px-4 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
              >
                <FiX className="h-5 w-5" />
                Clear Data
              </button>
            </div>

            {/* Certificate Hash Highlight */}
            {extractedData?.certificateHash && (
              <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <FiFileText className="h-4 w-4 text-blue-600" />
                  <span className="text-sm font-semibold text-blue-900">Certificate Hash</span>
                </div>
                <p className="text-xs text-blue-800 break-all font-mono bg-white p-2 rounded border">
                  {extractedData.certificateHash}
                </p>
                <p className="text-xs text-blue-600 mt-2">
                  This hash will be used for verification
                </p>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
};

export default OCRSidebar;