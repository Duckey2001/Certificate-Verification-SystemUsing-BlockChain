import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiDollarSign, FiSearch, FiFilter, FiEye, FiDownload, FiTrendingUp, FiCalendar, FiCheck, FiX, FiClock } from 'react-icons/fi';
import DataTable from './DataTable';

const PaymentManagement = () => {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedPayment, setSelectedPayment] = useState(null);
  const [showDetails, setShowDetails] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterMethod, setFilterMethod] = useState('all');
  const [dateRange, setDateRange] = useState({ start: '', end: '' });

  useEffect(() => {
    setLoading(true);
    // Simulate API call
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
          verificationId: 'VER_001',
          certificateHash: '0x7b3d8f9a2c5e6f1b4a8c9d0e3f5a7b9',
          paymentDate: '2024-01-15T10:30:00Z',
          confirmedDate: '2024-01-15T10:32:00Z',
          fee: 0.25,
          netAmount: 4.75,
          ipAddress: '192.168.1.100',
          location: 'Maseru, Lesotho'
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
          verificationId: 'VER_002',
          certificateHash: '0x9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4',
          paymentDate: '2024-01-15T09:15:00Z',
          confirmedDate: null,
          fee: 0.25,
          netAmount: 4.75,
          ipAddress: '192.168.1.101',
          location: 'Leribe, Lesotho'
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
          verificationId: 'VER_003',
          certificateHash: '0x1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6',
          paymentDate: '2024-01-14T15:45:00Z',
          confirmedDate: null,
          fee: 0.25,
          netAmount: 4.75,
          ipAddress: '192.168.1.102',
          location: 'Mafeteng, Lesotho',
          failureReason: 'Insufficient funds'
        }
      ]);
      setLoading(false);
    }, 1000);
  }, []);

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
      render: (value) => (
        <div className="flex items-center">
          <div className="w-8 h-8 rounded-full bg-gradient-to-r from-green-500 to-emerald-500 flex items-center justify-center text-white text-sm font-bold mr-3">
            {value.charAt(0)}
          </div>
          <div>
            <span className="font-medium">{value}</span>
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
      filterable: true,
      sortable: true,
      options: [
        { value: 'all', label: 'All Methods' },
        { value: 'mpesa', label: 'M-Pesa' },
        { value: 'ecocash', label: 'EcoCash' },
        { value: 'bank', label: 'Bank Transfer' }
      ],
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
      filterable: true,
      sortable: true,
      options: [
        { value: 'all', label: 'All Status' },
        { value: 'confirmed', label: 'Confirmed' },
        { value: 'pending', label: 'Pending' },
        { value: 'failed', label: 'Failed' },
        { value: 'refunded', label: 'Refunded' }
      ],
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
      key: 'verificationId',
      label: 'Verification',
      sortable: true,
      render: (value) => (
        <span className="font-mono text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-400 px-2 py-1 rounded">
          {value}
        </span>
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
      key: 'confirmedDate',
      label: 'Confirmed',
      sortable: true,
      render: (value) => (
        <div className="flex items-center">
          {value ? (
            <>
              <FiCheck className="w-4 h-4 mr-1 text-green-500" />
              <span className="text-sm">{new Date(value).toLocaleDateString()}</span>
            </>
          ) : (
            <>
              <FiClock className="w-4 h-4 mr-1 text-yellow-500" />
              <span className="text-sm text-gray-500">Pending</span>
            </>
          )}
        </div>
      )
    }
  ];

  const handleViewPayment = (payment) => {
    setSelectedPayment(payment);
    setShowDetails(true);
  };

  const handleExportPayments = () => {
    const csv = [
      ['Payment ID', 'Transaction ID', 'Payer Name', 'Amount', 'Method', 'Status', 'Payment Date'],
      ...payments.map(p => [
        p.paymentId,
        p.transactionId,
        p.payerName,
        p.amount,
        p.method,
        p.status,
        p.paymentDate
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `payments_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  const stats = {
    total: payments.length,
    confirmed: payments.filter(p => p.status === 'confirmed').length,
    pending: payments.filter(p => p.status === 'pending').length,
    failed: payments.filter(p => p.status === 'failed').length,
    totalRevenue: payments.filter(p => p.status === 'confirmed').reduce((sum, p) => sum + p.netAmount, 0),
    totalFees: payments.filter(p => p.status === 'confirmed').reduce((sum, p) => sum + p.fee, 0)
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Payment Management</h2>
          <p className="text-gray-600 dark:text-gray-400">Monitor and manage all payment transactions</p>
        </div>
        
        <div className="flex space-x-3">
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
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
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

      {/* Payment Methods Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Payment Methods Distribution</h3>
          <div className="space-y-4">
            {['mpesa', 'ecocash', 'bank'].map(method => {
              const count = payments.filter(p => p.method === method).length;
              const percentage = payments.length > 0 ? (count / payments.length * 100).toFixed(1) : 0;
              const colors = {
                mpesa: 'bg-green-500',
                ecocash: 'bg-blue-500',
                bank: 'bg-purple-500'
              };
              const icons = {
                mpesa: '📱 M-Pesa',
                ecocash: '📲 EcoCash',
                bank: '🏦 Bank Transfer'
              };
              
              return (
                <div key={method} className="flex items-center space-x-4">
                  <span className="text-lg w-24">{icons[method]}</span>
                  <div className="flex-1">
                    <div className="flex justify-between mb-1">
                      <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{count} payments</span>
                      <span className="text-sm text-gray-600 dark:text-gray-400">{percentage}%</span>
                    </div>
                    <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                      <div className={`h-full ${colors[method]} transition-all duration-500`} style={{ width: `${percentage}%` }} />
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Quick Stats</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
              <span className="text-sm font-medium text-green-700 dark:text-green-400">Success Rate</span>
              <span className="text-bold text-green-600">
                {payments.length > 0 ? ((stats.confirmed / payments.length) * 100).toFixed(1) : 0}%
              </span>
            </div>
            <div className="flex justify-between items-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <span className="text-sm font-medium text-blue-700 dark:text-blue-400">Avg. Transaction</span>
              <span className="text-bold text-blue-600">M5.00</span>
            </div>
            <div className="flex justify-between items-center p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
              <span className="text-sm font-medium text-purple-700 dark:text-purple-400">Total Volume</span>
              <span className="text-bold text-purple-600">M{(payments.length * 5).toFixed(0)}</span>
            </div>
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
        onView={handleViewPayment}
      />

      {/* Payment Details Modal */}
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
              className="bg-white dark:bg-gray-800 rounded-2xl p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto"
              onClick={e => e.stopPropagation()}
            >
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-6">Payment Details</h3>
              
              <div className="space-y-6">
                {/* Payment Overview */}
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Payment Overview</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Payment ID</p>
                      <p className="font-mono">{selectedPayment.paymentId}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Transaction ID</p>
                      <p className="font-mono">{selectedPayment.transactionId}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Status</p>
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        selectedPayment.status === 'confirmed' ? 'bg-green-100 text-green-800' :
                        selectedPayment.status === 'pending' ? 'bg-yellow-100 text-yellow-800' :
                        'bg-red-100 text-red-800'
                      }`}>
                        {selectedPayment.status}
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
                      <p className="text-sm text-gray-500 dark:text-gray-400">IP Address</p>
                      <p className="font-mono">{selectedPayment.ipAddress}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-500 dark:text-gray-400">Location</p>
                      <p className="font-medium">{selectedPayment.location}</p>
                    </div>
                  </div>
                </div>

                {/* Timeline */}
                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-3">Transaction Timeline</h4>
                  <div className="space-y-3">
                    <div className="flex items-center">
                      <FiCalendar className="w-4 h-4 mr-3 text-blue-500" />
                      <div>
                        <p className="text-sm font-medium">Payment Initiated</p>
                        <p className="text-xs text-gray-500">{new Date(selectedPayment.paymentDate).toLocaleString()}</p>
                      </div>
                    </div>
                    {selectedPayment.confirmedDate && (
                      <div className="flex items-center">
                        <FiCheck className="w-4 h-4 mr-3 text-green-500" />
                        <div>
                          <p className="text-sm font-medium">Payment Confirmed</p>
                          <p className="text-xs text-gray-500">{new Date(selectedPayment.confirmedDate).toLocaleString()}</p>
                        </div>
                      </div>
                    )}
                    {selectedPayment.failureReason && (
                      <div className="flex items-center">
                        <FiX className="w-4 h-4 mr-3 text-red-500" />
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
