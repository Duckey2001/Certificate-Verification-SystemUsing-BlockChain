// src/api/axiosConfig.js
import axios from 'axios';
import { API_BASE } from '../config';

// Create axios instance with base URL
const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Important for sessions/cookies
});

// Add request interceptor to attach auth token
api.interceptors.request.use(
  (config) => {
    // Debug log for requests
    if (process.env.NODE_ENV === 'development') {
      console.log('🔍 API Request:', {
        url: config.url,
        method: config.method,
        baseURL: config.baseURL,
        fullURL: config.baseURL + config.url
      });
    }
    
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for debugging and error handling
api.interceptors.response.use(
  (response) => {
    // Debug log for successful responses
    if (process.env.NODE_ENV === 'development') {
      console.log('✅ API Success:', {
        url: response.config.url,
        method: response.config.method,
        status: response.status,
        data: response.data
      });
    }
    return response;
  },
  (error) => {
    // Debug log for errors
    if (process.env.NODE_ENV === 'development') {
      console.error('❌ API Error:', {
        url: error.config?.url,
        method: error.config?.method,
        baseURL: error.config?.baseURL,
        fullURL: error.config?.baseURL + error.config?.url,
        status: error.response?.status,
        error: error.response?.data || error.message
      });
    }
    
    // Handle specific error cases
    if (error.response?.status === 401) {
      // Unauthorized - clear token and redirect to login
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      window.location.href = '/login';
    }
    
    if (error.response?.status === 403) {
      // Forbidden - show access denied message
      console.error('Access denied. Insufficient permissions.');
    }
    
    return Promise.reject(error);
  }
);

// Helper function for file uploads (multipart/form-data)
api.upload = async (url, formData, config = {}) => {
  return api.post(url, formData, {
    ...config,
    headers: {
      ...config.headers,
      'Content-Type': 'multipart/form-data',
    },
  });
};

// Helper function for debugging (manual)
api.debugRequest = async (config) => {
  console.group('🔍 Manual API Debug');
  console.log('Request Config:', config);
  try {
    const response = await api(config);
    console.log('Response:', response.data);
    console.groupEnd();
    return response;
  } catch (error) {
    console.error('Error:', error.response?.data || error.message);
    console.groupEnd();
    throw error;
  }
};

export default api;
