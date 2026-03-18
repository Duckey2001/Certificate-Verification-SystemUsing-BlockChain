from dotenv import load_dotenv
load_dotenv()

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, Session
from models import Base
import os

# Database URL - defaults to SQLite, but can be PostgreSQL or others
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./certivert.db")

# Create engine
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # For PostgreSQL and other databases, no special connect_args are needed
    engine = create_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

def _ensure_sqlite_columns():
    """
    Lightweight, dev-friendly schema evolution for SQLite.
    Adds new nullable columns when models change (no full migrations).
    """
    try:
        if not DATABASE_URL.startswith("sqlite"):
            return

        inspector = inspect(engine)

        # USERS TABLE - User management
        if "users" in inspector.get_table_names():
            user_cols = {col["name"] for col in inspector.get_columns("users")}
            
            # OAuth fields
            if "google_id" not in user_cols:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE users ADD COLUMN google_id VARCHAR(255)"))
                    conn.commit()
            
            # GitHub OAuth
            if "github_id" not in user_cols:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE users ADD COLUMN github_id VARCHAR(255)"))
                    conn.commit()
            
            # Institution association
            if "institution_code" not in user_cols:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE users ADD COLUMN institution_code VARCHAR(50)"))
                    conn.commit()
            
            # User role and status
            if "role" not in user_cols:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'user'"))
                    conn.commit()
            
            if "is_active" not in user_cols:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1"))
                    conn.commit()
            
            if "last_login_at" not in user_cols:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE users ADD COLUMN last_login_at TIMESTAMP"))
                    conn.commit()

        # SESSIONS TABLE - Session management
        if "sessions" not in inspector.get_table_names():
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE sessions (
                        id VARCHAR(255) PRIMARY KEY,
                        session_token VARCHAR(255) UNIQUE NOT NULL,
                        user_id VARCHAR(255) NOT NULL,
                        expires TIMESTAMP NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.commit()
        else:
            session_cols = {col["name"] for col in inspector.get_columns("sessions")}
            if "session_token" not in session_cols:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE sessions ADD COLUMN session_token VARCHAR(255) UNIQUE"))
                    conn.commit()

        # LOGIN_ACTIVITY TABLE - Audit trail
        if "login_activity" not in inspector.get_table_names():
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE login_activity (
                        id VARCHAR(255) PRIMARY KEY,
                        user_id VARCHAR(255) NOT NULL,
                        institution_code VARCHAR(50),
                        ip_address VARCHAR(45),
                        user_agent TEXT,
                        location VARCHAR(255),
                        status VARCHAR(20) DEFAULT 'success',
                        failure_reason TEXT,
                        login_method VARCHAR(50) DEFAULT 'password',
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.commit()
        else:
            login_cols = {col["name"] for col in inspector.get_columns("login_activity")}
            if "login_method" not in login_cols:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE login_activity ADD COLUMN login_method VARCHAR(50) DEFAULT 'password'"))
                    conn.commit()

        # PAYMENTS TABLE - M-Pesa and other payment methods
        if "payments" not in inspector.get_table_names():
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE payments (
                        id VARCHAR(255) PRIMARY KEY,
                        verification_request_id INTEGER,
                        payer_user_id VARCHAR(255) NOT NULL,
                        payee_institution_code VARCHAR(50),
                        method VARCHAR(50) NOT NULL,
                        amount FLOAT NOT NULL,
                        currency VARCHAR(10) DEFAULT 'LSL',
                        status VARCHAR(20) DEFAULT 'PENDING',
                        phone_number VARCHAR(20),
                        digits VARCHAR(10),
                        reference VARCHAR(100),
                        description TEXT,
                        mpesa_merchant_request_id VARCHAR(100) UNIQUE,
                        mpesa_checkout_request_id VARCHAR(100) UNIQUE,
                        mpesa_transaction_id VARCHAR(100) UNIQUE,
                        mpesa_response_code VARCHAR(20),
                        mpesa_response_description TEXT,
                        mpesa_customer_message TEXT,
                        mpesa_phone_number VARCHAR(20),
                        mpesa_amount FLOAT,
                        mpesa_transaction_date VARCHAR(50),
                        error_message TEXT,
                        retry_count INTEGER DEFAULT 0,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        confirmed_at TIMESTAMP,
                        verification_request JSON
                    )
                """))
                conn.commit()
        else:
            payment_cols = {col["name"] for col in inspector.get_columns("payments")}
            
            # Add any missing payment columns
            payment_columns_to_add = {
                "currency": "ALTER TABLE payments ADD COLUMN currency VARCHAR(10) DEFAULT 'LSL'",
                "mpesa_phone_number": "ALTER TABLE payments ADD COLUMN mpesa_phone_number VARCHAR(20)",
                "mpesa_amount": "ALTER TABLE payments ADD COLUMN mpesa_amount FLOAT",
                "mpesa_transaction_date": "ALTER TABLE payments ADD COLUMN mpesa_transaction_date VARCHAR(50)",
                "retry_count": "ALTER TABLE payments ADD COLUMN retry_count INTEGER DEFAULT 0",
                "verification_request": "ALTER TABLE payments ADD COLUMN verification_request JSON"
            }
            
            for col_name, alter_stmt in payment_columns_to_add.items():
                if col_name not in payment_cols:
                    with engine.connect() as conn:
                        conn.execute(text(alter_stmt))
                        conn.commit()

        # PAYMENT_CALLBACKS TABLE - Store raw M-Pesa callbacks
        if "payment_callbacks" not in inspector.get_table_names():
            with engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE payment_callbacks (
                        id VARCHAR(255) PRIMARY KEY,
                        payment_id VARCHAR(255) NOT NULL,
                        callback_data JSON NOT NULL,
                        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        result_code VARCHAR(20),
                        result_desc TEXT
                    )
                """))
                conn.commit()

        # CERTIFICATES TABLE - Blockchain metadata
        if "certificates" in inspector.get_table_names():
            cert_cols = {col["name"] for col in inspector.get_columns("certificates")}
            if "blockchain_tx_id" not in cert_cols:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE certificates ADD COLUMN blockchain_tx_id VARCHAR(200)"))
                    conn.commit()
            if "blockchain_network" not in cert_cols:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE certificates ADD COLUMN blockchain_network VARCHAR(50)"))
                    conn.commit()
            if "blockchain_block_number" not in cert_cols:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE certificates ADD COLUMN blockchain_block_number INTEGER"))
                    conn.commit()

        # VERIFICATION_REQUESTS TABLE - Payment tracking
        if "verification_requests" in inspector.get_table_names():
            vr_cols = {col["name"] for col in inspector.get_columns("verification_requests")}
            if "payment_method" not in vr_cols:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE verification_requests ADD COLUMN payment_method VARCHAR(20)"))
                    conn.commit()
            if "payment_status" not in vr_cols:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE verification_requests ADD COLUMN payment_status VARCHAR(20)"))
                    conn.commit()
            if "payment_reference" not in vr_cols:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE verification_requests ADD COLUMN payment_reference VARCHAR(100)"))
                    conn.commit()
            if "payment_confirmed_at" not in vr_cols:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE verification_requests ADD COLUMN payment_confirmed_at TIMESTAMP"))
                    conn.commit()

        # Create indexes for better performance
        with engine.connect() as conn:
            # Users indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_institution ON users(institution_code)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"))
            
            # Sessions indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires)"))
            
            # Login activity indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_login_activity_user ON login_activity(user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_login_activity_institution ON login_activity(institution_code)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_login_activity_created ON login_activity(created_at)"))
            
            # Payments indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_payments_user ON payments(payer_user_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_payments_institution ON payments(payee_institution_code)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_payments_created ON payments(created_at)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_payments_checkout ON payments(mpesa_checkout_request_id)"))
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_payments_transaction ON payments(mpesa_transaction_id)"))
            
            # Payment callbacks indexes
            conn.execute(text("CREATE INDEX IF NOT EXISTS idx_callbacks_payment ON payment_callbacks(payment_id)"))
            
            conn.commit()

        # Create trigger for updating updated_at (SQLite specific)
        if DATABASE_URL.startswith("sqlite"):
            # Users update trigger
            conn.execute(text("""
                CREATE TRIGGER IF NOT EXISTS update_users_updated_at 
                AFTER UPDATE ON users
                BEGIN
                    UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END;
            """))
            
            # Sessions update trigger
            conn.execute(text("""
                CREATE TRIGGER IF NOT EXISTS update_sessions_updated_at 
                AFTER UPDATE ON sessions
                BEGIN
                    UPDATE sessions SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END;
            """))
            
            # Payments update trigger
            conn.execute(text("""
                CREATE TRIGGER IF NOT EXISTS update_payments_updated_at 
                AFTER UPDATE ON payments
                BEGIN
                    UPDATE payments SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END;
            """))
            
            conn.commit()

    except Exception as e:
        # Log error but don't prevent app startup in dev
        print(f"Warning: Schema evolution issue: {e}")
        # Schema will be fixed manually if needed.
        pass

_ensure_sqlite_columns()

def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Utility functions for database operations
def init_default_admin():
    """Initialize default admin user if not exists"""
    try:
        if not DATABASE_URL.startswith("sqlite"):
            return
            
        with engine.connect() as conn:
            # Check if admin exists
            result = conn.execute(text("SELECT COUNT(*) FROM users WHERE username = 'admin'"))
            count = result.scalar()
            
            if count == 0:
                # Import here to avoid circular imports
                from passlib.context import CryptContext
                pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
                
                # Create default admin (password: Admin@123 - change immediately)
                hashed_password = pwd_context.hash("Admin@123")
                
                conn.execute(text("""
                    INSERT INTO users (id, username, email, password_hash, role, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """), (
                    str(uuid.uuid4()),
                    "admin",
                    "admin@certivert.com",
                    hashed_password,
                    "admin",
                    1
                ))
                conn.commit()
                print("Default admin user created")
    except Exception as e:
        print(f"Warning: Could not create default admin: {e}")

# Try to create default admin (only in dev)
try:
    import uuid
    init_default_admin()
except:
    pass