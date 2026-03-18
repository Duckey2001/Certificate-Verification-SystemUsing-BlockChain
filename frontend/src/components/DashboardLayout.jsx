import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const DashboardLayout = ({ children, title, role }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <div className="flex-shrink-0 flex items-center">
                <div className="bg-gradient-to-r from-purple-600 to-blue-600 p-2 rounded-lg">
                  <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                  </svg>
                </div>
                <span className="ml-3 text-xl font-bold text-gray-900">CertiVert</span>
                <span className="ml-3 px-3 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                  {role?.toUpperCase()}
                </span>
              </div>
              <div className="hidden md:ml-6 md:flex md:space-x-8">
                <Link to={`/${role}`} className="text-purple-600 border-b-2 border-purple-600 inline-flex items-center px-1 pt-1 text-sm font-medium">
                  Dashboard
                </Link>
                {role === 'admin' && (
                  <>
                    <Link to="/admin/users" className="text-gray-500 hover:text-gray-700 inline-flex items-center px-1 pt-1 text-sm font-medium">
                      Users
                    </Link>
                    <Link to="/admin/invitations" className="text-gray-500 hover:text-gray-700 inline-flex items-center px-1 pt-1 text-sm font-medium">
                      Invitations
                    </Link>
                  </>
                )}
                {role === 'issuer' && (
                  <>
                    <Link to="/issuer/issue" className="text-gray-500 hover:text-gray-700 inline-flex items-center px-1 pt-1 text-sm font-medium">
                      Issue Certificate
                    </Link>
                    <Link to="/issuer/certificates" className="text-gray-500 hover:text-gray-700 inline-flex items-center px-1 pt-1 text-sm font-medium">
                      My Certificates
                    </Link>
                  </>
                )}
                {role === 'verifier' && (
                  <>
                    <Link to="/verifier/verify" className="text-gray-500 hover:text-gray-700 inline-flex items-center px-1 pt-1 text-sm font-medium">
                      Verify Certificate
                    </Link>
                    <Link to="/verifier/history" className="text-gray-500 hover:text-gray-700 inline-flex items-center px-1 pt-1 text-sm font-medium">
                      Verification History
                    </Link>
                  </>
                )}
              </div>
            </div>
            <div className="flex items-center">
              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900">{user?.username}</p>
                  <p className="text-xs text-gray-500">{user?.institution || 'No institution'}</p>
                </div>
                <button
                  onClick={handleLogout}
                  className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors text-sm"
                >
                  Logout
                </button>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">{title}</h1>
          <p className="text-gray-600 mt-2">Welcome back, {user?.username}!</p>
        </div>
        
        {children}
      </div>
    </div>
  );
};

export default DashboardLayout;
