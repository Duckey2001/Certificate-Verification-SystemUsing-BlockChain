import React, { useState } from 'react';
import { CopyToClipboard } from 'react-copy-to-clipboard';

const BYOPeerGuide = () => {
  const [copied, setCopied] = useState(false);

  const dockerComposeExample = `version: '3.8'

services:
  peer0.org1.certivert.com:
    container_name: peer0.org1.certivert.com
    image: hyperledger/fabric-peer:2.5.0
    environment:
      - CORE_VM_ENDPOINT=unix:///host/var/run/docker.sock
      - CORE_VM_DOCKER_HOSTCONFIG_NETWORKMODE=fabric_test
      - FABRIC_LOGGING_SPEC=INFO
      - CORE_PEER_ID=peer0.org1.certivert.com
      - CORE_PEER_ADDRESS=peer0.org1.certivert.com:7051
      - CORE_PEER_LISTENADDRESS=0.0.0.0:7051
      - CORE_PEER_CHAINCODEADDRESS=peer0.org1.certivert.com:7052
      - CORE_PEER_CHAINCODELISTENADDRESS=0.0.0.0:7052
      - CORE_PEER_GOSSIP_BOOTSTRAP=peer0.org1.certivert.com:7051
      - CORE_PEER_GOSSIP_EXTERNALENDPOINT=peer0.org1.certivert.com:7051
      - CORE_PEER_LOCALMSPID=Org1MSP
    volumes:
      - ./crypto-config/peerOrganizations/org1.certivert.com/peers/peer0.org1.certivert.com/msp:/etc/hyperledger/fabric/msp
      - ./crypto-config/peerOrganizations/org1.certivert.com/peers/peer0.org1.certivert.com/tls:/etc/hyperledger/fabric/tls
      - peer0.org1.certivert.com:/var/hyperledger/production
    working_dir: /opt/gopath/src/github.com/hyperledger/fabric/peer
    command: peer node start
    ports:
      - 7051:7051
    networks:
      - fabric_test

networks:
  fabric_test:
    driver: bridge`;

  const connectionProfile = `{
  "name": "certivert-network",
  "version": "1.0.0",
  "client": {
    "organization": "Org1",
    "connection": {
      "timeout": {
        "peer": {
          "endorser": "300"
        }
      }
    }
  },
  "organizations": {
    "Org1": {
      "mspid": "Org1MSP",
      "peers": [
        "peer0.org1.certivert.com"
      ],
      "certificateAuthorities": [
        "ca.org1.certivert.com"
      ]
    }
  },
  "peers": {
    "peer0.org1.certivert.com": {
      "url": "grpcs://peer0.org1.certivert.com:7051",
      "tlsCACerts": {
        "pem": "-----BEGIN CERTIFICATE-----\\nTLS_CERT_HERE\\n-----END CERTIFICATE-----"
      },
      "grpcOptions": {
        "ssl-target-name-override": "peer0.org1.certivert.com"
      }
    }
  }
}`;

  const steps = [
    {
      step: 1,
      title: "Prerequisites",
      icon: "✅",
      content: [
        "Docker and Docker Compose installed",
        "4GB RAM minimum, 8GB recommended",
        "50GB free disk space",
        "Linux/Unix environment",
        "Basic knowledge of command line"
      ]
    },
    {
      step: 2,
      title: "Download MSP Package",
      icon: "📦",
      content: [
        "Download your organization's MSP package from the onboarding portal",
        "Extract the package to a secure location",
        "Verify certificate validity and permissions"
      ]
    },
    {
      step: 3,
      title: "Configure Docker Compose",
      icon: "🐳",
      content: [
        "Copy the provided docker-compose.yaml template",
        "Update with your organization's MSP paths",
        "Configure network settings and ports",
        "Set appropriate resource limits"
      ]
    },
    {
      step: 4,
      title: "Start Your Peer",
      icon: "🚀",
      content: [
        "Run: docker-compose up -d",
        "Check peer logs: docker-compose logs -f peer",
        "Verify peer is syncing with the network",
        "Test connection with the network"
      ]
    },
    {
      step: 5,
      title: "Join the Channel",
      icon: "⛓️",
      content: [
        "Use the provided channel join command",
        "Verify your peer has joined successfully",
        "Check peer has received the genesis block",
        "Install chaincode on your peer"
      ]
    },
    {
      step: 6,
      title: "Test & Validate",
      icon: "🧪",
      content: [
        "Test certificate query operations",
        "Verify ledger synchronization",
        "Test endorsement if you're an issuer",
        "Run health checks and monitoring"
      ]
    }
  ];

  const handleCopy = () => {
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="byo-peer-guide">
      <div className="guide-header">
        <h1>Bring Your Own Peer (BYO) Guide</h1>
        <p>Complete guide to running your own Hyperledger Fabric peer for CertiVert</p>
        <div className="guide-badge">
          <span className="badge-icon">⚡</span>
          <span>Advanced Setup - Recommended for Technical Teams</span>
        </div>
      </div>

      <div className="guide-container">
        {/* Sidebar Navigation */}
        <div className="guide-sidebar">
          <h3>Quick Navigation</h3>
          <ul className="sidebar-nav">
            {steps.map(s => (
              <li key={s.step}>
                <a href={`#step-${s.step}`}>
                  <span className="step-icon">{s.icon}</span>
                  <span>Step {s.step}: {s.title}</span>
                </a>
              </li>
            ))}
            <li>
              <a href="#docker-compose">
                <span className="step-icon">🐳</span>
                <span>Docker Compose</span>
              </a>
            </li>
            <li>
              <a href="#troubleshooting">
                <span className="step-icon">🔧</span>
                <span>Troubleshooting</span>
              </a>
            </li>
            <li>
              <a href="#support">
                <span className="step-icon">💬</span>
                <span>Support</span>
              </a>
            </li>
          </ul>

          <div className="sidebar-resources">
            <h4>Resources</h4>
            <a href="#" className="resource-link">
              📚 Fabric Documentation
            </a>
            <a href="#" className="resource-link">
              🐳 Docker Guide
            </a>
            <a href="#" className="resource-link">
              🔐 Security Best Practices
            </a>
            <a href="#" className="resource-link">
              📊 Monitoring Setup
            </a>
          </div>
        </div>

        {/* Main Content */}
        <div className="guide-content">
          {/* Benefits Section */}
          <div className="benefits-section">
            <h2>Why BYO Peer?</h2>
            <div className="benefits-grid">
              <div className="benefit-card">
                <div className="benefit-icon">🔒</div>
                <h3>Enhanced Security</h3>
                <p>Full control over your private keys and data</p>
              </div>
              <div className="benefit-card">
                <div className="benefit-icon">⚡</div>
                <h3>Direct Access</h3>
                <p>Direct read/write access to the blockchain ledger</p>
              </div>
              <div className="benefit-card">
                <div className="benefit-icon">📊</div>
                <h3>Custom Monitoring</h3>
                <p>Set up custom monitoring and alerts</p>
              </div>
              <div className="benefit-card">
                <div className="benefit-icon">💰</div>
                <h3>Cost Control</h3>
                <p>No monthly hosting fees - pay for your own infrastructure</p>
              </div>
            </div>
          </div>

          {/* Steps */}
          {steps.map(step => (
            <section key={step.step} id={`step-${step.step}`} className="step-section">
              <div className="step-header">
                <div className="step-number">{step.step}</div>
                <div className="step-title">
                  <h2>{step.title}</h2>
                  <div className="step-icon-large">{step.icon}</div>
                </div>
              </div>
              
              <div className="step-content">
                <ul className="step-checklist">
                  {step.content.map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
                
                {step.step === 3 && (
                  <div className="code-example">
                    <div className="code-header">
                      <h4>Docker Compose Template</h4>
                      <CopyToClipboard text={dockerComposeExample} onCopy={handleCopy}>
                        <button className="copy-btn">
                          {copied ? '✅ Copied!' : '📋 Copy'}
                        </button>
                      </CopyToClipboard>
                    </div>
                    <pre className="code-block">
                      <code>{dockerComposeExample}</code>
                    </pre>
                  </div>
                )}
                
                {step.step === 4 && (
                  <div className="command-examples">
                    <h4>Common Commands:</h4>
                    <div className="command-grid">
                      <div className="command-card">
                        <div className="command">docker-compose up -d</div>
                        <div className="description">Start the peer in background</div>
                      </div>
                      <div className="command-card">
                        <div className="command">docker-compose logs -f peer</div>
                        <div className="description">Follow peer logs</div>
                      </div>
                      <div className="command-card">
                        <div className="command">docker-compose ps</div>
                        <div className="description">Check container status</div>
                      </div>
                      <div className="command-card">
                        <div className="command">docker-compose restart peer</div>
                        <div className="description">Restart the peer</div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </section>
          ))}

          {/* Docker Compose Details */}
          <section id="docker-compose" className="section">
            <h2>Docker Compose Configuration</h2>
            <div className="config-explanation">
              <p>Your docker-compose.yaml file should include:</p>
              <div className="config-points">
                <div className="config-point">
                  <div className="point-icon">🔧</div>
                  <div className="point-content">
                    <h4>Peer Configuration</h4>
                    <p>Set correct MSP paths, peer ID, and addresses</p>
                  </div>
                </div>
                <div className="config-point">
                  <div className="point-icon">🔒</div>
                  <div className="point-content">
                    <h4>TLS Configuration</h4>
                    <p>Proper TLS certificates for secure communication</p>
                  </div>
                </div>
                <div className="config-point">
                  <div className="point-icon">💾</div>
                  <div className="point-content">
                    <h4>Persistence</h4>
                    <p>Configure volumes for ledger data persistence</p>
                  </div>
                </div>
                <div className="config-point">
                  <div className="point-icon">🌐</div>
                  <div className="point-content">
                    <h4>Networking</h4>
                    <p>Correct network configuration for Fabric communication</p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Connection Profile */}
          <section className="section">
            <h2>Connection Profile</h2>
            <div className="connection-profile">
              <p>Use this connection profile in your applications:</p>
              <div className="code-example">
                <div className="code-header">
                  <h4>connection-profile.json</h4>
                  <CopyToClipboard text={connectionProfile} onCopy={handleCopy}>
                    <button className="copy-btn">
                      {copied ? '✅ Copied!' : '📋 Copy'}
                    </button>
                  </CopyToClipboard>
                </div>
                <pre className="code-block">
                  <code>{connectionProfile}</code>
                </pre>
              </div>
            </div>
          </section>

          {/* Troubleshooting */}
          <section id="troubleshooting" className="section">
            <h2>Troubleshooting</h2>
            <div className="troubleshooting-grid">
              <div className="issue-card">
                <h4>Peer won't start</h4>
                <ul>
                  <li>Check Docker is running: <code>docker ps</code></li>
                  <li>Verify MSP certificates are in correct location</li>
                  <li>Check port conflicts: <code>netstat -tulpn | grep 7051</code></li>
                </ul>
              </div>
              <div className="issue-card">
                <h4>Can't join channel</h4>
                <ul>
                  <li>Verify you have the correct genesis block</li>
                  <li>Check peer can connect to orderer</li>
                  <li>Verify your organization is in channel config</li>
                </ul>
              </div>
              <div className="issue-card">
                <h4>Ledger not syncing</h4>
                <ul>
                  <li>Check peer logs for errors</li>
                  <li>Verify network connectivity</li>
                  <li>Check disk space on host</li>
                </ul>
              </div>
              <div className="issue-card">
                <h4>TLS handshake errors</h4>
                <ul>
                  <li>Verify TLS certificates are valid</li>
                  <li>Check certificate expiration dates</li>
                  <li>Verify TLS CA certificates are correct</li>
                </ul>
              </div>
            </div>
          </section>

          {/* Support */}
          <section id="support" className="section">
            <h2>Need Help?</h2>
            <div className="support-options">
              <div className="support-card">
                <div className="support-icon">📚</div>
                <h3>Documentation</h3>
                <p>Complete Fabric documentation and tutorials</p>
                <a href="#" className="btn btn-outline">View Docs</a>
              </div>
              <div className="support-card">
                <div className="support-icon">💬</div>
                <h3>Community</h3>
                <p>Join our Discord community for peer support</p>
                <a href="#" className="btn btn-outline">Join Discord</a>
              </div>
              <div className="support-card">
                <div className="support-icon">🎓</div>
                <h3>Training</h3>
                <p>Schedule a training session with our experts</p>
                <a href="#" className="btn btn-outline">Schedule Training</a>
              </div>
              <div className="support-card">
                <div className="support-icon">🔧</div>
                <h3>Professional Services</h3>
                <p>Get help with setup and configuration</p>
                <a href="#" className="btn btn-primary">Get Help</a>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};

export default BYOPeerGuide;
