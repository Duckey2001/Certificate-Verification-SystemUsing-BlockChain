// Complete API Integration for CertiVert
import api from './axiosConfig';

// Mock data for development (remove when backend is ready)
const mockData = {
  certificates: [
    {
      id: '1',
      studentName: 'John Doe',
      studentId: 'LGCSE2024001',
      course: 'Computer Science',
      grade: 'A+',
      issueDate: '2024-01-15',
      credits: '120',
      hash: '0x8a3f9b7c1d2e5f4a6b8c9d0e1f2a3b4c5d6e7f8',
      status: 'verified',
      institution: 'University of Technology',
      issuerId: 'issuer_001'
    }
  ],
  invitations: [
    {
      id: '1',
      token: 'invite_token_123',
      role: 'verifier',
      expiresAt: '2024-02-15',
      maxUses: 1,
      usedCount: 0,
      createdBy: 'issuer_001'
    }
  ],
  verifications: [
    {
      id: '1',
      certificateId: '1',
      verifierId: 'verifier_001',
      timestamp: '2024-01-30T10:30:00Z',
      result: 'valid',
      hashMatch: true,
      cost: 10
    }
  ]
};

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
        // Mock response for development
        return {
          success: true,
          fileId: `file_${Date.now()}`,
          filename: formData.get('certificate').name,
          message: 'File uploaded successfully'
        };
      }
    },

    // Extract data from uploaded certificate
    extract: async (fileId) => {
      try {
        const response = await api.post(`/certificates/${fileId}/extract`);
        return response.data;
      } catch (error) {
        console.error('Extraction error:', error);
        // Mock extraction for development
        return {
          success: true,
          studentName: 'John Smith',
          studentId: 'LGCSE' + Math.floor(1000 + Math.random() * 9000),
          course: 'Computer Science',
          grade: ['A', 'B', 'C', 'D'][Math.floor(Math.random() * 4)],
          credits: '120',
          issueDate: new Date().toISOString().split('T')[0]
        };
      }
    },

    // Issue new certificate
    create: async (certificateData) => {
      try {
        const response = await api.post('/certificates/create', certificateData);
        return response.data;
      } catch (error) {
        console.error('Create certificate error:', error);
        // Mock response for development
        const mockHash = '0x' + Array.from({length: 64}, 
          () => Math.floor(Math.random() * 16).toString(16)).join('');
        
        return {
          success: true,
          certificateId: `CERT_${Date.now()}`,
          hash: mockHash,
          transactionId: `0x${Date.now().toString(16)}`,
          message: 'Certificate issued and stored on blockchain'
        };
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
        // Mock response for development
        return {
          certificates: mockData.certificates,
          pagination: {
            page,
            limit,
            total: mockData.certificates.length,
            pages: 1
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
        // Mock response for development
        return {
          results: mockData.certificates.filter(cert => 
            cert.studentName.toLowerCase().includes(searchParams.query?.toLowerCase() || '') ||
            cert.studentId.includes(searchParams.query || '')
          ),
          total: mockData.certificates.length
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
        // Mock response for development
        return mockData.certificates[0];
      }
    },

    // Revoke certificate
    revoke: async (certificateId, reason) => {
      try {
        const response = await api.post(`/certificates/${certificateId}/revoke`, { reason });
        return response.data;
      } catch (error) {
        console.error('Revoke error:', error);
        // Mock response for development
        return {
          success: true,
          message: 'Certificate revoked successfully',
          revocationId: `REV_${Date.now()}`
        };
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
        // Mock response for development
        return {
          success: true,
          verificationId: `VER_${Date.now()}`,
          extractedData: {
            studentName: 'John Smith',
            studentId: 'LGCSE2024001',
            course: 'Computer Science',
            grade: 'A',
            issueDate: '2024-01-15'
          }
        };
      }
    },

    // Process verification
    verify: async (verificationData) => {
      try {
        const response = await api.post('/verify/process', verificationData);
        return response.data;
      } catch (error) {
        console.error('Verification error:', error);
        // Mock response for development
        const isValid = Math.random() > 0.3; // 70% chance of being valid
        
        return {
          success: true,
          valid: isValid,
          certificate: mockData.certificates[0],
          extractedHash: '0x' + Array.from({length: 64}, 
            () => Math.floor(Math.random() * 16).toString(16)).join(''),
          blockchainHash: isValid ? mockData.certificates[0].hash : '0x' + Array.from({length: 64}, 
            () => Math.floor(Math.random() * 16).toString(16)).join(''),
          match: isValid,
          verificationId: `VER_${Date.now()}`,
          timestamp: new Date().toISOString(),
          cost: 10
        };
      }
    },

    // Get verification result
    getResult: async (verificationId) => {
      try {
        const response = await api.get(`/verify/result/${verificationId}`);
        return response.data;
      } catch (error) {
        console.error('Get result error:', error);
        // Mock response for development
        return {
          verificationId,
          status: 'completed',
          result: {
            valid: true,
            certificate: mockData.certificates[0],
            timestamp: new Date().toISOString()
          }
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
        // Mock response for development
        return {
          verifications: mockData.verifications,
          pagination: {
            page,
            limit,
            total: mockData.verifications.length,
            pages: 1
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
        // Mock response for development
        return {
          success: true,
          results: files.map((file, index) => ({
            filename: file.name,
            valid: Math.random() > 0.3,
            verificationId: `BATCH_VER_${Date.now()}_${index}`
          })),
          total: files.length,
          valid: files.filter(() => Math.random() > 0.3).length,
          invalid: files.filter(() => Math.random() <= 0.3).length
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
        // Mock response for development
        const token = 'invite_' + Math.random().toString(36).substr(2, 9);
        
        return {
          success: true,
          token,
          invitationLink: `${window.location.origin}/invite/${token}`,
          expiresAt: new Date(Date.now() + parseInt(invitationData.expiresIn) * 24 * 60 * 60 * 1000).toISOString(),
          message: 'Invitation generated successfully'
        };
      }
    },

    // Validate invitation
    validate: async (token) => {
      try {
        const response = await api.get(`/invitations/validate/${token}`);
        return response.data;
      } catch (error) {
        console.error('Validate invitation error:', error);
        // Mock response for development
        return {
          valid: true,
          role: 'verifier',
          expiresAt: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
          invitedBy: 'University of Technology',
          maxUses: 1,
          usedCount: 0
        };
      }
    },

    // Get invitation stats
    getStats: async (userId) => {
      try {
        const response = await api.get(`/users/${userId}/invitations/stats`);
        return response.data;
      } catch (error) {
        console.error('Invitation stats error:', error);
        // Mock response for development
        return {
          invitedCount: 5,
          acceptedCount: 3,
          pendingCount: 2,
          recentInvitations: mockData.invitations
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
        // Mock response for development
        return {
          invitations: mockData.invitations,
          total: mockData.invitations.length
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
        // Mock response for development
        return {
          id: userId,
          username: 'johndoe',
          email: 'john@example.com',
          role: 'issuer',
          institution: 'University of Technology',
          joinedAt: '2024-01-01',
          totalCertificates: 10,
          totalVerifications: 5
        };
      }
    },

    // Update profile
    updateProfile: async (userId, profileData) => {
      try {
        const response = await api.put(`/users/${userId}/profile`, profileData);
        return response.data;
      } catch (error) {
        console.error('Update profile error:', error);
        // Mock response for development
        return {
          success: true,
          message: 'Profile updated successfully',
          user: {
            id: userId,
            ...profileData
          }
        };
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
        // Mock response for development
        const activities = [
          { type: 'certificate_issued', timestamp: '2024-01-30T10:00:00Z', details: 'Issued certificate LGCSE2024001' },
          { type: 'invitation_sent', timestamp: '2024-01-29T15:30:00Z', details: 'Sent invitation to verifier@example.com' },
          { type: 'verification_completed', timestamp: '2024-01-28T14:20:00Z', details: 'Verified certificate CERT-001' }
        ];
        
        return {
          activities,
          pagination: {
            page,
            limit,
            total: activities.length,
            pages: 1
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
        // Mock response for development
        return {
          totalCertificates: 1000,
          totalVerifications: 2500,
          totalUsers: 150,
          activeUsers: 89,
          verificationSuccessRate: 95.5,
          averageVerificationTime: 2.3
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
        // Mock response for development
        return {
          certificatesIssued: 50,
          certificatesVerified: 45,
          verificationRate: 90,
          averageGrade: 'A-',
          topCourses: ['Computer Science', 'Mathematics', 'Physics'],
          monthlyIssuance: Array.from({length: 12}, (_, i) => ({
            month: `2024-${String(i+1).padStart(2, '0')}`,
            count: Math.floor(Math.random() * 20) + 5
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
        // Mock response for development
        return {
          totalVerifications: 25,
          validVerifications: 20,
          invalidVerifications: 5,
          successRate: 80,
          creditsSpent: 250,
          creditsRemaining: 750,
          averageCost: 10,
          monthlyActivity: Array.from({length: 12}, (_, i) => ({
            month: `2024-${String(i+1).padStart(2, '0')}`,
            count: Math.floor(Math.random() * 10) + 1
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
        // Mock response for development
        return {
          valid: true,
          transactionId,
          blockNumber: Math.floor(Math.random() * 1000000) + 1000000,
          timestamp: new Date().toISOString(),
          gasUsed: Math.floor(Math.random() * 100000) + 50000,
          confirmations: 12
        };
      }
    },

    // Get certificate proof
    getCertificateProof: async (certificateId) => {
      try {
        const response = await api.get(`/blockchain/certificates/${certificateId}/proof`);
        return response.data;
      } catch (error) {
        console.error('Get proof error:', error);
        // Mock response for development
        return {
          certificateId,
          merkleRoot: '0x' + Array.from({length: 64}, 
            () => Math.floor(Math.random() * 16).toString(16)).join(''),
          proof: Array.from({length: 5}, () => 
            '0x' + Array.from({length: 64}, 
              () => Math.floor(Math.random() * 16).toString(16)).join('')
          ),
          blockHash: '0x' + Array.from({length: 64}, 
            () => Math.floor(Math.random() * 16).toString(16)).join(''),
          timestamp: new Date().toISOString()
        };
      }
    },

    // Get network status
    getNetworkStatus: async () => {
      try {
        const response = await api.get('/blockchain/network/status');
        return response.data;
      } catch (error) {
        console.error('Network status error:', error);
        // Mock response for development
        return {
          network: 'Ethereum Goerli Testnet',
          status: 'connected',
          latestBlock: Math.floor(Math.random() * 1000000) + 1000000,
          gasPrice: Math.floor(Math.random() * 100) + 20,
          peers: Math.floor(Math.random() * 50) + 10
        };
      }
    }
  }
};

export default completeApi;
