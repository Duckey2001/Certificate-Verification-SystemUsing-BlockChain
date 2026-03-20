import React, { useEffect, useMemo, useState, useCallback, useRef } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { certificateApi, userApi, institutionApi } from '../../api';
import RecentActivity from '../../components/RecentActivity.jsx';
import BulkUploadModal from '../../components/BulkUploadModal.jsx';
import CertificatePreview from '../../components/CertificatePreview.jsx';
import ProfileEditor from '../../components/ProfileEditor.jsx';
import BlockchainStatus from '../../components/BlockchainStatus.jsx';
import OCRSidebar from '../../components/OCRSidebar.jsx';
import CertificateScanner from '../../components/CertificateScanner.jsx';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FiHome,
  FiFileText,
  FiUpload,
  FiCheckCircle,
  FiList,
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
  FiEye,
  FiClock,
  FiTrendingUp,
  FiTrendingDown,
  FiAward,
  FiUsers,
  FiMail,
  FiPrinter,
  FiShare2,
  FiStar,
  FiAlertCircle,
  FiCheck,
  FiX,
  FiCamera,
  FiUploadCloud,
  FiFile,
  FiGrid,
  FiBarChart2,
  FiZap,
  FiCopy
} from 'react-icons/fi';
import { 
  FaQrcode, 
  FaBarcode, 
  FaCertificate,
  FaRegCreditCard,
  FaRegClock,
  FaRegCheckCircle,
  FaRegTimesCircle
} from 'react-icons/fa';
import { format, subDays, parseISO, differenceInDays } from 'date-fns';
import { QRCodeCanvas } from 'qrcode.react';
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

// Register ChartJS components
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

