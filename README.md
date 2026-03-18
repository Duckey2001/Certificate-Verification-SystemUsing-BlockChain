# CertiVert Project

A certificate verification system with blockchain integration.

## Project Structure

- **backend/**: FastAPI backend server
- **frontend/**: React frontend application
- **blockchain/**: Hardhat blockchain contracts

## Installation

### Quick Installation (All Dependencies)

Run the installation script to install all dependencies:

```bash
./install.sh
```

This will install:
- ✅ Python backend dependencies (FastAPI, SQLAlchemy, etc.)
- ✅ React frontend dependencies (React, Axios, Router, etc.)
- ✅ Blockchain dependencies (Hardhat, OpenZeppelin, etc.)

### Manual Installation

#### Python Backend Dependencies

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### React Frontend Dependencies

```bash
cd frontend
npm install
```

#### Blockchain Dependencies

```bash
cd blockchain
npm install
```

## Quick Start

### Option 1: Using the startup script (Recommended)

```bash
./start.sh
```

This will start both backend and frontend servers automatically.

### Option 2: Manual startup

#### Backend

```bash
cd backend
source venv/bin/activate  # or: venv\Scripts\activate on Windows
pip install -r requirements.txt
python3 main.py
```

Backend will run on `http://localhost:8000`
API documentation available at `http://localhost:8000/docs`

#### Frontend

```bash
cd frontend
npm install
npm start
```

Frontend will run on `http://localhost:3000`

## Fixed Issues

1. ✅ Updated `requirements.txt` - Replaced Flask dependencies with FastAPI dependencies
2. ✅ Created `database.py` - Database connection and session management
3. ✅ Created `auth.py` - Authentication and authorization utilities
4. ✅ Fixed imports in `main.py` - Updated to use new database module
5. ✅ Verified all dependencies are installed correctly
6. ✅ Tested backend startup and imports

## Dependencies

### Backend
- FastAPI
- SQLAlchemy
- Python-JOSE (JWT)
- Passlib (password hashing)
- Pytesseract (OCR)
- Pillow (image processing)

### Frontend
- React 18.2.0+
- React Router DOM 6.20.1+
- Axios 1.13.4+
- React Scripts 5.0.1+

### Blockchain
- Hardhat 2.22.0+
- @nomicfoundation/hardhat-toolbox 4.0.0+
- @openzeppelin/contracts 5.4.0+

## Environment Variables

Create a `.env` file in the `backend/` directory:

```env
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///./certivert.db
```

## API Endpoints

- `GET /` - API welcome message
- `GET /health` - Health check
- `POST /token` - Login (OAuth2)
- `POST /register` - User registration
- `POST /api/certificates/upload` - Upload certificate
- `GET /api/certificates/{hash}` - Get certificate by hash
- `POST /api/certificates/verify` - Verify certificate

## Google OAuth Login

The application supports Google OAuth login. To enable it:

1. Follow the setup guide in `GOOGLE_OAUTH_SETUP.md`
2. Configure Google OAuth credentials in Google Cloud Console
3. Add environment variables to `backend/.env` and `frontend/.env`
4. Restart both servers

See `GOOGLE_OAUTH_SETUP.md` for detailed instructions.

## Notes

- The backend uses SQLite for development (database file: `certivert.db`)
- OCR functionality requires Tesseract to be installed on the system
- PDF processing requires poppler-utils (for pdf2image)
- Google OAuth requires configuration before use (see `GOOGLE_OAUTH_SETUP.md`)
