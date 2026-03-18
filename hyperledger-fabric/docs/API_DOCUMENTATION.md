# LGCSE Certificate Verification System - API Documentation

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Certificate Management APIs](#certificate-management-apis)
4. [Verification APIs](#verification-apis)
5. [Institution APIs](#institution-apis)
6. [Blockchain Management APIs](#blockchain-management-apis)
7. [Monitoring APIs](#monitoring-apis)
8. [Error Handling](#error-handling)
9. [Rate Limiting](#rate-limiting)
10. [SDK Integration](#sdk-integration)

## Overview

The LGCSE Certificate Verification System provides RESTful APIs for certificate management, verification, and blockchain operations. All APIs follow REST principles and use JSON for data exchange.

### Base URL

- **Development**: `http://localhost:8000/api/v1`
- **Production**: `https://lgcse.example.com/api/v1`

### API Versioning

The API uses semantic versioning:
- `v1.0.0`: Initial release
- `v1.1.0`: Added batch operations
- `v2.0.0`: Breaking changes with enhanced security

### Content Types

All requests and responses use `application/json` content type.

## Authentication

### Bearer Token Authentication

```http
Authorization: Bearer <token>
```

### API Key Authentication

```http
X-API-Key: <api-key>
```

### Obtaining Tokens

```bash
# Login to get JWT token
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin@lgcse.example.com",
    "password": "secure_password"
  }'
```

Response:
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600,
  "user": {
    "id": "user_123",
    "username": "admin@lgcse.example.com",
    "role": "admin",
    "institution": "LGCSE"
  }
}
```

## Certificate Management APIs

### Issue Certificate

Issues a new certificate on the blockchain.

**Endpoint**: `POST /certificates/issue`

**Request Body**:
```json
{
  "certificateHash": "CERT_001",
  "studentId": "STU_001",
  "studentName": "John",
  "studentSurname": "Doe",
  "examinationYear": 2023,
  "subjects": [
    {
      "name": "Mathematics",
      "grade": "A",
      "symbol": "*",
      "marks": 85
    },
    {
      "name": "English",
      "grade": "B",
      "symbol": "+",
      "marks": 75
    }
  ],
  "credits": 5,
  "issueDate": "2023-12-01",
  "issuer": "LGCSE Certificate Authority",
  "institutionCode": "LGCSE",
  "privateData": "encrypted_sensitive_data"
}
```

**Response**:
```json
{
  "success": true,
  "certificate": {
    "certificateHash": "CERT_001",
    "transactionId": "tx_123456",
    "blockNumber": 100,
    "timestamp": "2023-12-01T10:00:00Z",
    "status": "issued"
  },
  "message": "Certificate issued successfully"
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/api/v1/certificates/issue \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "certificateHash": "CERT_001",
    "studentId": "STU_001",
    "studentName": "John",
    "studentSurname": "Doe",
    "examinationYear": 2023,
    "subjects": [{"name": "Mathematics", "grade": "A", "symbol": "*"}],
    "credits": 5,
    "issueDate": "2023-12-01",
    "issuer": "LGCSE Certificate Authority",
    "institutionCode": "LGCSE"
  }'
```

### Get Certificate

Retrieves certificate details by hash.

**Endpoint**: `GET /certificates/{certificateHash}`

**Response**:
```json
{
  "success": true,
  "certificate": {
    "certificateHash": "CERT_001",
    "studentId": "STU_001",
    "studentName": "John",
    "studentSurname": "Doe",
    "examinationYear": 2023,
    "subjects": [
      {
        "name": "Mathematics",
        "grade": "A",
        "symbol": "*",
        "marks": 85
      }
    ],
    "credits": 5,
    "issueDate": "2023-12-01",
    "issuer": "LGCSE Certificate Authority",
    "institutionCode": "LGCSE",
    "status": "active",
    "createdAt": "2023-12-01T10:00:00Z",
    "updatedAt": "2023-12-01T10:00:00Z",
    "verificationCount": 5,
    "lastVerified": "2023-12-15T14:30:00Z"
  }
}
```

### Update Certificate

Updates certificate information.

**Endpoint**: `PUT /certificates/{certificateHash}`

**Request Body**:
```json
{
  "studentName": "John Updated",
  "subjects": [
    {
      "name": "Mathematics",
      "grade": "A+",
      "symbol": "*",
      "marks": 90
    }
  ],
  "credits": 6
}
```

### Revoke Certificate

Revokes a certificate.

**Endpoint**: `POST /certificates/{certificateHash}/revoke`

**Request Body**:
```json
{
  "reason": "Academic misconduct",
  "revokedBy": "admin@lgcse.example.com",
  "institutionCode": "LGCSE"
}
```

**Response**:
```json
{
  "success": true,
  "certificate": {
    "certificateHash": "CERT_001",
    "status": "revoked",
    "revocationReason": "Academic misconduct",
    "revokedAt": "2023-12-20T09:00:00Z",
    "revokedBy": "admin@lgcse.example.com"
  },
  "message": "Certificate revoked successfully"
}
```

### List Certificates

Lists certificates with pagination and filtering.

**Endpoint**: `GET /certificates`

**Query Parameters**:
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20)
- `institutionCode`: Filter by institution
- `status`: Filter by status (active, revoked)
- `studentId`: Filter by student ID
- `examinationYear`: Filter by year

**Response**:
```json
{
  "success": true,
  "certificates": [
    {
      "certificateHash": "CERT_001",
      "studentId": "STU_001",
      "studentName": "John",
      "studentSurname": "Doe",
      "institutionCode": "LGCSE",
      "status": "active",
      "issueDate": "2023-12-01",
      "createdAt": "2023-12-01T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8
  }
}
```

### Batch Issue Certificates

Issues multiple certificates in a single transaction.

**Endpoint**: `POST /certificates/batch-issue`

**Request Body**:
```json
{
  "certificates": [
    {
      "certificateHash": "CERT_001",
      "studentId": "STU_001",
      "studentName": "John",
      "studentSurname": "Doe",
      "examinationYear": 2023,
      "subjects": [{"name": "Mathematics", "grade": "A", "symbol": "*"}],
      "credits": 5,
      "issueDate": "2023-12-01",
      "issuer": "LGCSE Certificate Authority",
      "institutionCode": "LGCSE"
    },
    {
      "certificateHash": "CERT_002",
      "studentId": "STU_002",
      "studentName": "Jane",
      "studentSurname": "Smith",
      "examinationYear": 2023,
      "subjects": [{"name": "English", "grade": "B", "symbol": "+"}],
      "credits": 4,
      "issueDate": "2023-12-01",
      "issuer": "LGCSE Certificate Authority",
      "institutionCode": "LGCSE"
    }
  ]
}
```

**Response**:
```json
{
  "success": true,
  "batchId": "batch_123456",
  "transactionId": "tx_batch_123456",
  "results": [
    {
      "certificateHash": "CERT_001",
      "status": "issued",
      "transactionId": "tx_123456_1"
    },
    {
      "certificateHash": "CERT_002",
      "status": "issued",
      "transactionId": "tx_123456_2"
    }
  ],
  "summary": {
    "total": 2,
    "issued": 2,
    "failed": 0
  }
}
```

## Verification APIs

### Verify Certificate

Verifies a certificate using various methods.

**Endpoint**: `POST /verifications/verify`

**Request Body**:
```json
{
  "certificateHash": "CERT_001",
  "verifierId": "VER_001",
  "verifierName": "Test Verifier",
  "institutionCode": "LIMKOWING",
  "verificationMethod": "hash",
  "ipAddress": "192.168.1.100",
  "userAgent": "Mozilla/5.0",
  "verificationData": "additional_verification_data"
}
```

**Response**:
```json
{
  "success": true,
  "verification": {
    "requestId": "VERIFY_123456",
    "certificateHash": "CERT_001",
    "result": "valid",
    "confidenceScore": 0.98,
    "timestamp": "2023-12-15T14:30:00Z",
    "processingTime": 1500,
    "verifierId": "VER_001",
    "verifierName": "Test Verifier",
    "institutionCode": "LIMKOWING",
    "verificationMethod": "hash"
  },
  "certificate": {
    "certificateHash": "CERT_001",
    "studentId": "STU_001",
    "studentName": "John",
    "studentSurname": "Doe",
    "institutionCode": "LGCSE",
    "status": "active",
    "issueDate": "2023-12-01"
  }
}
```

### Get Verification History

Gets verification history for a certificate.

**Endpoint**: `GET /verifications/{certificateHash}/history`

**Response**:
```json
{
  "success": true,
  "history": [
    {
      "requestId": "VERIFY_123456",
      "certificateHash": "CERT_001",
      "result": "valid",
      "confidenceScore": 0.98,
      "timestamp": "2023-12-15T14:30:00Z",
      "verifierId": "VER_001",
      "verifierName": "Test Verifier",
      "institutionCode": "LIMKOWING",
      "verificationMethod": "hash",
      "ipAddress": "192.168.1.100"
    }
  ],
  "summary": {
    "totalVerifications": 5,
    "validVerifications": 5,
    "lastVerification": "2023-12-15T14:30:00Z"
  }
}
```

### Batch Verify Certificates

Verifies multiple certificates in a single request.

**Endpoint**: `POST /verifications/batch-verify`

**Request Body**:
```json
{
  "verifications": [
    {
      "certificateHash": "CERT_001",
      "verifierId": "VER_001",
      "verifierName": "Test Verifier",
      "institutionCode": "LIMKOWING",
      "verificationMethod": "hash"
    },
    {
      "certificateHash": "CERT_002",
      "verifierId": "VER_001",
      "verifierName": "Test Verifier",
      "institutionCode": "LIMKOWING",
      "verificationMethod": "file"
    }
  ]
}
```

## Institution APIs

### Get Institution

Retrieves institution information.

**Endpoint**: `GET /institutions/{institutionCode}`

**Response**:
```json
{
  "success": true,
  "institution": {
    "nodeId": "LGCSE_NODE_001",
    "institutionCode": "LGCSE",
    "institutionName": "LGCSE Certificate Authority",
    "nodeType": "issuer",
    "mspId": "LGCSEOrgMSP",
    "peerId": "peer0.lgcse.example.com",
    "channelName": "lgcse-channel",
    "status": "active",
    "publicKey": "-----BEGIN PUBLIC KEY-----...",
    "nodeConfig": {
      "region": "lesotho",
      "type": "university",
      "establishedYear": 2007
    },
    "createdAt": "2023-01-01T00:00:00Z",
    "updatedAt": "2023-12-01T10:00:00Z"
  }
}
```

### Update Institution

Updates institution information.

**Endpoint**: `PUT /institutions/{institutionCode}`

**Request Body**:
```json
{
  "institutionName": "Ecol University Updated",
  "nodeConfig": {
    "region": "lesotho",
    "type": "university",
    "establishedYear": 2007,
    "website": "https://www.ecol.ac.ls"
  }
}
```

### List Institutions

Lists all institutions.

**Endpoint**: `GET /institutions`

**Response**:
```json
{
  "success": true,
  "institutions": [
    {
      "nodeId": "LGCSE_NODE_001",
      "institutionCode": "LGCSE",
      "institutionName": "LGCSE Certificate Authority",
      "nodeType": "issuer",
      "status": "active"
    },
    {
      "nodeId": "LIMKOWING_NODE_001",
      "institutionCode": "LIMKOWING",
      "institutionName": "Limkokwing University",
      "nodeType": "verifier",
      "status": "active"
    }
  ]
}
```

### Get Institution Statistics

Gets statistics for an institution.

**Endpoint**: `GET /institutions/{institutionCode}/statistics`

**Response**:
```json
{
  "success": true,
  "statistics": {
    "institutionCode": "LGCSE",
    "totalCertificates": 1500,
    "activeCertificates": 1450,
    "revokedCertificates": 50,
    "totalVerifications": 5000,
    "verificationsThisMonth": 250,
    "averageConfidenceScore": 0.95,
    "lastActivity": "2023-12-15T14:30:00Z"
  }
}
```

## Blockchain Management APIs

### Get Network Statistics

Gets network-wide statistics.

**Endpoint**: `GET /blockchain/statistics`

**Response**:
```json
{
  "success": true,
  "statistics": {
    "totalCertificates": 10000,
    "totalInstitutions": 4,
    "totalVerifications": 50000,
    "activeChannels": 4,
    "blockHeight": 5000,
    "totalTransactions": 15000,
    "averageResponseTime": 2.5,
    "networkHealth": "healthy"
  }
}
```

### Get Channel Information

Gets channel information.

**Endpoint**: `GET /blockchain/channels/{channelName}`

**Response**:
```json
{
  "success": true,
  "channel": {
    "name": "lgcse-channel",
    "type": "certificate_verification",
    "organizations": ["EcolOrgMSP", "LimkokwingOrgMSP", "BothoOrgMSP", "NulOrgMSP"],
    "status": "active",
    "blockHeight": 5000,
    "created_at": "2023-01-01T00:00:00Z",
    "last_updated": "2023-12-15T14:30:00Z"
  }
}
```

### Get Chaincode Information

Gets chaincode information.

**Endpoint**: `GET /blockchain/chaincode/{chaincodeName}`

**Response**:
```json
{
  "success": true,
  "chaincode": {
    "name": "certificate-chaincode",
    "version": "1.0.0",
    "status": "active",
    "channels": ["lgcse-channel"],
    "installed_on": ["peer0.ecol.example.com", "peer0.limkokwing.example.com"],
    "instantiated_on": ["lgcse-channel"],
    "created_at": "2023-01-01T00:00:00Z",
    "updated_at": "2023-12-01T10:00:00Z"
  }
}
```

### Get Block Information

Gets block information by number.

**Endpoint**: `GET /blockchain/blocks/{blockNumber}`

**Response**:
```json
{
  "success": true,
  "block": {
    "number": 1000,
    "hash": "block_hash_123456",
    "previousHash": "block_hash_123455",
    "dataHash": "data_hash_123456",
    "timestamp": "2023-12-15T14:30:00Z",
    "transactions": [
      {
        "id": "tx_123456",
        "type": "certificate_issuance",
        "timestamp": "2023-12-15T14:30:00Z"
      }
    ]
  }
}
```

## Monitoring APIs

### Get System Health

Gets system health status.

**Endpoint**: `GET /monitoring/health`

**Response**:
```json
{
  "success": true,
  "health": {
    "status": "healthy",
    "timestamp": "2023-12-15T14:30:00Z",
    "services": {
      "blockchain": "healthy",
      "database": "healthy",
      "cache": "healthy",
      "api": "healthy"
    },
    "metrics": {
      "cpu_usage": 45.2,
      "memory_usage": 67.8,
      "disk_usage": 23.4,
      "response_time": 1.2
    }
  }
}
```

### Get Performance Metrics

Gets performance metrics.

**Endpoint**: `GET /monitoring/metrics`

**Response**:
```json
{
  "success": true,
  "metrics": {
    "timestamp": "2023-12-15T14:30:00Z",
    "performance": {
      "total_transactions": 15000,
      "transactions_per_second": 25.5,
      "average_response_time": 1.2,
      "error_rate": 0.5
    },
    "resources": {
      "cpu_usage": 45.2,
      "memory_usage": 67.8,
      "disk_usage": 23.4,
      "network_io": 1024.5
    },
    "cache": {
      "hit_rate": 85.2,
      "size": "1GB",
      "entries": 10000
    }
  }
}
```

### Get Audit Logs

Gets audit logs.

**Endpoint**: `GET /monitoring/audit-logs`

**Query Parameters**:
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 50)
- `startDate`: Start date filter
- `endDate`: End date filter
- `userId`: User ID filter
- `action`: Action filter

**Response**:
```json
{
  "success": true,
  "logs": [
    {
      "id": "log_123456",
      "timestamp": "2023-12-15T14:30:00Z",
      "userId": "user_123",
      "action": "certificate_issued",
      "resource": "CERT_001",
      "ipAddress": "192.168.1.100",
      "userAgent": "Mozilla/5.0",
      "result": "success",
      "details": {
        "certificateHash": "CERT_001",
        "studentId": "STU_001"
      }
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 5000,
    "pages": 100
  }
}
```

## Error Handling

### Error Response Format

All errors follow this format:

```json
{
  "success": false,
  "error": {
    "code": "CERTIFICATE_NOT_FOUND",
    "message": "Certificate not found",
    "details": {
      "certificateHash": "CERT_001",
      "timestamp": "2023-12-15T14:30:00Z"
    },
    "requestId": "req_123456"
  }
}
```

### Error Codes

| Error Code | HTTP Status | Description |
|------------|------------|-------------|
| `UNAUTHORIZED` | 401 | Authentication failed |
| `FORBIDDEN` | 403 | Access denied |
| `CERTIFICATE_NOT_FOUND` | 404 | Certificate not found |
| `INVALID_REQUEST` | 400 | Invalid request parameters |
| `DUPLICATE_CERTIFICATE` | 409 | Certificate already exists |
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `RATE_LIMIT_EXCEEDED` | 429 | Rate limit exceeded |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

### Handling Errors

```javascript
// Example error handling in JavaScript
try {
  const response = await fetch('/api/v1/certificates/CERT_001', {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  
  const data = await response.json();
  
  if (!data.success) {
    console.error('API Error:', data.error);
    
    // Handle specific error codes
    switch (data.error.code) {
      case 'CERTIFICATE_NOT_FOUND':
        // Handle certificate not found
        break;
      case 'UNAUTHORIZED':
        // Redirect to login
        break;
      default:
        // Generic error handling
        break;
    }
  }
} catch (error) {
  console.error('Network error:', error);
}
```

## Rate Limiting

### Rate Limits

- **Authentication**: 10 requests per minute
- **Certificate operations**: 100 requests per minute
- **Verification**: 200 requests per minute
- **Monitoring**: 50 requests per minute

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1702694400
```

### Handling Rate Limits

```javascript
// Example rate limit handling
async function makeRequest(url, options = {}) {
  const response = await fetch(url, options);
  
  if (response.status === 429) {
    const resetTime = response.headers.get('X-RateLimit-Reset');
    const waitTime = resetTime ? (resetTime * 1000 - Date.now()) : 60000;
    
    console.log(`Rate limit exceeded. Waiting ${waitTime}ms...`);
    await new Promise(resolve => setTimeout(resolve, waitTime));
    
    // Retry the request
    return makeRequest(url, options);
  }
  
  return response;
}
```

## SDK Integration

### Python SDK Example

```python
from fabric_sdk import FabricSDK

# Initialize SDK
sdk = FabricSDK(
    api_url="http://localhost:8000/api/v1",
    token="your_jwt_token"
)

# Issue a certificate
result = sdk.issue_certificate({
    "certificateHash": "CERT_001",
    "studentId": "STU_001",
    "studentName": "John",
    "studentSurname": "Doe",
    "examinationYear": 2023,
    "subjects": [{"name": "Mathematics", "grade": "A", "symbol": "*"}],
    "credits": 5,
    "issueDate": "2023-12-01",
    "issuer": "LGCSE Certificate Authority",
    "institutionCode": "LGCSE"
})

if result["success"]:
    print(f"Certificate issued: {result['transactionId']}")
else:
    print(f"Error: {result['error']['message']}")
```

### JavaScript SDK Example

```javascript
import { LGCSEClient } from 'lgcse-js-sdk';

// Initialize client
const client = new LGCSEClient({
  baseURL: 'http://localhost:8000/api/v1',
  token: 'your_jwt_token'
});

// Verify a certificate
try {
  const result = await client.verifyCertificate({
    certificateHash: 'CERT_001',
    verifierId: 'VER_001',
    verifierName: 'Test Verifier',
    institutionCode: 'LIMKOWING',
    verificationMethod: 'hash'
  });
  
  console.log('Verification result:', result);
} catch (error) {
  console.error('Verification failed:', error);
}
```

### Go SDK Example

```go
package main

import (
    "fmt"
    "github.com/lgcse/fabric-sdk-go"
)

func main() {
    // Initialize SDK
    client := lgcse.NewClient("http://localhost:8000/api/v1", "your_jwt_token")
    
    // Get certificate
    cert, err := client.GetCertificate("CERT_001")
    if err != nil {
        fmt.Printf("Error: %v\n", err)
        return
    }
    
    fmt.Printf("Certificate: %+v\n", cert)
}
```

## Testing

### API Testing with Postman

Import the Postman collection from `docs/postman-collection.json`.

### Automated Testing

```bash
# Run API tests
cd tests
python3 api_tests.py

# Run performance tests
python3 performance_tests.py

# Run integration tests
python3 integration_tests.py
```

## Support

### Documentation

- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [Architecture Documentation](ARCHITECTURE.md)
- [Security Guide](SECURITY.md)
- [Performance Guide](PERFORMANCE.md)

### Contact

- **API Support**: api-support@lgcse.example.com
- **Documentation**: docs@lgcse.example.com
- **Issues**: [GitHub Issues](https://github.com/lgcse/issues)

---

**Last Updated**: December 2023
**Version**: v1.2.0
**Maintainers**: LGCSE Development Team
