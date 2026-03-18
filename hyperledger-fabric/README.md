# LGCSE Certificate Verification - Hyperledger Fabric Implementation

## Overview

This is a comprehensive Hyperledger Fabric blockchain implementation for the LGCSE Certificate Verification System. It provides enterprise-grade blockchain infrastructure with complete certificate management, verification, and audit capabilities.

## Architecture

### Network Components

- **Orderer Service**: Raft-based ordering service for transaction ordering
- **Peer Organizations**: 4 university organizations (ECOL, Limkokwing, Botho, NUL)
- **Certificate Authorities**: 5 CAs (1 orderer CA + 4 organization CAs)
- **Channel**: Single application channel `lgcse-channel`
- **Chaincode**: Go-based smart contract for certificate operations

### Organization Structure

| Organization | Role | MSP ID | Peer | CA Port |
|--------------|------|--------|------|---------|
| Ecol University | Issuer | EcolOrgMSP | peer0.ecol.example.com:7051 | 8054 |
| Limkokwing University | Verifier | LimkokwingOrgMSP | peer0.limkokwing.example.com:9051 | 9054 |
| Botho University | Verifier | BothoOrgMSP | peer0.botho.example.com:11051 | 10054 |
| National University of Lesotho | Verifier | NulOrgMSP | peer0.nul.example.com:12051 | 11054 |

## Features

### ✅ Implemented Features

1. **Complete Network Setup**
   - Automated CA setup and configuration
   - Crypto material generation
   - Channel creation and peer joining
   - Chaincode deployment and lifecycle management

2. **Certificate Management**
   - Certificate issuance with blockchain storage
   - Certificate verification with audit trail
   - Certificate revocation and status tracking
   - Private data collections for sensitive information

3. **Enterprise Security**
   - TLS-enabled network communication
   - Role-based access control (RBAC)
   - MSP-based identity management
   - Certificate-based authentication

4. **Monitoring & Analytics**
   - Real-time network health monitoring
   - Comprehensive audit logging
   - Network statistics and metrics
   - Performance monitoring

5. **Private Data Collections**
   - Certificate private data protection
   - Verification data privacy
   - Institution-specific private collections
   - Access control for private data

6. **Backend Integration**
   - Fabric SDK integration
   - REST API endpoints
   - Database synchronization
   - Real-time notifications

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Go 1.21+
- Hyperledger Fabric binaries
- Python 3.8+ (for backend)
- Sufficient disk space (2GB+)

### 🎯 Interactive Deployment Menu (Recommended)

The LGCSE system now includes an **intelligent deployment menu** that automatically analyzes your laptop resources and recommends the optimal configuration:

```bash
cd hyperledger-fabric
./scripts/deploy-menu.sh
```

The menu will:
1. **Analyze your system resources** (CPU, RAM, Disk)
2. **Recommend deployment options** based on available resources
3. **Allow you to choose** from minimal, standard, full, or custom configurations
4. **Generate optimized docker-compose** files for your setup
5. **Deploy the selected configuration** automatically

### 🖥️ Deployment Options

#### For Low-Resource Systems (≤4GB RAM)
- **📱 Minimal Deployment**
  - 1 organization (Ecol University)
  - 1 peer node
  - 1 orderer
  - 2 certificate authorities
  - No monitoring stack
  - Memory usage: ~2.5GB
  - CPU usage: ~2 cores

#### For Medium-Resource Systems (8GB RAM)
- **🚀 Standard Deployment** (Recommended)
  - 2 organizations (Ecol, Limkokwing)
  - 2 peer nodes
  - 1 orderer
  - 3 certificate authorities
  - Basic monitoring
  - Memory usage: ~5.0GB
  - CPU usage: ~3 cores

#### For High-Resource Systems (16GB+ RAM)
- **🏢 Full Enterprise Deployment**
  - 4 organizations (Ecol, Limkokwing, Botho, NUL)
  - 4 peer nodes
  - 3 orderers (Raft consensus)
  - 5 certificate authorities
  - Full monitoring stack
  - Memory usage: ~12.0GB
  - CPU usage: ~6 cores

- **⚡ High-Performance Deployment**
  - 4 organizations (Ecol, Limkokwing, Botho, NUL)
  - 8 peer nodes (2 per org)
  - 3 orderers (Raft consensus)
  - 5 certificate authorities
  - Full monitoring stack
  - Memory usage: ~20.0GB
  - CPU usage: ~10 cores

#### 🔧 Custom Deployment
- Choose your own number of organizations
- Select peers per organization
- Configure orderer count
- Enable/disable monitoring
- Resource requirements calculated automatically

### 📋 Command Line Options

