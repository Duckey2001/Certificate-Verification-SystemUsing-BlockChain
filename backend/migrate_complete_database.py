#!/usr/bin/env python3
"""
Complete Database Migration Script for CertiVert LGCSE System
Ensures all project features are supported in the database
"""

import os
import sys
from sqlalchemy import create_engine, inspect, text
from dotenv import load_dotenv

load_dotenv()

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./certivert.db")
engine = create_engine(DATABASE_URL)

def run_migration():
    """Complete database migration for all project features"""
    print("🚀 Starting complete database migration...")
    
    try:
        inspector = inspect(engine)
        
        # === USERS TABLE UPDATES ===
        print("\n📝 Updating users table...")
        
        if "users" in inspector.get_table_names():
            existing_cols = {col["name"] for col in inspector.get_columns("users")}
            
            # Add missing columns for Google OAuth
            missing_oauth_cols = {
                "google_access_token": "VARCHAR(500)",
                "google_refresh_token": "VARCHAR(500)", 
                "google_token_expires_at": "TIMESTAMP",
                "google_profile_data": "JSONB",
                "oauth_provider": "VARCHAR(50) DEFAULT 'password'",
                "last_oauth_login_at": "TIMESTAMP"
            }
            
            # Add missing columns for profile management
            missing_profile_cols = {
                "profile_completion_score": "INTEGER DEFAULT 0",
                "profile_visibility": "VARCHAR(20) DEFAULT 'public'",
                "profile_theme": "VARCHAR(20) DEFAULT 'light'",
                "language_preference": "VARCHAR(10) DEFAULT 'en'",
                "timezone": "VARCHAR(50) DEFAULT 'UTC'",
                "date_format": "VARCHAR(20) DEFAULT 'YYYY-MM-DD'",
                "email_notifications": "BOOLEAN DEFAULT true",
                "sms_notifications": "BOOLEAN DEFAULT false",
                "push_notifications": "BOOLEAN DEFAULT true"
            }
            
            # Add missing columns for security
            missing_security_cols = {
                "two_factor_enabled": "BOOLEAN DEFAULT false",
                "two_factor_secret": "VARCHAR(255)",
                "backup_codes": "TEXT",
                "failed_login_attempts": "INTEGER DEFAULT 0",
                "account_locked_until": "TIMESTAMP",
                "password_changed_at": "TIMESTAMP",
                "last_password_reset_at": "TIMESTAMP",
                "security_questions": "JSONB",
                "device_fingerprints": "JSONB"
            }
            
            all_user_cols = {**missing_oauth_cols, **missing_profile_cols, **missing_security_cols}
            
            with engine.connect() as conn:
                for col_name, col_def in all_user_cols.items():
                    if col_name not in existing_cols:
                        print(f"  Adding column: {col_name}")
                        conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}"))
                
                conn.commit()
        
        # === PAYMENTS TABLE UPDATES ===
        print("\n💳 Updating payments table...")
        
        if "payments" in inspector.get_table_names():
            existing_cols = {col["name"] for col in inspector.get_columns("payments")}
            
            missing_payment_cols = {
                "currency": "VARCHAR(10) DEFAULT 'LSL'",
                "payment_method_type": "VARCHAR(50) DEFAULT 'mobile_money'",
                "gateway_provider": "VARCHAR(50)",
                "gateway_transaction_id": "VARCHAR(255)",
                "gateway_response": "JSONB",
                "processing_fee": "DOUBLE PRECISION DEFAULT 0",
                "tax_amount": "DOUBLE PRECISION DEFAULT 0",
                "discount_amount": "DOUBLE PRECISION DEFAULT 0",
                "refund_amount": "DOUBLE PRECISION DEFAULT 0",
                "refund_reason": "TEXT",
                "refund_status": "VARCHAR(20) DEFAULT 'none'",
                "refunded_at": "TIMESTAMP",
                "dispute_status": "VARCHAR(20) DEFAULT 'none'",
                "dispute_reason": "TEXT",
                "disputed_at": "TIMESTAMP",
                "settlement_status": "VARCHAR(20) DEFAULT 'pending'",
                "settled_at": "TIMESTAMP",
                "metadata": "JSONB",
                "ip_address": "VARCHAR(45)",
                "user_agent": "TEXT",
                "retry_count": "INTEGER DEFAULT 0",
                "next_retry_at": "TIMESTAMP",
                "webhook_delivered": "BOOLEAN DEFAULT false",
                "webhook_attempts": "INTEGER DEFAULT 0"
            }
            
            with engine.connect() as conn:
                for col_name, col_def in missing_payment_cols.items():
                    if col_name not in existing_cols:
                        print(f"  Adding column: {col_name}")
                        conn.execute(text(f"ALTER TABLE payments ADD COLUMN {col_name} {col_def}"))
                
                conn.commit()
        
        # === CREATE PROFILE PICTURES TABLE ===
        print("\n📸 Creating profile_pictures table...")
        
        if "profile_pictures" not in inspector.get_table_names():
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE profile_pictures (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        file_name VARCHAR(255) NOT NULL,
                        file_path VARCHAR(500) NOT NULL,
                        file_size INTEGER NOT NULL,
                        mime_type VARCHAR(100) NOT NULL,
                        width INTEGER,
                        height INTEGER,
                        is_active BOOLEAN DEFAULT true,
                        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.commit()
                print("  ✅ profile_pictures table created")
        
        # === CREATE USER PREFERENCES TABLE ===
        print("\n⚙️ Creating user_preferences table...")
        
        if "user_preferences" not in inspector.get_table_names():
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE user_preferences (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                        dashboard_layout JSONB DEFAULT '{}',
                        notification_settings JSONB DEFAULT '{}',
                        privacy_settings JSONB DEFAULT '{}',
                        accessibility_settings JSONB DEFAULT '{}',
                        custom_settings JSONB DEFAULT '{}',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.commit()
                print("  ✅ user_preferences table created")
        
        # === CREATE USER SESSIONS ENHANCED TABLE ===
        print("\n🔐 Enhancing sessions table...")
        
        if "sessions" in inspector.get_table_names():
            existing_cols = {col["name"] for col in inspector.get_columns("sessions")}
            
            missing_session_cols = {
                "device_info": "JSONB",
                "location": "VARCHAR(255)",
                "is_active": "BOOLEAN DEFAULT true",
                "last_activity_at": "TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "logout_reason": "VARCHAR(100)",
                "force_logout_at": "TIMESTAMP"
            }
            
            with engine.connect() as conn:
                for col_name, col_def in missing_session_cols.items():
                    if col_name not in existing_cols:
                        print(f"  Adding column: {col_name}")
                        conn.execute(text(f"ALTER TABLE sessions ADD COLUMN {col_name} {col_def}"))
                
                conn.commit()
        
        # === CREATE AUDIT LOGS TABLE ===
        print("\n📋 Creating audit_logs table...")
        
        if "audit_logs" not in inspector.get_table_names():
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE audit_logs (
                        id SERIAL PRIMARY KEY,
                        user_id INTEGER REFERENCES users(id),
                        action VARCHAR(100) NOT NULL,
                        resource_type VARCHAR(50) NOT NULL,
                        resource_id VARCHAR(255),
                        old_values JSONB,
                        new_values JSONB,
                        ip_address VARCHAR(45),
                        user_agent TEXT,
                        session_id VARCHAR(255),
                        status VARCHAR(20) DEFAULT 'success',
                        error_message TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.commit()
                print("  ✅ audit_logs table created")
        
        # === CREATE INDEXES FOR PERFORMANCE ===
        print("\n🔍 Creating performance indexes...")
        
        with engine.connect() as conn:
            # Users indexes
            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id)",
                "CREATE INDEX IF NOT EXISTS idx_users_oauth_provider ON users(oauth_provider)",
                "CREATE INDEX IF NOT EXISTS idx_users_email_verified ON users(email_verified_at)",
                "CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login_at)",
                "CREATE INDEX IF NOT EXISTS idx_users_profile_completion ON users(profile_completion_score)",
                
                # Profile pictures indexes
                "CREATE INDEX IF NOT EXISTS idx_profile_pictures_user ON profile_pictures(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_profile_pictures_active ON profile_pictures(is_active)",
                
                # User preferences indexes
                "CREATE INDEX IF NOT EXISTS idx_user_preferences_user ON user_preferences(user_id)",
                
                # Audit logs indexes
                "CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action)",
                "CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs(resource_type, resource_id)",
                "CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at)",
                
                # Payments indexes
                "CREATE INDEX IF NOT EXISTS idx_payments_gateway ON payments(gateway_provider)",
                "CREATE INDEX IF NOT EXISTS idx_payments_refund ON payments(refund_status)",
                "CREATE INDEX IF NOT EXISTS idx_payments_dispute ON payments(dispute_status)",
                "CREATE INDEX IF NOT EXISTS idx_payments_settlement ON payments(settlement_status)",
                
                # Sessions indexes
                "CREATE INDEX IF NOT EXISTS idx_sessions_device ON sessions(device_info)",
                "CREATE INDEX IF NOT EXISTS idx_sessions_activity ON sessions(last_activity_at)"
            ]
            
            for index_sql in indexes:
                conn.execute(text(index_sql))
            
            conn.commit()
            print("  ✅ All indexes created")
        
        # === CREATE TRIGGERS FOR AUTOMATIC UPDATES ===
        print("\n⚡ Creating triggers...")
        
        if DATABASE_URL.startswith("sqlite"):
            with engine.connect() as conn:
                # Update triggers for SQLite
                triggers = [
                    """
                    CREATE TRIGGER IF NOT EXISTS update_profile_pictures_updated_at 
                    AFTER UPDATE ON profile_pictures
                    BEGIN
                        UPDATE profile_pictures SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                    END;
                    """,
                    """
                    CREATE TRIGGER IF NOT EXISTS update_user_preferences_updated_at 
                    AFTER UPDATE ON user_preferences
                    BEGIN
                        UPDATE user_preferences SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                    END;
                    """,
                    """
                    CREATE TRIGGER IF NOT EXISTS update_sessions_last_activity 
                    AFTER UPDATE ON sessions
                    BEGIN
                        UPDATE sessions SET last_activity_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                    END;
                    """
                ]
                
                for trigger_sql in triggers:
                    conn.execute(text(trigger_sql))
                
                conn.commit()
                print("  ✅ Triggers created")
        
        print("\n✅ Database migration completed successfully!")
        print("🎉 All project features are now supported in the database")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    run_migration()
