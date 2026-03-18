import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FiX, FiCheck, FiClock, FiAlertCircle, FiShield,
  FiRefreshCw, FiDownload, FiMail, FiPhone, FiCalendar,
  FiDollarSign, FiCreditCard, FiSmartphone, FiBuilding,
  FiArrowLeft, FiCopy, FiExternalLink
} from 'react-icons/fi';

const MpesaPayment = ({
  isOpen,
  onClose,
  universityCode,
  certificateReference,
  amount,
  onPaymentComplete,
  onPaymentFailed
}) => {
  const [loading, setLoading] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [paymentStatus, setPaymentStatus] = useState(null);
  const [transactionId, setTransactionId] = useState(null);
  const [paymentDetails, setPaymentDetails] = useState(null);
  const [error, setError] = useState(null);
  const [countdown, setCountdown] = useState(0);
  const [pollingInterval, setPollingInterval] = useState(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [pollingInterval]);

  // Handle countdown
  useEffect(() => {
    if (countdown > 0) {
      const timer = setTimeout(() => setCountdown(countdown - 1), 1000);
      return () => clearTimeout(timer);
    }
  }, [countdown]);

  const initiatePayment = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch('/api/mpesa/b2b-payment', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          university_code: universityCode,
          amount: amount.toString(),
          certificate_reference: certificateReference,
          description: `Certificate verification fee for ${certificateReference}`
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Payment initiation failed');
      }

      if (data.success) {
        setTransactionId(data.transaction_id);
        setPaymentStatus('processing');
        setPaymentDetails(data);
        
        // Start polling for transaction status
        startPolling(data.transaction_id);
        
        // Set countdown for next check
        setCountdown(10);
      } else {
        throw new Error(data.message || 'Payment failed');
      }
    } catch (err) {
      setError(err.message);
      if (onPaymentFailed) {
        onPaymentFailed(err.message);
      }
    } finally {
      setLoading(false);
    }
  };

  const startPolling = (transId) => {
    // Clear any existing interval
    if (pollingInterval) {
      clearInterval(pollingInterval);
    }

    // Poll every 5 seconds for 2 minutes
    let attempts = 0;
    const maxAttempts = 24; // 2 minutes worth of polling

    const interval = setInterval(async () => {
      attempts++;
      
      try {
        const status = await checkTransactionStatus(transId);
        
        if (status.success && status.status === 'completed') {
          // Payment completed successfully
          clearInterval(interval);
          setPaymentStatus('completed');
          setPaymentDetails(prev => ({ ...prev, ...status }));
          
          if (onPaymentComplete) {
            onPaymentComplete({
              transactionId: transId,
              ...status
            });
          }
        } else if (status.status === 'failed' || attempts >= maxAttempts) {
          // Payment failed or timeout
          clearInterval(interval);
          setPaymentStatus('failed');
          setError(status.message || 'Payment verification timeout');
          
          if (onPaymentFailed) {
            onPaymentFailed(status.message || 'Payment verification timeout');
          }
        } else {
          // Still processing
          setPaymentStatus('processing');
          setCountdown(5);
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    }, 5000);

    setPollingInterval(interval);
  };

  const checkTransactionStatus = async (transId) => {
    try {
      const response = await fetch('/api/mpesa/query-transaction', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          transaction_reference: transId
        })
      });

      const data = await response.json();
      return data;
    } catch (err) {
      console.error('Error checking transaction status:', err);
      return { success: false, status: 'error', message: err.message };
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    // Show toast notification (implement based on your UI)
  };

  const handleRetry = () => {
    setError(null);
    setPaymentStatus(null);
    setTransactionId(null);
    initiatePayment();
  };

  const handleClose = () => {
    if (pollingInterval) {
      clearInterval(pollingInterval);
    }
    onClose();
  };

  const formatCurrency = (amount, currency = 'LSL') => {
    return new Intl.NumberFormat('en-LS', {
      style: 'currency',
      currency: currency
    }).format(amount);
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString('en-LS', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
        onClick={handleClose}
      >
        <motion.div
          initial={{ scale: 0.9, y: 20 }}
          animate={{ scale: 1, y: 0 }}
          exit={{ scale: 0.9, y: 20 }}
          className="bg-white dark:bg-gray-800 rounded-2xl p-6 max-w-md w-full mx-4"
          onClick={e => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex justify-between items-center mb-6">
            <div className="flex items-center">
              <FiCreditCard className="w-6 h-6 text-green-600 mr-2" />
              <h3 className="text-xl font-bold text-gray-900 dark:text-white">
                M-Pesa B2B Payment
              </h3>
            </div>
            <button
              onClick={handleClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
            >
              <FiX className="w-6 h-6" />
            </button>
          </div>

          {/* Payment Summary */}
          <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4 mb-6">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-gray-600 dark:text-gray-400">Certificate:</span>
              <span className="text-sm font-mono font-medium">{certificateReference}</span>
            </div>
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-gray-600 dark:text-gray-400">University:</span>
              <span className="text-sm font-medium">{universityCode}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">Amount:</span>
              <span className="text-lg font-bold text-green-600">
                {formatCurrency(amount)}
              </span>
            </div>
          </div>

          {/* Payment Status */}
          {!paymentStatus && !error && !loading && (
            <div className="space-y-4">
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Click the button below to initiate M-Pesa B2B payment for certificate verification.
              </p>
              
              <button
                onClick={initiatePayment}
                className="w-full px-4 py-3 bg-green-600 hover:bg-green-700 text-white rounded-lg font-medium transition-colors flex items-center justify-center"
              >
                <FiSmartphone className="w-5 h-5 mr-2" />
                Pay {formatCurrency(amount)} with M-Pesa
              </button>
            </div>
          )}

          {/* Loading State */}
          {loading && (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600 mx-auto mb-4"></div>
              <p className="text-gray-600 dark:text-gray-400">Initiating payment...</p>
            </div>
          )}

          {/* Processing State */}
          {paymentStatus === 'processing' && !error && (
            <div className="space-y-4">
              <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
                <div className="flex items-center mb-3">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-yellow-600 mr-3"></div>
                  <p className="text-yellow-800 dark:text-yellow-400 font-medium">
                    Payment Processing
                  </p>
                </div>
                <p className="text-sm text-yellow-700 dark:text-yellow-500 mb-2">
                  Your payment is being processed. This may take a few moments.
                </p>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-yellow-600">Transaction ID:</span>
                  <span className="font-mono bg-yellow-100 dark:bg-yellow-800 px-2 py-1 rounded">
                    {transactionId}
                  </span>
                </div>
                {countdown > 0 && (
                  <p className="text-xs text-yellow-600 mt-2">
                    Next status check in {countdown} seconds...
                  </p>
                )}
              </div>

              <button
                onClick={() => checkTransactionStatus(transactionId)}
                className="w-full px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg flex items-center justify-center"
              >
                <FiRefreshCw className="w-4 h-4 mr-2" />
                Check Status
              </button>
            </div>
          )}

          {/* Completed State */}
          {paymentStatus === 'completed' && (
            <div className="space-y-4">
              <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
                <div className="flex items-center mb-3">
                  <div className="w-8 h-8 rounded-full bg-green-100 dark:bg-green-800 flex items-center justify-center mr-3">
                    <FiCheck className="w-5 h-5 text-green-600 dark:text-green-400" />
                  </div>
                  <div>
                    <p className="text-green-800 dark:text-green-400 font-medium">
                      Payment Successful!
                    </p>
                    <p className="text-xs text-green-600 dark:text-green-500">
                      {formatDate(paymentDetails?.transaction_date)}
                    </p>
                  </div>
                </div>
                
                <div className="space-y-2 mt-3">
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-600">Transaction ID:</span>
                    <div className="flex items-center">
                      <span className="text-xs font-mono bg-white dark:bg-gray-800 px-2 py-1 rounded mr-2">
                        {transactionId}
                      </span>
                      <button
                        onClick={() => copyToClipboard(transactionId)}
                        className="text-gray-400 hover:text-gray-600"
                      >
                        <FiCopy className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-xs text-gray-600">Amount Paid:</span>
                    <span className="text-sm font-bold text-green-600">
                      {formatCurrency(amount)}
                    </span>
                  </div>
                </div>
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={() => window.open(`/certificate/${certificateReference}`, '_blank')}
                  className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center justify-center"
                >
                  <FiExternalLink className="w-4 h-4 mr-2" />
                  View Certificate
                </button>
                <button
                  onClick={handleClose}
                  className="flex-1 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg"
                >
                  Close
                </button>
              </div>
            </div>
          )}

          {/* Failed State */}
          {paymentStatus === 'failed' && (
            <div className="space-y-4">
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                <div className="flex items-center mb-3">
                  <div className="w-8 h-8 rounded-full bg-red-100 dark:bg-red-800 flex items-center justify-center mr-3">
                    <FiAlertCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
                  </div>
                  <div>
                    <p className="text-red-800 dark:text-red-400 font-medium">
                      Payment Failed
                    </p>
                  </div>
                </div>
                
                <p className="text-sm text-red-700 dark:text-red-500 mb-2">
                  {error || 'Your payment could not be processed. Please try again.'}
                </p>
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={handleRetry}
                  className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg flex items-center justify-center"
                >
                  <FiRefreshCw className="w-4 h-4 mr-2" />
                  Try Again
                </button>
                <button
                  onClick={handleClose}
                  className="flex-1 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg"
                >
                  Close
                </button>
              </div>
            </div>
          )}

          {/* Error State (before payment) */}
          {error && !paymentStatus && (
            <div className="space-y-4">
              <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
                <p className="text-sm text-red-700 dark:text-red-500">
                  {error}
                </p>
              </div>

              <div className="flex space-x-3">
                <button
                  onClick={handleRetry}
                  className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg"
                >
                  Try Again
                </button>
                <button
                  onClick={handleClose}
                  className="flex-1 px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg"
                >
                  Close
                </button>
              </div>
            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
};

export default MpesaPayment;