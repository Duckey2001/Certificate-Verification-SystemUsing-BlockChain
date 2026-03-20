# LGCSE Certificate Verification System - Complete Setup Checklist

## 🚀 Quick Start

### Option 1: Complete System Startup (Recommended)
```bash
./start-complete-system.sh
```

### Option 2: Manual Setup
Follow the detailed steps below if you prefer manual configuration.

---

## 📋 Prerequisites Checklist

### System Requirements
- [ ] **Node.js** (v18+)
- [ ] **Python 3** (v3.8+)
- [ ] **PostgreSQL** (v12+)
- [ ] **npm** (v8+)
- [ ] **Git**
- [ ] **curl** (for health checks)

### System Dependencies Installation
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y nodejs npm python3 python3-pip postgresql postgresql-contrib curl git

# CentOS/RHEL
sudo yum install -y nodejs npm python3 python3-pip postgresql-server postgresql-contrib curl git

# macOS (using Homebrew)
brew install node python postgresql curl git
```

---

## 🔧 Project Setup Checklist

### 1. Database Setup
- [ ] **Start PostgreSQL service**
  ```bash
  sudo systemctl start postgresql
  sudo systemctl enable postgresql
  ```

- [ ] **Create database and user**
  ```bash
  sudo -u postgres psql -c "CREATE USER certivert WITH PASSWORD 'certivert';"
  sudo -u postgres psql -c "CREATE DATABASE CertiVert OWNER certivert;"
  sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE CertiVert TO certivert;"
  ```

- [ ] **Verify database connection**
  ```bash
  psql -h localhost -U certivert -d CertiVert -c "SELECT version();"
  ```

### 2. Backend Setup (Python FastAPI)
- [ ] **Create virtual environment**
  ```bash
  cd backend
  python3 -m venv venv
  source venv/bin/activate
  ```

- [ ] **Install Python dependencies**
  ```bash
  pip install -r requirements.txt
  ```

- [ ] **Set environment variables**
  ```bash
  # Create .env file
  cp .env.example .env
  # Edit .env with your configurations
  ```

- [ ] **Test Python backend**
  ```bash
  python3 main.py
  # Should start on http://localhost:8000
  ```

### 3. Node.js Backend Setup
- [ ] **Install Node.js dependencies**
  ```bash
  cd /path/to/project/root
  npm install
  ```

- [ ] **Test Node.js backend**
  ```bash
  node server.js
  # Should start on http://localhost:5000
  ```

### 4. Frontend Setup (React)
- [ ] **Install React dependencies**
  ```bash
  cd frontend
  npm install
  ```

- [ ] **Set environment variables**
  ```bash
  # Create .env file
  cp .env.example .env
  # Edit .env with API URLs
  ```

- [ ] **Test React frontend**
  ```bash
  npm start
  # Should start on http://localhost:3000
  ```

### 5. Blockchain Setup (Hardhat)
- [ ] **Install blockchain dependencies**
  ```bash
  cd blockchain
  npm install
  ```

- [ ] **Compile smart contracts**
  ```bash
  npm run compile
  ```

- [ ] **Start Hardhat node**
  ```bash
  npm run node
  # Should start on http://localhost:8545
  ```

- [ ] **Deploy contracts**
  ```bash
  # In another terminal
  npm run deploy
  ```

---

## 🔗 Service Integration Checklist

### Environment Variables Configuration

#### Python Backend (.env)
```env
DATABASE_URL=postgresql://certivert:certivert@localhost:5432/CertiVert
SECRET_KEY=your-secret-key-here
OCR_SPACE_API_KEY=8195ce015388957
OCR_SPACE_API_URL=https://api.ocr.space/parse/image
```

#### Node.js Backend
```bash
export NODE_ENV=development
export DATABASE_URL=postgresql://certivert:certivert@localhost:5432/CertiVert
```

#### Frontend (.env)
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_NODEJS_API_URL=http://localhost:5000
REACT_APP_BLOCKCHAIN_URL=http://localhost:8545
```

### Service Communication
- [ ] **Python Backend** can connect to PostgreSQL
- [ ] **Node.js Backend** can connect to PostgreSQL
- [ ] **Frontend** can reach both backends
- [ ] **Both backends** can reach blockchain node
- [ ] **OCR.space API** is accessible (test with key)

---

## 🧪 Testing Checklist

### Health Checks
- [ ] **Python Backend Health**: `curl http://localhost:8000/health`
- [ ] **Node.js Backend Health**: `curl http://localhost:5000/health`
- [ ] **Frontend Loading**: `http://localhost:3000`
- [ ] **Blockchain RPC**: `curl http://localhost:8545`
- [ ] **Database Connection**: Test via both backends

