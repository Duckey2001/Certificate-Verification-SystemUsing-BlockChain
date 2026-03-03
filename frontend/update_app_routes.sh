#!/bin/bash

cd ~/lgcse-project/frontend

# Update App.jsx to include new components
cat > src/App.jsx << 'APP_EOF'
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import PrivateRoute from './components/PrivateRoute';
import DashboardLayout from './components/DashboardLayout';

// Pages
import LandingPage from './pages/LandingPage';
import Login from './pages/Login';
import Register from './pages/Register';
import JoinNetwork from './pages/JoinNetwork';
import JoinConfirmation from './pages/JoinConfirmation';

// Dashboard Pages
import AdminDashboard from './pages/dashboard/AdminDashboard';
import IssuerDashboard from './pages/dashboard/IssuerDashboard';
import VerifierDashboard from './pages/dashboard/VerifierDashboard';
import InstitutionDashboard from './components/InstitutionManagement/InstitutionDashboard';

// New Components
import HostedPeerDashboard from './components/HostedPeerDashboard';
import BYOPeerGuide from './components/BYOPeerGuide';
import FabricConfigManager from './components/FabricConfigManager';

import './App.css';

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          {/* Public Routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/invite/:token" element={<Register />} />
          <Route path="/join-network" element={<JoinNetwork />} />
          <Route path="/join-confirmation" element={<JoinConfirmation />} />
          <Route path="/byo-peer-guide" element={<BYOPeerGuide />} />

          {/* Protected Routes */}
          <Route path="/dashboard" element={
            <PrivateRoute>
              <DashboardLayout />
            </PrivateRoute>
          }>
            <Route index element={<Navigate to="overview" />} />
            <Route path="overview" element={<div>Overview Dashboard</div>} />
            <Route path="admin" element={<AdminDashboard />} />
            <Route path="issuer" element={<IssuerDashboard />} />
            <Route path="verifier" element={<VerifierDashboard />} />
            <Route path="institutions" element={<InstitutionDashboard />} />
            <Route path="hosted-peers" element={<HostedPeerDashboard />} />
            <Route path="fabric-config" element={<FabricConfigManager />} />
            <Route path="profile" element={<div>Profile</div>} />
            <Route path="settings" element={<div>Settings</div>} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </AuthProvider>
    </Router>
  );
}

export default App;
APP_EOF

echo "✅ App.jsx updated with new routes!"
