# ✅ Database Connection - Success Reference

This document shows what your system should display when database connection is working correctly.

---

## 1️⃣ Running Verification Script

### Command
```bash
cd /home/duckey/lgcse-project
python verify_database.py
```

### Expected Output (SAMPLE)
```
============================================================
  LGCSE Database Connection Verification
============================================================

============================================================
  Step 1: PostgreSQL Installation
============================================================

✓ PostgreSQL installed: psql (PostgreSQL) 16.11 (Ubuntu 16.11-0ubuntu0.24.04.1)

============================================================
  Step 2: PostgreSQL Service Status
============================================================

✓ PostgreSQL service is running and accepting connections

============================================================
  Step 3: Environment Configuration
============================================================

✓ Environment file found: backend/.env
✓ DATABASE_URL configured correctly
ℹ Connection: postgresql://diploma_admin:diploma1234@localhost:5432/diploma_verification

============================================================
  Step 4: Database Connection Test
============================================================

✓ Database connection successful!
ℹ Database: diploma_verification
ℹ User: diploma_admin
ℹ Host: localhost:5432

============================================================
  Step 5: Database Tables
============================================================

✓ Database has tables (5 found)

Tables:
  | public | Certificate | table | diploma_admin |
  | public | Institution | table | diploma_admin |
  | public | VerificationLog | table | diploma_admin |

============================================================
  Step 6: Python Dependencies
============================================================

✓ Virtual environment found: backend/venv
✓ psycopg2 installed (version 2.9.9)
✓ SQLAlchemy installed (version 2.0.23)

============================================================
  Verification Complete ✓
============================================================

Your system is ready to run the LGCSE application!

Next steps:
  1. cd backend
  2. source venv/bin/activate
  3. python scripts/setup_database.py  (if tables don't exist)
  4. python main.py

In another terminal:
  1. cd frontend
  2. npm start

Then open: http://localhost:3000
```

---

## 2️⃣ Running Setup Script

### Command
```bash
./setup_postgres_quick.sh
```

### Expected Output (SAMPLE)
```
╔════════════════════════════════════════╗
║  LGCSE Database Setup                  ║
║  PostgreSQL Configuration              ║
╚════════════════════════════════════════╝

Configuration:
  User: diploma_admin
  Database: diploma_verification
  Host: localhost:5432

Creating PostgreSQL user...
✓ User created
Creating database...
✓ Database created
Granting privileges...
✓ Privileges configured

Verifying connection...
✓ Connection successful!

════════════════════════════════════════
✓ PostgreSQL setup complete!
════════════════════════════════════════

Next steps:
1. Initialize tables: cd backend && python scripts/setup_database.py
2. Start backend: python main.py
```

---

## 3️⃣ Initializing Database Tables

### Command
```bash
cd backend
source venv/bin/activate
python scripts/setup_database.py
```

### Expected Output (SAMPLE)
```
🔧 Creating database tables...
✅ Tables created successfully

👤 Setting up admin user...
✅ Admin user created: letsapobokang.certivert@gmail.com

🏢 Creating institutions...
✅ Institutions created (ECOL, LUCT, NUL, LP)

📊 Creating sample certificates...
✅ Sample certificates added

🔐 Creating audit events...
✅ Audit events logged

✨ Database initialization complete!
```

---

## 4️⃣ Starting Backend Server

### Command
```bash
cd backend
source venv/bin/activate
python main.py
```

### Expected Output (SAMPLE)
```
2026-03-02 18:45:23 - INFO - Starting LGCSE Backend Server
2026-03-02 18:45:23 - INFO - Loading environment variables from .env
2026-03-02 18:45:23 - INFO - Database URL: postgresql://diploma_admin:****@localhost:5432/diploma_verification
2026-03-02 18:45:23 - INFO - Connecting to database...
2026-03-02 18:45:23 - INFO - ✓ Database connection successful
2026-03-02 18:45:24 - INFO - Flask app initialized
2026-03-02 18:45:24 - INFO - CORS configured
2026-03-02 18:45:24 - INFO - Blueprint routes registered

 * Serving Flask app 'app'
 * Debug mode: on
 * Running on http://127.0.0.1:8000
 * WARNING: This is a development server. Do not use it in production.
 * Press CTRL+C to quit
```

