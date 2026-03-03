#!/bin/bash

echo "🔧 Fixing all import errors..."
echo

cd ~/Documents/Certivert\ project/frontend

# Create missing directories
echo "1. Creating missing directories..."
mkdir -p src/utils src/api src/components

# Create missing files
echo "2. Creating missing files..."

# Utils
cat > src/utils/index.js << 'UTILS_EOF'
export const createPageUrl = (path) => path;
export const formatDate = (date) => new Date(date).toLocaleDateString();
export const truncateText = (text, length = 50) => 
  text.length > length ? text.substring(0, length) + '...' : text;
UTILS_EOF

# API Client
cat > src/api/base44Client.js << 'API_EOF'
import axios from 'axios';
const api = axios.create({ baseURL: 'http://localhost:5000/api' });
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = \`Bearer \${token}\`;
  return config;
});
export const base44 = {
  certificates: {
    getAll: () => api.get('/my-certificates'),
    issue: (data) => api.post('/issue-certificate', data),
    verify: (hash) => api.post('/verify-certificate', { certificateHash: hash }),
  },
  auth: {
    login: (credentials) => api.post('/login', credentials),
    logout: () => {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
    },
  },
  blockchain: {
    getStatus: () => api.get('/blockchain-status'),
  },
};
export default api;
API_EOF

# RBAC Utils
cat > src/components/rbacUtils.js << 'RBAC_EOF'
export const getUserRoleDisplayName = (role) => {
  const roleMap = { issuer: 'Issuer', verifier: 'Verifier', admin: 'Administrator' };
  return roleMap[role] || role;
};
export const canAccessRoute = (userRole, requiredRole) => {
  const roleHierarchy = {
    admin: ['admin', 'issuer', 'verifier'],
    issuer: ['issuer', 'verifier'],
    verifier: ['verifier'],
  };
  return roleHierarchy[userRole]?.includes(requiredRole) || false;
};
RBAC_EOF

# Create missing components
echo "3. Creating missing components..."

# VerificationStatusBadge
cat > src/components/VerificationStatusBadge.jsx << 'BADGE_EOF'
import React from 'react';
const VerificationStatusBadge = ({ status }) => {
  const configs = {
    verified: { color: 'bg-green-100 text-green-800', text: 'Verified' },
    pending: { color: 'bg-yellow-100 text-yellow-800', text: 'Pending' },
  };
  const config = configs[status] || { color: 'bg-gray-100 text-gray-800', text: 'Unknown' };
  return (
    <span className={\`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium \${config.color}\`}>
      {config.text}
    </span>
  );
};
export default VerificationStatusBadge;
BADGE_EOF

# BlockchainVisualization
cat > src/components/BlockchainVisualization.jsx << 'BLOCKCHAIN_EOF'
import React from 'react';
const BlockchainVisualization = () => (
  <div className="bg-white rounded-lg shadow p-4">
    <h3 className="text-lg font-semibold mb-2">Blockchain Status</h3>
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <span className="text-gray-600">Network:</span>
        <span className="font-medium">Local (Ganache)</span>
      </div>
      <div className="flex items-center justify-between">
        <span className="text-gray-600">Status:</span>
        <span className="text-green-600 font-medium">Connected</span>
      </div>
    </div>
  </div>
);
export default BlockchainVisualization;
BLOCKCHAIN_EOF

# AIVerificationAnalysis
cat > src/components/AIVerificationAnalysis.jsx << 'AI_EOF'
import React from 'react';
const AIVerificationAnalysis = () => (
  <div className="bg-white rounded-lg shadow p-4">
    <h3 className="text-lg font-semibold mb-2">AI Verification Analysis</h3>
    <div className="space-y-2">
      <div className="flex items-center">
        <div className="w-4 h-4 bg-green-500 rounded-full mr-2"></div>
        <span>Certificate authenticity: 98%</span>
      </div>
    </div>
  </div>
);
export default AIVerificationAnalysis;
AI_EOF

# QRScanner (simplified)
cat > src/components/QRScanner.jsx << 'QR_EOF'
import React from 'react';
const QRScanner = () => (
  <div className="bg-white rounded-lg shadow p-4">
    <h3 className="text-lg font-semibold mb-2">QR Code Scanner</h3>
    <p className="text-gray-600">Scan certificate QR codes for verification</p>
  </div>
);
export default QRScanner;
QR_EOF

# Update vite.config.js
echo "4. Updating vite.config.js..."
cat > vite.config.js << 'VITE_EOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
export default defineConfig({
  plugins: [react()],
  server: { port: 3000, host: true, open: true },
  resolve: { alias: { '@': path.resolve(__dirname, './src') } }
})
VITE_EOF

# Install missing dependencies
echo "5. Installing missing dependencies..."
npm install @tanstack/react-query lucide-react --legacy-peer-deps

echo
echo "✅ All imports fixed!"
echo "🌐 Restarting frontend..."
pkill -f "vite" 2>/dev/null
sleep 2
npm start
