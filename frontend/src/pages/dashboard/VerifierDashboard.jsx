import React, { useEffect, useMemo, useState, useCallback, useRef } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { useTheme } from '../../contexts/ThemeContext';
import { certificateApi, paymentApi } from '../../api';
import pdfProcessor from '../../services/pdfProcessor';
import RecentActivity from '../../components/RecentActivity';
import CertificatePreview from '../../components/CertificatePreview';
import PaymentModal from '../../components/PaymentModal';
import OCRSidebar from '../../components/OCRSidebar';
import CertificateScanner from '../../components/CertificateScanner';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  FiCheckCircle, 
  FiXCircle, 
  FiClock, 
  FiDollarSign,
  FiFileText,
  FiUpload,
  FiCamera,
  FiSearch,
  FiFilter,
  FiDownload,
  FiShare2,
  FiPrinter,
  FiEye,
  FiStar,
  FiTrendingUp,
  FiTrendingDown,
  FiAward,
  FiAlertCircle,
  FiCheck,
  FiX,
  FiMenu,
  FiBell,
  FiLogOut,
  FiHome,
  FiBarChart2,
  FiList,
  FiSettings,
  FiRefreshCw,
  FiCopy,
  FiExternalLink,
  FiQrCode
} from 'react-icons/fi';
import { FaQrcode, FaBarcode, FaRegCreditCard, FaRegClock, FaRegCheckCircle, FaRegTimesCircle } from 'react-icons/fa';
import { QRCodeCanvas } from 'qrcode.react';
import { format, subDays, parseISO } from 'date-fns';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

