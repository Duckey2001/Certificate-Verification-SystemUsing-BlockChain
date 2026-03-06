import React, { useEffect, useState, useCallback } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import RecentActivity from '../../components/RecentActivity';
import { adminApi, authApi, paymentApi } from '../../api';
import CertificatePreview from '../../components/CertificatePreview';
import PaymentDetails from '../../components/PaymentDetails';
import UserProfileCard from '../../components/UserProfileCard';

const TABS = ['overview', 'users', 'certificates', 'verifications', 'payments', 'invitations', 'logs'];

const AdminDashboard = () => {
  const { user, logout } = useAuth();
  const [stats, setStats] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [users, setUsers] = useState({ users: [], total: 0 });
  const [certificates, setCertificates] = useState({ certificates: [], total: 0 });
  const [verifications, setVerifications] = useState({ verifications: [], total: 0 });
  const [payments, setPayments] = useState({ payments: [], total: 0 });
  const [logs, setLogs] = useState({ logs: [], total: 0 });
  const [invitations, setInvitations] = useState([]);
  const [pendingUsers, setPendingUsers] = useState([]);
  const [inviteEmail, setInviteEmail] = useState('');
  const [inviteRole, setInviteRole] = useState('verifier');
  const [inviteLoading, setInviteLoading] = useState(false);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState({ users: 1, certificates: 1, verifications: 1, payments: 1, logs: 1 });
  const [actionMsg, setActionMsg] = useState('');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const [userRoleFilter, setUserRoleFilter] = useState('all');
  const [userInstitutionFilter, setUserInstitutionFilter] = useState('');
  const [userSearch, setUserSearch] = useState('');
  const [selectedCertificate, setSelectedCertificate] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const [selectedPayment, setSelectedPayment] = useState(null);
  const [showPaymentDetails, setShowPaymentDetails] = useState(false);
  const [dateRange, setDateRange] = useState({ start: '', end: '' });
  const [paymentStats, setPaymentStats] = useState(null);

  // Mock data for development
  const mockStats = {
    total_users: 156,
    total_certificates: 342,
    total_verifications: 1256,
    total_payments: 89,
    total_payment_amount: 4450.75,
    valid_verifications: 1180,
    invalid_verifications: 76
  };

  const mockPendingUsers = [
    { id: 101, username: 'john_doe', email: 'john.doe@example.com', created_at: new Date().toISOString() },
    { id: 102, username: 'jane_smith', email: 'jane.smith@example.com', created_at: new Date().toISOString() },
    { id: 103, username: 'mike_wilson', email: 'mike.wilson@example.com', created_at: new Date().toISOString() },
  ];

  const mockUsers = {
    users: [
      { id: 1, username: 'admin_user', email: 'admin@certivert.com', role: 'admin', institution_code: 'HQ', is_active: true, last_login_at: new Date().toISOString() },
      { id: 2, username: 'mpholekunye6', email: 'mpholekunye6@gmail.com', role: 'admin', institution_code: 'Ecol', is_active: true, last_login_at: new Date().toISOString() },
      { id: 3, username: 'issuer1', email: 'issuer@institution.com', role: 'issuer', institution_code: 'UNI001', is_active: true, last_login_at: new Date(Date.now() - 86400000).toISOString() },
      { id: 4, username: 'verifier1', email: 'verifier@example.com', role: 'verifier', institution_code: null, is_active: true, last_login_at: new Date(Date.now() - 172800000).toISOString() },
      { id: 5, username: 'pending_user', email: 'pending@example.com', role: 'pending', institution_code: null, is_active: false, last_login_at: null },
    ],
    total: 5
  };

  const mockCertificates = {
    certificates: [
      { id: 'C001', certificate_hash: '0x7d8a9f3e2b1c4d5e6f7a8b9c0d1e2f3a4b5c6d7e', student_name: 'Alice Johnson', student_id: 'STU001', issuer_code: 'UNI001', issue_date: new Date().toISOString(), status: 'verified', blockchain_tx_id: '0x9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b', blockchain_network: 'Hardhat' },
      { id: 'C002', certificate_hash: '0x1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b', student_name: 'Bob Smith', student_id: 'STU002', issuer_code: 'UNI001', issue_date: new Date(Date.now() - 604800000).toISOString(), status: 'verified', blockchain_tx_id: '0x8f7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b1a0f9e', blockchain_network: 'Hardhat' },
      { id: 'C003', certificate_hash: '0x9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e', student_name: 'Carol Davis', student_id: 'STU003', issuer_code: 'UNI002', issue_date: new Date(Date.now() - 1209600000).toISOString(), status: 'pending', blockchain_tx_id: null, blockchain_network: null },
    ],
    total: 3
  };

  const mockVerifications = {
    verifications: [
      { id: 1001, verification_date: new Date().toISOString(), certificate_hash: '0x7d8a9f3e2b1c4d5e6f7a8b9c0d1e2f3a4b5c6d7e', verifier_name: 'verifier1', verifier_id: 4, result: 'verified', blockchain_match: true, payment_method: 'mpesa_lesotho', verification_fee: 5.00 },
      { id: 1002, verification_date: new Date(Date.now() - 86400000).toISOString(), certificate_hash: '0x1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b', verifier_name: 'verifier1', verifier_id: 4, result: 'verified', blockchain_match: true, payment_method: 'mpesa', verification_fee: 5.00 },
      { id: 1003, verification_date: new Date(Date.now() - 172800000).toISOString(), certificate_hash: '0x9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e', verifier_name: 'external', verifier_id: null, result: 'invalid', blockchain_match: false, payment_method: 'ecocash', verification_fee: 5.00 },
    ],
    total: 3
  };

  const mockPayments = {
    payments: [
      { id: 5001, created_at: new Date().toISOString(), user_name: 'Alice Johnson', amount: 5.00, method: 'mpesa_lesotho', reference: 'REF123456', status: 'CONFIRMED', mpesa_transaction_id: 'MPS789012' },
      { id: 5002, created_at: new Date(Date.now() - 86400000).toISOString(), user_name: 'Bob Smith', amount: 5.00, method: 'mpesa', reference: 'REF789012', status: 'CONFIRMED', mpesa_transaction_id: 'MPS345678' },
      { id: 5003, created_at: new Date(Date.now() - 172800000).toISOString(), user_name: 'Carol Davis', amount: 5.00, method: 'ecocash', reference: 'REF345678', status: 'PENDING', mpesa_transaction_id: null },
    ],
    total: 3
  };

  const mockLogs = {
    logs: [
      { id: 9001, created_at: new Date().toISOString(), event_type: 'user_login_success', actor_user_id: '2', actor_role: 'admin', target_user_id: null, payload: { ip: '192.168.1.100' } },
      { id: 9002, created_at: new Date(Date.now() - 3600000).toISOString(), event_type: 'certificate_issued', actor_user_id: '3', actor_role: 'issuer', target_user_id: null, certificate_hash: '0x7d8a9f3e2b1c4d5e6f7a8b9c0d1e2f3a4b5c6d7e', payload: { student_name: 'Alice Johnson' } },
      { id: 9003, created_at: new Date(Date.now() - 7200000).toISOString(), event_type: 'payment_confirmed', actor_user_id: 'System', target_user_id: null, payload: { payment_id: 5001, amount: 5.00 } },
      { id: 9004, created_at: new Date(Date.now() - 86400000).toISOString(), event_type: 'user_approved', actor_user_id: '1', actor_role: 'admin', target_user_id: '5', payload: { role: 'verifier' } },
    ],
    total: 4
  };

  const mockInvitations = [
    { id: 3001, email: 'new.issuer@institution.com', role: 'issuer', used: false, created_at: new Date().toISOString(), expires_at: new Date(Date.now() + 604800000).toISOString(), link: 'https://certivert.com/invite/abc123' },
    { id: 3002, email: 'external.verifier@example.com', role: 'verifier', used: false, created_at: new Date(Date.now() - 86400000).toISOString(), expires_at: new Date(Date.now() + 518400000).toISOString(), link: 'https://certivert.com/invite/def456' },
    { id: 3003, email: 'used.invite@example.com', role: 'admin', used: true, created_at: new Date(Date.now() - 1209600000).toISOString(), expires_at: new Date(Date.now() - 604800000).toISOString(), link: 'https://certivert.com/invite/ghi789' },
  ];

  const mockPaymentStats = {
    total_payments: 89,
    total_amount: 4450.75,
    confirmed_payments: 76,
    pending_payments: 13
  };

  // Fetch initial data
  useEffect(() => {
    let mounted = true;
    
    const fetchInitialData = async () => {
      try {
        // Try to fetch real data, fallback to mock if not available
        let statsData = { stats: null };
        let pendingData = [];
        
        try {
          if (adminApi.getSystemStats) {
            statsData = await adminApi.getSystemStats();
          } else {
            throw new Error('API function not available');
          }
        } catch (e) {
          console.log('Using mock stats data');
          statsData = { stats: mockStats };
        }
        
        try {
          if (adminApi.getPendingUsers) {
            pendingData = await adminApi.getPendingUsers();
          } else {
            throw new Error('API function not available');
          }
        } catch (e) {
          console.log('Using mock pending data');
          pendingData = mockPendingUsers;
        }
        
        if (mounted) {
          setStats(statsData?.stats || mockStats);
          setPendingUsers(pendingData || mockPendingUsers);
        }
      } catch (error) {
        console.error('Failed to fetch initial data:', error);
        if (mounted) {
          setStats(mockStats);
          setPendingUsers(mockPendingUsers);
        }
      }
    };
    
    fetchInitialData();
    
    return () => { mounted = false; };
  }, []);

  // Fetch data based on active tab
  useEffect(() => {
    const fetchTabData = async () => {
      setLoading(true);
      try {
        if (activeTab === 'users') {
          try {
            if (adminApi.getAllUsers) {
              const data = await adminApi.getAllUsers(page.users, 20, {
                role: userRoleFilter === 'all' ? undefined : userRoleFilter,
                institution: userInstitutionFilter || undefined,
                q: userSearch || undefined
              });
              setUsers(data);
            } else {
              setUsers(mockUsers);
            }
          } catch (e) {
            console.log('Using mock users data');
            setUsers(mockUsers);
          }
        } else if (activeTab === 'certificates') {
          try {
            if (adminApi.getAllCertificates) {
              const data = await adminApi.getAllCertificates(page.certificates, 20, {
                start_date: dateRange.start || undefined,
                end_date: dateRange.end || undefined
              });
              setCertificates(data);
            } else {
              setCertificates(mockCertificates);
            }
          } catch (e) {
            console.log('Using mock certificates data');
            setCertificates(mockCertificates);
          }
        } else if (activeTab === 'verifications') {
          try {
            if (adminApi.getAllVerifications) {
              const data = await adminApi.getAllVerifications(page.verifications, 20, {
                start_date: dateRange.start || undefined,
                end_date: dateRange.end || undefined
              });
              setVerifications(data);
            } else {
              setVerifications(mockVerifications);
            }
          } catch (e) {
            console.log('Using mock verifications data');
            setVerifications(mockVerifications);
          }
        } else if (activeTab === 'payments') {
          try {
            let paymentsData = { payments: [], total: 0 };
            let statsData = null;
            
            if (adminApi.getAllPayments && paymentApi.getPaymentStats) {
              [paymentsData, statsData] = await Promise.all([
                adminApi.getAllPayments(page.payments, 20, {
                  start_date: dateRange.start || undefined,
                  end_date: dateRange.end || undefined
                }),
                paymentApi.getPaymentStats()
              ]);
            } else {
              throw new Error('API functions not available');
            }
            setPayments(paymentsData);
            setPaymentStats(statsData);
          } catch (e) {
            console.log('Using mock payments data');
            setPayments(mockPayments);
            setPaymentStats(mockPaymentStats);
          }
        } else if (activeTab === 'logs') {
          try {
            if (adminApi.getSystemLogs) {
              const data = await adminApi.getSystemLogs(page.logs, 50);
              setLogs(data);
            } else {
              setLogs(mockLogs);
            }
          } catch (e) {
            console.log('Using mock logs data');
            setLogs(mockLogs);
          }
        } else if (activeTab === 'invitations') {
          try {
            if (authApi.getAllInvitations) {
              const data = await authApi.getAllInvitations();
              setInvitations(Array.isArray(data) ? data : []);
            } else {
              setInvitations(mockInvitations);
            }
          } catch (e) {
            console.log('Using mock invitations data');
            setInvitations(mockInvitations);
          }
        }
      } catch (error) {
        console.error(`Failed to fetch ${activeTab}:`, error);
      } finally {
        setLoading(false);
      }
    };

    fetchTabData();
  }, [activeTab, page, userRoleFilter, userInstitutionFilter, userSearch, dateRange]);

  const handleUpdateRole = async (userId, role) => {
    try {
      if (adminApi.updateUserRole) {
        await adminApi.updateUserRole(userId, role);
        setActionMsg('✅ Role updated successfully');
      } else {
        setActionMsg('✅ Role updated successfully (mock)');
      }
      
      // Refresh users
      if (adminApi.getAllUsers) {
        const data = await adminApi.getAllUsers(page.users, 20, {
          role: userRoleFilter === 'all' ? undefined : userRoleFilter,
          institution: userInstitutionFilter || undefined,
          q: userSearch || undefined
        });
        setUsers(data);
      } else {
        // Update mock data
        setUsers(prev => ({
          ...prev,
          users: prev.users.map(u => 
            u.id === userId ? { ...u, role } : u
          )
        }));
      }
    } catch (e) {
      setActionMsg(`❌ ${e?.response?.data?.detail || 'Failed to update role'}`);
    }
    setTimeout(() => setActionMsg(''), 3000);
  };

  const handleApproveUser = async (userId, approve, role = 'verifier') => {
    try {
      if (adminApi.approveUser) {
        await adminApi.approveUser({ user_id: userId, approve, role });
        setActionMsg(`✅ User ${approve ? 'approved' : 'rejected'} successfully`);
      } else {
        setActionMsg(`✅ User ${approve ? 'approved' : 'rejected'} successfully (mock)`);
      }
      
      // Refresh pending users
      if (adminApi.getPendingUsers) {
        const pendingData = await adminApi.getPendingUsers();
        setPendingUsers(pendingData || []);
      } else {
        setPendingUsers(prev => prev.filter(u => u.id !== userId));
      }
      
      // Refresh users list
      if (adminApi.getAllUsers) {
        const data = await adminApi.getAllUsers(page.users, 20, {
          role: userRoleFilter === 'all' ? undefined : userRoleFilter,
          institution: userInstitutionFilter || undefined,
          q: userSearch || undefined
        });
        setUsers(data);
      } else if (approve) {
        // Add to mock users
        const approvedUser = pendingUsers.find(u => u.id === userId);
        if (approvedUser) {
          setUsers(prev => ({
            ...prev,
            users: [...prev.users, {
              id: userId,
              username: approvedUser.username,
              email: approvedUser.email,
              role: role,
              institution_code: null,
              is_active: true,
              last_login_at: null
            }],
            total: prev.total + 1
          }));
        }
      }
    } catch (e) {
      setActionMsg(`❌ ${e?.response?.data?.detail || 'Failed to process user'}`);
    }
    setTimeout(() => setActionMsg(''), 3000);
  };

  const handleInvite = async (e) => {
    e.preventDefault();
    if (!inviteEmail.trim()) return;
    
    setInviteLoading(true);
    setActionMsg('');
    
    try {
      if (authApi.generateInvitation) {
        const { link } = await authApi.generateInvitation({ 
          email: inviteEmail.trim(), 
          role: inviteRole 
        });
        setActionMsg(`✓ Invitation created! Share this link: ${link}`);
      } else {
        const mockLink = `https://certivert.com/invite/${Math.random().toString(36).substring(2, 10)}`;
        setActionMsg(`✓ Invitation created! Share this link: ${mockLink} (mock)`);
        
        // Add to mock invitations
        const newInvite = {
          id: Date.now(),
          email: inviteEmail.trim(),
          role: inviteRole,
          used: false,
          created_at: new Date().toISOString(),
          expires_at: new Date(Date.now() + 604800000).toISOString(),
          link: mockLink
        };
        setInvitations(prev => [...prev, newInvite]);
      }
      
      setInviteEmail('');
      
      // Refresh invitations
      if (authApi.getAllInvitations) {
        const data = await authApi.getAllInvitations();
        setInvitations(Array.isArray(data) ? data : []);
      }
    } catch (e) {
      setActionMsg(`❌ ${e?.response?.data?.detail || 'Failed to create invite'}`);
    }
    
    setInviteLoading(false);
    setTimeout(() => setActionMsg(''), 5000);
  };

  const handleDeleteUser = async (userId) => {
    if (!window.confirm('Are you sure you want to delete this user? This action cannot be undone.')) return;
    
    try {
      if (adminApi.deleteUser) {
        await adminApi.deleteUser(userId);
        setActionMsg('✅ User deleted successfully');
      } else {
        setActionMsg('✅ User deleted successfully (mock)');
      }
      
      // Refresh users
      if (adminApi.getAllUsers) {
        const data = await adminApi.getAllUsers(page.users, 20, {
          role: userRoleFilter === 'all' ? undefined : userRoleFilter,
          institution: userInstitutionFilter || undefined,
          q: userSearch || undefined
        });
        setUsers(data);
      } else {
        setUsers(prev => ({
          ...prev,
          users: prev.users.filter(u => u.id !== userId),
          total: prev.total - 1
        }));
      }
    } catch (e) {
      setActionMsg(`❌ ${e?.response?.data?.detail || 'Failed to delete user'}`);
    }
    setTimeout(() => setActionMsg(''), 3000);
  };

  const handleRevokeCertificate = async (certificateId) => {
    if (!window.confirm('Are you sure you want to revoke this certificate?')) return;
    
    try {
      if (adminApi.revokeCertificate) {
        await adminApi.revokeCertificate(certificateId);
        setActionMsg('✅ Certificate revoked successfully');
      } else {
        setActionMsg('✅ Certificate revoked successfully (mock)');
      }
      
      // Refresh certificates
      if (adminApi.getAllCertificates) {
        const data = await adminApi.getAllCertificates(page.certificates, 20);
        setCertificates(data);
      } else {
        setCertificates(prev => ({
          ...prev,
          certificates: prev.certificates.map(c => 
            c.id === certificateId ? { ...c, status: 'revoked' } : c
          )
        }));
      }
    } catch (e) {
      setActionMsg(`❌ ${e?.response?.data?.detail || 'Failed to revoke certificate'}`);
    }
    setTimeout(() => setActionMsg(''), 3000);
  };

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const getTabIcon = (tab) => {
    switch(tab) {
      case 'overview': return '📊';
      case 'users': return '👥';
      case 'certificates': return '📜';
      case 'verifications': return '✓';
      case 'payments': return '💰';
      case 'invitations': return '📧';
      case 'logs': return '📋';
      default: return '•';
    }
  };

  const getStatusColor = (status) => {
    switch(status?.toLowerCase()) {
      case 'confirmed':
      case 'verified':
      case 'success':
        return 'bg-green-100 text-green-800';
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'failed':
      case 'rejected':
      case 'invalid':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatCurrency = (amount) => {
    return `M${parseFloat(amount).toFixed(2)}`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex">
      {/* Modals */}
      {showPreview && selectedCertificate && (
        <CertificatePreview
          certificate={selectedCertificate}
          onClose={() => {
            setShowPreview(false);
            setSelectedCertificate(null);
          }}
          onRevoke={() => handleRevokeCertificate(selectedCertificate.id)}
        />
      )}

      {showPaymentDetails && selectedPayment && (
        <PaymentDetails
          payment={selectedPayment}
          onClose={() => {
            setShowPaymentDetails(false);
            setSelectedPayment(null);
          }}
        />
      )}

      {/* Left Sidebar */}
      <div className={`${sidebarCollapsed ? 'w-20' : 'w-80'} bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 text-white transition-all duration-300 shadow-2xl flex flex-col relative`}>
        {/* Logo Area */}
        <div className="p-6 border-b border-gray-700/50">
          <div className="flex items-center space-x-4">
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-purple-500 to-blue-500 rounded-xl blur-lg opacity-50 animate-pulse"></div>
              <div className="relative bg-gradient-to-r from-purple-500 to-blue-500 p-3 rounded-xl shadow-lg transform hover:scale-105 transition-transform duration-300">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
              </div>
            </div>
            {!sidebarCollapsed && (
              <div className="animate-fadeIn">
                <span className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">CertiVert</span>
                <span className="block text-xs text-gray-400 mt-1">Admin Portal</span>
              </div>
            )}
          </div>
        </div>

        {/* Admin Profile */}
        <div className="p-6 border-b border-gray-700/50">
          <div className="flex items-center space-x-4">
            <div className="relative">
              <div className="w-16 h-16 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold text-xl shadow-lg transform hover:scale-105 transition-transform">
                {user?.username?.charAt(0).toUpperCase() || 'A'}
              </div>
              <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-green-500 border-2 border-gray-800 rounded-full animate-pulse"></div>
            </div>
            {!sidebarCollapsed && (
              <div className="flex-1">
                <p className="font-semibold text-lg">{user?.username || 'Admin'}</p>
                <p className="text-xs text-gray-400 truncate">{user?.email || 'admin@certivert.com'}</p>
                <span className="inline-block mt-2 px-3 py-1 bg-purple-600/30 text-purple-300 rounded-full text-xs font-medium">
                  SUPER ADMIN
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Quick Stats */}
        {!sidebarCollapsed && stats && (
          <div className="p-4 border-b border-gray-700/50">
            <h4 className="text-xs uppercase tracking-wider text-gray-400 mb-3 flex items-center">
              <span className="w-1 h-4 bg-purple-500 rounded-full mr-2"></span>
              System Health
            </h4>
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-gray-800/50 rounded-lg p-3">
                <p className="text-xs text-gray-400">Users</p>
                <p className="text-xl font-bold text-purple-400">{stats.total_users}</p>
              </div>
              <div className="bg-gray-800/50 rounded-lg p-3">
                <p className="text-xs text-gray-400">Certificates</p>
                <p className="text-xl font-bold text-blue-400">{stats.total_certificates}</p>
              </div>
              <div className="bg-gray-800/50 rounded-lg p-3">
                <p className="text-xs text-gray-400">Payments</p>
                <p className="text-xl font-bold text-green-400">{stats.total_payments}</p>
              </div>
              <div className="bg-gray-800/50 rounded-lg p-3">
                <p className="text-xs text-gray-400">Pending</p>
                <p className="text-xl font-bold text-yellow-400">{pendingUsers.length}</p>
              </div>
            </div>
          </div>
        )}

        {/* Navigation Tabs */}
        <nav className="flex-1 overflow-y-auto py-6 px-3">
          {TABS.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 mb-1 relative group ${
                activeTab === tab 
                  ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white shadow-lg transform scale-105' 
                  : 'text-gray-300 hover:bg-gray-700/50 hover:text-white'
              }`}
            >
              <span className="text-xl">{getTabIcon(tab)}</span>
              {!sidebarCollapsed && (
                <>
                  <span className="font-medium capitalize">{tab}</span>
                  {activeTab === tab && (
                    <span className="absolute right-3 w-2 h-2 bg-white rounded-full animate-ping"></span>
                  )}
                </>
              )}
              {tab === 'users' && pendingUsers.length > 0 && !sidebarCollapsed && (
                <span className="absolute right-3 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center animate-pulse">
                  {pendingUsers.length}
                </span>
              )}
            </button>
          ))}
        </nav>

        {/* Logout Section */}
        <div className="p-6 border-t border-gray-700/50">
          {!showLogoutConfirm ? (
            <button
              onClick={() => setShowLogoutConfirm(true)}
              className="w-full flex items-center space-x-3 px-4 py-3 text-gray-300 hover:text-white hover:bg-red-600/20 rounded-xl transition-all duration-200 group"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
              </svg>
              {!sidebarCollapsed && <span className="font-medium">Logout</span>}
            </button>
          ) : (
            <div className="bg-gray-800/50 rounded-xl p-4 animate-slideUp">
              <p className="text-sm text-gray-300 text-center mb-3">Confirm logout?</p>
              <div className="flex space-x-2">
                <button
                  onClick={handleLogout}
                  className="flex-1 px-3 py-2 bg-red-600 hover:bg-red-700 rounded-lg text-white text-sm font-medium transition-colors"
                >
                  Yes
                </button>
                <button
                  onClick={() => setShowLogoutConfirm(false)}
                  className="flex-1 px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-white text-sm font-medium transition-colors"
                >
                  No
                </button>
              </div>
            </div>
          )}
          
          {/* Sidebar Toggle */}
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="absolute bottom-6 -right-3 w-8 h-8 bg-gray-800 rounded-full flex items-center justify-center text-white border-2 border-gray-700 hover:bg-gray-700 transition-colors shadow-lg"
          >
            {sidebarCollapsed ? '→' : '←'}
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-auto">
        {/* Top Bar */}
        <div className="bg-white/80 backdrop-blur-md shadow-sm sticky top-0 z-10 border-b border-gray-200">
          <div className="px-8 py-4 flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-800 capitalize">{activeTab} Dashboard</h1>
              <p className="text-sm text-gray-500">Welcome back, {user?.username}! Here's what's happening.</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="relative">
                <span className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full animate-pulse"></span>
                <div className="w-10 h-10 rounded-full bg-gradient-to-r from-purple-500 to-blue-500 flex items-center justify-center text-white font-bold shadow-lg">
                  {user?.username?.charAt(0).toUpperCase() || 'A'}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Action Message */}
        {actionMsg && (
          <div className="mx-8 mt-4 px-6 py-4 rounded-xl bg-gradient-to-r from-green-500 to-green-600 text-white shadow-lg animate-slideDown flex items-center">
            <span className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center mr-3">✓</span>
            {actionMsg}
          </div>
        )}

        {/* Content Area */}
        <div className="p-8">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <>
              {/* Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
                <div className="bg-white rounded-2xl shadow-lg p-6 transform hover:scale-105 transition-all duration-300 border-l-4 border-purple-500">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-gray-500 text-sm">Total Users</p>
                      <p className="text-3xl font-bold text-gray-800">{stats?.total_users ?? 0}</p>
                    </div>
                    <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
                      <span className="text-2xl">👥</span>
                    </div>
                  </div>
                  <p className="text-xs text-gray-400 mt-2">Registered users</p>
                </div>

                <div className="bg-white rounded-2xl shadow-lg p-6 transform hover:scale-105 transition-all duration-300 border-l-4 border-blue-500">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-gray-500 text-sm">Certificates</p>
                      <p className="text-3xl font-bold text-gray-800">{stats?.total_certificates ?? 0}</p>
                    </div>
                    <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                      <span className="text-2xl">📜</span>
                    </div>
                  </div>
                  <p className="text-xs text-gray-400 mt-2">Certificates issued</p>
                </div>

                <div className="bg-white rounded-2xl shadow-lg p-6 transform hover:scale-105 transition-all duration-300 border-l-4 border-green-500">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-gray-500 text-sm">Verifications</p>
                      <p className="text-3xl font-bold text-gray-800">{stats?.total_verifications ?? 0}</p>
                    </div>
                    <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                      <span className="text-2xl">✓</span>
                    </div>
                  </div>
                  <p className="text-xs text-gray-400 mt-2">
                    Valid: {stats?.valid_verifications ?? 0} | Invalid: {stats?.invalid_verifications ?? 0}
                  </p>
                </div>

                <div className="bg-white rounded-2xl shadow-lg p-6 transform hover:scale-105 transition-all duration-300 border-l-4 border-yellow-500">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-gray-500 text-sm">Payments</p>
                      <p className="text-3xl font-bold text-gray-800">{stats?.total_payments ?? 0}</p>
                    </div>
                    <div className="w-12 h-12 bg-yellow-100 rounded-xl flex items-center justify-center">
                      <span className="text-2xl">💰</span>
                    </div>
                  </div>
                  <p className="text-xs text-gray-400 mt-2">Total: {formatCurrency(stats?.total_payment_amount || 0)}</p>
                </div>
              </div>

              {/* Pending Approvals */}
              {pendingUsers.length > 0 && (
                <div className="bg-white rounded-2xl shadow-lg overflow-hidden mb-6">
                  <div className="px-6 py-4 bg-gradient-to-r from-yellow-500 to-orange-600 flex justify-between items-center">
                    <h3 className="text-lg font-semibold text-white flex items-center">
                      <span className="w-2 h-2 bg-white rounded-full mr-2 animate-pulse"></span>
                      Pending Approvals ({pendingUsers.length})
                    </h3>
                  </div>
                  <div className="p-6">
                    <div className="space-y-4">
                      {pendingUsers.map((user) => (
                        <div key={user.id} className="bg-gray-50 rounded-xl p-4 flex items-center justify-between hover:shadow-md transition-shadow">
                          <div className="flex items-center space-x-4">
                            <div className="w-12 h-12 rounded-full bg-gradient-to-r from-yellow-500 to-orange-500 flex items-center justify-center text-white font-bold">
                              {user.username?.charAt(0).toUpperCase()}
                            </div>
                            <div>
                              <p className="font-medium text-gray-800">{user.username}</p>
                              <p className="text-sm text-gray-500">{user.email}</p>
                              <p className="text-xs text-gray-400 mt-1">Requested: {formatDate(user.created_at)}</p>
                            </div>
                          </div>
                          <div className="flex space-x-3">
                            <select
                              onChange={(e) => handleApproveUser(user.id, true, e.target.value)}
                              className="px-3 py-2 border-2 border-green-200 rounded-lg text-sm focus:border-green-500 focus:ring focus:ring-green-200"
                              defaultValue=""
                            >
                              <option value="" disabled>Approve as...</option>
                              <option value="verifier">Verifier</option>
                              <option value="issuer">Issuer</option>
                              <option value="admin">Admin</option>
                            </select>
                            <button
                              onClick={() => handleApproveUser(user.id, false)}
                              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                            >
                              Reject
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Recent Activity */}
              <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
                <div className="px-6 py-4 bg-gradient-to-r from-purple-500 to-blue-600">
                  <h3 className="text-lg font-semibold text-white">Live System Activity</h3>
                </div>
                <div className="p-6">
                  <RecentActivity limit={8} />
                </div>
              </div>
            </>
          )}

          {/* Users Tab */}
          {activeTab === 'users' && (
            <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
              <div className="px-6 py-4 bg-gradient-to-r from-blue-500 to-blue-600">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                  <h3 className="text-lg font-semibold text-white flex items-center">
                    <span className="w-2 h-2 bg-white rounded-full mr-2"></span>
                    Users Management ({users.total})
                  </h3>
                  <div className="flex flex-wrap gap-3">
                    <select
                      value={userRoleFilter}
                      onChange={(e) => { setPage((p) => ({ ...p, users: 1 })); setUserRoleFilter(e.target.value); }}
                      className="text-sm border-0 rounded-lg px-3 py-2 bg-white/10 text-white placeholder:text-blue-100 focus:outline-none focus:ring-2 focus:ring-white/40"
                    >
                      <option value="all">All roles</option>
                      <option value="admin">Admin</option>
                      <option value="issuer">Issuer</option>
                      <option value="verifier">Verifier</option>
                      <option value="pending">Pending</option>
                    </select>
                    <input
                      type="text"
                      placeholder="Filter by institution..."
                      value={userInstitutionFilter}
                      onChange={(e) => { setPage((p) => ({ ...p, users: 1 })); setUserInstitutionFilter(e.target.value); }}
                      className="text-sm border-0 rounded-lg px-3 py-2 bg-white/10 text-white placeholder:text-blue-100 focus:outline-none focus:ring-2 focus:ring-white/40"
                    />
                    <input
                      type="text"
                      placeholder="Search users..."
                      value={userSearch}
                      onChange={(e) => { setPage((p) => ({ ...p, users: 1 })); setUserSearch(e.target.value); }}
                      className="text-sm border-0 rounded-lg px-3 py-2 bg-white/10 text-white placeholder:text-blue-100 focus:outline-none focus:ring-2 focus:ring-white/40"
                    />
                  </div>
                </div>
              </div>
              
              {loading ? (
                <div className="p-12 text-center">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-blue-500 border-t-transparent"></div>
                  <p className="text-gray-500 mt-2">Loading users...</p>
                </div>
              ) : (
                <>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Institution</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Last Login</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {(users.users || []).map((u, index) => (
                          <tr key={u.id} className="hover:bg-gray-50 transition-colors animate-fadeIn" style={{ animationDelay: `${index * 50}ms` }}>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <div className="w-10 h-10 rounded-full bg-gradient-to-r from-purple-500 to-blue-500 flex items-center justify-center text-white font-bold mr-3">
                                  {u.username?.charAt(0).toUpperCase()}
                                </div>
                                <span className="text-sm font-medium text-gray-900">{u.username}</span>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{u.email}</td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <select 
                                value={u.role} 
                                onChange={(e) => handleUpdateRole(u.id, e.target.value)}
                                className={`text-sm border-2 rounded-lg px-3 py-1.5 focus:ring-2 transition-all ${
                                  u.role === 'admin' ? 'border-purple-300 bg-purple-50' :
                                  u.role === 'issuer' ? 'border-green-300 bg-green-50' :
                                  u.role === 'verifier' ? 'border-blue-300 bg-blue-50' :
                                  'border-yellow-300 bg-yellow-50'
                                }`}
                              >
                                <option value="admin">Admin</option>
                                <option value="issuer">Issuer</option>
                                <option value="verifier">Verifier</option>
                                <option value="pending">Pending</option>
                              </select>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {u.institution_code || '-'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                                u.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                              }`}>
                                <span className={`w-2 h-2 rounded-full mr-1 ${u.is_active ? 'bg-green-500' : 'bg-red-500'}`}></span>
                                {u.is_active ? 'Active' : 'Inactive'}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {u.last_login_at ? formatDate(u.last_login_at) : 'Never'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm">
                              {u.id !== user?.id && (
                                <button 
                                  onClick={() => handleDeleteUser(u.id)}
                                  className="text-red-600 hover:text-red-800 font-medium hover:underline"
                                >
                                  Delete
                                </button>
                              )}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  
                  {/* Pagination */}
                  {users.total > 20 && (
                    <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex items-center justify-between">
                      <button
                        disabled={page.users <= 1}
                        onClick={() => setPage((p) => ({ ...p, users: p.users - 1 }))}
                        className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        Previous
                      </button>
                      <span className="text-sm text-gray-700">
                        Page <span className="font-medium">{page.users}</span> of <span className="font-medium">{Math.ceil(users.total / 20)}</span>
                      </span>
                      <button
                        disabled={page.users * 20 >= users.total}
                        onClick={() => setPage((p) => ({ ...p, users: p.users + 1 }))}
                        className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                      >
                        Next
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {/* Certificates Tab */}
          {activeTab === 'certificates' && (
            <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
              <div className="px-6 py-4 bg-gradient-to-r from-green-500 to-green-600">
                <div className="flex justify-between items-center">
                  <h3 className="text-lg font-semibold text-white">Certificates ({certificates.total})</h3>
                  <div className="flex gap-3">
                    <input
                      type="date"
                      value={dateRange.start}
                      onChange={(e) => setDateRange({...dateRange, start: e.target.value})}
                      className="text-sm border-0 rounded-lg px-3 py-2 bg-white/10 text-white placeholder:text-green-100"
                      placeholder="Start date"
                    />
                    <input
                      type="date"
                      value={dateRange.end}
                      onChange={(e) => setDateRange({...dateRange, end: e.target.value})}
                      className="text-sm border-0 rounded-lg px-3 py-2 bg-white/10 text-white placeholder:text-green-100"
                      placeholder="End date"
                    />
                  </div>
                </div>
              </div>
              
              {loading ? (
                <div className="p-12 text-center">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-green-500 border-t-transparent"></div>
                  <p className="text-gray-500 mt-2">Loading certificates...</p>
                </div>
              ) : (
                <>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Certificate</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Student</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Issuer</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Issue Date</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Blockchain</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {(certificates.certificates || []).map((c, index) => (
                          <tr key={c.id} className="hover:bg-gray-50 transition-colors">
                            <td className="px-6 py-4">
                              <div className="flex flex-col">
                                <span className="text-xs text-gray-500">ID: {c.id}</span>
                                <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded mt-1">
                                  {c.certificate_hash?.slice(0, 20)}...
                                </span>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="text-sm font-medium text-gray-900">{c.student_name}</div>
                              <div className="text-xs text-gray-500">ID: {c.student_id}</div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{c.issuer_code}</td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {formatDate(c.issue_date)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                                c.status === 'verified' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                              }`}>
                                {c.status}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              {c.blockchain_tx_id ? (
                                <div className="flex flex-col">
                                  <span className="text-xs font-mono bg-blue-100 text-blue-800 px-2 py-1 rounded">
                                    {String(c.blockchain_tx_id).slice(0, 12)}...
                                  </span>
                                  <span className="text-xs text-gray-400 mt-1">{c.blockchain_network}</span>
                                </div>
                              ) : (
                                <span className="text-xs text-gray-400">Not on blockchain</span>
                              )}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm">
                              <button
                                onClick={() => {
                                  setSelectedCertificate(c);
                                  setShowPreview(true);
                                }}
                                className="text-blue-600 hover:text-blue-800 font-medium mr-3"
                              >
                                View
                              </button>
                              <button
                                onClick={() => handleRevokeCertificate(c.id)}
                                className="text-red-600 hover:text-red-800 font-medium"
                              >
                                Revoke
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  
                  {/* Pagination */}
                  {certificates.total > 20 && (
                    <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex items-center justify-between">
                      <button
                        disabled={page.certificates <= 1}
                        onClick={() => setPage((p) => ({ ...p, certificates: p.certificates - 1 }))}
                        className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                      >
                        Previous
                      </button>
                      <span className="text-sm text-gray-700">
                        Page {page.certificates} of {Math.ceil(certificates.total / 20)}
                      </span>
                      <button
                        disabled={page.certificates * 20 >= certificates.total}
                        onClick={() => setPage((p) => ({ ...p, certificates: p.certificates + 1 }))}
                        className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                      >
                        Next
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {/* Verifications Tab */}
          {activeTab === 'verifications' && (
            <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
              <div className="px-6 py-4 bg-gradient-to-r from-indigo-500 to-indigo-600">
                <div className="flex justify-between items-center">
                  <h3 className="text-lg font-semibold text-white">Verifications ({verifications.total})</h3>
                  <div className="flex gap-3">
                    <input
                      type="date"
                      value={dateRange.start}
                      onChange={(e) => setDateRange({...dateRange, start: e.target.value})}
                      className="text-sm border-0 rounded-lg px-3 py-2 bg-white/10 text-white"
                    />
                    <input
                      type="date"
                      value={dateRange.end}
                      onChange={(e) => setDateRange({...dateRange, end: e.target.value})}
                      className="text-sm border-0 rounded-lg px-3 py-2 bg-white/10 text-white"
                    />
                  </div>
                </div>
              </div>
              
              {loading ? (
                <div className="p-12 text-center">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-indigo-500 border-t-transparent"></div>
                  <p className="text-gray-500 mt-2">Loading verifications...</p>
                </div>
              ) : (
                <>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Certificate</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Verifier</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Result</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Blockchain</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Payment</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Fee</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {(verifications.verifications || []).map((v, index) => (
                          <tr key={v.id} className="hover:bg-gray-50 transition-colors">
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {formatDate(v.verification_date)}
                            </td>
                            <td className="px-6 py-4">
                              <div className="flex flex-col">
                                <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded">
                                  {v.certificate_hash?.slice(0, 20)}...
                                </span>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {v.verifier_name || v.verifier_id}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                                v.result === 'verified' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                              }`}>
                                {v.result}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`text-xs font-medium ${v.blockchain_match ? 'text-green-600' : 'text-red-600'}`}>
                                {v.blockchain_match ? '✓ Match' : '✗ No match'}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <span className="text-lg mr-1">
                                  {v.payment_method === 'mpesa_lesotho' ? '📱' : 
                                   v.payment_method === 'mpesa' ? '📱' :
                                   v.payment_method === 'ecocash' ? '📲' : '🏦'}
                                </span>
                                <span className="text-sm text-gray-600">{v.payment_method?.replace('_', ' ')}</span>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-green-600">
                              {formatCurrency(v.verification_fee || 5.00)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  
                  {/* Pagination */}
                  {verifications.total > 20 && (
                    <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex items-center justify-between">
                      <button
                        disabled={page.verifications <= 1}
                        onClick={() => setPage((p) => ({ ...p, verifications: p.verifications - 1 }))}
                        className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                      >
                        Previous
                      </button>
                      <span className="text-sm text-gray-700">
                        Page {page.verifications} of {Math.ceil(verifications.total / 20)}
                      </span>
                      <button
                        disabled={page.verifications * 20 >= verifications.total}
                        onClick={() => setPage((p) => ({ ...p, verifications: p.verifications + 1 }))}
                        className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                      >
                        Next
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {/* Payments Tab */}
          {activeTab === 'payments' && (
            <div className="space-y-6">
              {/* Payment Stats */}
              {paymentStats && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <div className="bg-white rounded-2xl shadow-lg p-6">
                    <p className="text-sm text-gray-500">Total Payments</p>
                    <p className="text-2xl font-bold text-gray-800">{paymentStats.total_payments}</p>
                  </div>
                  <div className="bg-white rounded-2xl shadow-lg p-6">
                    <p className="text-sm text-gray-500">Total Amount</p>
                    <p className="text-2xl font-bold text-green-600">{formatCurrency(paymentStats.total_amount)}</p>
                  </div>
                  <div className="bg-white rounded-2xl shadow-lg p-6">
                    <p className="text-sm text-gray-500">Confirmed</p>
                    <p className="text-2xl font-bold text-green-600">{paymentStats.confirmed_payments}</p>
                  </div>
                  <div className="bg-white rounded-2xl shadow-lg p-6">
                    <p className="text-sm text-gray-500">Pending</p>
                    <p className="text-2xl font-bold text-yellow-600">{paymentStats.pending_payments}</p>
                  </div>
                </div>
              )}

              <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
                <div className="px-6 py-4 bg-gradient-to-r from-green-500 to-green-600">
                  <div className="flex justify-between items-center">
                    <h3 className="text-lg font-semibold text-white">Payment Transactions ({payments.total})</h3>
                    <div className="flex gap-3">
                      <input
                        type="date"
                        value={dateRange.start}
                        onChange={(e) => setDateRange({...dateRange, start: e.target.value})}
                        className="text-sm border-0 rounded-lg px-3 py-2 bg-white/10 text-white"
                      />
                      <input
                        type="date"
                        value={dateRange.end}
                        onChange={(e) => setDateRange({...dateRange, end: e.target.value})}
                        className="text-sm border-0 rounded-lg px-3 py-2 bg-white/10 text-white"
                      />
                    </div>
                  </div>
                </div>
                
                {loading ? (
                  <div className="p-12 text-center">
                    <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-green-500 border-t-transparent"></div>
                    <p className="text-gray-500 mt-2">Loading payments...</p>
                  </div>
                ) : (
                  <>
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">User</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Method</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reference</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">M-Pesa ID</th>
                            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
                          </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                          {(payments.payments || []).map((p, index) => (
                            <tr key={p.id} className="hover:bg-gray-50 transition-colors">
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {formatDate(p.created_at)}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div className="flex items-center">
                                  <div className="w-8 h-8 rounded-full bg-gradient-to-r from-purple-500 to-blue-500 flex items-center justify-center text-white text-xs font-bold mr-2">
                                    {p.user_name?.charAt(0).toUpperCase()}
                                  </div>
                                  <span className="text-sm font-medium text-gray-900">{p.user_name}</span>
                                </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                {formatCurrency(p.amount)}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <div className="flex items-center">
                                  <span className="text-lg mr-1">
                                    {p.method === 'mpesa_lesotho' ? '📱' : 
                                     p.method === 'mpesa' ? '📱' :
                                     p.method === 'ecocash' ? '📲' : '🏦'}
                                  </span>
                                  <span className="text-sm text-gray-600">{p.method?.replace('_', ' ')}</span>
                                </div>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                {p.reference || '-'}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap">
                                <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                                  p.status === 'CONFIRMED' ? 'bg-green-100 text-green-800' :
                                  p.status === 'PENDING' ? 'bg-yellow-100 text-yellow-800' :
                                  'bg-red-100 text-red-800'
                                }`}>
                                  {p.status}
                                </span>
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-xs font-mono text-gray-500">
                                {p.mpesa_transaction_id || '-'}
                              </td>
                              <td className="px-6 py-4 whitespace-nowrap text-sm">
                                <button
                                  onClick={() => {
                                    setSelectedPayment(p);
                                    setShowPaymentDetails(true);
                                  }}
                                  className="text-blue-600 hover:text-blue-800 font-medium"
                                >
                                  Details
                                </button>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    
                    {/* Pagination */}
                    {payments.total > 20 && (
                      <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex items-center justify-between">
                        <button
                          disabled={page.payments <= 1}
                          onClick={() => setPage((p) => ({ ...p, payments: p.payments - 1 }))}
                          className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                        >
                          Previous
                        </button>
                        <span className="text-sm text-gray-700">
                          Page {page.payments} of {Math.ceil(payments.total / 20)}
                        </span>
                        <button
                          disabled={page.payments * 20 >= payments.total}
                          onClick={() => setPage((p) => ({ ...p, payments: p.payments + 1 }))}
                          className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                        >
                          Next
                        </button>
                      </div>
                    )}
                  </>
                )}
              </div>
            </div>
          )}

          {/* Invitations Tab */}
          {activeTab === 'invitations' && (
            <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
              <div className="px-6 py-4 bg-gradient-to-r from-orange-500 to-orange-600">
                <h3 className="text-lg font-semibold text-white">Invitations ({invitations.length})</h3>
              </div>
              
              {/* Invite Form */}
              <div className="p-6 bg-gray-50 border-b border-gray-200">
                <form onSubmit={handleInvite} className="flex gap-4 flex-wrap items-end">
                  <div className="flex-1 min-w-[200px]">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Email Address</label>
                    <input
                      type="email"
                      placeholder="user@example.com"
                      value={inviteEmail}
                      onChange={(e) => setInviteEmail(e.target.value)}
                      className="w-full px-4 py-2 border-2 border-gray-200 rounded-lg focus:border-orange-500 focus:ring focus:ring-orange-200 transition-all"
                      required
                    />
                  </div>
                  <div className="w-48">
                    <label className="block text-sm font-medium text-gray-700 mb-1">Role</label>
                    <select
                      value={inviteRole}
                      onChange={(e) => setInviteRole(e.target.value)}
                      className="w-full px-4 py-2 border-2 border-gray-200 rounded-lg focus:border-orange-500 focus:ring focus:ring-orange-200 transition-all"
                    >
                      <option value="verifier">Verifier</option>
                      <option value="issuer">Issuer</option>
                      <option value="admin">Admin</option>
                    </select>
                  </div>
                  <button
                    type="submit"
                    disabled={inviteLoading}
                    className="px-6 py-2 bg-gradient-to-r from-orange-500 to-orange-600 text-white rounded-lg hover:from-orange-600 hover:to-orange-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all transform hover:scale-105"
                  >
                    {inviteLoading ? (
                      <span className="flex items-center">
                        <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Sending...
                      </span>
                    ) : 'Send Invitation'}
                  </button>
                </form>
              </div>

              {/* Invitations Table */}
              {loading ? (
                <div className="p-12 text-center">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-orange-500 border-t-transparent"></div>
                  <p className="text-gray-500 mt-2">Loading invitations...</p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Email</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Created</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Expires</th>
                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Invitation Link</th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {invitations.map((i, index) => (
                        <tr key={i.id} className="hover:bg-gray-50 transition-colors">
                          <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{i.email}</td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                              i.role === 'issuer' ? 'bg-green-100 text-green-800' : 
                              i.role === 'admin' ? 'bg-purple-100 text-purple-800' :
                              'bg-blue-100 text-blue-800'
                            }`}>
                              {i.role}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
                              i.used 
                                ? 'bg-gray-100 text-gray-800' 
                                : 'bg-green-100 text-green-800'
                            }`}>
                              <span className={`w-2 h-2 rounded-full mr-1 ${i.used ? 'bg-gray-400' : 'bg-green-400 animate-pulse'}`}></span>
                              {i.used ? 'Used' : 'Pending'}
                            </span>
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {formatDate(i.created_at)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                            {formatDate(i.expires_at)}
                          </td>
                          <td className="px-6 py-4 whitespace-nowrap">
                            {!i.used && (
                              <button
                                onClick={() => {
                                  navigator.clipboard.writeText(i.link);
                                  setActionMsg('✅ Link copied to clipboard!');
                                  setTimeout(() => setActionMsg(''), 2000);
                                }}
                                className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                              >
                                Copy Link
                              </button>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          )}

          {/* Logs Tab */}
          {activeTab === 'logs' && (
            <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
              <div className="px-6 py-4 bg-gradient-to-r from-gray-700 to-gray-800">
                <h3 className="text-lg font-semibold text-white">System Audit Logs ({logs.total})</h3>
              </div>
              
              {loading ? (
                <div className="p-12 text-center">
                  <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-gray-700 border-t-transparent"></div>
                  <p className="text-gray-500 mt-2">Loading logs...</p>
                </div>
              ) : (
                <>
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Timestamp</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Event Type</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actor</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Target</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Details</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {(logs.logs || []).map((log, index) => (
                          <tr key={log.id} className="hover:bg-gray-50 transition-colors">
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {formatDate(log.created_at)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                                log.event_type.includes('success') || log.event_type.includes('approved') ? 'bg-green-100 text-green-800' :
                                log.event_type.includes('error') || log.event_type.includes('failed') || log.event_type.includes('rejected') ? 'bg-red-100 text-red-800' :
                                log.event_type.includes('pending') ? 'bg-yellow-100 text-yellow-800' :
                                'bg-blue-100 text-blue-800'
                              }`}>
                                {log.event_type}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                              {log.actor_user_id || 'System'}
                              {log.actor_role && <span className="text-xs text-gray-500 ml-1">({log.actor_role})</span>}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {log.target_user_id || log.certificate_hash || '-'}
                            </td>
                            <td className="px-6 py-4 text-sm text-gray-500 max-w-md">
                              <div className="truncate">
                                {JSON.stringify(log.payload)}
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  
                  {/* Pagination */}
                  {logs.total > 50 && (
                    <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex items-center justify-between">
                      <button
                        disabled={page.logs <= 1}
                        onClick={() => setPage((p) => ({ ...p, logs: p.logs - 1 }))}
                        className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                      >
                        Previous
                      </button>
                      <span className="text-sm text-gray-700">
                        Page {page.logs} of {Math.ceil(logs.total / 50)}
                      </span>
                      <button
                        disabled={page.logs * 50 >= logs.total}
                        onClick={() => setPage((p) => ({ ...p, logs: p.logs + 1 }))}
                        className="px-4 py-2 border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
                      >
                        Next
                      </button>
                    </div>
                  )}
                </>
              )}
            </div>
          )}
        </div>
      </div>

      {/* Animations */}
      <style jsx>{`
        @keyframes slideDown {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .animate-slideDown {
          animation: slideDown 0.3s ease-out;
        }
        
        .animate-slideUp {
          animation: slideUp 0.3s ease-out;
        }
        
        .animate-fadeIn {
          opacity: 0;
          animation: fadeIn 0.5s ease-out forwards;
        }
      `}</style>
    </div>
  );
};

export default AdminDashboard;