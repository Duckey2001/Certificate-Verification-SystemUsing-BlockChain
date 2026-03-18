# Database Connection Setup Guide

## Quick Start

The project uses PostgreSQL for the database backend. Here's how to set it up:

### 1. Prerequisites
- PostgreSQL 16+ installed
- Python 3.8+ with psycopg2
- Backup file: `backend/certivert_backup.sql`

### 2. Configure Environment Variables

The `.env` file in the backend directory already has the correct settings:

```
DATABASE_URL=postgresql://certivert:certivert123@localhost:5432/certivert_db
```

### 3. Create Database User and Database

Run the Python setup script:

```bash
cd /home/duckey/lgcse-project
python3 setup_database.py
```

Or manually using psql:

```bash
# Connect as postgres
psql -U postgres -h localhost

# Run these commands:
CREATE USER certivert WITH PASSWORD 'certivert123' CREATEDB;
CREATE DATABASE certivert_db OWNER certivert;
GRANT ALL PRIVILEGES ON DATABASE certivert_db TO certivert;
\q
```

### 4. Restore Database Schema

```bash
# Use the backup SQL file
PGPASSWORD="certivert123" psql -U certivert -h localhost -d certivert_db -f backend/certivert_backup.sql
```

### 5. Verify Connection

Test the connection:

```bash
PGPASSWORD="certivert123" psql -U certivert -h localhost -d certivert_db -c "SELECT COUNT(*) FROM \"Certificate\";"
```

You should see the certificate count.

## Database Tables

The database contains the following tables:

- **Certificate**: Stores LGCSE certificates with grades and metadata
- **Institution**: Stores issuer and verifier institutions
- **VerificationLog**: Tracks certificate verification attempts
- **_prisma_migrations**: Migration history

## Connection String Format

For different programming languages/drivers:

```
# Node.js (pg library)
postgres://certivert:certivert123@localhost:5432/certivert_db

# Python (SQLAlchemy)
postgresql://certivert:certivert123@localhost:5432/certivert_db

# JDBC (Java)
jdbc:postgresql://localhost:5432/certivert_db

# psql command line
psql -U certivert -h localhost -d certivert_db
```

## Troubleshooting

### "FATAL: role 'postgres' does not exist"
Run psql as the postgres system user:
```bash
sudo -u postgres psql
```

### "Connection refused"
Make sure PostgreSQL service is running:
```bash
sudo systemctl status postgresql
sudo systemctl start postgresql
```

### "FATAL: password authentication failed"
Verify the password matches in `.env` file

### Restore errors
Make sure PostgreSQL can connect as the certivert user first, then restore:
```bash
PGPASSWORD="certivert123" psql -U certivert -h localhost -d certivert_db -f backend/certivert_backup.sql
```

## Backend Integration

The backend Python code (`backend/database.py`) automatically:
1. Reads the DATABASE_URL from `.env`
2. Creates SQLAlchemy engine with proper connection pooling
3. Creates all necessary tables on startup
4. Handles migrations

To start the backend after database setup:

```bash
cd backend
python main.py
```

## Frontend Integration

The Node.js frontend (`server.js`) has a separate PostgreSQL connection pool:

```javascript
const pool = new Pool({
    user: 'diploma_admin',
    host: 'localhost',
    database: 'diploma_verification',
    password: 'diploma1234',
    port: 5432,
});
```

Make sure this user exists or update to use 'certivert' instead.

## Additional Notes

- The backup file (`certivert_backup.sql`) contains sample data for testing
- Passwords should be changed in production
- Consider using environment-specific .env files
- Set up proper database backups in production
