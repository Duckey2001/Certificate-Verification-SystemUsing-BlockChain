import React from 'react';

const PaymentDetails = ({ payment, onClose }) => {
  const getStatusColor = (status) => {
    switch(status?.toLowerCase()) {
      case 'confirmed':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString('en-LS', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatCurrency = (amount, currency = 'LSL') => {
    return new Intl.NumberFormat('en-LS', {
      style: 'currency',
      currency: currency
    }).format(amount);
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-full max-w-2xl shadow-lg rounded-lg bg-white">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xl font-bold text-gray-900">Payment Details</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="space-y-4">
          {/* Payment Status */}
          <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
            <span className="text-sm font-medium text-gray-600">Payment Status</span>
            <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getStatusColor(payment?.status)}`}>
              {payment?.status?.toUpperCase() || 'PENDING'}
            </span>
          </div>

          {/* Payment Information */}
          <div className="grid grid-cols-2 gap-4">
            <div className="col-span-2 md:col-span-1">
              <label className="block text-xs font-medium text-gray-500">Payment ID</label>
              <p className="text-sm font-mono bg-gray-50 p-2 rounded">{payment?.payment_id || payment?.id || 'N/A'}</p>
            </div>
            <div className="col-span-2 md:col-span-1">
              <label className="block text-xs font-medium text-gray-500">Amount</label>
              <p className="text-sm font-semibold text-green-600">{formatCurrency(payment?.amount, payment?.currency)}</p>
            </div>
          </div>

          {/* M-Pesa Details */}
          {payment?.method === 'mpesa_lesotho' && (
            <>
              <div className="border-t border-gray-200 pt-4">
                <h4 className="text-sm font-semibold text-gray-700 mb-3">M-Pesa Transaction Details</h4>
                <div className="space-y-2">
                  {payment?.mpesa_transaction_id && (
                    <div className="flex justify-between">
                      <span className="text-xs text-gray-500">M-Pesa Transaction ID:</span>
                      <span className="text-xs font-mono">{payment.mpesa_transaction_id}</span>
                    </div>
                  )}
                  {payment?.mpesa_phone_number && (
                    <div className="flex justify-between">
                      <span className="text-xs text-gray-500">Phone Number:</span>
                      <span className="text-xs">{payment.mpesa_phone_number}</span>
                    </div>
                  )}
                  {payment?.mpesa_checkout_request_id && (
                    <div className="flex justify-between">
                      <span className="text-xs text-gray-500">Checkout Request ID:</span>
                      <span className="text-xs font-mono">{payment.mpesa_checkout_request_id}</span>
                    </div>
                  )}
                  {payment?.mpesa_merchant_request_id && (
                    <div className="flex justify-between">
                      <span className="text-xs text-gray-500">Merchant Request ID:</span>
                      <span className="text-xs font-mono">{payment.mpesa_merchant_request_id}</span>
                    </div>
                  )}
                </div>
              </div>
            </>
          )}

          {/* Timestamps */}
          <div className="border-t border-gray-200 pt-4">
            <h4 className="text-sm font-semibold text-gray-700 mb-3">Timeline</h4>
            <div className="space-y-2">
              <div className="flex justify-between">
                <span className="text-xs text-gray-500">Created:</span>
                <span className="text-xs">{formatDate(payment?.created_at || payment?.createdAt)}</span>
              </div>
              {payment?.confirmed_at && (
                <div className="flex justify-between">
                  <span className="text-xs text-gray-500">Confirmed:</span>
                  <span className="text-xs">{formatDate(payment.confirmed_at)}</span>
                </div>
              )}
            </div>
          </div>

          {/* Error Message (if any) */}
          {payment?.error_message && (
            <div className="bg-red-50 border border-red-200 rounded p-3">
              <p className="text-xs text-red-600">{payment.error_message}</p>
            </div>
          )}

          {/* Close Button */}
          <div className="flex justify-end pt-4">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-gray-600 text-white text-sm font-medium rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
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