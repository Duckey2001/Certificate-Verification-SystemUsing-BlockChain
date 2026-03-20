// src/api/verifierApi.js
import api from './axiosConfig';

// Helper for debugging
const logRequest = (method, url, data = null) => {
  console.log(`🔍 Verifier API ${method}: ${url}`, data || '');
};

// Helper to handle errors
const handleError = (error, defaultMessage) => {
  console.error(`❌ Verifier API Error:`, error.response?.data || error.message);
  throw error;
};

export const verifierApi = {
  // Get verification statistics
  getStats: async () => {
    try {
      logRequest('GET', '/api/verifier/stats');
      const response = await api.get('/api/verifier/stats');
      console.log('✅ Verifier stats received:', response.data);
      return response.data;
    } catch (error) {
      return handleError(error, 'Failed to fetch verifier stats');
    }
  },
  
  // Get my verifications
  getMyVerifications: async (limit = 50, offset = 0) => {
    try {
      logRequest('GET', `/api/verifier/verifications?limit=${limit}`);
      const response = await api.get('/api/verifier/verifications', {
        params: { limit }
      });
      console.log(`✅ Received ${response.data?.length || 0} verifications`);
      return response.data;
    } catch (error) {
      return handleError(error, 'Failed to fetch verifications');
    }
  },
  
  // Get pending verifications
  getPendingVerifications: async (limit = 10) => {
    try {
      logRequest('GET', `/certificates/pending-verifications?limit=${limit}`);
      const response = await api.get('/certificates/pending-verifications', {
        params: { limit }
      });
      console.log(`✅ Received ${response.data?.length || 0} pending verifications`);
      return response.data;
    } catch (error) {
      return handleError(error, 'Failed to fetch pending verifications');
    }
  },
  
  // Get recent verifications
  getRecentVerifications: async (limit = 5) => {
    try {
      logRequest('GET', `/certificates/recent-verifications?limit=${limit}`);
      const response = await api.get('/certificates/recent-verifications', {
        params: { limit }
      });
      console.log(`✅ Received ${response.data?.length || 0} recent verifications`);
      return response.data;
    } catch (error) {
      return handleError(error, 'Failed to fetch recent verifications');
    }
  },
  
  // Get verification details
  getVerificationDetails: async (id) => {
    try {
      logRequest('GET', `/certificates/verification-details/${id}`);
      const response = await api.get(`/certificates/verification-details/${id}`);
      console.log('✅ Verification details received:', response.data);
      return response.data;
    } catch (error) {
      return handleError(error, `Failed to fetch verification details for ID: ${id}`);
    }
  },
  
  // Process verification (approve/reject/flag)
  processVerification: async (id, action, notes = '') => {
    try {
      logRequest('POST', `/certificates/process-verification/${id}`, { action, notes });
      
      // Create form data
      const formData = new FormData();
      formData.append('action', action);
      formData.append('notes', notes);
      
      const response = await api.post(`/certificates/process-verification/${id}`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      console.log(`✅ Verification ${action} successful:`, response.data);
      return response.data;
    } catch (error) {
      return handleError(error, `Failed to ${action} verification`);
    }
  },
  
  // Get verifier activity for charts
  getActivity: async (days = 7) => {
    try {
      logRequest('GET', `/certificates/verifier-activity?days=${days}`);
      const response = await api.get('/certificates/verifier-activity', {
        params: { days }
      });
      console.log('✅ Activity data received');
      return response.data;
    } catch (error) {
      return handleError(error, 'Failed to fetch activity data');
    }
  },
  
  // Test authentication (for debugging)
  testAuth: async () => {
    try {
      const token = localStorage.getItem('token');
      console.log('🔑 Test - Token in localStorage:', token ? `${token.substring(0, 20)}...` : 'No token');
      
      const response = await api.get('/certificates/test-auth');
      console.log('✅ Test - Auth successful:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Test - Auth failed:', error.response?.data || error.message);
      throw error;
    }
  },
  
  // Debug function to check token and endpoint
  debugEndpoint: async (endpoint) => {
    console.group(`🔍 Debugging endpoint: ${endpoint}`);
    
    // Check token
    const token = localStorage.getItem('token');
    console.log('Token exists:', !!token);
    if (token) {
      console.log('Token preview:', token.substring(0, 30) + '...');
      console.log('Token length:', token.length);
      
      // Decode token payload (just for debugging)
      try {
        const base64Url = token.split('.')[1];
        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
        const payload = JSON.parse(atob(base64));
        console.log('Token payload:', payload);
      } catch (e) {
        console.log('Could not decode token');
      }
    }
    
    // Test the endpoint
    try {
      console.log(`Making request to: /certificates${endpoint}`);
      const response = await api.get(`/certificates${endpoint}`);
      console.log('✅ Success:', response.data);
      console.groupEnd();
      return { success: true, data: response.data };
    } catch (error) {
      console.log('❌ Failed:', error.response?.status, error.response?.data || error.message);
      console.groupEnd();
      return { 
        success: false, 
        status: error.response?.status,
        error: error.response?.data || error.message 
      };
    }
  }
};

// For debugging in browser console
if (typeof window !== 'undefined') {
  window.verifierApi = verifierApi;
}