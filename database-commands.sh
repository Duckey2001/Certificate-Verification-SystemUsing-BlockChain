#!/bin/bash

# LGCSE Certificate Verification System - Database Setup Commands
# This script provides all database-related commands for PostgreSQL and SQLite

echo "LGCSE Certificate Verification System - Database Commands"
echo "========================================================="
echo ""

# Project directories
PROJECT_ROOT="/home/duckey/lgcse-project"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo "Project Root: $PROJECT_ROOT"
echo "Backend Directory: $BACKEND_DIR"
echo ""

echo "DATABASE SETUP OPTIONS"
echo "====================="
echo ""

echo "1. POSTGRESQL SETUP (Recommended for Production)"
echo "=============================================="
echo ""

echo "# Install PostgreSQL (Ubuntu/Debian)"
echo "sudo apt update"
echo "sudo apt install postgresql postgresql-contrib"
echo ""

echo "# Start PostgreSQL service"
echo "sudo systemctl start postgresql"
echo "sudo systemctl enable postgresql"
echo ""

echo "# Create database and user"
echo "sudo -u postgres psql -c \"CREATE USER lgcsedb WITH PASSWORD 'lgcsedb123';\""
echo "sudo -u postgres psql -c \"CREATE DATABASE lgcsedb OWNER lgcsedb;\""
echo "sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE lgcsedb TO lgcsedb;\""
echo ""

echo "# Alternative database name (certivert)"
echo "sudo -u postgres psql -c \"CREATE USER certivert WITH PASSWORD 'certivert123';\""
echo "sudo -u postgres psql -c \"CREATE DATABASE certivert OWNER certivert;\""
echo "sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE certivert TO certivert;\""
echo ""

echo "# Test database connection"
echo "psql -h localhost -p 5432 -U lgcsedb -d lgcsedb"
echo "# or"
echo "psql -h localhost -p 5432 -U certivert -d certivert"
echo ""

echo "2. AUTOMATED DATABASE SETUP"
echo "=========================="
echo ""

echo "# Run automated database setup script"
echo "cd $BACKEND_DIR"
echo "source venv/bin/activate"
echo "python3 setup_database.py"
echo ""

echo "# Alternative quick setup"
echo "cd $PROJECT_ROOT"
echo "./setup_postgres_quick.sh"
echo ""

echo "3. SQLITE SETUP (Development/Testing)"
echo "===================================="
echo ""

echo "# SQLite is used as fallback - no installation needed"
echo "# Database file will be created automatically: certivert.db"
echo "cd $BACKEND_DIR"
echo "ls -la *.db"
echo ""

echo "4. DATABASE CONFIGURATION"
echo "========================="
echo ""

echo "# Backend environment configuration"
echo "cd $BACKEND_DIR"
echo "cp .env.example .env"
echo ""
echo "# Edit .env file with database settings:"
echo "# For PostgreSQL:"
echo "DATABASE_URL=postgresql://lgcsedb:lgcsedb123@localhost:5432/lgcsedb"
echo "# or"
echo "DATABASE_URL=postgresql://certivert:certivert123@localhost:5432/certivert"
echo ""
echo "# For SQLite (fallback):"
echo "DATABASE_URL=sqlite:///./certivert.db"
echo ""

echo "5. DATABASE VERIFICATION"
echo "======================="
echo ""

echo "# Check PostgreSQL status"
echo "sudo systemctl status postgresql"
echo ""

echo "# Test database connection from backend"
echo "cd $BACKEND_DIR"
echo "source venv/bin/activate"
echo "python3 verify_database.py"
echo ""

echo "# Quick connection test"
echo "cd $PROJECT_ROOT"
echo "node test-connection.js"
echo ""

echo "6. DATABASE MANAGEMENT COMMANDS"
echo "=============================="
echo ""

echo "# Connect to PostgreSQL database"
echo "psql -h localhost -p 5432 -U lgcsedb -d lgcsedb"
echo ""

echo "# List all databases"
echo "sudo -u postgres psql -l"
echo ""

