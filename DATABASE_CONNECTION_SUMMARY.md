# Database Connection Setup Summary

## 📊 Your Project Configuration

**Project**: LGCSE Diploma Verification System  
**Location**: `/home/duckey/lgcse-project`  
**Database**: PostgreSQL  
**Status**: Ready to connect

### Current Configuration (from `.env`)

```
Database Server:  PostgreSQL on localhost:5432
Database Name:    diploma_verification
Database User:    diploma_admin
Database Pass:    diploma1234
Connection URL:   postgresql://diploma_admin:diploma1234@localhost:5432/diploma_verification
```

---

## 🚀 Quick Setup (Choose One)

### **Method 1: Automatic Setup (⭐ RECOMMENDED)**

Run this one command (will ask for sudo password):

```bash
cd /home/duckey/lgcse-project
chmod +x setup_postgres_quick.sh
./setup_postgres_quick.sh
```

Then initialize tables:

```bash
cd backend
source venv/bin/activate
python scripts/setup_database.py
```

### **Method 2: Step-By-Step Manual

**Terminal 1: Set up PostgreSQL**
```bash
# This will prompt for your sudo password
sudo -u postgres psql

# Inside psql, type these 3 commands:
CREATE USER diploma_admin WITH PASSWORD 'diploma1234' CREATEDB;
CREATE DATABASE diploma_verification OWNER diploma_admin;
GRANT ALL PRIVILEGES ON DATABASE diploma_verification TO diploma_admin;

# Exit psql
\q
```

**Terminal 2: Initialize Database Tables**
```bash
cd /home/duckey/lgcse-project/backend
source venv/bin/activate
python scripts/setup_database.py
```

### **Method 3: Using Python (No sudo needed)**

```bash
cd /home/duckey/lgcse-project/backend
source venv/bin/activate
python scripts/postgres_setup.py
python scripts/setup_database.py
```

---

## ✅ Verify Setup

### Check PostgreSQL is running:
```bash
sudo systemctl status postgresql
```

### Test database access:
```bash
export PGPASSWORD="diploma1234"
psql -U diploma_admin -h localhost -d diploma_verification -c "SELECT version();"
```

### Expected output (version check):
```
 version
─────────────────────────────────────
 PostgreSQL 16.11 on ... (Ubuntu ...)
(1 row)
```

---

## 🎯 Start Your Application

### Start Backend Server
```bash
cd /home/duckey/lgcse-project/backend
source venv/bin/activate
python main.py
```

Backend will run on: `http://localhost:8000`

### Start Frontend (in another terminal)
```bash
cd /home/duckey/lgcse-project/frontend  
npm start
```

Frontend will run on: `http://localhost:3000`

---

## 📝 Files Created/Modified

| File | Purpose |
|------|---------|
| `backend/.env` | Database connection config (FIXED) |
| `setup_postgres_quick.sh` | Quick PostgreSQL setup script |
| `backend/scripts/postgres_setup.py` | Python PostgreSQL setup |
| `backend/scripts/setup_database.py` | Initialize tables and data |
| `QUICK_DB_SETUP.md` | Detailed setup guide |

---

## 🔧 Available Commands

```bash
# Test connection
export PGPASSWORD="diploma1234"
psql -U diploma_admin -h localhost -d diploma_verification

# Backup database
pg_dump -U diploma_admin -h localhost diploma_verification > backup.sql

# View tables
psql -U diploma_admin -h localhost -d diploma_verification -c "\dt"

# View users
sudo -u postgres psql -c "\du"

# Drop database (if needed)
sudo -u postgres psql -c "DROP DATABASE diploma_verification;"
```

---

## ❌ Troubleshooting

### PostgreSQL not running
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql  # auto-start on boot
```

### Permission denied on setup
Use sudo with the password "Thlony57620256"

### Connection refused  
Make sure PostgreSQL is listening on localhost:5432
```bash
sudo netstat -plnt | grep postgres
```

### Database already exists error
The database is already created, you can proceed to the next step

### Python psycopg2 errors
```bash
cd backend
source venv/bin/activate  
pip install psycopg2-binary
```

---

## 📚 Additional Resources

- [PostgreSQL Installation Guide](https://www.postgresql.org/download/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Project README](/home/duckey/lgcse-project/README.md)

---

## ✨ What's Next?

1. ✅ Connect database (this guide)
2. ▶️ Start backend server (`python main.py`)
3. ▶️ Start frontend (`npm start`)
4. ▶️ Open http://localhost:3000 in browser
5. ▶️ Test certificate verification features

---

**Modified**: March 2, 2026  
**Status**: Database connection configured and ready for setup
