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

const IssuerDashboard = () => {
  const { user, logout, updateUser } = useAuth();
  const [issuerStats, setIssuerStats] = useState(null);
  const [myCertificates, setMyCertificates] = useState([]);
  const [institutionInfo, setInstitutionInfo] = useState(null);
  const fileInputRef = useRef(null);
  
  // Bulk upload state
  const [showBulkModal, setShowBulkModal] = useState(false);
  const [bulkFiles, setBulkFiles] = useState([]);
  const [bulkLoading, setBulkLoading] = useState(false);
  const [bulkPct, setBulkPct] = useState(0);
  const [bulkError, setBulkError] = useState('');
  const [bulkResult, setBulkResult] = useState(null);

  // Single certificate issuance
  const [singleForm, setSingleForm] = useState({
    student_name: '',
    student_surname: '',
    student_id: '',
    institution: user?.institution || '',
    issue_date: new Date().toISOString().split('T')[0],
    expiry_date: '',
    grade: '',
    subjects: [],
    exam_session: '',
    certificate_number: ''
  });
  const [singleFile, setSingleFile] = useState(null);
  const [singleLoading, setSingleLoading] = useState(false);
  const [singleError, setSingleError] = useState('');
  
  // OCR extracted data state
  const [extractedData, setExtractedData] = useState(null);
  const [extractedDisplay, setExtractedDisplay] = useState(null);
  const [ocrLoading, setOcrLoading] = useState(false);
  const [ocrError, setOcrError] = useState('');
  const [showOcrSidebar, setShowOcrSidebar] = useState(false);
  const [ocrConfidence, setOcrConfidence] = useState(null);
  const [showScanner, setShowScanner] = useState(false);

  // Verification state
  const [verifyHash, setVerifyHash] = useState('');
  const [verifyFile, setVerifyFile] = useState(null);
  const [verifyMethod, setVerifyMethod] = useState('both');
  const [verifyLoading, setVerifyLoading] = useState(false);
  const [verifyPct, setVerifyPct] = useState(0);
  const [verifyError, setVerifyError] = useState('');
  const [verifyResult, setVerifyResult] = useState(null);

  // UI state
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [showLogoutConfirm, setShowLogoutConfirm] = useState(false);
  const [showProfileEditor, setShowProfileEditor] = useState(false);
  const [actionMsg, setActionMsg] = useState('');
  const [activeView, setActiveView] = useState('dashboard');
  const [selectedCertificate, setSelectedCertificate] = useState(null);
  const [showPreview, setShowPreview] = useState(false);

  // Filters
  const [statusFilter, setStatusFilter] = useState('all');
  const [dateRange, setDateRange] = useState({ start: '', end: '' });
  const [searchTerm, setSearchTerm] = useState('');

  // Mock data for development
  const mockStats = {
    total: 24,
    verified: 18,
    pending: 4,
    rejected: 2,
    monthly: 8,
    ocr_today: 3
  };

  const mockCertificates = [
    {
      id: 1,
      student_name: 'John Doe',
      student_id: 'STU2024001',
      certificate_hash: '0x7d8a9f3e2b1c4d5e6f7a8b9c0d1e2f3a4b5c6d7e',
      issue_date: new Date().toISOString(),
      status: 'verified',
      blockchain_tx_id: '0x9a8b7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b'
    },
    {
      id: 2,
      student_name: 'Jane Smith',
      student_id: 'STU2024002',
      certificate_hash: '0x1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b',
      issue_date: new Date(Date.now() - 86400000).toISOString(),
      status: 'verified',
      blockchain_tx_id: '0x8f7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b1a0f9e'
    },
    {
      id: 3,
      student_name: 'Mike Johnson',
      student_id: 'STU2024003',
      certificate_hash: '0x9f8e7d6c5b4a3f2e1d0c9b8a7f6e5d4c3b2a1f0e',
      issue_date: new Date(Date.now() - 172800000).toISOString(),
      status: 'pending',
      blockchain_tx_id: null
    },
    {
      id: 4,
      student_name: 'Sarah Williams',
      student_id: 'STU2024004',
      certificate_hash: '0x8a7b6c5d4e3f2a1b0c9d8e7f6a5b4c3d2e1f0a9b',
      issue_date: new Date(Date.now() - 259200000).toISOString(),
      status: 'rejected',
      blockchain_tx_id: null
    }
  ];

  const mockInstitutionInfo = {
    name: 'Ecol',
    code: 'ECL001',
    credits: 150
  };

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
      return verifyHash.trim().length > 0;
    } else if (verifyMethod === 'file') {
      return !!verifyFile;
    } else {
      return verifyHash.trim().length > 0 && !!verifyFile;
    }
  }, [verifyHash, verifyFile, verifyMethod, verifyLoading]);

  // Mock OCR extraction function
  const mockExtractCertificateData = (file) => {
    return new Promise((resolve) => {
      setTimeout(() => {
        // Generate random mock data based on file name
        const randomNum = Math.floor(Math.random() * 1000);
        const firstName = ['John', 'Jane', 'Michael', 'Sarah', 'David', 'Emma'][Math.floor(Math.random() * 6)];
        const lastName = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia'][Math.floor(Math.random() * 6)];
        
        const mockData = {
          display_html: `
            <div class="p-4">
              <h3 class="font-bold text-lg">Extracted Certificate Data</h3>
              <div class="mt-2 space-y-2">
                <p><span class="font-medium">Student:</span> ${firstName} ${lastName}</p>
                <p><span class="font-medium">ID:</span> STU2024${randomNum}</p>
                <p><span class="font-medium">Institution:</span> Ecol</p>
                <p><span class="font-medium">Issue Date:</span> ${new Date().toISOString().split('T')[0]}</p>
                <p><span class="font-medium">Grade:</span> ${['A', 'B', 'C', 'Distinction'][Math.floor(Math.random() * 4)]}</p>
                <p><span class="font-medium">Subjects:</span> Mathematics, English, Science</p>
              </div>
            </div>
          `,
          form_data: {
            student_name: `${firstName} ${lastName}`,
            student_id: `STU2024${randomNum}`,
            institution: 'Ecol',
            issue_date: new Date().toISOString().split('T')[0],
            grade: ['A', 'B', 'C', 'Distinction'][Math.floor(Math.random() * 4)],
            subjects: ['Mathematics', 'English', 'Science'],
            examination_session: 'November 2023',
            certificate_numbers: [`CERT-${randomNum}`]
          },
          validation: {
            confidence: 85 + Math.floor(Math.random() * 15)
          }
        };
        resolve({ data: mockData });
      }, 2000); // Simulate 2 second processing
    });
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

    // Trigger OCR extraction
    setOcrLoading(true);
    setOcrError('');
    setExtractedDisplay(null);
    
    try {
      let response;
      
      // Check if the API function exists, otherwise use mock
      if (certificateApi.extractCertificateData) {
        const formData = new FormData();
        formData.append('file', file);
        response = await certificateApi.extractCertificateData(formData);
      } else {
        // Use mock implementation
        response = await mockExtractCertificateData(file);
      }
      
      if (response.data) {
        const data = response.data;
        setExtractedData(data);
        setExtractedDisplay(data.display_html);
        setOcrConfidence(data.validation?.confidence);
        setShowOcrSidebar(true);
        
        // Auto-fill form with extracted data
        if (data.form_data) {
          // Parse full name into first name and surname if needed
          const fullName = data.form_data.student_name || '';
          const nameParts = fullName.split(' ');
          const firstName = nameParts[0] || '';
          const lastName = nameParts.slice(1).join(' ') || '';
          
          setSingleForm(prev => ({
            ...prev,
            student_name: firstName,
            student_surname: lastName,
            student_id: data.form_data.student_id || prev.student_id,
            institution: data.form_data.institution || prev.institution,
            issue_date: data.form_data.issue_date || prev.issue_date,
            grade: data.form_data.grade || prev.grade,
            subjects: data.form_data.subjects || prev.subjects,
            exam_session: data.form_data.examination_session || prev.exam_session,
            certificate_number: data.form_data.certificate_numbers?.[0] || prev.certificate_number
          }));
        }
        
        setActionMsg('✅ Certificate scanned successfully! Please review the extracted data.');
        setTimeout(() => setActionMsg(''), 5000);
      }
    } catch (err) {
      setOcrError('Failed to extract data from certificate. Please fill manually or try again.');
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

    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500));
      
      const fullName = `${singleForm.student_name} ${singleForm.student_surname}`.trim();
      
      setActionMsg(`✅ Certificate issued successfully for ${fullName}`);
      
      // Add to mock certificates
      const newCert = {
        id: mockCertificates.length + 1,
        student_name: fullName,
        student_id: singleForm.student_id,
        certificate_hash: '0x' + Math.random().toString(16).substring(2, 42),
        issue_date: singleForm.issue_date,
        status: 'pending',
        blockchain_tx_id: null
      };
      
      mockCertificates.unshift(newCert);
      setMyCertificates([newCert, ...myCertificates]);
      
      // Update stats
      setIssuerStats(prev => ({
        ...prev,
        total: (prev?.total || 0) + 1,
        pending: (prev?.pending || 0) + 1
      }));
      
      // Reset form
      setSingleForm({
        student_name: '',
        student_surname: '',
        student_id: '',
        institution: user?.institution || '',
        issue_date: new Date().toISOString().split('T')[0],
        expiry_date: '',
        grade: '',
        subjects: [],
        exam_session: '',
        certificate_number: ''
      });
      
      setSingleFile(null);
      setExtractedData(null);
      setExtractedDisplay(null);
      setShowOcrSidebar(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      
      setTimeout(() => setActionMsg(''), 3000);
    } catch (err) {
      setSingleError(err?.message || 'Failed to issue certificate');
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
    setBulkLoading(true);

    try {
      // Simulate progress
      for (let i = 0; i <= 100; i += 10) {
        await new Promise(resolve => setTimeout(resolve, 200));
        setBulkPct(i);
      }
      
      const mockResult = {
        success_count: Math.floor(bulkFiles.length * 0.8),
        failure_count: Math.floor(bulkFiles.length * 0.2),
        total_processed: bulkFiles.length,
        results: bulkFiles.map((file, idx) => ({
          filename: file.name,
          success: idx % 5 !== 0, // 80% success rate
          certificate_hash: idx % 5 !== 0 ? '0x' + Math.random().toString(16).substring(2, 42) : null,
          extracted: idx % 5 !== 0 ? { student_name: `Student ${idx + 1}` } : null,
          ocr_confidence: 70 + Math.floor(Math.random() * 25),
          error: idx % 5 === 0 ? 'OCR failed: Low quality image' : null
        }))
      };
      
      setBulkResult(mockResult);
      setActionMsg(`✅ Successfully uploaded ${mockResult.success_count} certificates`);
      
      // Refresh certificates
      fetchCertificates();
      
      setTimeout(() => setActionMsg(''), 3000);
    } catch (err) {
      setBulkError(err?.message || 'Bulk upload failed');
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
      // Simulate progress
      for (let i = 0; i <= 100; i += 20) {
        await new Promise(resolve => setTimeout(resolve, 300));
        setVerifyPct(i);
      }
      
      // Mock verification result
      const mockResult = {
        verified: Math.random() > 0.3,
        blockchain_verified: Math.random() > 0.2,
        verification_id: 'VER-' + Math.random().toString(36).substring(2, 10).toUpperCase(),
        certificate_data: {
          student_name: 'John Doe',
          student_id: 'STU2024001',
          institution: 'Ecol',
          issue_date: new Date().toISOString()
        }
      };
      
      setVerifyResult(mockResult);
      
      if (mockResult.verified) {
        setActionMsg('✅ Certificate verified successfully!');
      } else {
        setActionMsg('⚠️ Certificate verification failed');
      }
      
      setTimeout(() => setActionMsg(''), 3000);
    } catch (err) {
      setVerifyError(err?.message || 'Verification failed');
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
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setActionMsg('✅ Certificate revoked successfully');
      
      // Update certificate status
      setMyCertificates(prev => 
        prev.map(cert => 
          cert.id === certificateId ? { ...cert, status: 'revoked' } : cert
        )
      );
      
      setTimeout(() => setActionMsg(''), 3000);
    } catch (err) {
      setActionMsg('❌ Failed to revoke certificate');
      setTimeout(() => setActionMsg(''), 3000);
    }
  };

  // Handle profile update
  const handleProfileUpdate = async (updatedData) => {
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setActionMsg('✅ Profile updated successfully');
      setShowProfileEditor(false);
      setTimeout(() => setActionMsg(''), 3000);
    } catch (error) {
      setSingleError('Failed to update profile: ' + error.message);
    }
  };

  // Handle logout
  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  // Fetch data
  const fetchStats = useCallback(async () => {
    try {
      // Use mock data
      setIssuerStats(mockStats);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  }, []);

  const fetchCertificates = useCallback(async () => {
    try {
      // Use mock data
      setMyCertificates(mockCertificates);
    } catch (error) {
      console.error('Failed to fetch certificates:', error);
    }
  }, []);

  const fetchInstitutionInfo = useCallback(async () => {
    try {
      setInstitutionInfo(mockInstitutionInfo);
    } catch (error) {
      console.error('Failed to fetch institution info:', error);
    }
  }, []);

  // Initial data fetch
  useEffect(() => {
    let mounted = true;
    
    const fetchInitialData = async () => {
      try {
        if (mounted) {
          setIssuerStats(mockStats);
          setMyCertificates(mockCertificates);
        }
      } catch (error) {
        console.error('Failed to fetch initial data:', error);
      }
    };
    
    fetchInitialData();
    fetchInstitutionInfo();
    
    return () => {
      mounted = false;
    };
  }, [fetchInstitutionInfo]);

  // Filter certificates
  const filteredCertificates = useMemo(() => {
    return myCertificates.filter(cert => {
      if (statusFilter !== 'all' && cert.status !== statusFilter) return false;
      if (searchTerm) {
        const term = searchTerm.toLowerCase();
        return (
          cert.student_name?.toLowerCase().includes(term) ||
          cert.student_id?.toLowerCase().includes(term) ||
          cert.certificate_hash?.toLowerCase().includes(term)
        );
      }
      return true;
    });
  }, [myCertificates, statusFilter, searchTerm]);

  const getStatusColor = (status) => {
    switch(status?.toLowerCase()) {
      case 'verified': return 'bg-green-100 text-green-800 border-green-200';
      case 'pending': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'rejected': return 'bg-red-100 text-red-800 border-red-200';
      case 'revoked': return 'bg-gray-100 text-gray-800 border-gray-200';
      default: return 'bg-blue-100 text-blue-800 border-blue-200';
    }
  };

  const getStatusIcon = (status) => {
    switch(status?.toLowerCase()) {
      case 'verified': return '✅';
      case 'pending': return '⏳';
      case 'rejected': return '❌';
      case 'revoked': return '🚫';
      default: return '📄';
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex">
      {/* Modals */}
      {showBulkModal && (
        <BulkUploadModal
          files={bulkFiles}
          setFiles={setBulkFiles}
          onClose={() => setShowBulkModal(false)}
          onConfirm={handleBulkUpload}
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
        />
      )}

      {showProfileEditor && (
        <ProfileEditor
          user={user}
          onClose={() => setShowProfileEditor(false)}
          onSave={handleProfileUpdate}
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

      {/* Blockchain Status Indicator */}
      <BlockchainStatus />

      {/* Left Sidebar */}
      <div className={`${sidebarCollapsed ? 'w-20' : 'w-80'} bg-gradient-to-b from-gray-900 via-gray-800 to-gray-900 text-white transition-all duration-300 shadow-2xl flex flex-col relative`}>
        {/* Logo Area */}
        <div className="p-6 border-b border-gray-700/50">
          <div className="flex items-center space-x-4">
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-r from-green-500 to-blue-500 rounded-xl blur-lg opacity-50 animate-pulse"></div>
              <div className="relative bg-gradient-to-r from-green-500 to-blue-500 p-3 rounded-xl shadow-lg transform hover:scale-105 transition-transform duration-300">
                <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
              </div>
            </div>
            {!sidebarCollapsed && (
              <div className="animate-fadeIn">
                <span className="text-2xl font-bold bg-gradient-to-r from-green-400 to-blue-400 bg-clip-text text-transparent">CertiVert</span>
                <span className="block text-xs text-gray-400 mt-1">Issuer Portal</span>
              </div>
            )}
          </div>
        </div>

        {/* User Profile Card */}
        <div className="p-6 border-b border-gray-700/50">
          <div className="flex items-center space-x-4">
            <div className="relative">
              <div className="w-16 h-16 rounded-full bg-gradient-to-r from-green-500 to-blue-500 flex items-center justify-center text-white font-bold text-xl shadow-lg transform hover:scale-105 transition-transform">
                {user?.username?.charAt(0).toUpperCase() || 'I'}
              </div>
              <div className="absolute -bottom-1 -right-1 w-5 h-5 bg-green-500 border-2 border-gray-800 rounded-full animate-pulse"></div>
            </div>
            {!sidebarCollapsed && (
              <div className="flex-1">
                <p className="font-semibold text-lg">{user?.username || 'Issuer'}</p>
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
              </div>
            )}
          </div>
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
                    <div 
                      className="h-full bg-gradient-to-r from-green-500 to-green-400 rounded-full"
                      style={{ width: `${issuerStats?.total > 0 ? (issuerStats.verified / issuerStats.total) * 100 : 0}%` }}
                    ></div>
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
          <div className="space-y-2">
            <button
              onClick={() => setActiveView('dashboard')}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 relative group ${
                activeView === 'dashboard'
                  ? 'bg-gradient-to-r from-green-600 to-blue-600 text-white shadow-lg transform scale-105'
                  : 'text-gray-300 hover:bg-gray-700/50 hover:text-white'
              }`}
            >
              <span className="text-xl">📊</span>
              {!sidebarCollapsed && (
                <>
                  <span className="font-medium">Dashboard</span>
                  {activeView === 'dashboard' && (
                    <span className="absolute right-3 w-2 h-2 bg-white rounded-full animate-ping"></span>
                  )}
                </>
              )}
            </button>
            
            <button
              onClick={() => setActiveView('issue')}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                activeView === 'issue'
                  ? 'bg-gradient-to-r from-green-600 to-blue-600 text-white shadow-lg transform scale-105'
                  : 'text-gray-300 hover:bg-gray-700/50 hover:text-white'
              }`}
            >
              <span className="text-xl">📜</span>
              {!sidebarCollapsed && <span className="font-medium">Issue Certificate</span>}
            </button>
            
            <button
              onClick={() => setActiveView('bulk')}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                activeView === 'bulk'
                  ? 'bg-gradient-to-r from-purple-600 to-pink-600 text-white shadow-lg transform scale-105'
                  : 'text-gray-300 hover:bg-gray-700/50 hover:text-white'
              }`}
            >
              <span className="text-xl">📤</span>
              {!sidebarCollapsed && <span className="font-medium">Bulk Upload</span>}
            </button>
            
            <button
              onClick={() => setActiveView('verify')}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                activeView === 'verify'
                  ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg transform scale-105'
                  : 'text-gray-300 hover:bg-gray-700/50 hover:text-white'
              }`}
            >
              <span className="text-xl">✓</span>
              {!sidebarCollapsed && <span className="font-medium">Verify</span>}
            </button>
            
            <button
              onClick={() => setActiveView('certificates')}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                activeView === 'certificates'
                  ? 'bg-gradient-to-r from-yellow-600 to-orange-600 text-white shadow-lg transform scale-105'
                  : 'text-gray-300 hover:bg-gray-700/50 hover:text-white'
              }`}
            >
              <span className="text-xl">📋</span>
              {!sidebarCollapsed && <span className="font-medium">Certificates</span>}
            </button>
            
            <button
              onClick={() => setActiveView('settings')}
              className={`w-full flex items-center space-x-3 px-4 py-3 rounded-xl transition-all duration-200 ${
                activeView === 'settings'
                  ? 'bg-gradient-to-r from-gray-600 to-gray-700 text-white shadow-lg transform scale-105'
                  : 'text-gray-300 hover:bg-gray-700/50 hover:text-white'
              }`}
            >
              <span className="text-xl">⚙️</span>
              {!sidebarCollapsed && <span className="font-medium">Settings</span>}
            </button>
          </div>
        </nav>

        {/* Institution Info */}
        {!sidebarCollapsed && institutionInfo && (
          <div className="px-4 py-3 mx-4 mb-4 bg-gray-800/50 rounded-xl">
            <p className="text-xs text-gray-400 mb-1">Institution</p>
            <p className="text-sm font-medium text-white">{institutionInfo.name}</p>
            <p className="text-xs text-gray-400">ID: {institutionInfo.code}</p>
            <div className="mt-2 flex items-center">
              <span className="text-xs text-gray-400">Balance:</span>
              <span className="ml-2 text-sm font-bold text-green-400">
                {institutionInfo.credits || 0} credits
              </span>
            </div>
          </div>
        )}

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
        </div>

        {/* Sidebar Toggle */}
        <button
          onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          className="absolute bottom-6 -right-3 w-8 h-8 bg-gray-800 rounded-full flex items-center justify-center text-white border-2 border-gray-700 hover:bg-gray-700 transition-colors shadow-lg"
        >
          {sidebarCollapsed ? '→' : '←'}
        </button>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 overflow-auto">
        {/* Top Bar */}
        <div className="bg-white/80 backdrop-blur-md shadow-sm sticky top-0 z-10 border-b border-gray-200">
          <div className="px-8 py-4 flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-800">
                {activeView === 'dashboard' && 'Issuer Dashboard'}
                {activeView === 'issue' && 'Issue Certificate'}
                {activeView === 'bulk' && 'Bulk Upload Certificates'}
                {activeView === 'verify' && 'Verify Certificate'}
                {activeView === 'certificates' && 'My Certificates'}
                {activeView === 'settings' && 'Account Settings'}
              </h1>
              <p className="text-sm text-gray-500">
                {activeView === 'dashboard' && 'Overview of your certificate issuance activities'}
                {activeView === 'issue' && 'Issue a new LGCSE certificate with OCR auto-fill'}
                {activeView === 'bulk' && 'Upload multiple certificates at once'}
                {activeView === 'verify' && 'Verify certificate authenticity'}
                {activeView === 'certificates' && 'Manage your issued certificates'}
                {activeView === 'settings' && 'Manage your profile and preferences'}
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <button 
                onClick={() => setShowProfileEditor(true)}
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 rounded-xl text-gray-700 text-sm font-medium transition-colors flex items-center space-x-2"
              >
                <span>👤</span>
                <span>Profile</span>
              </button>
              <div className="relative">
                <span className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full animate-pulse"></span>
                <div className="w-10 h-10 rounded-full bg-gradient-to-r from-green-500 to-blue-500 flex items-center justify-center text-white font-bold shadow-lg">
                  {user?.username?.charAt(0).toUpperCase() || 'I'}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Action Messages */}
        {actionMsg && (
          <div className="mx-8 mt-4 px-6 py-4 rounded-xl bg-gradient-to-r from-green-500 to-green-600 text-white shadow-lg animate-slideDown flex items-center">
            <span className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center mr-3">✓</span>
            {actionMsg}
          </div>
        )}

        {/* Error Messages */}
        {(singleError || bulkError || verifyError || ocrError) && (
          <div className="mx-8 mt-4 px-6 py-4 rounded-xl bg-gradient-to-r from-red-500 to-red-600 text-white shadow-lg animate-slideDown flex items-center">
            <span className="w-6 h-6 rounded-full bg-white/20 flex items-center justify-center mr-3">⚠️</span>
            {singleError || bulkError || verifyError || ocrError}
          </div>
        )}

        {/* Content Area */}
        <div className="p-8">
          {/* Dashboard View */}
          {activeView === 'dashboard' && (
            <div className="space-y-8">
              {/* Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                <div className="bg-white rounded-2xl shadow-lg p-6 transform hover:scale-105 transition-all duration-300 border-l-4 border-green-500">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-gray-500 text-sm">Total Issued</p>
                      <p className="text-3xl font-bold text-gray-800">{issuerStats?.total ?? 0}</p>
                    </div>
                    <div className="w-12 h-12 bg-green-100 rounded-xl flex items-center justify-center">
                      <span className="text-2xl">📜</span>
                    </div>
                  </div>
                  <p className="text-xs text-gray-400 mt-2">All time certificates</p>
                </div>

                <div className="bg-white rounded-2xl shadow-lg p-6 transform hover:scale-105 transition-all duration-300 border-l-4 border-blue-500">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-gray-500 text-sm">Verified</p>
                      <p className="text-3xl font-bold text-gray-800">{issuerStats?.verified ?? 0}</p>
                    </div>
                    <div className="w-12 h-12 bg-blue-100 rounded-xl flex items-center justify-center">
                      <span className="text-2xl">✅</span>
                    </div>
                  </div>
                  <p className="text-xs text-gray-400 mt-2">{issuerStats?.total > 0 ? Math.round((issuerStats.verified / issuerStats.total) * 100) : 0}% success rate</p>
                </div>

                <div className="bg-white rounded-2xl shadow-lg p-6 transform hover:scale-105 transition-all duration-300 border-l-4 border-yellow-500">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-gray-500 text-sm">Pending</p>
                      <p className="text-3xl font-bold text-gray-800">{issuerStats?.pending ?? 0}</p>
                    </div>
                    <div className="w-12 h-12 bg-yellow-100 rounded-xl flex items-center justify-center">
                      <span className="text-2xl">⏳</span>
                    </div>
                  </div>
                  <p className="text-xs text-gray-400 mt-2">Awaiting verification</p>
                </div>

                <div className="bg-white rounded-2xl shadow-lg p-6 transform hover:scale-105 transition-all duration-300 border-l-4 border-purple-500">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-gray-500 text-sm">OCR Today</p>
                      <p className="text-3xl font-bold text-gray-800">{issuerStats?.ocr_today ?? 0}</p>
                    </div>
                    <div className="w-12 h-12 bg-purple-100 rounded-xl flex items-center justify-center">
                      <span className="text-2xl">🔍</span>
                    </div>
                  </div>
                  <p className="text-xs text-gray-400 mt-2">Certificates scanned</p>
                </div>
              </div>

              {/* OCR Quick Scan Card */}
              <div className="bg-gradient-to-r from-purple-500 to-indigo-600 rounded-2xl shadow-xl p-6 text-white">
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

              {/* Recent Certificates */}
              <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
                <div className="px-6 py-4 bg-gradient-to-r from-green-500 to-blue-600 flex justify-between items-center">
                  <h3 className="text-lg font-semibold text-white">Recent Certificates</h3>
                  <button
                    onClick={() => setActiveView('certificates')}
                    className="px-3 py-1 bg-white/20 hover:bg-white/30 rounded-lg text-white text-sm transition-colors"
                  >
                    View All
                  </button>
                </div>
                
                {myCertificates.length === 0 ? (
                  <div className="p-12 text-center">
                    <div className="text-6xl mb-4">📜</div>
                    <p className="text-gray-500 text-lg">No certificates issued yet</p>
                    <p className="text-sm text-gray-400 mt-2">Start by issuing your first certificate</p>
                    <button
                      onClick={() => setActiveView('issue')}
                      className="mt-4 px-6 py-2 bg-gradient-to-r from-green-500 to-blue-600 text-white rounded-xl hover:from-green-600 hover:to-blue-700 transition-all"
                    >
                      Issue Certificate
                    </button>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Student</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Hash</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Issue Date</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {myCertificates.slice(0, 5).map((cert, index) => (
                          <tr key={cert.id} className="hover:bg-gray-50 transition-colors animate-fadeIn" style={{ animationDelay: `${index * 50}ms` }}>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <div className="w-8 h-8 rounded-full bg-gradient-to-r from-green-500 to-blue-500 flex items-center justify-center text-white text-xs font-bold mr-2">
                                  {cert.student_name?.charAt(0).toUpperCase()}
                                </div>
                                <span className="text-sm font-medium text-gray-900">{cert.student_name}</span>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{cert.student_id}</td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded">
                                {cert.certificate_hash?.slice(0, 12)}...
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
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
                                className="text-blue-600 hover:text-blue-800 font-medium mr-3"
                              >
                                View
                              </button>
                              {cert.status === 'pending' && (
                                <button
                                  onClick={() => handleRevokeCertificate(cert.id)}
                                  className="text-red-600 hover:text-red-800 font-medium"
                                >
                                  Revoke
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
            </div>
          )}

          {/* Issue Certificate View */}
          {activeView === 'issue' && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Issue Form */}
              <div className="lg:col-span-2 bg-white rounded-2xl shadow-xl overflow-hidden">
                <div className="px-6 py-4 bg-gradient-to-r from-green-500 to-blue-600">
                  <h3 className="text-lg font-semibold text-white flex items-center">
                    <span className="w-2 h-2 bg-white rounded-full mr-2 animate-pulse"></span>
                    Issue New Certificate with OCR
                  </h3>
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
                          <p className="text-sm text-gray-500">Upload certificate to automatically extract data</p>
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
                              Upload File
                            </>
                          )}
                        </button>
                        <button
                          onClick={() => setShowScanner(true)}
                          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center"
                        >
                          <span className="mr-2">📷</span>
                          Camera
                        </button>
                      </div>
                    </div>
                    
                    {singleFile && !ocrLoading && (
                      <div className="mt-3 flex items-center justify-between bg-white p-2 rounded-lg">
                        <div className="flex items-center">
                          <span className="text-2xl mr-2">📄</span>
                          <span className="text-sm text-gray-600">{singleFile.name}</span>
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

                  <form onSubmit={handleIssueSingle} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          First Name <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="text"
                          value={singleForm.student_name}
                          onChange={(e) => setSingleForm({...singleForm, student_name: e.target.value})}
                          placeholder="First name"
                          className="w-full rounded-xl border-2 border-gray-200 px-4 py-2 text-sm focus:border-green-500 focus:ring focus:ring-green-200"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Surname <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="text"
                          value={singleForm.student_surname}
                          onChange={(e) => setSingleForm({...singleForm, student_surname: e.target.value})}
                          placeholder="Surname"
                          className="w-full rounded-xl border-2 border-gray-200 px-4 py-2 text-sm focus:border-green-500 focus:ring focus:ring-green-200"
                          required
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Student ID <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="text"
                          value={singleForm.student_id}
                          onChange={(e) => setSingleForm({...singleForm, student_id: e.target.value})}
                          placeholder="LGCSE ID"
                          className="w-full rounded-xl border-2 border-gray-200 px-4 py-2 text-sm focus:border-green-500 focus:ring focus:ring-green-200"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Certificate Number
                        </label>
                        <input
                          type="text"
                          value={singleForm.certificate_number}
                          onChange={(e) => setSingleForm({...singleForm, certificate_number: e.target.value})}
                          placeholder="Certificate number"
                          className="w-full rounded-xl border-2 border-gray-200 px-4 py-2 text-sm focus:border-green-500 focus:ring focus:ring-green-200"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Institution <span className="text-red-500">*</span>
                      </label>
                      <input
                        type="text"
                        value={singleForm.institution}
                        onChange={(e) => setSingleForm({...singleForm, institution: e.target.value})}
                        placeholder="Institution name"
                        className="w-full rounded-xl border-2 border-gray-200 px-4 py-2 text-sm focus:border-green-500 focus:ring focus:ring-green-200"
                        required
                      />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Issue Date <span className="text-red-500">*</span>
                        </label>
                        <input
                          type="date"
                          value={singleForm.issue_date}
                          onChange={(e) => setSingleForm({...singleForm, issue_date: e.target.value})}
                          className="w-full rounded-xl border-2 border-gray-200 px-4 py-2 text-sm focus:border-green-500 focus:ring focus:ring-green-200"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Exam Session
                        </label>
                        <input
                          type="text"
                          value={singleForm.exam_session}
                          onChange={(e) => setSingleForm({...singleForm, exam_session: e.target.value})}
                          placeholder="e.g., November 2023"
                          className="w-full rounded-xl border-2 border-gray-200 px-4 py-2 text-sm focus:border-green-500 focus:ring focus:ring-green-200"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
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
                        className="w-full rounded-xl border-2 border-gray-200 px-4 py-2 text-sm focus:border-green-500 focus:ring focus:ring-green-200"
                      />
                    </div>

                    <button
                      type="submit"
                      disabled={!canIssueSingle}
                      className={`w-full px-6 py-3 rounded-xl text-white font-medium transition-all transform hover:scale-105 ${
                        canIssueSingle 
                          ? 'bg-gradient-to-r from-green-500 to-blue-600 hover:from-green-600 hover:to-blue-700 shadow-lg' 
                          : 'bg-gray-300 cursor-not-allowed'
                      }`}
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
                    </button>
                  </form>

                  <div className="mt-4 text-xs text-gray-400 bg-gray-50 p-3 rounded-lg">
                    ℹ️ Upload a certificate image to auto-fill the form using OCR technology.
                  </div>
                </div>
              </div>

              {/* OCR Preview & Tips */}
              <div className="space-y-6">
                <div className="bg-gradient-to-br from-green-50 to-blue-50 rounded-2xl p-6">
                  <h4 className="text-sm font-semibold text-gray-800 mb-4 flex items-center">
                    <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                    Certificate Preview
                  </h4>
                  
                  {singleForm.student_name || singleForm.student_surname ? (
                    <div className="bg-white rounded-xl p-6 shadow-inner">
                      <div className="text-center mb-4">
                        <div className="w-16 h-16 mx-auto bg-gradient-to-r from-green-500 to-blue-500 rounded-full flex items-center justify-center text-white text-2xl mb-2">
                          {(singleForm.student_name?.charAt(0) || '') + (singleForm.student_surname?.charAt(0) || '')}
                        </div>
                        <h3 className="font-bold text-gray-800">
                          {singleForm.student_name} {singleForm.student_surname}
                        </h3>
                        <p className="text-sm text-gray-500">ID: {singleForm.student_id || '______'}</p>
                      </div>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-500">Institution:</span>
                          <span className="font-medium">{singleForm.institution || '______'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Issue Date:</span>
                          <span className="font-medium">{singleForm.issue_date}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Subjects:</span>
                          <span className="font-medium">{singleForm.subjects.length || 0}</span>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-12 bg-white rounded-xl">
                      <div className="text-4xl mb-3">📝</div>
                      <p className="text-gray-500">Fill in the form or upload a certificate</p>
                    </div>
                  )}
                </div>

                <div className="bg-white rounded-2xl p-6">
                  <h4 className="text-sm font-semibold text-gray-800 mb-3">OCR Tips</h4>
                  <ul className="space-y-2 text-sm text-gray-600">
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
                </div>
              </div>
            </div>
          )}

          {/* Bulk Upload View */}
          {activeView === 'bulk' && (
            <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
              <div className="px-6 py-4 bg-gradient-to-r from-purple-500 to-pink-600">
                <h3 className="text-lg font-semibold text-white">Bulk Certificate Upload with OCR</h3>
              </div>
              
              <div className="p-6">
                <div className="mb-6">
                  <div className="border-2 border-dashed border-gray-300 rounded-xl p-12 text-center hover:border-purple-500 transition-colors">
                    <input
                      type="file"
                      multiple
                      accept=".pdf,image/*"
                      onChange={(e) => setBulkFiles(Array.from(e.target.files || []))}
                      className="hidden"
                      id="bulk-upload"
                    />
                    <label htmlFor="bulk-upload" className="cursor-pointer">
                      <div className="text-6xl mb-4">📤</div>
                      <p className="text-xl text-gray-600 mb-2">Click to select files or drag and drop</p>
                      <p className="text-sm text-gray-400">Multiple PDF or Image files supported (OCR will extract data)</p>
                    </label>
                    {bulkFiles.length > 0 && (
                      <div className="mt-4">
                        <span className="inline-flex items-center px-4 py-2 rounded-full text-sm bg-purple-100 text-purple-800">
                          📎 {bulkFiles.length} file(s) selected
                        </span>
                      </div>
                    )}
                  </div>
                </div>

                {bulkFiles.length > 0 && (
                  <div className="mb-6">
                    <h4 className="text-sm font-medium text-gray-700 mb-3">Selected Files:</h4>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                      {bulkFiles.map((file, index) => (
                        <div key={index} className="bg-gray-50 rounded-lg p-3 flex items-center">
                          <span className="text-2xl mr-2">📄</span>
                          <div className="flex-1 truncate">
                            <p className="text-xs font-medium truncate">{file.name}</p>
                            <p className="text-xs text-gray-400">{(file.size / 1024).toFixed(1)} KB</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="flex justify-between items-center">
                  <button
                    onClick={() => setShowBulkModal(true)}
                    disabled={bulkFiles.length === 0 || bulkLoading}
                    className={`px-8 py-4 rounded-xl text-white font-medium transition-all transform hover:scale-105 ${
                      bulkFiles.length > 0 && !bulkLoading
                        ? 'bg-gradient-to-r from-purple-500 to-pink-600 hover:from-purple-600 hover:to-pink-700 shadow-lg'
                        : 'bg-gray-300 cursor-not-allowed'
                    }`}
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
                  </button>

                  {bulkFiles.length > 0 && !bulkLoading && (
                    <button
                      onClick={() => setBulkFiles([])}
                      className="text-sm text-gray-500 hover:text-red-500 transition-colors"
                    >
                      Clear all files
                    </button>
                  )}
                </div>

                {bulkLoading && (
                  <div className="mt-6 space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Processing files with OCR</span>
                      <span className="font-medium text-purple-600">{bulkPct}%</span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-gray-200 overflow-hidden">
                      <div 
                        className="h-2 rounded-full bg-gradient-to-r from-purple-500 to-pink-600 transition-all duration-300"
                        style={{ width: `${bulkPct}%` }}
                      />
                    </div>
                  </div>
                )}

                {bulkResult && (
                  <div className="mt-8 animate-fadeIn">
                    <h4 className="font-medium text-gray-800 mb-4">Upload Results</h4>
                    <div className="grid grid-cols-3 gap-4 mb-4">
                      <div className="bg-green-50 rounded-lg p-4 text-center">
                        <p className="text-2xl font-bold text-green-600">{bulkResult.success_count}</p>
                        <p className="text-xs text-gray-500">Successful</p>
                      </div>
                      <div className="bg-red-50 rounded-lg p-4 text-center">
                        <p className="text-2xl font-bold text-red-600">{bulkResult.failure_count}</p>
                        <p className="text-xs text-gray-500">Failed</p>
                      </div>
                      <div className="bg-blue-50 rounded-lg p-4 text-center">
                        <p className="text-2xl font-bold text-blue-600">{bulkResult.total_processed}</p>
                        <p className="text-xs text-gray-500">Total</p>
                      </div>
                    </div>

                    <div className="border rounded-xl overflow-hidden">
                      <table className="min-w-full text-sm">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">File</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Hash</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Student</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">OCR Confidence</th>
                            <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Error</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                          {bulkResult.results?.map((r, idx) => (
                            <tr key={idx} className="hover:bg-gray-50">
                              <td className="px-4 py-3 whitespace-nowrap text-sm">{r.filename}</td>
                              <td className="px-4 py-3 whitespace-nowrap">
                                <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                                  r.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                                }`}>
                                  {r.success ? 'Success' : 'Failed'}
                                </span>
                              </td>
                              <td className="px-4 py-3 whitespace-nowrap font-mono text-xs text-gray-600">
                                {r.certificate_hash ? `${r.certificate_hash.slice(0, 12)}...` : '-'}
                              </td>
                              <td className="px-4 py-3 whitespace-nowrap text-sm">{r.extracted?.student_name || '-'}</td>
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
                              <td className="px-4 py-3 whitespace-nowrap text-xs text-red-600">{r.error || ''}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Verify View */}
          {activeView === 'verify' && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              {/* Verification Form */}
              <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
                <div className="px-6 py-4 bg-gradient-to-r from-blue-500 to-indigo-600">
                  <h3 className="text-lg font-semibold text-white">Verify Certificate</h3>
                </div>
                
                <div className="p-6">
                  {/* Method Selection */}
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-3">
                      Verification Method
                    </label>
                    <div className="grid grid-cols-3 gap-3">
                      <button
                        type="button"
                        onClick={() => setVerifyMethod('hash')}
                        className={`px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                          verifyMethod === 'hash'
                            ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-lg transform scale-105'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        🔑 Hash Only
                      </button>
                      <button
                        type="button"
                        onClick={() => setVerifyMethod('file')}
                        className={`px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                          verifyMethod === 'file'
                            ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-lg transform scale-105'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        📄 File Only
                      </button>
                      <button
                        type="button"
                        onClick={() => setVerifyMethod('both')}
                        className={`px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                          verifyMethod === 'both'
                            ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-lg transform scale-105'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                        }`}
                      >
                        🔄 Both
                      </button>
                    </div>
                  </div>

                  <form onSubmit={handleVerify} className="space-y-4">
                    {(verifyMethod === 'hash' || verifyMethod === 'both') && (
                      <div className="animate-slideDown">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Certificate Hash
                        </label>
                        <input
                          value={verifyHash}
                          onChange={(e) => setVerifyHash(e.target.value)}
                          placeholder="Enter 64-character certificate hash"
                          className="w-full rounded-xl border-2 border-gray-200 px-4 py-3 text-sm focus:border-blue-500 focus:ring focus:ring-blue-200"
                        />
                      </div>
                    )}

                    {(verifyMethod === 'file' || verifyMethod === 'both') && (
                      <div className="animate-slideDown">
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Certificate File
                        </label>
                        <div className="border-2 border-dashed border-gray-200 rounded-xl p-4 text-center hover:border-blue-500 transition-colors">
                          <input
                            type="file"
                            accept=".pdf,image/*"
                            onChange={(e) => setVerifyFile(e.target.files?.[0] || null)}
                            className="hidden"
                            id="verify-file"
                          />
                          <label htmlFor="verify-file" className="cursor-pointer">
                            <span className="text-3xl mb-2 block">📎</span>
                            <span className="text-sm text-gray-600">
                              {verifyFile ? verifyFile.name : 'Click to select file'}
                            </span>
                          </label>
                        </div>
                      </div>
                    )}

                    <button
                      type="submit"
                      disabled={!canVerify}
                      className={`w-full px-6 py-3 rounded-xl text-white font-medium transition-all transform hover:scale-105 ${
                        canVerify 
                          ? 'bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 shadow-lg' 
                          : 'bg-gray-300 cursor-not-allowed'
                      }`}
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
                    </button>

                    {verifyLoading && (
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Progress</span>
                          <span className="font-medium text-blue-600">{verifyPct}%</span>
                        </div>
                        <div className="h-2 w-full rounded-full bg-gray-200 overflow-hidden">
                          <div 
                            className="h-2 rounded-full bg-gradient-to-r from-blue-500 to-indigo-600 transition-all duration-300"
                            style={{ width: `${verifyPct}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </form>
                </div>
              </div>

              {/* Result Display */}
              <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
                <div className="px-6 py-4 bg-gradient-to-r from-indigo-500 to-purple-600">
                  <h3 className="text-lg font-semibold text-white">Verification Result</h3>
                </div>
                
                <div className="p-6">
                  {!verifyResult ? (
                    <div className="text-center py-16">
                      <div className="text-7xl mb-6 animate-bounce">🔍</div>
                      <p className="text-gray-500 text-lg">Ready to verify</p>
                      <p className="text-sm text-gray-400 mt-2">Enter details to check authenticity</p>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div className={`p-6 rounded-xl ${
                        verifyResult.verified ? 'bg-green-50 border-2 border-green-200' : 'bg-red-50 border-2 border-red-200'
                      }`}>
                        <div className="flex items-center">
                          <div className={`w-16 h-16 rounded-full flex items-center justify-center text-3xl mr-4 ${
                            verifyResult.verified ? 'bg-green-100' : 'bg-red-100'
                          }`}>
                            {verifyResult.verified ? '✅' : '❌'}
                          </div>
                          <div>
                            <h4 className={`text-xl font-bold ${verifyResult.verified ? 'text-green-700' : 'text-red-700'}`}>
                              {verifyResult.verified ? 'VALID CERTIFICATE' : 'INVALID CERTIFICATE'}
                            </h4>
                            <p className="text-sm text-gray-600 mt-1">
                              Blockchain: {verifyResult.blockchain_verified ? '✅ Verified' : '❌ Not Found'}
                            </p>
                          </div>
                        </div>
                      </div>

                      {verifyResult.certificate_data && (
                        <div className="bg-white rounded-xl border-2 border-gray-100 p-4">
                          <h5 className="text-sm font-semibold text-gray-700 mb-3">Certificate Details</h5>
                          <div className="grid grid-cols-2 gap-3">
                            <div className="bg-gray-50 p-3 rounded-lg">
                              <p className="text-xs text-gray-500">Student Name</p>
                              <p className="text-sm font-medium text-gray-800">{verifyResult.certificate_data.student_name}</p>
                            </div>
                            <div className="bg-gray-50 p-3 rounded-lg">
                              <p className="text-xs text-gray-500">Student ID</p>
                              <p className="text-sm font-medium text-gray-800">{verifyResult.certificate_data.student_id}</p>
                            </div>
                            <div className="bg-gray-50 p-3 rounded-lg">
                              <p className="text-xs text-gray-500">Institution</p>
                              <p className="text-sm font-medium text-gray-800">{verifyResult.certificate_data.institution}</p>
                            </div>
                            <div className="bg-gray-50 p-3 rounded-lg">
                              <p className="text-xs text-gray-500">Issue Date</p>
                              <p className="text-sm font-medium text-gray-800">{formatDate(verifyResult.certificate_data.issue_date)}</p>
                            </div>
                          </div>
                        </div>
                      )}

                      <div className="bg-gray-50 rounded-xl p-3">
                        <p className="text-xs text-gray-500 mb-1">Verification ID</p>
                        <p className="text-sm font-mono bg-white p-2 rounded border border-gray-200">
                          {verifyResult.verification_id}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Certificates List View */}
          {activeView === 'certificates' && (
            <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
              <div className="px-6 py-4 bg-gradient-to-r from-yellow-500 to-orange-600">
                <h3 className="text-lg font-semibold text-white">My Certificates</h3>
              </div>
              
              <div className="p-6">
                {/* Filters */}
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">Status</label>
                    <select
                      value={statusFilter}
                      onChange={(e) => setStatusFilter(e.target.value)}
                      className="w-full rounded-lg border-2 border-gray-200 px-3 py-2 text-sm focus:border-yellow-500"
                    >
                      <option value="all">All Status</option>
                      <option value="pending">Pending</option>
                      <option value="verified">Verified</option>
                      <option value="rejected">Rejected</option>
                      <option value="revoked">Revoked</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">Search</label>
                    <input
                      type="text"
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      placeholder="Name, ID, or Hash"
                      className="w-full rounded-lg border-2 border-gray-200 px-3 py-2 text-sm focus:border-yellow-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">From Date</label>
                    <input
                      type="date"
                      value={dateRange.start}
                      onChange={(e) => setDateRange({...dateRange, start: e.target.value})}
                      className="w-full rounded-lg border-2 border-gray-200 px-3 py-2 text-sm focus:border-yellow-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-xs text-gray-500 mb-1">To Date</label>
                    <input
                      type="date"
                      value={dateRange.end}
                      onChange={(e) => setDateRange({...dateRange, end: e.target.value})}
                      className="w-full rounded-lg border-2 border-gray-200 px-3 py-2 text-sm focus:border-yellow-500"
                    />
                  </div>
                </div>

                {/* Certificates Table */}
                {filteredCertificates.length === 0 ? (
                  <div className="text-center py-16">
                    <div className="text-6xl mb-4">📋</div>
                    <p className="text-gray-500 text-lg">No certificates found</p>
                    <p className="text-sm text-gray-400 mt-2">Try adjusting your filters or issue new certificates</p>
                  </div>
                ) : (
                  <div className="overflow-x-auto">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Student</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">ID</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Hash</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Issue Date</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Blockchain</th>
                          <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {filteredCertificates.map((cert, index) => (
                          <tr key={cert.id} className="hover:bg-gray-50 transition-colors">
                            <td className="px-6 py-4 whitespace-nowrap">
                              <div className="flex items-center">
                                <div className="w-8 h-8 rounded-full bg-gradient-to-r from-yellow-500 to-orange-500 flex items-center justify-center text-white text-xs font-bold mr-2">
                                  {cert.student_name?.charAt(0).toUpperCase()}
                                </div>
                                <span className="text-sm font-medium text-gray-900">{cert.student_name}</span>
                              </div>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{cert.student_id}</td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded">
                                {cert.certificate_hash?.slice(0, 12)}...
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                              {formatDate(cert.issue_date)}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              <span className={`px-3 py-1 rounded-full text-xs font-medium ${getStatusColor(cert.status)}`}>
                                {getStatusIcon(cert.status)} {cert.status}
                              </span>
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap">
                              {cert.blockchain_tx_id ? (
                                <span className="text-xs font-mono bg-blue-100 text-blue-800 px-2 py-1 rounded">
                                  {cert.blockchain_tx_id.slice(0, 10)}...
                                </span>
                              ) : (
                                <span className="text-xs text-gray-400">Pending</span>
                              )}
                            </td>
                            <td className="px-6 py-4 whitespace-nowrap text-sm">
                              <button
                                onClick={() => {
                                  setSelectedCertificate(cert);
                                  setShowPreview(true);
                                }}
                                className="text-blue-600 hover:text-blue-800 font-medium mr-3"
                              >
                                View
                              </button>
                              {cert.status === 'pending' && (
                                <button
                                  onClick={() => handleRevokeCertificate(cert.id)}
                                  className="text-red-600 hover:text-red-800 font-medium"
                                >
                                  Revoke
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
            </div>
          )}

          {/* Settings View */}
          {activeView === 'settings' && (
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Profile Settings */}
              <div className="lg:col-span-2 bg-white rounded-2xl shadow-xl overflow-hidden">
                <div className="px-6 py-4 bg-gradient-to-r from-gray-700 to-gray-800">
                  <h3 className="text-lg font-semibold text-white">Profile Settings</h3>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    <div className="flex items-center space-x-4">
                      <div className="relative">
                        <div className="w-20 h-20 rounded-full bg-gradient-to-r from-green-500 to-blue-500 flex items-center justify-center text-white font-bold text-2xl">
                          {user?.username?.charAt(0).toUpperCase() || 'I'}
                        </div>
                        <button className="absolute bottom-0 right-0 w-6 h-6 bg-white rounded-full flex items-center justify-center shadow-lg hover:bg-gray-100">
                          📷
                        </button>
                      </div>
                      <div>
                        <h4 className="text-lg font-medium text-gray-800">{user?.username || 'Issuer'}</h4>
                        <p className="text-sm text-gray-500">{user?.email || 'issuer@example.com'}</p>
                        <p className="text-xs text-gray-400 mt-1">Member since {new Date().getFullYear()}</p>
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
              <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
                <div className="px-6 py-4 bg-gradient-to-r from-green-600 to-green-700">
                  <h3 className="text-lg font-semibold text-white">Institution Stats</h3>
                </div>
                <div className="p-6">
                  <div className="space-y-4">
                    <div className="text-center">
                      <p className="text-3xl font-bold text-green-600">{institutionInfo?.credits || 0}</p>
                      <p className="text-sm text-gray-500">Available Credits</p>
                    </div>
                    
                    <div className="border-t pt-4">
                      <div className="flex justify-between mb-2">
                        <span className="text-sm text-gray-600">Certificates Issued</span>
                        <span className="font-medium">{issuerStats?.total || 0}</span>
                      </div>
                      <div className="flex justify-between mb-2">
                        <span className="text-sm text-gray-600">This Month</span>
                        <span className="font-medium">{issuerStats?.monthly || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">OCR Scans Today</span>
                        <span className="font-medium">{issuerStats?.ocr_today || 0}</span>
                      </div>
                    </div>
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
            transform: translateY(-20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        @keyframes slideUp {
          from {
            opacity: 0;
            transform: translateY(20px);
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
        
        @keyframes scaleIn {
          from {
            opacity: 0;
            transform: scale(0.9);
          }
          to {
            opacity: 1;
            transform: scale(1);
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
        
        .animate-scaleIn {
          animation: scaleIn 0.3s ease-out;
        }
      `}</style>
    </div>
  );
};

export default IssuerDashboard;