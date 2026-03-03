#!/usr/bin/env python3
"""
Quick database setup - Connect to PostgreSQL and setup the database
Run this script from the project root directory
"""

import subprocess
import sys
import os

def run_command(cmd, description=""):
    """Run a shell command and return success status"""
    if description:
        print(f"\n→ {description}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            if result.stdout.strip():
                print(f"  {result.stdout.strip()}")
            return True
        else:
            if result.stderr.strip():
                print(f"  Error: {result.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        print(f"  Timeout executing command")
        return False
    except Exception as e:
        print(f"  Exception: {e}")
        return False

def main():
    print("\n╔═══════════════════════════════════════════════════╗")
    print("║   LGCSE Project - PostgreSQL Database Setup      ║")
    print("╚═══════════════════════════════════════════════════╝")
    
    # Configuration
    DB_USER = "certivert"
    DB_PASSWORD = "certivert123"
    DB_NAME = "certivert_db"
    DB_HOST = "localhost"
    BACKUP_FILE = "backend/certivert_backup.sql"
    
    print(f"\nConfiguration:")
    print(f"  Database: {DB_NAME}")
    print(f"  User: {DB_USER}")
    print(f"  Host: {DB_HOST}")
    
    # Step 1: Check PostgreSQL
    print("\n[Step 1] Checking PostgreSQL installation...")
    if run_command("psql --version", "Checking psql version"):
        print("  ✓ PostgreSQL is installed")
    else:
        print("  ✗ PostgreSQL not found. Please install it first.")
        return False
    
    # Step 2: Check PostgreSQL service
    print("\n[Step 2] Checking PostgreSQL service...")
    if run_command("pg_isready -h localhost", "Testing PostgreSQL connection"):
        print("  ✓ PostgreSQL service is running")
    else:
        print("  ⚠ PostgreSQL may not be running. Starting...")
        run_command("sudo systemctl start postgresql", "Starting PostgreSQL")
    
    # Step 3: Create user and database
    print("\n[Step 3] Setting up database user and database...")
    
    # Create SQL commands
    sql_commands = f"""
    -- Create certivert user
    CREATE USER {DB_USER} WITH PASSWORD '{DB_PASSWORD}' CREATEDB;
    CREATE DATABASE {DB_NAME} OWNER {DB_USER};
    GRANT ALL PRIVILEGES ON DATABASE {DB_NAME} TO {DB_USER};
    \\c {DB_NAME}
    GRANT ALL ON SCHEMA public TO {DB_USER};
    """
    
    # Save to temp file
    with open('/tmp/setup_db.sql', 'w') as f:
        f.write(sql_commands)
    
    # Run as postgres user
    cmd = f"sudo -u postgres psql < /tmp/setup_db.sql 2>&1 | grep -v 'already exists' || true"
    if run_command(cmd, "Creating user and database"):
        print("  ✓ Database user and database set up")
    
    # Step 4: Restore backup
    print("\n[Step 4] Restoring database from backup...")
    if not os.path.exists(BACKUP_FILE):
        print(f"  ⚠ Backup file not found: {BACKUP_FILE}")
    else:
        restore_cmd = f"PGPASSWORD='{DB_PASSWORD}' psql -U {DB_USER} -h {DB_HOST} -d {DB_NAME} -f {BACKUP_FILE} 2>&1 | tail -5"
        if run_command(restore_cmd, "Restoring from backup"):
            print("  ✓ Database restored")
        else:
            print("  ⚠ Backup restore had issues (may be normal)")
    
    # Step 5: Verify
    print("\n[Step 5] Verifying database connection...")
    verify_cmd = f"PGPASSWORD='{DB_PASSWORD}' psql -U {DB_USER} -h {DB_HOST} -d {DB_NAME} -c 'SELECT version();' 2>&1"
    if run_command(verify_cmd, "Testing connection"):
        print("  ✓ Connection successful!")
    else:
        print("  ✗ Connection failed")
        return False
    
    # Step 6: Show tables
    print("\n[Step 6] Tables in database...")
    tables_cmd = f"PGPASSWORD='{DB_PASSWORD}' psql -U {DB_USER} -h {DB_HOST} -d {DB_NAME} -c '\\dt' 2>&1 | tail -10"
    run_command(tables_cmd)
    
    print("\n╔═══════════════════════════════════════════════════╗")
    print("║   ✓ Database Setup Complete!                     ║")
    print("╚═══════════════════════════════════════════════════╝")
    
    print("\nNext Steps:")
    print("  1. Install Python dependencies:")
    print("     cd backend && pip install -r requirements.txt")
    print("\n  2. Start the backend server:")
    print("     python main.py")
    print("\n  3. In another terminal, start the frontend:")
    print("     cd frontend && npm start")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
