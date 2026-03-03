import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const PrivateRoute = ({ children, allowedRoles }) => {
  const { user, loading, isAuthenticated } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && !allowedRoles.includes(user?.role)) {
    // If logged in but not allowed here, send them to their own dashboard
    return <Navigate to="/dashboard" replace />;
  }

  // Redirect based on role after login
  if (location.pathname === '/dashboard' || location.pathname === '/') {
    switch (user?.role) {
      case 'admin':
        return <Navigate to="/admin" replace />;
      case 'issuer':
        return <Navigate to="/issuer" replace />;
      case 'verifier':
        return <Navigate to="/verifier" replace />;
      default:
        return <Navigate to="/" replace />;
    }
  }

  return children;
};

export default PrivateRoute;
