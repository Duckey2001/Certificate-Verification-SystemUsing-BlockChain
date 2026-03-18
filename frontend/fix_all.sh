#!/bin/bash

cd ~/lgcse-project/frontend

echo "1. Fixing AuthContext.jsx..."
cat > src/contexts/AuthContext.jsx << 'AUTH_EOF'
import React, { createContext, useState, useContext, useEffect, useCallback } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:8000';
const AuthContext = createContext({});
export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [invitationBadge, setInvitationBadge] = useState(0);

  const fetchCurrentUser = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      if (token) {
        const userData = localStorage.getItem('user');
        if (userData) {
          setUser(JSON.parse(userData));
          const userObj = JSON.parse(userData);
          if (userObj.role === 'issuer' || userObj.role === 'admin') {
            try {
              const response = await axios.get(\`\${API_URL}/api/users/\${userObj.id}/invitations/stats\`, {
                headers: { Authorization: \`Bearer \${token}\` }
              });
              setInvitationBadge(response.data.invitedCount || 0);
            } catch (error) {
              console.error('Error fetching invitation stats:', error);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error in fetchCurrentUser:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCurrentUser();
  }, [fetchCurrentUser]);

  const login = async (credentials) => {
    const response = await axios.post(\`\${API_URL}/api/auth/login\`, credentials);
    const { token, user } = response.data;
    localStorage.setItem('token', token);
    localStorage.setItem('user', JSON.stringify(user));
    setUser(user);
    return response.data;
  };

  const register = async (userData) => {
    const response = await axios.post(\`\${API_URL}/api/auth/register\`, userData);
    return response.data;
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    window.location.href = '/login';
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, invitationBadge }}>
      {children}
    </AuthContext.Provider>
  );
};
AUTH_EOF

echo "2. Installing Tailwind CSS v4..."
npm install -D @tailwindcss/postcss

echo "3. Updating configuration files..."
cat > postcss.config.js << 'POSTCSS_EOF'
module.exports = {
  plugins: {
    '@tailwindcss/postcss': {},
    autoprefixer: {},
  },
}
POSTCSS_EOF

echo "4. Cleaning up CSS files..."
cat > src/index.css << 'CSS_EOF'
@import 'tailwindcss';
CSS_EOF

cat > src/App.css << 'APPCSS_EOF'
/* Empty for now */
APPCSS_EOF

echo "5. Creating .env file..."
cat > .env << 'ENV_EOF'
REACT_APP_API_URL=http://localhost:8000
DISABLE_ESLINT_PLUGIN=true
ENV_EOF

echo "✅ All fixes applied. Starting app..."
npm start