const VerifierDashboard = () => {
  const { user, logout } = useAuth();
  const { darkMode, toggleTheme } = useTheme();
  const [verifierStats, setVerifierStats] = useState(null);
  const [history, setHistory] = useState([]);
  const [certificateHash, setCertificateHash] = useState('');
  const [file, setFile] = useState(null);
  const [verificationMode, setVerificationMode] = useState('both');
  const [paymentMethod, setPaymentMethod] = useState('mpesa_lesotho');
  const [paymentDigits, setPaymentDigits] = useState('');
  const [loading, setLoading] = useState(false);
  const [uploadPct, setUploadPct] = useState(0);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);
  
  // OCR state
  const [extractedData, setExtractedData] = useState(null);
  const [extractedDisplay, setExtractedDisplay] = useState(null);
  const [ocrLoading, setOcrLoading] = useState(false);
  const [ocrError, setOcrError] = useState('');
  const [showOcrSidebar, setShowOcrSidebar] = useState(false);
  const [ocrConfidence, setOcrConfidence] = useState(null);
  const [showScanner, setShowScanner] = useState(false);
  const [ocrHistory, setOcrHistory] = useState([]);
  
  // Payment state
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [pendingPayment, setPendingPayment] = useState(null);
  const [paymentHistory, setPaymentHistory] = useState([]);
  const [paymentStats, setPaymentStats] = useState(null);
  const [selectedCertificate, setSelectedCertificate] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  
  // QR Code state
  const [showQR, setShowQR] = useState(false);
  const [qrData, setQrData] = useState('');
  
  // UI state
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const [actionMsg, setActionMsg] = useState({ type: '', text: '' });
  const [activeView, setActiveView] = useState('verify');
  const [compactMode, setCompactMode] = useState(false);
  const [dateRange, setDateRange] = useState({
    start: format(subDays(new Date(), 30), 'yyyy-MM-dd'),
    end: format(new Date(), 'yyyy-MM-dd')
  });
  const [filters, setFilters] = useState({
    status: 'all',
    paymentMethod: 'all'
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('date_desc');
  const [chartData, setChartData] = useState(null);
  const [showNotifications, setShowNotifications] = useState(false);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [realtimeUpdates, setRealtimeUpdates] = useState([]);
  
  const fileInputRef = useRef(null);
  const [wsConnection, setWsConnection] = useState(null);

  // Initialize WebSocket connection
  useEffect(() => {
    if (user) {
      const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';
      const ws = new WebSocket(`${wsUrl}/api/ws/verifier/${user.id}`);
      
      ws.onopen = () => {
        console.log('WebSocket connected');
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        handleRealtimeUpdate(data);
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
      
      setWsConnection(ws);
      
      return () => {
        ws.close();
      };
    }
  }, [user]);

  // Handle real-time updates
  const handleRealtimeUpdate = (data) => {
    switch(data.type) {
      case 'verification_complete':
        setRealtimeUpdates(prev => [{
          id: Date.now(),
          message: `Certificate ${data.verified ? 'verified' : 'failed'}: ${data.hash?.slice(0, 12)}...`,
          timestamp: new Date().toISOString(),
          type: data.verified ? 'success' : 'error'
        }, ...prev].slice(0, 10));
        fetchVerificationHistory();
        fetchVerifierStats();
        break;
        
      case 'payment_confirmed':
        setRealtimeUpdates(prev => [{
          id: Date.now(),
          message: `Payment confirmed: M${data.amount}`,
          timestamp: new Date().toISOString(),
          type: 'success'
        }, ...prev].slice(0, 10));
        fetchPaymentHistory();
        fetchPaymentStats();
        break;
        
      default:
        break;
    }
  };

  // Load initial data
  useEffect(() => {
    let mounted = true;
    let refreshTimer;

    const fetchInitialData = async () => {
      try {
        const [stats, history, payments, paymentStats, notifs, chartData] = await Promise.all([
          certificateApi.getMyVerifierStats(),
          certificateApi.getMyVerifications(50),
          paymentApi.getMyPayments(),
          paymentApi.getVerifierPaymentStats(dateRange),
          certificateApi.getNotifications(),
          certificateApi.getVerificationChartData(dateRange)
        ]);
        
        if (mounted) {
          setVerifierStats(stats);
          setHistory(history || []);
          setPaymentHistory(payments || []);
          setPaymentStats(paymentStats);
          setNotifications(notifs || []);
          setUnreadCount(notifs?.filter(n => !n.read).length || 0);
          setChartData(chartData);
        }
      } catch (error) {
        console.error('Failed to fetch initial data:', error);
        showNotification('error', 'Failed to load dashboard data');
      }
    };
    
    fetchInitialData();

    // Auto-refresh
    if (mounted) {
      refreshTimer = setInterval(() => {
        fetchInitialData();
      }, 30000);
    }

    return () => {
      mounted = false;
      if (refreshTimer) clearInterval(refreshTimer);
    };
  }, [dateRange]);

  // Show notification
  const showNotification = (type, text) => {
    setActionMsg({ type, text });
    setTimeout(() => setActionMsg({ type: '', text: '' }), 5000);
  };

  // Handle file upload and OCR extraction
  const handleFileUpload = async (file) => {
    setFile(file);
    if (!file) {
      setExtractedData(null);
      setExtractedDisplay(null);
      setShowOcrSidebar(false);
      return;
    }

    setOcrLoading(true);
    setOcrError('');
    setExtractedDisplay(null);
    
    try {
      // Process PDF with OCR
      const pdfResult = await pdfProcessor.processCertificate(file, (progress) => {
        setUploadPct(progress);
      });
      
      if (pdfResult.success) {
        const data = pdfResult.data;
        setExtractedData(data);
        
        // Create display HTML
        const displayHtml = `
          <div class="ocr-result">
            <div class="ocr-header">
              <h3>Extracted Certificate Data</h3>
              <div class="confidence-score ${data.confidence > 80 ? 'high' : data.confidence > 60 ? 'medium' : 'low'}">
                Confidence: ${data.confidence}%
              </div>
            </div>
            <div class="ocr-content">
              <div class="data-grid">
                <div class="data-item">
                  <label>Student Name</label>
                  <value>${data.studentName || 'Not found'}</value>
                </div>
                <div class="data-item">
                  <label>Student ID</label>
                  <value>${data.studentId || 'Not found'}</value>
                </div>
                <div class="data-item">
                  <label>Institution</label>
                  <value>${data.institution || 'Not found'}</value>
                </div>
                <div class="data-item">
                  <label>Issue Date</label>
                  <value>${data.issueDate || 'Not found'}</value>
                </div>
                <div class="data-item">
                  <label>Certificate Number</label>
                  <value>${data.certificateNumber || 'Not found'}</value>
                </div>
                <div class="data-item full-width">
                  <label>Certificate Hash</label>
                  <value class="hash">${data.certificateHash || 'Not found'}</value>
                </div>
              </div>
              ${data.subjects && data.subjects.length > 0 ? `
                <div class="subjects-section">
                  <h4>Subjects</h4>
                  <table class="subjects-table">
                    <thead>
                      <tr>
                        <th>Subject</th>
                        <th>Grade</th>
                      </tr>
                    </thead>
                    <tbody>
                      ${data.subjects.map(s => `
                        <tr>
                          <td>${s.name}</td>
                          <td class="grade-${s.grade}">${s.grade}</td>
                        </tr>
                      `).join('')}
                    </tbody>
                  </table>
                </div>
              ` : ''}
            </div>
          </div>
        `;
        
        setExtractedDisplay(displayHtml);
        setOcrConfidence(data.confidence);
        setShowOcrSidebar(true);
        
        // Auto-fill certificate hash if extracted
        if (data.certificateHash) {
          setCertificateHash(data.certificateHash);
        }
        
        // Add to OCR history
        setOcrHistory(prev => [{
          id: Date.now(),
          filename: file.name,
          timestamp: new Date().toISOString(),
          confidence: data.confidence,
          studentName: data.studentName,
          success: true
        }, ...prev].slice(0, 20));
        
        showNotification('success', '✅ Certificate processed successfully! Review extracted data.');
      } else {
        throw new Error(pdfResult.error);
      }
    } catch (err) {
      setOcrError('Failed to process certificate: ' + err.message);
      
      // Add failed OCR to history
      setOcrHistory(prev => [{
        id: Date.now(),
        filename: file.name,
        timestamp: new Date().toISOString(),
        error: err.message,
        success: false
      }, ...prev].slice(0, 20));
    } finally {
      setOcrLoading(false);
      setUploadPct(0);
    }
  };

  // Handle scanner capture
  const handleScannerCapture = async (imageFile) => {
    setShowScanner(false);
    await handleFileUpload(imageFile);
  };

  // Clear OCR data
  const handleClearOcr = () => {
    setExtractedData(null);
    setExtractedDisplay(null);
    setShowOcrSidebar(false);
    setFile(null);
    setCertificateHash('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Check payment requirement before verification
  const checkPaymentRequirement = async () => {
    try {
      const response = await paymentApi.checkPaymentRequired();
      if (response.required) {
        setPendingPayment(response);
        setShowPaymentModal(true);
        return false;
      }
      return true;
    } catch (err) {
      setError('Failed to check payment status');
      return false;
    }
  };

  // Handle payment completion
  const handlePaymentComplete = async (paymentResult) => {
    setShowPaymentModal(false);
    setPendingPayment(null);
    
    if (paymentResult.success) {
      showNotification('success', '✅ Payment successful! You can now verify certificates.');
      fetchPaymentHistory();
      fetchPaymentStats();
    } else {
      setError('Payment failed. Please try again.');
    }
  };

  // Handle verification
  const handleVerify = async (e) => {
    e.preventDefault();
    
    // Check payment requirement first
    const canProceed = await checkPaymentRequirement();
    if (!canProceed) return;
    
    setError('');
    setResult(null);
    setUploadPct(0);
    setLoading(true);

    try {
      const formData = new FormData();
      
      if (verificationMode === 'hash' || verificationMode === 'both') {
        formData.append('certificate_hash', certificateHash.trim());
      }
      
      if (verificationMode === 'file' || verificationMode === 'both') {
        if (file) {
          formData.append('file', file);
        }
      }

      formData.append('payment_method', paymentMethod);
      if (paymentDigits) {
        formData.append('payment_digits', paymentDigits);
      }

      const data = await certificateApi.verifyCertificate(formData, (progress) => {
        setUploadPct(progress);
      });
      
      setResult(data);
      
      // Generate QR code for valid certificate
      if (data.verified && data.certificate_hash) {
        setQrData(data.certificate_hash);
        setShowQR(true);
        setTimeout(() => setShowQR(false), 5000);
      }
      
      showNotification(
        data.verified ? 'success' : 'error',
        data.verified ? '✅ Certificate verified successfully!' : '⚠️ Certificate verification failed'
      );
      
      // Refresh data
      fetchVerificationHistory();
      fetchVerifierStats();
      fetchPaymentHistory();
      
    } catch (err) {
      const detail = err?.response?.data?.detail;
      if (typeof detail === 'string') setError(detail);
      else if (Array.isArray(detail)) setError(detail.map((d) => d.msg).join(', '));
      else setError(err?.message || 'Verification failed');
    } finally {
      setLoading(false);
    }
  };

  // Handle logout
  const handleLogout = async () => {
    try {
      if (wsConnection) {
        wsConnection.close();
      }
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  // Fetch data functions
  const fetchVerifierStats = useCallback(async () => {
    try {
      const stats = await certificateApi.getMyVerifierStats(dateRange);
      setVerifierStats(stats);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  }, [dateRange]);

  const fetchVerificationHistory = useCallback(async () => {
    try {
      const history = await certificateApi.getMyVerifications(50, {
        status: filters.status !== 'all' ? filters.status : undefined,
        payment_method: filters.paymentMethod !== 'all' ? filters.paymentMethod : undefined,
        search: searchTerm || undefined,
        start_date: dateRange.start,
        end_date: dateRange.end,
        sort: sortBy
      });
      setHistory(history || []);
    } catch (error) {
      console.error('Failed to fetch history:', error);
    }
  }, [filters, searchTerm, dateRange, sortBy]);

  const fetchPaymentHistory = useCallback(async () => {
    try {
      const payments = await paymentApi.getMyPayments();
      setPaymentHistory(payments || []);
    } catch (error) {
      console.error('Failed to fetch payment history:', error);
    }
  }, []);

  const fetchPaymentStats = useCallback(async () => {
    try {
      const stats = await paymentApi.getVerifierPaymentStats(dateRange);
      setPaymentStats(stats);
    } catch (error) {
      console.error('Failed to fetch payment stats:', error);
    }
  }, [dateRange]);

  // Mark notification as read
  const markAsRead = async (notificationId) => {
    try {
      await certificateApi.markNotificationRead(notificationId);
      setNotifications(prev => 
        prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  // Export verification history
  const handleExport = async (format = 'csv') => {
    try {
      const data = await certificateApi.exportVerifications({
        format,
        status: filters.status !== 'all' ? filters.status : undefined,
        start_date: dateRange.start,
        end_date: dateRange.end
      });
      
      const blob = new Blob([data], { 
        type: format === 'csv' ? 'text/csv' : 'application/json' 
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `verifications_${format(new Date(), 'yyyy-MM-dd')}.${format}`;
      a.click();
      
      showNotification('success', '✅ Verifications exported successfully');
    } catch (error) {
      showNotification('error', 'Failed to export verifications');
    }
  };

  // Filter history
  const filteredHistory = useMemo(() => {
    let filtered = [...history];
    
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(v => 
        v.certificate_hash?.toLowerCase().includes(term) ||
        v.student_name?.toLowerCase().includes(term) ||
        v.certificate_number?.toLowerCase().includes(term)
      );
    }
    
    switch(sortBy) {
      case 'date_desc':
        filtered.sort((a, b) => new Date(b.verification_date) - new Date(a.verification_date));
        break;
      case 'date_asc':
        filtered.sort((a, b) => new Date(a.verification_date) - new Date(b.verification_date));
        break;
      case 'amount_desc':
        filtered.sort((a, b) => (b.verification_fee || 0) - (a.verification_fee || 0));
        break;
      case 'amount_asc':
        filtered.sort((a, b) => (a.verification_fee || 0) - (b.verification_fee || 0));
        break;
      default:
        break;
    }
    
    return filtered;
  }, [history, searchTerm, sortBy]);

  const canSubmit = useMemo(() => {
    const hasHash = certificateHash.trim().length > 0;
    const hasFile = !!file;
    
    if (verificationMode === 'hash') {
      return hasHash && !loading;
    } else if (verificationMode === 'file') {
      return hasFile && !loading;
    } else {
      return hasHash && hasFile && !loading;
    }
  }, [certificateHash, file, loading, verificationMode]);

  const getPaymentIcon = (method) => {
    switch(method) {
      case 'mpesa_lesotho': return '📱';
      case 'mpesa': return '📱';
      case 'ecocash': return '📲';
      case 'bank': return '🏦';
      default: return '💳';
    }
  };

  const getResultColor = (result) => {
    return result === 'verified' || result === true 
      ? 'bg-green-100 text-green-800 border-green-200' 
      : 'bg-red-100 text-red-800 border-red-200';
  };

  const getResultIcon = (result) => {
    return result === 'verified' || result === true 
      ? <FiCheckCircle className="text-green-600" />
      : <FiXCircle className="text-red-600" />;
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 80) return 'text-green-600';
    if (confidence >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return format(parseISO(dateString), 'MMM dd, yyyy HH:mm');
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-LS', {
      style: 'currency',
      currency: 'LSL'
    }).format(amount || 0);
  };

  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1
      }
    }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1
    }
  };

  const sidebarVariants = {
    expanded: { width: 280 },
    collapsed: { width: 80 }
  };

  return (
    <div className={`min-h-screen ${darkMode ? 'dark' : ''}`}>
      <div className="flex bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
        
        {/* QR Code Modal */}
        <AnimatePresence>
          {showQR && qrData && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
              onClick={() => setShowQR(false)}
            >
              <motion.div
                initial={{ scale: 0.9, y: 20 }}
                animate={{ scale: 1, y: 0 }}
                exit={{ scale: 0.9, y: 20 }}
                className="bg-white dark:bg-gray-800 rounded-2xl p-8 max-w-md w-full mx-4"
                onClick={e => e.stopPropagation()}
              >
                <h3 className="text-xl font-bold text-gray-800 dark:text-white mb-4">
                  Verified Certificate QR Code
                </h3>
                <div className="bg-white p-4 rounded-xl flex justify-center">
                  <QRCodeCanvas
                    value={qrData}
                    size={200}
                    level="H"
                    includeMargin={true}
                    bgColor="#ffffff"
                    fgColor="#000000"
                  />
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400 text-center mt-4">
                  Scan to verify certificate authenticity
                </p>
                <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                  <p className="text-xs text-green-700 dark:text-green-400 break-all">
                    Hash: {qrData}
                  </p>
                </div>
                <button
                  onClick={() => {
                    navigator.clipboard.writeText(qrData);
                    showNotification('success', 'Hash copied to clipboard');
                  }}
                  className="mt-4 w-full px-4 py-2 bg-gradient-to-r from-green-500 to-blue-600 text-white rounded-xl hover:from-green-600 hover:to-blue-700"
                >
                  Copy Hash
                </button>
                <button
                  onClick={() => setShowQR(false)}
                  className="mt-2 w-full px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-xl hover:bg-gray-200 dark:hover:bg-gray-600"
                >
                  Close
                </button>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Modals */}
        <AnimatePresence>
          {showPaymentModal && pendingPayment && (
            <PaymentModal
              amount={pendingPayment.amount}
              currency={pendingPayment.currency}
              onClose={() => setShowPaymentModal(false)}
              onComplete={handlePaymentComplete}
              paymentMethods={[
                { id: 'mpesa_lesotho', name: 'M-Pesa Lesotho', icon: '📱' },
                { id: 'mpesa', name: 'M-Pesa', icon: '📱' },
                { id: 'ecocash', name: 'EcoCash', icon: '📲' },
                { id: 'bank', name: 'Bank Transfer', icon: '🏦' }
              ]}
            />
          )}

          {showPreview && selectedCertificate && (
            <CertificatePreview
              certificate={selectedCertificate}
              onClose={() => {
                setShowPreview(false);
                setSelectedCertificate(null);
              }}
              onVerify={() => {
                setCertificateHash(selectedCertificate.certificate_hash);
                setShowPreview(false);
                setActiveView('verify');
              }}
              onShare={() => {
                navigator.share?.({
                  title: 'Certificate',
                  text: `Certificate for ${selectedCertificate.student_name}`,
                  url: `${window.location.origin}/verify/${selectedCertificate.certificate_hash}`
                });
              }}
            />
          )}

          {showScanner && (
            <CertificateScanner
              onCapture={handleScannerCapture}
              onClose={() => setShowScanner(false)}
              onError={(error) => setOcrError(error)}
            />
          )}
        </AnimatePresence>

        {/* OCR Sidebar */}
        <AnimatePresence>
          {showOcrSidebar && extractedDisplay && (
            <OCRSidebar
              displayHtml={extractedDisplay}
              extractedData={extractedData}
              confidence={ocrConfidence}
              isLoading={ocrLoading}
              onClose={() => setShowOcrSidebar(false)}
              onClear={handleClearOcr}
              onAccept={() => {
                setShowOcrSidebar(false);
                showNotification('success', 'OCR data accepted');
              }}
              onRetry={() => {
                if (file) {
                  handleFileUpload(file);
                }
              }}
            />
          )}
        </AnimatePresence>

        {/* Notifications Panel */}
        <AnimatePresence>
          {showNotifications && (
            <motion.div
              initial={{ opacity: 0, x: 300 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 300 }}
              className="fixed right-0 top-0 h-full w-80 bg-white dark:bg-gray-800 shadow-2xl z-40 overflow-y-auto"
            >
              <div className="p-6">
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-lg font-bold text-gray-800 dark:text-white">
                    Notifications
                  </h3>
                  <button
                    onClick={() => setShowNotifications(false)}
                    className="text-gray-500 hover:text-gray-700 dark:text-gray-400"
                  >
                    <FiX className="w-5 h-5" />
                  </button>
                </div>
                
                {unreadCount > 0 && (
                  <button
                    onClick={async () => {
                      await Promise.all(notifications.map(n => markAsRead(n.id)));
                    }}
                    className="mb-4 text-sm text-blue-600 hover:text-blue-800"
                  >
                    Mark all as read
                  </button>
                )}
                
                <div className="space-y-4">
                  {notifications.length === 0 ? (
                    <p className="text-center text-gray-500 py-8">
                      No notifications
                    </p>
                  ) : (
                    notifications.map((notif) => (
                      <motion.div
                        key={notif.id}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        className={`p-4 rounded-lg cursor-pointer ${
                          notif.read ? 'bg-gray-50 dark:bg-gray-700/50' : 'bg-blue-50 dark:bg-blue-900/20'
                        }`}
                        onClick={() => markAsRead(notif.id)}
                      >
                        <p className="text-sm text-gray-800 dark:text-white">
                          {notif.message}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                          {format(parseISO(notif.created_at), 'MMM dd, HH:mm')}
                        </p>
                      </motion.div>
                    ))
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Left Sidebar */}
        <motion.div
          variants={sidebarVariants}
          animate={sidebarCollapsed ? 'collapsed' : 'expanded'}
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
                <div className="absolute inset-0 bg-gradient-to-r from-red-500 to-orange-500 rounded-xl blur-lg opacity-50 animate-pulse" />
                <div className="relative bg-gradient-to-r from-red-500 to-orange-500 p-3 rounded-xl shadow-lg">
                  <FiCheckCircle className="w-8 h-8 text-white" />
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
                    <h2 className="text-2xl font-bold bg-gradient-to-r from-red-400 to-orange-400 bg-clip-text text-transparent">
                      CertiVert
                    </h2>
                    <p className="text-xs text-gray-400 mt-1">Verifier Portal</p>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          </div>

          {/* User Profile */}
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
                <div className="w-12 h-12 rounded-full bg-gradient-to-r from-red-500 to-orange-500 flex items-center justify-center text-white font-bold text-xl shadow-lg">
                  {user?.username?.charAt(0).toUpperCase() || 'V'}
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
                    <p className="font-semibold text-lg truncate">{user?.username || 'Verifier'}</p>
                    <p className="text-xs text-gray-400 truncate">{user?.email || 'verifier@example.com'}</p>
                    <div className="flex items-center mt-2 space-x-2">
                      <span className="px-2 py-1 bg-red-600/30 text-red-300 rounded-full text-xs font-medium">
                        VERIFIER
                      </span>
                      {user?.institution && (
                        <span className="px-2 py-1 bg-orange-600/30 text-orange-300 rounded-full text-xs font-medium truncate max-w-[100px]">
                          {user.institution}
                        </span>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          </div>

          {/* Quick Stats */}
          {!sidebarCollapsed && verifierStats && (
            <div className="p-4 border-b border-gray-700/50">
              <h4 className="text-xs uppercase tracking-wider text-gray-400 mb-3 flex items-center">
                <span className="w-1 h-4 bg-red-500 rounded-full mr-2"></span>
                Today's Summary
              </h4>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-gray-800/50 rounded-lg p-3">
                  <p className="text-xs text-gray-400">Verified</p>
                  <p className="text-xl font-bold text-green-400">{verifierStats?.today?.verified || 0}</p>
                </div>
                <div className="bg-gray-800/50 rounded-lg p-3">
                  <p className="text-xs text-gray-400">Fees</p>
                  <p className="text-xl font-bold text-yellow-400">
                    {formatCurrency(verifierStats?.today?.fees || 0)}
                  </p>
                </div>
                <div className="bg-gray-800/50 rounded-lg p-3 col-span-2">
                  <p className="text-xs text-gray-400 mb-1">Verification Rate</p>
                  <div className="flex items-center">
                    <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
                      <motion.div 
                        className="h-full bg-gradient-to-r from-green-500 to-green-400 rounded-full"
                        initial={{ width: 0 }}
                        animate={{ width: `${verifierStats?.total > 0 ? (verifierStats.valid / verifierStats.total) * 100 : 0}%` }}
                        transition={{ duration: 1 }}
                      />
                    </div>
                    <span className="text-xs text-gray-300 ml-2">
                      {verifierStats?.total > 0 ? Math.round((verifierStats.valid / verifierStats.total) * 100) : 0}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Navigation */}
          <nav className="flex-1 overflow-y-auto py-6 px-4">
            <motion.div 
              className="space-y-2"
              variants={containerVariants}
              initial="hidden"
              animate="visible"
            >
              <motion.button
                variants={itemVariants}
                onClick={() => setActiveView('verify')}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 relative group ${
                  activeView === 'verify'
                    ? 'bg-gradient-to-r from-red-600 to-orange-600 text-white shadow-lg transform scale-105'
                    : 'text-gray-300 hover:bg-gray-700/50 hover:text-white'
                }`}
                whileHover={{ x: 5 }}
                whileTap={{ scale: 0.98 }}
              >
                <FiCheckCircle className="w-5 h-5" />
                <AnimatePresence>
                  {!sidebarCollapsed && (
                    <motion.span
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -10 }}
                      className="font-medium"
                    >
                      Verify Certificate
                    </motion.span>
                  )}
                </AnimatePresence>
                {activeView === 'verify' && !sidebarCollapsed && (
                  <motion.div
                    layoutId="activeTab"
                    className="absolute right-3 w-2 h-2 bg-white rounded-full"
                    animate={{ scale: [1, 1.5, 1] }}
                    transition={{ repeat: Infinity, duration: 2 }}
                  />
                )}
              </motion.button>

              <motion.button
                variants={itemVariants}
                onClick={() => setActiveView('history')}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                  activeView === 'history'
                    ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg transform scale-105'
                    : 'text-gray-300 hover:bg-gray-700/50 hover:text-white'
                }`}
                whileHover={{ x: 5 }}
                whileTap={{ scale: 0.98 }}
              >
                <FiList className="w-5 h-5" />
                <AnimatePresence>
                  {!sidebarCollapsed && (
                    <motion.span
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -10 }}
                      className="font-medium"
                    >
                      History
                    </motion.span>
                  )}
                </AnimatePresence>
                {history.length > 0 && !sidebarCollapsed && (
                  <span className="ml-auto bg-white/20 px-2 py-0.5 rounded-full text-xs">
                    {history.length}
                  </span>
                )}
              </motion.button>

              <motion.button
                variants={itemVariants}
                onClick={() => setActiveView('payments')}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                  activeView === 'payments'
                    ? 'bg-gradient-to-r from-green-600 to-emerald-600 text-white shadow-lg transform scale-105'
                    : 'text-gray-300 hover:bg-gray-700/50 hover:text-white'
                }`}
                whileHover={{ x: 5 }}
                whileTap={{ scale: 0.98 }}
              >
                <FiDollarSign className="w-5 h-5" />
                <AnimatePresence>
                  {!sidebarCollapsed && (
                    <motion.span
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -10 }}
                      className="font-medium"
                    >
                      Payments
                    </motion.span>
                  )}
                </AnimatePresence>
              </motion.button>

              <motion.button
                variants={itemVariants}
                onClick={() => setActiveView('stats')}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                  activeView === 'stats'
                    ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg transform scale-105'
                    : 'text-gray-300 hover:bg-gray-700/50 hover:text-white'
                }`}
                whileHover={{ x: 5 }}
                whileTap={{ scale: 0.98 }}
              >
                <FiBarChart2 className="w-5 h-5" />
                <AnimatePresence>
                  {!sidebarCollapsed && (
                    <motion.span
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -10 }}
                      className="font-medium"
                    >
                      Statistics
                    </motion.span>
                  )}
                </AnimatePresence>
              </motion.button>
            </motion.div>
          </nav>

          {/* Institution Info */}
          <AnimatePresence>
            {!sidebarCollapsed && user?.institution && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
                className="px-4 py-3 mx-4 mb-4 bg-gray-800/50 rounded-xl"
              >
                <p className="text-xs text-gray-400 mb-1">Institution</p>
                <p className="text-sm font-medium text-white">{user.institution}</p>
                <div className="mt-2 flex items-center">
                  <span className="text-xs text-gray-400">Verifications today:</span>
                  <span className="ml-2 text-sm font-bold text-green-400">
                    {verifierStats?.today?.verified || 0}
                  </span>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Logout Section */}
          <div className="p-6 border-t border-gray-700/50">
            <AnimatePresence mode="wait">
              {!showLogoutConfirm ? (
                <motion.button
                  key="logout"
                  onClick={() => setShowLogoutConfirm(true)}
                  className="w-full flex items-center space-x-3 px-4 py-3 text-gray-300 hover:text-white hover:bg-red-600/20 rounded-xl transition-all duration-200 group"
                  whileHover={{ scale: 1.02, x: 5 }}
                  whileTap={{ scale: 0.98 }}
                >
                  <FiLogOut className="w-5 h-5" />
                  <AnimatePresence>
                    {!sidebarCollapsed && (
                      <motion.span
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -10 }}
                        className="font-medium"
                      >
                        Logout
                      </motion.span>
                    )}
                  </AnimatePresence>
                </motion.button>
              ) : (
                <motion.div
                  key="confirm"
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
                {/* Title */}
                <div>
                  <h1 className="text-2xl font-bold text-gray-800 dark:text-white capitalize flex items-center">
                    {activeView === 'verify' && 'Verify Certificate'}
                    {activeView === 'history' && 'Verification History'}
                    {activeView === 'payments' && 'Payment History'}
                    {activeView === 'stats' && 'Statistics & Analytics'}
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
                    {activeView === 'verify' && 'Verify LGCSE certificates with OCR and blockchain'}
                    {activeView === 'history' && `View your verification history (${filteredHistory.length} total)`}
                    {activeView === 'payments' && `Track your payments and earnings`}
                    {activeView === 'stats' && 'Analytics and performance metrics'}
                  </p>
                </div>

                {/* Actions */}
                <div className="flex items-center space-x-4">
                  {/* Search (for history view) */}
                  {activeView === 'history' && (
                    <div className="relative">
                      <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                      <input
                        type="text"
                        placeholder="Search by hash or name..."
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                        className="pl-10 pr-4 py-2 border-2 border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:border-red-500 focus:ring focus:ring-red-200 dark:focus:ring-red-800 transition-all w-64"
                      />
                    </div>
                  )}

                  {/* Sort Dropdown */}
                  {activeView === 'history' && (
                    <select
                      value={sortBy}
                      onChange={(e) => setSortBy(e.target.value)}
                      className="px-3 py-2 border-2 border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:border-red-500 focus:ring focus:ring-red-200 dark:focus:ring-red-800 transition-all"
                    >
                      <option value="date_desc">Newest First</option>
                      <option value="date_asc">Oldest First</option>
                      <option value="amount_desc">Highest Fee</option>
                      <option value="amount_asc">Lowest Fee</option>
                    </select>
                  )}

                  {/* Export Button */}
                  {activeView === 'history' && (
                    <motion.button
                      onClick={() => handleExport('csv')}
                      className="p-2 border-2 border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                    >
                      <FiDownload className="w-5 h-5 text-gray-600 dark:text-gray-300" />
                    </motion.button>
                  )}

                  {/* Notifications Bell */}
                  <motion.button
                    onClick={() => setShowNotifications(!showNotifications)}
                    className="relative p-2 border-2 border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    <FiBell className="w-5 h-5 text-gray-600 dark:text-gray-300" />
                    {unreadCount > 0 && (
                      <motion.span
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center"
                      >
                        {unreadCount}
                      </motion.span>
                    )}
                  </motion.button>

                  {/* Dark Mode Toggle */}
                  <motion.button
                    onClick={toggleTheme}
                    className="p-2 border-2 border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                  >
                    {darkMode ? '☀️' : '🌙'}
                  </motion.button>

                  {/* User Avatar */}
                  <motion.div
                    className="relative cursor-pointer"
                    whileHover={{ scale: 1.1 }}
                    whileTap={{ scale: 0.9 }}
                  >
                    <div className="w-10 h-10 rounded-full bg-gradient-to-r from-red-500 to-orange-500 flex items-center justify-center text-white font-bold shadow-lg">
                      {user?.username?.charAt(0).toUpperCase() || 'V'}
                    </div>
                    <motion.div 
                      className="absolute -bottom-1 -right-1 w-3 h-3 bg-green-500 border-2 border-white dark:border-gray-800 rounded-full"
                      animate={{ scale: [1, 1.2, 1] }}
                      transition={{ repeat: Infinity, duration: 2 }}
                    />
                  </motion.div>
                </div>
              </div>

              {/* Filters for History View */}
              {activeView === 'history' && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-4 flex items-center space-x-4"
                >
                  <select
                    value={filters.status}
                    onChange={(e) => setFilters({...filters, status: e.target.value})}
                    className="px-4 py-2 border-2 border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:border-red-500 focus:ring focus:ring-red-200 dark:focus:ring-red-800 transition-all"
                  >
                    <option value="all">All Status</option>
                    <option value="verified">Verified</option>
                    <option value="invalid">Invalid</option>
                  </select>

                  <select
                    value={filters.paymentMethod}
                    onChange={(e) => setFilters({...filters, paymentMethod: e.target.value})}
                    className="px-4 py-2 border-2 border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:border-red-500 focus:ring focus:ring-red-200 dark:focus:ring-red-800 transition-all"
                  >
                    <option value="all">All Payments</option>
                    <option value="mpesa_lesotho">M-Pesa Lesotho</option>
                    <option value="mpesa">M-Pesa</option>
                    <option value="ecocash">EcoCash</option>
                    <option value="bank">Bank Transfer</option>
                  </select>

                  <input
                    type="date"
                    value={dateRange.start}
                    onChange={(e) => setDateRange({...dateRange, start: e.target.value})}
                    className="px-4 py-2 border-2 border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:border-red-500 focus:ring focus:ring-red-200 dark:focus:ring-red-800 transition-all"
                  />
                  <span className="text-gray-500">to</span>
                  <input
                    type="date"
                    value={dateRange.end}
                    onChange={(e) => setDateRange({...dateRange, end: e.target.value})}
                    className="px-4 py-2 border-2 border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:border-red-500 focus:ring focus:ring-red-200 dark:focus:ring-red-800 transition-all"
                  />
                </motion.div>
              )}
            </div>
          </div>

          {/* Action Messages */}
          <AnimatePresence>
            {actionMsg.text && (
              <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className={`mx-8 mt-4 px-6 py-4 rounded-xl shadow-lg flex items-center ${
                  actionMsg.type === 'success' 
                    ? 'bg-gradient-to-r from-green-500 to-green-600 text-white'
                    : actionMsg.type === 'error'
                    ? 'bg-gradient-to-r from-red-500 to-red-600 text-white'
                    : 'bg-gradient-to-r from-blue-500 to-blue-600 text-white'
                }`}
              >
                {actionMsg.type === 'success' && <FiCheck className="w-5 h-5 mr-3" />}
                {actionMsg.type === 'error' && <FiAlertCircle className="w-5 h-5 mr-3" />}
                {actionMsg.text}
              </motion.div>
            )}
          </AnimatePresence>

          {/* Real-time Updates Ticker */}
          {realtimeUpdates.length > 0 && (
            <div className="mx-8 mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
              <div className="flex items-center space-x-4 overflow-x-auto">
                <FiZap className="text-blue-500 w-5 h-5 flex-shrink-0" />
                {realtimeUpdates.map((update) => (
                  <div
                    key={update.id}
                    className="flex items-center space-x-2 text-sm whitespace-nowrap"
                  >
                    <span className={`w-2 h-2 rounded-full ${
                      update.type === 'success' ? 'bg-green-500' :
                      update.type === 'error' ? 'bg-red-500' : 'bg-blue-500'
                    }`} />
                    <span className="text-gray-700 dark:text-gray-300">{update.message}</span>
                    <span className="text-xs text-gray-400">
                      {format(parseISO(update.timestamp), 'HH:mm')}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Error Messages */}
          <AnimatePresence>
            {(error || ocrError) && (
              <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="mx-8 mt-4 px-6 py-4 rounded-xl bg-gradient-to-r from-red-500 to-red-600 text-white shadow-lg flex items-center"
              >
                <FiAlertCircle className="w-5 h-5 mr-3" />
                {error || ocrError}
                <button
                  onClick={() => {
                    setError('');
                    setOcrError('');
                  }}
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
                key={activeView}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ duration: 0.2 }}
              >
                {/* Verify View */}
                {activeView === 'verify' && (
                  <motion.div
                    variants={containerVariants}
                    initial="hidden"
                    animate="visible"
                    className="space-y-6"
                  >
                    {/* Stats Cards */}
                    <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-4 gap-6">
                      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 transform hover:scale-105 transition-all duration-300 border-l-4 border-blue-500">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-gray-500 dark:text-gray-400 text-sm">Total Verifications</p>
                            <p className="text-3xl font-bold text-gray-800 dark:text-white">{verifierStats?.total ?? 0}</p>
                          </div>
                          <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-xl flex items-center justify-center">
                            <FiList className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                          </div>
                        </div>
                      </div>

                      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 transform hover:scale-105 transition-all duration-300 border-l-4 border-green-500">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-gray-500 dark:text-gray-400 text-sm">Valid</p>
                            <p className="text-3xl font-bold text-gray-800 dark:text-white">{verifierStats?.valid ?? 0}</p>
                          </div>
                          <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-xl flex items-center justify-center">
                            <FiCheckCircle className="w-6 h-6 text-green-600 dark:text-green-400" />
                          </div>
                        </div>
                      </div>

                      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 transform hover:scale-105 transition-all duration-300 border-l-4 border-red-500">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-gray-500 dark:text-gray-400 text-sm">Invalid</p>
                            <p className="text-3xl font-bold text-gray-800 dark:text-white">{verifierStats?.invalid ?? 0}</p>
                          </div>
                          <div className="w-12 h-12 bg-red-100 dark:bg-red-900/30 rounded-xl flex items-center justify-center">
                            <FiXCircle className="w-6 h-6 text-red-600 dark:text-red-400" />
                          </div>
                        </div>
                      </div>

                      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 transform hover:scale-105 transition-all duration-300 border-l-4 border-yellow-500">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-gray-500 dark:text-gray-400 text-sm">Fees Earned</p>
                            <p className="text-3xl font-bold text-gray-800 dark:text-white">
                              {formatCurrency(verifierStats?.total_fees || 0)}
                            </p>
                          </div>
                          <div className="w-12 h-12 bg-yellow-100 dark:bg-yellow-900/30 rounded-xl flex items-center justify-center">
                            <FiDollarSign className="w-6 h-6 text-yellow-600 dark:text-yellow-400" />
                          </div>
                        </div>
                      </div>
                    </motion.div>

                    {/* Quick OCR Scan Card */}
                    <motion.div variants={itemVariants} className="bg-gradient-to-r from-purple-500 to-indigo-600 rounded-2xl shadow-xl p-6 text-white">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="text-xl font-bold mb-2">Quick Certificate Scan</h3>
                          <p className="text-purple-100 mb-4">Upload or scan a certificate to auto-fill verification</p>
                          <div className="flex space-x-4">
                            <button
                              onClick={() => fileInputRef.current?.click()}
                              className="px-6 py-3 bg-white text-purple-600 rounded-xl font-medium hover:bg-purple-50 transition-colors flex items-center"
                            >
                              <FiUpload className="mr-2" />
                              Upload Certificate
                            </button>
                            <button
                              onClick={() => setShowScanner(true)}
                              className="px-6 py-3 bg-purple-600 text-white rounded-xl font-medium hover:bg-purple-700 transition-colors flex items-center border border-white/30"
                            >
                              <FiCamera className="mr-2" />
                              Scan with Camera
                            </button>
                          </div>
                        </div>
                        <div className="text-7xl opacity-50">🔍</div>
                      </div>
                    </motion.div>

                    {/* Main Verification Form */}
                    <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                      {/* Left Column - Form */}
                      <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-2xl shadow-xl overflow-hidden">
                        <div className="px-6 py-4 bg-gradient-to-r from-red-500 to-orange-600">
                          <h3 className="text-lg font-semibold text-white flex items-center">
                            <FiCheckCircle className="mr-2" />
                            Verify Certificate
                          </h3>
                        </div>
                        <div className="p-6">
                          {/* File Upload Area */}
                          <div className="mb-6 p-4 bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 rounded-xl border-2 border-dashed border-purple-200 dark:border-purple-800">
                            <div className="flex items-center justify-between">
                              <div className="flex items-center space-x-4">
                                <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/30 rounded-full flex items-center justify-center">
                                  <FiCamera className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                                </div>
                                <div>
                                  <h4 className="font-medium text-gray-800 dark:text-white">OCR Auto-Fill</h4>
                                  <p className="text-sm text-gray-500 dark:text-gray-400">Upload certificate to auto-extract hash</p>
                                </div>
                              </div>
                              <input
                                type="file"
                                ref={fileInputRef}
                                accept=".pdf,image/*"
                                onChange={(e) => handleFileUpload(e.target.files?.[0] || null)}
                                className="hidden"
                                id="verify-file"
                              />
                              <button
                                onClick={() => fileInputRef.current?.click()}
                                disabled={ocrLoading}
                                className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center disabled:opacity-50"
                              >
                                {ocrLoading ? (
                                  <>
                                    <svg className="animate-spin h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24">
                                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    Scanning...
                                  </>
                                ) : (
                                  <>
                                    <FiUpload className="mr-2" />
                                    Select File
                                  </>
                                )}
                              </button>
                            </div>
                            
                            {file && !ocrLoading && (
                              <div className="mt-3 flex items-center justify-between bg-white dark:bg-gray-700 p-2 rounded-lg">
                                <div className="flex items-center">
                                  <FiFileText className="w-5 h-5 mr-2 text-gray-500" />
                                  <span className="text-sm text-gray-600 dark:text-gray-300">{file.name}</span>
                                  {ocrConfidence && (
                                    <span className={`ml-3 text-xs font-medium ${getConfidenceColor(ocrConfidence)}`}>
                                      Confidence: {ocrConfidence}%
                                    </span>
                                  )}
                                </div>
                                <button
                                  onClick={handleClearOcr}
                                  className="text-red-500 hover:text-red-700"
                                >
                                  <FiX className="w-5 h-5" />
                                </button>
                              </div>
                            )}
                            
                            {ocrLoading && (
                              <div className="mt-3">
                                <div className="flex items-center justify-between mb-2">
                                  <span className="text-sm text-gray-600 dark:text-gray-400">Extracting data...</span>
                                  <span className="text-xs text-purple-600 dark:text-purple-400">{uploadPct}%</span>
                                </div>
                                <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                  <motion.div
                                    className="h-2 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full"
                                    initial={{ width: 0 }}
                                    animate={{ width: `${uploadPct}%` }}
                                    transition={{ duration: 0.3 }}
                                  />
                                </div>
                              </div>
                            )}
                          </div>

                          <form onSubmit={handleVerify} className="space-y-6">
                            {/* Verification Mode Selection */}
                            <div>
                              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                                Verification Method
                              </label>
                              <div className="grid grid-cols-3 gap-3">
                                <button
                                  type="button"
                                  onClick={() => setVerificationMode('hash')}
                                  className={`px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                                    verificationMode === 'hash'
                                      ? 'bg-gradient-to-r from-red-500 to-orange-600 text-white shadow-lg transform scale-105'
                                      : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                                  }`}
                                >
                                  <FaQrcode className="mx-auto mb-1 w-5 h-5" />
                                  Hash Only
                                </button>
                                <button
                                  type="button"
                                  onClick={() => setVerificationMode('file')}
                                  className={`px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                                    verificationMode === 'file'
                                      ? 'bg-gradient-to-r from-red-500 to-orange-600 text-white shadow-lg transform scale-105'
                                      : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                                  }`}
                                >
                                  <FiFileText className="mx-auto mb-1 w-5 h-5" />
                                  File Only
                                </button>
                                <button
                                  type="button"
                                  onClick={() => setVerificationMode('both')}
                                  className={`px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                                    verificationMode === 'both'
                                      ? 'bg-gradient-to-r from-red-500 to-orange-600 text-white shadow-lg transform scale-105'
                                      : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                                  }`}
                                >
                                  <FiRefreshCw className="mx-auto mb-1 w-5 h-5" />
                                  Both
                                </button>
                              </div>
                            </div>

                            {/* Certificate Hash */}
                            {(verificationMode === 'hash' || verificationMode === 'both') && (
                              <motion.div
                                initial={{ opacity: 0, y: -10 }}
                                animate={{ opacity: 1, y: 0 }}
                                className="space-y-2"
                              >
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                  Certificate Hash
                                </label>
                                <div className="relative">
                                  <FaQrcode className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                                  <input
                                    value={certificateHash}
                                    onChange={(e) => setCertificateHash(e.target.value)}
                                    placeholder="Enter 64-character certificate hash"
                                    className="w-full pl-10 pr-4 py-3 rounded-xl border-2 border-gray-200 dark:border-gray-700 dark:bg-gray-900 dark:text-white focus:border-red-500 focus:ring focus:ring-red-200 dark:focus:ring-red-800 transition-all"
                                  />
                                </div>
                                <p className="text-xs text-gray-500 dark:text-gray-400">
                                  Enter the unique certificate hash (e.g., 0x7b3d8f9a...)
                                </p>
                              </motion.div>
                            )}

                            {/* Payment Section */}
                            <div className="grid grid-cols-2 gap-4">
                              <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                  Payment Method
                                </label>
                                <select
                                  value={paymentMethod}
                                  onChange={(e) => setPaymentMethod(e.target.value)}
                                  className="w-full rounded-xl border-2 border-gray-200 dark:border-gray-700 dark:bg-gray-900 dark:text-white px-4 py-3 text-sm focus:border-red-500 focus:ring focus:ring-red-200 dark:focus:ring-red-800 transition-all"
                                >
                                  <option value="mpesa_lesotho">📱 M-Pesa Lesotho</option>
                                  <option value="mpesa">📱 M-Pesa</option>
                                  <option value="ecocash">📲 EcoCash</option>
                                  <option value="bank">🏦 Bank Transfer</option>
                                </select>
                              </div>
                              <div>
                                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                  Phone/Account Digits
                                </label>
                                <input
                                  value={paymentDigits}
                                  onChange={(e) => setPaymentDigits(e.target.value.replace(/\D/g, '').slice(0, 6))}
                                  inputMode="numeric"
                                  placeholder="Last 6 digits"
                                  className="w-full rounded-xl border-2 border-gray-200 dark:border-gray-700 dark:bg-gray-900 dark:text-white px-4 py-3 text-sm focus:border-red-500 focus:ring focus:ring-red-200 dark:focus:ring-red-800 transition-all"
                                />
                              </div>
                            </div>

                            <motion.button
                              type="submit"
                              disabled={!canSubmit}
                              className={`w-full px-6 py-3 rounded-xl text-white font-medium transition-all transform hover:scale-105 ${
                                canSubmit 
                                  ? 'bg-gradient-to-r from-red-500 to-orange-600 hover:from-red-600 hover:to-orange-700 shadow-lg' 
                                  : 'bg-gray-300 dark:bg-gray-600 cursor-not-allowed'
                              }`}
                              whileHover={canSubmit ? { scale: 1.05 } : {}}
                              whileTap={canSubmit ? { scale: 0.95 } : {}}
                            >
                              {loading ? (
                                <span className="flex items-center justify-center">
                                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                  </svg>
                                  Verifying... {uploadPct}%
                                </span>
                              ) : 'Verify Certificate'}
                            </motion.button>

                            {loading && (
                              <div className="space-y-2">
                                <div className="flex justify-between text-sm">
                                  <span className="text-gray-600 dark:text-gray-400">Progress</span>
                                  <span className="font-medium text-red-600 dark:text-red-400">{uploadPct}%</span>
                                </div>
                                <div className="h-2 w-full rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
                                  <motion.div 
                                    className="h-2 rounded-full bg-gradient-to-r from-red-500 to-orange-600"
                                    initial={{ width: 0 }}
                                    animate={{ width: `${uploadPct}%` }}
                                    transition={{ duration: 0.3 }}
                                  />
                                </div>
                              </div>
                            )}
                          </form>

                          {/* OCR History */}
                          {ocrHistory.length > 0 && (
                            <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
                              <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                                Recent OCR Scans
                              </h4>
                              <div className="space-y-2">
                                {ocrHistory.slice(0, 3).map((item) => (
                                  <div key={item.id} className="flex items-center justify-between text-xs">
                                    <div className="flex items-center">
                                      <span className={item.success ? 'text-green-600' : 'text-red-600'}>
                                        {item.success ? '✓' : '✗'}
                                      </span>
                                      <span className="ml-2 text-gray-600 dark:text-gray-400 truncate max-w-[150px]">
                                        {item.filename}
                                      </span>
                                    </div>
                                    {item.success && (
                                      <span className={`font-medium ${getConfidenceColor(item.confidence)}`}>
                                        {item.confidence}%
                                      </span>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Right Column - Result */}
                      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl overflow-hidden">
                        <div className="px-6 py-4 bg-gradient-to-r from-indigo-500 to-purple-600">
                          <h3 className="text-lg font-semibold text-white flex items-center">
                            <FiStar className="mr-2" />
                            Verification Result
                          </h3>
                        </div>
                        <div className="p-6">
                          {!result ? (
                            <div className="text-center py-12">
                              <div className="relative">
                                <motion.div
                                  animate={{ rotate: 360 }}
                                  transition={{ repeat: Infinity, duration: 10, ease: "linear" }}
                                  className="w-24 h-24 mx-auto mb-6"
                                >
                                  <FiCheckCircle className="w-24 h-24 text-gray-200 dark:text-gray-700" />
                                </motion.div>
                                <div className="absolute inset-0 flex items-center justify-center">
                                  <FaQrcode className="w-12 h-12 text-gray-400 dark:text-gray-500" />
                                </div>
                              </div>
                              <p className="text-gray-500 dark:text-gray-400 text-lg">Ready to verify</p>
                              <p className="text-sm text-gray-400 dark:text-gray-500 mt-2">Enter details to check authenticity</p>
                            </div>
                          ) : (
                            <motion.div
                              initial={{ opacity: 0, scale: 0.9 }}
                              animate={{ opacity: 1, scale: 1 }}
                              className="space-y-4"
                            >
                              <div className={`p-6 rounded-xl ${
                                result.verified ? 'bg-green-50 dark:bg-green-900/20 border-2 border-green-200 dark:border-green-800' : 'bg-red-50 dark:bg-red-900/20 border-2 border-red-200 dark:border-red-800'
                              }`}>
                                <div className="flex items-center">
                                  <motion.div
                                    initial={{ scale: 0 }}
                                    animate={{ scale: 1 }}
                                    transition={{ type: "spring", stiffness: 260, damping: 20 }}
                                    className={`w-16 h-16 rounded-full flex items-center justify-center text-3xl mr-4 ${
                                      result.verified ? 'bg-green-100 dark:bg-green-900/30' : 'bg-red-100 dark:bg-red-900/30'
                                    }`}
                                  >
                                    {result.verified ? '✅' : '❌'}
                                  </motion.div>
                                  <div>
                                    <h4 className={`text-xl font-bold ${result.verified ? 'text-green-700 dark:text-green-400' : 'text-red-700 dark:text-red-400'}`}>
                                      {result.verified ? 'VALID CERTIFICATE' : 'INVALID CERTIFICATE'}
                                    </h4>
                                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                      Blockchain: {result.blockchain_verified ? '✅ Verified' : '❌ Not Found'}
                                    </p>
                                    {result.confidence && (
                                      <p className={`text-sm font-medium ${getConfidenceColor(result.confidence)}`}>
                                        OCR Confidence: {result.confidence}%
                                      </p>
                                    )}
                                  </div>
                                </div>
                              </div>

                              {result.certificate && (
                                <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                                  <div className="flex justify-between items-center mb-3">
                                    <h5 className="text-sm font-semibold text-gray-700 dark:text-gray-300">
                                      Certificate Details
                                    </h5>
                                    <button
                                      onClick={() => {
                                        setSelectedCertificate(result.certificate);
                                        setShowPreview(true);
                                      }}
                                      className="text-xs text-blue-600 hover:text-blue-800 dark:text-blue-400 flex items-center"
                                    >
                                      <FiEye className="mr-1" /> View Full
                                    </button>
                                  </div>
                                  <div className="grid grid-cols-2 gap-3">
                                    <div className="bg-white dark:bg-gray-800 p-3 rounded-lg">
                                      <p className="text-xs text-gray-500 dark:text-gray-400">Student Name</p>
                                      <p className="text-sm font-medium text-gray-800 dark:text-white">{result.certificate.full_name}</p>
                                    </div>
                                    <div className="bg-white dark:bg-gray-800 p-3 rounded-lg">
                                      <p className="text-xs text-gray-500 dark:text-gray-400">Student ID</p>
                                      <p className="text-sm font-medium text-gray-800 dark:text-white">{result.certificate.candidate_number}</p>
                                    </div>
                                    <div className="bg-white dark:bg-gray-800 p-3 rounded-lg">
                                      <p className="text-xs text-gray-500 dark:text-gray-400">Institution</p>
                                      <p className="text-sm font-medium text-gray-800 dark:text-white">{result.certificate.issuer_code}</p>
                                    </div>
                                    <div className="bg-white dark:bg-gray-800 p-3 rounded-lg">
                                      <p className="text-xs text-gray-500 dark:text-gray-400">Issue Date</p>
                                      <p className="text-sm font-medium text-gray-800 dark:text-white">{result.certificate.date_of_issue}</p>
                                    </div>
                                  </div>
                                </div>
                              )}

                              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-3">
                                <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Verification ID</p>
                                <div className="flex items-center justify-between">
                                  <p className="text-sm font-mono bg-white dark:bg-gray-800 p-2 rounded border border-gray-200 dark:border-gray-700 flex-1">
                                    {result.verification_id}
                                  </p>
                                  <button
                                    onClick={() => {
                                      navigator.clipboard.writeText(result.verification_id);
                                      showNotification('success', 'Verification ID copied');
                                    }}
                                    className="ml-2 p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400"
                                  >
                                    <FiCopy className="w-4 h-4" />
                                  </button>
                                </div>
                              </div>

                              {result.timestamp && (
                                <p className="text-xs text-gray-400 dark:text-gray-500 text-right">
                                  Verified on {format(parseISO(result.timestamp), 'MMM dd, yyyy HH:mm')}
                                </p>
                              )}

                              {result.message && (
                                <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                                  <p className="text-sm text-blue-700 dark:text-blue-400">{result.message}</p>
                                </div>
                              )}
                            </motion.div>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  </motion.div>
                )}

                {/* History View */}
                {activeView === 'history' && (
                  <motion.div
                    variants={containerVariants}
                    initial="hidden"
                    animate="visible"
                    className="space-y-6"
                  >
                    <motion.div variants={itemVariants} className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl overflow-hidden">
                      <div className="px-6 py-4 bg-gradient-to-r from-blue-500 to-indigo-600">
                        <h3 className="text-lg font-semibold text-white flex items-center">
                          <FiList className="mr-2" />
                          Verification History
                        </h3>
                      </div>
                      <div className="p-6">
                        {filteredHistory.length === 0 ? (
                          <div className="text-center py-12">
                            <FiFileText className="w-16 h-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
                            <p className="text-gray-500 dark:text-gray-400 text-lg">No verification history found</p>
                            <p className="text-sm text-gray-400 dark:text-gray-500 mt-2">Start verifying certificates to see history here</p>
                          </div>
                        ) : (
                          <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                              <thead className="bg-gray-50 dark:bg-gray-900">
                                <tr>
                                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Date</th>
                                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Certificate</th>
                                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Result</th>
                                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Payment</th>
                                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Fee</th>
                                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                                </tr>
                              </thead>
                              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                                {filteredHistory.map((v, index) => (
                                  <motion.tr
                                    key={v.id}
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: index * 0.05 }}
                                    className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                                  >
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                      {formatDate(v.verification_date)}
                                    </td>
                                    <td className="px-6 py-4">
                                      <div className="flex flex-col">
                                        <span className="font-mono text-xs bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded mb-1">
                                          {v.certificate_hash?.slice(0, 16)}...
                                        </span>
                                        <span className="text-xs text-gray-500 dark:text-gray-400">{v.student_name}</span>
                                      </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${getResultColor(v.result)}`}>
                                        {getResultIcon(v.result)} {v.result}
                                      </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                      <div className="flex items-center">
                                        <span className="text-lg mr-1">{getPaymentIcon(v.payment_method)}</span>
                                        <span className="text-sm text-gray-600 dark:text-gray-400">
                                          {v.payment_method?.replace('_', ' ')}
                                        </span>
                                      </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-green-600 dark:text-green-400">
                                      {formatCurrency(v.verification_fee || 5.00)}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                      <div className="flex items-center space-x-2">
                                        <button
                                          onClick={() => {
                                            setResult({
                                              verified: v.result === 'verified',
                                              verification_id: v.verification_id,
                                              certificate: v.certificate,
                                              timestamp: v.verification_date,
                                              blockchain_verified: v.blockchain_verified
                                            });
                                            setActiveView('verify');
                                          }}
                                          className="text-blue-600 hover:text-blue-800 dark:text-blue-400"
                                          title="View Details"
                                        >
                                          <FiEye className="w-4 h-4" />
                                        </button>
                                        <button
                                          onClick={() => {
                                            navigator.clipboard.writeText(v.certificate_hash);
                                            showNotification('success', 'Hash copied');
                                          }}
                                          className="text-gray-600 hover:text-gray-800 dark:text-gray-400"
                                          title="Copy Hash"
                                        >
                                          <FiCopy className="w-4 h-4" />
                                        </button>
                                      </div>
                                    </td>
                                  </motion.tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  </motion.div>
                )}

                {/* Payments View */}
                {activeView === 'payments' && (
                  <motion.div
                    variants={containerVariants}
                    initial="hidden"
                    animate="visible"
                    className="space-y-6"
                  >
                    {/* Payment Stats */}
                    {paymentStats && (
                      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-4 gap-6">
                        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                          <p className="text-sm text-gray-500 dark:text-gray-400">Total Spent</p>
                          <p className="text-2xl font-bold text-gray-800 dark:text-white">
                            {formatCurrency(paymentStats.total_spent)}
                          </p>
                        </div>
                        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                          <p className="text-sm text-gray-500 dark:text-gray-400">Successful Payments</p>
                          <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                            {paymentStats.successful_payments}
                          </p>
                        </div>
                        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                          <p className="text-sm text-gray-500 dark:text-gray-400">Pending Payments</p>
                          <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
                            {paymentStats.pending_payments}
                          </p>
                        </div>
                        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                          <p className="text-sm text-gray-500 dark:text-gray-400">Average Fee</p>
                          <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                            {formatCurrency(paymentStats.average_fee)}
                          </p>
                        </div>
                      </motion.div>
                    )}

                    {/* Payment History Table */}
                    <motion.div variants={itemVariants} className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl overflow-hidden">
                      <div className="px-6 py-4 bg-gradient-to-r from-green-500 to-emerald-600">
                        <h3 className="text-lg font-semibold text-white flex items-center">
                          <FiDollarSign className="mr-2" />
                          Payment History
                        </h3>
                      </div>
                      <div className="p-6">
                        {paymentHistory.length === 0 ? (
                          <div className="text-center py-12">
                            <FiDollarSign className="w-16 h-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
                            <p className="text-gray-500 dark:text-gray-400 text-lg">No payment history yet</p>
                          </div>
                        ) : (
                          <div className="overflow-x-auto">
                            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                              <thead className="bg-gray-50 dark:bg-gray-900">
                                <tr>
                                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Date</th>
                                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Amount</th>
                                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Method</th>
                                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Reference</th>
                                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
                                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">M-Pesa ID</th>
                                </tr>
                              </thead>
                              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                                {paymentHistory.map((p, index) => (
                                  <tr key={p.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                      {formatDate(p.created_at)}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 dark:text-white">
                                      {formatCurrency(p.amount)}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                      <div className="flex items-center">
                                        <span className="text-lg mr-1">{getPaymentIcon(p.method)}</span>
                                        <span className="text-sm text-gray-600 dark:text-gray-400">
                                          {p.method?.replace('_', ' ')}
                                        </span>
                                      </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                      {p.reference || '-'}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                        p.status === 'CONFIRMED' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' :
                                        p.status === 'PENDING' ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400' :
                                        'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                                      }`}>
                                        {p.status}
                                      </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-xs font-mono text-gray-500 dark:text-gray-400">
                                      {p.mpesa_transaction_id || '-'}
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  </motion.div>
                )}

                {/* Statistics View */}
                {activeView === 'stats' && (
                  <motion.div
                    variants={containerVariants}
                    initial="hidden"
                    animate="visible"
                    className="space-y-6"
                  >
                    {/* Charts */}
                    <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-6">
                        <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">
                          Verification Trend
                        </h3>
                        {chartData?.trend && (
                          <Line
                            data={chartData.trend}
                            options={{
                              responsive: true,
                              plugins: {
                                legend: {
                                  display: false
                                }
                              },
                              scales: {
                                y: {
                                  beginAtZero: true,
                                  grid: {
                                    color: 'rgba(0,0,0,0.05)'
                                  }
                                }
                              }
                            }}
                          />
                        )}
                      </div>

                      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-6">
                        <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">
                          Status Distribution
                        </h3>
                        {chartData?.distribution && (
                          <Doughnut
                            data={chartData.distribution}
                            options={{
                              responsive: true,
                              plugins: {
                                legend: {
                                  position: 'bottom'
                                }
                              }
                            }}
                          />
                        )}
                      </div>
                    </motion.div>

                    {/* Payment Methods Distribution */}
                    <motion.div variants={itemVariants} className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-6">
                      <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">
                        Payment Methods Distribution
                      </h3>
                      <div className="space-y-4">
                        <div className="flex items-center p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                          <span className="text-2xl mr-3">📱</span>
                          <div className="flex-1">
                            <div className="flex justify-between mb-1">
                              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">M-Pesa Lesotho</span>
                              <span className="text-sm text-gray-600 dark:text-gray-400">48%</span>
                            </div>
                            <div className="h-2 w-full rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
                              <div className="h-2 rounded-full bg-green-500" style={{ width: '48%' }} />
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                          <span className="text-2xl mr-3">📱</span>
                          <div className="flex-1">
                            <div className="flex justify-between mb-1">
                              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">M-Pesa</span>
                              <span className="text-sm text-gray-600 dark:text-gray-400">32%</span>
                            </div>
                            <div className="h-2 w-full rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
                              <div className="h-2 rounded-full bg-blue-500" style={{ width: '32%' }} />
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                          <span className="text-2xl mr-3">📲</span>
                          <div className="flex-1">
                            <div className="flex justify-between mb-1">
                              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">EcoCash</span>
                              <span className="text-sm text-gray-600 dark:text-gray-400">12%</span>
                            </div>
                            <div className="h-2 w-full rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
                              <div className="h-2 rounded-full bg-purple-500" style={{ width: '12%' }} />
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                          <span className="text-2xl mr-3">🏦</span>
                          <div className="flex-1">
                            <div className="flex justify-between mb-1">
                              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Bank Transfer</span>
                              <span className="text-sm text-gray-600 dark:text-gray-400">8%</span>
                            </div>
                            <div className="h-2 w-full rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
                              <div className="h-2 rounded-full bg-yellow-500" style={{ width: '8%' }} />
                            </div>
                          </div>
                        </div>
                      </div>

                      <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                        <p className="text-sm text-blue-800 dark:text-blue-300 font-medium mb-2">Verification Fee Structure</p>
                        <p className="text-xs text-blue-600 dark:text-blue-400">• Standard verification: M5.00 per certificate</p>
                        <p className="text-xs text-blue-600 dark:text-blue-400">• Bulk discount available for 10+ verifications</p>
                        <p className="text-xs text-blue-600 dark:text-blue-400">• Payments processed via M-Pesa Lesotho</p>
                      </div>
                    </motion.div>

                    {/* Performance Metrics */}
                    <motion.div variants={itemVariants} className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-6">
                      <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">
                        Performance Metrics
                      </h3>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="text-center">
                          <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                            {verifierStats?.total > 0 ? Math.round((verifierStats.valid / verifierStats.total) * 100) : 0}%
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">Success Rate</p>
                        </div>
                        <div className="text-center">
                          <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                            {verifierStats?.total || 0}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">Total Verifications</p>
                        </div>
                        <div className="text-center">
                          <p className="text-2xl font-bold text-purple-600 dark:text-purple-400">
                            {formatCurrency(verifierStats?.total_fees || 0)}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">Total Fees</p>
                        </div>
                        <div className="text-center">
                          <p className="text-2xl font-bold text-orange-600 dark:text-orange-400">
                            {verifierStats?.today?.verified || 0}
                          </p>
                          <p className="text-xs text-gray-500 dark:text-gray-400">Today</p>
                        </div>
                      </div>
                    </motion.div>
                  </motion.div>
                )}
              </motion.div>
            </AnimatePresence>
          </div>

          {/* Recent Activity Footer */}
          <div className="p-8 pt-0">
            <RecentActivity title="Live System Activity" limit={5} />
          </div>
        </motion.div>
      </div>

      {/* Floating Action Button */}
      <motion.button
        className="fixed bottom-8 right-8 w-14 h-14 bg-gradient-to-r from-red-600 to-orange-600 rounded-full shadow-2xl flex items-center justify-center text-white z-30"
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
          fileInputRef.current?.click();
        }}
      >
        <FiUpload className="w-6 h-6" />
      </motion.button>
    </div>
  );
};

export default VerifierDashboard;