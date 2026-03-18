// src/TestApi.jsx
import React, { useEffect, useState } from 'react';
import { authApi, certificateApi } from './api';

const TestApi = () => {
  const [status, setStatus] = useState('Testing...');
  const [backendStatus, setBackendStatus] = useState('Unknown');

  useEffect(() => {
    testApiConnection();
  }, []);

  const testApiConnection = async () => {
    try {
      setStatus('Testing backend connection...');
      
      // Try to connect to backend
      const testResponse = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000/api'}/health`);
      if (testResponse.ok) {
        const data = await testResponse.json();
        setBackendStatus(`✅ Running: ${data.message || 'OK'}`);
      } else {
        setBackendStatus('⚠️ Backend responded with error');
      }
      
      // Test login with dummy credentials (expected to fail)
      setStatus('Testing auth endpoints...');
      try {
        await authApi.login({
          username: 'test',
          password: 'test123'
        });
      } catch (error) {
        // Expected to fail - but shows API is communicating
        console.log('Auth test (expected failure):', error.message);
      }
      
      setStatus('✅ API setup complete! Check browser console for details.');
      
    } catch (error) {
      setStatus(`❌ Error: ${error.message}`);
      setBackendStatus('❌ Cannot connect to backend');
      console.error('Connection error:', error);
    }
  };

  return (
    <div className="p-6 max-w-md mx-auto mt-10 bg-white rounded-lg shadow-md">
      <h2 className="text-2xl font-bold mb-4 text-blue-600">CertiVert API Test</h2>
      
      <div className="space-y-4">
        <div className="p-3 bg-gray-100 rounded">
          <strong>API Status:</strong> {status}
        </div>
        
        <div className="p-3 bg-gray-100 rounded">
          <strong>Backend Status:</strong> {backendStatus}
        </div>
        
        <div className="p-3 bg-blue-50 rounded border border-blue-200">
          <p className="font-semibold">Next Steps:</p>
          <ol className="list-decimal list-inside mt-2 text-sm">
            <li>Check browser Console (F12) for API debug logs</li>
            <li>Make sure Python backend is running on port 8000</li>
            <li>Test actual API calls from your components</li>
          </ol>
        </div>
        
        <button
          onClick={testApiConnection}
          className="w-full py-2 px-4 bg-blue-500 text-white rounded hover:bg-blue-600 transition"
        >
          Run Tests Again
        </button>
      </div>
    </div>
  );
};

export default TestApi;
