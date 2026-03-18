# 🗄️ Database Connection Guide

## Quick Start

Your LGCSE project is configured to use **PostgreSQL**. Follow these steps to connect it:

### Configuration Details

```
Database: diploma_verification
User: diploma_admin  
Password: diploma1234
Host: localhost:5432
Connection: postgresql://diploma_admin:diploma1234@localhost:5432/diploma_verification
```

---

## ✅ Setup Options

### **Option A: Automatic Setup (RECOMMENDED)**

The easiest way - the system will handle everything:

```bash
cd /home/duckey/lgcse-project/backend
source venv/bin/activate

# This creates the PostgreSQL user and database
python scripts/postgres_setup.py

# This initializes tables and default data  
python scripts/setup_database.py
```

### **Option B: Manual Setup with psql**

If you prefer to set up manually, open a terminal and run:

```bash
# 1. Enter PostgreSQL as the root user
sudo -u postgres psql

# 2. Inside psql, paste these commands:
CREATE USER diploma_admin WITH PASSWORD 'diploma1234' CREATEDB;
CREATE DATABASE diploma_verification OWNER diploma_admin;
GRANT ALL PRIVILEGES ON DATABASE diploma_verification TO diploma_admin;
\q

# 3. Verify the connection
export PGPASSWORD="diploma1234"
psql -U diploma_admin -h localhost -d diploma_verification -c "SELECT 1;"
```

### **Option C: Using Docker (if PostgreSQL not installed)**

```bash
# Start a PostgreSQL container
docker run --name lgcse-postgres \
  -e POSTGRES_USER=diploma_admin \
  -e POSTGRES_PASSWORD=diploma1234 \
  -e POSTGRES_DB=diploma_verification \
  -p 5432:5432 \
  -d postgres:16

# Then run the setup scripts as in Option A
```

---

## 🚀 Next Steps (After Database Setup)

### 1. **Start the Backend Server**

```bash
cd /home/duckey/lgcse-project/backend
source venv/bin/activate
python main.py
```

The backend will run on `http://localhost:8000`

### 2. **Start the Frontend**

```bash
cd /home/duckey/lgcse-project/frontend
npm start
```

The frontend will run on `http://localhost:3000`

### 3. **Test the API**

```bash
# Check if backend is running
curl http://localhost:8000/health

# Or use the test file
cd /home/duckey/lgcse-project/backend
python test_api.py
```

---

## 🔍 Verification Commands

### Check PostgreSQL is running:
```bash
sudo systemctl status postgresql
```

### Test database connection:
```bash
export PGPASSWORD="diploma1234"
psql -U diploma_admin -h localhost -d diploma_verification -c "SELECT version();"
```

### List tables in database:
```bash
export PGPASSWORD="diploma1234"
psql -U diploma_admin -h localhost -d diploma_verification -c "\dt"
```

### View database users:
```bash
sudo -u postgres psql -c "\du"
```

---

## 🐛 Troubleshooting

### ❌ "connection refused" 
PostgreSQL is not running:
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql  # Auto-start on boot
```

### ❌ "FATAL: role 'diploma_admin' does not exist"
The user wasn't created. Run:
```bash
sudo -u postgres psql -c "CREATE USER diploma_admin WITH PASSWORD 'diploma1234' CREATEDB;"
```

### ❌ "FATAL: database 'diploma_verification' does not exist"
The database wasn't created. Run:
```bash
sudo -u postgres psql -c "CREATE DATABASE diploma_verification OWNER diploma_admin;"
```

### ❌ "permission denied" on database creation
Grant permissions:
```bash
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE diploma_verification TO diploma_admin;"
```

### ❌ "psycopg2.ProgrammingError: invalid dsn"
The .env file has invalid database URL. Fix it:
```
DATABASE_URL=postgresql://diploma_admin:diploma1234@localhost:5432/diploma_verification
```
(No `?schema=public` at the end)

---

## 📁 Important Files

- **Configuration**: `/home/duckey/lgcse-project/backend/.env`
- **Setup Scripts**: `/home/duckey/lgcse-project/backend/scripts/`
- **Database Backup**: `/home/duckey/lgcse-project/backend/certivert_backup.sql`
- **Models**: `/home/duckey/lgcse-project/backend/models.py`
- **Database Module**: `/home/duckey/lgcse-project/backend/database.py`

---

## 📚 More Information

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Project README](../README.md)

---

**Need help?** Check the logs in your terminal or file an issue!
