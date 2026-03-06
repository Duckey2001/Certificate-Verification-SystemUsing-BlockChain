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
    console.log('Token from localStorage:', token ? 'exists' : 'not found');
    
    if (!token) {
      console.log('No token found, setting loading to false');
      setLoading(false);
      return;
    }
    
    try {
      console.log('Fetching user from /auth/me...');
      console.log('API baseURL:', api.defaults.baseURL);
      
      const { data } = await api.get('/auth/me');
      console.log('User data received:', data);
      
      setUser(data);
      localStorage.setItem('user', JSON.stringify(data));
    } catch (err) {
      console.error('Error fetching user:', err);
      console.error('Error response:', err.response);
      console.error('Error config:', err.config);
      
      // If token is invalid, clear storage
      if (err.response?.status === 401) {
        console.log('Token invalid, clearing storage');
        localStorage.removeItem('token');
        localStorage.removeItem('user');
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
      console.log('Logging in with username:', username);
      
      const response = await api.post('/auth/login', {
        username: username,
        password: password
      }, {
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      console.log('Login response:', response.data);
      
      const { access_token, user } = response.data;
      
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(user));
      setUser(user);
      
      return response.data;
    } catch (error) {
      console.error('Login error:', error);
      console.error('Error response:', error.response);
      throw error;
    }
  };

  const loginWithGoogle = async (googleToken) => {
    try {
      const response = await api.post('/auth/google/verify-token', {
        token: googleToken
      });
      
      const { access_token, user } = response.data;
      
      localStorage.setItem('token', access_token);
      localStorage.setItem('user', JSON.stringify(user));
      setUser(user);
      
      return response.data;
    } catch (error) {
      console.error('Google login error:', error);
      
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
      
      const { access_token, user } = response.data;
      
      if (access_token) {
        localStorage.setItem('token', access_token);
        localStorage.setItem('user', JSON.stringify(user));
        setUser(user);
      }
      
      return response.data;
    } catch (error) {
      console.error('Registration error:', error);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
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