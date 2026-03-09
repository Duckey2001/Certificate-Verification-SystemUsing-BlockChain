import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { adminApi, authApi, paymentApi } from '../../api';
import RecentActivity from '../../components/RecentActivity';
import CertificatePreview from '../../components/CertificatePreview';
import PaymentDetails from '../../components/PaymentDetails';
import UserProfileCard from '../../components/UserProfileCard';
import BlockchainVisualization from '../../components/BlockchainVisualization';
import NetworkMonitor from '../../components/NetworkMonitor';
import BlockchainEducation from '../../components/BlockchainEducation';
import AdminStats from '../../components/AdminStats';
import AdminCharts from '../../components/AdminCharts';
import DataTable from '../../components/DataTable';
import NotificationCenter from '../../components/NotificationCenter';
import QuickActions from '../../components/QuickActions';
import SystemHealth from '../SystemHealth';
import UserManagement from '../../components/UserManagement';
import CertificateManagement from '../../components/CertificateManagement';
import VerificationManagement from '../../components/VerificationManagement';
import PaymentManagement from '../../components/PaymentManagement';
// import InvitationManagement from '../../components/InvitationManagement';
// import LogViewer from '../../components/LogViewer';
// import ThemeCustomizer from '../../components/ThemeCustomizer';
import ExportData from '../../components/ExportData';
import { 
  FiHome, 
  FiUsers, 
  FiFileText, 
  FiCheckCircle, 
  FiDollarSign, 
  FiMail, 
  FiActivity, 
  FiBarChart2,
  FiShield,
  FiGlobe,
  FiBook,
  FiSettings,
  FiLogOut,
  FiMenu,
  FiBell,
  FiSearch,
  FiFilter,
  FiDownload,
  FiRefreshCw,
  FiPlus,
  FiTrash2,
  FiEdit,
  FiEye,
  FiLock,
  FiUnlock,
  FiUserCheck,
  FiUserX,
  FiAward,
  FiClock,
  FiTrendingUp,
  FiTrendingDown,
  FiServer,
  FiCpu,
  FiDatabase,
  FiCloud,
  FiZap,
  FiAlertCircle,
  FiCheck,
  FiX
} from 'react-icons/fi';
import { 
  FaBitcoin, 
  FaEthereum, 
  FaGithub, 
  FaTwitter, 
  FaLinkedin,
  FaTelegram,
  FaDiscord,
  FaReddit
} from 'react-icons/fa';
import { motion, AnimatePresence } from 'framer-motion';
import { format, subDays, isWithinInterval, parseISO } from 'date-fns';

const TABS = [
  { id: 'overview', label: 'Overview', icon: FiHome, color: 'purple' },
  { id: 'blockchain', label: 'Blockchain', icon: FaBitcoin, color: 'orange' },
  { id: 'network', label: 'Network', icon: FiGlobe, color: 'blue' },
  { id: 'education', label: 'Education', icon: FiBook, color: 'green' },
  { id: 'users', label: 'Users', icon: FiUsers, color: 'indigo' },
  { id: 'certificates', label: 'Certificates', icon: FiFileText, color: 'yellow' },
  { id: 'verifications', label: 'Verifications', icon: FiCheckCircle, color: 'teal' },
  { id: 'payments', label: 'Payments', icon: FiDollarSign, color: 'pink' },
  { id: 'invitations', label: 'Invitations', icon: FiMail, color: 'cyan' },
  { id: 'logs', label: 'Logs', icon: FiActivity, color: 'gray' }
];

