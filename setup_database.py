#!/usr/bin/env python3
"""
Database Setup Script for LGCSE Certificate Verification System
"""

import psycopg2
from psycopg2 import sql
import os
from pathlib import Path

# Database configuration
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'postgres',
    'user': 'postgres',
    'password': 'Thlony57620256'
}

NEW_USER = 'certivert'
NEW_PASSWORD = 'certivert123'
NEW_DB = 'certivert_db'
BACKUP_FILE = 'backend/certivert_backup.sql'

def connect_postgres():
    """Connect to PostgreSQL as postgres user"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return None

def create_user_and_db(conn):
    """Create user and database"""
    cursor = conn.cursor()
    try:
        # Create user
        print("Creating user 'certivert'...")
        cursor.execute(f"""
            CREATE USER {NEW_USER} WITH PASSWORD '{NEW_PASSWORD}' CREATEDB;
        """)
        print(f"✓ User '{NEW_USER}' created")
    except psycopg2.errors.DuplicateObject:
        print(f"✓ User '{NEW_USER}' already exists")
    except Exception as e:
        print(f"⚠ User creation: {e}")
    
    try:
        # Create database
        print(f"Creating database '{NEW_DB}'...")
        cursor.execute(f"""
            CREATE DATABASE {NEW_DB} OWNER {NEW_USER};
        """)
        print(f"✓ Database '{NEW_DB}' created")
    except psycopg2.errors.DuplicateDatabase:
        print(f"✓ Database '{NEW_DB}' already exists")
    except Exception as e:
        print(f"⚠ Database creation: {e}")
    
    try:
        # Grant privileges
        print(f"Granting privileges...")
        cursor.execute(f"""
            GRANT ALL PRIVILEGES ON DATABASE {NEW_DB} TO {NEW_USER};
        """)
        print(f"✓ Privileges granted")
    except Exception as e:
        print(f"⚠ Privileges: {e}")
    
    cursor.close()

def restore_backup(backup_file):
    """Restore database from backup"""
    if not os.path.exists(backup_file):
        print(f"❌ Backup file not found: {backup_file}")
        return False
    
    restore_config = {
        'host': 'localhost',
        'port': 5432,
        'database': NEW_DB,
        'user': NEW_USER,
        'password': NEW_PASSWORD
    }
    
    try:
        print(f"\nRestoring from backup: {backup_file}")
        conn = psycopg2.connect(**restore_config)
        cursor = conn.cursor()
        
        with open(backup_file, 'r') as f:
            backup_sql = f.read()
            # Remove the restrict/unrestrict lines
            backup_sql = backup_sql.replace('\\restrict', '--').replace('\\unrestrict', '--')
            cursor.execute(backup_sql)
        
        conn.commit()
        cursor.close()
        conn.close()
        print("✓ Backup restored successfully")
        return True
    except Exception as e:
        print(f"⚠ Backup restore error: {e}")
        return False

def verify_connection():
    """Verify database connection"""
    test_config = {
        'host': 'localhost',
        'port': 5432,
        'database': NEW_DB,
        'user': NEW_USER,
        'password': NEW_PASSWORD
    }
    
    try:
        conn = psycopg2.connect(**test_config)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        print(f"\n✓ Database connection successful")
        print(f"  PostgreSQL: {version[0][:50]}...")
        
        # List tables
        cursor.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema='public'
        """)
        tables = cursor.fetchall()
        print(f"  Tables: {', '.join([t[0] for t in tables]) if tables else 'None'}")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Connection verification failed: {e}")
        return False

def main():
    print("=" * 50)
    print("LGCSE Database Setup")
    print("=" * 50)
    
    # Step 1: Connect to PostgreSQL
    print("\n[1/4] Connecting to PostgreSQL...")
    conn = connect_postgres()
    if not conn:
        print("Failed to connect to PostgreSQL")
        return False
    print("✓ Connected to PostgreSQL")
    
    # Step 2: Create user and database
    print("\n[2/4] Creating user and database...")
    create_user_and_db(conn)
    conn.close()
    
    # Step 3: Restore backup
    print("\n[3/4] Restoring database backup...")
    restore_backup(BACKUP_FILE)
    
    # Step 4: Verify connection
    print("\n[4/4] Verifying connection...")
    verify_connection()
    
    print("\n" + "=" * 50)
    print("✓ Database setup complete!")
    print("=" * 50)
    print("\nConnection Details:")
    print(f"  Host: localhost")
    print(f"  Port: 5432")
    print(f"  Database: {NEW_DB}")
    print(f"  User: {NEW_USER}")
    print(f"  Password: (configured in .env)")
    
    return True

if __name__ == '__main__':
    main()
