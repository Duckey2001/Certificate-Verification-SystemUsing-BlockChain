import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { FiUsers, FiSearch, FiFilter, FiEdit, FiTrash2, FiEye, FiMail, FiShield, FiCheck, FiX, FiUserPlus, FiDownload } from 'react-icons/fi';
import DataTable from './DataTable';

const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedUser, setSelectedUser] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRole, setFilterRole] = useState('all');

  // Mock data - in real app, this would come from API
  useEffect(() => {
    setLoading(true);
    // Simulate API call
    setTimeout(() => {
      setUsers([
        {
          id: 1,
          username: 'admin',
          email: 'admin@ecol.ac.ls',
          role: 'admin',
          status: 'active',
          institution: 'Examination Council',
          lastLogin: '2024-01-15T10:30:00Z',
          createdAt: '2024-01-01T00:00:00Z',
          verified: true
        },
        {
          id: 2,
          username: 'issuer1',
          email: 'issuer1@ecol.ac.ls',
          role: 'issuer',
          status: 'active',
          institution: 'Examination Council',
          lastLogin: '2024-01-15T09:15:00Z',
          createdAt: '2024-01-02T00:00:00Z',
          verified: true
        },
        {
          id: 3,
          username: 'verifier1',
          email: 'verifier1@example.com',
          role: 'verifier',
          status: 'pending',
          institution: 'Independent',
          lastLogin: null,
          createdAt: '2024-01-14T00:00:00Z',
          verified: false
        }
      ]);
      setLoading(false);
    }, 1000);
  }, []);

  const columns = [
    {
      key: 'username',
      label: 'Username',
      sortable: true,
      render: (value) => (
        <div className="flex items-center">
          <div className="w-8 h-8 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center text-white text-sm font-bold mr-3">
            {value.charAt(0).toUpperCase()}
          </div>
          <span className="font-medium">{value}</span>
        </div>
      )
    },
    {
      key: 'email',
      label: 'Email',
      sortable: true,
      render: (value) => (
        <div className="flex items-center">
          <FiMail className="w-4 h-4 mr-2 text-gray-400" />
          <span className="text-sm">{value}</span>
        </div>
      )
    },
    {
      key: 'role',
      label: 'Role',
      filterable: true,
      sortable: true,
      options: [
        { value: 'all', label: 'All Roles' },
        { value: 'admin', label: 'Admin' },
        { value: 'issuer', label: 'Issuer' },
        { value: 'verifier', label: 'Verifier' }
      ],
      render: (value) => {
        const colors = {
          admin: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
          issuer: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
          verifier: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400'
        };
        return (
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[value]}`}>
            {value.charAt(0).toUpperCase() + value.slice(1)}
          </span>
        );
      }
    },
    {
      key: 'status',
      label: 'Status',
      filterable: true,
      sortable: true,
      options: [
        { value: 'all', label: 'All Status' },
        { value: 'active', label: 'Active' },
        { value: 'pending', label: 'Pending' },
        { value: 'suspended', label: 'Suspended' }
      ],
      render: (value) => {
        const colors = {
          active: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
          pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
          suspended: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
        };
        return (
          <span className={`px-2 py-1 rounded-full text-xs font-medium ${colors[value]}`}>
            {value.charAt(0).toUpperCase() + value.slice(1)}
          </span>
        );
      }
    },
    {
      key: 'verified',
      label: 'Verified',
      sortable: true,
      render: (value) => (
        <div className="flex items-center">
          {value ? (
            <>
              <FiCheck className="w-4 h-4 text-green-500 mr-1" />
              <span className="text-xs text-green-600 dark:text-green-400">Yes</span>
            </>
          ) : (
            <>
              <FiX className="w-4 h-4 text-red-500 mr-1" />
              <span className="text-xs text-red-600 dark:text-red-400">No</span>
            </>
          )}
        </div>
      )
    },
    {
      key: 'lastLogin',
      label: 'Last Login',
      sortable: true,
      render: (value) => (
        <span className="text-sm text-gray-600 dark:text-gray-400">
          {value ? new Date(value).toLocaleDateString() : 'Never'}
        </span>
      )
    }
  ];

  const handleViewUser = (user) => {
    setSelectedUser(user);
  };

  const handleEditUser = (user) => {
    setSelectedUser(user);
    setShowEditModal(true);
  };

  const handleDeleteUser = (user) => {
    if (window.confirm(`Are you sure you want to delete user "${user.username}"?`)) {
      // Delete user logic
      setUsers(prev => prev.filter(u => u.id !== user.id));
    }
  };

  const handleVerifyUser = (user) => {
    // Verify user logic
    setUsers(prev => 
      prev.map(u => 
        u.id === user.id ? { ...u, verified: true, status: 'active' } : u
      )
    );
  };

  const handleSuspendUser = (user) => {
    // Suspend user logic
    setUsers(prev => 
      prev.map(u => 
        u.id === user.id ? { ...u, status: 'suspended' } : u
      )
    );
  };

  const handleExportUsers = () => {
    // Export logic
    const csv = [
      ['Username', 'Email', 'Role', 'Status', 'Verified', 'Last Login'],
      ...users.map(u => [
        u.username,
        u.email,
        u.role,
        u.status,
        u.verified,
        u.lastLogin || 'Never'
      ])
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `users_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white">User Management</h2>
          <p className="text-gray-600 dark:text-gray-400">Manage system users and permissions</p>
        </div>
        
        <div className="flex space-x-3">
          <button
            onClick={handleExportUsers}
            className="px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg flex items-center"
          >
            <FiDownload className="w-4 h-4 mr-2" />
            Export
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            className="px-4 py-2 bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white rounded-lg flex items-center"
          >
            <FiUserPlus className="w-4 h-4 mr-2" />
            Add User
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Total Users</p>
              <p className="text-2xl font-bold text-gray-900 dark:text-white">{users.length}</p>
            </div>
            <FiUsers className="w-8 h-8 text-blue-500" />
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Active</p>
              <p className="text-2xl font-bold text-green-600">{users.filter(u => u.status === 'active').length}</p>
            </div>
            <FiCheck className="w-8 h-8 text-green-500" />
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Pending</p>
              <p className="text-2xl font-bold text-yellow-600">{users.filter(u => u.status === 'pending').length}</p>
            </div>
            <FiShield className="w-8 h-8 text-yellow-500" />
          </div>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-500 dark:text-gray-400">Verified</p>
              <p className="text-2xl font-bold text-blue-600">{users.filter(u => u.verified).length}</p>
            </div>
            <FiShield className="w-8 h-8 text-blue-500" />
          </div>
        </div>
      </div>

      {/* Users Table */}
      <DataTable
        data={users}
        columns={columns}
        loading={loading}
        searchable={true}
        sortable={true}
        paginated={true}
        itemsPerPage={10}
        onView={handleViewUser}
        onEdit={handleEditUser}
        onDelete={handleDeleteUser}
        actions={[
          {
            icon: <FiCheck className="w-4 h-4" />,
            title: 'Verify',
            className: 'text-green-600 hover:text-green-800',
            onClick: handleVerifyUser,
            show: (user) => !user.verified
          },
          {
            icon: <FiX className="w-4 h-4" />,
            title: 'Suspend',
            className: 'text-yellow-600 hover:text-yellow-800',
            onClick: handleSuspendUser,
            show: (user) => user.status === 'active'
          }
        ]}
      />

      {/* User Detail Modal */}
      <AnimatePresence>
        {selectedUser && !showEditModal && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
            onClick={() => setSelectedUser(null)}
          >
            <motion.div
              initial={{ scale: 0.9, y: 20 }}
              animate={{ scale: 1, y: 0 }}
              exit={{ scale: 0.9, y: 20 }}
              className="bg-white dark:bg-gray-800 rounded-2xl p-6 max-w-md w-full mx-4"
              onClick={e => e.stopPropagation()}
            >
              <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">User Details</h3>
              <div className="space-y-4">
                <div className="flex items-center">
                  <div className="w-16 h-16 rounded-full bg-gradient-to-r from-blue-500 to-purple-500 flex items-center justify-center text-white text-2xl font-bold mr-4">
                    {selectedUser.username.charAt(0).toUpperCase()}
                  </div>
                  <div>
                    <h4 className="text-lg font-semibold">{selectedUser.username}</h4>
                    <p className="text-gray-600 dark:text-gray-400">{selectedUser.email}</p>
                  </div>
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Role</p>
                    <p className="font-medium">{selectedUser.role}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Status</p>
                    <p className="font-medium">{selectedUser.status}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Verified</p>
                    <p className="font-medium">{selectedUser.verified ? 'Yes' : 'No'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">Member Since</p>
                    <p className="font-medium">{new Date(selectedUser.createdAt).toLocaleDateString()}</p>
                  </div>
                </div>
              </div>
              
              <div className="flex justify-end space-x-3 mt-6">
                <button
                  onClick={() => setSelectedUser(null)}
                  className="px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg"
                >
                  Close
                </button>
                <button
                  onClick={() => {
                    setShowEditModal(true);
                  }}
                  className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg"
                >
                  Edit User
                </button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default UserManagement;
