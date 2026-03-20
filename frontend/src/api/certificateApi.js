// src/api/certificateApi.js
import api from './axiosConfig';

export const certificateApi = {
  // Upload certificate file (image/PDF)
  uploadCertificate: async (formData, onProgress) => {
    const response = await api.upload('/certificates/upload', formData, {
      onUploadProgress: onProgress
    });
    return response.data;
  },

  // Bulk upload certificates (multiple PDFs/images)
  uploadCertificatesBulk: async (files, onProgress) => {
    const formData = new FormData();
    files.forEach((f) => formData.append('files', f));
    const response = await api.upload('/certificates/upload-bulk', formData, {
      onUploadProgress: onProgress
    });
    return response.data;
  },
  
  // Extract data from certificate file using OCR
  extractCertificateData: async (formData) => {
    const response = await api.post('/ocr/extract', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      }
    });
    return response.data;
  },

  // Alternative OCR endpoint (fallback)
  extractCertificateDataLegacy: async (formData) => {
    const response = await api.post('/ocr/extract-certificate-data', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      }
    });
    return response.data;
  },
  
  // Save extracted certificate data
  saveExtractedCertificate: async (certificateData) => {
    const response = await api.post('/ocr/save-extracted-certificate', certificateData);
    return response.data;
  },

  // Get OCR extraction history
  getExtractionHistory: async (limit = 10) => {
    const response = await api.get('/ocr/extraction-history', {
      params: { limit }
    });
    return response.data;
  },

  // Validate extracted certificate data
  validateExtractedData: async (certificateData) => {
    const response = await api.post('/ocr/validate-extracted-data', certificateData);
    return response.data;
  },

  // Get OCR system status
  getOcrStatus: async () => {
    const response = await api.get('/ocr/ocr-status');
    return response.data;
  },
  
  // Issue a new certificate
  issueCertificate: async (formData) => {
    const response = await api.post('/certificates/issue', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      }
    });
    return response.data;
  },
  
  // Generate and store certificate with hash
  createCertificate: async (certificateData) => {
    const response = await api.post('/certificates/create', certificateData);
    return response.data;
  },
  
  // Get certificate by ID
  getCertificate: async (certificateId) => {
    const response = await api.get(`/certificates/${certificateId}`);
    return response.data;
  },
  
  // Get all certificates for issuer
  getIssuerCertificates: async (issuerId, page = 1, limit = 10) => {
    const response = await api.get(`/issuers/${issuerId}/certificates`, {
      params: { page, limit }
    });
    return response.data;
  },

  // Issuer (current user) stats
  getMyIssuerStats: async () => {
    const response = await api.get('/api/issuer/stats');
    return response.data;
  },

  // Issuer (current user) certificates
  getMyIssuerCertificates: async (limit = 50) => {
    const response = await api.get('/api/issuer/certificates', { params: { limit } });
    return response.data;
  },
  
  // Upload certificate for verification
  uploadForVerification: async (formData, onProgress) => {
    const response = await api.upload('/verify/upload', formData, {
      onUploadProgress: onProgress
    });
    return response.data;
  },
  
  // Verify certificate
  verifyCertificate: async ({ certificateHash, file, paymentMethod, paymentDigits, verificationMode }, onProgress) => {
    const formData = new FormData();
    
    // Only append certificate_hash if not file-only mode
    if (verificationMode !== 'file') {
      formData.append('certificate_hash', certificateHash);
    }
    
    // Only append file if not hash-only mode
    if (verificationMode !== 'hash') {
      formData.append('verification_file', file);
    }
    
    formData.append('payment_method', paymentMethod);
    formData.append('payment_digits', paymentDigits);
    formData.append('verification_mode', verificationMode);

    const response = await api.upload('/certificates/verify', formData, {
      onUploadProgress: onProgress
    });
    return response.data;
  },
  
  // Get verification result
  getVerificationResult: async (verificationId) => {
    const response = await api.get(`/verify/result/${verificationId}`);
    return response.data;
  },
  
  // Get verification history for verifier
  getVerificationHistory: async (verifierId, page = 1, limit = 10) => {
    const response = await api.get(`/verifiers/${verifierId}/history`, {
      params: { page, limit }
    });
    return response.data;
  },

  // Verifier (current user) stats
  getMyVerifierStats: async () => {
    const response = await api.get('/api/verifier/stats');
    return response.data;
  },

  // Verifier (current user) verifications
  getMyVerifications: async (limit = 50) => {
    const response = await api.get('/api/verifier/my-verifications', { params: { limit } });
    return response.data;
  },
  
  // Search certificates
  searchCertificates: async (searchParams) => {
    const response = await api.get('/certificates/search', {
      params: searchParams
    });
    return response.data;
  },
  
  // Get certificate statistics
  getCertificateStats: async (issuerId) => {
    const response = await api.get(`/certificates/stats/${issuerId}`);
    return response.data;
  },

  // Get recent activities
  getRecentActivities: async (limit = 10) => {
    const response = await api.get('/api/activities/recent', {
      params: { limit }
    });
    return response.data;
  },

  // Get activity statistics
  getActivityStats: async () => {
    const response = await api.get('/api/activities/stats');
    return response.data;
  }
};

export default certificateApi;
