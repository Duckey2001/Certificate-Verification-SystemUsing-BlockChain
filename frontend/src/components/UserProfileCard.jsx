import React from 'react';

const UserProfileCard = ({ user, onEdit, onLogout }) => {
  const getInitials = (name) => {
    if (!name) return 'U';
    return name.charAt(0).toUpperCase();
  };

  const getRoleBadgeColor = (role) => {
    switch(role?.toLowerCase()) {
      case 'admin':
        return 'bg-purple-100 text-purple-800';
      case 'issuer':
        return 'bg-blue-100 text-blue-800';
      case 'verifier':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center space-x-4">
        {/* Avatar */}
        <div className="flex-shrink-0">
          <div className="h-16 w-16 rounded-full bg-blue-500 flex items-center justify-center">
            <span className="text-2xl font-bold text-white">
              {getInitials(user?.username)}
            </span>
          </div>
        </div>

        {/* User Info */}
        <div className="flex-1 min-w-0">
          <p className="text-lg font-semibold text-gray-900 truncate">
            {user?.username}
          </p>
          <p className="text-sm text-gray-500 truncate">
            {user?.email || 'No email provided'}
          </p>
          <div className="flex items-center mt-2 space-x-2">
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRoleBadgeColor(user?.role)}`}>
              {user?.role?.toUpperCase() || 'USER'}
            </span>
            {user?.institution && (
              <span className="px-2 py-1 bg-gray-100 text-gray-800 rounded-full text-xs font-medium">
                {user.institution}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="mt-6 grid grid-cols-3 gap-4 border-t border-gray-200 pt-4">
        <div className="text-center">
          <p className="text-xl font-semibold text-gray-900">
            {user?.verificationsCount || 0}
          </p>
          <p className="text-xs text-gray-500">Verifications</p>
        </div>
        <div className="text-center">
          <p className="text-xl font-semibold text-gray-900">
            {user?.paymentsCount || 0}
          </p>
          <p className="text-xs text-gray-500">Payments</p>
        </div>
        <div className="text-center">
          <p className="text-xl font-semibold text-gray-900">
            {user?.certificatesCount || 0}
          </p>
          <p className="text-xs text-gray-500">Certificates</p>
        </div>
      </div>

      {/* Last Login */}
      {user?.lastLoginAt && (
        <div className="mt-4 text-xs text-gray-500 border-t border-gray-200 pt-4">
          <span>Last login: {new Date(user.lastLoginAt).toLocaleString('en-LS')}</span>
        </div>
      )}

      {/* Actions */}
      <div className="mt-4 flex space-x-2">
        {onEdit && (
          <button
            onClick={onEdit}
            className="flex-1 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            Edit Profile
          </button>
        )}
        {onLogout && (
          <button
            onClick={onLogout}
            className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 text-sm font-medium rounded-md hover:bg-gray-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500"
          >
            Logout
          </button>
        )}
      </div>
    </div>
  );
};

export default UserProfileCard;