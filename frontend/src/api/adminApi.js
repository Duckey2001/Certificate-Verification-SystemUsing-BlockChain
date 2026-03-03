// src/api/adminApi.js
import api from './axiosConfig';

export const adminApi = {
  // Get all users
  getAllUsers: async (page = 1, limit = 20, filters = {}) => {
    const { role, institution, q } = filters;
    const response = await api.get('/admin/users', {
      params: { page, limit, role, institution, q }
    });
    return response.data;
  },
  
  // Get pending users
  getPendingUsers: async () => {
    const response = await api.get('/admin/pending-users');
    return response.data;
  },
  
  // Approve or reject a user
  approveUser: async (payload) => {
    const response = await api.post('/admin/users/approve', payload);
    return response.data;
  },
  
  // Update user role
  updateUserRole: async (userId, role) => {
    const response = await api.put(`/admin/users/${userId}/role`, { role });
    return response.data;
  },
  
  // Delete user
  deleteUser: async (userId) => {
    const response = await api.delete(`/admin/users/${userId}`);
    return response.data;
  },
  
  // Get system statistics
  getSystemStats: async () => {
    const response = await api.get('/admin/stats');
    return response.data;
  },
  
  // Get all certificates (admin view)
  getAllCertificates: async (page = 1, limit = 20, filters = {}) => {
    const response = await api.get('/admin/certificates', {
      params: { page, limit, ...filters }
    });
    return response.data;
  },
  
  // Revoke a certificate
  revokeCertificate: async (certificateId) => {
    const response = await api.post(`/admin/certificates/${certificateId}/revoke`);
    return response.data;
  },
  
  // Get all verifications
  getAllVerifications: async (page = 1, limit = 20, filters = {}) => {
    const response = await api.get('/admin/verifications', {
      params: { page, limit, ...filters }
    });
    return response.data;
  },
  
  // Get logs
  getSystemLogs: async (page = 1, limit = 50) => {
    const response = await api.get('/admin/logs', {
      params: { page, limit }
    });
    return response.data;
  },

  // Get all payments
  getAllPayments: async (page = 1, limit = 20, filters = {}) => {
    const response = await api.get('/admin/payments', {
      params: { page, limit, ...filters }
    });
    return response.data;
  }
};

export default adminApi;
