#!/usr/bin/env python3
"""
PostgreSQL Setup - Creates user and database before application startup
"""

import subprocess
import sys
import os

def run_psql_as_postgres(sql_command):
    """Run a SQL command as the postgres user"""
    try:
        cmd = ['sudo', '-u', 'postgres', 'psql', '-c', sql_command]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return 1, "", "Command timeout"
    except Exception as e:
        return 1, "", str(e)

def main():
    print("\n" + "="*70)
    print("PostgreSQL Database Setup - LGCSE Diploma Verification System")
    print("="*70 + "\n")
    
    # Configuration
    db_user = "diploma_admin"
    db_password = "diploma1234"
    db_name = "diploma_verification"
    
    print(f"Creating PostgreSQL user: {db_user}")
    print(f"Creating database: {db_name}\n")
    
    # Step 1: Create user
    print("Step 1: Creating PostgreSQL user...")
    create_user_sql = f"CREATE USER {db_user} WITH PASSWORD '{db_password}' CREATEDB;"
    ret, out, err = run_psql_as_postgres(create_user_sql)
    
    if ret == 0 or "already exists" in err:
        print(f"  ✓ User '{db_user}' ready")
    else:
        print(f"  ✗ Error: {err}")
        return False
    
    # Step 2: Create database
    print("Step 2: Creating PostgreSQL database...")
    create_db_sql = f"CREATE DATABASE {db_name} OWNER {db_user};"
    ret, out, err = run_psql_as_postgres(create_db_sql)
    
    if ret == 0 or "already exists" in err:
        print(f"  ✓ Database '{db_name}' ready")
    else:
        print(f"  ✗ Error: {err}")
        return False
    
    # Step 3: Grant privileges
    print("Step 3: Granting privileges...")
    grant_sql = f"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {db_user};"
    ret, out, err = run_psql_as_postgres(grant_sql)
    
    if ret == 0:
        print(f"  ✓ Privileges granted")
    else:
        print(f"  ✗ Error: {err}")
        return False
    
    # Success
    print("\n" + "="*70)
    print("✓ PostgreSQL setup complete!")
    print("="*70)
    print(f"\nYou can now run: python scripts/setup_database.py")
    print("This will initialize the database tables and data.\n")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n✗ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)
