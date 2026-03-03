import React, { useEffect, useMemo, useState, useCallback, useRef } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { certificateApi, paymentApi } from '../../api';
import RecentActivity from '../../components/RecentActivity';
import CertificatePreview from '../../components/CertificatePreview';
import PaymentModal from '../../components/PaymentModal';
import OCRSidebar from '../../components/OCRSidebar';
import CertificateScanner from '../../components/CertificateScanner';

const VerifierDashboard = () => {
  const { user, logout } = useAuth();
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
  
  // Payment state
  const [showPaymentModal, setShowPaymentModal] = useState(false);
  const [pendingPayment, setPendingPayment] = useState(null);
  const [paymentHistory, setPaymentHistory] = useState([]);
  const [selectedCertificate, setSelectedCertificate] = useState(null);
  const [showPreview, setShowPreview] = useState(false);
  
  const fileInputRef = useRef(null);
  
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const [actionMsg, setActionMsg] = useState('');
  const [activeView, setActiveView] = useState('verify');

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

  // Handle file upload and OCR extraction
  const handleFileUpload = async (file) => {
    setFile(file);
    if (!file) {
      setExtractedData(null);
      setExtractedDisplay(null);
      setShowOcrSidebar(false);
      return;
    }

    // Trigger OCR extraction
    setOcrLoading(true);
    setOcrError('');
    setExtractedDisplay(null);
    
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      // Call OCR extraction endpoint
      const response = await certificateApi.extractCertificateData(formData);
      
      if (response.data) {
        const data = response.data;
        setExtractedData(data);
        setExtractedDisplay(data.display_html);
        setOcrConfidence(data.validation?.confidence);
        setShowOcrSidebar(true);
        
        // Auto-fill certificate hash if extracted
        if (data.certificate_hash) {
          setCertificateHash(data.certificate_hash);
        }
        
        setActionMsg('✅ Certificate scanned successfully! Review the extracted data.');
        setTimeout(() => setActionMsg(''), 5000);
      }
    } catch (err) {
      setOcrError('Failed to extract data from certificate. Please verify manually.');
      console.error('OCR Error:', err);
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
      setActionMsg('✅ Payment successful! You can now verify certificates.');
      // Refresh payment history
      fetchPaymentHistory();
    } else {
      setError('Payment failed. Please try again.');
    }
    setTimeout(() => setActionMsg(''), 3000);
  };

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

      // Add payment tracking
      formData.append('payment_method', paymentMethod);
      if (paymentDigits) {
        formData.append('payment_digits', paymentDigits);
      }

      const data = await certificateApi.verifyCertificate(formData, (evt) => {
        if (!evt.total) return;
        setUploadPct(Math.round((evt.loaded * 100) / evt.total));
      });
      
      setResult(data);
      
      if (data.verified) {
        setActionMsg('✅ Certificate verified successfully!');
      } else {
        setActionMsg('⚠️ Certificate verification failed');
      }
      
      // Refresh history
      fetchVerificationHistory();
      
      setTimeout(() => setActionMsg(''), 3000);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      if (typeof detail === 'string') setError(detail);
      else if (Array.isArray(detail)) setError(detail.map((d) => d.msg).join(', '));
      else setError(err?.message || 'Verification failed');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const fetchVerificationStats = useCallback(async () => {
    try {
      const stats = await certificateApi.getMyVerifierStats();
      setVerifierStats(stats);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  }, []);

  const fetchVerificationHistory = useCallback(async () => {
    try {
      const history = await certificateApi.getMyVerifications(50);
      setHistory(history || []);
    } catch (error) {
      console.error('Failed to fetch history:', error);
    }
  }, []);

  const fetchPaymentHistory = useCallback(async () => {
    try {
      const payments = await paymentApi.getMyPayments();
      setPaymentHistory(payments || []);
    } catch (error) {
      console.error('Failed to fetch payment history:', error);
    }
  }, []);

  useEffect(() => {
    let mounted = true;
    
    const fetchInitialData = async () => {
      try {
        const [stats, history, payments] = await Promise.all([
          certificateApi.getMyVerifierStats(),
          certificateApi.getMyVerifications(25),
          paymentApi.getMyPayments()
        ]);
        
        if (mounted) {
          setVerifierStats(stats);
          setHistory(history || []);
          setPaymentHistory(payments || []);
        }
      } catch (error) {
        console.error('Failed to fetch initial data:', error);
      }
    };
    
    fetchInitialData();
    
    return () => {
      mounted = false;
    };
  }, []);

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
      ? 'bg-green-100 text-green-800' 
      : 'bg-red-100 text-red-800';
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 80) return 'text-green-600';
    if (confidence >= 60) return 'text-yellow-600';
    return 'text-red-600';
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex">
      {/* Modals */}
      {showPaymentModal && pendingPayment && (
        <PaymentModal
          amount={pendingPayment.amount}
          currency={pendingPayment.currency}
          onClose={() => setShowPaymentModal(false)}
          onComplete={handlePaymentComplete}
        />
      )}

      {showPreview && selectedCertificate && (
        <CertificatePreview
          certificate={selectedCertificate}
          onClose={() => {
            setShowPreview(false);
            setSelectedCertificate(null);
          }}
        />
      )}

      {showScanner && (
        <CertificateScanner
          onCapture={handleScannerCapture}
          onClose={() => setShowScanner(false)}
        />
      )}

      {/* OCR Sidebar */}
      {showOcrSidebar && extractedDisplay && (
        <OCRSidebar
          displayHtml={extractedDisplay}
          extractedData={extractedData}
          confidence={ocrConfidence}
          onClose={() => setShowOcrSidebar(false)}
          onClear={handleClearOcr}
          onAccept={() => setShowOcrSidebar(false)}
        />
      )}

      {/* Left Sidebar */}
      <div className={`${sidebarCollapsed ? 'w-20' : 'w-80'} bg-gradient-to-b from-gray-900 to-gray-800 text-white transition-all duration-300 shadow-2xl flex flex-col relative`}>
        {/* Logo Area */}
        <div className="p-6 border-b border-gray-700">
          <div className="flex items-center space-x-3">
            <div className="bg-gradient-to-r from-red-500 to-orange-500 p-3 rounded-xl shadow-lg transform hover:scale-105 transition-transform">
              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
              </svg>
            </div>
            {!sidebarCollapsed && (
              <div>
                <span className="text-xl font-bold bg-gradient-to-r from-red-400 to-orange-400 bg-clip-text text-transparent">CertiVert</span>
                <span className="block text-xs text-gray-400">Verifier Portal</span>
              </div>
            )}
          </div>
        </div>

        {/* User Profile */}
        <div className="p-6 border-b border-gray-700">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 rounded-full bg-gradient-to-r from-red-500 to-orange-500 flex items-center justify-center text-white font-bold text-lg shadow-lg">
              {user?.username?.charAt(0).toUpperCase() || 'V'}
            </div>
            {!sidebarCollapsed && (
              <div>
                <p className="font-medium">{user?.username || 'Verifier'}</p>
                <p className="text-xs text-gray-400 truncate max-w-[150px]">{user?.institution || 'Independent Verifier'}</p>
                <span className="inline-block mt-1 px-2 py-0.5 bg-red-600/30 text-red-300 rounded-full text-xs">
                  VERIFIER
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Quick Stats */}
        {!sidebarCollapsed && verifierStats && (
          <div className="p-4 border-b border-gray-700">
            <h4 className="text-xs uppercase tracking-wider text-gray-400 mb-3">Quick Stats</h4>
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-300">Total</span>
                <span className="text-sm font-bold text-blue-400">{verifierStats?.total ?? 0}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-300">Valid</span>
                <span className="text-sm font-bold text-green-400">{verifierStats?.valid ?? 0}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-sm text-gray-300">Invalid</span>
                <span className="text-sm font-bold text-red-400">{verifierStats?.invalid ?? 0}</span>
              </div>
              <div className="flex justify-between items-center pt-2 border-t border-gray-700">
                <span className="text-sm text-gray-300">Fees Earned</span>
                <span className="text-sm font-bold text-yellow-400">
                  M{verifierStats?.total_fees?.toFixed(2) || '0.00'}
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Navigation */}
        <nav className="flex-1 overflow-y-auto py-6">
          <button
            onClick={() => setActiveView('verify')}
            className={`w-full flex items-center space-x-3 px-6 py-4 transition-all duration-200 relative group ${
              activeView === 'verify'
                ? 'bg-gradient-to-r from-red-600 to-orange-600 text-white shadow-lg'
                : 'text-gray-300 hover:bg-gray-700 hover:text-white'
            }`}
          >
            <span className="text-xl">✓</span>
            {!sidebarCollapsed && (
              <>
                <span className="font-medium">Verify Certificate</span>
                {activeView === 'verify' && (
                  <span className="absolute right-3 w-2 h-2 rounded-full bg-white animate-pulse"></span>
                )}
              </>
            )}
          </button>
          
          <button
            onClick={() => setActiveView('history')}
            className={`w-full flex items-center space-x-3 px-6 py-4 transition-all duration-200 relative group ${
              activeView === 'history'
                ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white shadow-lg'
                : 'text-gray-300 hover:bg-gray-700 hover:text-white'
            }`}
          >
            <span className="text-xl">📋</span>
            {!sidebarCollapsed && (
              <>
                <span className="font-medium">History</span>
                {activeView === 'history' && (
                  <span className="absolute right-3 w-2 h-2 rounded-full bg-white animate-pulse"></span>
                )}
              </>
            )}
          </button>
          
          <button
            onClick={() => setActiveView('payments')}
            className={`w-full flex items-center space-x-3 px-6 py-4 transition-all duration-200 relative group ${
              activeView === 'payments'
                ? 'bg-gradient-to-r from-green-600 to-green-700 text-white shadow-lg'
                : 'text-gray-300 hover:bg-gray-700 hover:text-white'
            }`}
          >
            <span className="text-xl">💰</span>
            {!sidebarCollapsed && (
              <>
                <span className="font-medium">Payments</span>
                {activeView === 'payments' && (
                  <span className="absolute right-3 w-2 h-2 rounded-full bg-white animate-pulse"></span>
                )}
              </>
            )}
          </button>
          
          <button
            onClick={() => setActiveView('stats')}
            className={`w-full flex items-center space-x-3 px-6 py-4 transition-all duration-200 relative group ${
              activeView === 'stats'
                ? 'bg-gradient-to-r from-purple-600 to-purple-700 text-white shadow-lg'
                : 'text-gray-300 hover:bg-gray-700 hover:text-white'
            }`}
          >
            <span className="text-xl">📊</span>
            {!sidebarCollapsed && (
              <>
                <span className="font-medium">Statistics</span>
                {activeView === 'stats' && (
                  <span className="absolute right-3 w-2 h-2 rounded-full bg-white animate-pulse"></span>
                )}
              </>
            )}
          </button>
        </nav>

        {/* Logout Section */}
        <div className="p-6 border-t border-gray-700">
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
            <div className="space-y-2">
              <p className="text-sm text-gray-300 text-center">Confirm logout?</p>
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
          
          <button
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
            className="absolute bottom-6 -right-3 w-8 h-8 bg-gray-800 rounded-full flex items-center justify-center text-white border-2 border-gray-700 hover:bg-gray-700 transition-colors"
          >
            {sidebarCollapsed ? '→' : '←'}
          </button>
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-auto">
        {/* Top Bar */}
        <div className="bg-white shadow-sm sticky top-0 z-10">
          <div className="px-8 py-4 flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-800">Verifier Dashboard</h1>
              <p className="text-sm text-gray-500">Verify LGCSE certificates with OCR and blockchain</p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="relative">
                <span className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full animate-pulse"></span>
                <div className="w-10 h-10 rounded-full bg-gradient-to-r from-red-500 to-orange-500 flex items-center justify-center text-white font-bold">
                  {user?.username?.charAt(0).toUpperCase() || 'V'}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Action Messages */}
        {actionMsg && (
          <div className="mx-8 mt-4 px-6 py-3 rounded-xl bg-gradient-to-r from-green-500 to-green-600 text-white shadow-lg animate-slideDown flex items-center">
            <span className="mr-2">✓</span>
            {actionMsg}
          </div>
        )}

        {/* Error Messages */}
        {error && (
          <div className="mx-8 mt-4 px-6 py-3 rounded-xl bg-gradient-to-r from-red-500 to-red-600 text-white shadow-lg animate-slideDown flex items-center">
            <span className="mr-2">⚠️</span>
            {error}
          </div>
        )}

        {ocrError && (
          <div className="mx-8 mt-4 px-6 py-3 rounded-xl bg-gradient-to-r from-yellow-500 to-yellow-600 text-white shadow-lg animate-slideDown flex items-center">
            <span className="mr-2">⚠️</span>
            {ocrError}
          </div>
        )}

        {/* Content Area */}
        <div className="p-8">
          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            <div className="bg-white rounded-2xl shadow-lg p-6 transform hover:scale-105 transition-transform duration-300 border-l-4 border-blue-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-500 text-sm">Total Verifications</p>
                  <p className="text-3xl font-bold text-gray-800">{verifierStats?.total ?? 0}</p>
                </div>
                <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                  <span className="text-2xl">📊</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl shadow-lg p-6 transform hover:scale-105 transition-transform duration-300 border-l-4 border-green-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-500 text-sm">Valid</p>
                  <p className="text-3xl font-bold text-gray-800">{verifierStats?.valid ?? 0}</p>
                </div>
                <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                  <span className="text-2xl">✓</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl shadow-lg p-6 transform hover:scale-105 transition-transform duration-300 border-l-4 border-red-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-500 text-sm">Invalid</p>
                  <p className="text-3xl font-bold text-gray-800">{verifierStats?.invalid ?? 0}</p>
                </div>
                <div className="w-12 h-12 bg-red-100 rounded-xl flex items-center justify-center">
                  <span className="text-2xl">✗</span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-2xl shadow-lg p-6 transform hover:scale-105 transition-transform duration-300 border-l-4 border-yellow-500">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-500 text-sm">Fees Earned</p>
                  <p className="text-3xl font-bold text-gray-800">M{verifierStats?.total_fees?.toFixed(2) ?? '0.00'}</p>
                </div>
                <div className="w-12 h-12 bg-yellow-100 rounded-xl flex items-center justify-center">
                  <span className="text-2xl">💰</span>
                </div>
              </div>
            </div>
          </div>

          {/* Quick OCR Scan Card */}
          <div className="bg-gradient-to-r from-purple-500 to-indigo-600 rounded-2xl shadow-xl p-6 text-white mb-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-xl font-bold mb-2">Quick Certificate Scan</h3>
                <p className="text-purple-100 mb-4">Upload or scan a certificate to auto-fill verification</p>
                <div className="flex space-x-4">
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="px-6 py-3 bg-white text-purple-600 rounded-xl font-medium hover:bg-purple-50 transition-colors flex items-center"
                  >
                    <span className="mr-2">📤</span>
                    Upload Certificate
                  </button>
                  <button
                    onClick={() => setShowScanner(true)}
                    className="px-6 py-3 bg-purple-600 text-white rounded-xl font-medium hover:bg-purple-700 transition-colors flex items-center border border-white/30"
                  >
                    <span className="mr-2">📷</span>
                    Scan with Camera
                  </button>
                </div>
              </div>
              <div className="text-7xl opacity-50">🔍</div>
            </div>
          </div>

          {/* Verify View */}
          {activeView === 'verify' && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Main Form */}
              <div className="lg:col-span-2 bg-white rounded-2xl shadow-lg overflow-hidden">
                <div className="px-6 py-4 bg-gradient-to-r from-red-500 to-orange-600">
                  <h3 className="text-lg font-semibold text-white">Verify Certificate</h3>
                </div>
                <div className="p-6">
                  {/* File Upload Area */}
                  <div className="mb-6 p-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-xl border-2 border-dashed border-purple-200">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                          <span className="text-2xl">🔍</span>
                        </div>
                        <div>
                          <h4 className="font-medium text-gray-800">OCR Auto-Fill</h4>
                          <p className="text-sm text-gray-500">Upload certificate to auto-extract hash</p>
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
                        className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center"
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
                            <span className="mr-2">📤</span>
                            Select File
                          </>
                        )}
                      </button>
                    </div>
                    
                    {file && !ocrLoading && (
                      <div className="mt-3 flex items-center justify-between bg-white p-2 rounded-lg">
                        <div className="flex items-center">
                          <span className="text-2xl mr-2">📄</span>
                          <span className="text-sm text-gray-600">{file.name}</span>
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
                          ✕
                        </button>
                      </div>
                    )}
                    
                    {ocrLoading && (
                      <div className="mt-3">
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm text-gray-600">Extracting data...</span>
                          <span className="text-xs text-purple-600">Processing</span>
                        </div>
                        <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                          <div className="h-2 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full animate-pulse" style={{ width: '60%' }}></div>
                        </div>
                      </div>
                    )}
                  </div>

                  <form onSubmit={handleVerify} className="space-y-6">
                    {/* Verification Mode Selection */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-3">
                        Verification Method
                      </label>
                      <div className="grid grid-cols-3 gap-3">
                        <button
                          type="button"
                          onClick={() => setVerificationMode('hash')}
                          className={`px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                            verificationMode === 'hash'
                              ? 'bg-gradient-to-r from-red-500 to-orange-600 text-white shadow-lg'
                              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                          }`}
                        >
                          🔑 Hash Only
                        </button>
                        <button
                          type="button"
                          onClick={() => setVerificationMode('file')}
                          className={`px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                            verificationMode === 'file'
                              ? 'bg-gradient-to-r from-red-500 to-orange-600 text-white shadow-lg'
                              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                          }`}
                        >
                          📄 File Only
                        </button>
                        <button
                          type="button"
                          onClick={() => setVerificationMode('both')}
                          className={`px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                            verificationMode === 'both'
                              ? 'bg-gradient-to-r from-red-500 to-orange-600 text-white shadow-lg'
                              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                          }`}
                        >
                          🔐📄 Both
                        </button>
                      </div>
                    </div>

                    {/* Certificate Hash */}
                    {(verificationMode === 'hash' || verificationMode === 'both') && (
                      <div className="animate-slideDown">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Certificate Hash
                        </label>
                        <input
                          value={certificateHash}
                          onChange={(e) => setCertificateHash(e.target.value)}
                          placeholder="Enter 64-character certificate hash"
                          className="w-full rounded-xl border-2 border-gray-200 px-4 py-3 text-sm focus:border-red-500 focus:ring focus:ring-red-200 transition-all"
                        />
                      </div>
                    )}

                    {/* Payment Section */}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Payment Method
                        </label>
                        <select
                          value={paymentMethod}
                          onChange={(e) => setPaymentMethod(e.target.value)}
                          className="w-full rounded-xl border-2 border-gray-200 px-4 py-3 text-sm focus:border-red-500 focus:ring focus:ring-red-200 transition-all"
                        >
                          <option value="mpesa_lesotho">📱 M-Pesa Lesotho</option>
                          <option value="mpesa">📱 M-Pesa</option>
                          <option value="ecocash">📲 EcoCash</option>
                          <option value="bank">🏦 Bank Transfer</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Phone/Account Digits
                        </label>
                        <input
                          value={paymentDigits}
                          onChange={(e) => setPaymentDigits(e.target.value.replace(/\D/g, '').slice(0, 6))}
                          inputMode="numeric"
                          placeholder="Last 6 digits"
                          className="w-full rounded-xl border-2 border-gray-200 px-4 py-3 text-sm focus:border-red-500 focus:ring focus:ring-red-200 transition-all"
                        />
                      </div>
                    </div>

                    <button
                      type="submit"
                      disabled={!canSubmit}
                      className={`w-full px-6 py-3 rounded-xl text-white font-medium transition-all transform hover:scale-105 ${
                        canSubmit 
                          ? 'bg-gradient-to-r from-red-500 to-orange-600 hover:from-red-600 hover:to-orange-700 shadow-lg' 
                          : 'bg-gray-300 cursor-not-allowed'
                      }`}
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
                    </button>

                    {loading && (
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Progress</span>
                          <span className="font-medium text-red-600">{uploadPct}%</span>
                        </div>
                        <div className="h-2 w-full rounded-full bg-gray-200 overflow-hidden">
                          <div 
                            className="h-2 rounded-full bg-gradient-to-r from-red-500 to-orange-600 transition-all duration-300"
                            style={{ width: `${uploadPct}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </form>
                </div>
              </div>

              {/* Result Display */}
              <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
                <div className="px-6 py-4 bg-gradient-to-r from-indigo-500 to-purple-600">
                  <h3 className="text-lg font-semibold text-white">Verification Result</h3>
                </div>
                <div className="p-6">
                  {!result ? (
                    <div className="text-center py-12">
                      <div className="text-7xl mb-6 animate-bounce">🔍</div>
                      <p className="text-gray-500 text-lg">Ready to verify</p>
                      <p className="text-sm text-gray-400 mt-2">Enter details to check authenticity</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div className={`p-6 rounded-xl ${
                        result.verified ? 'bg-green-50 border-2 border-green-200' : 'bg-red-50 border-2 border-red-200'
                      }`}>
                        <div className="flex items-center">
                          <div className={`w-16 h-16 rounded-full flex items-center justify-center text-3xl mr-4 ${
                            result.verified ? 'bg-green-100' : 'bg-red-100'
                          }`}>
                            {result.verified ? '✅' : '❌'}
                          </div>
                          <div>
                            <h4 className={`text-xl font-bold ${result.verified ? 'text-green-700' : 'text-red-700'}`}>
                              {result.verified ? 'VALID CERTIFICATE' : 'INVALID CERTIFICATE'}
                            </h4>
                            <p className="text-sm text-gray-600 mt-1">
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
                        <div className="bg-white rounded-xl border-2 border-gray-100 p-4">
                          <div className="flex justify-between items-center mb-3">
                            <h5 className="text-sm font-semibold text-gray-700">Certificate Details</h5>
                            <button
                              onClick={() => {
                                setSelectedCertificate(result.certificate);
                                setShowPreview(true);
                              }}
                              className="text-xs text-blue-600 hover:text-blue-800"
                            >
                              View Full Certificate
                            </button>
                          </div>
                          <div className="grid grid-cols-2 gap-3">
                            <div className="bg-gray-50 p-3 rounded-lg">
                              <p className="text-xs text-gray-500">Student Name</p>
                              <p className="text-sm font-medium text-gray-800">{result.certificate.full_name}</p>
                            </div>
                            <div className="bg-gray-50 p-3 rounded-lg">
                              <p className="text-xs text-gray-500">Student ID</p>
                              <p className="text-sm font-medium text-gray-800">{result.certificate.candidate_number}</p>
                            </div>
                            <div className="bg-gray-50 p-3 rounded-lg">
                              <p className="text-xs text-gray-500">Institution</p>
                              <p className="text-sm font-medium text-gray-800">{result.certificate.issuer_code}</p>
                            </div>
                            <div className="bg-gray-50 p-3 rounded-lg">
                              <p className="text-xs text-gray-500">Issue Date</p>
                              <p className="text-sm font-medium text-gray-800">{result.certificate.date_of_issue}</p>
                            </div>
                          </div>
                        </div>
                      )}

                      <div className="bg-gray-50 rounded-xl p-3">
                        <p className="text-xs text-gray-500 mb-1">Verification ID</p>
                        <p className="text-sm font-mono bg-white p-2 rounded border border-gray-200">
                          {result.verification_id}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* History View */}
          {activeView === 'history' && (
            <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
              <div className="px-6 py-4 bg-gradient-to-r from-blue-500 to-blue-600">
                <h3 className="text-lg font-semibold text-white">Verification History</h3>
              </div>
              <div className="p-6">
                {history.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="text-6xl mb-4">📋</div>
                    <p className="text-gray-500">No verification history yet.</p>
                    <p className="text-sm text-gray-400 mt-2">Start verifying certificates to see history here.</p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Certificate</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Result</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Payment</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fee</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {history.map((v, index) => (
                          <tr key={v.id} className="hover:bg-gray-50 transition-colors animate-fadeIn" style={{ animationDelay: `${index * 50}ms` }}>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {formatDate(v.verification_date)}
                            </td>
                            <td className="px-6 py-4">
                              <div className="flex flex-col">
                                <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded mb-1">
                                  {v.certificate_hash?.slice(0, 16)}...
                                </span>
                                <span className="text-xs text-gray-500">{v.student_name}</span>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                                v.result === 'verified' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                              }`}>
                                {v.result}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <span className="text-lg mr-1">{getPaymentIcon(v.payment_method)}</span>
                                <span className="text-sm text-gray-600">
                                  {v.payment_method?.replace('_', ' ')}
                                </span>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-green-600">
                              M{v.verification_fee?.toFixed(2) || '5.00'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <button
                                onClick={() => {
                                  setResult(v);
                                  setActiveView('verify');
                                }}
                                className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                              >
                                View Details
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Payments View */}
          {activeView === 'payments' && (
            <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
              <div className="px-6 py-4 bg-gradient-to-r from-green-500 to-green-600">
                <h3 className="text-lg font-semibold text-white">Payment History</h3>
              </div>
              <div className="p-6">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  <div className="bg-green-50 rounded-lg p-4 text-center">
                    <p className="text-3xl font-bold text-green-600">
                      M{paymentHistory.reduce((sum, p) => sum + (p.amount || 0), 0).toFixed(2)}
                    </p>
                    <p className="text-sm text-gray-600">Total Spent</p>
                  </div>
                  <div className="bg-blue-50 rounded-lg p-4 text-center">
                    <p className="text-3xl font-bold text-blue-600">
                      {paymentHistory.filter(p => p.status === 'CONFIRMED').length}
                    </p>
                    <p className="text-sm text-gray-600">Successful Payments</p>
                  </div>
                  <div className="bg-purple-50 rounded-lg p-4 text-center">
                    <p className="text-3xl font-bold text-purple-600">
                      {paymentHistory.length}
                    </p>
                    <p className="text-sm text-gray-600">Total Transactions</p>
                  </div>
                </div>

                {paymentHistory.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="text-6xl mb-4">💰</div>
                    <p className="text-gray-500">No payment history yet.</p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Method</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reference</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">M-Pesa ID</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {paymentHistory.map((p, index) => (
                          <tr key={p.id} className="hover:bg-gray-50">
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {formatDate(p.created_at)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                              M{p.amount.toFixed(2)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <span className="text-lg mr-1">{getPaymentIcon(p.method)}</span>
                                <span className="text-sm">{p.method?.replace('_', ' ')}</span>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {p.reference || '-'}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
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
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Statistics View */}
          {activeView === 'stats' && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
                <div className="px-6 py-4 bg-gradient-to-r from-purple-500 to-purple-600">
                  <h3 className="text-lg font-semibold text-white">Verification Statistics</h3>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    <div className="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
                      <span className="text-gray-600">Total Verifications</span>
                      <span className="text-2xl font-bold text-gray-800">{verifierStats?.total ?? 0}</span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-green-50 rounded-lg">
                      <span className="text-green-600">Valid</span>
                      <span className="text-2xl font-bold text-green-600">{verifierStats?.valid ?? 0}</span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-red-50 rounded-lg">
                      <span className="text-red-600">Invalid</span>
                      <span className="text-2xl font-bold text-red-600">{verifierStats?.invalid ?? 0}</span>
                    </div>
                    <div className="flex justify-between items-center p-3 bg-yellow-50 rounded-lg">
                      <span className="text-yellow-600">Total Fees</span>
                      <span className="text-2xl font-bold text-yellow-600">M{verifierStats?.total_fees?.toFixed(2) || '0.00'}</span>
                    </div>
                    
                    {/* Success Rate */}
                    <div className="mt-4 pt-4 border-t border-gray-200">
                      <div className="flex justify-between text-sm text-gray-500 mb-2">
                        <span>Success Rate</span>
                        <span>
                          {verifierStats?.total > 0 
                            ? Math.round((verifierStats.valid / verifierStats.total) * 100) 
                            : 0}%
                        </span>
                      </div>
                      <div className="h-3 w-full rounded-full bg-gray-200 overflow-hidden">
                        <div 
                          className="h-3 rounded-full bg-gradient-to-r from-green-500 to-green-600"
                          style={{ 
                            width: `${verifierStats?.total > 0 
                              ? (verifierStats.valid / verifierStats.total) * 100 
                              : 0}%` 
                          }}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
                <div className="px-6 py-4 bg-gradient-to-r from-orange-500 to-orange-600">
                  <h3 className="text-lg font-semibold text-white">Payment Methods Distribution</h3>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    <div className="flex items-center p-3 bg-gray-50 rounded-lg">
                      <span className="text-2xl mr-3">📱</span>
                      <div className="flex-1">
                        <div className="flex justify-between mb-1">
                          <span className="text-sm font-medium">M-Pesa Lesotho</span>
                          <span className="text-sm text-gray-600">48%</span>
                        </div>
                        <div className="h-2 w-full rounded-full bg-gray-200 overflow-hidden">
                          <div className="h-2 rounded-full bg-green-500" style={{ width: '48%' }} />
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center p-3 bg-gray-50 rounded-lg">
                      <span className="text-2xl mr-3">📱</span>
                      <div className="flex-1">
                        <div className="flex justify-between mb-1">
                          <span className="text-sm font-medium">M-Pesa</span>
                          <span className="text-sm text-gray-600">32%</span>
                        </div>
                        <div className="h-2 w-full rounded-full bg-gray-200 overflow-hidden">
                          <div className="h-2 rounded-full bg-blue-500" style={{ width: '32%' }} />
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center p-3 bg-gray-50 rounded-lg">
                      <span className="text-2xl mr-3">📲</span>
                      <div className="flex-1">
                        <div className="flex justify-between mb-1">
                          <span className="text-sm font-medium">EcoCash</span>
                          <span className="text-sm text-gray-600">12%</span>
                        </div>
                        <div className="h-2 w-full rounded-full bg-gray-200 overflow-hidden">
                          <div className="h-2 rounded-full bg-purple-500" style={{ width: '12%' }} />
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center p-3 bg-gray-50 rounded-lg">
                      <span className="text-2xl mr-3">🏦</span>
                      <div className="flex-1">
                        <div className="flex justify-between mb-1">
                          <span className="text-sm font-medium">Bank Transfer</span>
                          <span className="text-sm text-gray-600">8%</span>
                        </div>
                        <div className="h-2 w-full rounded-full bg-gray-200 overflow-hidden">
                          <div className="h-2 rounded-full bg-yellow-500" style={{ width: '8%' }} />
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-6 p-4 bg-blue-50 rounded-lg">
                    <p className="text-sm text-blue-800 font-medium mb-2">Verification Fee Structure</p>
                    <p className="text-xs text-blue-600">• Standard verification: M5.00 per certificate</p>
                    <p className="text-xs text-blue-600">• Bulk discount available for 10+ verifications</p>
                    <p className="text-xs text-blue-600">• Payments processed via M-Pesa Lesotho</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Recent Activity */}
          <div className="mt-8">
            <RecentActivity title="Live System Activity" limit={6} />
          </div>
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
        
        .animate-fadeIn {
          opacity: 0;
          animation: fadeIn 0.5s ease-out forwards;
        }
      `}</style>
    </div>
  );
};

export default VerifierDashboard;