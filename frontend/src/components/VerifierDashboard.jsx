import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './VerifierDashboard.css';

const VerifierDashboard = () => {
  const [user, setUser] = useState(null);
  const [verifierCredential, setVerifierCredential] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [auditLogs, setAuditLogs] = useState([]);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('token');
    const userData = localStorage.getItem('user');
    const credentialData = localStorage.getItem('verifier_credential');

    if (!token || !userData || !credentialData) {
      navigate('/verifier/login');
      return;
    }

    try {
      setUser(JSON.parse(userData));
      setVerifierCredential(JSON.parse(credentialData));
      fetchAuditLogs();
    } catch (error) {
      console.error('Error parsing stored data:', error);
      navigate('/verifier/login');
    } finally {
      setLoading(false);
    }
  }, [navigate]);

  const fetchAuditLogs = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/verifier/audit-log?limit=10', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const logs = await response.json();
        setAuditLogs(logs);
      }
    } catch (error) {
      console.error('Error fetching audit logs:', error);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    localStorage.removeItem('verifier_credential');
    navigate('/verifier/login');
  };

  const handleBlockchainRegistration = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/verifier/blockchain/register', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        alert(`Successfully registered on blockchain! TX ID: ${data.blockchain_tx_id}`);
        // Refresh credential data
        setVerifierCredential(prev => ({
          ...prev,
          blockchain_registered: true,
          blockchain_tx_id: data.blockchain_tx_id
        }));
      } else {
        const error = await response.json();
        alert(error.detail || 'Failed to register on blockchain');
      }
    } catch (error) {
      console.error('Blockchain registration error:', error);
      alert('Network error. Please try again.');
    }
  };

  if (loading) {
    return (
      <div className="verifier-dashboard-loading">
        <div className="loading-spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  if (!user || !verifierCredential) {
    return null;
  }

  return (
    <div className="verifier-dashboard">
      <header className="dashboard-header">
        <div className="header-content">
          <div className="header-left">
            <h1>Verifier Dashboard</h1>
            <p>Welcome back, {user.username}</p>
          </div>
          <div className="header-right">
            <div className="credential-status">
              <span className={`status-badge ${verifierCredential.accreditation_status}`}>
                {verifierCredential.accreditation_status.toUpperCase()}
              </span>
              {verifierCredential.blockchain_registered && (
                <span className="blockchain-badge">✓ Blockchain</span>
              )}
            </div>
            <button onClick={handleLogout} className="logout-btn">
              Logout
            </button>
          </div>
        </div>
      </header>

      <div className="dashboard-content">
        <nav className="dashboard-nav">
          <button
            className={`nav-btn ${activeTab === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveTab('overview')}
          >
            Overview
          </button>
          <button
            className={`nav-btn ${activeTab === 'profile' ? 'active' : ''}`}
            onClick={() => setActiveTab('profile')}
          >
            Profile
          </button>
          <button
            className={`nav-btn ${activeTab === 'blockchain' ? 'active' : ''}`}
            onClick={() => setActiveTab('blockchain')}
          >
            Blockchain
          </button>
          <button
            className={`nav-btn ${activeTab === 'audit' ? 'active' : ''}`}
            onClick={() => setActiveTab('audit')}
          >
            Audit Log
          </button>
        </nav>

        <main className="dashboard-main">
          {activeTab === 'overview' && (
            <div className="tab-content overview-tab">
              <h2>Verifier Overview</h2>
              
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-icon">📋</div>
                  <div className="stat-content">
                    <h3>{verifierCredential.verification_count}</h3>
                    <p>Total Verifications</p>
                  </div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-icon">⭐</div>
                  <div className="stat-content">
                    <h3>{verifierCredential.reputation_score.toFixed(1)}</h3>
                    <p>Reputation Score</p>
                  </div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-icon">🔍</div>
                  <div className="stat-content">
                    <h3>{verifierCredential.accreditation_status}</h3>
                    <p>Accreditation Status</p>
                  </div>
                </div>
                
                <div className="stat-card">
                  <div className="stat-icon">🔗</div>
                  <div className="stat-content">
                    <h3>{verifierCredential.blockchain_registered ? 'Yes' : 'No'}</h3>
                    <p>Blockchain Registered</p>
                  </div>
                </div>
              </div>

              <div className="quick-actions">
                <h3>Quick Actions</h3>
                <div className="action-buttons">
                  <button 
                    className="action-btn primary"
                    onClick={() => navigate('/certificates/verify')}
                  >
                    Verify Certificate
                  </button>
                  <button 
                    className="action-btn secondary"
                    onClick={() => setActiveTab('blockchain')}
                    disabled={verifierCredential.blockchain_registered}
                  >
                    {verifierCredential.blockchain_registered ? 'Blockchain Registered' : 'Register on Blockchain'}
                  </button>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'profile' && (
            <div className="tab-content profile-tab">
              <h2>Verifier Profile</h2>
              
              <div className="profile-info">
                <div className="info-section">
                  <h3>Account Information</h3>
                  <div className="info-grid">
                    <div className="info-item">
                      <label>Username</label>
                      <span>{user.username}</span>
                    </div>
                    <div className="info-item">
                      <label>Email</label>
                      <span>{user.email}</span>
                    </div>
                    <div className="info-item">
                      <label>Credential ID</label>
                      <span>{verifierCredential.credential_id}</span>
                    </div>
                  </div>
                </div>

                <div className="info-section">
                  <h3>Professional Information</h3>
                  <div className="info-grid">
                    <div className="info-item">
                      <label>License Number</label>
                      <span>{verifierCredential.license_number || 'Not provided'}</span>
                    </div>
                    <div className="info-item">
                      <label>Specialization</label>
                      <span>{verifierCredential.specialization || 'Not specified'}</span>
                    </div>
                    <div className="info-item">
                      <label>Qualification Level</label>
                      <span>{verifierCredential.qualification_level || 'Not specified'}</span>
                    </div>
                    <div className="info-item">
                      <label>Years of Experience</label>
                      <span>{verifierCredential.years_experience}</span>
                    </div>
                    <div className="info-item">
                      <label>Institution</label>
                      <span>{verifierCredential.institution_affiliation || 'Not specified'}</span>
                    </div>
                  </div>
                </div>

                <div className="info-section">
                  <h3>Status Information</h3>
                  <div className="info-grid">
                    <div className="info-item">
                      <label>Accreditation Status</label>
                      <span className={`status-text ${verifierCredential.accreditation_status}`}>
                        {verifierCredential.accreditation_status}
                      </span>
                    </div>
                    <div className="info-item">
                      <label>Account Status</label>
                      <span className={verifierCredential.is_active ? 'status-active' : 'status-inactive'}>
                        {verifierCredential.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </div>
                    <div className="info-item">
                      <label>Reputation Score</label>
                      <span>{verifierCredential.reputation_score.toFixed(1)}/100</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'blockchain' && (
            <div className="tab-content blockchain-tab">
              <h2>Blockchain Integration</h2>
              
              <div className="blockchain-status">
                <div className="status-card">
                  <h3>Registration Status</h3>
                  <div className="status-indicator">
                    <div className={`indicator ${verifierCredential.blockchain_registered ? 'registered' : 'not-registered'}`}></div>
                    <span>{verifierCredential.blockchain_registered ? 'Registered' : 'Not Registered'}</span>
                  </div>
                  
                  {verifierCredential.blockchain_registered ? (
                    <div className="blockchain-info">
                      <p><strong>Transaction ID:</strong> {verifierCredential.blockchain_tx_id || 'N/A'}</p>
                      <p><strong>Network:</strong> {verifierCredential.blockchain_network || 'N/A'}</p>
                      <p><strong>Verifier ID:</strong> {verifierCredential.blockchain_verifier_id || 'N/A'}</p>
                    </div>
                  ) : (
                    <div className="blockchain-actions">
                      <p>Register your verifier credentials on the blockchain to enable immutable verification records.</p>
                      <button 
                        className="blockchain-register-btn"
                        onClick={handleBlockchainRegistration}
                      >
                        Register on Blockchain
                      </button>
                    </div>
                  )}
                </div>

                <div className="benefits-card">
                  <h3>Blockchain Benefits</h3>
                  <ul>
                    <li>Immutable verification records</li>
                    <li>Enhanced trust and transparency</li>
                    <li>Decentralized credential storage</li>
                    <li>Tamper-proof audit trails</li>
                    <li>Cross-platform verification</li>
                  </ul>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'audit' && (
            <div className="tab-content audit-tab">
              <h2>Audit Log</h2>
              
              <div className="audit-logs">
                {auditLogs.length > 0 ? (
                  <div className="logs-table">
                    <div className="table-header">
                      <div>Activity</div>
                      <div>Action</div>
                      <div>Status</div>
                      <div>Date</div>
                    </div>
                    {auditLogs.map((log) => (
                      <div key={log.id} className="table-row">
                        <div className="activity-type">{log.activity_type}</div>
                        <div className="action">{log.action}</div>
                        <div className={`status ${log.status}`}>{log.status}</div>
                        <div className="date">
                          {new Date(log.created_at).toLocaleString()}
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="no-logs">
                    <p>No audit logs available.</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default VerifierDashboard;
