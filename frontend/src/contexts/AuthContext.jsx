import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import api from '../api/axiosConfig';

const AuthContext = createContext({});
export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const isAuthenticated = !!user;

  const fetchCurrentUser = useCallback(async () => {
    const token = localStorage.getItem('token');
    
    if (!token) {
      setLoading(false);
      return;
    }
    
    try {
      // Set the token in the default headers for all requests
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      
      const { data } = await api.get('/auth/me');
      
      setUser(data.user || data);
      localStorage.setItem('user', JSON.stringify(data));
    } catch (err) {
      console.error('Error fetching user:', err.response?.data?.message || err.message);
      
      // If token is invalid, clear storage
      if (err.response?.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        delete api.defaults.headers.common['Authorization'];
        setUser(null);
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCurrentUser();
  }, [fetchCurrentUser]);

  const login = async (username, password) => {
    try {
      const response = await api.post('/auth/login', {
        username: username,
        password: password
      }, {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      // Your backend returns { access_token, user }
      const { access_token, user } = response.data;
      
      // Store token in localStorage
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(user));
      
      // Set token in axios defaults for all future requests
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      setUser(user);
      
      return response.data;
    } catch (error) {
      console.error('Login error:', error.response?.data?.message || error.message);
      throw error;
    }
  };

  const loginWithGoogle = async (googleToken) => {
    try {
      const response = await api.post('/auth/google/verify-token', {
        token: googleToken
      });
      
      // Handle both possible response formats
      const token = response.data.token || response.data.access_token;
      const user = response.data.user;
      
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(user));
      
      api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      setUser(user);
      
      return response.data;
    } catch (error) {
      if (error.response?.status === 403) {
        throw new Error(error.response?.data?.detail || 'Access denied. Only admin and institution emails are allowed.');
      } else if (error.response?.status === 500) {
        throw new Error('Google OAuth not configured. Please contact administrator.');
      } else if (error.response?.status === 404) {
        throw new Error('Google login endpoint not configured on server.');
      } else {
        throw new Error('Google sign-in failed. Please try again.');
      }
    }
  };
  
  const register = async (userData, inviteToken = null) => {
    try {
      const url = inviteToken
        ? `/auth/register/invite/${inviteToken}`
        : '/auth/register';
      
      const payload = inviteToken
        ? { username: userData.username, password: userData.password }
        : userData;
      
      const response = await api.post(url, payload);
      
      // Handle both possible response formats
      const token = response.data.token || response.data.access_token;
      const user = response.data.user;
      
      if (token) {
        localStorage.setItem('token', token);
        localStorage.setItem('user', JSON.stringify(user));
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        setUser(user);
      }
      
      return response.data;
    } catch (error) {
      console.error('Registration error:', error.response?.data?.message || error.message);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    delete api.defaults.headers.common['Authorization'];
    setUser(null);
    window.location.href = '/login';
  };

  const value = {
    user,
    loading,
    isAuthenticated,
    login,
    register,
    loginWithGoogle,
    logout
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};