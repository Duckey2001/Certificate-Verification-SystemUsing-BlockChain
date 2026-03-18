// src/api/authApi.js
import api from './axiosConfig';

export const authApi = {
  // Login user
  login: async (credentials) => {
    const response = await api.post('/auth/login', credentials);
    if (response.data.token) {
      localStorage.setItem('token', response.data.token);
      localStorage.setItem('user', JSON.stringify(response.data.user));
    }
    return response.data;
  },
  
  // Register new user
  register: async (userData) => {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },
  
  // Register with invitation token
  registerWithInvitation: async (userData, token) => {
    const response = await api.post(`/auth/register/invite/${token}`, userData);
    return response.data;
  },
  
  // Get current user info
  getCurrentUser: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
  
  // Logout
  logout: async () => {
    const response = await api.post('/auth/logout');
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    return response.data;
  },
  
  // Generate invitation link (admin/issuer only)
  generateInvitation: async (inviteData) => {
    const response = await api.post('/auth/invite/generate', inviteData);
    return response.data;
  },
  
  // Validate invitation token
  validateInvitation: async (token) => {
    const response = await api.get(`/auth/invite/validate/${token}`);
    return response.data;
  },
  
  // Get user's invitation stats
  getInvitationStats: async (userId) => {
    const response = await api.get(`/users/${userId}/invitations/stats`);
    return response.data;
  },
  
  // Get all invitations (admin only)
  getAllInvitations: async () => {
    const response = await api.get('/auth/invite/all');
    return response.data;
  }
};

export default authApi;
