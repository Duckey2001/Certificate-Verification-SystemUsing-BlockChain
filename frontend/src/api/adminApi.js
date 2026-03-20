// src/api/adminApi.js
import api from './axiosConfig';

export const adminApi = {
  // Get all users
  getAllUsers: async (page = 1, limit = 20, filters = {}) => {
    const { role, institution, q } = filters;
    const response = await api.get('/api/admin/users', {
      params: { page, limit, role, institution, q }
    });
    return response.data;
  },
  
  // Get pending users
  getPendingUsers: async () => {
    const response = await api.get('/api/admin/pending-users');
    return response.data;
  },
  
  // Approve or reject a user
  approveUser: async (payload) => {
    const response = await api.post('/api/admin/users/approve', payload);
    return response.data;
  },
  
  // Update user role
  updateUserRole: async (userId, role) => {
    const response = await api.put(`/api/admin/users/${userId}/role`, { role });
    return response.data;
  },
  
  // Delete user
  deleteUser: async (userId) => {
    const response = await api.delete(`/api/admin/users/${userId}`);
    return response.data;
  },
  
  // Get system statistics
  getSystemStats: async () => {
    const response = await api.get('/api/admin/stats');
    return response.data;
  },

  // Get system health
  getSystemHealth: async () => {
    const response = await api.get('/api/admin/system-health');
    return response.data;
  },

  // Get dashboard charts
  getDashboardCharts: async (dateRange = 7) => {
    const response = await api.get('/api/admin/dashboard-charts', {
      params: { days: dateRange }
    });
    return response.data;
  },

  // Get notifications
  getNotifications: async () => {
    const response = await api.get('/api/admin/notifications');
    return response.data;
  },

  // Get recent alerts
  getRecentAlerts: async () => {
    const response = await api.get('/api/admin/recent-alerts');
    return response.data;
  },

  // Mark notification as read
  markNotificationRead: async (notificationId) => {
    const response = await api.post(`/api/admin/notifications/${notificationId}/read`);
    return response.data;
  },

  // Mark all notifications as read
  markAllNotificationsRead: async () => {
    const response = await api.post('/api/admin/notifications/read-all');
    return response.data;
  },

  // Get institutions
  getInstitutions: async () => {
    const response = await api.get('/api/admin/institutions');
    return response.data;
  },

  // Export data
  exportData: async (tab, format = 'csv') => {
    const response = await api.get('/api/admin/export', {
      params: { tab, format }
    });
    return response.data;
  },
  
  // Get all certificates (admin view)
  getAllCertificates: async (page = 1, limit = 20, filters = {}) => {
    const response = await api.get('/api/admin/certificates', {
      params: { page, limit, ...filters }
    });
    return response.data;
  },
  
  // Revoke a certificate
  revokeCertificate: async (certificateId) => {
    const response = await api.post(`/api/admin/certificates/${certificateId}/revoke`);
    return response.data;
  },
  
  // Get all verifications
  getAllVerifications: async (page = 1, limit = 20, filters = {}) => {
    const response = await api.get('/api/admin/verifications', {
      params: { page, limit, ...filters }
    });
    return response.data;
  },
  
  // Get logs
  getSystemLogs: async (page = 1, limit = 50) => {
    const response = await api.get('/api/admin/logs', {
      params: { page, limit }
    });
    return response.data;
  },

  // Get all payments
  getAllPayments: async (page = 1, limit = 20, filters = {}) => {
    const response = await api.get('/api/admin/payments', {
      params: { page, limit, ...filters }
    });
    return response.data;
  }
};

export default adminApi;
