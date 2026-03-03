import React, { useState } from 'react';
import axios from 'axios';

const PaymentModal = ({ isOpen, onClose, amount = 5.00, verificationId, onPaymentComplete }) => {
  const [phoneNumber, setPhoneNumber] = useState('');
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const formatLesothoPhone = (phone) => {
    // Remove non-digits
    let cleaned = phone.replace(/\D/g, '');
    
    if (cleaned.startsWith('266')) {
      return '+' + cleaned;
    } else if (cleaned.startsWith('0')) {
      return '+266' + cleaned.substring(1);
    } else if (cleaned.length === 8) {
      return '+266' + cleaned;
    }
    return phone;
  };

  const handlePayment = async (e) => {
    e.preventDefault();
    
    if (!phoneNumber) {
      setError('Please enter your M-Pesa phone number');
      return;
    }

    setProcessing(true);
    setError('');
    setSuccess('');

    try {
      const formattedPhone = formatLesothoPhone(phoneNumber);
      
      const response = await axios.post('/api/mpesa/stk-push', {
        phone_number: formattedPhone,
        amount: amount,
        verification_request_id: verificationId,
        account_reference: `CertiVert-LS-${Date.now()}`
      });

      setSuccess('STK push sent! Please check your phone and enter your PIN.');
      
      if (onPaymentComplete) {
        onPaymentComplete(response.data);
      }

      // Auto close after 5 seconds on success
      setTimeout(() => {
        onClose();
      }, 5000);
      
    } catch (err) {
      setError(err.response?.data?.detail || 'Payment failed. Please try again.');
    } finally {
      setProcessing(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-full max-w-md shadow-lg rounded-lg bg-white">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xl font-bold text-gray-900">M-Pesa Payment</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handlePayment} className="space-y-4">
          {/* Amount Display */}
          <div className="bg-blue-50 p-4 rounded-lg">
            <p className="text-sm text-blue-600 mb-1">Amount to Pay</p>
            <p className="text-3xl font-bold text-blue-800">M {amount.toFixed(2)}</p>
            <p className="text-xs text-blue-600 mt-1">Lesotho Maloti</p>
          </div>

          {/* Phone Number Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              M-Pesa Phone Number (Lesotho)
            </label>
            <input
              type="tel"
              value={phoneNumber}
              onChange={(e) => setPhoneNumber(e.target.value)}
              placeholder="5XXX XXXX or +266 5XXX XXXX"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={processing}
              required
            />
            <p className="text-xs text-gray-500 mt-1">
              Enter your Vodacom Lesotho M-Pesa number
            </p>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={processing}
            className={`w-full py-3 px-4 rounded-lg font-medium transition-colors ${
              processing
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-green-600 text-white hover:bg-green-700'
            }`}
          >
            {processing ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Processing...
              </span>
            ) : (
              'Pay with M-Pesa'
            )}
          </button>

          {/* Error Message */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          {/* Success Message */}
          {success && (
            <div className="p-3 bg-green-50 border border-green-200 rounded">
              <p className="text-sm text-green-600">{success}</p>
            </div>
          )}
        </form>

        {/* M-Pesa Instructions */}
        <div className="mt-4 p-3 bg-gray-50 rounded-lg">
          <h4 className="text-xs font-semibold text-gray-700 mb-2">How to pay:</h4>
          <ol className="text-xs text-gray-600 space-y-1 list-decimal list-inside">
            <li>Enter your M-Pesa registered phone number</li>
            <li>Click "Pay with M-Pesa" to receive STK push</li>
            <li>Enter your M-Pesa PIN on your phone</li>
            <li>Wait for confirmation message</li>
          </ol>
        </div>
      </div>
    </div>
  );
};

export default PaymentModal;