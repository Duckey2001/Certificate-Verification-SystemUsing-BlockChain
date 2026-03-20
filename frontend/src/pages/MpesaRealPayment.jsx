import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { toast, ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const API_BASE_URL = 'http://localhost:5000/api/mpesa';

const MpesaPayment = () => {
    const [loading, setLoading] = useState(false);
    const [sessionLoading, setSessionLoading] = useState(false);
    const [sessionId, setSessionId] = useState(null);
    const [config, setConfig] = useState({});
    const [formData, setFormData] = useState({
        customer_msisdn: '',
        amount: '',
        mandate_id: '15045',
        reference: ''
    });

    // Load config on component mount
    useEffect(() => {
        fetchConfig();
    }, []);

    const fetchConfig = async () => {
        try {
            const response = await axios.get(`${API_BASE_URL}/config`);
            if (response.data.success) {
                setConfig(response.data.config);
            }
        } catch (error) {
            console.error('Failed to load config:', error);
        }
    };

    const generateSession = async () => {
        setSessionLoading(true);
        try {
            const response = await axios.post(`${API_BASE_URL}/generate-session`);
            if (response.data.success) {
                setSessionId(response.data.session_id);
                toast.success('✅ Production session generated!');
                console.log('Session endpoint:', response.data.endpoint);
            } else {
                toast.error('Failed to generate session');
            }
        } catch (error) {
            toast.error('Error generating session: ' + error.message);
        } finally {
            setSessionLoading(false);
        }
    };

    const handleInputChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        
        if (!formData.customer_msisdn || !formData.amount) {
            toast.warning('Please fill all required fields');
            return;
        }

        setLoading(true);
        try {
            const response = await axios.post(`${API_BASE_URL}/direct-debit`, {
                ...formData,
                reference: formData.reference || `ref_${Date.now()}` 
            });

            if (response.data.success) {
                toast.success('✅ Real payment processed successfully!');
                console.log('Payment response:', response.data);
                
                // Reset form on success
                setFormData({
                    customer_msisdn: '',
                    amount: '',
                    mandate_id: '15045',
                    reference: ''
                });
            } else {
                toast.error('Payment failed: ' + (response.data.message || 'Unknown error'));
            }
        } catch (error) {
            toast.error('Error processing payment: ' + error.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-100 py-6 flex flex-col justify-center sm:py-12">
            <ToastContainer position="top-right" autoClose={5000} />
            
            <div className="relative py-3 sm:max-w-xl sm:mx-auto">
                <div className="absolute inset-0 bg-gradient-to-r from-blue-300 to-blue-600 shadow-lg transform -skew-y-6 sm:skew-y-0 sm:-rotate-6 sm:rounded-3xl"></div>
                
                <div className="relative px-4 py-10 bg-white shadow-lg sm:rounded-3xl sm:p-20">
                    <div className="max-w-md mx-auto">
                        <div className="divide-y divide-gray-200">
                            <div className="py-8 text-base leading-6 space-y-4 text-gray-700 sm:text-lg sm:leading-7">
                                <h2 className="text-2xl font-bold mb-8 text-center text-yellow-600">
                                    🧪 M-Pesa SANDBOX - No Real Money
                                </h2>
                                
                                {/* Business Info */}
                                <div className="bg-yellow-50 border-l-4 border-yellow-500 p-4 rounded-lg mb-6">
                                    <p className="text-sm text-gray-600">Business Shortcode:</p>
                                    <p className="text-xl font-bold text-yellow-700">{config.shortcode || '110799'}</p>
                                    <p className="text-sm text-gray-600 mt-2">Market: Lesotho (LSL)</p>
                                    <p className="text-sm text-gray-600">Environment: <span className="font-bold text-yellow-600">{config.environment || 'SANDBOX'}</span></p>
                                    <p className="text-xs text-yellow-600 mt-2">🔴 NO REAL MONEY - TESTING ONLY</p>
                                </div>

                                {/* Session Management */}
                                <div className="mb-6">
                                    <button
                                        onClick={generateSession}
                                        disabled={sessionLoading}
                                        className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${
                                            sessionLoading 
                                                ? 'bg-gray-400 cursor-not-allowed' 
                                                : 'bg-yellow-600 hover:bg-yellow-700'
                                        } focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500`}
                                    >
                                        {sessionLoading ? 'Generating...' : sessionId ? 'Regenerate Session' : 'Generate Session'}
                                    </button>
                                    
                                    {sessionId && (
                                        <p className="mt-2 text-xs text-green-600 break-all">
                                            Session ID: {sessionId.substring(0, 20)}...
                                        </p>
                                    )}
                                </div>

                                {/* Payment Form */}
                                <form onSubmit={handleSubmit} className="space-y-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700">
                                            Customer MSISDN (Real Phone Number) *
                                        </label>
                                        <input
                                            type="text"
                                            name="customer_msisdn"
                                            value={formData.customer_msisdn}
                                            onChange={handleInputChange}
                                            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-red-500 focus:border-red-500 sm:text-sm"
                                            placeholder="+266 5888 1234"
                                            required
                                        />
                                        <p className="text-xs text-gray-500 mt-1">
                                            Enter real customer mobile number with country code
                                        </p>
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-gray-700">
                                            Amount (LSL) *
                                        </label>
                                        <input
                                            type="number"
                                            name="amount"
                                            value={formData.amount}
                                            onChange={handleInputChange}
                                            step="0.01"
                                            min="0.01"
                                            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                                            placeholder="10.00"
                                            required
                                        />
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-gray-700">
                                            Mandate ID
                                        </label>
                                        <input
                                            type="text"
                                            name="mandate_id"
                                            value={formData.mandate_id}
                                            onChange={handleInputChange}
                                            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                                            placeholder="15045"
                                        />
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-gray-700">
                                            Reference (Optional)
                                        </label>
                                        <input
                                            type="text"
                                            name="reference"
                                            value={formData.reference}
                                            onChange={handleInputChange}
                                            className="mt-1 block w-full border border-gray-300 rounded-md shadow-sm py-2 px-3 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                                            placeholder={`ref_${Date.now()}`}
                                        />
                                    </div>

                                    <button
                                        type="submit"
                                        disabled={loading || !sessionId}
                                        className={`w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white ${
                                            loading || !sessionId
                                                ? 'bg-gray-400 cursor-not-allowed'
                                                : 'bg-yellow-600 hover:bg-yellow-700'
                                        } focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-yellow-500`}
                                    >
                                        {loading ? 'Processing...' : '🧪 Test Sandbox Payment'}
                                    </button>
                                </form>

                                {/* Sandbox Info */}
                                <div className="mt-8 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                                    <h3 className="text-sm font-medium text-yellow-800 mb-2">🧪 SANDBOX MODE - TESTING ONLY</h3>
                                    <div className="text-xs space-y-1 text-yellow-700">
                                        <p>🔴 NO real USSD prompts sent to phones</p>
                                        <p>💰 NO real money deducted from accounts</p>
                                        <p>📱 NO SMS notifications sent</p>
                                        <p>� API calls go to sandbox servers</p>
                                        <p>📊 Responses are simulated/dummy data</p>
                                        <p>✅ Safe for testing without consequences</p>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default MpesaPayment;
