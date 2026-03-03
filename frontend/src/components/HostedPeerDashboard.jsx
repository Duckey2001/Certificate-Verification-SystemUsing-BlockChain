import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';

const HostedPeerDashboard = () => {
  const { user } = useAuth();
  const [peers, setPeers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [metrics, setMetrics] = useState({
    cpuUsage: 45,
    memoryUsage: 62,
    diskUsage: 28,
    networkThroughput: 125
  });

  useEffect(() => {
    loadPeers();
    loadMetrics();
  }, []);

  const loadPeers = async () => {
    // Mock data
    const mockPeers = [
      {
        id: 'peer0-org1',
        name: 'peer0.org1.certivert.com',
        organization: 'University of Technology',
        status: 'running',
        version: '2.5.0',
        port: 7051,
        tlsPort: 7053,
        chaincodes: ['certificate-cc:v1.0'],
        lastBlock: 1245,
        uptime: '15d 6h 32m',
        resources: {
          cpu: '2 cores',
          memory: '4GB',
          storage: '100GB'
        }
      },
      {
        id: 'peer0-org2',
        name: 'peer0.org2.certivert.com',
        organization: 'LUCT',
        status: 'running',
        version: '2.5.0',
        port: 9051,
        tlsPort: 9053,
        chaincodes: ['certificate-cc:v1.0'],
        lastBlock: 1245,
        uptime: '8d 12h 15m',
        resources: {
          cpu: '2 cores',
          memory: '4GB',
          storage: '100GB'
        }
      },
      {
        id: 'peer1-org1',
        name: 'peer1.org1.certivert.com',
        organization: 'University of Technology',
        status: 'stopped',
        version: '2.5.0',
        port: 7056,
        tlsPort: 7058,
        chaincodes: ['certificate-cc:v1.0'],
        lastBlock: 1245,
        uptime: '0d 0h 0m',
        resources: {
          cpu: '2 cores',
          memory: '4GB',
          storage: '100GB'
        }
      }
    ];
    setPeers(mockPeers);
    setLoading(false);
  };

  const loadMetrics = async () => {
    // Simulate metrics loading
    setTimeout(() => {
      setMetrics({
        cpuUsage: Math.floor(Math.random() * 100),
        memoryUsage: Math.floor(Math.random() * 100),
        diskUsage: Math.floor(Math.random() * 100),
        networkThroughput: Math.floor(Math.random() * 200)
      });
    }, 1000);
  };

  const handleStartPeer = (peerId) => {
    setPeers(prev => prev.map(peer => 
      peer.id === peerId ? { ...peer, status: 'running', uptime: '0d 0h 1m' } : peer
    ));
    alert(`Starting peer ${peerId}...`);
  };

  const handleStopPeer = (peerId) => {
    if (window.confirm('Are you sure you want to stop this peer?')) {
      setPeers(prev => prev.map(peer => 
        peer.id === peerId ? { ...peer, status: 'stopped', uptime: '0d 0h 0m' } : peer
      ));
      alert(`Peer ${peerId} stopped`);
    }
  };

  const handleRestartPeer = (peerId) => {
    setPeers(prev => prev.map(peer => 
      peer.id === peerId ? { ...peer, status: 'restarting', uptime: '0d 0h 0m' } : peer
    ));
    
    setTimeout(() => {
      setPeers(prev => prev.map(peer => 
        peer.id === peerId ? { ...peer, status: 'running', uptime: '0d 0h 0m' } : peer
      ));
    }, 3000);
    
    alert(`Restarting peer ${peerId}...`);
  };

  const handleDeployPeer = () => {
    const newPeer = {
      id: `peer${peers.length + 1}-org${peers.length + 1}`,
      name: `peer${peers.length}.org${peers.length + 1}.certivert.com`,
      organization: 'New Institution',
      status: 'deploying',
      version: '2.5.0',
      port: 8051 + (peers.length * 1000),
      tlsPort: 8053 + (peers.length * 1000),
      chaincodes: [],
      lastBlock: 0,
      uptime: '0d 0h 0m',
      resources: {
        cpu: '2 cores',
        memory: '4GB',
        storage: '100GB'
      }
    };
    
    setPeers(prev => [...prev, newPeer]);
    
    setTimeout(() => {
      setPeers(prev => prev.map(peer => 
        peer.id === newPeer.id ? { ...peer, status: 'running', uptime: '0d 0h 0m' } : peer
      ));
    }, 5000);
    
    alert('Deploying new peer...');
  };

  return (
    <div className="hosted-peer-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <h1>Hosted Peer Management</h1>
        <p>Manage blockchain peers for all institutions</p>
        <div className="header-actions">
          <button className="btn btn-primary" onClick={handleDeployPeer}>
            🚀 Deploy New Peer
          </button>
          <button className="btn btn-outline" onClick={loadMetrics}>
            🔄 Refresh Metrics
          </button>
        </div>
      </div>

      {/* Metrics */}
      <div className="metrics-section">
        <h2>Infrastructure Metrics</h2>
        <div className="metrics-grid">
          <div className="metric-card">
            <div className="metric-header">
              <div className="metric-icon">⚡</div>
              <h3>CPU Usage</h3>
            </div>
            <div className="metric-value">{metrics.cpuUsage}%</div>
            <div className="progress-bar">
              <div 
                className="progress-fill"
                style={{ width: `${metrics.cpuUsage}%` }}
              ></div>
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-header">
              <div className="metric-icon">💾</div>
              <h3>Memory Usage</h3>
            </div>
            <div className="metric-value">{metrics.memoryUsage}%</div>
            <div className="progress-bar">
              <div 
                className="progress-fill"
                style={{ width: `${metrics.memoryUsage}%` }}
              ></div>
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-header">
              <div className="metric-icon">💿</div>
              <h3>Disk Usage</h3>
            </div>
            <div className="metric-value">{metrics.diskUsage}%</div>
            <div className="progress-bar">
              <div 
                className="progress-fill"
                style={{ width: `${metrics.diskUsage}%` }}
              ></div>
            </div>
          </div>

          <div className="metric-card">
            <div className="metric-header">
              <div className="metric-icon">🌐</div>
              <h3>Network</h3>
            </div>
            <div className="metric-value">{metrics.networkThroughput} MB/s</div>
            <div className="metric-description">Throughput</div>
          </div>
        </div>
      </div>

      {/* Peer Management */}
      <div className="peers-section">
        <div className="section-header">
          <h2>Managed Peers</h2>
          <p>{peers.length} peers across {new Set(peers.map(p => p.organization)).size} organizations</p>
        </div>

        {loading ? (
          <div className="loading">Loading peers...</div>
        ) : (
          <div className="peers-grid">
            {peers.map(peer => (
              <div key={peer.id} className="peer-card">
                <div className="peer-header">
                  <div className="peer-info">
                    <div className="peer-name">{peer.name}</div>
                    <div className="peer-org">{peer.organization}</div>
                  </div>
                  <div className={`peer-status ${peer.status}`}>
                    {peer.status}
                  </div>
                </div>

                <div className="peer-details">
                  <div className="detail">
                    <span className="label">Version:</span>
                    <span className="value">{peer.version}</span>
                  </div>
                  <div className="detail">
                    <span className="label">Ports:</span>
                    <span className="value">{peer.port} (gRPC), {peer.tlsPort} (TLS)</span>
                  </div>
                  <div className="detail">
                    <span className="label">Last Block:</span>
                    <span className="value">{peer.lastBlock}</span>
                  </div>
                  <div className="detail">
                    <span className="label">Uptime:</span>
                    <span className="value">{peer.uptime}</span>
                  </div>
                  <div className="detail">
                    <span className="label">Chaincodes:</span>
                    <span className="value">
                      {peer.chaincodes.map(cc => (
                        <span key={cc} className="chaincode-badge">{cc}</span>
                      ))}
                    </span>
                  </div>
                </div>

                <div className="peer-resources">
                  <h4>Resources</h4>
                  <div className="resource-list">
                    <div className="resource">
                      <span className="resource-icon">⚡</span>
                      <span>{peer.resources.cpu}</span>
                    </div>
                    <div className="resource">
                      <span className="resource-icon">💾</span>
                      <span>{peer.resources.memory}</span>
                    </div>
                    <div className="resource">
                      <span className="resource-icon">💿</span>
                      <span>{peer.resources.storage}</span>
                    </div>
                  </div>
                </div>

                <div className="peer-actions">
                  {peer.status === 'running' ? (
                    <>
                      <button 
                        className="btn btn-outline"
                        onClick={() => handleRestartPeer(peer.id)}
                      >
                        🔄 Restart
                      </button>
                      <button 
                        className="btn btn-danger"
                        onClick={() => handleStopPeer(peer.id)}
                      >
                        ⏸️ Stop
                      </button>
                    </>
                  ) : peer.status === 'stopped' ? (
                    <button 
                      className="btn btn-success"
                      onClick={() => handleStartPeer(peer.id)}
                    >
                      ▶️ Start
                    </button>
                  ) : peer.status === 'deploying' ? (
                    <button className="btn btn-outline" disabled>
                      ⏳ Deploying...
                    </button>
                  ) : null}
                  
                  <button className="btn-icon" title="View Logs">
                    📜
                  </button>
                  <button className="btn-icon" title="Monitor">
                    📊
                  </button>
                  <button className="btn-icon" title="Configure">
                    ⚙️
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="quick-actions">
        <h2>Quick Actions</h2>
        <div className="action-grid">
          <button className="action-card">
            <div className="action-icon">📦</div>
            <div className="action-content">
              <h3>Bulk Deploy</h3>
              <p>Deploy multiple peers at once</p>
            </div>
          </button>
          <button className="action-card">
            <div className="action-icon">🔄</div>
            <div className="action-content">
              <h3>Rolling Update</h3>
              <p>Update Fabric version across all peers</p>
            </div>
          </button>
          <button className="action-card">
            <div className="action-icon">🔒</div>
            <div className="action-content">
              <h3>Security Scan</h3>
              <p>Scan peers for vulnerabilities</p>
            </div>
          </button>
          <button className="action-card">
            <div className="action-icon">📊</div>
            <div className="action-content">
              <h3>Performance Report</h3>
              <p>Generate performance analytics</p>
            </div>
          </button>
        </div>
      </div>

      {/* Cost Management */}
      <div className="cost-management">
        <h2>Cost Management</h2>
        <div className="cost-summary">
          <div className="cost-card">
            <div className="cost-header">
              <div className="cost-icon">💰</div>
              <h3>Monthly Cost</h3>
            </div>
            <div className="cost-value">$1,245</div>
            <div className="cost-breakdown">
              <div className="breakdown-item">
                <span>Peer Hosting:</span>
                <span>$995</span>
              </div>
              <div className="breakdown-item">
                <span>Storage:</span>
                <span>$150</span>
              </div>
              <div className="breakdown-item">
                <span>Network:</span>
                <span>$100</span>
              </div>
            </div>
          </div>

          <div className="cost-card">
            <div className="cost-header">
              <div className="cost-icon">📈</div>
              <h3>Cost Projection</h3>
            </div>
            <div className="cost-value">$1,450</div>
            <div className="cost-description">
              Estimated next month with current growth
            </div>
          </div>

          <div className="cost-card">
            <div className="cost-header">
              <div className="cost-icon">💡</div>
              <h3>Optimization</h3>
            </div>
            <div className="cost-savings">Save up to $300/month</div>
            <button className="btn btn-outline">
              View Optimization Tips
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default HostedPeerDashboard;
