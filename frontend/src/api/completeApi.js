// Complete API Integration for CertiVert
import api from './axiosConfig';

// Removed mock data - using real API responses only

export const completeApi = {
  // Certificate Management
  certificates: {
    // Upload certificate file
    upload: async (formData) => {
      try {
        const response = await api.upload('/certificates/upload', formData);
        return response.data;
      } catch (error) {
        console.error('Upload error:', error);
        throw error;
      }
    },

    // Extract data from uploaded certificate
    extract: async (fileId) => {
      try {
        const response = await api.post(`/certificates/${fileId}/extract`);
        return response.data;
      } catch (error) {
        console.error('Extraction error:', error);
        throw error;
      }
    },

    // Issue new certificate
    create: async (certificateData) => {
      try {
        const response = await api.post('/certificates/create', certificateData);
        return response.data;
      } catch (error) {
        console.error('Create certificate error:', error);
        throw error;
      }
    },

    // Get certificates by issuer
    getByIssuer: async (issuerId, page = 1, limit = 10) => {
      try {
        const response = await api.get(`/issuers/${issuerId}/certificates`, {
          params: { page, limit }
        });
        return response.data;
      } catch (error) {
        console.error('Get certificates error:', error);
        // Return empty result if no certificates
        return {
          certificates: [],
          pagination: {
            page,
            limit,
            total: 0,
            pages: 0
          }
        };
      }
    },

    // Search certificates
    search: async (searchParams) => {
      try {
        const response = await api.get('/certificates/search', {
          params: searchParams
        });
        return response.data;
      } catch (error) {
        console.error('Search error:', error);
        // Return empty search results
        return {
          results: [],
          total: 0
        };
      }
    },

    // Get certificate by ID
    getById: async (certificateId) => {
      try {
        const response = await api.get(`/certificates/${certificateId}`);
        return response.data;
      } catch (error) {
        console.error('Get certificate error:', error);
        throw error;
      }
    },

    // Revoke certificate
    revoke: async (certificateId, reason) => {
      try {
        const response = await api.post(`/certificates/${certificateId}/revoke`, { reason });
        return response.data;
      } catch (error) {
        console.error('Revoke error:', error);
        throw error;
      }
    }
  },

  // Verification System
  verification: {
    // Upload for verification
    uploadForVerification: async (formData) => {
      try {
        const response = await api.upload('/verify/upload', formData);
        return response.data;
      } catch (error) {
        console.error('Verification upload error:', error);
        throw error;
      }
    },

    // Process verification
    verify: async (verificationData) => {
      try {
        const response = await api.post('/verify/process', verificationData);
        return response.data;
      } catch (error) {
        console.error('Verification error:', error);
        throw error;
      }
    },

    // Get verification result
    getResult: async (verificationId) => {
      try {
        const response = await api.get(`/verify/result/${verificationId}`);
        return response.data;
      } catch (error) {
        console.error('Get result error:', error);
        // Return empty result
        return {
          verificationId,
          status: 'not_found',
          result: null
        };
      }
    },

    // Get verification history
    getHistory: async (verifierId, page = 1, limit = 10) => {
      try {
        const response = await api.get(`/verifiers/${verifierId}/history`, {
          params: { page, limit }
        });
        return response.data;
      } catch (error) {
        console.error('History error:', error);
        // Return empty history
        return {
          verifications: [],
          pagination: {
            page,
            limit,
            total: 0,
            pages: 0
          }
        };
      }
    },

    // Batch verification
    batchVerify: async (files) => {
      try {
        const formData = new FormData();
        files.forEach(file => {
          formData.append('certificates', file);
        });
        
        const response = await api.upload('/verify/batch', formData);
        return response.data;
      } catch (error) {
        console.error('Batch verification error:', error);
        // Return empty batch result
        return {
          success: false,
          message: 'Batch verification failed',
          results: [],
          total: 0,
          valid: 0,
          invalid: 0
        };
      }
    }
  },

  // Invitation System
  invitations: {
    // Generate invitation
    generate: async (invitationData) => {
      try {
        const response = await api.post('/invitations/generate', invitationData);
        return response.data;
      } catch (error) {
        console.error('Generate invitation error:', error);
        throw error;
      }
    },

    // Validate invitation
    validate: async (token) => {
      try {
        const response = await api.get(`/invitations/validate/${token}`);
        return response.data;
      } catch (error) {
        console.error('Validate invitation error:', error);
        throw error;
      }
    },

    // Get invitation stats
    getStats: async (userId) => {
      try {
        const response = await api.get(`/users/${userId}/invitations/stats`);
        return response.data;
      } catch (error) {
        console.error('Invitation stats error:', error);
        // Return empty stats
        return {
          invitedCount: 0,
          acceptedCount: 0,
          pendingCount: 0,
          recentInvitations: []
        };
      }
    },

    // Get all invitations
    getAll: async (userId) => {
      try {
        const response = await api.get(`/users/${userId}/invitations`);
        return response.data;
      } catch (error) {
        console.error('Get invitations error:', error);
        // Return empty invitations
        return {
          invitations: [],
          total: 0
        };
      }
    }
  },

  // User Management
  users: {
    // Get user profile
    getProfile: async (userId) => {
      try {
        const response = await api.get(`/users/${userId}/profile`);
        return response.data;
      } catch (error) {
        console.error('Get profile error:', error);
        throw error;
      }
    },

    // Update profile
    updateProfile: async (userId, profileData) => {
      try {
        const response = await api.put(`/users/${userId}/profile`, profileData);
        return response.data;
      } catch (error) {
        console.error('Update profile error:', error);
        throw error;
      }
    },

    // Get user activity
    getActivity: async (userId, page = 1, limit = 20) => {
      try {
        const response = await api.get(`/users/${userId}/activity`, {
          params: { page, limit }
        });
        return response.data;
      } catch (error) {
        console.error('Activity error:', error);
        // Return empty activity
        return {
          activities: [],
          pagination: {
            page,
            limit,
            total: 0,
            pages: 0
          }
        };
      }
    }
  },

  // Analytics
  analytics: {
    // Get system stats
    getSystemStats: async () => {
      try {
        const response = await api.get('/analytics/system-stats');
        return response.data;
      } catch (error) {
        console.error('System stats error:', error);
        // Return zero stats
        return {
          totalCertificates: 0,
          totalVerifications: 0,
          totalUsers: 0,
          activeUsers: 0,
          verificationSuccessRate: 0,
          averageVerificationTime: 0
        };
      }
    },

    // Get issuer stats
    getIssuerStats: async (issuerId) => {
      try {
        const response = await api.get(`/analytics/issuers/${issuerId}/stats`);
        return response.data;
      } catch (error) {
        console.error('Issuer stats error:', error);
        // Return zero stats
        return {
          certificatesIssued: 0,
          certificatesVerified: 0,
          verificationRate: 0,
          averageGrade: 'N/A',
          topCourses: [],
          monthlyIssuance: Array.from({length: 12}, (_, i) => ({
            month: `2024-${String(i+1).padStart(2, '0')}`,
            count: 0
          }))
        };
      }
    },

    // Get verifier stats
    getVerifierStats: async (verifierId) => {
      try {
        const response = await api.get(`/analytics/verifiers/${verifierId}/stats`);
        return response.data;
      } catch (error) {
        console.error('Verifier stats error:', error);
        // Return zero stats
        return {
          totalVerifications: 0,
          validVerifications: 0,
          invalidVerifications: 0,
          successRate: 0,
          creditsSpent: 0,
          creditsRemaining: 0,
          averageCost: 0,
          monthlyActivity: Array.from({length: 12}, (_, i) => ({
            month: `2024-${String(i+1).padStart(2, '0')}`,
            count: 0
          }))
        };
      }
    }
  },

  // Blockchain
  blockchain: {
    // Verify transaction
    verifyTransaction: async (transactionId) => {
      try {
        const response = await api.get(`/blockchain/transactions/${transactionId}/verify`);
        return response.data;
      } catch (error) {
        console.error('Verify transaction error:', error);
        throw error;
      }
    },

    // Get certificate proof
    getCertificateProof: async (certificateId) => {
      try {
        const response = await api.get(`/blockchain/certificates/${certificateId}/proof`);
        return response.data;
      } catch (error) {
        console.error('Get proof error:', error);
        throw error;
      }
    },

    // Get network status
    getNetworkStatus: async () => {
      try {
        const response = await api.get('/blockchain/network/status');
        return response.data;
      } catch (error) {
        console.error('Network status error:', error);
        throw error;
      }
    }
  }
};

export default completeApi;