If you prefer command-line deployment, you can use these shortcuts:

```bash
# Check system resources only
./scripts/deploy-menu.sh --check

# Deploy minimal configuration (for testing)
./scripts/deploy-menu.sh --minimal

# Deploy standard configuration (development)
./scripts/deploy-menu.sh --standard

# Deploy full enterprise configuration (production)
./scripts/deploy-menu.sh --full
```

### 🔧 Manual Installation

If you want to deploy manually without the menu:

1. **Clone and Setup**
```bash
cd hyperledger-fabric
chmod +x scripts/*.sh
```

2. **Start Certificate Authorities**
```bash
./scripts/setup-ca.sh
```

3. **Create Network and Channel**
```bash
./scripts/create-channel.sh
```

4. **Deploy Chaincode**
```bash
./scripts/deploy-chaincode.sh
```

5. **Start Network Services**
```bash
docker-compose -f docker-compose.yaml up -d
```

### Verification

1. **Check Network Health**
```bash
docker exec cli peer channel list
```

2. **Query Chaincode**
```bash
docker exec cli peer chaincode query -C lgcse-channel -n certificate-chaincode -c '{"Args":["GetAllInstitutions"]}'
```

3. **Test Certificate Operations**
```bash
# Issue a certificate
docker exec cli peer chaincode invoke -C lgcse-channel -n certificate-chaincode -c '{"Args":["IssueCertificate","CERT_001","STU001","John","Doe",2023,"[{\"name\":\"Mathematics\",\"grade\":\"A\",\"symbol\":\"*\"}]","5","2023-12-01","Ecol University","ECOL",""]}'

# Verify certificate
docker exec cli peer chaincode invoke -C lgcse-channel -n certificate-chaincode -c '{"Args":["VerifyCertificate","CERT_001","VER001","Alice Smith","LIMKOWING","hash","192.168.1.100","Mozilla/5.0",""]}'
```

## Configuration

### Network Configuration Files

- `configtx.yaml`: Channel and organization configuration
- `crypto-config.yaml`: Certificate generation configuration
- `docker-compose.yaml`: Service definitions and networking
- `connection-profile.json`: SDK connection profiles

### Chaincode Configuration

- `chaincode/certificate-chaincode/`: Smart contract implementation
- `chaincode/certificate-chaincode/go.mod`: Go module dependencies
- Private data collections configuration embedded in chaincode

### CA Configuration

Each organization has its own Certificate Authority:
- Orderer CA: `ca.orderer.example.com:7054`
- Ecol CA: `ca.ecol.example.com:8054`
- Limkokwing CA: `ca.limkokwing.example.com:9054`
- Botho CA: `ca.botho.example.com:10054`
- Nul CA: `ca.nul.example.com:11054`

## API Integration

### Backend Integration

The Fabric network integrates with the backend through:

1. **Fabric SDK** (`backend/utils/fabric_sdk.py`)
   - Certificate issuance and verification
   - Network monitoring and statistics
   - Private data management

2. **REST API** (`backend/api/fabric_integration.py`)
   - Certificate management endpoints
   - Institution management
   - Network monitoring APIs