Backend is ready at: **http://localhost:8000**

---

## 5️⃣ Starting Frontend

### Command (in another terminal)
```bash
cd frontend
npm start
```

### Expected Output (SAMPLE)
```
> lgcse-diploma-system@1.0.0 start
> react-scripts start

webpack compiled successfully
Compiled successfully!

You can now view lgcse-diploma-system in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.x.x:3000

Note that the development build is not optimized.
To create a production build, use npm run build.

webpack compiled successfully
```

Frontend is ready at: **http://localhost:3000**

---

## 6️⃣ Testing Database Connection

### Command
```bash
export PGPASSWORD="diploma1234"
psql -U diploma_admin -h localhost -d diploma_verification -c "SELECT version();"
```

### Expected Output
```
                          version
─────────────────────────────────────────────────────────
 PostgreSQL 16.11 on x86_64-pc-linux-gnu, compiled by g...
(1 row)
```

---

## 7️⃣ Checking Database Tables

### Command
```bash
export PGPASSWORD="diploma1234"
psql -U diploma_admin -h localhost -d diploma_verification -c "\dt"
```

### Expected Output
```
                   List of relations
 Schema |        Name         | Type  |    Owner
────────┼─────────────────────┼───────┼──────────────
 public | Certificate         | table | diploma_admin
 public | Institution         | table | diploma_admin
 public | VerificationLog     | table | diploma_admin
 public | _prisma_migrations  | table | diploma_admin
(4 rows)
```

---

## 8️⃣ Testing API Endpoint

### Command
```bash
curl -s http://localhost:8000/health | python -m json.tool
```

### Expected Output
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2026-03-02T18:50:00Z"
}
```

---

## 🎯 Common Error Messages & Solutions

### ❌ "psql: could not connect to server"
**Solution**: PostgreSQL not running
```bash
sudo systemctl start postgresql
```

### ❌ "FATAL: role 'diploma_admin' does not exist"
**Solution**: User not created
```bash
sudo -u postgres psql -c "CREATE USER diploma_admin WITH PASSWORD 'diploma1234' CREATEDB;"
```

### ❌ "FATAL: password authentication failed"
**Solution**: Wrong password - check `.env` file

### ❌ "ERROR:  database 'diploma_verification' does not exist"
**Solution**: Database not created
```bash
sudo -u postgres psql -c "CREATE DATABASE diploma_verification OWNER diploma_admin;"
```

### ❌ "psycopg2.ProgrammingError: invalid dsn"
**Solution**: Invalid DATABASE_URL format
- CORRECT: `postgresql://user:pass@localhost:5432/dbname`
- WRONG: `postgresql://user:pass@localhost:5432/dbname?schema=public`

---

## 📝 Checklist for Success

- [ ] `Python verify_database.py` shows ✓ for all steps
- [ ] `./setup_postgres_quick.sh` completes successfully
- [ ] `python scripts/setup_database.py` shows database tables created
- [ ] `python main.py` starts backend server
- [ ] `npm start` starts frontend application
- [ ] `http://localhost:3000` opens in browser
- [ ] Can access API endpoints (e.g., `/health`)
- [ ] Database tables are visible with `psql`

---

## 🎉 When Everything Works

You should be able to:

1. ✅ Open http://localhost:3000 in your browser
2. ✅ See the LGCSE Dashboard
3. ✅ Log in with demo credentials
4. ✅ Verify certificates
5. ✅ View uploaded documents
6. ✅ Check blockchain integration

---

**Status**: Ready to deploy! 🚀

For troubleshooting, see: [Detailed Setup Guide](QUICK_DB_SETUP.md)
