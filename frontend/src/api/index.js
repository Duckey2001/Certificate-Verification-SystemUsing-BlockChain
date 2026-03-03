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
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
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
    
    // Handle token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
          refresh_token: refreshToken,
        });
        
        localStorage.setItem('access_token', response.data.access_token);
        api.defaults.headers.common['Authorization'] = `Bearer ${response.data.access_token}`;
        
        return api(originalRequest);
      } catch (refreshError) {
        // Redirect to login
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  login: async (credentials) => {
    const response = await api.post('/auth/login', credentials);
    if (response.data.access_token) {
      localStorage.setItem('access_token', response.data.access_token);
      localStorage.setItem('refresh_token', response.data.refresh_token);
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
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
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
    
    const response = await api.post('/certificates/bulk-upload', formData, {
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
    if (params.status) queryParams.append('status', params.status);
    if (params.search) queryParams.append('search', params.search);
    if (params.start_date) queryParams.append('start_date', params.start_date);
    if (params.end_date) queryParams.append('end_date', params.end_date);
    
    const response = await api.get(`/certificates/my-issued?${queryParams}`);
    return response.data;
  },
  
  getMyIssuerStats: async () => {
    const response = await api.get('/certificates/issuer-stats');
    return response.data;
  },
  
  revokeCertificate: async (certificateId) => {
    const response = await api.post(`/certificates/${certificateId}/revoke`);
    return response.data;
  },
  
  // Verifier endpoints
  verifyCertificate: async (formData, onUploadProgress) => {
    const response = await api.post('/certificates/verify', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress,
    });
    return response.data;
  },
  
  getMyVerifications: async (limit = 50) => {
    const response = await api.get(`/certificates/my-verifications?limit=${limit}`);
    return response.data;
  },
  
  getMyVerifierStats: async () => {
    const response = await api.get('/certificates/verifier-stats');
    return response.data;
  },
  
  // Common endpoints
  getCertificateDetails: async (hash) => {
    const response = await api.get(`/certificates/${hash}`);
    return response.data;
  },
  
  downloadCertificate: async (hash) => {
    const response = await api.get(`/certificates/${hash}/download`, {
      responseType: 'blob',
    });
    return response.data;
  },
  
  getVerificationHistory: async (certificateId) => {
    const response = await api.get(`/certificates/${certificateId}/verifications`);
    return response.data;
  },
};

// Payment API
export const paymentApi = {
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

// Admin API
export const adminApi = {
  getSystemStats: async () => {
    const response = await api.get('/admin/system-stats');
    return response.data;
  },
  
  getUsers: async (params = {}) => {
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
};
