import React from 'react';

const BulkUploadModal = ({ files, setFiles, onClose, onConfirm }) => {
  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 animate-fadeIn">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full mx-4 animate-scaleIn">
        <div className="px-6 py-4 bg-gradient-to-r from-purple-500 to-pink-600 rounded-t-2xl flex justify-between items-center">
          <h3 className="text-lg font-semibold text-white">Confirm Bulk Upload</h3>
          <button onClick={onClose} className="text-white/80 hover:text-white">
            ✕
          </button>
        </div>
        
        <div className="p-6">
          <div className="mb-6">
            <p className="text-gray-700 mb-4">
              You are about to upload <span className="font-bold text-purple-600">{files.length}</span> certificate files.
            </p>
            
            <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 mb-4">
              <h4 className="text-sm font-medium text-yellow-800 mb-2">⚠️ Important Notes:</h4>
              <ul className="text-xs text-yellow-700 space-y-1">
                <li>• Each file will be processed individually</li>
                <li>• Files should contain clear certificate images/PDFs</li>
                <li>• Each certificate will cost 1 credit from your institution</li>
                <li>• Processing may take a few minutes</li>
                <li>• Results will be shown after completion</li>
              </ul>
            </div>

            <div className="max-h-60 overflow-y-auto border rounded-xl p-3">
              <h4 className="text-sm font-medium text-gray-700 mb-2">Selected Files:</h4>
              {files.map((file, index) => (
                <div key={index} className="flex items-center justify-between py-2 border-b last:border-0">
                  <div className="flex items-center">
                    <span className="text-xl mr-2">📄</span>
                    <div>
                      <p className="text-sm font-medium">{file.name}</p>
                      <p className="text-xs text-gray-400">{(file.size / 1024).toFixed(1)} KB</p>
                    </div>
                  </div>
                  <button
                    onClick={() => setFiles(files.filter((_, i) => i !== index))}
                    className="text-red-500 hover:text-red-700"
                  >
                    ✕
                  </button>
                </div>
              ))}
            </div>
          </div>

          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-3 border-2 border-gray-200 rounded-xl text-gray-700 font-medium hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={onConfirm}
              className="flex-1 px-4 py-3 bg-gradient-to-r from-purple-500 to-pink-600 rounded-xl text-white font-medium hover:from-purple-600 hover:to-pink-700 transition-all transform hover:scale-105"
            >
              Start Upload
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default BulkUploadModal;
