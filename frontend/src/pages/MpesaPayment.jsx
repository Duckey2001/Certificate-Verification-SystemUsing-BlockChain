import React, { useState } from 'react';
import axios from 'axios';
import { useAuth } from '../contexts/AuthContext';

const MpesaPayment = () => {
  const { user } = useAuth();
  const [phoneNumber, setPhoneNumber] = useState('');
  const [amount, setAmount] = useState('5.00');
  const [verificationRequestId, setVerificationRequestId] = useState('');
  const [processing, setProcessing] = useState(false);
  const [paymentResult, setPaymentResult] = useState(null);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Format phone number for Lesotho (Vodacom Lesotho M-Pesa)
  const formatLesothoPhoneNumber = (phone) => {
    // Remove any non-digit characters
    let cleaned = phone.replace(/\D/g, '');
    
    // Lesotho phone numbers start with 5 or 6 (mobile prefixes)
    // Format: +266 XXXX XXXX or 0XXXX XXXX
    
    if (cleaned.startsWith('266')) {
      // Already has country code
      return '+' + cleaned;
    } else if (cleaned.startsWith('0')) {
      // Local format, add country code
      return '+266' + cleaned.substring(1);
    } else if (cleaned.length === 8) {
      // Just the 8-digit number
      return '+266' + cleaned;
    } else {
      // Return as is, backend will handle validation
      return phone;
    }
  };

  const handlePayment = async (e) => {
    e.preventDefault();
    
    if (!user) {
      setError('Please login to make payments');
      return;
    }

    if (!phoneNumber) {
      setError('Please enter phone number');
      return;
    }

    setProcessing(true);
    setError('');
    setSuccess('');
    setPaymentResult(null);

    try {
      // Format phone number for Lesotho
      const formattedPhone = formatLesothoPhoneNumber(phoneNumber);
      
      const payload = {
        phone_number: formattedPhone,
        amount: parseFloat(amount),
        verification_request_id: verificationRequestId ? parseInt(verificationRequestId) : null,
        account_reference: `CertiVert-LS-${user.username}`,
        transaction_desc: 'Certificate Verification Fee (Lesotho)'
      };

      const response = await axios.post('/api/mpesa/stk-push', payload);
      
      setPaymentResult(response.data);
      setSuccess('M-Pesa STK push initiated! Please check your phone and enter your PIN.');
      
      // Reset form
      setPhoneNumber('');
      setVerificationRequestId('');
      
    } catch (error) {
      console.error('Payment error:', error);
      if (error.response?.data?.detail) {
        setError(error.response.data.detail);
      } else if (error.response?.data?.message) {
        setError(error.response.data.message);
      } else {
        setError('Failed to initiate payment. Please ensure your phone number is correct and try again.');
      }
    } finally {
      setProcessing(false);
    }
  };

  const checkPaymentStatus = async (paymentId) => {
    try {
      const response = await axios.get(`/api/mpesa/status/${paymentId}`);
      setPaymentResult(prev => ({
        ...prev,
        ...response.data
      }));
    } catch (error) {
      console.error('Status check error:', error);
      setError('Failed to check payment status. Please try again.');
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-2xl mx-auto px-4">
        <div className="bg-white rounded-lg shadow-md p-6">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">M-Pesa Payment (Lesotho)</h1>
          <p className="text-gray-600 mb-8">
            Pay for certificate verification using Vodacom Lesotho M-Pesa
          </p>

          {!user && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
              <p className="text-yellow-800 text-sm">
                Please login to make payments. <a href="/login" className="underline">Login here</a>
              </p>
            </div>
          )}

          {/* Payment Form */}
          <form onSubmit={handlePayment} className="space-y-6">
            {/* Phone Number */}
            <div>
              <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-2">
                M-Pesa Phone Number (Lesotho)
              </label>
              <input
                type="tel"
                id="phone"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                placeholder="5XXX XXXX or +266 5XXX XXXX"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={!user || processing}
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                Format: 5XXX XXXX, 6XXX XXXX, or +266 5XXX XXXX (Vodacom Lesotho numbers only)
              </p>
              <p className="text-xs text-blue-600 mt-1">
                Examples: 5123 4567, 6123 4567, or +266 5123 4567
              </p>
            </div>

            {/* Amount */}
            <div>
              <label htmlFor="amount" className="block text-sm font-medium text-gray-700 mb-2">
                Amount (Maloti - M)
              </label>
              <div className="relative">
                <span className="absolute left-3 top-2 text-gray-500">M</span>
                <input
                  type="number"
                  id="amount"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  step="0.01"
                  min="1.00"
                  className="w-full pl-8 pr-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  disabled={!user || processing}
                  required
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">
                Standard verification fee: M 5.00 (Maloti)
              </p>
            </div>

            {/* Verification Request ID (Optional) */}
            <div>
              <label htmlFor="verificationId" className="block text-sm font-medium text-gray-700 mb-2">
                Verification Request ID (Optional)
              </label>
              <input
                type="number"
                id="verificationId"
                value={verificationRequestId}
                onChange={(e) => setVerificationRequestId(e.target.value)}
                placeholder="Enter verification request ID if available"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={!user || processing}
              />
              <p className="text-xs text-gray-500 mt-1">
                Leave blank if paying for general verification
              </p>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={!user || processing}
              className={`w-full py-3 px-4 rounded-lg font-medium transition-colors ${
                !user || processing
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
                  Processing Payment...
                </span>
              ) : (
                'Pay with M-Pesa (Lesotho)'
              )}
            </button>
          </form>

          {/* Error Message */}
          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800 text-sm">{error}</p>
            </div>
          )}

          {/* Success Message */}
          {success && (
            <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-green-800 text-sm">{success}</p>
            </div>
          )}

          {/* Payment Result */}
          {paymentResult && (
            <div className="mt-6 bg-gray-50 rounded-lg p-6">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">Payment Details</h3>
              
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Payment ID:</span>
                  <span className="text-sm font-medium text-gray-800">{paymentResult.payment_id}</span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Amount:</span>
                  <span className="text-sm font-medium text-gray-800">M {paymentResult.amount || amount}</span>
                </div>
                
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Status:</span>
                  <span className={`text-sm font-medium ${
                    paymentResult.status === 'confirmed' ? 'text-green-600' : 
                    paymentResult.status === 'pending' ? 'text-yellow-600' : 'text-red-600'
                  }`}>
                    {paymentResult.status?.toUpperCase()}
                  </span>
                </div>

                {paymentResult.merchant_request_id && (
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Merchant Request ID:</span>
                    <span className="text-sm font-medium text-gray-800">{paymentResult.merchant_request_id}</span>
                  </div>
                )}

                {paymentResult.checkout_request_id && (
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Checkout Request ID:</span>
                    <span className="text-sm font-medium text-gray-800">{paymentResult.checkout_request_id}</span>
                  </div>
                )}

                {paymentResult.customer_message && (
                  <div className="mt-4 p-3 bg-blue-50 rounded">
                    <p className="text-sm text-blue-800">{paymentResult.customer_message}</p>
                  </div>
                )}

                {paymentResult.next_step && (
                  <div className="mt-4 p-3 bg-yellow-50 rounded">
                    <p className="text-sm text-yellow-800">{paymentResult.next_step}</p>
                  </div>
                )}

                {paymentResult.mpesa_transaction_id && (
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">M-Pesa Transaction ID:</span>
                    <span className="text-sm font-medium text-gray-800">{paymentResult.mpesa_transaction_id}</span>
                  </div>
                )}

                {paymentResult.confirmed_at && (
                  <div className="flex justify-between">
                    <span className="text-sm text-gray-600">Confirmed At:</span>
                    <span className="text-sm font-medium text-gray-800">
                      {new Date(paymentResult.confirmed_at).toLocaleString()}
                    </span>
                  </div>
                )}
              </div>

              {/* Check Status Button */}
              {paymentResult.status === 'pending' && (
                <button
                  onClick={() => checkPaymentStatus(paymentResult.payment_id)}
                  className="mt-4 w-full py-2 px-4 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                >
                  Check Payment Status
                </button>
              )}
            </div>
          )}
        </div>

        {/* M-Pesa Lesotho Info */}
        <div className="mt-6 bg-blue-50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-blue-800 mb-3">About M-Pesa Lesotho Payments</h3>
          <div className="space-y-2 text-sm text-blue-700">
            <p>• You will receive an STK push on your Vodacom Lesotho M-Pesa registered number</p>
            <p>• Enter your M-Pesa PIN to complete the payment (amount in Maloti - M)</p>
            <p>• Payment confirmation may take a few seconds to process</p>
            <p>• You can check payment status using the payment ID provided</p>
            <p>• All payments are recorded and linked to your verification requests</p>
            <p className="font-semibold mt-2">Need help?</p>
            <p>• Ensure your phone is on and has network coverage</p>
            <p>• Check that you have sufficient M-Pesa balance (M {amount} required)</p>
            <p>• Contact Vodacom Lesotho M-Pesa support at 100 if issues persist</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MpesaPayment;