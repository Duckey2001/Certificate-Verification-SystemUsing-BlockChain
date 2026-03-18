import React, { useState } from 'react';
import { FiX, FiCheck, FiClock, FiAlertCircle, FiShield, FiRefreshCw, FiDownload, FiMail, FiPhone, FiCalendar, FiDollarSign } from 'react-icons/fi';

const PaymentDetails = ({ payment, onClose, onVerify, onRefresh }) => {
  const [verifying, setVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState(null);
  const [receiptLoading, setReceiptLoading] = useState(false);

  const getStatusColor = (status) => {
    switch(status?.toLowerCase()) {
      case 'confirmed':
      case 'completed':
        return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400';
      case 'pending':
      case 'processing':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400';
      case 'failed':
      case 'cancelled':
        return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400';
      case 'refunded':
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400';
    }
  };

  const getStatusIcon = (status) => {
    switch(status?.toLowerCase()) {
      case 'confirmed':
      case 'completed':
        return <FiCheck className="w-4 h-4" />;
      case 'pending':
      case 'processing':
        return <FiClock className="w-4 h-4" />;
      case 'failed':
      case 'cancelled':
        return <FiAlertCircle className="w-4 h-4" />;
      default:
        return null;
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    try {
      return new Date(dateString).toLocaleString('en-LS', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      });
    } catch (error) {
      return 'Invalid Date';
    }
  };

  const formatCurrency = (amount, currency = 'LSL') => {
    if (amount === null || amount === undefined) return 'N/A';
    try {
      return new Intl.NumberFormat('en-LS', {
        style: 'currency',
        currency: currency,
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(amount);
    } catch (error) {
      return `${currency} ${amount.toFixed(2)}`;
    }
  };

  const handleVerify = async () => {
    if (!onVerify) return;
    
    setVerifying(true);
    setVerificationResult(null);
    
    try {
      const result = await onVerify(payment);
      setVerificationResult({
        success: true,
        message: 'Payment verified successfully',
        ...result
      });
    } catch (error) {
      setVerificationResult({
        success: false,
        message: error.message || 'Verification failed'
      });
    } finally {
      setVerifying(false);
    }
  };

  const handleDownloadReceipt = async () => {
    setReceiptLoading(true);
    try {
      // Simulate receipt generation - replace with actual API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      // Create a simple receipt HTML
      const receiptContent = `
        <!DOCTYPE html>
        <html>
        <head>
          <title>Payment Receipt - ${payment?.payment_id || payment?.id}</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 40px; }
            .receipt { max-width: 600px; margin: 0 auto; border: 1px solid #ddd; padding: 30px; }
            .header { text-align: center; margin-bottom: 30px; }
            .title { font-size: 24px; color: #333; }
            .details { margin: 20px 0; }
            .row { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }
            .label { color: #666; }
            .value { font-weight: bold; }
            .status { padding: 5px 10px; border-radius: 4px; display: inline-block; }
            .footer { margin-top: 40px; text-align: center; color: #999; font-size: 12px; }
          </style>
        </head>
        <body>
          <div class="receipt">
            <div class="header">
              <h1 class="title">Payment Receipt</h1>
              <p>${formatDate(new Date())}</p>
            </div>
            <div class="details">
              <div class="row">
                <span class="label">Payment ID:</span>
                <span class="value">${payment?.payment_id || payment?.id}</span>
              </div>
              <div class="row">
                <span class="label">Transaction ID:</span>
                <span class="value">${payment?.transaction_id || payment?.transactionId || 'N/A'}</span>
              </div>
              <div class="row">
                <span class="label">Amount:</span>
                <span class="value">${formatCurrency(payment?.amount, payment?.currency)}</span>
              </div>
              <div class="row">
                <span class="label">Status:</span>
                <span class="value status ${getStatusColor(payment?.status)}">${payment?.status}</span>
              </div>
              <div class="row">
                <span class="label">Payment Method:</span>
                <span class="value">${payment?.method || 'N/A'}</span>
              </div>
              <div class="row">
                <span class="label">Payer Name:</span>
                <span class="value">${payment?.payer_name || payment?.payerName || 'N/A'}</span>
              </div>
              <div class="row">
                <span class="label">Payer Email:</span>
                <span class="value">${payment?.payer_email || payment?.payerEmail || 'N/A'}</span>
              </div>
              <div class="row">
                <span class="label">Payment Date:</span>
                <span class="value">${formatDate(payment?.created_at || payment?.createdAt || payment?.paymentDate)}</span>
              </div>
              ${payment?.confirmed_at || payment?.confirmedDate ? `
              <div class="row">
                <span class="label">Confirmed Date:</span>
                <span class="value">${formatDate(payment?.confirmed_at || payment?.confirmedDate)}</span>
              </div>
              ` : ''}
            </div>
            <div class="footer">
              <p>This is an electronically generated receipt</p>
            </div>
          </div>
        </body>
        </html>
      `;

      // Download as HTML file
      const blob = new Blob([receiptContent], { type: 'text/html' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `receipt_${payment?.payment_id || payment?.id}_${new Date().toISOString().split('T')[0]}.html`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading receipt:', error);
      alert('Failed to download receipt. Please try again.');
    } finally {
      setReceiptLoading(false);
    }
  };

  const handleSendEmail = () => {
    const email = payment?.payer_email || payment?.payerEmail;
    if (!email) {
      alert('No email address available for this payment');
      return;
    }

    // Create mailto link with payment details
    const subject = `Payment Receipt - ${payment?.payment_id || payment?.id}`;
    const body = `Dear ${payment?.payer_name || payment?.payerName},\n\n` +
      `Thank you for your payment. Here are your payment details:\n\n` +
      `Payment ID: ${payment?.payment_id || payment?.id}\n` +
      `Transaction ID: ${payment?.transaction_id || payment?.transactionId || 'N/A'}\n` +
      `Amount: ${formatCurrency(payment?.amount, payment?.currency)}\n` +
      `Status: ${payment?.status}\n` +
      `Date: ${formatDate(payment?.created_at || payment?.createdAt || payment?.paymentDate)}\n\n` +
      `You can download your receipt from the payment portal.\n\n` +
      `Thank you for your business!`;

    window.location.href = `mailto:${email}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
  };

  // Ensure payment data exists
  if (!payment) {
    return (
      <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
        <div className="relative top-20 mx-auto p-5 border w-full max-w-md shadow-lg rounded-lg bg-white dark:bg-gray-800">
          <div className="text-center">
            <FiAlertCircle className="mx-auto h-12 w-12 text-red-500" />
            <h3 className="text-lg font-medium text-gray-900 dark:text-white mt-4">No Payment Data</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-2">Unable to load payment details.</p>
            <button
              onClick={onClose}
              className="mt-4 px-4 py-2 bg-gray-600 text-white text-sm font-medium rounded-md hover:bg-gray-700"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-6 border w-full max-w-3xl shadow-xl rounded-xl bg-white dark:bg-gray-800">
        {/* Header */}
        <div className="flex justify-between items-center mb-6">
          <div>
            <h3 className="text-2xl font-bold text-gray-900 dark:text-white">Payment Details</h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
              Transaction #{payment?.payment_id || payment?.id}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            <FiX className="h-6 w-6" />
          </button>
        </div>

        <div className="space-y-6">
          {/* Status Banner */}
          <div className={`p-4 rounded-lg flex items-center justify-between ${getStatusColor(payment?.status)}`}>
            <div className="flex items-center">
              {getStatusIcon(payment?.status)}
              <span className="ml-2 font-medium">
                Payment {payment?.status?.toUpperCase() || 'PENDING'}
              </span>
            </div>
            {payment?.verified && (
              <div className="flex items-center text-sm">
                <FiShield className="w-4 h-4 mr-1" />
                <span>Verified</span>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex flex-wrap gap-3">
            {onVerify && payment?.status?.toLowerCase() === 'pending' && (
              <button
                onClick={handleVerify}
                disabled={verifying}
                className="flex items-center px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-lg transition-colors"
              >
                {verifying ? (
                  <>
                    <FiRefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    Verifying...
                  </>
                ) : (
                  <>
                    <FiShield className="w-4 h-4 mr-2" />
                    Verify Payment
                  </>
                )}
              </button>
            )}
            
            <button
              onClick={handleDownloadReceipt}
              disabled={receiptLoading}
              className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition-colors"
            >
              {receiptLoading ? (
                <>
                  <FiRefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <FiDownload className="w-4 h-4 mr-2" />
                  Download Receipt
                </>
              )}
            </button>

            {(payment?.payer_email || payment?.payerEmail) && (
              <button
                onClick={handleSendEmail}
                className="flex items-center px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
              >
                <FiMail className="w-4 h-4 mr-2" />
                Email Receipt
              </button>
            )}

            {onRefresh && (
              <button
                onClick={onRefresh}
                className="flex items-center px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded-lg transition-colors ml-auto"
              >
                <FiRefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </button>
            )}
          </div>

          {/* Verification Result */}
          {verificationResult && (
            <div className={`p-4 rounded-lg ${verificationResult.success ? 'bg-green-50 dark:bg-green-900/20' : 'bg-red-50 dark:bg-red-900/20'}`}>
              <div className="flex items-center">
                {verificationResult.success ? (
                  <FiCheck className="w-5 h-5 text-green-600 dark:text-green-400" />
                ) : (
                  <FiAlertCircle className="w-5 h-5 text-red-600 dark:text-red-400" />
                )}
                <span className={`ml-2 font-medium ${verificationResult.success ? 'text-green-800 dark:text-green-400' : 'text-red-800 dark:text-red-400'}`}>
                  {verificationResult.message}
                </span>
              </div>
              {verificationResult.details && (
                <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">{verificationResult.details}</p>
              )}
            </div>
          )}

          {/* Payment Information Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center">
                <FiDollarSign className="w-4 h-4 mr-1" />
                Payment Information
              </h4>
              
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 space-y-3">
                <div>
                  <label className="block text-xs font-medium text-gray-500 dark:text-gray-400">Payment ID</label>
                  <p className="text-sm font-mono font-medium text-gray-900 dark:text-white">
                    {payment?.payment_id || payment?.id || 'N/A'}
                  </p>
                </div>
                
                <div>
                  <label className="block text-xs font-medium text-gray-500 dark:text-gray-400">Transaction ID</label>
                  <p className="text-sm font-mono text-gray-900 dark:text-white">
                    {payment?.transaction_id || payment?.transactionId || 'N/A'}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-500 dark:text-gray-400">Amount</label>
                    <p className="text-lg font-bold text-green-600 dark:text-green-400">
                      {formatCurrency(payment?.amount, payment?.currency)}
                    </p>
                  </div>
                  
                  <div>
                    <label className="block text-xs font-medium text-gray-500 dark:text-gray-400">Method</label>
                    <p className="text-sm font-medium text-gray-900 dark:text-white capitalize">
                      {payment?.method?.replace('_', ' ') || 'N/A'}
                    </p>
                  </div>
                </div>

                {payment?.fee > 0 && (
                  <div className="grid grid-cols-2 gap-3 pt-2 border-t border-gray-200 dark:border-gray-600">
                    <div>
                      <label className="block text-xs font-medium text-gray-500 dark:text-gray-400">Fee</label>
                      <p className="text-sm text-orange-600 dark:text-orange-400">
                        {formatCurrency(payment.fee, payment?.currency)}
                      </p>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-500 dark:text-gray-400">Net Amount</label>
                      <p className="text-sm font-medium text-blue-600 dark:text-blue-400">
                        {formatCurrency(payment?.net_amount || payment?.netAmount || payment?.amount - (payment?.fee || 0), payment?.currency)}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="space-y-3">
              <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 flex items-center">
                <FiPhone className="w-4 h-4 mr-1" />
                Customer Information
              </h4>
              
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 space-y-3">
                <div>
                  <label className="block text-xs font-medium text-gray-500 dark:text-gray-400">Name</label>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    {payment?.payer_name || payment?.payerName || 'N/A'}
                  </p>
                </div>
                
                <div>
                  <label className="block text-xs font-medium text-gray-500 dark:text-gray-400">Email</label>
                  <p className="text-sm text-gray-900 dark:text-white">
                    {payment?.payer_email || payment?.payerEmail || 'N/A'}
                  </p>
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-500 dark:text-gray-400">Phone</label>
                  <p className="text-sm text-gray-900 dark:text-white">
                    {payment?.payer_phone || payment?.payerPhone || payment?.mpesa_phone_number || 'N/A'}
                  </p>
                </div>

                {(payment?.ip_address || payment?.ipAddress) && (
                  <div>
                    <label className="block text-xs font-medium text-gray-500 dark:text-gray-400">IP Address</label>
                    <p className="text-sm font-mono text-gray-900 dark:text-white">
                      {payment?.ip_address || payment?.ipAddress}
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* M-Pesa Specific Details */}
          {payment?.method?.toLowerCase().includes('mpesa') && (
            <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
              <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">M-Pesa Transaction Details</h4>
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {payment?.mpesa_transaction_id && (
                    <div>
                      <label className="block text-xs font-medium text-gray-500 dark:text-gray-400">M-Pesa Transaction ID</label>
                      <p className="text-sm font-mono">{payment.mpesa_transaction_id}</p>
                    </div>
                  )}
                  {payment?.mpesa_phone_number && (
                    <div>
                      <label className="block text-xs font-medium text-gray-500 dark:text-gray-400">Phone Number</label>
                      <p className="text-sm">{payment.mpesa_phone_number}</p>
                    </div>
                  )}
                  {payment?.mpesa_checkout_request_id && (
                    <div>
                      <label className="block text-xs font-medium text-gray-500 dark:text-gray-400">Checkout Request ID</label>
                      <p className="text-sm font-mono">{payment.mpesa_checkout_request_id}</p>
                    </div>
                  )}
                  {payment?.mpesa_merchant_request_id && (
                    <div>
                      <label className="block text-xs font-medium text-gray-500 dark:text-gray-400">Merchant Request ID</label>
                      <p className="text-sm font-mono">{payment.mpesa_merchant_request_id}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Timeline */}
          <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
            <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center">
              <FiCalendar className="w-4 h-4 mr-1" />
              Timeline
            </h4>
            <div className="space-y-3">
              <div className="flex items-center justify-between bg-gray-50 dark:bg-gray-700/50 p-3 rounded-lg">
                <span className="text-sm text-gray-600 dark:text-gray-400">Created:</span>
                <span className="text-sm font-medium text-gray-900 dark:text-white">
                  {formatDate(payment?.created_at || payment?.createdAt || payment?.paymentDate)}
                </span>
              </div>
              
              {(payment?.confirmed_at || payment?.confirmedDate) && (
                <div className="flex items-center justify-between bg-green-50 dark:bg-green-900/20 p-3 rounded-lg">
                  <span className="text-sm text-green-600 dark:text-green-400">Confirmed:</span>
                  <span className="text-sm font-medium text-green-700 dark:text-green-300">
                    {formatDate(payment?.confirmed_at || payment?.confirmedDate)}
                  </span>
                </div>
              )}

              {payment?.verified_at && (
                <div className="flex items-center justify-between bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg">
                  <span className="text-sm text-blue-600 dark:text-blue-400">Verified:</span>
                  <span className="text-sm font-medium text-blue-700 dark:text-blue-300">
                    {formatDate(payment.verified_at)}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Error Message */}
          {payment?.error_message && (
            <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <div className="flex items-start">
                <FiAlertCircle className="w-5 h-5 text-red-600 dark:text-red-400 mt-0.5 mr-3 flex-shrink-0" />
                <div>
                  <p className="text-sm font-medium text-red-800 dark:text-red-400">Error Message</p>
                  <p className="text-sm text-red-600 dark:text-red-300 mt-1">{payment.error_message}</p>
                </div>
              </div>
            </div>
          )}

          {/* Close Button */}
          <div className="flex justify-end pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={onClose}
              className="px-6 py-2 bg-gray-600 hover:bg-gray-700 text-white text-sm font-medium rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PaymentDetails;