import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import LandingPage from './pages/LandingPage';
import Login from './pages/Login';
import Register from './pages/Register';
import Demo from './pages/Demo';
import Contact from './pages/Contact';
import OCRProcessor from './pages/OCRProcessor';
import MpesaPayment from './pages/MpesaPayment';
import VerifyCertificate from './pages/VerifyCertificate';
import AdminDashboard from './pages/dashboard/AdminDashboard';
import IssuerDashboard from './pages/dashboard/IssuerDashboard';
import VerifierDashboard from './pages/dashboard/VerifierDashboard';
import PrivateRoute from './components/PrivateRoute';
import './App.css';

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
      <Router future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}>
        <div className="App min-h-screen bg-gray-50">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/demo" element={<Demo />} />
            <Route path="/contact" element={<Contact />} />
            <Route path="/ocr" element={<OCRProcessor />} />
            <Route path="/mpesa" element={<MpesaPayment />} />
            <Route path="/verify" element={<VerifyCertificate />} />

            {/* Dashboard redirect (role-based) */}
            <Route
              path="/dashboard"
              element={
                <PrivateRoute>
                  <div />
                </PrivateRoute>
              }
            />
            
            {/* Protected Routes */}
            <Route path="/admin/*" element={
              <PrivateRoute allowedRoles={['admin']}>
                <AdminDashboard />
              </PrivateRoute>
            } />
            
            <Route path="/issuer/*" element={
              <PrivateRoute allowedRoles={['issuer', 'admin']}>
                <IssuerDashboard />
              </PrivateRoute>
            } />
            
            <Route path="/verifier/*" element={
              <PrivateRoute allowedRoles={['verifier', 'admin']}>
                <VerifierDashboard />
              </PrivateRoute>
            } />
            
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </Router>
    </AuthProvider>
  </ThemeProvider>
  );
}

export default App;