3. **MSP Management** (`hyperledger-fabric/utils/msp_manager.py`)
   - User enrollment and registration
   - Certificate lifecycle management
   - Identity validation

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/fabric/certificates/issue` | POST | Issue new certificate |
| `/api/fabric/certificates/verify` | POST | Verify certificate |
| `/api/fabric/certificates/{hash}` | GET | Get certificate details |
| `/api/fabric/certificates/revoke` | POST | Revoke certificate |
| `/api/fabric/network/health` | GET | Network health status |
| `/api/fabric/network/statistics` | GET | Network statistics |
| `/api/fabric/audit-logs` | GET | Audit logs |

## Chaincode Operations

### Certificate Operations

1. **IssueCertificate**
```go
IssueCertificate(certificateHash, studentID, studentName, studentSurname, examinationYear, subjects, credits, issueDate, issuer, institutionCode, privateData)
```

2. **VerifyCertificate**
```go
VerifyCertificate(certificateHash, verifierID, verifierName, institutionCode, verificationMethod, ipAddress, userAgent, verificationData)
```

3. **RevokeCertificate**
```go
RevokeCertificate(certificateHash, reason, revokedBy, institutionCode)
```

### Query Operations

1. **GetCertificate**
```go
GetCertificate(certificateHash) -> Certificate
```

2. **GetAllCertificates**
```go
GetAllCertificates() -> []Certificate
```

3. **GetVerificationHistory**
```go
GetVerificationHistory(certificateHash) -> []VerificationRequest
```

4. **GetNetworkStatistics**
```go
GetNetworkStatistics() -> NetworkStats
```

### Private Data Operations

1. **GetCertificatePrivateData**
```go
GetCertificatePrivateData(certificateHash) -> PrivateData
```

2. **GetVerificationPrivateData**
```go
GetVerificationPrivateData(requestID) -> VerificationPrivateData
```

## Security Features

### Network Security

- **TLS Encryption**: All network communications encrypted
- **Mutual TLS**: Certificate-based authentication
- **Channel Isolation**: Private channel for certificate operations
- **Access Control**: MSP-based role management

### Data Security

- **Private Collections**: Sensitive data in private collections
- **Access Control**: Role-based data access
- **Audit Trail**: Comprehensive logging of all operations
- **Data Encryption**: Encrypted private data storage

### Identity Management

- **Certificate Authorities**: 5 CAs for identity management
- **MSP Configuration**: Organization-specific MSPs
- **User Enrollment**: Automated user registration and enrollment
- **Certificate Lifecycle**: Complete certificate lifecycle management

## Monitoring and Maintenance

### Health Monitoring

1. **Network Health**
   - Peer connectivity status
   - Channel block height
   - Transaction processing status
   - CA service availability

2. **Performance Metrics**
   - Transaction processing time
   - Chaincode execution performance
   - Network throughput
   - Resource utilization

### Maintenance Operations

1. **Certificate Renewal**
   - Automated certificate renewal
   - CA certificate rotation
   - MSP configuration updates

2. **Chaincode Upgrades**
   - Versioned chaincode deployment
   - Backward compatibility
   - Data migration support

## Troubleshooting

### Common Issues

1. **CA Connection Failed**
   - Check CA service status: `docker ps | grep ca`
   - Verify CA ports: `netstat -tlnp | grep 7054`
   - Check CA logs: `docker logs ca_ecol`

2. **Peer Not Joining Channel**
   - Verify peer TLS certificates
   - Check channel configuration
   - Review peer logs: `docker logs peer0.ecol.example.com`

3. **Chaincode Invocation Failed**
   - Check chaincode installation: `peer lifecycle chaincode queryinstalled`
   - Verify endorsement policy
   - Review chaincode logs

### Debug Commands

```bash
# Check all services
docker-compose ps

# View service logs
docker-compose logs -f peer0.ecol.example.com

# Check channel status
docker exec cli peer channel getinfo -c lgcse-channel

# Query installed chaincodes
docker exec cli peer lifecycle chaincode queryinstalled

# Check peer connectivity
docker exec cli peer channel list
```

## Development

### Adding New Organizations

1. **Update Configuration**
   - Add organization to `configtx.yaml`
   - Update `crypto-config.yaml`
   - Modify `docker-compose.yaml`

2. **Generate Crypto Material**
   - Run `cryptogen generate` with updated config
   - Generate MSP configurations

3. **Update Channel**
   - Create new channel configuration
   - Update anchor peers
   - Join new organization to channel

### Chaincode Development

1. **Modify Chaincode**
   - Edit `chaincode/certificate-chaincode/certificate_chaincode.go`
   - Update Go dependencies: `go mod tidy`
   - Test locally: `go test`

2. **Deploy New Version**
   - Package chaincode: `peer lifecycle chaincode package`
   - Install on peers: `peer lifecycle chaincode install`
   - Approve and commit: `peer lifecycle chaincode approveformyorg`

## Production Deployment

### Environment Setup

1. **Hardware Requirements**
   - Minimum 4 CPU cores, 8GB RAM per peer
   - 100GB storage for ledger data
   - Network bandwidth: 1Gbps recommended

2. **Security Hardening**
   - Enable firewall rules
   - Implement network segmentation
   - Use production CA certificates
   - Enable audit logging

3. **High Availability**
   - Multiple orderer nodes
   - Redundant peer deployments
   - Load balancer configuration
   - Backup and recovery procedures

### Backup Strategy

1. **Ledger Backups**
   - Regular ledger snapshots
   - Chaincode backup
   - Configuration backups

2. **CA Backups**
   - CA database backups
   - Certificate backups
   - MSP configuration backups

## Support

For issues and questions:

1. **Documentation**: Review this README and inline code comments
2. **Logs**: Check Docker logs and application logs
3. **Health Checks**: Use `/api/fabric/network/health` endpoint
4. **Community**: Contact the development team

## License

This implementation is part of the LGCSE Certificate Verification System and follows the project's licensing terms.

---

**Note**: This is a production-ready Hyperledger Fabric implementation with enterprise-grade features. Ensure proper security configurations before deploying to production environments.
