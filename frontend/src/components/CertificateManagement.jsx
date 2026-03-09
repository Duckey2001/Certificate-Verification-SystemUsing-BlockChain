import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiFileText, FiSearch, FiFilter, FiEdit, FiTrash2, FiEye, FiDownload, FiCheck, FiX, FiRefreshCw, FiShield } from 'react-icons/fi';
import DataTable from './DataTable';

const CertificateManagement = () => {
  const [certificates, setCertificates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedCertificate, setSelectedCertificate] = useState(null);
  const [showDetails, setShowDetails] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterInstitution, setFilterInstitution] = useState('all');

  useEffect(() => {
    setLoading(true);
    // Simulate API call
    setTimeout(() => {
      setCertificates([
        {
          id: 1,
          certificateHash: '0x7b3d8f9a2c5e6f1b4a8c9d0e3f5a7b9c1d2e4f6a8b0c1d2e4f6a8b0c1d2e4',
          studentName: 'John Doe',
          studentId: 'STD001',
          institution: 'Examination Council',
          issueDate: '2024-01-15',
          status: 'verified',
          blockchainTxId: '0x1234567890abcdef',
          verificationCount: 15,
          createdAt: '2024-01-15T10:30:00Z'
        },
        {
          id: 2,
          certificateHash: '0x9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f',
          studentName: 'Jane Smith',
          studentId: 'STD002',
          institution: 'Examination Council',
          issueDate: '2024-01-14',
          status: 'pending',
          blockchainTxId: null,
          verificationCount: 3,
          createdAt: '2024-01-14T15:45:00Z'
        },
        {
          id: 3,
          certificateHash: '0x1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1',
          studentName: 'Bob Johnson',
          studentId: 'STD003',
          institution: 'Ministry of Education',
          issueDate: '2024-01-13',
          status: 'revoked',
          blockchainTxId: '0xabcdef1234567890',
          verificationCount: 8,
          createdAt: '2024-01-13T09:20:00Z'
        }
      ]);
      setLoading(false);
    }, 1000);
  }, []);

  const columns = [
    {
      key: 'studentName',
      label: 'Student Name',
      sortable: true,
      render: (value) => (
        <div className="flex items-center">
          <div className="w-8 h-8 rounded-full bg-gradient-to-r from-green-500 to-blue-500 flex items-center justify-center text-white text-sm font-bold mr-3">
            {value.charAt(0)}
          </div>
          <span className="font-medium">{value}</span>
        </div>
      )
    },
    {
      key: 'studentId',
      label: 'Student ID',
      sortable: true,
      render: (value) => (
        <span className="text-sm font-mono bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
          {value}
        </span>
      )
    },
    {
      key: 'institution',
      label: 'Institution',
      filterable: true,
      sortable: true,
      options: [
        { value: 'all', label: 'All Institutions' },
        { value: 'Examination Council', label: 'Examination Council' },
        { value: 'Ministry of Education', label: 'Ministry of Education' }
      ]
    },
    {
      key: 'certificateHash',
      label: 'Certificate Hash',
      sortable: true,
      render: (value) => (
        <span className="text-xs font-mono bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded block truncate max-w-[200px]">
          {value.slice(0, 16)}...
        </span>
      )
    },
    {
      key: 'issueDate',
      label: 'Issue Date',
      sortable: true,
      render: (value) => (
        <span className="text-sm text-gray-600 dark:text-gray-400">
          {new Date(value).toLocaleDateString()}
        </span>
      )
    },
    {
      key: 'status',
      label: 'Status',
      filterable: true,
      sortable: true,
      options: [
        { value: 'all', label: 'All Status' },
        { value: 'verified', label: 'Verified' },
        { value: 'pending', label: 'Pending' },
        { value: 'revoked', label: 'Revoked' }
      ],
      render: (value) => {
        const colors = {
          verified: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
          pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
          revoked: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
        };
        return (
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[value]}`}>
            {value.charAt(0).toUpperCase() + value.slice(1)}
          </span>
        );
      }
    },
    {
      key: 'verificationCount',
      label: 'Verifications',
      sortable: true,
      render: (value) => (
        <div className="flex items-center">
          <FiEye className="w-4 h-4 mr-1 text-blue-500" />
          <span className="text-sm font-medium">{value}</span>
        </div>
      )
    },
    {
      key: 'blockchainTxId',
      label: 'Blockchain',
      sortable: true,
      render: (value) => (
        <div className="flex items-center">
          {value ? (
            <>
              <FiCheck className="w-4 h-4 text-green-500 mr-1" />
              <span className="text-xs text-green-600 dark:text-green-400">Confirmed</span>
            </>
          ) : (
            <>
              <FiX className="w-4 h-4 text-yellow-500 mr-1" />
              <span className="text-xs text-yellow-600 dark:text-yellow-400">Pending</span>
            </>
          )}
        </div>
      )
    }
  ];

  const handleViewCertificate = (certificate) => {
    setSelectedCertificate(certificate);
    setShowDetails(true);
  };

  const handleRevokeCertificate = (certificate) => {
    if (window.confirm(`Are you sure you want to revoke certificate for "${certificate.studentName}"?`)) {
      setCertificates(prev => 
        prev.map(c => 
          c.id === certificate.id ? { ...c, status: 'revoked' } : c
        )
      );
    }
  };

  const handleVerifyCertificate = (certificate) => {
    setCertificates(prev => 
      prev.map(c => 
        c.id === certificate.id ? { ...c, status: 'verified', blockchainTxId: '0x' + Math.random().toString(36).substr(2, 16) } : c
      )
    );
  };

  const handleExportCertificates = () => {
    const csv = [
      ['Student Name', 'Student ID', 'Institution', 'Status', 'Issue Date', 'Verification Count'],
      ...certificates.map(c => [
        c.studentName,
        c.studentId,
        c.institution,
        c.status,
        c.issueDate,
        c.verificationCount
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `certificates_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Certificate Management</h2>
          <p className="text-gray-600 dark:text-gray-400">Manage and monitor all certificates</p>
        </div>
        
        <div className="flex space-x-3">
          <button
            onClick={handleExportCertificates}
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg flex items-center"
          >
            <FiDownload className="w-4 h-4 mr-2" />
            Export
          </button>
          <button
            className="px-4 py-2 bg-gradient-to-r from-green-500 to-green-600 hover:from-green-600 hover:to-green-700 text-white rounded-lg flex items-center"
          >
            <FiFileText className="w-4 h-4 mr-2" />
            Issue Certificate
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Total Certificates</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{certificates.length}</p>
            </div>
            <FiFileText className="w-8 h-8 text-blue-500" />
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Verified</p>
              <p className="text-2xl font-bold text-green-600">{certificates.filter(c => c.status === 'verified').length}</p>
            </div>
            <FiCheck className="w-8 h-8 text-green-500" />
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Pending</p>
              <p className="text-2xl font-bold text-yellow-600">{certificates.filter(c => c.status === 'pending').length}</p>
            </div>
            <FiRefreshCw className="w-8 h-8 text-yellow-500" />
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Revoked</p>
              <p className="text-2xl font-bold text-red-600">{certificates.filter(c => c.status === 'revoked').length}</p>
            </div>
            <FiX className="w-8 h-8 text-red-500" />
          </div>
        </div>
      </div>

      {/* Certificates Table */}
      <DataTable
        data={certificates}
        columns={columns}
        loading={loading}
        searchable={true}
        sortable={true}
        paginated={true}
        itemsPerPage={10}
        onView={handleViewCertificate}
        actions={[
          {
            icon: <FiCheck className="w-4 h-4" />,
            title: 'Verify',
            className: 'text-green-600 hover:text-green-800',
            onClick: handleVerifyCertificate,
            show: (cert) => cert.status === 'pending'
          },
          {
            icon: <FiX className="w-4 h-4" />,
            title: 'Revoke',
            className: 'text-red-600 hover:text-red-800',
            onClick: handleRevokeCertificate,
            show: (cert) => cert.status === 'verified'
          }
        ]}
      />

      {/* Certificate Details Modal */}
      <AnimatePresence>
        {showDetails && selectedCertificate && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => setShowDetails(false)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="bg-white dark:bg-gray-800 rounded-2xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto"
              onClick={e => e.stopPropagation()}
            >
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-6">Certificate Details</h3>
              
              <div className="space-y-6">
                {/* Student Information */}
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Student Information</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Name</p>
                      <p className="font-medium">{selectedCertificate.studentName}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Student ID</p>
                      <p className="font-mono">{selectedCertificate.studentId}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Institution</p>
                      <p className="font-medium">{selectedCertificate.institution}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Issue Date</p>
                      <p className="font-medium">{new Date(selectedCertificate.issueDate).toLocaleDateString()}</p>
                    </div>
                  </div>
                </div>

                {/* Certificate Information */}
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Certificate Information</h4>
                  <div className="space-y-3">
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Certificate Hash</p>
                      <p className="font-mono text-xs bg-white dark:bg-gray-800 p-2 rounded border break-all">
                        {selectedCertificate.certificateHash}
                      </p>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-gray-500 dark:text-gray-400">Status</p>
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          selectedCertificate.status === 'verified' ? 'bg-green-100 text-green-800' :
                          selectedCertificate.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {selectedCertificate.status}
                        </span>
                      </div>
                      <div>
                        <p className="text-sm text-gray-500 dark:text-gray-400">Verification Count</p>
                        <p className="font-medium">{selectedCertificate.verificationCount}</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Blockchain Information */}
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
                    <FiShield className="w-5 h-5 mr-2" />
                    Blockchain Information
                  </h4>
                  <div className="space-y-3">
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Transaction ID</p>
                      <p className="font-mono text-sm">
                        {selectedCertificate.blockchainTxId || 'Not yet mined'}
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Created At</p>
                      <p className="font-medium">{new Date(selectedCertificate.createdAt).toLocaleString()}</p>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => setShowDetails(false)}
                  className="px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg"
                >
                  Close
                </button>
                <button
                  className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg flex items-center"
                >
                  <FiDownload className="w-4 h-4 mr-2" />
                  Download PDF
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default CertificateManagement;
