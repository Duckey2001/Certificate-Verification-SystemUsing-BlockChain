import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiDollarSign, FiSearch, FiFilter, FiEye, FiDownload, FiTrendingUp, FiCalendar, FiCheck, FiX, FiClock, FiRefreshCw, FiShield } from 'react-icons/fi';
import DataTable from './DataTable';

const PaymentManagement = () => {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [selectedPayment, setSelectedPayment] = useState(null);
  const [showDetails, setShowDetails] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterMethod, setFilterMethod] = useState('all');
  const [dateRange, setDateRange] = useState({ start: '', end: '' });
  const [verificationResult, setVerificationResult] = useState(null);

  useEffect(() => {
    fetchPayments();
  }, []);

  const fetchPayments = async () => {
    setLoading(true);
    try {
      // Simulate API call - replace with actual API endpoint
      setTimeout(() => {
        setPayments([
          {
            id: 1,
            paymentId: 'PAY_001',
            transactionId: 'MPESA_123456',
            amount: 5.00,
            currency: 'LSL',
            method: 'mpesa',
            status: 'confirmed',
            payerName: 'Alice Smith',
            payerEmail: 'alice@example.com',
            payerPhone: '+266 1234 5678',
            verificationId: 'VER_001',
            certificateHash: '0x7b3d8f9a2c5e6f1b4a8c9d0e3f5a7b9',
            paymentDate: '2024-01-15T10:30:00Z',
            confirmedDate: '2024-01-15T10:32:00Z',
            fee: 0.25,
            netAmount: 4.75,
            ipAddress: '192.168.1.100',
            location: 'Maseru, Lesotho',
            verified: true,
            verifiedBy: 'system',
            verifiedAt: '2024-01-15T10:32:00Z'
          },
          {
            id: 2,
            paymentId: 'PAY_002',
            transactionId: 'ECOCASH_789012',
            amount: 5.00,
            currency: 'LSL',
            method: 'ecocash',
            status: 'pending',
            payerName: 'Bob Johnson',
            payerEmail: 'bob@example.com',
            payerPhone: '+266 2345 6789',
            verificationId: 'VER_002',
            certificateHash: '0x9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4',
            paymentDate: '2024-01-15T09:15:00Z',
            confirmedDate: null,
            fee: 0.25,
            netAmount: 4.75,
            ipAddress: '192.168.1.101',
            location: 'Leribe, Lesotho',
            verified: false
          },
          {
            id: 3,
            paymentId: 'PAY_003',
            transactionId: 'BANK_345678',
            amount: 5.00,
            currency: 'LSL',
            method: 'bank',
            status: 'failed',
            payerName: 'Carol Davis',
            payerEmail: 'carol@example.com',
            payerPhone: '+266 3456 7890',
            verificationId: 'VER_003',
            certificateHash: '0x1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6',
            paymentDate: '2024-01-14T15:45:00Z',
            confirmedDate: null,
            fee: 0.25,
            netAmount: 4.75,
            ipAddress: '192.168.1.102',
            location: 'Mafeteng, Lesotho',
            failureReason: 'Insufficient funds',
            verified: false
          }
        ]);
        setLoading(false);
      }, 1000);
    } catch (error) {
      console.error('Error fetching payments:', error);
      setLoading(false);
    }
  };

  const verifyPayment = async (payment) => {
    setVerifying(true);
    setVerificationResult(null);
    
    try {
      // Simulate payment verification process
      // In production, this would call your actual verification API
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      // Mock verification logic
      const verificationSteps = [
        { name: 'Transaction ID Validation', status: 'success', message: 'Transaction ID format valid' },
        { name: 'Amount Verification', status: 'success', message: 'Amount matches expected value' },
        { name: 'Certificate Hash Check', status: 'success', message: 'Certificate hash verified on blockchain' },
        { name: 'Payment Provider Confirmation', status: 'success', message: 'Confirmed with payment provider' }
      ];

      // Simulate a failure for demonstration (remove in production)
      if (payment.id === 3) {
        verificationSteps[3] = { 
          name: 'Payment Provider Confirmation', 
          status: 'failed', 
          message: 'Unable to confirm with payment provider' 
        };
      }

      const allSuccessful = verificationSteps.every(step => step.status === 'success');
      
      setVerificationResult({
        success: allSuccessful,
        steps: verificationSteps,
        verifiedAt: new Date().toISOString(),
        verifiedBy: 'admin'
      });

      // Update payment status if verification successful
      if (allSuccessful && payment.status === 'pending') {
        updatePaymentStatus(payment.id, 'confirmed');
      }

    } catch (error) {
      setVerificationResult({
        success: false,
        error: error.message,
        steps: [],
        verifiedAt: new Date().toISOString()
      });
    } finally {
      setVerifying(false);
    }
  };

  const updatePaymentStatus = (paymentId, newStatus) => {
    setPayments(prevPayments =>
      prevPayments.map(payment =>
        payment.id === paymentId
          ? {
              ...payment,
              status: newStatus,
              confirmedDate: newStatus === 'confirmed' ? new Date().toISOString() : payment.confirmedDate,
              verified: true,
              verifiedBy: 'admin',
              verifiedAt: new Date().toISOString()
            }
          : payment
      )
    );

    // Update selected payment if modal is open
    if (selectedPayment && selectedPayment.id === paymentId) {
      setSelectedPayment(prev => ({
        ...prev,
        status: newStatus,
        confirmedDate: newStatus === 'confirmed' ? new Date().toISOString() : prev.confirmedDate,
        verified: true,
        verifiedBy: 'admin',
        verifiedAt: new Date().toISOString()
      }));
    }
  };

  const handleViewPayment = (payment) => {
    setSelectedPayment(payment);
    setVerificationResult(null);
    setShowDetails(true);
  };

  const handleExportPayments = () => {
    const csv = [
      ['Payment ID', 'Transaction ID', 'Payer Name', 'Amount', 'Method', 'Status', 'Verified', 'Payment Date', 'Confirmed Date'],
      ...payments.map(p => [
        p.paymentId,
        p.transactionId,
        p.payerName,
        p.amount,
        p.method,
        p.status,
        p.verified ? 'Yes' : 'No',
        p.paymentDate,
        p.confirmedDate || 'Pending'
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `payments_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  const columns = [
    {
      key: 'paymentId',
      label: 'Payment ID',
      sortable: true,
      render: (value) => (
        <span className="font-mono text-sm bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-400 px-2 py-1 rounded">
          {value}
        </span>
      )
    },
    {
      key: 'transactionId',
      label: 'Transaction ID',
      sortable: true,
      render: (value) => (
        <span className="font-mono text-xs bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
          {value}
        </span>
      )
    },
    {
      key: 'payerName',
      label: 'Payer',
      sortable: true,
      render: (value, row) => (
        <div className="flex items-center">
          <div className="w-8 h-8 rounded-full bg-gradient-to-r from-green-500 to-emerald-500 flex items-center justify-center text-white text-sm font-bold mr-3">
            {value.charAt(0)}
          </div>
          <div>
            <span className="font-medium">{value}</span>
            {row.payerPhone && (
              <p className="text-xs text-gray-500">{row.payerPhone}</p>
            )}
          </div>
        </div>
      )
    },
    {
      key: 'amount',
      label: 'Amount',
      sortable: true,
      render: (value, row) => (
        <div className="text-right">
          <p className="font-bold text-green-600">M{value.toFixed(2)}</p>
          <p className="text-xs text-gray-500">Fee: M{row.fee.toFixed(2)}</p>
        </div>
      )
    },
    {
      key: 'method',
      label: 'Method',
      sortable: true,
      render: (value) => {
        const methods = {
          mpesa: { icon: '📱', color: 'text-green-600', name: 'M-Pesa' },
          ecocash: { icon: '📲', color: 'text-blue-600', name: 'EcoCash' },
          bank: { icon: '🏦', color: 'text-purple-600', name: 'Bank' }
        };
        const method = methods[value] || { icon: '💳', color: 'text-gray-600', name: value };
        return (
          <div className="flex items-center">
            <span className="mr-2">{method.icon}</span>
            <span className={`text-sm font-medium ${method.color}`}>{method.name}</span>
          </div>
        );
      }
    },
    {
      key: 'status',
      label: 'Status',
      sortable: true,
      render: (value) => {
        const colors = {
          confirmed: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
          pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
          failed: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
          refunded: 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400'
        };
        const icons = {
          confirmed: <FiCheck className="w-3 h-3" />,
          pending: <FiClock className="w-3 h-3" />,
          failed: <FiX className="w-3 h-3" />,
          refunded: <FiDownload className="w-3 h-3" />
        };
        return (
          <span className={`px-2 py-1 rounded-full text-xs font-medium flex items-center ${colors[value]}`}>
            {icons[value]}
            <span className="ml-1">{value.charAt(0).toUpperCase() + value.slice(1)}</span>
          </span>
        );
      }
    },
    {
      key: 'verified',
      label: 'Verified',
      sortable: true,
      render: (value) => (
        <div className="flex items-center">
          {value ? (
            <>
              <FiShield className="w-4 h-4 mr-1 text-green-500" />
              <span className="text-sm text-green-600">Verified</span>
            </>
          ) : (
            <>
              <FiClock className="w-4 h-4 mr-1 text-yellow-500" />
              <span className="text-sm text-yellow-600">Pending</span>
            </>
          )}
        </div>
      )
    },
    {
      key: 'paymentDate',
      label: 'Payment Date',
      sortable: true,
      render: (value) => (
        <div className="flex items-center">
          <FiCalendar className="w-4 h-4 mr-1 text-gray-400" />
          <span className="text-sm">{new Date(value).toLocaleDateString()}</span>
        </div>
      )
    },
    {
      key: 'actions',
      label: 'Actions',
      render: (_, row) => (
        <button
          onClick={(e) => {
            e.stopPropagation();
            handleViewPayment(row);
          }}
          className="p-2 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
        >
          <FiEye className="w-4 h-4" />
        </button>
      )
    }
  ];

  const stats = {
    total: payments.length,
    confirmed: payments.filter(p => p.status === 'confirmed').length,
    pending: payments.filter(p => p.status === 'pending').length,
    failed: payments.filter(p => p.status === 'failed').length,
    verified: payments.filter(p => p.verified).length,
    totalRevenue: payments.filter(p => p.status === 'confirmed').reduce((sum, p) => sum + p.netAmount, 0),
    totalFees: payments.filter(p => p.status === 'confirmed').reduce((sum, p) => sum + p.fee, 0)
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Payment Management</h2>
          <p className="text-gray-600 dark:text-gray-400">Monitor, verify, and manage all payment transactions</p>
        </div>
        
        <div className="flex space-x-3">
          <button
            onClick={fetchPayments}
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg flex items-center"
          >
            <FiRefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </button>
          <button
            onClick={handleExportPayments}
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg flex items-center"
          >
            <FiDownload className="w-4 h-4 mr-2" />
            Export
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">Total Payments</p>
              <p className="text-xl font-bold text-gray-900 dark:text-white">{stats.total}</p>
            </div>
            <FiDollarSign className="w-6 h-6 text-blue-500" />
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">Verified</p>
              <p className="text-xl font-bold text-green-600">{stats.verified}</p>
            </div>
            <FiShield className="w-6 h-6 text-green-500" />
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">Confirmed</p>
              <p className="text-xl font-bold text-green-600">{stats.confirmed}</p>
            </div>
            <FiCheck className="w-6 h-6 text-green-500" />
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
            <FiTrendingUp className="w-6 h-6 text-purple-500" />
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400">Fees</p>
              <p className="text-xl font-bold text-orange-600">M{stats.totalFees.toFixed(0)}</p>
            </div>
            <FiDollarSign className="w-6 h-6 text-orange-500" />
          </div>
        </div>
      </div>

      {/* Payments Table */}
      <DataTable
        data={payments}
        columns={columns}
        loading={loading}
        searchable={true}
        sortable={true}
        paginated={true}
        itemsPerPage={15}
        onRowClick={handleViewPayment}
      />

      {/* Payment Details Modal with Verification */}
      <AnimatePresence>
        {showDetails && selectedPayment && (
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
              className="bg-white dark:bg-gray-800 rounded-2xl p-6 max-w-3xl w-full mx-4 max-h-[90vh] overflow-y-auto"
              onClick={e => e.stopPropagation()}
            >
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-xl font-bold text-gray-900 dark:text-white">Payment Details</h3>
                <button
                  onClick={() => setShowDetails(false)}
                  className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"
                >
                  <FiX className="w-5 h-5" />
                </button>
              </div>
              
              <div className="space-y-6">
                {/* Payment Overview */}
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Payment Overview</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Payment ID</p>
                      <p className="font-mono font-medium">{selectedPayment.paymentId}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Transaction ID</p>
                      <p className="font-mono font-medium">{selectedPayment.transactionId}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Status</p>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium inline-flex items-center ${
                        selectedPayment.status === 'confirmed' ? 'bg-green-100 text-green-800' :
                        selectedPayment.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {selectedPayment.status === 'confirmed' && <FiCheck className="w-3 h-3 mr-1" />}
                        {selectedPayment.status === 'pending' && <FiClock className="w-3 h-3 mr-1" />}
                        {selectedPayment.status === 'failed' && <FiX className="w-3 h-3 mr-1" />}
                        {selectedPayment.status.charAt(0).toUpperCase() + selectedPayment.status.slice(1)}
                      </span>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Method</p>
                      <p className="font-medium">{selectedPayment.method.toUpperCase()}</p>
                    </div>
                  </div>
                </div>

                {/* Financial Details */}
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Financial Details</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Total Amount</p>
                      <p className="font-bold text-lg text-green-600">M{selectedPayment.amount.toFixed(2)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Processing Fee</p>
                      <p className="font-medium text-orange-600">M{selectedPayment.fee.toFixed(2)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Net Amount</p>
                      <p className="font-bold text-blue-600">M{selectedPayment.netAmount.toFixed(2)}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Currency</p>
                      <p className="font-medium">{selectedPayment.currency}</p>
                    </div>
                  </div>
                </div>

                {/* Payer Information */}
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Payer Information</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Name</p>
                      <p className="font-medium">{selectedPayment.payerName}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Email</p>
                      <p className="font-medium">{selectedPayment.payerEmail}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Phone</p>
                      <p className="font-medium">{selectedPayment.payerPhone}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Location</p>
                      <p className="font-medium">{selectedPayment.location}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">IP Address</p>
                      <p className="font-mono text-sm">{selectedPayment.ipAddress}</p>
                    </div>
                  </div>
                </div>

                {/* Verification Section */}
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                  <div className="flex justify-between items-center mb-3">
                    <h4 className="font-semibold text-gray-900 dark:text-white">Payment Verification</h4>
                    {selectedPayment.verified && (
                      <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs font-medium flex items-center">
                        <FiShield className="w-3 h-3 mr-1" />
                        Verified by {selectedPayment.verifiedBy}
                      </span>
                    )}
                  </div>

                  {!selectedPayment.verified && selectedPayment.status === 'pending' && (
                    <div className="space-y-4">
                      <button
                        onClick={() => verifyPayment(selectedPayment)}
                        disabled={verifying}
                        className="w-full px-4 py-3 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-lg flex items-center justify-center"
                      >
                        {verifying ? (
                          <>
                            <FiRefreshCw className="w-4 h-4 mr-2 animate-spin" />
                            Verifying Payment...
                          </>
                        ) : (
                          <>
                            <FiShield className="w-4 h-4 mr-2" />
                            Verify Payment
                          </>
                        )}
                      </button>

                      {verificationResult && (
                        <div className={`mt-4 p-4 rounded-lg ${
                          verificationResult.success ? 'bg-green-100' : 'bg-red-100'
                        }`}>
                          <h5 className={`font-medium mb-2 ${
                            verificationResult.success ? 'text-green-800' : 'text-red-800'
                          }`}>
                            Verification {verificationResult.success ? 'Successful' : 'Failed'}
                          </h5>
                          
                          {verificationResult.steps.map((step, index) => (
                            <div key={index} className="flex items-center justify-between py-2 border-b last:border-0">
                              <span className="text-sm">{step.name}</span>
                              <span className={`flex items-center text-sm ${
                                step.status === 'success' ? 'text-green-600' : 'text-red-600'
                              }`}>
                                {step.status === 'success' ? (
                                  <FiCheck className="w-4 h-4 mr-1" />
                                ) : (
                                  <FiX className="w-4 h-4 mr-1" />
                                )}
                                {step.message}
                              </span>
                            </div>
                          ))}

                          <p className="text-xs text-gray-500 mt-2">
                            Verified at: {new Date(verificationResult.verifiedAt).toLocaleString()}
                          </p>
                        </div>
                      )}
                    </div>
                  )}

                  {selectedPayment.verified && (
                    <div className="space-y-2">
                      <div className="flex items-center text-green-600">
                        <FiShield className="w-4 h-4 mr-2" />
                        <span className="font-medium">Payment verified successfully</span>
                      </div>
                      <p className="text-sm text-gray-600">
                        Verified by: {selectedPayment.verifiedBy} at {new Date(selectedPayment.verifiedAt).toLocaleString()}
                      </p>
                      <p className="text-sm text-gray-600">
                        Certificate Hash: <span className="font-mono">{selectedPayment.certificateHash}</span>
                      </p>
                    </div>
                  )}

                  {selectedPayment.failureReason && (
                    <div className="mt-2 p-3 bg-red-50 rounded-lg">
                      <p className="text-sm text-red-600">
                        <span className="font-medium">Failure Reason:</span> {selectedPayment.failureReason}
                      </p>
                    </div>
                  )}
                </div>

                {/* Timeline */}
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Transaction Timeline</h4>
                  <div className="space-y-3">
                    <div className="flex items-center">
                      <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center mr-3">
                        <FiCalendar className="w-4 h-4 text-blue-600" />
                      </div>
                      <div>
                        <p className="text-sm font-medium">Payment Initiated</p>
                        <p className="text-xs text-gray-500">{new Date(selectedPayment.paymentDate).toLocaleString()}</p>
                      </div>
                    </div>
                    
                    {selectedPayment.verified && (
                      <div className="flex items-center">
                        <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center mr-3">
                          <FiShield className="w-4 h-4 text-green-600" />
                        </div>
                        <div>
                          <p className="text-sm font-medium">Payment Verified</p>
                          <p className="text-xs text-gray-500">{new Date(selectedPayment.verifiedAt).toLocaleString()}</p>
                        </div>
                      </div>
                    )}

                    {selectedPayment.confirmedDate && (
                      <div className="flex items-center">
                        <div className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center mr-3">
                          <FiCheck className="w-4 h-4 text-green-600" />
                        </div>
                        <div>
                          <p className="text-sm font-medium">Payment Confirmed</p>
                          <p className="text-xs text-gray-500">{new Date(selectedPayment.confirmedDate).toLocaleString()}</p>
                        </div>
                      </div>
                    )}

                    {selectedPayment.failureReason && (
                      <div className="flex items-center">
                        <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center mr-3">
                          <FiX className="w-4 h-4 text-red-600" />
                        </div>
                        <div>
                          <p className="text-sm font-medium">Payment Failed</p>
                          <p className="text-xs text-red-600">{selectedPayment.failureReason}</p>
                        </div>
                      </div>
                    )}
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

export default PaymentManagement;