const AdminDashboard = () => {
  const { user, logout } = useAuth();
  const [stats, setStats] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const [showNotifications, setShowNotifications] = useState(false);
  // const [showThemeCustomizer, setShowThemeCustomizer] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({});
  const [dateRange, setDateRange] = useState({
    start: format(subDays(new Date(), 30), 'yyyy-MM-dd'),
    end: format(new Date(), 'yyyy-MM-dd')
  });
  const [refreshInterval, setRefreshInterval] = useState(30000); // 30 seconds
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [theme, setTheme] = useState('light');
  const [chartData, setChartData] = useState(null);
  const [systemHealth, setSystemHealth] = useState(null);
  const [recentAlerts, setRecentAlerts] = useState([]);

  // Load initial data
  useEffect(() => {
    let mounted = true;
    let refreshTimer;

    const fetchInitialData = async () => {
      try {
        setLoading(true);
        
        // Fetch system stats
        const statsData = await adminApi.getSystemStats();
        if (mounted) setStats(statsData);

        // Fetch system health
        const healthData = await adminApi.getSystemHealth();
        if (mounted) setSystemHealth(healthData);

        // Fetch chart data
        const chartData = await adminApi.getDashboardCharts(dateRange);
        if (mounted) setChartData(chartData);

        // Fetch notifications
        const notifData = await adminApi.getNotifications();
        if (mounted) {
          setNotifications(notifData);
          setUnreadCount(notifData.filter(n => !n.read).length);
        }

        // Fetch recent alerts
        const alertsData = await adminApi.getRecentAlerts();
        if (mounted) setRecentAlerts(alertsData);

      } catch (error) {
        console.error('Failed to fetch initial data:', error);
        if (mounted) setError('Failed to load dashboard data');
      } finally {
        if (mounted) setLoading(false);
      }
    };

    fetchInitialData();

    // Set up auto-refresh
    if (autoRefresh) {
      refreshTimer = setInterval(() => {
        fetchInitialData();
      }, refreshInterval);
    }

    return () => {
      mounted = false;
      if (refreshTimer) clearInterval(refreshTimer);
    };
  }, [dateRange, autoRefresh, refreshInterval]);

  // Handle tab change
  const handleTabChange = useCallback((tabId) => {
    setActiveTab(tabId);
    // Reset filters when changing tabs
    setFilters({});
    setSearchQuery('');
  }, []);

  // Handle logout
  const handleLogout = useCallback(async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
      setError('Failed to logout');
    }
  }, [logout]);

  // Mark notification as read
  const markAsRead = useCallback(async (notificationId) => {
    try {
      await adminApi.markNotificationRead(notificationId);
      setNotifications(prev => 
        prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  }, []);

  // Mark all notifications as read
  const markAllAsRead = useCallback(async () => {
    try {
      await adminApi.markAllNotificationsRead();
      setNotifications(prev => prev.map(n => ({ ...n, read: true })));
      setUnreadCount(0);
      setSuccess('All notifications marked as read');
    } catch (error) {
      console.error('Failed to mark all notifications as read:', error);
      setError('Failed to mark notifications as read');
    }
  }, []);

  // Export data
  const handleExport = useCallback(async (format = 'csv') => {
    try {
      const data = await adminApi.exportData(activeTab, filters, dateRange);
      const blob = new Blob([data], { 
        type: format === 'csv' ? 'text/csv' : 'application/json' 
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${activeTab}_export_${format(new Date(), 'yyyy-MM-dd')}.${format}`;
      a.click();
      setSuccess('Data exported successfully');
    } catch (error) {
      console.error('Export failed:', error);
      setError('Failed to export data');
    }
  }, [activeTab, filters, dateRange]);

  // Refresh current tab data
  const refreshData = useCallback(async () => {
    try {
      setLoading(true);
      
      if (activeTab === 'overview') {
        const [statsData, healthData, chartData] = await Promise.all([
          adminApi.getSystemStats(),
          adminApi.getSystemHealth(),
          adminApi.getDashboardCharts(dateRange)
        ]);
        setStats(statsData);
        setSystemHealth(healthData);
        setChartData(chartData);
      }
      
      setSuccess('Data refreshed successfully');
    } catch (error) {
      console.error('Refresh failed:', error);
      setError('Failed to refresh data');
    } finally {
      setLoading(false);
    }
  }, [activeTab, dateRange]);

  // Get status color
  const getStatusColor = useCallback((status) => {
    const colors = {
      success: 'bg-green-100 text-green-800 border-green-200',
      warning: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      error: 'bg-red-100 text-red-800 border-red-200',
      info: 'bg-blue-100 text-blue-800 border-blue-200',
      pending: 'bg-purple-100 text-purple-800 border-purple-200',
      active: 'bg-emerald-100 text-emerald-800 border-emerald-200',
      inactive: 'bg-gray-100 text-gray-800 border-gray-200',
      verified: 'bg-teal-100 text-teal-800 border-teal-200',
      revoked: 'bg-rose-100 text-rose-800 border-rose-200'
    };
    return colors[status?.toLowerCase()] || colors.info;
  }, []);

  // Format currency
  const formatCurrency = useCallback((amount) => {
    return new Intl.NumberFormat('en-LS', {
      style: 'currency',
      currency: 'LSL',
      minimumFractionDigits: 2
    }).format(amount);
  }, []);

  // Format date
  const formatDate = useCallback((date) => {
    if (!date) return 'N/A';
    return format(parseISO(date), 'MMM dd, yyyy HH:mm');
  }, []);

  // Calculate percentage change
  const calculateChange = useCallback((current, previous) => {
    if (!previous || previous === 0) return 100;
    return ((current - previous) / previous) * 100;
  }, []);

  // Get change indicator
  const getChangeIndicator = useCallback((current, previous) => {
    const change = calculateChange(current, previous);
    if (change > 0) {
      return {
        icon: FiTrendingUp,
        color: 'text-green-600',
        text: `+${change.toFixed(1)}%`
      };
    } else if (change < 0) {
      return {
        icon: FiTrendingDown,
        color: 'text-red-600',
        text: `${change.toFixed(1)}%`
      };
    }
    return null;
  }, [calculateChange]);

  // Render overview tab
  const renderOverview = () => (
    <div className="space-y-6">
      {/* Stats Cards */}
      <AdminStats 
        stats={stats}
        loading={loading}
        formatCurrency={formatCurrency}
        getChangeIndicator={getChangeIndicator}
      />

      {/* System Health */}
      <SystemHealth 
        health={systemHealth}
        alerts={recentAlerts}
        loading={loading}
      />

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <AdminCharts 
          data={chartData}
          type="activity"
          title="System Activity"
          loading={loading}
        />
        <AdminCharts 
          data={chartData}
          type="payments"
          title="Payment Trends"
          loading={loading}
        />
      </div>

      {/* Recent Activity & Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <RecentActivity limit={5} />
        </div>
        <div>
          <QuickActions 
            onAction={(action) => {
              switch(action) {
                case 'export':
                  handleExport();
                  break;
                case 'refresh':
                  refreshData();
                  break;
                case 'invite':
                  setActiveTab('invitations');
                  break;
                default:
                  break;
              }
            }}
          />
        </div>
      </div>

      {/* Recent Alerts */}
      {recentAlerts.length > 0 && (
        <div className="bg-white rounded-xl shadow-lg overflow-hidden">
          <div className="px-6 py-4 bg-gradient-to-r from-amber-500 to-orange-600">
            <h3 className="text-lg font-semibold text-white flex items-center">
              <FiAlertCircle className="mr-2" />
              Recent Alerts
            </h3>
          </div>
          <div className="divide-y divide-gray-200">
            {recentAlerts.map((alert, index) => (
              <motion.div
                key={alert.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.1 }}
                className="p-4 hover:bg-gray-50 transition-colors"
              >
                <div className="flex items-start">
                  <div className={`w-2 h-2 rounded-full mt-2 mr-3 ${
                    alert.severity === 'high' ? 'bg-red-500 animate-pulse' :
                    alert.severity === 'medium' ? 'bg-yellow-500' :
                    'bg-blue-500'
                  }`} />
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{alert.message}</p>
                    <p className="text-xs text-gray-500 mt-1">
                      {formatDate(alert.timestamp)}
                    </p>
                  </div>
                  <button
                    onClick={() => {/* Handle alert action */}}
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    View
                  </button>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      )}
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 flex">
        {/* Theme Customizer Modal */}
        {/* <AnimatePresence>
          {showThemeCustomizer && (
            <ThemeCustomizer
              theme={theme}
              onClose={() => setShowThemeCustomizer(false)}
              onThemeChange={setTheme}
            />
          )}
        </AnimatePresence> */}

      {/* Notifications Panel */}
      <AnimatePresence>
        {showNotifications && (
          <NotificationCenter
            notifications={notifications}
            unreadCount={unreadCount}
            onClose={() => setShowNotifications(false)}
            onMarkRead={markAsRead}
            onMarkAllRead={markAllAsRead}
          />
        )}
      </AnimatePresence>

      {/* Left Sidebar */}
      <motion.div
        initial={false}
        animate={{ width: sidebarCollapsed ? 80 : 280 }}
        className="bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 text-white shadow-2xl flex flex-col relative z-20"
      >
        {/* Logo Area */}
        <div className="p-6 border-b border-gray-700/50">
          <motion.div 
            className="flex items-center space-x-4"
            layout
          >
            <motion.div 
              className="relative"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <div className="absolute inset-0 bg-gradient-to-r from-purple-500 to-blue-500 rounded-xl blur-lg opacity-50 animate-pulse" />
              <div className="relative bg-gradient-to-r from-purple-500 to-blue-500 p-3 rounded-xl shadow-lg">
                <FiShield className="w-8 h-8 text-white" />
              </div>
            </motion.div>
            
            <AnimatePresence>
              {!sidebarCollapsed && (
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="overflow-hidden"
                >
                  <h2 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
                    CertiVert
                  </h2>
                  <p className="text-xs text-gray-400 mt-1">Admin Portal</p>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </div>

        {/* Admin Profile */}
        <div className="p-6 border-b border-gray-700/50">
          <motion.div 
            className="flex items-center space-x-4"
            layout
          >
            <motion.div 
              className="relative"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
            >
              <div className="w-12 h-12 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 flex items-center justify-center text-white font-bold text-xl shadow-lg">
                {user?.username?.charAt(0).toUpperCase() || 'A'}
              </div>
              <motion.div 
                className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 border-2 border-gray-800 rounded-full"
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ repeat: Infinity, duration: 2 }}
              />
            </motion.div>
            
            <AnimatePresence>
              {!sidebarCollapsed && (
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="flex-1 overflow-hidden"
                >
                  <p className="font-semibold text-lg truncate">{user?.username || 'Admin'}</p>
                  <p className="text-xs text-gray-400 truncate">{user?.email || 'admin@certivert.com'}</p>
                  <motion.span 
                    className="inline-block mt-2 px-3 py-1 bg-purple-600/30 text-purple-300 rounded-full text-xs font-medium"
                    whileHover={{ scale: 1.05 }}
                  >
                    SUPER ADMIN
                  </motion.span>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        </div>

        {/* Quick Stats (collapsed mode) */}
        {sidebarCollapsed && stats && (
          <div className="p-4 border-b border-gray-700/50">
            <div className="space-y-3">
              <div className="text-center">
                <div className="w-8 h-8 mx-auto bg-purple-600/30 rounded-lg flex items-center justify-center">
                  <FiUsers className="text-purple-400" />
                </div>
                <p className="text-xs text-gray-400 mt-1">{stats.total_users}</p>
              </div>
              <div className="text-center">
                <div className="w-8 h-8 mx-auto bg-blue-600/30 rounded-lg flex items-center justify-center">
                  <FiFileText className="text-blue-400" />
                </div>
                <p className="text-xs text-gray-400 mt-1">{stats.total_certificates}</p>
              </div>
            </div>
          </div>
        )}

        {/* Navigation Tabs */}
        <nav className="flex-1 overflow-y-auto py-6 px-3">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            
            return (
              <motion.button
                key={tab.id}
                onClick={() => handleTabChange(tab.id)}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 mb-1 relative group ${
                  isActive 
                    ? `bg-gradient-to-r from-${tab.color}-600 to-${tab.color}-700 text-white shadow-lg` 
                    : 'text-gray-300 hover:bg-gray-700/50 hover:text-white'
                }`}
                whileHover={{ scale: 1.02, x: 5 }}
                whileTap={{ scale: 0.98 }}
              >
                <Icon className={`w-5 h-5 ${isActive ? 'text-white' : 'text-gray-400 group-hover:text-white'}`} />
                
                <AnimatePresence>
                  {!sidebarCollapsed && (
                    <motion.span
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -10 }}
                      className="font-medium capitalize flex-1 text-left"
                    >
                      {tab.label}
                    </motion.span>
                  )}
                </AnimatePresence>

                {isActive && !sidebarCollapsed && (
                  <motion.div
                    layoutId="activeTab"
                    className="absolute right-3 w-2 h-2 bg-white rounded-full"
                    animate={{ scale: [1, 1.5, 1] }}
                    transition={{ repeat: Infinity, duration: 2 }}
                  />
                )}

                {tab.id === 'users' && pendingUsers?.length > 0 && !sidebarCollapsed && (
                  <motion.span
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="absolute right-3 bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center"
                  >
                    {pendingUsers.length}
                  </motion.span>
                )}
              </motion.button>
            );
          })}
        </nav>

        {/* Bottom Actions */}
        <div className="p-6 border-t border-gray-700/50 space-y-2">
          {/* Notifications */}
          <motion.button
            onClick={() => setShowNotifications(!showNotifications)}
            className="w-full flex items-center space-x-3 px-4 py-3 text-gray-300 hover:text-white hover:bg-gray-700/50 rounded-xl transition-all relative group"
            whileHover={{ scale: 1.02, x: 5 }}
            whileTap={{ scale: 0.98 }}
          >
            <FiBell className="w-5 h-5" />
            {!sidebarCollapsed && (
              <span className="font-medium">Notifications</span>
            )}
            {unreadCount > 0 && (
              <motion.span
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                className={`${sidebarCollapsed ? 'absolute -top-1 -right-1' : 'absolute right-3'} bg-red-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center`}
              >
                {unreadCount}
              </motion.span>
            )}
          </motion.button>

          {/* Theme Customizer */}
          {/* <motion.button
            onClick={() => setShowThemeCustomizer(true)}
            className="w-full flex items-center space-x-3 px-4 py-3 text-gray-300 hover:text-white hover:bg-gray-700/50 rounded-xl transition-all"
            whileHover={{ scale: 1.02, x: 5 }}
            whileTap={{ scale: 0.98 }}
          >
            <FiSettings className="w-5 h-5" />
            {!sidebarCollapsed && <span className="font-medium">Customize</span>}
          </motion.button>

          {/* Logout */}
          <AnimatePresence>
            {!showLogoutConfirm ? (
              <motion.button
                onClick={() => setShowLogoutConfirm(true)}
                className="w-full flex items-center space-x-3 px-4 py-3 text-gray-300 hover:text-white hover:bg-red-600/20 rounded-xl transition-all"
                whileHover={{ scale: 1.02, x: 5 }}
                whileTap={{ scale: 0.98 }}
              >
                <FiLogOut className="w-5 h-5" />
                {!sidebarCollapsed && <span className="font-medium">Logout</span>}
              </motion.button>
            ) : (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                className="bg-gray-800/50 rounded-xl p-4"
              >
                <p className="text-sm text-gray-300 text-center mb-3">Confirm logout?</p>
                <div className="flex space-x-2">
                  <motion.button
                    onClick={handleLogout}
                    className="flex-1 px-3 py-2 bg-red-600 hover:bg-red-700 rounded-lg text-white text-sm font-medium transition-colors"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    Yes
                  </motion.button>
                  <motion.button
                    onClick={() => setShowLogoutConfirm(false)}
                    className="flex-1 px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-white text-sm font-medium transition-colors"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    No
                  </motion.button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Sidebar Toggle */}
          <motion.button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="absolute bottom-6 -right-3 w-8 h-8 bg-gray-800 rounded-full flex items-center justify-center text-white border-2 border-gray-700 hover:bg-gray-700 transition-colors shadow-lg"
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
          >
            <FiMenu className={`w-4 h-4 transform transition-transform ${sidebarCollapsed ? 'rotate-180' : ''}`} />
          </motion.button>
        </div>
      </motion.div>

      {/* Main Content Area */}
      <motion.div 
        className="flex-1 overflow-auto"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.3 }}
      >
        {/* Top Bar */}
        <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-md shadow-sm sticky top-0 z-10 border-b border-gray-200 dark:border-gray-700">
          <div className="px-8 py-4">
            <div className="flex justify-between items-center">
              {/* Title and Breadcrumb */}
              <div>
                <h1 className="text-2xl font-bold text-gray-800 dark:text-white capitalize flex items-center">
                  {TABS.find(t => t.id === activeTab)?.label} Dashboard
                  {loading && (
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
                      className="ml-3"
                    >
                      <FiRefreshCw className="w-4 h-4 text-gray-400" />
                    </motion.div>
                  )}
                </h1>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Welcome back, {user?.username}! Here's what's happening with your system.
                </p>
              </div>

              {/* Search and Actions */}
              <div className="flex items-center space-x-4">
                {/* Search Bar */}
                <div className="relative">
                  <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                  <input
                    type="text"
                    placeholder="Search..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 pr-4 py-2 border-2 border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:border-purple-500 focus:ring focus:ring-purple-200 dark:focus:ring-purple-800 transition-all w-64"
                  />
                </div>

                {/* Filter Button */}
                <motion.button
                  onClick={() => {/* Toggle filters */}}
                  className="p-2 border-2 border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors relative"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <FiFilter className="w-5 h-5 text-gray-600 dark:text-gray-300" />
                  {Object.keys(filters).length > 0 && (
                    <span className="absolute -top-1 -right-1 w-3 h-3 bg-purple-500 rounded-full" />
                  )}
                </motion.button>

                {/* Export Button */}
                <motion.button
                  onClick={() => handleExport('csv')}
                  className="p-2 border-2 border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                >
                  <FiDownload className="w-5 h-5 text-gray-600 dark:text-gray-300" />
                </motion.button>

                {/* Refresh Button */}
                <motion.button
                  onClick={refreshData}
                  className="p-2 border-2 border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  animate={autoRefresh ? { rotate: [0, 360] } : {}}
                  transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                >
                  <FiRefreshCw className="w-5 h-5 text-gray-600 dark:text-gray-300" />
                </motion.button>

                {/* Date Range Selector */}
                <select
                  value={`${dateRange.start}_${dateRange.end}`}
                  onChange={(e) => {
                    const [start, end] = e.target.value.split('_');
                    setDateRange({ start, end });
                  }}
                  className="px-4 py-2 border-2 border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:border-purple-500 focus:ring focus:ring-purple-200 dark:focus:ring-purple-800 transition-all"
                >
                  <option value={`${format(subDays(new Date(), 7), 'yyyy-MM-dd')}_${format(new Date(), 'yyyy-MM-dd')}`}>Last 7 days</option>
                  <option value={`${format(subDays(new Date(), 30), 'yyyy-MM-dd')}_${format(new Date(), 'yyyy-MM-dd')}`}>Last 30 days</option>
                  <option value={`${format(subDays(new Date(), 90), 'yyyy-MM-dd')}_${format(new Date(), 'yyyy-MM-dd')}`}>Last 90 days</option>
                  <option value={`2024-01-01_${format(new Date(), 'yyyy-MM-dd')}`}>Year to date</option>
                </select>

                {/* User Avatar */}
                <motion.div
                  className="relative cursor-pointer"
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.9 }}
                >
                  <div className="w-10 h-10 rounded-full bg-gradient-to-r from-purple-500 to-blue-500 flex items-center justify-center text-white font-bold shadow-lg">
                    {user?.username?.charAt(0).toUpperCase() || 'A'}
                  </div>
                  <motion.div 
                    className="absolute -bottom-1 -right-1 w-3 h-3 bg-green-500 border-2 border-white dark:border-gray-800 rounded-full"
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ repeat: Infinity, duration: 2 }}
                  />
                </motion.div>
              </div>
            </div>

            {/* Active Filters */}
            {Object.keys(filters).length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="mt-4 flex items-center space-x-2"
              >
                <span className="text-sm text-gray-500 dark:text-gray-400">Active filters:</span>
                {Object.entries(filters).map(([key, value]) => (
                  <span
                    key={key}
                    className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200"
                  >
                    {key}: {value}
                    <button
                      onClick={() => {
                        const newFilters = { ...filters };
                        delete newFilters[key];
                        setFilters(newFilters);
                      }}
                      className="ml-2 hover:text-purple-600"
                    >
                      <FiX className="w-3 h-3" />
                    </button>
                  </span>
                ))}
                <button
                  onClick={() => setFilters({})}
                  className="text-sm text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
                >
                  Clear all
                </button>
              </motion.div>
            )}
          </div>
        </div>

        {/* Action Messages */}
        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="mx-8 mt-4 px-6 py-4 rounded-xl bg-gradient-to-r from-red-500 to-red-600 text-white shadow-lg flex items-center"
            >
              <FiAlertCircle className="w-5 h-5 mr-3" />
              {error}
              <button
                onClick={() => setError('')}
                className="ml-auto hover:text-white/80"
              >
                <FiX className="w-5 h-5" />
              </button>
            </motion.div>
          )}

          {success && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="mx-8 mt-4 px-6 py-4 rounded-xl bg-gradient-to-r from-green-500 to-green-600 text-white shadow-lg flex items-center"
            >
              <FiCheck className="w-5 h-5 mr-3" />
              {success}
              <button
                onClick={() => setSuccess('')}
                className="ml-auto hover:text-white/80"
              >
                <FiX className="w-5 h-5" />
              </button>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Content Area */}
        <div className="p-8">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.2 }}
            >
              {/* Overview Tab */}
              {activeTab === 'overview' && renderOverview()}

              {/* Blockchain Tab */}
              {activeTab === 'blockchain' && (
                <BlockchainVisualization 
                  data={chartData?.blockchain}
                  onAction={(action) => console.log('Blockchain action:', action)}
                />
              )}

              {/* Network Monitor Tab */}
              {activeTab === 'network' && (
                <NetworkMonitor 
                  onAlert={(alert) => setRecentAlerts(prev => [alert, ...prev].slice(0, 10))}
                />
              )}

              {/* Education Tab */}
              {activeTab === 'education' && (
                <BlockchainEducation 
                  userRole="admin"
                  onComplete={(module) => console.log('Completed module:', module)}
                />
              )}

              {/* Users Tab */}
              {activeTab === 'users' && (
                <UserManagement
                  filters={filters}
                  searchQuery={searchQuery}
                  dateRange={dateRange}
                  onAction={(action, data) => {
                    switch(action) {
                      case 'edit':
                        // Handle edit
                        break;
                      case 'delete':
                        // Handle delete
                        break;
                      case 'approve':
                        // Handle approve
                        break;
                      case 'reject':
                        // Handle reject
                        break;
                      default:
                        break;
                    }
                  }}
                />
              )}

              {/* Certificates Tab */}
              {activeTab === 'certificates' && (
                <CertificateManagement
                  filters={filters}
                  searchQuery={searchQuery}
                  dateRange={dateRange}
                  onAction={(action, data) => {
                    switch(action) {
                      case 'view':
                        setSelectedCertificate(data);
                        setShowPreview(true);
                        break;
                      case 'revoke':
                        handleRevokeCertificate(data.id);
                        break;
                      case 'verify':
                        // Handle verify
                        break;
                      default:
                        break;
                    }
                  }}
                />
              )}

              {/* Verifications Tab */}
              {activeTab === 'verifications' && (
                <VerificationManagement
                  filters={filters}
                  searchQuery={searchQuery}
                  dateRange={dateRange}
                  onAction={(action, data) => {
                    switch(action) {
                      case 'view':
                        // Handle view
                        break;
                      case 'export':
                        handleExport('csv');
                        break;
                      default:
                        break;
                    }
                  }}
                />
              )}

              {/* Payments Tab */}
              {activeTab === 'payments' && (
                <PaymentManagement
                  filters={filters}
                  searchQuery={searchQuery}
                  dateRange={dateRange}
                  formatCurrency={formatCurrency}
                  onAction={(action, data) => {
                    switch(action) {
                      case 'view':
                        setSelectedPayment(data);
                        setShowPaymentDetails(true);
                        break;
                      case 'refund':
                        // Handle refund
                        break;
                      case 'export':
                        handleExport('csv');
                        break;
                      default:
                        break;
                    }
                  }}
                />
              )}

              {/* Invitations Tab */}
              {activeTab === 'invitations' && (
                <div className="p-6 text-center text-gray-500">
                  <p>Invitation Management component not available</p>
                </div>
                // <InvitationManagement
                //   filters={filters}
                //   searchQuery={searchQuery}
                //   onInvite={(email, role) => {
                //     // Handle invite
                //     console.log('Invite:', email, role);
                //   }}
                //   onCopy={(link) => {
                //     navigator.clipboard.writeText(link);
                //     setSuccess('Link copied to clipboard!');
                //   }}
                // />
              )}

              {/* Logs Tab */}
              {activeTab === 'logs' && (
                <div className="p-6 text-center text-gray-500">
                  <p>Log Viewer component not available</p>
                </div>
                // <LogViewer
                //   filters={filters}
                //   dateRange={dateRange}
                //   onExport={handleExport}
                // />
              )}
            </motion.div>
          </AnimatePresence>
        </div>
      </motion.div>

      {/* Floating Action Button */}
      <motion.button
        className="fixed bottom-8 right-8 w-14 h-14 bg-gradient-to-r from-purple-600 to-blue-600 rounded-full shadow-2xl flex items-center justify-center text-white z-30"
        whileHover={{ scale: 1.1, rotate: 90 }}
        whileTap={{ scale: 0.9 }}
        animate={{ 
          boxShadow: [
            '0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04)',
            '0 25px 50px -12px rgba(0,0,0,0.25)',
            '0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04)'
          ]
        }}
        transition={{ repeat: Infinity, duration: 2 }}
        onClick={() => {
          // Quick action menu
          console.log('FAB clicked');
        }}
      >
        <FiPlus className="w-6 h-6" />
      </motion.button>
    </div>
  );
};

export default AdminDashboard;