// src/api/index.js
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    // FIX: Use 'token' not 'access_token' to match your backend
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
      console.log(`🔑 Token attached to ${config.url}`);
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // Handle token refresh - FIX: Use 'token' not 'access_token'
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        // FIX: Update endpoint to match your backend
        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });
        
        // FIX: Use 'token' not 'access_token'
        localStorage.setItem('token', response.data.token);
        api.defaults.headers.common['Authorization'] = `Bearer ${response.data.token}`;
        
        return api(originalRequest);
      } catch (refreshError) {
        // Redirect to login
        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

// Make api available globally for debugging
if (typeof window !== 'undefined') {
  window.api = api;
}

// Auth API
export const authApi = {
  login: async (credentials) => {
    const response = await api.post('/auth/login', credentials);
    // FIX: Use 'token' not 'access_token' from response
    if (response.data.token) {
      localStorage.setItem('token', response.data.token);
      if (response.data.refresh_token) {
        localStorage.setItem('refresh_token', response.data.refresh_token);
      }
      localStorage.setItem('user', JSON.stringify(response.data.user));
    }
    return response.data;
  },
  
  register: async (userData) => {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },
  
  logout: async () => {
    try {
      await api.post('/auth/logout');
    } finally {
      localStorage.removeItem('token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
    }
  },
  
  refreshToken: async (refreshToken) => {
    const response = await api.post('/auth/refresh', { refresh_token: refreshToken });
    return response.data;
  },
  
  verifyEmail: async (token) => {
    const response = await api.post('/auth/verify-email', { token });
    return response.data;
  },
  
  requestPasswordReset: async (email) => {
    const response = await api.post('/auth/request-password-reset', { email });
    return response.data;
  },
  
  resetPassword: async (token, newPassword) => {
    const response = await api.post('/auth/reset-password', { token, new_password: newPassword });
    return response.data;
  },
  
  generateInvitation: async (invitationData) => {
    const response = await api.post('/auth/invite', invitationData);
    return response.data;
  },
  
  getAllInvitations: async () => {
    const response = await api.get('/auth/invitations');
    return response.data;
  },
  
  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
};

// User API
export const userApi = {
  getProfile: async () => {
    const response = await api.get('/users/profile');
    return response.data;
  },
  
  updateProfile: async (profileData) => {
    const response = await api.put('/users/profile', profileData);
    return response.data;
  },
  
  changePassword: async (passwordData) => {
    const response = await api.post('/users/change-password', passwordData);
    return response.data;
  },
  
  updatePreferences: async (preferences) => {
    const response = await api.put('/users/preferences', preferences);
    return response.data;
  },
  
  getNotifications: async () => {
    const response = await api.get('/users/notifications');
    return response.data;
  },
  
  markNotificationRead: async (notificationId) => {
    const response = await api.post(`/users/notifications/${notificationId}/read`);
    return response.data;
  },
};

// Certificate API
export const certificateApi = {
  // Issuer endpoints
  issueCertificate: async (formData) => {
    const response = await api.post('/certificates/issue', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  
  uploadCertificatesBulk: async (files, onUploadProgress) => {
    const formData = new FormData();
    files.forEach(file => {
      formData.append('files', file);
    });
    
    const response = await api.post('/certificates/upload-bulk', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress,
    });
    return response.data;
  },
  
  getMyIssuerCertificates: async (params = {}) => {
    const queryParams = new URLSearchParams();
    if (params.limit) queryParams.append('limit', params.limit);
    
    const response = await api.get(`/api/issuer/certificates?${queryParams}`);
    return response.data;
  },
  
  getMyIssuerStats: async () => {
    const response = await api.get('/api/issuer/stats');
    return response.data;
  },
  
  revokeCertificate: async (certificateId) => {
    const response = await api.post(`/certificates/${certificateId}/revoke`);
    return response.data;
  },
  
  // Verifier endpoints - FIX: Match your backend paths
  verifyCertificate: async (formData, onUploadProgress) => {
    const response = await api.post('/certificates/verify', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress,
    });
    return response.data;
  },
  
  getMyVerifications: async (params = {}) => {
    const queryParams = new URLSearchParams();
    if (params.limit) queryParams.append('limit', params.limit);
    if (params.start_date) queryParams.append('start_date', params.start_date);
    if (params.end_date) queryParams.append('end_date', params.end_date);
    
    const response = await api.get(`/api/verifier/my-verifications?${queryParams}`);
    return response.data;
  },
  
  getPendingVerifications: async (limit = 10) => {
    const response = await api.get('/certificates/pending-verifications', {
      params: { limit }
    });
    return response.data;
  },
  
  getRecentVerifications: async (limit = 5) => {
    const response = await api.get('/certificates/recent-verifications', {
      params: { limit }
    });
    return response.data;
  },
  
  getVerificationDetails: async (id) => {
    const response = await api.get(`/certificates/verification-details/${id}`);
    return response.data;
  },
  
  processVerification: async (id, action, notes = '') => {
    const formData = new FormData();
    formData.append('action', action);
    formData.append('notes', notes);
    
    const response = await api.post(`/certificates/process-verification/${id}`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  
  // Missing verifier-specific endpoints
  getInstitutions: async () => {
    // Mock institutions data - can be enhanced to fetch from database
    return [
      { id: 1, name: 'Ministry of Education', code: 'MOE' },
      { id: 2, name: 'Examination Council', code: 'ECOL' }
    ];
  },

  getCertificateTypes: async () => {
    // Mock certificate types - can be enhanced to fetch from database
    return [
      { id: 'LGCSE', name: 'LGCSE' },
      { id: 'COSC', name: 'COSC' }
    ];
  },

  // Fix the verifier stats endpoint path
  getMyVerifierStats: async () => {
    const response = await api.get('/api/verifier/stats');
    return response.data;
  },
  
  getVerifierActivity: async (days = 7) => {
    // Use the verifications endpoint as activity data
    const response = await api.get('/verifier/verifications', {
      params: { limit: days * 10 }
    });
    return response.data;
  },
  
  // Common endpoints
  getCertificateByHash: async (hash) => {
    const response = await api.get(`/certificates/${hash}`);
    return response.data;
  },
  
  searchCertificates: async (query) => {
    const response = await api.get('/certificates/search', {
      params: { q: query }
    });
    return response.data;
  },
  
  listCertificates: async (skip = 0, limit = 100) => {
    const response = await api.get('/certificates/', {
      params: { skip, limit }
    });
    return response.data;
  },
  
  getVerificationResult: async (verificationId) => {
    const response = await api.get(`/certificates/verify/result/${verificationId}`);
    return response.data;
  },
  
  // Missing issuer-specific endpoints
  getMyIssuerStats: async (dateRange = 7) => {
    const response = await api.get('/certificates/issuer/stats', {
      params: { days: dateRange }
    });
    return response.data;
  },

  getIssuanceTrend: async (dateRange = 7) => {
    const response = await api.get('/certificates/issuer/trend', {
      params: { days: dateRange }
    });
    return response.data;
  },

  getStatusDistribution: async () => {
    const response = await api.get('/certificates/issuer/status-distribution');
    return response.data;
  },

  getMonthlyComparison: async () => {
    const response = await api.get('/certificates/issuer/monthly-comparison');
    return response.data;
  },

  getVerificationHistory: async () => {
    const response = await api.get('/certificates/issuer/verification-history');
    return response.data;
  },

  exportCertificates: async (params) => {
    const response = await api.get('/certificates/issuer/export', { params });
    return response.data;
  },

  // Alias for upload to match issuer dashboard usage
  upload: async (formData) => {
    return await certificateApi.uploadCertificate(formData);
  },

  verify: async (formData, onProgress) => {
    return await certificateApi.verifyCertificate(formData, onProgress);
  },
  
  extractCertificateData: async (formData) => {
    const response = await api.post('/certificates/extract-data', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  
  getOcrHistory: async () => {
    const response = await api.get('/certificates/ocr-history');
    return response.data;
  },
  
  getNotifications: async () => {
    const response = await api.get('/api/activities/recent');
    return response.data;
  },
  
  getVerificationChartData: async (dateRange) => {
    const params = {};
    if (dateRange?.start) params.start_date = dateRange.start;
    if (dateRange?.end) params.end_date = dateRange.end;
    
    const response = await api.get('/api/activities/stats', { params });
    return response.data;
  },
  
  markNotificationRead: async (notificationId) => {
    const response = await api.post(`/admin/notifications/${notificationId}/read`);
    return response.data;
  },
  
  exportVerifications: async (params) => {
    const response = await api.get('/admin/export', { params });
    return response.data;
  },
  
  // Debug endpoints
  testAuth: async () => {
    const response = await api.get('/certificates/test-auth');
    return response.data;
  },
  
  debugCertificates: async () => {
    const response = await api.get('/certificates/debug');
    return response.data;
  },
};

// Payment API
export const paymentApi = {
  getMyPayments: async () => {
    const response = await api.get('/payments/my');
    return response.data;
  },
  
  getVerifierPaymentStats: async (dateRange) => {
    const params = {};
    if (dateRange?.start) params.start_date = dateRange.start;
    if (dateRange?.end) params.end_date = dateRange.end;
    
    const response = await api.get('/payments/stats', { params });
    return response.data;
  },
  
  checkPaymentRequired: async () => {
    const response = await api.get('/payments/check-required');
    return response.data;
  },
  
  processPayment: async (paymentData) => {
    const response = await api.post('/payments/process', paymentData);
    return response.data;
  },
  
  getPaymentMethods: async () => {
    const response = await api.get('/payments/methods');
    return response.data;
  },
  
  verifyPayment: async (reference) => {
    const response = await api.get(`/payments/verify/${reference}`);
    return response.data;
  },
  
  getTransactionHistory: async (params = {}) => {
    const response = await api.get('/payments/history', { params });
    return response.data;
  },
  
  getPaymentStats: async () => {
    const response = await api.get('/payments/stats');
    return response.data;
  },
  
  requestRefund: async (transactionId, reason) => {
    const response = await api.post(`/payments/${transactionId}/refund`, { reason });
    return response.data;
  },
};

// Institution API
export const institutionApi = {
  getMyInstitution: async () => {
    const response = await api.get('/api/institutions/my');
    return response.data;
  },
  
  getInstitutionInfo: async (institutionId) => {
    const response = await api.get(`/institutions/${institutionId}`);
    return response.data;
  },
  
  updateInstitution: async (institutionId, data) => {
    const response = await api.put(`/institutions/${institutionId}`, data);
    return response.data;
  },
  
  getInstitutionStats: async (institutionId) => {
    const response = await api.get(`/institutions/${institutionId}/stats`);
    return response.data;
  },
  
  getCredits: async (institutionId) => {
    const response = await api.get(`/institutions/${institutionId}/credits`);
    return response.data;
  },
  
  purchaseCredits: async (institutionId, amount) => {
    const response = await api.post(`/institutions/${institutionId}/credits/purchase`, { amount });
    return response.data;
  },
  
  getInstitutionCertificates: async (institutionId, params = {}) => {
    const response = await api.get(`/institutions/${institutionId}/certificates`, { params });
    return response.data;
  },
  
  getInstitutionVerifiers: async (institutionId) => {
    const response = await api.get(`/institutions/${institutionId}/verifiers`);
    return response.data;
  },
  
  addVerifier: async (institutionId, verifierData) => {
    const response = await api.post(`/institutions/${institutionId}/verifiers`, verifierData);
    return response.data;
  },
  
  removeVerifier: async (institutionId, verifierId) => {
    const response = await api.delete(`/institutions/${institutionId}/verifiers/${verifierId}`);
    return response.data;
  },
};

// Admin API - Updated to match backend dashboard endpoints
export const adminApi = {
  getSystemStats: async () => {
    const response = await api.get('/api/admin/stats');
    return response.data;
  },
  
  getSystemHealth: async () => {
    // Mock system health for now - can be implemented later
    return {
      status: 'healthy',
      database: 'connected',
      blockchain: 'connected',
      services: 'operational'
    };
  },
  
  getDashboardCharts: async (dateRange) => {
    // Get comprehensive chart data from backend
    const params = {};
    if (dateRange?.start) params.start_date = dateRange.start;
    if (dateRange?.end) params.end_date = dateRange.end;
    
    const response = await api.get('/api/admin/system-stats', { params });
    return response.data;
  },
  
  getRecentAlerts: async () => {
    const response = await api.get('/api/admin/audit-events', { params: { limit: 10 } });
    return response.data.map(event => ({
      id: event.id,
      message: `${event.event_type} by ${event.actor_role}`,
      severity: event.event_type.includes('error') ? 'high' : event.event_type.includes('login') ? 'medium' : 'low',
      timestamp: event.created_at,
      type: event.event_type
    }));
  },
  
  getNotifications: async () => {
    const response = await api.get('/api/admin/audit-events', { params: { limit: 20 } });
    return response.data.map((event, index) => ({
      id: event.id,
      title: `System Activity: ${event.event_type}`,
      message: `${event.actor_role || 'User'} performed ${event.event_type}`,
      read: false,
      created_at: event.created_at,
      type: event.event_type
    }));
  },
  
  getPendingUsers: async () => {
    const response = await api.get('/api/admin/pending-users');
    return response.data.pending_users || [];
  },
  
  markNotificationRead: async (notificationId) => {
    // Mock implementation for now
    return { success: true };
  },
  
  markAllNotificationsRead: async () => {
    // Mock implementation for now
    return { success: true };
  },
  
  revokeCertificate: async (certificateId) => {
    const response = await api.post(`/api/admin/certificates/${certificateId}/revoke`);
    return response.data;
  },
  
  // Original admin endpoints (keep for backward compatibility)
  getAllUsers: async (page = 1, limit = 20, filters = {}) => {
    const params = { page, limit, ...filters };
    const response = await api.get('/admin/users', { params });
    return response.data;
  },
  
  getUserDetails: async (userId) => {
    const response = await api.get(`/admin/users/${userId}`);
    return response.data;
  },
  
  updateUserRole: async (userId, role) => {
    const response = await api.put(`/admin/users/${userId}/role`, { role });
    return response.data;
  },
  
  suspendUser: async (userId, reason) => {
    const response = await api.post(`/admin/users/${userId}/suspend`, { reason });
    return response.data;
  },
  
  activateUser: async (userId) => {
    const response = await api.post(`/admin/users/${userId}/activate`);
    return response.data;
  },
  
  deleteUser: async (userId) => {
    const response = await api.delete(`/admin/users/${userId}`);
    return response.data;
  },
  
  getAllCertificates: async (page = 1, limit = 20, filters = {}) => {
    const params = { page, limit, ...filters };
    const response = await api.get('/admin/certificates', { params });
    return response.data;
  },
  
  getAllVerifications: async (page = 1, limit = 20, filters = {}) => {
    const params = { page, limit, ...filters };
    const response = await api.get('/admin/verifications', { params });
    return response.data;
  },
  
  getAllPayments: async (page = 1, limit = 20, filters = {}) => {
    const params = { page, limit, ...filters };
    const response = await api.get('/admin/payments', { params });
    return response.data;
  },
  
  getSystemLogs: async (page = 1, limit = 50) => {
    const params = { page, limit };
    const response = await api.get('/admin/system-logs', { params });
    return response.data;
  },
  
  getInstitutions: async (params = {}) => {
    const response = await api.get('/admin/institutions', { params });
    return response.data;
  },
  
  getInstitutionDetails: async (institutionId) => {
    const response = await api.get(`/admin/institutions/${institutionId}`);
    return response.data;
  },
  
  approveInstitution: async (institutionId) => {
    const response = await api.post(`/admin/institutions/${institutionId}/approve`);
    return response.data;
  },
  
  rejectInstitution: async (institutionId, reason) => {
    const response = await api.post(`/admin/institutions/${institutionId}/reject`, { reason });
    return response.data;
  },
  
  getSystemSettings: async () => {
    const response = await api.get('/admin/settings');
    return response.data;
  },
  
  updateSystemSettings: async (settings) => {
    const response = await api.put('/admin/settings', settings);
    return response.data;
  },
  
  getAuditLogs: async (params = {}) => {
    const response = await api.get('/admin/audit-logs', { params });
    return response.data;
  },
  
  getDashboardMetrics: async () => {
    const response = await api.get('/admin/dashboard-metrics');
    return response.data;
  },
  
  sendSystemNotification: async (notification) => {
    const response = await api.post('/admin/notifications', notification);
    return response.data;
  },
};

// Blockchain API
export const blockchainApi = {
  getStatus: async () => {
    const response = await api.get('/blockchain/status');
    return response.data;
  },
  
  getTransaction: async (txId) => {
    const response = await api.get(`/blockchain/transaction/${txId}`);
    return response.data;
  },
  
  getBlock: async (blockNumber) => {
    const response = await api.get(`/blockchain/block/${blockNumber}`);
    return response.data;
  },
  
  verifyBlockchainProof: async (certificateHash) => {
    const response = await api.get(`/blockchain/verify/${certificateHash}`);
    return response.data;
  },
  
  getNetworkStats: async () => {
    const response = await api.get('/blockchain/network-stats');
    return response.data;
  },
};

// OCR API
export const ocrApi = {
  extractCertificateData: async (formData) => {
    const response = await api.post('/certificates/extract-data', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
  
  getOcrStatus: async () => {
    const response = await api.get('/ocr/status');
    return response.data;
  },
  
  processCertificate: async (formData) => {
    const response = await api.post('/ocr/process', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};

// Analytics API
export const analyticsApi = {
  getDashboardStats: async (userType) => {
    const response = await api.get(`/analytics/dashboard/${userType}`);
    return response.data;
  },
  
  getVerificationTrends: async (period = 'month') => {
    const response = await api.get(`/analytics/verification-trends?period=${period}`);
    return response.data;
  },
  
  getIssuerPerformance: async (institutionId, period = 'month') => {
    const response = await api.get(`/analytics/issuer-performance/${institutionId}?period=${period}`);
    return response.data;
  },
  
  getPaymentAnalytics: async (period = 'month') => {
    const response = await api.get(`/analytics/payments?period=${period}`);
    return response.data;
  },
};

// Activity API
export const activityApi = {
  getRecentActivity: async (limit = 10) => {
    const response = await api.get(`/activity/recent?limit=${limit}`);
    return response.data;
  },
  
  getUserActivity: async (userId, params = {}) => {
    const response = await api.get(`/activity/user/${userId}`, { params });
    return response.data;
  },
  
  getSystemLogs: async (params = {}) => {
    const response = await api.get('/activity/system-logs', { params });
    return response.data;
  },
};

// For backward compatibility with verifierApi
export const verifierApi = {
  getStats: certificateApi.getMyVerifierStats,
  getMyVerifications: certificateApi.getMyVerifications,
  getPendingVerifications: certificateApi.getPendingVerifications,
  getRecentVerifications: certificateApi.getRecentVerifications,
  getVerificationDetails: certificateApi.getVerificationDetails,
  processVerification: certificateApi.processVerification,
  getActivity: certificateApi.getVerifierActivity,
  testAuth: certificateApi.testAuth,
};

// Make verifierApi available globally
if (typeof window !== 'undefined') {
  window.verifierApi = verifierApi;
}

// Export all APIs
export default {
  auth: authApi,
  user: userApi,
  certificate: certificateApi,
  payment: paymentApi,
  institution: institutionApi,
  admin: adminApi,
  blockchain: blockchainApi,
  analytics: analyticsApi,
  activity: activityApi,
  verifier: verifierApi,
  ocr: ocrApi,
};

// Export individual APIs for direct import
export { issuerApi } from './issuerApi';