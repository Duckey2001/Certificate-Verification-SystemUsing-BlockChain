#!/usr/bin/env python3
"""
Script to retrieve all users from the database
"""

import os
import sys
from sqlalchemy.orm import Session
from sqlalchemy import text

# Add the backend directory to the path
sys.path.append('/home/duckey/lgcse-project/backend')

from database import SessionLocal, engine
from models import User

def get_all_users():
    """Retrieve all users from the database"""
    db = SessionLocal()
    try:
        # Get all users
        users = db.query(User).all()
        
        print(f"Found {len(users)} users in the database:")
        print("=" * 80)
        
        for user in users:
            print(f"ID: {user.id}")
            print(f"Username: {user.username}")
            print(f"Email: {user.email}")
            print(f"Role: {user.role}")
            print(f"Institution Code: {user.institution_code}")
            print(f"Institution: {user.institution}")
            print(f"Active: {user.is_active}")
            print(f"Verified: {user.is_verified}")
            print(f"Google ID: {user.google_id}")
            print(f"GitHub ID: {user.github_id}")
            print(f"Last Login: {user.last_login_at}")
            print(f"Created At: {user.created_at}")
            print(f"Updated At: {user.updated_at}")
            print(f"Available Credits: {user.available_credits}")
            print(f"Certificates Issued: {user.certificates_issued}")
            print(f"Certificates Verified: {user.certificates_verified}")
            print("-" * 40)
        
        return users
        
    except Exception as e:
        print(f"Error retrieving users: {e}")
        return []
    finally:
        db.close()

def get_user_summary():
    """Get a summary of users by role"""
    db = SessionLocal()
    try:
        # Get user count by role
        result = db.execute(text("""
            SELECT role, COUNT(*) as count 
            FROM users 
            GROUP BY role
            ORDER BY count DESC
        """))
        
        print("\nUser Summary by Role:")
        print("=" * 30)
        for row in result:
            print(f"{row[0]}: {row[1]}")
        
        # Get total user count
        total_result = db.execute(text("SELECT COUNT(*) FROM users"))
        total = total_result.scalar()
        print(f"\nTotal Users: {total}")
        
        # Get active vs inactive
        active_result = db.execute(text("""
            SELECT 
                SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active,
                SUM(CASE WHEN is_active = 0 THEN 1 ELSE 0 END) as inactive
            FROM users
        """))
        active_row = active_result.fetchone()
        print(f"Active Users: {active_row[0]}")
        print(f"Inactive Users: {active_row[1]}")
        
        # Get OAuth users
        oauth_result = db.execute(text("""
            SELECT 
                SUM(CASE WHEN google_id IS NOT NULL THEN 1 ELSE 0 END) as google_users,
                SUM(CASE WHEN github_id IS NOT NULL THEN 1 ELSE 0 END) as github_users,
                SUM(CASE WHEN password_hash IS NOT NULL THEN 1 ELSE 0 END) as password_users
            FROM users
        """))
        oauth_row = oauth_result.fetchone()
        print(f"Google OAuth Users: {oauth_row[0]}")
        print(f"GitHub OAuth Users: {oauth_row[1]}")
        print(f"Password Users: {oauth_row[2]}")
        
    except Exception as e:
        print(f"Error getting user summary: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    print("Retrieving all users from the database...")
    users = get_all_users()
    get_user_summary()
