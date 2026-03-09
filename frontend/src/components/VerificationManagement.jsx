import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiCheckCircle, FiSearch, FiFilter, FiEye, FiDownload, FiTrendingUp, FiDollarSign, FiCalendar, FiClock } from 'react-icons/fi';
import DataTable from './DataTable';

const VerificationManagement = () => {
  const [verifications, setVerifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedVerification, setSelectedVerification] = useState(null);
  const [showDetails, setShowDetails] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterMethod, setFilterMethod] = useState('all');
  const [dateRange, setDateRange] = useState({ start: '', end: '' });

  useEffect(() => {
    setLoading(true);
    // Simulate API call
    setTimeout(() => {
      setVerifications([
        {
          id: 1,
          verificationId: 'VER_001',
          certificateHash: '0x7b3d8f9a2c5e6f1b4a8c9d0e3f5a7b9',
          studentName: 'John Doe',
          verifierName: 'Alice Smith',
          status: 'successful',
          method: 'hash',
          paymentMethod: 'mpesa',
          fee: 5.00,
          verificationDate: '2024-01-15T10:30:00Z',
          duration: 2.5,
          blockchainVerified: true,
          ipAddress: '192.168.1.100',
          location: 'Maseru, Lesotho'
        },
        {
          id: 2,
          verificationId: 'VER_002',
          certificateHash: '0x9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4',
          studentName: 'Jane Smith',
          verifierName: 'Bob Johnson',
          status: 'failed',
          method: 'file',
          paymentMethod: 'ecocash',
          fee: 5.00,
          verificationDate: '2024-01-15T09:15:00Z',
          duration: 3.2,
          blockchainVerified: false,
          ipAddress: '192.168.1.101',
          location: 'Leribe, Lesotho'
        },
        {
          id: 3,
          verificationId: 'VER_003',
          certificateHash: '0x1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6',
          studentName: 'Bob Johnson',
          verifierName: 'Carol Davis',
          status: 'successful',
          method: 'both',
          paymentMethod: 'bank',
          fee: 5.00,
          verificationDate: '2024-01-14T15:45:00Z',
          duration: 1.8,
          blockchainVerified: true,
          ipAddress: '192.168.1.102',
          location: 'Mafeteng, Lesotho'
        }
      ]);
      setLoading(false);
    }, 1000);
  }, []);

  const columns = [
    {
      key: 'verificationId',
      label: 'Verification ID',
      sortable: true,
      render: (value) => (
        <span className="font-mono text-sm bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-400 px-2 py-1 rounded">
          {value}
        </span>
      )
    },
    {
      key: 'studentName',
      label: 'Student Name',
      sortable: true,
      render: (value) => (
        <div className="flex items-center">
          <div className="w-8 h-8 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center text-white text-sm font-bold mr-3">
            {value.charAt(0)}
          </div>
          <span className="font-medium">{value}</span>
        </div>
      )
    },
    {
      key: 'verifierName',
      label: 'Verifier',
      sortable: true,
      render: (value) => (
        <div className="flex items-center">
          <div className="w-6 h-6 rounded-full bg-gradient-to-r from-orange-500 to-red-500 flex items-center justify-center text-white text-xs font-bold mr-2">
            {value.charAt(0)}
          </div>
          <span className="text-sm">{value}</span>
        </div>
      )
    },
    {
      key: 'certificateHash',
      label: 'Certificate Hash',
      sortable: true,
      render: (value) => (
        <span className="text-xs font-mono bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded block truncate max-w-[150px]">
          {value}...
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
        { value: 'successful', label: 'Successful' },
        { value: 'failed', label: 'Failed' },
        { value: 'pending', label: 'Pending' }
      ],
      render: (value) => {
        const colors = {
          successful: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
          failed: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
          pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
        };
        return (
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[value]}`}>
            {value.charAt(0).toUpperCase() + value.slice(1)}
          </span>
        );
      }
    },
    {
      key: 'method',
      label: 'Method',
      filterable: true,
      sortable: true,
      options: [
        { value: 'all', label: 'All Methods' },
        { value: 'hash', label: 'Hash Only' },
        { value: 'file', label: 'File Only' },
        { value: 'both', label: 'Both' }
      ],
      render: (value) => {
        const icons = {
          hash: '🔑',
          file: '📄',
          both: '🔐'
        };
        return (
          <span className="flex items-center">
            <span className="mr-2">{icons[value]}</span>
            <span className="text-sm">{value.charAt(0).toUpperCase() + value.slice(1)}</span>
          </span>
        );
      }
    },
    {
      key: 'paymentMethod',
      label: 'Payment',
      sortable: true,
      render: (value) => {
        const methods = {
          mpesa: { icon: '📱', color: 'text-green-600' },
          ecocash: { icon: '📲', color: 'text-blue-600' },
          bank: { icon: '🏦', color: 'text-purple-600' }
        };
        const method = methods[value] || { icon: '💳', color: 'text-gray-600' };
        return (
          <span className={`flex items-center ${method.color}`}>
            <span className="mr-1">{method.icon}</span>
            <span className="text-sm">{value.toUpperCase()}</span>
          </span>
        );
      }
    },
    {
      key: 'fee',
      label: 'Fee',
      sortable: true,
      render: (value) => (
        <div className="flex items-center">
          <FiDollarSign className="w-4 h-4 mr-1 text-green-500" />
          <span className="font-medium text-green-600">M{value.toFixed(2)}</span>
        </div>
      )
    },
    {
      key: 'verificationDate',
      label: 'Date',
      sortable: true,
      render: (value) => (
        <div className="flex items-center">
          <FiCalendar className="w-4 h-4 mr-1 text-gray-400" />
          <span className="text-sm">{new Date(value).toLocaleDateString()}</span>
        </div>
      )
    },
    {
      key: 'duration',
      label: 'Duration',
      sortable: true,
      render: (value) => (
        <div className="flex items-center">
          <FiClock className="w-4 h-4 mr-1 text-blue-400" />
          <span className="text-sm">{value}s</span>
        </div>
      )
    },
    {
      key: 'blockchainVerified',
      label: 'Blockchain',
      sortable: true,
      render: (value) => (
        <div className="flex items-center">
          {value ? (
            <>
              <FiCheckCircle className="w-4 h-4 text-green-500 mr-1" />
              <span className="text-xs text-green-600">Verified</span>
            </>
          ) : (
            <>
              <FiClock className="w-4 h-4 text-yellow-500 mr-1" />
              <span className="text-xs text-yellow-600">Pending</span>
            </>
          )}
        </div>
      )
    }
  ];

  const handleViewVerification = (verification) => {
    setSelectedVerification(verification);
    setShowDetails(true);
  };

  const handleExportVerifications = () => {
    const csv = [
      ['Verification ID', 'Student Name', 'Verifier', 'Status', 'Method', 'Payment', 'Fee', 'Date'],
      ...verifications.map(v => [
        v.verificationId,
        v.studentName,
        v.verifierName,
        v.status,
        v.method,
        v.paymentMethod,
        v.fee,
        v.verificationDate
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `verifications_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  const stats = {
    total: verifications.length,
    successful: verifications.filter(v => v.status === 'successful').length,
    failed: verifications.filter(v => v.status === 'failed').length,
    pending: verifications.filter(v => v.status === 'pending').length,
    totalRevenue: verifications.reduce((sum, v) => sum + v.fee, 0),
    avgDuration: verifications.length > 0 
      ? (verifications.reduce((sum, v) => sum + v.duration, 0) / verifications.length).toFixed(1)
      : 0
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Verification Management</h2>
          <p className="text-gray-600 dark:text-gray-400">Monitor and manage certificate verifications</p>
        </div>
        
        <div className="flex space-x-3">
          <button
            onClick={handleExportVerifications}
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg flex items-center"
          >
            <FiDownload className="w-4 h-4 mr-2" />
            Export
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">Total</p>
              <p className="text-xl font-bold text-gray-900 dark:text-white">{stats.total}</p>
            </div>
            <FiCheckCircle className="w-6 h-6 text-blue-500" />
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">Successful</p>
              <p className="text-xl font-bold text-green-600">{stats.successful}</p>
            </div>
            <FiCheckCircle className="w-6 h-6 text-green-500" />
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">Failed</p>
              <p className="text-xl font-bold text-red-600">{stats.failed}</p>
            </div>
            <FiClock className="w-6 h-6 text-red-500" />
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">Pending</p>
              <p className="text-xl font-bold text-yellow-600">{stats.pending}</p>
            </div>
            <FiClock className="w-6 h-6 text-yellow-500" />
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">Revenue</p>
              <p className="text-xl font-bold text-purple-600">M{stats.totalRevenue.toFixed(0)}</p>
            </div>
            <FiDollarSign className="w-6 h-6 text-purple-500" />
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">Avg Time</p>
              <p className="text-xl font-bold text-blue-600">{stats.avgDuration}s</p>
            </div>
            <FiTrendingUp className="w-6 h-6 text-blue-500" />
          </div>
        </div>
      </div>

      {/* Date Range Filter */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Start Date</label>
            <input
              type="date"
              value={dateRange.start}
              onChange={(e) => setDateRange(prev => ({ ...prev, start: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">End Date</label>
            <input
              type="date"
              value={dateRange.end}
              onChange={(e) => setDateRange(prev => ({ ...prev, end: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-gray-900 dark:text-white"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={() => setDateRange({ start: '', end: '' })}
              className="w-full px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg"
            >
              Clear Dates
            </button>
          </div>
        </div>
      </div>

      {/* Verifications Table */}
      <DataTable
        data={verifications}
        columns={columns}
        loading={loading}
        searchable={true}
        sortable={true}
        paginated={true}
        itemsPerPage={15}
        onView={handleViewVerification}
      />

      {/* Verification Details Modal */}
      <AnimatePresence>
        {showDetails && selectedVerification && (
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
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-6">Verification Details</h3>
              
              <div className="space-y-6">
                {/* Verification Overview */}
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Verification Overview</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Verification ID</p>
                      <p className="font-mono">{selectedVerification.verificationId}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Status</p>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        selectedVerification.status === 'successful' ? 'bg-green-100 text-green-800' :
                        selectedVerification.status === 'failed' ? 'bg-red-100 text-red-800' :
                        'bg-yellow-100 text-yellow-800'
                      }`}>
                        {selectedVerification.status}
                      </span>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Method</p>
                      <p className="font-medium">{selectedVerification.method}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Duration</p>
                      <p className="font-medium">{selectedVerification.duration} seconds</p>
                    </div>
                  </div>
                </div>

                {/* Certificate Information */}
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Certificate Information</h4>
                  <div className="space-y-3">
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Student Name</p>
                      <p className="font-medium">{selectedVerification.studentName}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Certificate Hash</p>
                      <p className="font-mono text-xs bg-white dark:bg-gray-800 p-2 rounded border break-all">
                        {selectedVerification.certificateHash}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Payment Information */}
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Payment Information</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Payment Method</p>
                      <p className="font-medium">{selectedVerification.paymentMethod.toUpperCase()}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Fee</p>
                      <p className="font-medium text-green-600">M{selectedVerification.fee.toFixed(2)}</p>
                    </div>
                  </div>
                </div>

                {/* Technical Details */}
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Technical Details</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Verifier</p>
                      <p className="font-medium">{selectedVerification.verifierName}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">IP Address</p>
                      <p className="font-mono">{selectedVerification.ipAddress}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Location</p>
                      <p className="font-medium">{selectedVerification.location}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Verification Date</p>
                      <p className="font-medium">{new Date(selectedVerification.verificationDate).toLocaleString()}</p>
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
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default VerificationManagement;