const IssuerDashboard = () => {
  const { user, logout, updateUser } = useAuth();
  const [issuerStats, setIssuerStats] = useState(null);
  const [myCertificates, setMyCertificates] = useState([]);
  const [institutionInfo, setInstitutionInfo] = useState(null);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [showNotifications, setShowNotifications] = useState(false);
  const fileInputRef = useRef(null);
  const scannerRef = useRef(null);
  
  // Real-time updates
  const [realtimeUpdates, setRealtimeUpdates] = useState([]);
  const [wsConnection, setWsConnection] = useState(null);
  
  // Chart data
  const [chartData, setChartData] = useState({
    issuanceTrend: null,
    statusDistribution: null,
    monthlyComparison: null
  });

  // QR Code state
  const [showQR, setShowQR] = useState(false);
  const [qrData, setQrData] = useState('');

  // Bulk upload state
  const [showBulkModal, setShowBulkModal] = useState(false);
  const [bulkFiles, setBulkFiles] = useState([]);
  const [bulkLoading, setBulkLoading] = useState(false);
  const [bulkPct, setBulkPct] = useState(0);
  const [bulkError, setBulkError] = useState('');
  const [bulkResult, setBulkResult] = useState(null);
  const [bulkProgress, setBulkProgress] = useState([]);

  // Single certificate issuance
  const [singleForm, setSingleForm] = useState({
    student_name: '',
    student_surname: '',
    student_id: '',
    institution: user?.institution || '',
    issue_date: format(new Date(), 'yyyy-MM-dd'),
    expiry_date: format(new Date().setFullYear(new Date().getFullYear() + 5), 'yyyy-MM-dd'),
    grade: '',
    subjects: [],
    exam_session: `November ${new Date().getFullYear()}`,
    certificate_number: '',
    additional_info: ''
  });
  const [singleFile, setSingleFile] = useState(null);
  const [singleLoading, setSingleLoading] = useState(false);
  const [singleError, setSingleError] = useState('');
  const [singleSuccess, setSingleSuccess] = useState(null);
  
  // OCR extracted data state
  const [extractedData, setExtractedData] = useState(null);
  const [extractedDisplay, setExtractedDisplay] = useState(null);
  const [ocrLoading, setOcrLoading] = useState(false);
  const [ocrError, setOcrError] = useState('');
  const [showOcrSidebar, setShowOcrSidebar] = useState(false);
  const [ocrConfidence, setOcrConfidence] = useState(null);
  const [showScanner, setShowScanner] = useState(false);
  const [ocrHistory, setOcrHistory] = useState([]);

  // Verification state
  const [verifyHash, setVerifyHash] = useState('');
  const [verifyFile, setVerifyFile] = useState(null);
  const [verifyMethod, setVerifyMethod] = useState('both');
  const [verifyLoading, setVerifyLoading] = useState(false);
  const [verifyPct, setVerifyPct] = useState(0);
  const [verifyError, setVerifyError] = useState('');
  const [verifyResult, setVerifyResult] = useState(null);
  const [verifyHistory, setVerifyHistory] = useState([]);

  // UI state
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const [showProfileEditor, setShowProfileEditor] = useState(false);
  const [actionMsg, setActionMsg] = useState({ type: '', text: '' });
  const [activeView, setActiveView] = useState('dashboard');
  const [selectedCertificate, setSelectedCertificate] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  const [loading, setLoading] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [refreshInterval, setRefreshInterval] = useState(30000);
  const [darkMode, setDarkMode] = useState(false);
  const [compactMode, setCompactMode] = useState(false);
  const [dateRange, setDateRange] = useState({
    start: format(subDays(new Date(), 30), 'yyyy-MM-dd'),
    end: format(new Date(), 'yyyy-MM-dd')
  });

  // Filters
  const [statusFilter, setStatusFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('date_desc');
  const [viewMode, setViewMode] = useState('table'); // table, grid, cards

  // Initialize WebSocket connection for real-time updates
  useEffect(() => {
    if (user) {
      const ws = new WebSocket(`${process.env.REACT_APP_WS_URL}/issuer/${user.id}`);
      
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
      case 'certificate_issued':
        setRealtimeUpdates(prev => [{
          id: Date.now(),
          message: `New certificate issued to ${data.student_name}`,
          timestamp: new Date().toISOString(),
          type: 'success'
        }, ...prev].slice(0, 10));
        fetchCertificates();
        fetchStats();
        break;
        
      case 'certificate_verified':
        setRealtimeUpdates(prev => [{
          id: Date.now(),
          message: `Certificate verified: ${data.certificate_hash?.slice(0, 12)}...`,
          timestamp: new Date().toISOString(),
          type: 'info'
        }, ...prev].slice(0, 10));
        break;
        
      case 'bulk_upload_complete':
        setRealtimeUpdates(prev => [{
          id: Date.now(),
          message: `Bulk upload completed: ${data.success} successful, ${data.failed} failed`,
          timestamp: new Date().toISOString(),
          type: data.success > 0 ? 'success' : 'error'
        }, ...prev].slice(0, 10));
        fetchCertificates();
        fetchStats();
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
        setLoading(true);
        
        await Promise.all([
          fetchStats(),
          fetchCertificates(),
          fetchInstitutionInfo(),
          fetchNotifications(),
          fetchOcrHistory(),
          fetchVerifyHistory(),
          generateChartData()
        ]);
        
      } catch (error) {
        console.error('Failed to fetch initial data:', error);
        showNotification('error', 'Failed to load dashboard data');
      } finally {
        if (mounted) setLoading(false);
      }
    };

    fetchInitialData();

    // Set up auto-refresh
    if (autoRefresh) {
      refreshTimer = setInterval(() => {
        fetchStats();
        fetchNotifications();
      }, refreshInterval);
    }

    return () => {
      mounted = false;
      if (refreshTimer) clearInterval(refreshTimer);
    };
  }, [autoRefresh, refreshInterval]);

  // Fetch issuer stats
  const fetchStats = useCallback(async () => {
    try {
      const stats = await certificateApi.getMyIssuerStats(dateRange);
      setIssuerStats(stats);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  }, [dateRange]);

  // Fetch certificates
  const fetchCertificates = useCallback(async () => {
    try {
      const response = await certificateApi.getMyIssuerCertificates({
        status: statusFilter !== 'all' ? statusFilter : undefined,
        search: searchTerm || undefined,
        start_date: dateRange.start,
        end_date: dateRange.end,
        sort: sortBy
      });
      setMyCertificates(response.certificates || []);
    } catch (error) {
      console.error('Failed to fetch certificates:', error);
      showNotification('error', 'Failed to fetch certificates');
    }
  }, [statusFilter, searchTerm, dateRange, sortBy]);

  // Fetch institution info
  const fetchInstitutionInfo = useCallback(async () => {
    try {
      const info = await institutionApi.getMyInstitution();
      setInstitutionInfo(info);
    } catch (error) {
      console.error('Failed to fetch institution info:', error);
      // Set default
      setInstitutionInfo({
        name: user?.institution || 'Examination Council of Lesotho',
        code: 'ECOL',
        address: 'Maseru, Lesotho',
        phone: '+266 22 327 000',
        email: 'info@ecol.ac.ls',
        credits: 1250,
        logo: null,
        verified: true,
        established: '1964',
        website: 'https://ecol.ac.ls'
      });
    }
  }, [user]);

  // Fetch notifications
  const fetchNotifications = useCallback(async () => {
    try {
      const notifs = await userApi.getNotifications();
      setNotifications(notifs);
      setUnreadCount(notifs.filter(n => !n.read).length);
    } catch (error) {
      console.error('Failed to fetch notifications:', error);
    }
  }, []);

  // Fetch OCR history
  const fetchOcrHistory = useCallback(async () => {
    try {
      const history = await certificateApi.getOcrHistory();
      setOcrHistory(history);
    } catch (error) {
      console.error('Failed to fetch OCR history:', error);
      // Set empty array as fallback
      setOcrHistory([]);
    }
  }, []);

  // Fetch verification history
  const fetchVerifyHistory = useCallback(async () => {
    try {
      const history = await certificateApi.getVerificationHistory();
      setVerifyHistory(history);
    } catch (error) {
      console.error('Failed to fetch verification history:', error);
      // Set empty array as fallback
      setVerifyHistory([]);
    }
  }, []);

  // Generate chart data
  const generateChartData = useCallback(async () => {
    try {
      // Issuance trend chart
      try {
        const trendData = await certificateApi.getIssuanceTrend(dateRange);
        setChartData(prev => ({
          ...prev,
          issuanceTrend: {
            labels: trendData.labels || [],
            datasets: [
              {
                label: 'Certificates Issued',
                data: trendData.values || [],
                borderColor: 'rgb(34, 197, 94)',
                backgroundColor: 'rgba(34, 197, 94, 0.1)',
                tension: 0.4,
                fill: true
              }
            ]
          }
        }));
      } catch (trendError) {
        console.error('Failed to fetch issuance trend:', trendError);
        // Set default empty chart data
        setChartData(prev => ({
          ...prev,
          issuanceTrend: {
            labels: [],
            datasets: [{
              label: 'Certificates Issued',
              data: [],
              borderColor: 'rgb(34, 197, 94)',
              backgroundColor: 'rgba(34, 197, 94, 0.1)',
              tension: 0.4,
              fill: true
            }]
          }
        }));
      }

      // Status distribution chart
      try {
        const statusData = await certificateApi.getStatusDistribution();
        setChartData(prev => ({
          ...prev,
          statusDistribution: {
            labels: ['Verified', 'Pending', 'Rejected', 'Revoked'],
            datasets: [
              {
                data: [
                  statusData.verified || 0,
                  statusData.pending || 0,
                  statusData.rejected || 0,
                  statusData.revoked || 0
                ],
                backgroundColor: [
                  'rgba(34, 197, 94, 0.8)',
                  'rgba(234, 179, 8, 0.8)',
                  'rgba(239, 68, 68, 0.8)',
                  'rgba(107, 114, 128, 0.8)'
                ],
                borderWidth: 0
              }
            ]
          }
        }));
      } catch (statusError) {
        console.error('Failed to fetch status distribution:', statusError);
        // Set default empty chart data
        setChartData(prev => ({
          ...prev,
          statusDistribution: {
            labels: ['Verified', 'Pending', 'Rejected', 'Revoked'],
            datasets: [{
              data: [0, 0, 0, 0],
              backgroundColor: [
                'rgba(34, 197, 94, 0.8)',
                'rgba(234, 179, 8, 0.8)',
                'rgba(239, 68, 68, 0.8)',
                'rgba(107, 114, 128, 0.8)'
              ],
              borderWidth: 0
            }]
          }
        }));
      }

      // Monthly comparison chart
      try {
        const monthlyData = await certificateApi.getMonthlyComparison();
        setChartData(prev => ({
          ...prev,
          monthlyComparison: {
            labels: monthlyData.labels || [],
            datasets: [
              {
                label: 'This Year',
                data: monthlyData.thisYear || [],
                backgroundColor: 'rgba(34, 197, 94, 0.8)',
                borderRadius: 6
              },
              {
                label: 'Last Year',
                data: monthlyData.lastYear || [],
                backgroundColor: 'rgba(156, 163, 175, 0.5)',
                borderRadius: 6
              }
            ]
          }
        }));
      } catch (monthlyError) {
        console.error('Failed to fetch monthly comparison:', monthlyError);
        // Set default empty chart data
        setChartData(prev => ({
          ...prev,
          monthlyComparison: {
            labels: [],
            datasets: [
              {
                label: 'This Year',
                data: [],
                backgroundColor: 'rgba(34, 197, 94, 0.8)',
                borderRadius: 6
              },
              {
                label: 'Last Year',
                data: [],
                backgroundColor: 'rgba(156, 163, 175, 0.5)',
                borderRadius: 6
              }
            ]
          }
        }));
      }
    } catch (error) {
      console.error('Failed to generate chart data:', error);
    }
  }, [dateRange]);

  // Show notification
  const showNotification = (type, text) => {
    setActionMsg({ type, text });
    setTimeout(() => setActionMsg({ type: '', text: '' }), 5000);
  };

  // Handle file upload and OCR extraction
  const handleFileUpload = async (file) => {
    setSingleFile(file);
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
      const formData = new FormData();
      formData.append('file', file);
      
      const response = await certificateApi.extractCertificateData(formData, (progress) => {
        setOcrLoading(true);
      });
      
      if (response.data) {
        const data = response.data;
        setExtractedData(data);
        setExtractedDisplay(data.display_html);
        setOcrConfidence(data.validation?.confidence);
        setShowOcrSidebar(true);
        
        // Auto-fill form with extracted data
        const extractedFields = data.certificate_data || data.form_data || data.extracted_fields || {};
        
        const fullName = extractedFields.student_name || extractedFields.full_name || '';
        const nameParts = fullName.split(' ');
        const firstName = nameParts[0] || '';
        const lastName = nameParts.slice(1).join(' ') || '';
        
        const subjects = extractedFields.subjects || 
                        extractedFields.subjects_with_grades?.map(s => s.subject) || 
                        [];
        
        setSingleForm(prev => ({
          ...prev,
          student_name: firstName,
          student_surname: lastName,
          student_id: extractedFields.student_id || extractedFields.centre_number || prev.student_id,
          institution: extractedFields.institution || extractedFields.centre_name || prev.institution,
          issue_date: extractedFields.issue_date || prev.issue_date,
          grade: extractedFields.grade || extractedFields.grades_summary || prev.grade,
          subjects: subjects,
          exam_session: extractedFields.examination_session || extractedFields.exam_session || prev.exam_session,
          certificate_number: extractedFields.certificate_number || 
                           (Array.isArray(extractedFields.certificate_numbers) ? extractedFields.certificate_numbers[0] : extractedFields.certificate_numbers) || 
                           prev.certificate_number
        }));
        
        // Add to OCR history
        setOcrHistory(prev => [{
          id: Date.now(),
          filename: file.name,
          timestamp: new Date().toISOString(),
          confidence: data.validation?.confidence?.overall || 85,
          student_name: firstName + ' ' + lastName,
          success: true
        }, ...prev].slice(0, 20));
        
        showNotification('success', '✅ Certificate scanned successfully! Please review the extracted data.');
      }
    } catch (err) {
      setOcrError(err?.message || 'Failed to extract data from certificate');
      
      // Add failed OCR to history
      setOcrHistory(prev => [{
        id: Date.now(),
        filename: file.name,
        timestamp: new Date().toISOString(),
        confidence: 0,
        error: err?.message,
        success: false
      }, ...prev].slice(0, 20));
      
      showNotification('error', 'Failed to extract data from certificate');
    } finally {
      setOcrLoading(false);
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
    setSingleFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Handle single certificate issuance
  const handleIssueSingle = async (e) => {
    e.preventDefault();
    setSingleError('');
    setSingleLoading(true);
    setSingleSuccess(null);

    try {
      const formData = new FormData();
      formData.append('student_name', `${singleForm.student_name} ${singleForm.student_surname}`.trim());
      formData.append('student_id', singleForm.student_id);
      formData.append('institution', singleForm.institution);
      formData.append('issue_date', singleForm.issue_date);
      formData.append('expiry_date', singleForm.expiry_date);
      formData.append('grade', singleForm.grade);
      formData.append('subjects', JSON.stringify(singleForm.subjects));
      formData.append('exam_session', singleForm.exam_session);
      formData.append('certificate_number', singleForm.certificate_number);
      formData.append('additional_info', singleForm.additional_info);
      
      if (singleFile) {
        formData.append('certificate_image', singleFile);
      }
      
      const response = await certificateApi.upload(formData);
      
      setSingleSuccess(response);
      
      showNotification('success', `✅ Certificate issued successfully! Hash: ${response.certificate_hash?.slice(0, 12)}...`);
      
      // Refresh data
      await Promise.all([
        fetchCertificates(),
        fetchStats(),
        generateChartData()
      ]);
      
      // Reset form
      setSingleForm({
        student_name: '',
        student_surname: '',
        student_id: '',
        institution: user?.institution || '',
        issue_date: format(new Date(), 'yyyy-MM-dd'),
        expiry_date: format(new Date().setFullYear(new Date().getFullYear() + 5), 'yyyy-MM-dd'),
        grade: '',
        subjects: [],
        exam_session: `November ${new Date().getFullYear()}`,
        certificate_number: '',
        additional_info: ''
      });
      
      setSingleFile(null);
      setExtractedData(null);
      setExtractedDisplay(null);
      setShowOcrSidebar(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      
      // Generate QR code for the certificate
      if (response.certificate_hash) {
        setQrData(response.certificate_hash);
        setShowQR(true);
        setTimeout(() => setShowQR(false), 5000);
      }
      
    } catch (err) {
      setSingleError(err?.message || 'Failed to issue certificate');
      showNotification('error', 'Failed to issue certificate');
    } finally {
      setSingleLoading(false);
    }
  };

  // Handle bulk upload
  const handleBulkUpload = async () => {
    setShowBulkModal(false);
    setBulkError('');
    setBulkResult(null);
    setBulkPct(0);
    setBulkProgress([]);
    setBulkLoading(true);

    try {
      const formData = new FormData();
      bulkFiles.forEach(file => {
        formData.append('certificates', file);
      });
      
      const response = await certificateApi.uploadCertificatesBulk(formData, (progress) => {
        setBulkPct(progress.percentage);
        setBulkProgress(progress.details || []);
      });
      
      setBulkResult(response);
      
      showNotification('success', `✅ Successfully processed ${response.success_count || 0} certificates`);
      
      // Refresh data
      await Promise.all([
        fetchCertificates(),
        fetchStats(),
        generateChartData()
      ]);
      
    } catch (err) {
      setBulkError(err?.message || 'Bulk upload failed');
      showNotification('error', 'Bulk upload failed');
    } finally {
      setBulkLoading(false);
      setBulkFiles([]);
    }
  };

  // Handle verification
  const handleVerify = async (e) => {
    e.preventDefault();
    setVerifyError('');
    setVerifyResult(null);
    setVerifyPct(0);
    setVerifyLoading(true);

    try {
      const formData = new FormData();
      
      if (verifyHash.trim()) {
        formData.append('certificate_hash', verifyHash.trim());
      }
      
      if (verifyFile) {
        formData.append('file', verifyFile);
      }

      const data = await certificateApi.verify(formData, (progress) => {
        setVerifyPct(progress.percentage);
      });
      
      const result = {
        verified: data.verified || data.valid || false,
        blockchain_verified: data.blockchain_verified || false,
        verification_id: data.verification_id || `VER_${Date.now()}`,
        certificate_data: data.certificate_data || data.extractedData,
        timestamp: data.timestamp || new Date().toISOString(),
        message: data.message || ''
      };
      
      setVerifyResult(result);
      
      // Add to verification history
      setVerifyHistory(prev => [{
        id: Date.now(),
        hash: verifyHash || (data.certificate_data?.certificate_hash?.slice(0, 16) + '...'),
        timestamp: new Date().toISOString(),
        result: result.verified ? 'valid' : 'invalid',
        method: verifyMethod
      }, ...prev].slice(0, 20));
      
      showNotification(
        result.verified ? 'success' : 'error',
        result.verified ? '✅ Certificate verified successfully!' : '❌ Certificate verification failed'
      );
      
    } catch (err) {
      setVerifyError(err?.message || 'Verification failed');
      showNotification('error', 'Verification failed');
    } finally {
      setVerifyLoading(false);
    }
  };

  // Handle revoke certificate
  const handleRevokeCertificate = async (certificateId) => {
    if (!window.confirm('Are you sure you want to revoke this certificate? This action cannot be undone.')) {
      return;
    }

    try {
      await certificateApi.revokeCertificate(certificateId);
      
      showNotification('success', '✅ Certificate revoked successfully');
      
      // Update certificate status
      setMyCertificates(prev => 
        prev.map(cert => 
          cert.id === certificateId ? { ...cert, status: 'revoked' } : cert
        )
      );
      
      // Refresh stats
      fetchStats();
      
    } catch (err) {
      showNotification('error', 'Failed to revoke certificate');
    }
  };

  // Handle profile update
  const handleProfileUpdate = async (updatedData) => {
    try {
      await updateUser(updatedData);
      showNotification('success', '✅ Profile updated successfully');
      setShowProfileEditor(false);
      fetchInstitutionInfo();
    } catch (error) {
      showNotification('error', 'Failed to update profile: ' + error.message);
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

  // Mark notification as read
  const markAsRead = async (notificationId) => {
    try {
      await userApi.markNotificationRead(notificationId);
      setNotifications(prev => 
        prev.map(n => n.id === notificationId ? { ...n, read: true } : n)
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (error) {
      console.error('Failed to mark notification as read:', error);
    }
  };

  // Export certificates
  const handleExport = async (format = 'csv') => {
    try {
      const data = await certificateApi.exportCertificates({
        format,
        status: statusFilter !== 'all' ? statusFilter : undefined,
        start_date: dateRange.start,
        end_date: dateRange.end
      });
      
      const blob = new Blob([data], { 
        type: format === 'csv' ? 'text/csv' : 'application/json' 
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `certificates_export_${format(new Date(), 'yyyy-MM-dd')}.${format}`;
      a.click();
      
      showNotification('success', '✅ Certificates exported successfully');
    } catch (error) {
      showNotification('error', 'Failed to export certificates');
    }
  };

  // Print certificate
  const handlePrint = (certificate) => {
    const printWindow = window.open('', '_blank');
    printWindow.document.write(`
      <html>
        <head>
          <title>Certificate - ${certificate.student_name}</title>
          <style>
            body { font-family: Arial, sans-serif; padding: 40px; }
            .certificate { border: 2px solid #000; padding: 40px; max-width: 800px; margin: 0 auto; }
            h1 { text-align: center; color: #333; }
            .details { margin-top: 30px; }
            .footer { margin-top: 50px; text-align: center; }
          </style>
        </head>
        <body>
          <div class="certificate">
            <h1>Certificate of Achievement</h1>
            <div class="details">
              <p><strong>Student:</strong> ${certificate.student_name}</p>
              <p><strong>ID:</strong> ${certificate.student_id}</p>
              <p><strong>Institution:</strong> ${certificate.institution}</p>
              <p><strong>Issue Date:</strong> ${format(parseISO(certificate.issue_date), 'MMMM dd, yyyy')}</p>
              <p><strong>Certificate Hash:</strong> ${certificate.certificate_hash}</p>
            </div>
            <div class="footer">
              <p>Verified on Blockchain</p>
              <p>${institutionInfo?.name || 'ECOL'}</p>
            </div>
          </div>
        </body>
      </html>
    `);
    printWindow.document.close();
    printWindow.print();
  };

  // Share certificate
  const handleShare = async (certificate) => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Certificate',
          text: `Certificate for ${certificate.student_name}`,
          url: `${window.location.origin}/verify/${certificate.certificate_hash}` 
        });
      } catch (error) {
        console.error('Share failed:', error);
      }
    } else {
      navigator.clipboard.writeText(`${window.location.origin}/verify/${certificate.certificate_hash}`);
      showNotification('success', '✅ Verification link copied to clipboard');
    }
  };

  // Filter certificates
  const filteredCertificates = useMemo(() => {
    let filtered = [...myCertificates];
    
    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(cert => cert.status === statusFilter);
    }
    
    // Apply search
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(cert => 
        cert.student_name?.toLowerCase().includes(term) ||
        cert.student_id?.toLowerCase().includes(term) ||
        cert.certificate_hash?.toLowerCase().includes(term) ||
        cert.institution?.toLowerCase().includes(term)
      );
    }
    
    // Apply sorting
    switch(sortBy) {
      case 'date_desc':
        filtered.sort((a, b) => new Date(b.issue_date) - new Date(a.issue_date));
        break;
      case 'date_asc':
        filtered.sort((a, b) => new Date(a.issue_date) - new Date(b.issue_date));
        break;
      case 'name_asc':
        filtered.sort((a, b) => (a.student_name || '').localeCompare(b.student_name || ''));
        break;
      case 'name_desc':
        filtered.sort((a, b) => (b.student_name || '').localeCompare(a.student_name || ''));
        break;
      default:
        break;
    }
    
    return filtered;
  }, [myCertificates, statusFilter, searchTerm, sortBy]);

  // Get status color
  const getStatusColor = (status) => {
    const colors = {
      verified: 'bg-green-100 text-green-800 border-green-200',
      pending: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      rejected: 'bg-red-100 text-red-800 border-red-200',
      revoked: 'bg-gray-100 text-gray-800 border-gray-200',
      issued: 'bg-blue-100 text-blue-800 border-blue-200'
    };
    return colors[status?.toLowerCase()] || colors.pending;
  };

  const getStatusIcon = (status) => {
    switch(status?.toLowerCase()) {
      case 'verified': return <FiCheckCircle className="text-green-600" />;
      case 'pending': return <FiClock className="text-yellow-600" />;
      case 'rejected': return <FiX className="text-red-600" />;
      case 'revoked': return <FiTrash2 className="text-gray-600" />;
      default: return <FiFileText className="text-blue-600" />;
    }
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'N/A';
    return format(parseISO(dateString), 'MMM dd, yyyy');
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-LS', {
      style: 'currency',
      currency: 'LSL'
    }).format(amount);
  };

  // Check if form is valid
  const canIssueSingle = useMemo(() => {
    return (
      (singleForm.student_name.trim().length > 0 || singleForm.student_surname.trim().length > 0) &&
      singleForm.student_id.trim().length > 0 &&
      singleForm.institution.trim().length > 0 &&
      singleForm.issue_date &&
      !singleLoading
    );
  }, [singleForm, singleLoading]);

  const canVerify = useMemo(() => {
    if (verifyLoading) return false;
    
    if (verifyMethod === 'hash') {
      return verifyHash.trim().length >= 32;
    } else if (verifyMethod === 'file') {
      return !!verifyFile;
    } else {
      return (verifyHash.trim().length >= 32 || !!verifyFile);
    }
  }, [verifyHash, verifyFile, verifyMethod, verifyLoading]);

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
                  Certificate QR Code
                </h3>
                <div className="bg-white p-4 rounded-xl flex justify-center">
                  <QRCodeCanvas
                    value={qrData}
                    size={200}
                    level="H"
                    includeMargin={true}
                  />
                </div>
                <p className="text-sm text-gray-500 dark:text-gray-400 text-center mt-4">
                  Scan to verify certificate authenticity
                </p>
                <button
                  onClick={() => setShowQR(false)}
                  className="mt-6 w-full px-4 py-2 bg-gradient-to-r from-green-500 to-blue-600 text-white rounded-xl hover:from-green-600 hover:to-blue-700"
                >
                  Close
                </button>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Modals */}
        <AnimatePresence>
          {showBulkModal && (
            <BulkUploadModal
              files={bulkFiles}
              setFiles={setBulkFiles}
              onClose={() => setShowBulkModal(false)}
              onConfirm={handleBulkUpload}
              loading={bulkLoading}
              progress={bulkProgress}
            />
          )}

          {showPreview && selectedCertificate && (
            <CertificatePreview
              certificate={selectedCertificate}
              onClose={() => {
                setShowPreview(false);
                setSelectedCertificate(null);
              }}
              onRevoke={() => handleRevokeCertificate(selectedCertificate.id)}
              onPrint={() => handlePrint(selectedCertificate)}
              onShare={() => handleShare(selectedCertificate)}
              institution={institutionInfo}
            />
          )}

          {showProfileEditor && (
            <ProfileEditor
              user={user}
              institution={institutionInfo}
              onClose={() => setShowProfileEditor(false)}
              onSave={handleProfileUpdate}
            />
          )}

          {showScanner && (
            <CertificateScanner
              onCapture={handleScannerCapture}
              onClose={() => setShowScanner(false)}
              scannerRef={scannerRef}
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
              onAccept={async () => {
                setShowOcrSidebar(false);
                
                // Save extracted data to database and hash to blockchain
                try {
                  setSingleLoading(true);
                  
                  // Prepare certificate data from OCR extraction
                  const certificateData = {
                    student_name: extractedData.studentName || '',
                    student_id: extractedData.studentId || '',
                    institution: extractedData.institution || user?.institution || '',
                    issue_date: extractedData.issueDate || format(new Date(), 'yyyy-MM-dd'),
                    expiry_date: format(new Date().setFullYear(new Date().getFullYear() + 5), 'yyyy-MM-dd'),
                    grade: extractedData.grade || '',
                    subjects: JSON.stringify(extractedData.subjects || []),
                    exam_session: extractedData.examSession || `November ${new Date().getFullYear()}`,
                    certificate_number: extractedData.certificateNumber || '',
                    additional_info: extractedData.additionalInfo || '',
                    certificate_hash: extractedData.certificateHash || '',
                    ocr_confidence: ocrConfidence,
                    ocr_extracted_at: new Date().toISOString()
                  };
                  
                  // Create form data for API submission
                  const formData = new FormData();
                  Object.keys(certificateData).forEach(key => {
                    formData.append(key, certificateData[key]);
                  });
                  
                  if (singleFile) {
                    formData.append('certificate_image', singleFile);
                  }
                  
                  // Submit to backend (which will save to database and hash to blockchain)
                  const response = await certificateApi.upload(formData);
                  
                  setSingleSuccess(response);
                  
                  showNotification('success', `✅ Certificate issued successfully! Hash: ${response.certificate_hash?.slice(0, 12)}...`);
                  
                  // Refresh data
                  await Promise.all([
                    fetchCertificates(),
                    fetchStats(),
                    generateChartData(),
                    fetchOcrHistory()
                  ]);
                  
                  // Generate QR code for certificate
                  if (response.certificate_hash) {
                    setQrData(response.certificate_hash);
                    setShowQR(true);
                    setTimeout(() => setShowQR(false), 5000);
                  }
                  
                  // Reset form
                  setSingleForm({
                    student_name: '',
                    student_surname: '',
                    student_id: '',
                    institution: user?.institution || '',
                    issue_date: format(new Date(), 'yyyy-MM-dd'),
                    expiry_date: format(new Date().setFullYear(new Date().getFullYear() + 5), 'yyyy-MM-dd'),
                    grade: '',
                    subjects: [],
                    exam_session: `November ${new Date().getFullYear()}`,
                    certificate_number: '',
                    additional_info: ''
                  });
                  
                  setSingleFile(null);
                  setExtractedData(null);
                  setExtractedDisplay(null);
                  setOcrConfidence(null);
                  
                  if (fileInputRef.current) {
                    fileInputRef.current.value = '';
                  }
                  
                } catch (error) {
                  console.error('Failed to save certificate data:', error);
                  showNotification('error', 'Failed to save certificate data to database');
                } finally {
                  setSingleLoading(false);
                }
              }}
              onRetry={() => {
                if (singleFile) {
                  handleFileUpload(singleFile);
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
                        className={`p-4 rounded-lg ${
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

        {/* Blockchain Status Indicator */}
        <BlockchainStatus />

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
                <div className="absolute inset-0 bg-gradient-to-r from-green-500 to-blue-500 rounded-xl blur-lg opacity-50 animate-pulse" />
                <div className="relative bg-gradient-to-r from-green-500 to-blue-500 p-3 rounded-xl shadow-lg">
                  <FaCertificate className="w-8 h-8 text-white" />
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
                    <h2 className="text-2xl font-bold bg-gradient-to-r from-green-400 to-blue-400 bg-clip-text text-transparent">
                      CertiVert
                    </h2>
                    <p className="text-xs text-gray-400 mt-1">Issuer Portal</p>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          </div>

          {/* User Profile Card */}
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
                <div className="w-12 h-12 rounded-full bg-gradient-to-r from-green-500 to-blue-500 flex items-center justify-center text-white font-bold text-xl shadow-lg">
                  {user?.username?.charAt(0).toUpperCase() || 'I'}
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
                    <p className="font-semibold text-lg truncate">{user?.username || 'Issuer'}</p>
                    <p className="text-xs text-gray-400 truncate">{user?.email || 'issuer@example.com'}</p>
                    <div className="flex items-center mt-2 space-x-2">
                      <span className="px-2 py-1 bg-green-600/30 text-green-300 rounded-full text-xs font-medium">
                        ISSUER
                      </span>
                      {user?.institution && (
                        <span className="px-2 py-1 bg-blue-600/30 text-blue-300 rounded-full text-xs font-medium truncate max-w-[100px]">
                          {user.institution}
                        </span>
                      )}
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          </div>

          {/* Quick Stats Widget */}
          {!sidebarCollapsed && issuerStats && (
            <div className="p-4 border-b border-gray-700/50">
              <h4 className="text-xs uppercase tracking-wider text-gray-400 mb-3 flex items-center">
                <span className="w-1 h-4 bg-green-500 rounded-full mr-2"></span>
                Today's Summary
              </h4>
              <div className="grid grid-cols-2 gap-3">
                <div className="bg-gray-800/50 rounded-lg p-3">
                  <p className="text-xs text-gray-400">Issued</p>
                  <p className="text-xl font-bold text-green-400">{issuerStats?.total ?? 0}</p>
                </div>
                <div className="bg-gray-800/50 rounded-lg p-3">
                  <p className="text-xs text-gray-400">Pending</p>
                  <p className="text-xl font-bold text-yellow-400">{issuerStats?.pending ?? 0}</p>
                </div>
                <div className="bg-gray-800/50 rounded-lg p-3 col-span-2">
                  <p className="text-xs text-gray-400 mb-1">Verification Rate</p>
                  <div className="flex items-center">
                    <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
                      <motion.div 
                        className="h-full bg-gradient-to-r from-green-500 to-green-400 rounded-full"
                        initial={{ width: 0 }}
                        animate={{ width: `${issuerStats?.total > 0 ? (issuerStats.verified / issuerStats.total) * 100 : 0}%` }}
                        transition={{ duration: 1 }}
                      />
                    </div>
                    <span className="text-xs text-gray-300 ml-2">
                      {issuerStats?.total > 0 ? Math.round((issuerStats.verified / issuerStats.total) * 100) : 0}%
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
                onClick={() => setActiveView('dashboard')}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 relative group ${
                  activeView === 'dashboard'
                    ? 'bg-gradient-to-r from-green-600 to-blue-600 text-white shadow-lg transform scale-105'
                    : 'text-gray-300 hover:bg-gray-700/50 hover:text-white'
                }`}
                whileHover={{ x: 5 }}
                whileTap={{ scale: 0.98 }}
              >
                <FiHome className="w-5 h-5" />
                <AnimatePresence>
                  {!sidebarCollapsed && (
                    <motion.span
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -10 }}
                      className="font-medium"
                    >
                      Dashboard
                    </motion.span>
                  )}
                </AnimatePresence>
                {activeView === 'dashboard' && !sidebarCollapsed && (
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
                onClick={() => setActiveView('issue')}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                  activeView === 'issue'
                    ? 'bg-gradient-to-r from-green-600 to-blue-600 text-white shadow-lg transform scale-105'
                    : 'text-gray-300 hover:bg-gray-700/50 hover:text-white'
                }`}
                whileHover={{ x: 5 }}
                whileTap={{ scale: 0.98 }}
              >
                <FiFileText className="w-5 h-5" />
                <AnimatePresence>
                  {!sidebarCollapsed && (
                    <motion.span
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -10 }}
                      className="font-medium"
                    >
                      Issue Certificate
                    </motion.span>
                  )}
                </AnimatePresence>
              </motion.button>

              <motion.button
                variants={itemVariants}
                onClick={() => setActiveView('bulk')}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                  activeView === 'bulk'
                    ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg transform scale-105'
                    : 'text-gray-300 hover:bg-gray-700/50 hover:text-white'
                }`}
                whileHover={{ x: 5 }}
                whileTap={{ scale: 0.98 }}
              >
                <FiUploadCloud className="w-5 h-5" />
                <AnimatePresence>
                  {!sidebarCollapsed && (
                    <motion.span
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -10 }}
                      className="font-medium"
                    >
                      Bulk Upload
                    </motion.span>
                  )}
                </AnimatePresence>
              </motion.button>

              <motion.button
                variants={itemVariants}
                onClick={() => setActiveView('verify')}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                  activeView === 'verify'
                    ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg transform scale-105'
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
                      Verify
                    </motion.span>
                  )}
                </AnimatePresence>
              </motion.button>

              <motion.button
                variants={itemVariants}
                onClick={() => setActiveView('certificates')}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                  activeView === 'certificates'
                    ? 'bg-gradient-to-r from-yellow-600 to-orange-600 text-white shadow-lg transform scale-105'
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
                      Certificates
                    </motion.span>
                  )}
                </AnimatePresence>
                {myCertificates.length > 0 && !sidebarCollapsed && (
                  <span className="ml-auto bg-white/20 px-2 py-0.5 rounded-full text-xs">
                    {myCertificates.length}
                  </span>
                )}
              </motion.button>

              <motion.button
                variants={itemVariants}
                onClick={() => setActiveView('settings')}
                className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                  activeView === 'settings'
                    ? 'bg-gradient-to-r from-gray-600 to-gray-700 text-white shadow-lg transform scale-105'
                    : 'text-gray-300 hover:bg-gray-700/50 hover:text-white'
                }`}
                whileHover={{ x: 5 }}
                whileTap={{ scale: 0.98 }}
              >
                <FiSettings className="w-5 h-5" />
                <AnimatePresence>
                  {!sidebarCollapsed && (
                    <motion.span
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      exit={{ opacity: 0, x: -10 }}
                      className="font-medium"
                    >
                      Settings
                    </motion.span>
                  )}
                </AnimatePresence>
              </motion.button>
            </motion.div>
          </nav>

          {/* Institution Info */}
          <AnimatePresence>
            {!sidebarCollapsed && institutionInfo && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
                className="px-4 py-3 mx-4 mb-4 bg-gray-800/50 rounded-xl"
              >
                <p className="text-xs text-gray-400 mb-1">Institution</p>
                <p className="text-sm font-medium text-white">{institutionInfo.name}</p>
                <p className="text-xs text-gray-400">ID: {institutionInfo.code}</p>
                <div className="mt-2 flex items-center">
                  <span className="text-xs text-gray-400">Balance:</span>
                  <span className="ml-2 text-sm font-bold text-green-400">
                    {formatCurrency(institutionInfo.credits || 0)}
                  </span>
                </div>
                <div className="mt-2 h-1 bg-gray-700 rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-gradient-to-r from-green-500 to-blue-500"
                    initial={{ width: 0 }}
                    animate={{ width: `${Math.min(100, ((institutionInfo.credits || 0) / 2000) * 100)}%` }}
                    transition={{ duration: 1 }}
                  />
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
          </div>

          {/* Sidebar Toggle */}
          <motion.button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="absolute bottom-6 -right-3 w-8 h-8 bg-gray-800 rounded-full flex items-center justify-center text-white border-2 border-gray-700 hover:bg-gray-700 transition-colors shadow-lg"
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
          >
            <FiMenu className={`w-4 h-4 transform transition-transform ${sidebarCollapsed ? 'rotate-180' : ''}`} />
          </motion.button>
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
                    {activeView === 'dashboard' && 'Issuer Dashboard'}
                    {activeView === 'issue' && 'Issue Certificate'}
                    {activeView === 'bulk' && 'Bulk Upload Certificates'}
                    {activeView === 'verify' && 'Verify Certificate'}
                    {activeView === 'certificates' && 'My Certificates'}
                    {activeView === 'settings' && 'Account Settings'}
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
                    {activeView === 'dashboard' && 'Overview of your certificate issuance activities'}
                    {activeView === 'issue' && 'Issue a new LGCSE certificate with OCR auto-fill'}
                    {activeView === 'bulk' && 'Upload multiple certificates at once with OCR processing'}
                    {activeView === 'verify' && 'Verify certificate authenticity on blockchain'}
                    {activeView === 'certificates' && `Manage your issued certificates (${filteredCertificates.length} total)`}
                    {activeView === 'settings' && 'Manage your profile and preferences'}
                  </p>
                </div>

                {/* Search and Actions */}
                <div className="flex items-center space-x-4">
                  {/* Quick Actions */}
                  {activeView === 'certificates' && (
                    <>
                      {/* View Mode Toggle */}
                      <div className="flex border-2 border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                        <button
                          onClick={() => setViewMode('table')}
                          className={`p-2 ${viewMode === 'table' ? 'bg-green-500 text-white' : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400'}`}
                        >
                          <FiList className="w-5 h-5" />
                        </button>
                        <button
                          onClick={() => setViewMode('grid')}
                          className={`p-2 ${viewMode === 'grid' ? 'bg-green-500 text-white' : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-400'}`}
                        >
                          <FiGrid className="w-5 h-5" />
                        </button>
                      </div>

                      {/* Sort Dropdown */}
                      <select
                        value={sortBy}
                        onChange={(e) => setSortBy(e.target.value)}
                        className="px-3 py-2 border-2 border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:border-green-500 focus:ring focus:ring-green-200 dark:focus:ring-green-800 transition-all"
                      >
                        <option value="date_desc">Newest First</option>
                        <option value="date_asc">Oldest First</option>
                        <option value="name_asc">Name A-Z</option>
                        <option value="name_desc">Name Z-A</option>
                      </select>

                      {/* Export Button */}
                      <motion.button
                        onClick={() => handleExport('csv')}
                        className="p-2 border-2 border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                      >
                        <FiDownload className="w-5 h-5 text-gray-600 dark:text-gray-300" />
                      </motion.button>
                    </>
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
                    onClick={() => setDarkMode(!darkMode)}
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
                    onClick={() => setShowProfileEditor(true)}
                  >
                    <div className="w-10 h-10 rounded-full bg-gradient-to-r from-green-500 to-blue-500 flex items-center justify-center text-white font-bold shadow-lg">
                      {user?.username?.charAt(0).toUpperCase() || 'I'}
                    </div>
                    <motion.div 
                      className="absolute -bottom-1 -right-1 w-3 h-3 bg-green-500 border-2 border-white dark:border-gray-800 rounded-full"
                      animate={{ scale: [1, 1.2, 1] }}
                      transition={{ repeat: Infinity, duration: 2 }}
                    />
                  </motion.div>
                </div>
              </div>

              {/* Filters for Certificates View */}
              {activeView === 'certificates' && (
                <motion.div
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className="mt-4 flex items-center space-x-4"
                >
                  <div className="flex-1 relative">
                    <FiSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
                    <input
                      type="text"
                      placeholder="Search by name, ID, or hash..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 border-2 border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:border-green-500 focus:ring focus:ring-green-200 dark:focus:ring-green-800 transition-all"
                    />
                  </div>
                  
                  <select
                    value={statusFilter}
                    onChange={(e) => setStatusFilter(e.target.value)}
                    className="px-4 py-2 border-2 border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:border-green-500 focus:ring focus:ring-green-200 dark:focus:ring-green-800 transition-all"
                  >
                    <option value="all">All Status</option>
                    <option value="verified">Verified</option>
                    <option value="pending">Pending</option>
                    <option value="rejected">Rejected</option>
                    <option value="revoked">Revoked</option>
                  </select>

                  <input
                    type="date"
                    value={dateRange.start}
                    onChange={(e) => setDateRange({...dateRange, start: e.target.value})}
                    className="px-4 py-2 border-2 border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:border-green-500 focus:ring focus:ring-green-200 dark:focus:ring-green-800 transition-all"
                  />
                  <span className="text-gray-500">to</span>
                  <input
                    type="date"
                    value={dateRange.end}
                    onChange={(e) => setDateRange({...dateRange, end: e.target.value})}
                    className="px-4 py-2 border-2 border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:border-green-500 focus:ring focus:ring-green-200 dark:focus:ring-green-800 transition-all"
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
            {(singleError || bulkError || verifyError || ocrError) && (
              <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="mx-8 mt-4 px-6 py-4 rounded-xl bg-gradient-to-r from-red-500 to-red-600 text-white shadow-lg flex items-center"
              >
                <FiAlertCircle className="w-5 h-5 mr-3" />
                {singleError || bulkError || verifyError || ocrError}
                <button
                  onClick={() => {
                    setSingleError('');
                    setBulkError('');
                    setVerifyError('');
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
                {/* Dashboard View */}
                {activeView === 'dashboard' && (
                  <motion.div
                    variants={containerVariants}
                    initial="hidden"
                    animate="visible"
                    className="space-y-8"
                  >
                    {/* Stats Cards */}
                    <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-4 gap-6">
                      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 transform hover:scale-105 transition-all duration-300 border-l-4 border-green-500">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-gray-500 dark:text-gray-400 text-sm">Total Issued</p>
                            <p className="text-3xl font-bold text-gray-800 dark:text-white">{issuerStats?.total ?? 0}</p>
                          </div>
                          <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-xl flex items-center justify-center">
                            <FiFileText className="w-6 h-6 text-green-600 dark:text-green-400" />
                          </div>
                        </div>
                        <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">All time certificates</p>
                      </div>

                      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 transform hover:scale-105 transition-all duration-300 border-l-4 border-blue-500">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-gray-500 dark:text-gray-400 text-sm">Verified</p>
                            <p className="text-3xl font-bold text-gray-800 dark:text-white">{issuerStats?.verified ?? 0}</p>
                          </div>
                          <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-xl flex items-center justify-center">
                            <FiCheckCircle className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                          </div>
                        </div>
                        <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">
                          {issuerStats?.total > 0 ? Math.round((issuerStats.verified / issuerStats.total) * 100) : 0}% success rate
                        </p>
                      </div>

                      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 transform hover:scale-105 transition-all duration-300 border-l-4 border-yellow-500">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-gray-500 dark:text-gray-400 text-sm">Pending</p>
                            <p className="text-3xl font-bold text-gray-800 dark:text-white">{issuerStats?.pending ?? 0}</p>
                          </div>
                          <div className="w-12 h-12 bg-yellow-100 dark:bg-yellow-900/30 rounded-xl flex items-center justify-center">
                            <FiClock className="w-6 h-6 text-yellow-600 dark:text-yellow-400" />
                          </div>
                        </div>
                        <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">Awaiting verification</p>
                      </div>

                      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6 transform hover:scale-105 transition-all duration-300 border-l-4 border-purple-500">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-gray-500 dark:text-gray-400 text-sm">OCR Today</p>
                            <p className="text-3xl font-bold text-gray-800 dark:text-white">{issuerStats?.ocr_today ?? 0}</p>
                          </div>
                          <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/30 rounded-xl flex items-center justify-center">
                            <FiCamera className="w-6 h-6 text-purple-600 dark:text-purple-400" />
                          </div>
                        </div>
                        <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">Certificates scanned</p>
                      </div>
                    </motion.div>

                    {/* Charts Section */}
                    <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      {/* Issuance Trend Chart */}
                      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                        <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">
                          Issuance Trend
                        </h3>
                        {chartData.issuanceTrend && (
                          <Line
                            data={chartData.issuanceTrend}
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

                      {/* Status Distribution Chart */}
                      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                        <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">
                          Status Distribution
                        </h3>
                        {chartData.statusDistribution && (
                          <Doughnut
                            data={chartData.statusDistribution}
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

                    {/* Monthly Comparison Chart */}
                    <motion.div variants={itemVariants} className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-6">
                      <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">
                        Monthly Comparison
                      </h3>
                      {chartData.monthlyComparison && (
                        <Bar
                          data={chartData.monthlyComparison}
                          options={{
                            responsive: true,
                            plugins: {
                              legend: {
                                position: 'top'
                              }
                            },
                            scales: {
                              y: {
                                beginAtZero: true
                              }
                            }
                          }}
                        />
                      )}
                    </motion.div>

                    {/* OCR Quick Scan Card */}
                    <motion.div variants={itemVariants} className="bg-gradient-to-r from-purple-500 to-indigo-600 rounded-2xl shadow-xl p-6 text-white">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="text-xl font-bold mb-2">Quick Certificate Scan</h3>
                          <p className="text-purple-100 mb-4">Upload a certificate image to auto-fill the issuance form</p>
                          <div className="flex space-x-4">
                            <button
                              onClick={() => {
                                setActiveView('issue');
                                fileInputRef.current?.click();
                              }}
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

                    {/* Recent Certificates */}
                    <motion.div variants={itemVariants} className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl overflow-hidden">
                      <div className="px-6 py-4 bg-gradient-to-r from-green-500 to-blue-600 flex justify-between items-center">
                        <h3 className="text-lg font-semibold text-white">Recent Certificates</h3>
                        <button
                          onClick={() => setActiveView('certificates')}
                          className="px-3 py-1 bg-white/20 hover:bg-white/30 rounded-lg text-white text-sm transition-colors"
                        >
                          View All
                        </button>
                      </div>
                      
                      {filteredCertificates.length === 0 ? (
                        <div className="p-12 text-center">
                          <div className="text-6xl mb-4">📜</div>
                          <p className="text-gray-500 dark:text-gray-400 text-lg">No certificates issued yet</p>
                          <p className="text-sm text-gray-400 dark:text-gray-500 mt-2">Start by issuing your first certificate</p>
                          <button
                            onClick={() => setActiveView('issue')}
                            className="mt-4 px-6 py-2 bg-gradient-to-r from-green-500 to-blue-600 text-white rounded-xl hover:from-green-600 hover:to-blue-700 transition-all"
                          >
                            Issue Certificate
                          </button>
                        </div>
                      ) : (
                        <div className="overflow-x-auto">
                          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                            <thead className="bg-gray-50 dark:bg-gray-900">
                              <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Student</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">ID</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Hash</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Issue Date</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                              </tr>
                            </thead>
                            <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                              {filteredCertificates.slice(0, 5).map((cert, index) => (
                                <motion.tr
                                  key={cert.id}
                                  initial={{ opacity: 0, x: -20 }}
                                  animate={{ opacity: 1, x: 0 }}
                                  transition={{ delay: index * 0.1 }}
                                  className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                                >
                                  <td className="px-6 py-4 whitespace-nowrap">
                                    <div className="flex items-center">
                                      <div className="w-8 h-8 rounded-full bg-gradient-to-r from-green-500 to-blue-500 flex items-center justify-center text-white text-xs font-bold mr-2">
                                        {cert.student_name?.charAt(0).toUpperCase()}
                                      </div>
                                      <span className="text-sm font-medium text-gray-900 dark:text-white">
                                        {cert.student_name}
                                      </span>
                                    </div>
                                  </td>
                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                    {cert.student_id}
                                  </td>
                                  <td className="px-6 py-4 whitespace-nowrap">
                                    <span className="font-mono text-xs bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded dark:text-gray-300">
                                      {cert.certificate_hash?.slice(0, 12)}...
                                    </span>
                                  </td>
                                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                    {formatDate(cert.issue_date)}
                                  </td>
                                  <td className="px-6 py-4 whitespace-nowrap">
                                    <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(cert.status)}`}>
                                      {getStatusIcon(cert.status)} {cert.status}
                                    </span>
                                  </td>
                                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                                    <button
                                      onClick={() => {
                                        setSelectedCertificate(cert);
                                        setShowPreview(true);
                                      }}
                                      className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300 font-medium mr-3"
                                    >
                                      View
                                    </button>
                                    {cert.status === 'pending' && (
                                      <button
                                        onClick={() => handleRevokeCertificate(cert.id)}
                                        className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300 font-medium"
                                      >
                                        Revoke
                                      </button>
                                    )}
                                  </td>
                                </motion.tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      )}
                    </motion.div>

                    {/* Recent Activity */}
                    <motion.div variants={itemVariants}>
                      <RecentActivity limit={5} />
                    </motion.div>
                  </motion.div>
                )}

                {/* Issue Certificate View */}
                {activeView === 'issue' && (
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Issue Form */}
                    <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-2xl shadow-xl overflow-hidden">
                      <div className="px-6 py-4 bg-gradient-to-r from-green-500 to-blue-600">
                        <h3 className="text-lg font-semibold text-white flex items-center">
                          <FiFileText className="mr-2" />
                          Issue New Certificate with OCR
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
                                <p className="text-sm text-gray-500 dark:text-gray-400">Upload certificate to automatically extract data</p>
                              </div>
                            </div>
                            <div className="flex space-x-2">
                              <input
                                type="file"
                                ref={fileInputRef}
                                accept=".pdf,image/*"
                                onChange={(e) => handleFileUpload(e.target.files?.[0] || null)}
                                className="hidden"
                                id="certificate-file"
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
                                    Upload File
                                  </>
                                )}
                              </button>
                              <button
                                onClick={() => setShowScanner(true)}
                                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center"
                              >
                                <FiCamera className="mr-2" />
                                Camera
                              </button>
                            </div>
                          </div>
                          
                          {singleFile && !ocrLoading && (
                            <div className="mt-3 flex items-center justify-between bg-white dark:bg-gray-700 p-2 rounded-lg">
                              <div className="flex items-center">
                                <FiFile className="w-5 h-5 mr-2 text-gray-500" />
                                <span className="text-sm text-gray-600 dark:text-gray-300">{singleFile.name}</span>
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
                                <span className="text-xs text-purple-600 dark:text-purple-400">Processing</span>
                              </div>
                              <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                <motion.div
                                  className="h-2 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full"
                                  animate={{ width: ['0%', '100%'] }}
                                  transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                                />
                              </div>
                            </div>
                          )}
                        </div>

                        <form onSubmit={handleIssueSingle} className="space-y-4">
                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                First Name <span className="text-red-500">*</span>
                              </label>
                              <input
                                type="text"
                                value={singleForm.student_name}
                                onChange={(e) => setSingleForm({...singleForm, student_name: e.target.value})}
                                placeholder="First name"
                                className="w-full rounded-xl border-2 border-gray-200 dark:border-gray-700 dark:bg-gray-900 dark:text-white px-4 py-2 text-sm focus:border-green-500 focus:ring focus:ring-green-200 dark:focus:ring-green-800"
                                required
                              />
                            </div>
                            <div>
                              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Surname <span className="text-red-500">*</span>
                              </label>
                              <input
                                type="text"
                                value={singleForm.student_surname}
                                onChange={(e) => setSingleForm({...singleForm, student_surname: e.target.value})}
                                placeholder="Surname"
                                className="w-full rounded-xl border-2 border-gray-200 dark:border-gray-700 dark:bg-gray-900 dark:text-white px-4 py-2 text-sm focus:border-green-500 focus:ring focus:ring-green-200 dark:focus:ring-green-800"
                                required
                              />
                            </div>
                          </div>

                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Student ID <span className="text-red-500">*</span>
                              </label>
                              <input
                                type="text"
                                value={singleForm.student_id}
                                onChange={(e) => setSingleForm({...singleForm, student_id: e.target.value})}
                                placeholder="LGCSE ID"
                                className="w-full rounded-xl border-2 border-gray-200 dark:border-gray-700 dark:bg-gray-900 dark:text-white px-4 py-2 text-sm focus:border-green-500 focus:ring focus:ring-green-200 dark:focus:ring-green-800"
                                required
                              />
                            </div>
                            <div>
                              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Certificate Number
                              </label>
                              <input
                                type="text"
                                value={singleForm.certificate_number}
                                onChange={(e) => setSingleForm({...singleForm, certificate_number: e.target.value})}
                                placeholder="Certificate number"
                                className="w-full rounded-xl border-2 border-gray-200 dark:border-gray-700 dark:bg-gray-900 dark:text-white px-4 py-2 text-sm focus:border-green-500 focus:ring focus:ring-green-200 dark:focus:ring-green-800"
                              />
                            </div>
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                              Institution <span className="text-red-500">*</span>
                            </label>
                            <input
                              type="text"
                              value={singleForm.institution}
                              onChange={(e) => setSingleForm({...singleForm, institution: e.target.value})}
                              placeholder="Institution name"
                              className="w-full rounded-xl border-2 border-gray-200 dark:border-gray-700 dark:bg-gray-900 dark:text-white px-4 py-2 text-sm focus:border-green-500 focus:ring focus:ring-green-200 dark:focus:ring-green-800"
                              required
                            />
                          </div>

                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Issue Date <span className="text-red-500">*</span>
                              </label>
                              <input
                                type="date"
                                value={singleForm.issue_date}
                                onChange={(e) => setSingleForm({...singleForm, issue_date: e.target.value})}
                                className="w-full rounded-xl border-2 border-gray-200 dark:border-gray-700 dark:bg-gray-900 dark:text-white px-4 py-2 text-sm focus:border-green-500 focus:ring focus:ring-green-200 dark:focus:ring-green-800"
                                required
                              />
                            </div>
                            <div>
                              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Expiry Date
                              </label>
                              <input
                                type="date"
                                value={singleForm.expiry_date}
                                onChange={(e) => setSingleForm({...singleForm, expiry_date: e.target.value})}
                                className="w-full rounded-xl border-2 border-gray-200 dark:border-gray-700 dark:bg-gray-900 dark:text-white px-4 py-2 text-sm focus:border-green-500 focus:ring focus:ring-green-200 dark:focus:ring-green-800"
                              />
                            </div>
                          </div>

                          <div className="grid grid-cols-2 gap-4">
                            <div>
                              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Exam Session
                              </label>
                              <input
                                type="text"
                                value={singleForm.exam_session}
                                onChange={(e) => setSingleForm({...singleForm, exam_session: e.target.value})}
                                placeholder="e.g., November 2023"
                                className="w-full rounded-xl border-2 border-gray-200 dark:border-gray-700 dark:bg-gray-900 dark:text-white px-4 py-2 text-sm focus:border-green-500 focus:ring focus:ring-green-200 dark:focus:ring-green-800"
                              />
                            </div>
                            <div>
                              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Grade
                              </label>
                              <input
                                type="text"
                                value={singleForm.grade}
                                onChange={(e) => setSingleForm({...singleForm, grade: e.target.value})}
                                placeholder="e.g., A, B, C"
                                className="w-full rounded-xl border-2 border-gray-200 dark:border-gray-700 dark:bg-gray-900 dark:text-white px-4 py-2 text-sm focus:border-green-500 focus:ring focus:ring-green-200 dark:focus:ring-green-800"
                              />
                            </div>
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                              Subjects (comma separated)
                            </label>
                            <input
                              type="text"
                              value={singleForm.subjects.join(', ')}
                              onChange={(e) => setSingleForm({
                                ...singleForm, 
                                subjects: e.target.value.split(',').map(s => s.trim()).filter(s => s)
                              })}
                              placeholder="Mathematics, English, Science"
                              className="w-full rounded-xl border-2 border-gray-200 dark:border-gray-700 dark:bg-gray-900 dark:text-white px-4 py-2 text-sm focus:border-green-500 focus:ring focus:ring-green-200 dark:focus:ring-green-800"
                            />
                          </div>

                          <div>
                            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                              Additional Information
                            </label>
                            <textarea
                              value={singleForm.additional_info}
                              onChange={(e) => setSingleForm({...singleForm, additional_info: e.target.value})}
                              placeholder="Any additional notes..."
                              rows={3}
                              className="w-full rounded-xl border-2 border-gray-200 dark:border-gray-700 dark:bg-gray-900 dark:text-white px-4 py-2 text-sm focus:border-green-500 focus:ring focus:ring-green-200 dark:focus:ring-green-800"
                            />
                          </div>

                          <motion.button
                            type="submit"
                            disabled={!canIssueSingle}
                            className={`w-full px-6 py-3 rounded-xl text-white font-medium transition-all transform hover:scale-105 ${
                              canIssueSingle 
                                ? 'bg-gradient-to-r from-green-500 to-blue-600 hover:from-green-600 hover:to-blue-700 shadow-lg' 
                                : 'bg-gray-300 dark:bg-gray-600 cursor-not-allowed'
                            }`}
                            whileHover={canIssueSingle ? { scale: 1.05 } : {}}
                            whileTap={canIssueSingle ? { scale: 0.95 } : {}}
                          >
                            {singleLoading ? (
                              <span className="flex items-center justify-center">
                                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                Issuing...
                              </span>
                            ) : 'Issue Certificate'}
                          </motion.button>
                        </form>

                        {singleSuccess && (
                          <motion.div
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="mt-4 p-4 bg-green-50 dark:bg-green-900/20 rounded-lg"
                          >
                            <p className="text-sm text-green-700 dark:text-green-400">
                              ✅ Certificate issued successfully!
                            </p>
                            <p className="text-xs font-mono mt-2 text-gray-600 dark:text-gray-400">
                              Hash: {singleSuccess.certificate_hash}
                            </p>
                          </motion.div>
                        )}
                      </div>
                    </div>

                    {/* OCR Preview & Tips */}
                    <div className="space-y-6">
                      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-6">
                        <h4 className="text-sm font-semibold text-gray-800 dark:text-white mb-4 flex items-center">
                          <FiStar className="mr-2 text-yellow-500" />
                          OCR Preview
                        </h4>
                        
                        {singleForm.student_name || singleForm.student_surname ? (
                          <div className="bg-gradient-to-br from-green-50 to-blue-50 dark:from-green-900/20 dark:to-blue-900/20 rounded-xl p-6">
                            <div className="text-center mb-4">
                              <div className="w-16 h-16 mx-auto bg-gradient-to-r from-green-500 to-blue-500 rounded-full flex items-center justify-center text-white text-2xl mb-2">
                                {(singleForm.student_name?.charAt(0) || '') + (singleForm.student_surname?.charAt(0) || '')}
                              </div>
                              <h3 className="font-bold text-gray-800 dark:text-white">
                                {singleForm.student_name} {singleForm.student_surname}
                              </h3>
                              <p className="text-sm text-gray-500 dark:text-gray-400">ID: {singleForm.student_id || '______'}</p>
                            </div>
                            <div className="space-y-2 text-sm">
                              <div className="flex justify-between">
                                <span className="text-gray-500 dark:text-gray-400">Institution:</span>
                                <span className="font-medium text-gray-800 dark:text-white">{singleForm.institution || '______'}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-500 dark:text-gray-400">Issue Date:</span>
                                <span className="font-medium text-gray-800 dark:text-white">{singleForm.issue_date}</span>
                              </div>
                              <div className="flex justify-between">
                                <span className="text-gray-500 dark:text-gray-400">Subjects:</span>
                                <span className="font-medium text-gray-800 dark:text-white">{singleForm.subjects.length || 0}</span>
                              </div>
                              {ocrConfidence && (
                                <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
                                  <div className="flex justify-between items-center">
                                    <span className="text-gray-500 dark:text-gray-400">OCR Confidence:</span>
                                    <span className={`font-medium ${
                                      ocrConfidence > 80 ? 'text-green-600' :
                                      ocrConfidence > 60 ? 'text-yellow-600' : 'text-red-600'
                                    }`}>
                                      {ocrConfidence}%
                                    </span>
                                  </div>
                                  <div className="mt-2 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                    <motion.div
                                      className={`h-1.5 rounded-full ${
                                        ocrConfidence > 80 ? 'bg-green-500' :
                                        ocrConfidence > 60 ? 'bg-yellow-500' : 'bg-red-500'
                                      }`}
                                      initial={{ width: 0 }}
                                      animate={{ width: `${ocrConfidence}%` }}
                                      transition={{ duration: 1 }}
                                    />
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        ) : (
                          <div className="text-center py-12">
                            <FiCamera className="w-12 h-12 mx-auto text-gray-300 dark:text-gray-600 mb-3" />
                            <p className="text-gray-500 dark:text-gray-400">Fill in the form or upload a certificate</p>
                          </div>
                        )}
                      </div>
                      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-6">
                        <h4 className="text-sm font-semibold text-gray-800 dark:text-white mb-3">OCR Tips</h4>
                        <ul className="space-y-2 text-sm text-gray-600 dark:text-gray-400">
                          <li className="flex items-center">
                            <span className="w-1.5 h-1.5 bg-green-500 rounded-full mr-2"></span>
                            Supported formats: PDF, JPEG, PNG (max 10MB)
                          </li>
                          <li className="flex items-center">
                            <span className="w-1.5 h-1.5 bg-green-500 rounded-full mr-2"></span>
                            Ensure certificate is clear and well-lit
                          </li>
                          <li className="flex items-center">
                            <span className="w-1.5 h-1.5 bg-green-500 rounded-full mr-2"></span>
                            Review extracted data before issuing
                          </li>
                          <li className="flex items-center">
                            <span className="w-1.5 h-1.5 bg-green-500 rounded-full mr-2"></span>
                            OCR accuracy: 95%+ for clear images
                          </li>
                          <li className="flex items-center">
                            <span className="w-1.5 h-1.5 bg-green-500 rounded-full mr-2"></span>
                            Manual editing available after extraction
                          </li>
                        </ul>

                        {ocrHistory.length > 0 && (
                          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                            <h5 className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-2">
                              Recent OCR Scans
                            </h5>
                            <div className="space-y-2">
                              {ocrHistory.slice(0, 3).map((item) => (
                                <div key={item.id} className="flex items-center justify-between text-xs">
                                  <div className="flex items-center">
                                    <span className={item.success ? 'text-green-600' : 'text-red-600'}>
                                      {item.success ? '✓' : '✗'}
                                    </span>
                                    <span className="ml-2 text-gray-600 dark:text-gray-400 truncate max-w-[120px]">
                                      {item.filename}
                                    </span>
                                  </div>
                                  <span className="text-gray-400">
                                    {item.confidence > 0 ? `${item.confidence}%` : ''}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
                {/* Bulk Upload View */}
                {activeView === 'bulk' && (
                  <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl overflow-hidden">
                    <div className="px-6 py-4 bg-gradient-to-r from-purple-500 to-pink-600">
                      <h3 className="text-lg font-semibold text-white flex items-center">
                        <FiUploadCloud className="mr-2" />
                        Bulk Certificate Upload with OCR
                      </h3>
                    </div>
                    
                    <div className="p-6">
                      <div className="mb-6">
                        <div className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-xl p-12 text-center hover:border-purple-500 dark:hover:border-purple-400 transition-colors">
                          <input
                            type="file"
                            multiple
                            accept=".pdf,image/*"
                            onChange={(e) => setBulkFiles(Array.from(e.target.files || []))}
                            className="hidden"
                            id="bulk-upload"
                          />
                          <label htmlFor="bulk-upload" className="cursor-pointer">
                            <FiUploadCloud className="w-16 h-16 mx-auto text-gray-400 dark:text-gray-500 mb-4" />
                            <p className="text-xl text-gray-600 dark:text-gray-300 mb-2">Click to select files or drag and drop</p>
                            <p className="text-sm text-gray-400 dark:text-gray-500">Multiple PDF or Image files supported (OCR will extract data)</p>
                          </label>
                          {bulkFiles.length > 0 && (
                            <div className="mt-4">
                              <span className="inline-flex items-center px-4 py-2 rounded-full text-sm bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-300">
                                <FiFile className="mr-2" />
                                {bulkFiles.length} file(s) selected
                              </span>
                            </div>
                          )}
                        </div>
                      </div>

                      {bulkFiles.length > 0 && (
                        <div className="mb-6">
                          <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Selected Files:</h4>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                            {bulkFiles.map((file, index) => (
                              <div key={index} className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 flex items-center">
                                <FiFile className="w-5 h-5 mr-2 text-gray-500" />
                                <div className="flex-1 truncate">
                                  <p className="text-xs font-medium truncate text-gray-800 dark:text-gray-200">{file.name}</p>
                                  <p className="text-xs text-gray-400">{(file.size / 1024).toFixed(1)} KB</p>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="flex justify-between items-center">
                        <motion.button
                          onClick={() => setShowBulkModal(true)}
                          disabled={bulkFiles.length === 0 || bulkLoading}
                          className={`px-8 py-4 rounded-xl text-white font-medium transition-all transform hover:scale-105 ${
                            bulkFiles.length > 0 && !bulkLoading
                              ? 'bg-gradient-to-r from-purple-500 to-pink-600 hover:from-purple-600 hover:to-pink-700 shadow-lg'
                              : 'bg-gray-300 dark:bg-gray-600 cursor-not-allowed'
                          }`}
                          whileHover={bulkFiles.length > 0 && !bulkLoading ? { scale: 1.05 } : {}}
                          whileTap={bulkFiles.length > 0 && !bulkLoading ? { scale: 0.95 } : {}}
                        >
                          {bulkLoading ? (
                            <span className="flex items-center">
                              <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                              </svg>
                              Processing... {bulkPct}%
                            </span>
                          ) : 'Process Bulk Upload with OCR'}
                        </motion.button>

                        {bulkFiles.length > 0 && !bulkLoading && (
                          <button
                            onClick={() => setBulkFiles([])}
                            className="text-sm text-gray-500 dark:text-gray-400 hover:text-red-500 transition-colors"
                          >
                            Clear all files
                          </button>
                        )}
                      </div>

                      {bulkLoading && (
                        <div className="mt-6 space-y-2">
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-600 dark:text-gray-400">Processing files with OCR</span>
                            <span className="font-medium text-purple-600 dark:text-purple-400">{bulkPct}%</span>
                          </div>
                          <div className="h-2 w-full rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
                            <motion.div 
                              className="h-2 rounded-full bg-gradient-to-r from-purple-500 to-pink-600"
                              initial={{ width: 0 }}
                              animate={{ width: `${bulkPct}%` }}
                              transition={{ duration: 0.3 }}
                            />
                          </div>
                          
                          {bulkProgress.length > 0 && (
                            <div className="mt-4 max-h-40 overflow-y-auto">
                              {bulkProgress.map((item, idx) => (
                                <div key={idx} className="flex items-center justify-between text-xs py-1 border-b border-gray-100 dark:border-gray-700">
                                  <span className="truncate max-w-[200px]">{item.filename}</span>
                                  <span className={item.status === 'success' ? 'text-green-600' : 'text-yellow-600'}>
                                    {item.status}
                                  </span>
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}

                      {bulkResult && (
                        <motion.div
                          initial={{ opacity: 0, y: 20 }}
                          animate={{ opacity: 1, y: 0 }}
                          className="mt-8"
                        >
                          <h4 className="font-medium text-gray-800 dark:text-white mb-4">Upload Results</h4>
                          <div className="grid grid-cols-3 gap-4 mb-4">
                            <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-4 text-center">
                              <p className="text-2xl font-bold text-green-600 dark:text-green-400">{bulkResult.success_count}</p>
                              <p className="text-xs text-gray-500 dark:text-gray-400">Successful</p>
                            </div>
                            <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-4 text-center">
                              <p className="text-2xl font-bold text-red-600 dark:text-red-400">{bulkResult.failure_count}</p>
                              <p className="text-xs text-gray-500 dark:text-gray-400">Failed</p>
                            </div>
                            <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 text-center">
                              <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">{bulkResult.total_processed}</p>
                              <p className="text-xs text-gray-500 dark:text-gray-400">Total</p>
                            </div>
                          </div>

                          <div className="border dark:border-gray-700 rounded-xl overflow-hidden">
                            <table className="min-w-full text-sm">
                              <thead className="bg-gray-50 dark:bg-gray-900">
                                <tr>
                                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">File</th>
                                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Status</th>
                                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Hash</th>
                                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Student</th>
                                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">OCR Confidence</th>
                                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Error</th>
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                                {bulkResult.results?.map((r, idx) => (
                                  <tr key={idx} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-800 dark:text-gray-200">{r.filename}</td>
                                    <td className="px-4 py-3 whitespace-nowrap">
                                      <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                                        r.success ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400' : 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                                      }`}>
                                        {r.success ? 'Success' : 'Failed'}
                                      </span>
                                    </td>
                                    <td className="px-4 py-3 whitespace-nowrap font-mono text-xs text-gray-600 dark:text-gray-400">
                                      {r.certificate_hash ? `${r.certificate_hash.slice(0, 12)}...` : '-'}
                                    </td>
                                    <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-800 dark:text-gray-200">{r.extracted?.student_name || '-'}</td>
                                    <td className="px-4 py-3 whitespace-nowrap">
                                      {r.ocr_confidence ? (
                                        <span className={`text-xs font-medium ${
                                          r.ocr_confidence > 80 ? 'text-green-600' : 
                                          r.ocr_confidence > 60 ? 'text-yellow-600' : 'text-red-600'
                                        }`}>
                                          {r.ocr_confidence}%
                                        </span>
                                      ) : '-'}
                                    </td>
                                    <td className="px-4 py-3 whitespace-nowrap text-xs text-red-600 dark:text-red-400">{r.error || ''}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        </motion.div>
                      )}
                    </div>
                  </div>
                )}

                {/* Verify View */}
                {activeView === 'verify' && (
                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Verification Form */}
                    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl overflow-hidden">
                      <div className="px-6 py-4 bg-gradient-to-r from-blue-500 to-indigo-600">
                        <h3 className="text-lg font-semibold text-white flex items-center">
                          <FiCheckCircle className="mr-2" />
                          Verify Certificate
                        </h3>
                      </div>
                      
                      <div className="p-6">
                        {/* Method Selection */}
                        <div className="mb-6">
                          <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                            Verification Method
                          </label>
                          <div className="grid grid-cols-3 gap-3">
                            <button
                              type="button"
                              onClick={() => setVerifyMethod('hash')}
                              className={`px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                                verifyMethod === 'hash'
                                  ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-lg transform scale-105'
                                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                              }`}
                            >
                              <FaQrcode className="mx-auto mb-1 w-5 h-5" />
                              Hash Only
                            </button>
                            <button
                              type="button"
                              onClick={() => setVerifyMethod('file')}
                              className={`px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                                verifyMethod === 'file'
                                  ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-lg transform scale-105'
                                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                              }`}
                            >
                              <FiFile className="mx-auto mb-1 w-5 h-5" />
                              File Only
                            </button>
                            <button
                              type="button"
                              onClick={() => setVerifyMethod('both')}
                              className={`px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                                verifyMethod === 'both'
                                  ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-lg transform scale-105'
                                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                              }`}
                            >
                              <FiRefreshCw className="mx-auto mb-1 w-5 h-5" />
                              Both
                            </button>
                          </div>
                        </div>

                        <form onSubmit={handleVerify} className="space-y-4">
                          {(verifyMethod === 'hash' || verifyMethod === 'both') && (
                            <motion.div
                              initial={{ opacity: 0, y: -10 }}
                              animate={{ opacity: 1, y: 0 }}
                              className="space-y-2"
                            >
                              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Certificate Hash
                              </label>
                              <input
                                value={verifyHash}
                                onChange={(e) => setVerifyHash(e.target.value)}
                                placeholder="Enter 64-character certificate hash"
                                className="w-full rounded-xl border-2 border-gray-200 dark:border-gray-700 dark:bg-gray-900 dark:text-white px-4 py-3 text-sm focus:border-blue-500 focus:ring focus:ring-blue-200 dark:focus:ring-blue-800"
                              />
                              <p className="text-xs text-gray-500 dark:text-gray-400">
                                Enter the unique certificate hash (e.g., 0x7b3d8f9a...)
                              </p>
                            </motion.div>
                          )}

                          {(verifyMethod === 'file' || verifyMethod === 'both') && (
                            <motion.div
                              initial={{ opacity: 0, y: -10 }}
                              animate={{ opacity: 1, y: 0 }}
                              className="space-y-2"
                            >
                              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                                Certificate File
                              </label>
                              <div className="border-2 border-dashed border-gray-200 dark:border-gray-700 rounded-xl p-4 text-center hover:border-blue-500 dark:hover:border-blue-400 transition-colors">
                                <input
                                  type="file"
                                  accept=".pdf,image/*"
                                  onChange={(e) => setVerifyFile(e.target.files?.[0] || null)}
                                  className="hidden"
                                  id="verify-file"
                                />
                                <label htmlFor="verify-file" className="cursor-pointer">
                                  <FiUploadCloud className="w-8 h-8 mx-auto text-gray-400 mb-2" />
                                  <span className="text-sm text-gray-600 dark:text-gray-400">
                                    {verifyFile ? verifyFile.name : 'Click to select file'}
                                  </span>
                                </label>
                              </div>
                            </motion.div>
                          )}

                          <motion.button
                            type="submit"
                            disabled={!canVerify}
                            className={`w-full px-6 py-3 rounded-xl text-white font-medium transition-all transform hover:scale-105 ${
                              canVerify 
                                ? 'bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 shadow-lg' 
                                : 'bg-gray-300 dark:bg-gray-600 cursor-not-allowed'
                            }`}
                            whileHover={canVerify ? { scale: 1.05 } : {}}
                            whileTap={canVerify ? { scale: 0.95 } : {}}
                          >
                            {verifyLoading ? (
                              <span className="flex items-center justify-center">
                                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                </svg>
                                Verifying... {verifyPct}%
                              </span>
                            ) : 'Verify Certificate'}
                          </motion.button>

                          {verifyLoading && (
                            <div className="space-y-2">
                              <div className="flex justify-between text-sm">
                                <span className="text-gray-600 dark:text-gray-400">Progress</span>
                                <span className="font-medium text-blue-600 dark:text-blue-400">{verifyPct}%</span>
                              </div>
                              <div className="h-2 w-full rounded-full bg-gray-200 dark:bg-gray-700 overflow-hidden">
                                <motion.div 
                                  className="h-2 rounded-full bg-gradient-to-r from-blue-500 to-indigo-600"
                                  initial={{ width: 0 }}
                                  animate={{ width: `${verifyPct}%` }}
                                  transition={{ duration: 0.3 }}
                                />
                              </div>
                            </div>
                          )}
                        </form>

                        {/* Verification History */}
                        {verifyHistory.length > 0 && (
                          <div className="mt-6 pt-6 border-t border-gray-200 dark:border-gray-700">
                            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                              Recent Verifications
                            </h4>
                            <div className="space-y-2">
                              {verifyHistory.slice(0, 3).map((item) => (
                                <div key={item.id} className="flex items-center justify-between text-xs">
                                  <div className="flex items-center">
                                    <span className={item.result === 'valid' ? 'text-green-600' : 'text-red-600'}>
                                      {item.result === 'valid' ? '✓' : '✗'}
                                    </span>
                                    <span className="ml-2 text-gray-600 dark:text-gray-400 font-mono">
                                      {item.hash}
                                    </span>
                                  </div>
                                  <span className="text-gray-400">
                                    {format(parseISO(item.timestamp), 'HH:mm')}
                                  </span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Result Display */}
                    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl overflow-hidden">
                      <div className="px-6 py-4 bg-gradient-to-r from-indigo-500 to-purple-600">
                        <h3 className="text-lg font-semibold text-white">Verification Result</h3>
                      </div>
                      
                      <div className="p-6">
                        {!verifyResult ? (
                          <div className="text-center py-16">
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
                              verifyResult.verified ? 'bg-green-50 dark:bg-green-900/20 border-2 border-green-200 dark:border-green-800' : 'bg-red-50 dark:bg-red-900/20 border-2 border-red-200 dark:border-red-800'
                            }`}>
                              <div className="flex items-center">
                                <motion.div
                                  initial={{ scale: 0 }}
                                  animate={{ scale: 1 }}
                                  transition={{ type: "spring", stiffness: 260, damping: 20 }}
                                  className={`w-16 h-16 rounded-full flex items-center justify-center text-3xl mr-4 ${
                                    verifyResult.verified ? 'bg-green-100 dark:bg-green-900/30' : 'bg-red-100 dark:bg-red-900/30'
                                  }`}
                                >
                                  {verifyResult.verified ? '✅' : '❌'}
                                </motion.div>
                                <div>
                                  <h4 className={`text-xl font-bold ${verifyResult.verified ? 'text-green-700 dark:text-green-400' : 'text-red-700 dark:text-red-400'}`}>
                                    {verifyResult.verified ? 'VALID CERTIFICATE' : 'INVALID CERTIFICATE'}
                                  </h4>
                                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                                    Blockchain: {verifyResult.blockchain_verified ? '✅ Verified' : '❌ Not Found'}
                                  </p>
                                </div>
                              </div>
                            </div>

                            {verifyResult.certificate_data && (
                              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                                <h5 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Certificate Details</h5>
                                <div className="grid grid-cols-2 gap-3">
                                  <div className="bg-white dark:bg-gray-800 p-3 rounded-lg">
                                    <p className="text-xs text-gray-500 dark:text-gray-400">Student Name</p>
                                    <p className="text-sm font-medium text-gray-800 dark:text-white">{verifyResult.certificate_data.student_name}</p>
                                  </div>
                                  <div className="bg-white dark:bg-gray-800 p-3 rounded-lg">
                                    <p className="text-xs text-gray-500 dark:text-gray-400">Student ID</p>
                                    <p className="text-sm font-medium text-gray-800 dark:text-white">{verifyResult.certificate_data.student_id}</p>
                                  </div>
                                  <div className="bg-white dark:bg-gray-800 p-3 rounded-lg">
                                    <p className="text-xs text-gray-500 dark:text-gray-400">Institution</p>
                                    <p className="text-sm font-medium text-gray-800 dark:text-white">{verifyResult.certificate_data.institution}</p>
                                  </div>
                                  <div className="bg-white dark:bg-gray-800 p-3 rounded-lg">
                                    <p className="text-xs text-gray-500 dark:text-gray-400">Issue Date</p>
                                    <p className="text-sm font-medium text-gray-800 dark:text-white">{formatDate(verifyResult.certificate_data.issue_date)}</p>
                                  </div>
                                </div>
                              </div>
                            )}

                            <div className="bg-gray-50 dark:bg-gray-700/50 rounded-xl p-4">
                              <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Verification ID</p>
                              <div className="flex items-center justify-between">
                                <p className="text-sm font-mono bg-white dark:bg-gray-800 p-2 rounded border border-gray-200 dark:border-gray-700 flex-1">
                                  {verifyResult.verification_id}
                                </p>
                                <button
                                  onClick={() => {
                                    navigator.clipboard.writeText(verifyResult.verification_id);
                                    showNotification('success', 'Verification ID copied to clipboard');
                                  }}
                                  className="ml-2 p-2 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300"
                                >
                                  <FiCopy className="w-4 h-4" />
                                </button>
                              </div>
                            </div>

                            {verifyResult.timestamp && (
                              <p className="text-xs text-gray-400 dark:text-gray-500 text-right">
                                Verified on {format(parseISO(verifyResult.timestamp), 'MMM dd, yyyy HH:mm')}
                              </p>
                            )}

                            {verifyResult.message && (
                              <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                                <p className="text-sm text-blue-700 dark:text-blue-400">{verifyResult.message}</p>
                              </div>
                            )}
                          </motion.div>
                        )}
                      </div>
                    </div>
                  </div>
                )}

                {/* Certificates List View */}
                {activeView === 'certificates' && (
                  <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl overflow-hidden">
                    <div className="px-6 py-4 bg-gradient-to-r from-yellow-500 to-orange-600">
                      <h3 className="text-lg font-semibold text-white flex items-center">
                        <FiList className="mr-2" />
                        My Certificates
                      </h3>
                    </div>
                    
                    <div className="p-6">
                      {filteredCertificates.length === 0 ? (
                        <div className="text-center py-16">
                          <FiFileText className="w-16 h-16 mx-auto text-gray-300 dark:text-gray-600 mb-4" />
                          <p className="text-gray-500 dark:text-gray-400 text-lg">No certificates found</p>
                          <p className="text-sm text-gray-400 dark:text-gray-500 mt-2">Try adjusting your filters or issue new certificates</p>
                        </div>
                      ) : (
                        <div className={`${viewMode === 'table' ? 'overflow-x-auto' : 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4'}`}>
                          {viewMode === 'table' ? (
                            <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                              <thead className="bg-gray-50 dark:bg-gray-900">
                                <tr>
                                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Student</th>
                                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">ID</th>
                                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Hash</th>
                                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Issue Date</th>
                                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Status</th>
                                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Blockchain</th>
                                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Actions</th>
                                </tr>
                              </thead>
                              <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                                {filteredCertificates.map((cert, index) => (
                                  <motion.tr
                                    key={cert.id}
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    transition={{ delay: index * 0.05 }}
                                    className="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                                  >
                                    <td className="px-6 py-4 whitespace-nowrap">
                                      <div className="flex items-center">
                                        <div className="w-8 h-8 rounded-full bg-gradient-to-r from-yellow-500 to-orange-500 flex items-center justify-center text-white text-xs font-bold mr-2">
                                          {cert.student_name?.charAt(0).toUpperCase()}
                                        </div>
                                        <span className="text-sm font-medium text-gray-900 dark:text-white">{cert.student_name}</span>
                                      </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">{cert.student_id}</td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                      <span className="font-mono text-xs bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded dark:text-gray-300">
                                        {cert.certificate_hash?.slice(0, 12)}...
                                      </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                                      {formatDate(cert.issue_date)}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                      <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(cert.status)}`}>
                                        {getStatusIcon(cert.status)} {cert.status}
                                      </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                      {cert.blockchain_tx_id ? (
                                        <span className="text-xs font-mono bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 px-2 py-1 rounded">
                                          {cert.blockchain_tx_id.slice(0, 10)}...
                                        </span>
                                      ) : (
                                        <span className="text-xs text-gray-400 dark:text-gray-500">Pending</span>
                                      )}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm">
                                      <div className="flex items-center space-x-2">
                                        <button
                                          onClick={() => {
                                            setSelectedCertificate(cert);
                                            setShowPreview(true);
                                          }}
                                          className="text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300"
                                          title="View"
                                        >
                                          <FiEye className="w-4 h-4" />
                                        </button>
                                        <button
                                          onClick={() => handlePrint(cert)}
                                          className="text-gray-600 hover:text-gray-800 dark:text-gray-400 dark:hover:text-gray-300"
                                          title="Print"
                                        >
                                          <FiPrinter className="w-4 h-4" />
                                        </button>
                                        <button
                                          onClick={() => handleShare(cert)}
                                          className="text-green-600 hover:text-green-800 dark:text-green-400 dark:hover:text-green-300"
                                          title="Share"
                                        >
                                          <FiShare2 className="w-4 h-4" />
                                        </button>
                                        {cert.status === 'pending' && (
                                          <button
                                            onClick={() => handleRevokeCertificate(cert.id)}
                                            className="text-red-600 hover:text-red-800 dark:text-red-400 dark:hover:text-red-300"
                                            title="Revoke"
                                          >
                                            <FiTrash2 className="w-4 h-4" />
                                          </button>
                                        )}
                                      </div>
                                    </td>
                                  </motion.tr>
                                ))}
                              </tbody>
                            </table>
                          ) : (
                            filteredCertificates.map((cert, index) => (
                              <motion.div
                                key={cert.id}
                                initial={{ opacity: 0, scale: 0.9 }}
                                animate={{ opacity: 1, scale: 1 }}
                                transition={{ delay: index * 0.05 }}
                                className="bg-white dark:bg-gray-700 rounded-xl shadow-md p-4 hover:shadow-lg transition-shadow"
                              >
                                <div className="flex items-start justify-between mb-3">
                                  <div className="flex items-center">
                                    <div className="w-10 h-10 rounded-full bg-gradient-to-r from-yellow-500 to-orange-500 flex items-center justify-center text-white font-bold mr-3">
                                      {cert.student_name?.charAt(0).toUpperCase()}
                                    </div>
                                    <div>
                                      <h4 className="font-medium text-gray-800 dark:text-white">{cert.student_name}</h4>
                                      <p className="text-xs text-gray-500 dark:text-gray-400">ID: {cert.student_id}</p>
                                    </div>
                                  </div>
                                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(cert.status)}`}>
                                    {cert.status}
                                  </span>
                                </div>
                                
                                <div className="space-y-2 text-sm">
                                  <div className="flex justify-between">
                                    <span className="text-gray-500 dark:text-gray-400">Issue Date:</span>
                                    <span className="text-gray-800 dark:text-white">{formatDate(cert.issue_date)}</span>
                                  </div>
                                  <div className="flex justify-between">
                                    <span className="text-gray-500 dark:text-gray-400">Hash:</span>
                                    <span className="font-mono text-xs bg-gray-100 dark:bg-gray-600 px-2 py-1 rounded">
                                      {cert.certificate_hash?.slice(0, 16)}...
                                    </span>
                                  </div>
                                  {cert.blockchain_tx_id && (
                                    <div className="flex justify-between">
                                      <span className="text-gray-500 dark:text-gray-400">Blockchain:</span>
                                      <span className="text-xs font-mono bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-300 px-2 py-1 rounded">
                                        {cert.blockchain_tx_id.slice(0, 12)}...
                                      </span>
                                    </div>
                                  )}
                                </div>
                                
                                <div className="mt-4 flex justify-end space-x-2 pt-3 border-t border-gray-100 dark:border-gray-600">
                                  <button
                                    onClick={() => {
                                      setSelectedCertificate(cert);
                                      setShowPreview(true);
                                    }}
                                    className="px-3 py-1 text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400"
                                  >
                                    View
                                  </button>
                                  <button
                                    onClick={() => handlePrint(cert)}
                                    className="px-3 py-1 text-sm text-gray-600 hover:text-gray-800 dark:text-gray-400"
                                  >
                                    Print
                                  </button>
                                  {cert.status === 'pending' && (
                                    <button
                                      onClick={() => handleRevokeCertificate(cert.id)}
                                      className="px-3 py-1 text-sm text-red-600 hover:text-red-800 dark:text-red-400"
                                    >
                                      Revoke
                                    </button>
                                  )}
                                </div>
                              </motion.div>
                            ))
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Settings View */}
                {activeView === 'settings' && (
                  <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Profile Settings */}
                    <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-2xl shadow-xl overflow-hidden">
                      <div className="px-6 py-4 bg-gradient-to-r from-gray-700 to-gray-800">
                        <h3 className="text-lg font-semibold text-white flex items-center">
                          <FiSettings className="mr-2" />
                          Profile Settings
                        </h3>
                      </div>
                      <div className="p-6">
                        <div className="space-y-4">
                          <div className="flex items-center space-x-4">
                            <div className="relative">
                              <div className="w-20 h-20 rounded-full bg-gradient-to-r from-green-500 to-blue-500 flex items-center justify-center text-white font-bold text-2xl">
                                {user?.username?.charAt(0).toUpperCase() || 'I'}
                              </div>
                              <button className="absolute bottom-0 right-0 w-6 h-6 bg-white dark:bg-gray-700 rounded-full flex items-center justify-center shadow-lg hover:bg-gray-100 dark:hover:bg-gray-600">
                                <FiCamera className="w-3 h-3" />
                              </button>
                            </div>
                            <div>
                              <h4 className="text-lg font-medium text-gray-800 dark:text-white">{user?.username || 'Issuer'}</h4>
                              <p className="text-sm text-gray-500 dark:text-gray-400">{user?.email || 'issuer@example.com'}</p>
                              <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">Member since {format(new Date(), 'yyyy')}</p>
                            </div>
                          </div>

                          <button
                            onClick={() => setShowProfileEditor(true)}
                            className="px-6 py-2 bg-gradient-to-r from-green-500 to-blue-600 text-white rounded-xl hover:from-green-600 hover:to-blue-700 transition-all"
                          >
                            Edit Profile
                          </button>
                        </div>
                      </div>
                    </div>

                    {/* Institution Stats */}
                    <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl overflow-hidden">
                      <div className="px-6 py-4 bg-gradient-to-r from-green-600 to-green-700">
                        <h3 className="text-lg font-semibold text-white flex items-center">
                          <FiAward className="mr-2" />
                          Institution Stats
                        </h3>
                      </div>
                      <div className="p-6">
                        <div className="space-y-4">
                          <div className="text-center">
                            <p className="text-3xl font-bold text-green-600 dark:text-green-400">
                              {formatCurrency(institutionInfo?.credits || 0)}
                            </p>
                            <p className="text-sm text-gray-500 dark:text-gray-400">Available Credits</p>
                          </div>
                          
                          <div className="border-t dark:border-gray-700 pt-4">
                            <div className="flex justify-between mb-2">
                              <span className="text-sm text-gray-600 dark:text-gray-400">Certificates Issued</span>
                              <span className="font-medium text-gray-800 dark:text-white">{issuerStats?.total || 0}</span>
                            </div>
                            <div className="flex justify-between mb-2">
                              <span className="text-sm text-gray-600 dark:text-gray-400">This Month</span>
                              <span className="font-medium text-gray-800 dark:text-white">{issuerStats?.monthly || 0}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-sm text-gray-600 dark:text-gray-400">OCR Scans Today</span>
                              <span className="font-medium text-gray-800 dark:text-white">{issuerStats?.ocr_today || 0}</span>
                            </div>
                          </div>

                          {/* Quick Settings */}
                          <div className="border-t dark:border-gray-700 pt-4">
                            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Preferences</h4>
                            <div className="space-y-2">
                              <label className="flex items-center justify-between">
                                <span className="text-sm text-gray-600 dark:text-gray-400">Auto-refresh</span>
                                <input
                                  type="checkbox"
                                  checked={autoRefresh}
                                  onChange={(e) => setAutoRefresh(e.target.checked)}
                                  className="rounded text-green-500 focus:ring-green-500"
                                />
                              </label>
                              <label className="flex items-center justify-between">
                                <span className="text-sm text-gray-600 dark:text-gray-400">Compact Mode</span>
                                <input
                                  type="checkbox"
                                  checked={compactMode}
                                  onChange={(e) => setCompactMode(e.target.checked)}
                                  className="rounded text-green-500 focus:ring-green-500"
                                />
                              </label>
                              <label className="flex items-center justify-between">
                                <span className="text-sm text-gray-600 dark:text-gray-400">Dark Mode</span>
                                <input
                                  type="checkbox"
                                  checked={darkMode}
                                  onChange={(e) => setDarkMode(e.target.checked)}
                                  className="rounded text-green-500 focus:ring-green-500"
                                />
                              </label>
                            </div>
                          </div>

                          <div className="border-t dark:border-gray-700 pt-4">
                            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Refresh Interval</h4>
                            <select
                              value={refreshInterval}
                              onChange={(e) => setRefreshInterval(Number(e.target.value))}
                              className="w-full px-3 py-2 border-2 border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                            >
                              <option value={10000}>10 seconds</option>
                              <option value={30000}>30 seconds</option>
                              <option value={60000}>1 minute</option>
                              <option value={300000}>5 minutes</option>
                            </select>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </motion.div>
            </AnimatePresence>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default IssuerDashboard;