echo "# Backup database"
echo "pg_dump -h localhost -p 5432 -U lgcsedb lgcsedb > lgcsedb_backup.sql"
echo ""

echo "# Restore database"
echo "psql -h localhost -p 5432 -U lgcsedb lgcsedb < lgcsedb_backup.sql"
echo ""

echo "# Reset database (fresh start)"
echo "cd $BACKEND_DIR"
echo "source venv/bin/activate"
echo "python3 reset_db.py"
echo ""

echo "7. PRISMA DATABASE COMMANDS (if using Prisma ORM)"
echo "=============================================="
echo ""

echo "# Generate Prisma client"
echo "cd $PROJECT_ROOT"
echo "npx prisma generate"
echo ""

echo "# Run database migrations"
echo "npx prisma migrate deploy"
echo ""

echo "# Reset database (Prisma)"
echo "npx prisma migrate reset --force"
echo ""

echo "# View database in Prisma Studio"
echo "npx prisma studio"
echo ""

echo "8. TROUBLESHOOTING"
echo "================="
echo ""

echo "# If PostgreSQL connection fails:"
echo "sudo systemctl restart postgresql"
echo "sudo systemctl status postgresql"
echo ""
echo "# Check PostgreSQL logs"
echo "sudo tail -f /var/log/postgresql/postgresql-*-main.log"
echo ""
echo "# Check if database exists"
echo "sudo -u postgres psql -l | grep lgcsedb"
echo ""
echo "# Create database manually if needed"
echo "sudo -u postgres createdb lgcsedb"
echo ""

echo "9. ENVIRONMENT VARIABLES"
echo "======================"
echo ""

echo "# Required environment variables for backend/.env:"
echo "DATABASE_URL=postgresql://lgcsedb:lgcsedb123@localhost:5432/lgcsedb"
echo "SECRET_KEY=your-secret-key-here"
echo "ISSUER_PRIVATE_KEY=0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"
echo "CERT_REGISTRY_ADDRESS=auto-detected-after-deployment"
echo "HARDHAT_RPC_URL=http://127.0.0.1:8545"
echo ""

echo "10. QUICK START SEQUENCE"
echo "======================"
echo ""
echo "# Complete database setup sequence:"
echo "1. Install PostgreSQL: sudo apt install postgresql postgresql-contrib"
echo "2. Start service: sudo systemctl start postgresql"
echo "3. Create database: sudo -u postgres psql -c 'CREATE DATABASE lgcsedb;'"
echo "4. Create user: sudo -u postgres psql -c 'CREATE USER lgcsedb WITH PASSWORD lgcsedb123;'"
echo "5. Grant privileges: sudo -u postgres psql -c 'GRANT ALL PRIVILEGES ON DATABASE lgcsedb TO lgcsedb;'"
echo "6. Configure backend: cd $BACKEND_DIR && cp .env.example .env"
echo "7. Edit .env with database URL"
echo "8. Test connection: cd $BACKEND_DIR && source venv/bin/activate && python3 verify_database.py"
echo ""

echo "DATABASE STATUS CHECK"
echo "===================="
echo ""

# Check if PostgreSQL is running
if command -v pgrep > /dev/null && pgrep -x postgres > /dev/null; then
    echo "✓ PostgreSQL is running"
    echo "  Process ID: $(pgrep -x postgres)"
else
    echo "✗ PostgreSQL is not running"
    echo "  Start with: sudo systemctl start postgresql"
fi

# Check if database exists
if command -v psql > /dev/null; then
    echo ""
    echo "Available databases:"
    sudo -u postgres psql -l 2>/dev/null | grep -E "(lgcsedb|certivert)" || echo "  No LGCSE databases found"
fi

# Check SQLite database files
if [ -f "$BACKEND_DIR/certivert.db" ]; then
    echo ""
    echo "✓ SQLite database found: $BACKEND_DIR/certivert.db"
    echo "  Size: $(du -h "$BACKEND_DIR/certivert.db" | cut -f1)"
fi

echo ""
echo "For automated database setup, run:"
echo "cd $BACKEND_DIR && source venv/bin/activate && python3 setup_database.py"
