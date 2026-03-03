import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import api from '../api/axiosConfig';
import { API_URL } from '../config';

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
      const { data } = await api.get('/auth/me');
      setUser(data);
      localStorage.setItem('user', JSON.stringify(data));
    } catch (err) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCurrentUser();
  }, [fetchCurrentUser]);

  const login = async (username, password) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password);
    
    const response = await api.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });
    
    const { token, user } = response.data;
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
    setUser(user);
    return response.data;
  };

  const loginWithGoogle = async (googleToken) => {
    try {
      const response = await api.post('/auth/google/verify-token', {
        token: googleToken
      });
      const { token, user } = response.data;
      localStorage.setItem('token', token);
      localStorage.setItem('user', JSON.stringify(user));
      setUser(user);
      return response.data;
    } catch (error) {
      // Handle Google OAuth errors with specific messages
      if (error.response?.status === 403) {
        throw new Error(error.response?.data?.detail || 'Access denied. Only admin and institution emails are allowed.');
      } else if (error.response?.status === 500) {
        throw new Error('Google OAuth not configured. Please contact administrator.');
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
      return response.data;
    } catch (error) {
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    window.location.href = '/login';
  };

  return (
    <AuthContext.Provider value={{ user, loading, isAuthenticated, login, register, loginWithGoogle, logout }}>
      {children}
    </AuthContext.Provider>
  );
};
