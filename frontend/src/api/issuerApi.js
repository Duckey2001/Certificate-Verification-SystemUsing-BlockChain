// src/api/issuerApi.js
import api from './axiosConfig';

export const issuerApi = {
  // Get issuer statistics
  getStats: async () => {
    try {
      const response = await api.get('/api/issuer/stats');
      console.log('✅ Issuer stats received:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Failed to fetch issuer stats:', error.response?.data || error.message);
      throw error;
    }
  },
  
  // Get issuer certificates
  getCertificates: async (limit = 50) => {
    try {
      const response = await api.get('/api/issuer/certificates', {
        params: { limit }
      });
      console.log(`✅ Received ${response.data?.length || 0} certificates`);
      return response.data;
    } catch (error) {
      console.error('❌ Failed to fetch certificates:', error.response?.data || error.message);
      throw error;
    }
  },
  
  // Get certificate by ID
  getCertificate: async (certificateId) => {
    try {
      const response = await api.get(`/api/certificates/${certificateId}`);
      return response.data;
    } catch (error) {
      console.error('❌ Failed to fetch certificate:', error.response?.data || error.message);
      throw error;
    }
  },
  
  // Issue new certificate
  issueCertificate: async (certificateData) => {
    try {
      const response = await api.post('/api/certificates/issue', certificateData);
      console.log('✅ Certificate issued successfully:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Failed to issue certificate:', error.response?.data || error.message);
      throw error;
    }
  },
  
  // Update certificate
  updateCertificate: async (certificateId, updateData) => {
    try {
      const response = await api.put(`/api/certificates/${certificateId}`, updateData);
      console.log('✅ Certificate updated successfully:', response.data);
      return response.data;
    } catch (error) {
      console.error('❌ Failed to update certificate:', error.response?.data || error.message);
      throw error;
    }
  },
  
  // Get issuer activity for charts
  getActivity: async (days = 7) => {
    try {
      const response = await api.get('/api/issuer/activity', {
        params: { days }
      });
      console.log('✅ Activity data received');
      return response.data;
    } catch (error) {
      console.error('❌ Failed to fetch activity data:', error.response?.data || error.message);
      throw error;
    }
  },
  
  // Get certificate statistics
  getCertificateStats: async () => {
    try {
      const response = await api.get('/api/issuer/certificate-stats');
      return response.data;
    } catch (error) {
      console.error('❌ Failed to fetch certificate stats:', error.response?.data || error.message);
      throw error;
    }
  },
  
  // Get recent issuances
  getRecentIssuances: async (limit = 10) => {
    try {
      const response = await api.get('/api/issuer/recent-issuances', {
        params: { limit }
      });
      console.log(`✅ Received ${response.data?.length || 0} recent issuances`);
      return response.data;
    } catch (error) {
      console.error('❌ Failed to fetch recent issuances:', error.response?.data || error.message);
      throw error;
    }
  }
};

export default issuerApi;
