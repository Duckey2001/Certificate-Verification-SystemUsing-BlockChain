// src/testApiCall.js
import api from './api/axiosConfig';

// Test function to verify API setup
export const testApiConnection = async () => {
  try {
    console.log('🧪 Testing API connection...');
    
    // Try to connect to backend (adjust endpoint as needed)
    const response = await api.get('/health');
    console.log('✅ Backend is running:', response.data);
    return true;
  } catch (error) {
    console.log('⚠️ Backend may not be running or endpoint different');
    console.log('Error details:', error.message);
    
    // Try a different test endpoint
    try {
      const testResponse = await api.get('/');
      console.log('✅ Backend responded:', testResponse.status);
      return true;
    } catch (error2) {
      console.log('❌ Cannot connect to backend at http://localhost:8000');
      console.log('Make sure your Python backend is running');
      return false;
    }
  }
};

// Test authentication endpoints
export const testAuthEndpoints = async () => {
  const endpoints = ['/auth/login', '/auth/register', '/auth/logout'];
  
  for (const endpoint of endpoints) {
    try {
      const response = await api.options(endpoint);
      console.log(`✅ ${endpoint}:`, response.status);
    } catch (error) {
      console.log(`❌ ${endpoint}:`, error.message);
    }
  }
};
