import React, { useState, useEffect } from 'react';
import { useAuth } from '../../contexts/AuthContext';
import { completeApi } from '../../api';

const InstitutionDashboard = () => {
  const { user } = useAuth();
  const [institutions, setInstitutions] = useState([]);
  const [pendingRequests, setPendingRequests] = useState([]);
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedPeerModel, setSelectedPeerModel] = useState('hosted');

  useEffect(() => {
    if (user?.role === 'admin') {
      loadInstitutions();
      loadPendingRequests();
    }
  }, [user]);

  const loadInstitutions = async () => {
    try {
      // Mock data - replace with API call
      const mockInstitutions = [
        {
          id: 'org1',
          name: 'University of Technology',
          type: 'issuer',
          status: 'active',
          joinedDate: '2024-01-15',
          peerCount: 2,
          certificatesIssued: 150,
          peerModel: 'hosted',
          mspId: 'Org1MSP',
          anchorPeers: ['peer0.org1.certivert.com:7051']
        },
        {
          id: 'org2',
          name: 'LUCT',
          type: 'verifier',
          status: 'active',
          joinedDate: '2024-01-20',
          peerCount: 1,
          verifications: 45,
          peerModel: 'hosted',
          mspId: 'Org2MSP'
        },
        {
          id: 'org3',
          name: 'LP',
          type: 'verifier',
          status: 'pending',
          joinedDate: '2024-01-25',
          peerCount: 0,
          peerModel: 'byo'
        }
      ];
      setInstitutions(mockInstitutions);
    } catch (error) {
      console.error('Error loading institutions:', error);
    }
  };

  const loadPendingRequests = async () => {
    try {
      // Mock pending requests
      const mockRequests = [
        {
          id: 'req1',
          institutionName: 'National University',
          requestedRole: 'issuer',
          contactEmail: 'admin@nu.edu',
          contactPhone: '+1 (555) 123-4567',
          requestedAt: '2024-01-30 14:30',
          peerModel: 'hosted',
          status: 'pending',
          documents: ['business_license.pdf', 'accreditation.pdf']
        },
        {
          id: 'req2',
          institutionName: 'Digital College',
          requestedRole: 'verifier',
          contactEmail: 'hr@digitalcollege.edu',
          contactPhone: '+1 (555) 987-6543',
          requestedAt: '2024-01-29 11:20',
          peerModel: 'byo',
          status: 'pending',
          documents: ['accreditation.pdf']
        }
      ];
      setPendingRequests(mockRequests);
    } catch (error) {
      console.error('Error loading pending requests:', error);
    }
  };

  const handleApproveRequest = async (requestId) => {
    try {
      // Call backend to approve institution
      alert(`Approving institution request ${requestId}...`);
      
      // Update local state
      setPendingRequests(prev => prev.filter(req => req.id !== requestId));
      
      // Add to institutions
      const request = pendingRequests.find(req => req.id === requestId);
      if (request) {
        const newInstitution = {
          id: `org${institutions.length + 1}`,
          name: request.institutionName,
          type: request.requestedRole,
          status: 'active',
          joinedDate: new Date().toISOString().split('T')[0],
          peerCount: 0,
          peerModel: request.peerModel,
          mspId: `Org${institutions.length + 1}MSP`
        };
        setInstitutions(prev => [...prev, newInstitution]);
      }
      
      alert('Institution approved and added to network!');
    } catch (error) {
      console.error('Error approving request:', error);
      alert('Failed to approve request');
    }
  };

  const handleRejectRequest = (requestId) => {
    if (window.confirm('Are you sure you want to reject this institution request?')) {
      setPendingRequests(prev => prev.filter(req => req.id !== requestId));
      alert('Request rejected');
    }
  };

  const handleGenerateOnboardingPackage = async (institutionId) => {
    try {
      const institution = institutions.find(inst => inst.id === institutionId);
      
      // Generate onboarding package
      const packageData = {
        institutionId: institution.id,
        mspId: institution.mspId,
        peerModel: selectedPeerModel,
        timestamp: new Date().toISOString()
      };
      
      // Create downloadable package
      const blob = new Blob([JSON.stringify(packageData, null, 2)], {
        type: 'application/json'
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `certivert-onboarding-${institution.id}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      
      alert(`Onboarding package generated for ${institution.name}`);
    } catch (error) {
      console.error('Error generating package:', error);
    }
  };

  const handleUpdateChannelConfig = async (institutionId) => {
    try {
      // Call backend to update Fabric channel config
      alert(`Updating channel configuration for institution ${institutionId}...`);
      
      // Simulate Fabric config update
      setTimeout(() => {
        alert('✅ Channel configuration updated successfully!\n\n- MSP added to channel\n- Anchor peers configured\n- Chaincode endorsement policy updated');
      }, 2000);
    } catch (error) {
      console.error('Error updating channel config:', error);
    }
  };

  return (
    <div className="institution-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <h1>Institution Management</h1>
        <p>Manage organizations in the CertiVert blockchain network</p>
        <div className="network-status">
          <span className="status-label">Fabric Network:</span>
          <span className="status-value active">🟢 Online</span>
          <span className="status-label">Channel:</span>
          <span className="status-value">certificates-channel</span>
          <span className="status-label">Chaincode:</span>
          <span className="status-value">certificate-cc:v1.0</span>
        </div>
      </div>

      {/* Tabs */}
      <div className="management-tabs">
        <button 
          className={`tab ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          <span className="tab-icon">📊</span>
          <span>Network Overview</span>
        </button>
        <button 
          className={`tab ${activeTab === 'requests' ? 'active' : ''}`}
          onClick={() => setActiveTab('requests')}
        >
          <span className="tab-icon">📨</span>
          <span>Join Requests</span>
          {pendingRequests.length > 0 && (
            <span className="tab-badge">{pendingRequests.length}</span>
          )}
        </button>
        <button 
          className={`tab ${activeTab === 'institutions' ? 'active' : ''}`}
          onClick={() => setActiveTab('institutions')}
        >
          <span className="tab-icon">🏛️</span>
          <span>Institutions</span>
          <span className="tab-count">{institutions.length}</span>
        </button>
        <button 
          className={`tab ${activeTab === 'onboarding' ? 'active' : ''}`}
          onClick={() => setActiveTab('onboarding')}
        >
          <span className="tab-icon">⚙️</span>
          <span>Onboarding Tools</span>
        </button>
        <button 
          className={`tab ${activeTab === 'fabric' ? 'active' : ''}`}
          onClick={() => setActiveTab('fabric')}
        >
          <span className="tab-icon">⛓️</span>
          <span>Fabric Config</span>
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab === 'overview' && (
          <div className="overview-tab">
            <div className="network-stats">
              <div className="stat-card">
                <div className="stat-icon">🏛️</div>
                <div className="stat-content">
                  <div className="stat-value">{institutions.length}</div>
                  <div className="stat-label">Total Institutions</div>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">📄</div>
                <div className="stat-content">
                  <div className="stat-value">1,250</div>
                  <div className="stat-label">Certificates Issued</div>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">✅</div>
                <div className="stat-content">
                  <div className="stat-value">3,450</div>
                  <div className="stat-label">Verifications</div>
                </div>
              </div>
              <div className="stat-card">
                <div className="stat-icon">⚙️</div>
                <div className="stat-content">
                  <div className="stat-value">{institutions.filter(i => i.peerModel === 'hosted').length}</div>
                  <div className="stat-label">Hosted Peers</div>
                </div>
              </div>
            </div>

            <div className="network-visualization">
              <h3>Network Topology</h3>
              <div className="fabric-topology">
                <div className="orderer-node">
                  <div className="node-icon">🔄</div>
                  <div className="node-label">Orderer</div>
                  <div className="node-status">Single</div>
                </div>
                
                <div className="channel-line"></div>
                
                <div className="orgs-container">
                  {institutions.map((org, index) => (
                    <div key={org.id} className={`org-node ${org.type}`}>
                      <div className="org-header">
                        <div className="org-icon">{org.type === 'issuer' ? '🏛️' : '🔍'}</div>
                        <div className="org-name">{org.name}</div>
                        <div className={`org-status ${org.status}`}>{org.status}</div>
                      </div>
                      <div className="org-details">
                        <div className="detail">
                          <span>MSP:</span>
                          <code>{org.mspId}</code>
                        </div>
                        <div className="detail">
                          <span>Peers:</span>
                          <span>{org.peerCount}</span>
                        </div>
                        <div className="detail">
                          <span>Model:</span>
                          <span className={`model ${org.peerModel}`}>
                            {org.peerModel === 'hosted' ? 'Hosted' : 'BYO'}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="quick-actions">
              <h3>Quick Actions</h3>
              <div className="action-buttons">
                <button className="btn btn-primary" onClick={() => setActiveTab('requests')}>
                  Review Join Requests
                </button>
                <button className="btn btn-secondary" onClick={() => setActiveTab('onboarding')}>
                  Generate Onboarding Package
                </button>
                <button className="btn btn-secondary" onClick={() => setActiveTab('fabric')}>
                  Update Channel Config
                </button>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'requests' && (
          <div className="requests-tab">
            <div className="section-header">
              <h2>Pending Join Requests</h2>
              <p>Approve or reject institutions requesting to join the network</p>
            </div>

            {pendingRequests.length === 0 ? (
              <div className="empty-state">
                <div className="empty-icon">✅</div>
                <h3>No Pending Requests</h3>
                <p>All institution requests have been processed</p>
              </div>
            ) : (
              <div className="requests-list">
                {pendingRequests.map(request => (
                  <div key={request.id} className="request-card">
                    <div className="request-header">
                      <div className="request-title">
                        <h3>{request.institutionName}</h3>
                        <span className="request-role">{request.requestedRole}</span>
                      </div>
                      <div className="request-meta">
                        <span className="request-date">{request.requestedAt}</span>
                        <span className={`peer-model ${request.peerModel}`}>
                          {request.peerModel === 'hosted' ? 'Hosted Peer' : 'BYO Peer'}
                        </span>
                      </div>
                    </div>
                    
                    <div className="request-details">
                      <div className="detail-group">
                        <div className="detail">
                          <span className="label">Contact Email:</span>
                          <span className="value">{request.contactEmail}</span>
                        </div>
                        <div className="detail">
                          <span className="label">Contact Phone:</span>
                          <span className="value">{request.contactPhone}</span>
                        </div>
                      </div>
                      
                      <div className="documents">
                        <h4>Submitted Documents:</h4>
                        <div className="document-list">
                          {request.documents.map((doc, index) => (
                            <span key={index} className="document-badge">
                              📄 {doc}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                    
                    <div className="request-actions">
                      <button 
                        className="btn btn-success"
                        onClick={() => handleApproveRequest(request.id)}
                      >
                        ✅ Approve & Onboard
                      </button>
                      <button 
                        className="btn btn-danger"
                        onClick={() => handleRejectRequest(request.id)}
                      >
                        ❌ Reject
                      </button>
                      <button className="btn btn-outline">
                        📋 View Details
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}

            <div className="onboarding-guide">
              <h3>Onboarding Process</h3>
              <div className="process-steps">
                <div className="step">
                  <div className="step-number">1</div>
                  <div className="step-content">
                    <h4>Request Submission</h4>
                    <p>Institution submits join request with documents</p>
                  </div>
                </div>
                <div className="step">
                  <div className="step-number">2</div>
                  <div className="step-content">
                    <h4>Admin Review</h4>
                    <p>Network admin reviews and verifies institution</p>
                  </div>
                </div>
                <div className="step">
                  <div className="step-number">3</div>
                  <div className="step-content">
                    <h4>MSP Generation</h4>
                    <p>System generates MSP certificates for new org</p>
                  </div>
                </div>
                <div className="step">
                  <div className="step-number">4</div>
                  <div className="step-content">
                    <h4>Channel Update</h4>
                    <p>Channel config updated to include new organization</p>
                  </div>
                </div>
                <div className="step">
                  <div className="step-number">5</div>
                  <div className="step-content">
                    <h4>Peer Deployment</h4>
                    <p>Institution deploys peer (hosted or BYO)</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'institutions' && (
          <div className="institutions-tab">
            <div className="institutions-header">
              <h2>Network Institutions</h2>
              <div className="filters">
                <select defaultValue="">
                  <option value="">All Types</option>
                  <option value="issuer">Issuers</option>
                  <option value="verifier">Verifiers</option>
                </select>
                <select defaultValue="">
                  <option value="">All Status</option>
                  <option value="active">Active</option>
                  <option value="pending">Pending</option>
                  <option value="suspended">Suspended</option>
                </select>
                <input type="text" placeholder="Search institutions..." />
              </div>
            </div>

            <div className="institutions-table">
              <div className="table-header">
                <div className="table-cell">Institution</div>
                <div className="table-cell">Type</div>
                <div className="table-cell">MSP ID</div>
                <div className="table-cell">Peer Model</div>
                <div className="table-cell">Status</div>
                <div className="table-cell">Joined</div>
                <div className="table-cell">Actions</div>
              </div>

              {institutions.map(inst => (
                <div key={inst.id} className="table-row">
                  <div className="table-cell">
                    <div className="institution-info">
                      <div className="institution-avatar">
                        {inst.name.charAt(0)}
                      </div>
                      <div className="institution-details">
                        <div className="institution-name">{inst.name}</div>
                        <div className="institution-id">ID: {inst.id}</div>
                      </div>
                    </div>
                  </div>
                  <div className="table-cell">
                    <span className={`type-badge ${inst.type}`}>
                      {inst.type === 'issuer' ? '🏛️ Issuer' : '🔍 Verifier'}
                    </span>
                  </div>
                  <div className="table-cell">
                    <code className="msp-id">{inst.mspId}</code>
                  </div>
                  <div className="table-cell">
                    <span className={`peer-model ${inst.peerModel}`}>
                      {inst.peerModel === 'hosted' ? '🏠 Hosted' : '🖥️ BYO'}
                    </span>
                  </div>
                  <div className="table-cell">
                    <span className={`status-badge ${inst.status}`}>
                      {inst.status}
                    </span>
                  </div>
                  <div className="table-cell">
                    {inst.joinedDate}
                  </div>
                  <div className="table-cell">
                    <div className="institution-actions">
                      <button 
                        className="btn-icon"
                        title="View Details"
                        onClick={() => alert(`Details for ${inst.name}`)}
                      >
                        👁️
                      </button>
                      <button 
                        className="btn-icon"
                        title="Generate Package"
                        onClick={() => handleGenerateOnboardingPackage(inst.id)}
                      >
                        📦
                      </button>
                      <button 
                        className="btn-icon"
                        title="Update Config"
                        onClick={() => handleUpdateChannelConfig(inst.id)}
                      >
                        ⚙️
                      </button>
                      {inst.status === 'active' && (
                        <button 
                          className="btn-icon danger"
                          title="Suspend"
                          onClick={() => alert(`Suspend ${inst.name}`)}
                        >
                          ⏸️
                        </button>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'onboarding' && (
          <div className="onboarding-tab">
            <div className="onboarding-wizard">
              <div className="wizard-header">
                <h2>Institution Onboarding Wizard</h2>
                <p>Step-by-step process to onboard new institutions</p>
              </div>

              <div className="wizard-steps">
                <div className="step active">
                  <div className="step-header">
                    <div className="step-number">1</div>
                    <h3>Select Peer Model</h3>
                  </div>
                  <div className="step-content">
                    <div className="peer-model-selector">
                      <div 
                        className={`model-option ${selectedPeerModel === 'hosted' ? 'selected' : ''}`}
                        onClick={() => setSelectedPeerModel('hosted')}
                      >
                        <div className="model-icon">🏠</div>
                        <div className="model-content">
                          <h4>Hosted Peer Model</h4>
                          <p>We host the peer for the institution</p>
                          <ul className="model-features">
                            <li>✅ Faster onboarding</li>
                            <li>✅ No infrastructure management</li>
                            <li>✅ Lower operational cost</li>
                            <li>✅ Automatic updates</li>
                          </ul>
                        </div>
                      </div>
                      
                      <div 
                        className={`model-option ${selectedPeerModel === 'byo' ? 'selected' : ''}`}
                        onClick={() => setSelectedPeerModel('byo')}
                      >
                        <div className="model-icon">🖥️</div>
                        <div className="model-content">
                          <h4>Bring Your Own (BYO) Peer</h4>
                          <p>Institution runs their own peer</p>
                          <ul className="model-features">
                            <li>✅ More decentralization</li>
                            <li>✅ Stronger trust model</li>
                            <li>✅ Direct ledger access</li>
                            <li>✅ Full control</li>
                          </ul>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="step">
                  <div className="step-header">
                    <div className="step-number">2</div>
                    <h3>Generate MSP & Configuration</h3>
                  </div>
                  <div className="step-content">
                    <div className="config-generator">
                      <div className="form-group">
                        <label>Institution Name</label>
                        <input type="text" placeholder="Enter institution name" />
                      </div>
                      <div className="form-group">
                        <label>MSP ID (Auto-generated)</label>
                        <input 
                          type="text" 
                          value={`Org${institutions.length + 1}MSP`}
                          readOnly 
                        />
                      </div>
                      <div className="form-group">
                        <label>Organization Domain</label>
                        <input type="text" placeholder="org.example.com" />
                      </div>
                      <div className="form-group">
                        <label>Peer Count</label>
                        <input 
                          type="number" 
                          min="1" 
                          max="5" 
                          defaultValue={selectedPeerModel === 'hosted' ? 1 : 2}
                        />
                      </div>
                    </div>
                  </div>
                </div>

                <div className="step">
                  <div className="step-header">
                    <div className="step-number">3</div>
                    <h3>Generate Onboarding Package</h3>
                  </div>
                  <div className="step-content">
                    <div className="package-preview">
                      <h4>Package Contents:</h4>
                      <ul className="package-items">
                        <li>📄 MSP certificates (admincerts, cacerts, tlscacerts)</li>
                        <li>🔧 Connection profile (connection-org.yaml)</li>
                        <li>📋 Onboarding instructions (README.md)</li>
                        <li>⚙️ Peer deployment scripts (Docker Compose)</li>
                        <li>🔐 TLS certificates</li>
                        <li>📊 Network configuration</li>
                      </ul>
                      
                      <div className="package-actions">
                        <button className="btn btn-primary btn-lg">
                          🚀 Generate Complete Package
                        </button>
                        <button className="btn btn-outline">
                          📋 Generate MSP Only
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'fabric' && (
          <div className="fabric-tab">
            <div className="fabric-config">
              <div className="config-header">
                <h2>Hyperledger Fabric Configuration</h2>
                <p>Manage blockchain network configuration</p>
              </div>

              <div className="config-sections">
                <div className="config-section">
                  <h3>Channel Configuration</h3>
                  <div className="config-card">
                    <div className="config-info">
                      <div className="info-row">
                        <span className="label">Channel Name:</span>
                        <span className="value">certificates-channel</span>
                      </div>
                      <div className="info-row">
                        <span className="label">Consensus:</span>
                        <span className="value">Raft (3 orderers)</span>
                      </div>
                      <div className="info-row">
                        <span className="label">Block Size:</span>
                        <span className="value">2MB</span>
                      </div>
                      <div className="info-row">
                        <span className="label">Organizations:</span>
                        <span className="value">{institutions.length} orgs</span>
                      </div>
                    </div>
                    <div className="config-actions">
                      <button className="btn btn-primary">
                        Update Channel Config
                      </button>
                      <button className="btn btn-outline">
                        View Config Block
                      </button>
                    </div>
                  </div>
                </div>

                <div className="config-section">
                  <h3>Chaincode Management</h3>
                  <div className="config-card">
                    <div className="config-info">
                      <div className="info-row">
                        <span className="label">Chaincode Name:</span>
                        <span className="value">certificate-cc</span>
                      </div>
                      <div className="info-row">
                        <span className="label">Version:</span>
                        <span className="value">v1.0</span>
                      </div>
                      <div className="info-row">
                        <span className="label">Endorsement Policy:</span>
                        <span className="value">MAJORITY of issuers</span>
                      </div>
                      <div className="info-row">
                        <span className="label">Installed On:</span>
                        <span className="value">All peers</span>
                      </div>
                    </div>
                    <div className="config-actions">
                      <button className="btn btn-primary">
                        Upgrade Chaincode
                      </button>
                      <button className="btn btn-outline">
                        Query Chaincode
                      </button>
                    </div>
                  </div>
                </div>

                <div className="config-section">
                  <h3>Organization MSPs</h3>
                  <div className="msp-list">
                    {institutions.map(org => (
                      <div key={org.id} className="msp-card">
                        <div className="msp-header">
                          <div className="msp-name">{org.mspId}</div>
                          <span className={`msp-status ${org.status}`}>
                            {org.status}
                          </span>
                        </div>
                        <div className="msp-details">
                          <div className="detail">
                            <span>Organization:</span>
                            <span>{org.name}</span>
                          </div>
                          <div className="detail">
                            <span>Admin Certs:</span>
                            <span>1 certificate</span>
                          </div>
                          <div className="detail">
                            <span>CA Certificates:</span>
                            <span>2 certificates</span>
                          </div>
                          <div className="detail">
                            <span>TLS CA Certificates:</span>
                            <span>1 certificate</span>
                          </div>
                        </div>
                        <div className="msp-actions">
                          <button className="btn-icon">📋</button>
                          <button className="btn-icon">⬇️</button>
                          <button className="btn-icon">🔄</button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="fabric-actions">
                <h3>Network Operations</h3>
                <div className="action-grid">
                  <button className="action-card">
                    <div className="action-icon">🔍</div>
                    <div className="action-content">
                      <h4>Query Ledger</h4>
                      <p>Query blockchain state</p>
                    </div>
                  </button>
                  <button className="action-card">
                    <div className="action-icon">📊</div>
                    <div className="action-content">
                      <h4>Network Health</h4>
                      <p>Check peer/orderer status</p>
                    </div>
                  </button>
                  <button className="action-card">
                    <div className="action-icon">⚙️</div>
                    <div className="action-content">
                      <h4>Update Config</h4>
                      <p>Modify network parameters</p>
                    </div>
                  </button>
                  <button className="action-card">
                    <div className="action-icon">📜</div>
                    <div className="action-content">
                      <h4>View Logs</h4>
                      <p>Access Fabric logs</p>
                    </div>
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default InstitutionDashboard;
