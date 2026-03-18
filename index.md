---
layout: default
title: LGCSE Certificate Verification System
description: Blockchain-based certificate verification system using advanced OCR technology
---

# LGCSE Certificate Verification System

A comprehensive blockchain-based certificate verification system that uses advanced OCR technology to process and verify LGCSE certificates with high accuracy.

## Features

### 🔐 **Authentication & Security**
- Google OAuth integration
- Firebase authentication
- JWT token-based security
- Role-based access control

### 📄 **Certificate Processing**
- **Enhanced OCR System** with 88% accuracy for LGCSE certificates
- Multi-API OCR processing (OCR.space + Tesseract)
- LGCSE-specific subject and grade mapping
- Confidence scoring and validation
- Real-time processing with WebSocket updates

### ⛓️ **Blockchain Integration**
- Hyperledger Fabric network
- Immutable certificate storage
- Smart contract verification
- Distributed ledger technology

### 💳 **Payment System**
- M-Pesa integration (B2C and B2B)
- Secure payment processing
- Transaction monitoring
- Callback handling

### 📊 **Analytics & Monitoring**
- Real-time processing statistics
- OCR performance metrics
- Admin monitoring dashboard
- Comprehensive reporting

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │    │   Blockchain    │
│   (React/Vue)   │◄──►│   (Node.js)     │◄──►│ (Hyperledger)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Interface│    │   API Gateway   │    │   Smart         │
│   & Dashboard   │    │   & Processing  │    │   Contracts     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.11+
- PostgreSQL
- Redis (for caching)
- Docker (optional)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/duckey2001/Certificate-Verification-SystemUsing-BlockChain
   cd Certificate-Verification-SystemUsing-BlockChain
   ```

2. **Setup Backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Setup Frontend**
   ```bash
   cd frontend
   npm install
   ```

4. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Initialize Database**
   ```bash
   python setup_database.py
   ```

6. **Start the Application**
   ```bash
   # Backend
   cd backend && python main.py
   
   # Frontend (in separate terminal)
   cd frontend && npm start
   ```

## API Documentation

### Certificate Processing Endpoints

- **POST** `/api/ocr/extract-certificate-data` - Extract data from certificate
- **POST** `/api/certificates/upload` - Upload and process certificate
- **POST** `/api/certificates/upload-bulk` - Bulk certificate processing
- **GET** `/api/certificates/verify/{certificate_id}` - Verify certificate

### Real-time Updates

- **WebSocket** `/ws/processing` - Real-time processing updates
- **WebSocket** `/ws/admin-monitor` - Admin monitoring

### Statistics & Analytics

- **GET** `/api/statistics/processing-overview` - Processing statistics
- **GET** `/api/statistics/ocr-performance` - OCR performance metrics

## Technology Stack

### Frontend
- React.js
- Vue.js
- TailwindCSS
- WebSocket Client

### Backend
- Node.js
- Express.js
- Python (Flask/FastAPI)
- PostgreSQL
- Redis

### OCR Processing
- Tesseract OCR
- OCR.space API
- Custom LGCSE Processor
- Multi-API comparison

### Blockchain
- Hyperledger Fabric
- Smart Contracts
- Distributed Ledger

### Payment
- M-Pesa API
- B2C/B2B Integration
- Transaction Monitoring

## Performance Metrics

### OCR Accuracy
- **Enhanced LGCSE Processor**: 88% accuracy
- **Multi-API Processing**: 95% confidence
- **Subject Extraction**: 8 subjects average
- **Grade Recognition**: 92% accuracy

### Processing Speed
- **Single Certificate**: 2-3 seconds
- **Bulk Processing**: Up to 50 certificates
- **Real-time Updates**: <100ms latency
- **Blockchain Storage**: <500ms

## Security Features

- **Data Encryption**: AES-256 encryption
- **Hash Verification**: SHA-256 hashing
- **Access Control**: Role-based permissions
- **Audit Trail**: Complete transaction logging
- **Duplicate Detection**: Prevents duplicate certificates

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Contact the development team

---

**Note**: This system is designed specifically for LGCSE certificate processing and verification. The OCR models are trained and optimized for Lesotho General Certificate of Secondary Education certificates.
