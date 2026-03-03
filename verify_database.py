#!/usr/bin/env python3
"""
Database Connection Verification Script
Tests that your PostgreSQL database is properly configured
"""

import os
import sys
import subprocess
from pathlib import Path

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_success(text):
    print(f"✓ {text}")

def print_error(text):
    print(f"✗ {text}")

def print_info(text):
    print(f"ℹ {text}")

def run_command(cmd, shell=True):
    """Run a command and return (success, output, error)"""
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timeout"
    except Exception as e:
        return False, "", str(e)

def main():
    print_header("LGCSE Database Connection Verification")
    
    # Configuration
    db_user = "diploma_admin"
    db_password = "diploma1234"
    db_name = "diploma_verification"
    db_host = "localhost"
    db_port = "5432"
    
    # Step 1: Check PostgreSQL installation
    print_header("Step 1: PostgreSQL Installation")
    success, output, error = run_command("psql --version")
    
    if success:
        version_line = output.strip()
        print_success(f"PostgreSQL installed: {version_line}")
    else:
        print_error("PostgreSQL not installed")
        print_info("Install with: sudo apt-get install postgresql")
        return False
    
    # Step 2: Check PostgreSQL service
    print_header("Step 2: PostgreSQL Service Status")
    success, output, error = run_command("pg_isready -h localhost -p 5432")
    
    if success:
        print_success("PostgreSQL service is running and accepting connections")
    else:
        print_error("PostgreSQL not accepting connections")
        print_info("Start with: sudo systemctl start postgresql")
        return False
    
    # Step 3: Check environment file
    print_header("Step 3: Environment Configuration")
    env_file = Path("backend/.env")
    
    if env_file.exists():
        print_success(f"Environment file found: {env_file}")
        
        # Check DATABASE_URL
        with open(env_file) as f:
            for line in f:
                if line.startswith("DATABASE_URL"):
                    db_url = line.split("=", 1)[1].strip().strip('"')
                    if "diploma_verification" in db_url:
                        print_success(f"DATABASE_URL configured correctly")
                        print_info(f"Connection: {db_url}")
                    else:
                        print_error(f"DATABASE_URL may be incorrect")
                    break
    else:
        print_error(f"Environment file not found: {env_file}")
        return False
    
    # Step 4: Test database connection
    print_header("Step 4: Database Connection Test")
    
    cmd = f'PGPASSWORD="{db_password}" psql -U {db_user} -h {db_host} -d {db_name} -c "SELECT 1;" 2>&1'
    success, output, error = run_command(cmd)
    
    if success:
        print_success(f"Database connection successful!")
        print_info(f"Database: {db_name}")
        print_info(f"User: {db_user}")
        print_info(f"Host: {db_host}:{db_port}")
    else:
        if "does not exist" in error:
            print_error(f"Database '{db_name}' does not exist")
            print_info("Create with: sudo -u postgres psql -c 'CREATE DATABASE diploma_verification OWNER diploma_admin;'")
        elif "does not exist" in error and "role" in error:
            print_error(f"User '{db_user}' does not exist")
            print_info("Create with: sudo -u postgres psql -c \"CREATE USER diploma_admin WITH PASSWORD 'diploma1234';\"")
        elif "password authentication failed" in error:
            print_error("Password authentication failed")
            print_info("Check password in .env file")
        else:
            print_error(f"Connection failed: {error[:100]}")
        
        print_info("\nTo set up database, run:")
        print_info("  ./setup_postgres_quick.sh")
        return False
    
    # Step 5: Check database tables
    print_header("Step 5: Database Tables")
    
    cmd = f'PGPASSWORD="{db_password}" psql -U {db_user} -h {db_host} -d {db_name} -c "\\dt" 2>&1'
    success, output, error = run_command(cmd)
    
    if success and output.strip():
        table_lines = [l for l in output.split('\n') if '|' in l]
        if len(table_lines) > 2:
            print_success(f"Database has tables ({len(table_lines)-2} found)")
            print("\nTables:")
            for line in table_lines[:10]:  # Show first 10
                print(f"  {line}")
        else:
            print_info("No tables found (database may be empty)")
    else:
        print_info("Could not list tables")
    
    # Step 6: Check Python dependencies
    print_header("Step 6: Python Dependencies")
    
    # Check for venv
    venv_path = Path("backend/venv")
    if venv_path.exists():
        print_success(f"Virtual environment found: {venv_path}")
    else:
        print_error(f"Virtual environment not found")
        return False
    
    # Check psycopg2
    activator = "backend/venv/bin/activate"
    cmd = f"source {activator} && python -c 'import psycopg2; print(psycopg2.__version__)' 2>&1"
    success, output, error = run_command(cmd)
    
    if success:
        print_success(f"psycopg2 installed (version {output.strip()})")
    else:
        print_error("psycopg2 not installed")
        print_info("Install with: pip install psycopg2-binary")
        return False
    
    # Check sqlalchemy
    cmd = f"source {activator} && python -c 'import sqlalchemy; print(sqlalchemy.__version__)' 2>&1"
    success, output, error = run_command(cmd)
    
    if success:
        print_success(f"SQLAlchemy installed (version {output.strip()})")
    else:
        print_error("SQLAlchemy not installed")
    
    # Final summary
    print_header("Verification Complete ✓")
    print("\nYour system is ready to run the LGCSE application!")
    print("\nNext steps:")
    print("  1. cd backend")
    print("  2. source venv/bin/activate")
    print("  3. python scripts/setup_database.py  (if tables don't exist)")
    print("  4. python main.py")
    print("\nIn another terminal:")
    print("  1. cd frontend")
    print("  2. npm start")
    print("\nThen open: http://localhost:3000")
    
    return True

if __name__ == "__main__":
    os.chdir(Path(__file__).parent)
    
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n✗ Verification interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
