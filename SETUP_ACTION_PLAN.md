# 🎯 Database Connection - Action Plan

**Status**: Your LGCSE project is now configured to connect to PostgreSQL  
**Date**: March 2, 2026  
**Location**: `/home/duckey/lgcse-project`

---

## 📋 What Was Done

✅ Fixed `.env` file - Removed invalid Prisma parameters from DATABASE_URL  
✅ Created database setup scripts (Python and Bash)  
✅ Created verification scripts to test your setup  
✅ Updated document with detailed guides  

---

## 🚀 Next Steps (Choose Your Path)

### **Path A: One-Click Setup (EASIEST)**

```bash
cd /home/duckey/lgcse-project

# Run quick setup (will ask for sudo password)
./setup_postgres_quick.sh

# Then initialize database  
cd backend && source venv/bin/activate
python scripts/setup_database.py
```

### **Path B: Verify Then Setup**

```bash
cd /home/duckey/lgcse-project

# First, verify your system is ready
python verify_database.py

# If verification passes, run setup
./setup_postgres_quick.sh
cd backend && source venv/bin/activate
python scripts/setup_database.py
```

### **Path C: Manual Setup (Most Control)**

Open a terminal and follow these exact steps:

```bash
# Step 1: Connect to PostgreSQL as admin
sudo -u postgres psql

# Step 2: Inside psql, paste these commands (one by one, press Enter after each):
CREATE USER diploma_admin WITH PASSWORD 'diploma1234' CREATEDB;
CREATE DATABASE diploma_verification OWNER diploma_admin;
GRANT ALL PRIVILEGES ON DATABASE diploma_verification TO diploma_admin;

# Exit psql
\q

# Step 3: Verify connection
export PGPASSWORD="diploma1234"
psql -U diploma_admin -h localhost -d diploma_verification -c "SELECT 1;"

# Step 4: Initialize tables
cd /home/duckey/lgcse-project/backend
source venv/bin/activate
python scripts/setup_database.py
```

---

## 📦 Available Scripts

### Quick Setup
```bash
./setup_postgres_quick.sh  # ~30 seconds
```

### Database Verification
```bash
python verify_database.py  # Checks all requirements
```

### Manual Database Initialization
```bash
cd backend
source venv/bin/activate
python scripts/postgres_setup.py  # Setup PostgreSQL
python scripts/setup_database.py   # Initialize tables
```

---

## 🧪 Testing Your Connection

After running setup, test with:

```bash
# Quick test
python verify_database.py

# Or manual test
export PGPASSWORD="diploma1234"
psql -U diploma_admin -h localhost -d diploma_verification -c "SELECT version();"
```

Expected output: PostgreSQL version information

---

## ▶️ Running Your Application

Once database is set up:

### Terminal 1 - Backend
```bash
cd /home/duckey/lgcse-project/backend
source venv/bin/activate
python main.py
```

Backend URL: `http://localhost:8000`

### Terminal 2 - Frontend
```bash
cd /home/duckey/lgcse-project/frontend
npm start
```

Frontend URL: `http://localhost:3000`

---

## 📊 Database Configuration

| Setting | Value |
|---------|-------|
| **Type** | PostgreSQL |
| **Host** | localhost |
| **Port** | 5432 |
| **Database** | diploma_verification |
| **User** | diploma_admin |
| **Password** | diploma1234 |
| **Config File** | `backend/.env` |

---

## 🔍 Troubleshooting

### PostgreSQL not installed?
```bash
sudo apt update && sudo apt install postgresql postgresql-contrib
```

### PostgreSQL not running?
```bash
sudo systemctl start postgresql
sudo systemctl status postgresql
```

### Setup script asks for sudo password?
**Use**: `Thlony57620256`

### Connection refused?
```bash
# Check if PostgreSQL is listening
sudo netstat -plnt | grep postgres
# Should show port 5432 listening
```

### Database already exists (and that's OK)?
You can still proceed with the setup - it will create tables if they don't exist.

### Permission denied errors?
Ensure you're using sudo for postgres operations:
```bash
sudo -u postgres psql  # This is correct
psql -U postgres      # This may fail
```

---

## 📁 File Locations

```
/home/duckey/lgcse-project/
├── setup_postgres_quick.sh           ← Quick setup script
├── verify_database.py                ← Verification script
├── DATABASE_CONNECTION_SUMMARY.md    ← Full setup guide
├── QUICK_DB_SETUP.md                 ← Detailed troubleshooting
├── backend/
│   ├── .env                          ← Database config (fixed!)
│   ├── scripts/
│   │   ├── postgres_setup.py         ← PostgreSQL creator
│   │   └── setup_database.py         ← Table initializer
│   ├── database.py                   ← SQLAlchemy config
│   └── models.py                     ← Database models
└── certivert_backup.sql              ← Database backup
```

---

## ✅ Pre-Check Checklist

Before running setup, verify:

- [ ] PostgreSQL is installed (`psql --version` works)
- [ ] PostgreSQL is running (`sudo systemctl status postgresql` shows active)
- [ ] You have sudo access (you can run `sudo` commands)
- [ ] `.env` file exists in `backend/` directory
- [ ] Python virtual environment is active (`source venv/bin/activate`)

---

## 📞 Need Help?

If setup fails, run the verification script for detailed diagnostics:

```bash
cd /home/duckey/lgcse-project
python verify_database.py
```

This will show exactly which step is failing.

---

## 🎉 Success Indicators

✓ `./setup_postgres_quick.sh` completes without errors  
✓ `python verify_database.py` shows all checks passing  
✓ Backend starts: `python main.py` shows "Application startup complete"  
✓ Frontend starts: `npm start` opens browser at localhost:3000  
✓ Can access database: `psql -U diploma_admin -h localhost -d diploma_verification`  

---

**Ready to proceed?** Start with:
```bash
cd /home/duckey/lgcse-project
./setup_postgres_quick.sh
```

Good luck! 🚀