### Feature Tests
- [ ] **User Registration/Login**
- [ ] **Certificate Upload**
- [ ] **OCR Processing**
- [ ] **Blockchain Verification**
- [ ] **Certificate Search**
- [ ] **Admin Dashboard**

### API Endpoints Testing
- [ ] **Python API Docs**: `http://localhost:8000/docs`
- [ ] **Certificate Upload Endpoint**
- [ ] **Certificate Verification Endpoint**
- [ ] **OCR Processing Endpoint**
- [ ] **Blockchain Integration Endpoint**

---

## 🔐 Security Checklist

### Authentication & Authorization
- [ ] **JWT tokens** properly configured
- [ ] **Password hashing** (bcrypt) working
- [ ] **Session management** secure
- [ ] **CORS policies** properly set

### Database Security
- [ ] **Database credentials** not hardcoded
- [ ] **SQL injection** protection active
- [ ] **Database connections** use SSL (production)

### API Security
- [ ] **Input validation** on all endpoints
- [ ] **Rate limiting** configured
- [ ] **HTTPS** enabled (production)
- [ ] **Environment variables** secured

---

## 📊 Monitoring Checklist

### Logging
- [ ] **Application logs** configured
- [ ] **Error logging** active
- [ ] **Access logs** enabled
- [ ] **Database query logs** (development)

### Health Monitoring
- [ ] **Service health endpoints** working
- [ ] **Database connection monitoring**
- [ ] **Blockchain node monitoring**
- [ ] **Frontend error tracking**

### Performance Monitoring
- [ ] **Response time monitoring**
- [ ] **Memory usage tracking**
- [ ] **Database performance**
- [ ] **OCR processing performance**

---

## 🚀 Production Deployment Checklist

### Database
- [ ] **Production database** configured
- [ ] **Database backups** scheduled
- [ ] **Connection pooling** configured
- [ ] **Database indexing** optimized

### Application Security
- [ ] **Environment variables** secured
- [ ] **HTTPS certificates** installed
- [ ] **Firewall rules** configured
- [ ] **Security headers** set

### Performance
- [ ] **Load balancing** configured
- [ ] **CDN** for static assets
- [ ] **Caching strategies** implemented
- [ ] **Database optimization** complete

### Monitoring & Alerting
- [ ] **Application monitoring** set up
- [ ] **Error alerting** configured
- [ ] **Performance monitoring** active
- [ ] **Uptime monitoring** configured

---

## 🛠️ Troubleshooting Guide

### Common Issues

#### Port Already in Use
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>

# Or use stop script
./stop-all-services.sh
```

#### Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Restart PostgreSQL
sudo systemctl restart postgresql

# Test connection
psql -h localhost -U certivert -d CertiVert
```

#### Python Dependencies Issues
```bash
# Recreate virtual environment
cd backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Node.js Dependencies Issues
```bash
# Clear npm cache
npm cache clean --force

# Remove and reinstall node_modules
rm -rf node_modules package-lock.json
npm install
```

#### Blockchain Issues
```bash
# Reset blockchain network
cd blockchain
rm -rf artifacts cache
npm run compile
npm run node
```

---

## 📞 Support Information

### Log Locations
- **Python Backend**: `logs/python-backend.log`
- **Node.js Backend**: `logs/nodejs-backend.log`
- **Frontend**: `logs/frontend.log`
- **Blockchain**: `logs/blockchain.log`
- **Deployment**: `logs/deployment.log`

### Process IDs
- **Python Backend**: `pids/python-backend.pid`
- **Node.js Backend**: `pids/nodejs-backend.pid`
- **Frontend**: `pids/frontend.pid`
- **Blockchain**: `pids/blockchain.pid`

### Service URLs
- **Python Backend**: `http://localhost:8000`
- **Node.js Backend**: `http://localhost:5000`
- **Frontend**: `http://localhost:3000`
- **Blockchain**: `http://localhost:8545`
- **API Docs**: `http://localhost:8000/docs`

---

## ✅ Final Verification

Before going live, ensure:

- [ ] All services start without errors
- [ ] All health checks pass
- [ ] Database connections work
- [ ] OCR functionality works
- [ ] Blockchain integration works
- [ ] Frontend loads properly
- [ ] User authentication works
- [ ] Certificate upload/verification works
- [ ] Admin dashboard functions
- [ ] Monitoring and logging are active

---

## 🎉 Success!

Once all checklist items are complete, your LGCSE Certificate Verification System should be fully operational!

**For quick startup:** `./start-complete-system.sh`
**For stopping services:** `./stop-all-services.sh`
