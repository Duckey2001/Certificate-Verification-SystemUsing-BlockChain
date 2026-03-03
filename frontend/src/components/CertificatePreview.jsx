import React from 'react';

const CertificatePreview = ({ certificate, onClose, onRevoke }) => {
  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 animate-fadeIn">
      <div className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full mx-4 animate-scaleIn">
        <div className="px-6 py-4 bg-gradient-to-r from-yellow-500 to-orange-600 rounded-t-2xl flex justify-between items-center">
          <h3 className="text-lg font-semibold text-white">Certificate Details</h3>
          <button onClick={onClose} className="text-white/80 hover:text-white">
            ✕
          </button>
        </div>
        
        <div className="p-6">
          <div className="grid grid-cols-2 gap-6">
            {/* Certificate Display */}
            <div className="border-2 border-gray-200 rounded-xl p-6 bg-gradient-to-br from-yellow-50 to-orange-50">
              <div className="text-center mb-6">
                <h2 className="text-2xl font-bold text-gray-800">LGCSE Certificate</h2>
                <p className="text-sm text-gray-500">Lesotho General Certificate of Secondary Education</p>
              </div>
              
              <div className="space-y-4">
                <div className="flex justify-between">
                  <span className="text-gray-600">Student Name:</span>
                  <span className="font-bold">{certificate.student_name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Student ID:</span>
                  <span>{certificate.student_id}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Institution:</span>
                  <span>{certificate.institution}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Issue Date:</span>
                  <span>{new Date(certificate.issue_date).toLocaleDateString()}</span>
                </div>
                {certificate.grade && (
                  <div className="flex justify-between">
                    <span className="text-gray-600">Grade:</span>
                    <span className="font-bold text-green-600">{certificate.grade}</span>
                  </div>
                )}
                {certificate.subjects && certificate.subjects.length > 0 && (
                  <div>
                    <span className="text-gray-600 block mb-2">Subjects:</span>
                    <div className="flex flex-wrap gap-2">
                      {certificate.subjects.map((subject, idx) => (
                        <span key={idx} className="px-2 py-1 bg-gray-100 rounded-lg text-xs">
                          {subject}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Blockchain Info */}
            <div className="space-y-4">
              <div className="bg-gray-50 rounded-xl p-4">
                <h4 className="text-sm font-medium text-gray-700 mb-3">Blockchain Information</h4>
                <div className="space-y-3">
                  <div>
                    <p className="text-xs text-gray-500">Certificate Hash</p>
                    <p className="text-sm font-mono bg-white p-2 rounded border">
                      {certificate.certificate_hash}
                    </p>
                  </div>
                  {certificate.blockchain_tx_id && (
                    <div>
                      <p className="text-xs text-gray-500">Transaction ID</p>
                      <p className="text-sm font-mono bg-white p-2 rounded border">
                        {certificate.blockchain_tx_id}
                      </p>
                    </div>
                  )}
                  <div>
                    <p className="text-xs text-gray-500">Status</p>
                    <span className={`inline-block mt-1 px-3 py-1 rounded-full text-xs font-medium ${
                      certificate.status === 'verified' ? 'bg-green-100 text-green-800' :
                      certificate.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                      certificate.status === 'revoked' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {certificate.status}
                    </span>
                  </div>
                  <div>
                    <p className="text-xs text-gray-500">Created</p>
                    <p className="text-sm">{new Date(certificate.created_at).toLocaleString()}</p>
                  </div>
                </div>
              </div>

              {certificate.verifications && certificate.verifications.length > 0 && (
                <div className="bg-gray-50 rounded-xl p-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-3">Verification History</h4>
                  <div className="space-y-2">
                    {certificate.verifications.map((v, idx) => (
                      <div key={idx} className="flex justify-between text-xs">
                        <span>{new Date(v.timestamp).toLocaleString()}</span>
                        <span className={v.verified ? 'text-green-600' : 'text-red-600'}>
                          {v.verified ? '✓ Valid' : '✗ Invalid'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex space-x-3">
                <button
                  onClick={onClose}
                  className="flex-1 px-4 py-2 border-2 border-gray-200 rounded-xl text-gray-700 hover:bg-gray-50"
                >
                  Close
                </button>
                {certificate.status === 'pending' && (
                  <button
                    onClick={onRevoke}
                    className="flex-1 px-4 py-2 bg-red-500 text-white rounded-xl hover:bg-red-600"
                  >
                    Revoke Certificate
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CertificatePreview;
