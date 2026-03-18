# LGCSE Certificate Verification System - Deployment Guide

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Deployment Options](#deployment-options)
4. [Local Development Deployment](#local-development-deployment)
5. [Production Deployment](#production-deployment)
6. [Cloud Deployment](#cloud-deployment)
7. [Configuration](#configuration)
8. [Monitoring and Maintenance](#monitoring-and-maintenance)
9. [Troubleshooting](#troubleshooting)
10. [Performance Optimization](#performance-optimization)

## Overview

The LGCSE Certificate Verification System is a comprehensive Hyperledger Fabric blockchain solution for certificate issuance, verification, and management. This guide covers all deployment scenarios from local development to production cloud deployment.

## Prerequisites

### System Requirements

#### Minimum Requirements
- **CPU**: 2 cores
- **RAM**: 4GB
- **Disk**: 20GB available space
- **OS**: Linux, macOS, or Windows with WSL2

#### Recommended Requirements
- **CPU**: 4+ cores
- **RAM**: 8GB+
- **Disk**: 50GB+ available space
- **OS**: Linux (Ubuntu 20.04+ recommended)

#### Software Requirements
- Docker 20.10+
- Docker Compose 2.0+
- Go 1.21+
- Python 3.8+
- Git
- Make (optional, for building from source)

### Network Requirements
- Internet connection for downloading images
- Port access: 7050-12054 (for blockchain services)
- Port access: 3000, 8080, 9090 (for monitoring)

## Deployment Options

### 1. Interactive Menu Deployment (Recommended)

The intelligent deployment menu automatically analyzes your system resources and recommends the optimal configuration:

```bash
cd hyperledger-fabric
./scripts/deploy-menu.sh
```

### 2. Command-Line Deployment

```bash
# Check system resources
./scripts/deploy-menu.sh --check

# Deploy minimal configuration (2GB RAM)
./scripts/deploy-menu.sh --minimal

# Deploy standard configuration (8GB RAM)
./scripts/deploy-menu.sh --standard

# Deploy full enterprise configuration (16GB+ RAM)
./scripts/deploy-menu.sh --full
```

### 3. Manual Deployment

```bash
# 1. Setup Certificate Authorities
./scripts/setup-ca.sh

# 2. Create network and channels
./scripts/create-channel.sh

# 3. Deploy chaincode
./scripts/deploy-chaincode.sh

# 4. Start services
docker-compose -f docker-compose.yaml up -d
```

## Local Development Deployment

### Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd lgcse-project/hyperledger-fabric

# Run interactive deployment
./scripts/deploy-menu.sh

# Choose "Standard Deployment" for development
```

### Development Configuration

For local development, the standard deployment is recommended:

- **Organizations**: 2 (LGCSE Certificate Authority, Ministry of Education)
- **Peers**: 2 (1 per organization)
- **Orderers**: 1
- **Memory Usage**: ~5GB
- **CPU Usage**: ~3 cores
- **Features**: Basic monitoring, all core functionality

### Access Points

After deployment, access the following services:

- **Blockchain Explorer**: http://localhost:8080
- **Grafana Monitoring**: http://localhost:3000 (admin/admin)
- **Prometheus Metrics**: http://localhost:9090
- **Backend API**: http://localhost:8000

## Production Deployment

### Production Checklist

- [ ] Security review completed
- [ ] Resource requirements verified
- [ ] Backup strategy implemented
- [ ] Monitoring configured
- [ ] SSL certificates obtained
- [ ] Network security configured
- [ ] Performance testing completed

### AWS Production Deployment

#### Prerequisites
- AWS CLI configured with appropriate permissions
- EC2 key pair created
- Domain name configured (optional)
- SSL certificate obtained (optional)

#### Deployment Steps

```bash
# Deploy to AWS
cd hyperledger-fabric
./deploy/production/aws-deploy.sh

# This will:
# 1. Create IAM roles and security groups
# 2. Set up EFS and S3 for storage
# 3. Deploy EC2 instances
# 4. Configure monitoring and backup
# 5. Set up Route 53 (if domain provided)
```

#### AWS Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Load Balancer   │    │   CloudWatch    │
│   (Port 80/443)   │    │   (Monitoring)   │
└─────────────────┘    └─────────────────┘
          │                       │
┌─────────────────┐    ┌─────────────────┐
│   EC2 Instances │    │   S3 Bucket     │
│   (Blockchain)   │    │   (Backups)     │
└─────────────────┘    └─────────────────┘
          │                       │
┌─────────────────┐    ┌─────────────────┐
│      EFS         │    │   Route 53      │
│   (Shared Data)  │    │   (DNS)         │
└─────────────────┘    └─────────────────┘
```

### Kubernetes Production Deployment

#### Prerequisites
- Kubernetes cluster (v1.20+)
- kubectl configured
- StorageClass configured (EFS recommended)
- Ingress controller installed

#### Deployment Steps

```bash
# Deploy to Kubernetes
cd hyperledger-fabric
kubectl apply -f deploy/production/kubernetes-deploy.yaml

# Verify deployment
kubectl get pods -n lgcse-blockchain
kubectl get services -n lgcse-blockchain
```

#### Kubernetes Architecture

```
┌─────────────────┐
│   Ingress        │
└─────────────────┘
          │
┌─────────────────┐    ┌─────────────────┐
│   Services       │    │   ConfigMaps    │
└─────────────────┘    └─────────────────┘
          │                       │
┌─────────────────┐    ┌─────────────────┐
│   Deployments    │    │   StatefulSets  │
│   (Blockchain)   │    │   (Blockchain)   │
└─────────────────┘    └─────────────────┘
          │                       │
┌─────────────────┐    ┌─────────────────┐
│   PVCs           │    │   Namespaces    │
│   (Storage)      │    │   (Isolation)    │
└─────────────────┘    └─────────────────┘
```

## Cloud Deployment

### AWS Deployment

#### Features
- Auto-scaling with CloudWatch alarms
- EFS for shared storage
- S3 for backups
- CloudWatch monitoring
- Route 53 DNS management
- IAM security roles

#### Cost Optimization
- Use t3.xlarge instances for development
- Use m5.xlarge for production
- Enable S3 lifecycle policies
- Use reserved instances for long-term deployment

### Azure Deployment

#### Prerequisites
- Azure CLI installed
- Resource group created
- Key vault for secrets

#### Deployment Steps

```bash
# Deploy to Azure (script similar to AWS)
# TODO: Implement Azure deployment script
```

### Google Cloud Deployment

#### Prerequisites
- gcloud CLI installed
- Project created
- Service account configured

#### Deployment Steps

```bash
# Deploy to GCP (script similar to AWS)
# TODO: Implement GCP deployment script
```

## Configuration

### Environment Variables

Create `.env` file:

```bash
# Network Configuration
NETWORK_NAME=lgcse-network
DOMAIN_NAME=lgcse.example.com
SSL_CERT_PATH=/path/to/cert.pem
SSL_KEY_PATH=/path/to/key.pem

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=lgcse
DB_USER=lgcse
DB_PASSWORD=secure_password

# Blockchain Configuration
ORDERER_COUNT=3
PEERS_PER_ORG=1
CHANNEL_NAME=lgcse-channel
CHAINCODE_VERSION=1.0.0

# Monitoring Configuration
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
EXPLORER_PORT=8080

# Performance Configuration
BATCH_SIZE=10
CACHE_SIZE=1GB
MAX_CONNECTIONS=50
RESPONSE_TIMEOUT=5s
```

### Docker Compose Configuration

Key configuration options in `docker-compose.yaml`:

```yaml
version: '3.7'
services:
  peer0.lgcse.example.com:
    image: hyperledger/fabric-peer:latest
    environment:
      - CORE_PEER_ID=peer0.lgcse.example.com
      - CORE_PEER_ADDRESS=peer0.lgcse.example.com:7051
      - CORE_PEER_LOCALMSPID=LGCSEOrgMSP
      - CORE_LEDGER_STATE_STATEDATABASE=CouchDB
      - CORE_LEDGER_STATE_COUCHDBCONFIG_COUCHDBADDRESS=couchdb0:5984
    ports:
      - "7051:7051"
      - "7052:7052"
      - "9444:9444"
    volumes:
      - ./data/peer0.lgcse.example.com:/var/hyperledger/production
      - ./crypto-config/peerOrganizations/lgcse.example.com/peers/peer0.lgcse.example.com/msp:/etc/hyperledger/fabric/msp
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
```

### Chaincode Configuration

Optimization settings in `chaincode/certificate-chaincode/go.mod`:

```go
module certificate-chaincode

go 1.21

require (
    github.com/hyperledger/fabric-contract-api-go v1.2.0
    github.com/hyperledger/fabric-chaincode-go v0.0.0-20230125191254-598cd8c1ef0f
    github.com/hyperledger/fabric-protos-go v0.2.0
)
```

## Monitoring and Maintenance

### Health Checks

```bash
# Check service status
docker-compose ps

# Check container logs
docker-compose logs -f peer0.lgcse.example.com

# Check blockchain health
curl http://localhost:8080/api/health

# Check metrics
curl http://localhost:9090/metrics
```

### Backup Procedures

#### Automated Backups

```bash
# Enable automated backups
./scripts/disaster-recovery.sh schedule

# Manual backup
./scripts/disaster-recovery.sh full_backup

# Verify backup
./scripts/disaster-recovery.sh verify backup_manifest_20231201_120000.json
```

#### Backup Retention

- **Daily backups**: Retained for 30 days
- **Weekly backups**: Retained for 12 weeks
- **Monthly backups**: Retained for 12 months
- **Annual backups**: Retained for 7 years

### Maintenance Tasks

#### Weekly
- Review system performance metrics
- Check disk space usage
- Verify backup integrity
- Update security patches

#### Monthly
- Review and update SSL certificates
- Audit user access and permissions
- Performance optimization review
- Disaster recovery testing

#### Quarterly
- Major version updates
- Security audit
- Architecture review
- Capacity planning

### Scaling Procedures

#### Horizontal Scaling

```bash
# Add more peers to an organization
# Update docker-compose.yaml
# Add new peer service
# Update crypto-config.yaml
# Redeploy
```

#### Vertical Scaling

```bash
# Increase resource limits
# Update docker-compose.yaml
# Increase memory and CPU limits
# Restart services
```

## Troubleshooting

### Common Issues

#### 1. Certificate Authority Issues

**Problem**: CA services fail to start

**Solution**:
```bash
# Check CA logs
docker logs ca.lgcse.example.com

# Check port conflicts
netstat -tlnp | grep 8054

# Restart CA services
docker-compose restart ca.lgcse.example.com
```

#### 2. Peer Connection Issues

**Problem**: Peers cannot connect to orderer

**Solution**:
```bash
# Check network connectivity
docker exec peer0.lgcse.example.com ping orderer.example.com

# Check TLS certificates
docker exec peer0.lgcse.example.com ls /etc/hyperledger/fabric/tls/

# Restart peer
docker-compose restart peer0.lgcse.example.com
```

#### 3. Chaincode Issues

**Problem**: Chaincode deployment fails

**Solution**:
```bash
# Check chaincode logs
docker logs peer0.lgcse.example.com

# Verify chaincode installation
docker exec cli peer lifecycle chaincode queryinstalled

# Reinstall chaincode
./scripts/deploy-chaincode.sh
```

#### 4. Performance Issues

**Problem**: Slow response times

**Solution**:
```bash
# Check system resources
docker stats

# Enable performance tuning
cd optimization
python3 performance-tuner.py

# Apply optimization profile
python3 -c "
from performance_tuner import PerformanceTuner
tuner = PerformanceTuner()
tuner.auto_tune()
"
```

### Error Codes

| Error Code | Description | Solution |
|------------|-------------|---------|
| 401 | Unauthorized | Check user permissions and MSP configuration |
| 403 | Forbidden | Verify access control policies |
| 404 | Not Found | Check if resource exists |
| 500 | Internal Error | Check logs and restart services |
| 503 | Service Unavailable | Check service status and restart |

### Debug Mode

Enable debug logging:

```bash
# Enable debug logging
export FABRIC_LOGGING_SPEC=DEBUG
export CORE_PEER_LOGGING_SPEC=DEBUG

# Restart services with debug logging
docker-compose down
docker-compose up -d
```

## Performance Optimization

### Performance Tuning

#### 1. Chaincode Optimization

Use optimized chaincode:

```bash
# Deploy optimized chaincode
cd optimization
go build -o chaincode/certificate-chaincode/optimized-chaincode ./chaincode/certificate-chaincode/
```

#### 2. Database Optimization

Optimize CouchDB configuration:

```yaml
# In docker-compose.yaml
couchdb0:
  image: couchdb:3.3.2
  environment:
    - COUCHDB_USER=admin
    - COUCHDB_PASSWORD=adminpw
    - ERL_FLAGS=-setcap ulimit -s unlimited
  ulimits:
    memlock:
      soft: -1
      hard: -1
```

#### 3. Network Optimization

Optimize Docker networking:

```yaml
# In docker-compose.yaml
networks:
  lgcse:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.name: lgcse
      com.docker.network.driver.mtu: 1500
```

### Performance Monitoring

#### Metrics Collection

```bash
# Collect system metrics
cd optimization
python3 performance-tuner.py

# Generate performance report
python3 -c "
from performance_tuner import PerformanceTuner
tuner = PerformanceTuner()
report = tuner.get_performance_report()
print(report)
"
```

#### Alerting

Set up CloudWatch alerts:

```bash
# Create CloudWatch alarms for critical metrics
aws cloudwatch put-metric-alarm \
  --alarm-name "LGCSE-High-CPU" \
  --metric-name CPUUtilization \
  --namespace AWS/EC2 \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

### Optimization Profiles

#### High Throughput Profile

```python
from optimization.performance_tuner import PerformanceTuner

tuner = PerformanceTuner()
result = tuner.apply_optimization_profile("high_throughput")
```

#### Low Latency Profile

```python
result = tuner.apply_optimization_profile("low_latency")
```

#### Resource Constrained Profile

```python
result = tuner.apply_optimization_profile("resource_constrained")
```

## Security Best Practices

### Network Security

1. **TLS Encryption**: All communications use TLS
2. **Network Segmentation**: Use private networks
3. **Firewall Rules**: Restrict access to required ports
4. **VPN Access**: Use VPN for remote access

### Data Security

1. **Encryption at Rest**: Encrypt sensitive data
2. **Private Collections**: Use Fabric private data collections
3. **Access Control**: Implement role-based access control
4. **Audit Logging**: Log all access and modifications

### Identity Management

1. **Certificate Authorities**: Use Fabric CAs
2. **MSP Configuration**: Proper MSP setup
3. **User Enrollment**: Secure user enrollment process
4. **Certificate Rotation**: Regular certificate rotation

## Support

### Documentation

- [API Documentation](docs/API.md)
- [Architecture Guide](docs/ARCHITECTURE.md)
- [Security Guide](docs/SECURITY.md)
- [Performance Guide](docs/PERFORMANCE.md)

### Community Support

- GitHub Issues: Report bugs and feature requests
- Discussion Forum: Ask questions and share experiences
- Wiki: Community-maintained documentation

### Commercial Support

For enterprise support options:
- Email: support@lgcse.example.com
- Phone: +266-123-4567
- SLA: 99.9% uptime guarantee

---

**Last Updated**: December 2023
**Version**: 2.0.0
**Maintainers**: LGCSE Development Team
