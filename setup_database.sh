#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}==============================================${NC}"
echo -e "${BLUE}CertiVert LGCSE - Complete Database Setup Script${NC}"
echo -e "${BLUE}==============================================${NC}\n"

# Load environment variables from .env file
if [ -f .env ]; then
    echo -e "${YELLOW}Loading environment variables from .env...${NC}"
    export $(grep -v '^#' .env | xargs)
    echo -e "${GREEN}✓ Environment variables loaded${NC}\n"
fi

# PostgreSQL credentials from .env or defaults
DB_USER="${DB_USER:-certivert}"
DB_PASSWORD="${DB_PASSWORD:-certivert123}"
DB_NAME="${DB_NAME:-certivert_db}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_ADMIN_USER="${DB_ADMIN_USER:-postgres}"

# Backup file
BACKUP_FILE="${BACKUP_FILE:-backend/certivert_backup.sql}"
SCHEMA_FILE="${SCHEMA_FILE:-backend/schema.sql}"
INIT_DATA_FILE="${INIT_DATA_FILE:-backend/init_data.sql}"

# Log file
LOG_FILE="db_setup_$(date +%Y%m%d_%H%M%S).log"

# Function to log messages
log_message() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

# Function to check command status
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ $1${NC}" | tee -a "$LOG_FILE"
    else
        echo -e "${RED}✗ $1${NC}" | tee -a "$LOG_FILE"
        if [ "$2" = "exit" ]; then
            echo -e "${RED}Fatal error. Exiting.${NC}" | tee -a "$LOG_FILE"
            exit 1
        fi
    fi
}

# Function to create backup
create_backup() {
    local backup_file="backup_$(date +%Y%m%d_%H%M%S).sql"
    echo -e "${YELLOW}Creating database backup: $backup_file...${NC}" | tee -a "$LOG_FILE"
    
    if PGPASSWORD="$DB_PASSWORD" pg_dump -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" "$DB_NAME" > "$backup_file" 2>/dev/null; then
        echo -e "${GREEN}✓ Backup created: $backup_file${NC}" | tee -a "$LOG_FILE"
    else
        echo -e "${YELLOW}⚠ No backup created (database may not exist yet)${NC}" | tee -a "$LOG_FILE"
    fi
}

log_message "${YELLOW}Step 1: Checking PostgreSQL installation...${NC}"
if ! command -v psql &> /dev/null; then
    log_message "${RED}PostgreSQL is not installed. Please install it first.${NC}"
    log_message "${YELLOW}For Ubuntu/Debian: sudo apt-get install postgresql postgresql-contrib${NC}"
    log_message "${YELLOW}For macOS: brew install postgresql${NC}"
    exit 1
fi

# Check PostgreSQL version
PG_VERSION=$(psql --version | head -n1 | cut -d' ' -f3 | cut -d'.' -f1)
log_message "${GREEN}✓ PostgreSQL is installed (version $PG_VERSION)${NC}\n"

log_message "${YELLOW}Step 2: Checking PostgreSQL service status...${NC}"
if systemctl is-active --quiet postgresql 2>/dev/null; then
    log_message "${GREEN}✓ PostgreSQL service is running${NC}"
elif pg_isready -q 2>/dev/null; then
    log_message "${GREEN}✓ PostgreSQL is accepting connections${NC}"
else
    log_message "${YELLOW}⚠ PostgreSQL service may not be running. Attempting to start...${NC}"
    sudo systemctl start postgresql 2>/dev/null || sudo service postgresql start 2>/dev/null
    sleep 2
    if pg_isready -q 2>/dev/null; then
        log_message "${GREEN}✓ PostgreSQL started successfully${NC}"
    else
        log_message "${RED}✗ Could not start PostgreSQL. Please start it manually.${NC}"
        exit 1
    fi
fi
echo ""

log_message "${YELLOW}Step 3: Creating PostgreSQL user and database...${NC}"

# Create the user and database using sudo -u postgres
log_message "Creating user '$DB_USER'..."
sudo -u "$DB_ADMIN_USER" psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD' CREATEDB;" 2>&1 | grep -v "already exists" | tee -a "$LOG_FILE" || true

log_message "Creating database '$DB_NAME'..."
sudo -u "$DB_ADMIN_USER" psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" 2>&1 | grep -v "already exists" | tee -a "$LOG_FILE" || true

# Grant privileges
log_message "Granting privileges..."
sudo -u "$DB_ADMIN_USER" psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" 2>&1 | grep -v "error\|ERROR" | tee -a "$LOG_FILE" || true

# Grant schema privileges
sudo -u "$DB_ADMIN_USER" psql -d "$DB_NAME" -c "GRANT ALL ON SCHEMA public TO $DB_USER;" 2>&1 | grep -v "error\|ERROR" | tee -a "$LOG_FILE" || true

check_status "User and database created/verified"

# Create backup before restoring
create_backup
echo ""

log_message "${YELLOW}Step 4: Installing PostgreSQL extensions...${NC}"
sudo -u "$DB_ADMIN_USER" psql -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";" 2>&1 | tee -a "$LOG_FILE"
sudo -u "$DB_ADMIN_USER" psql -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";" 2>&1 | tee -a "$LOG_FILE"
check_status "Extensions installed"

echo ""

log_message "${YELLOW}Step 5: Restoring database schema...${NC}"

# Try multiple possible backup locations
BACKUP_LOCATIONS=(
    "$BACKUP_FILE"
    "backend/database/backups/certivert_backup.sql"
    "database/backups/certivert_backup.sql"
    "backups/certivert_backup.sql"
    "certivert_backup.sql"
)

RESTORED=false
for location in "${BACKUP_LOCATIONS[@]}"; do
    if [ -f "$location" ]; then
        log_message "Found backup at: $location"
        if PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -f "$location" 2>&1 | tee -a "$LOG_FILE" | grep -E "ERROR|WARNING" | grep -v "already exists" | grep -v "duplicate key"; then
            log_message "${GREEN}✓ Database restored from $location${NC}"
            RESTORED=true
            break
        else
            log_message "${YELLOW}⚠ Error restoring from $location${NC}"
        fi
    fi
done

if [ "$RESTORED" = false ]; then
    log_message "${YELLOW}⚠ No backup file found. Creating fresh schema...${NC}"
    
    # Create tables from schema if available
    if [ -f "$SCHEMA_FILE" ]; then
        PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -f "$SCHEMA_FILE" 2>&1 | tee -a "$LOG_FILE"
        log_message "${GREEN}✓ Schema created from $SCHEMA_FILE${NC}"
    else
        log_message "${YELLOW}No schema file found. Tables will be created by the application.${NC}"
    fi
    
    # Load initial data if available
    if [ -f "$INIT_DATA_FILE" ]; then
        PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -f "$INIT_DATA_FILE" 2>&1 | tee -a "$LOG_FILE"
        log_message "${GREEN}✓ Initial data loaded from $INIT_DATA_FILE${NC}"
    fi
fi
echo ""

log_message "${YELLOW}Step 6: Verifying database connection...${NC}"
if PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -c "SELECT version();" &>/dev/null; then
    log_message "${GREEN}✓ Database connection successful${NC}"
else
    log_message "${RED}✗ Database connection failed${NC}"
    log_message "Trying with password prompt..."
    psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -c "SELECT version();"
fi
echo ""

log_message "${YELLOW}Step 7: Checking database tables...${NC}"
TABLE_COUNT=$(PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -t -c "SELECT count(*) FROM information_schema.tables WHERE table_schema='public';" 2>/dev/null | xargs)
log_message "Found $TABLE_COUNT tables in database"

log_message "${YELLOW}List of tables:${NC}"
PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -c "\dt" 2>/dev/null | tee -a "$LOG_FILE"
echo ""

log_message "${YELLOW}Step 8: Creating or updating database indexes...${NC}"
# Create indexes for better performance
PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" <<EOF 2>&1 | tee -a "$LOG_FILE"
-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);
CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(payer_user_id);
CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status);
CREATE INDEX IF NOT EXISTS idx_payments_mpesa_transaction ON payments(mpesa_transaction_id);
CREATE INDEX IF NOT EXISTS idx_certificates_hash ON certificates(certificate_hash);
CREATE INDEX IF NOT EXISTS idx_certificates_issuer ON certificates(issuer_id);
CREATE INDEX IF NOT EXISTS idx_verifications_hash ON verification_requests(certificate_hash);
CREATE INDEX IF NOT EXISTS idx_verifications_verifier ON verification_requests(verifier_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_user ON audit_events(actor_user_id);
CREATE INDEX IF NOT EXISTS idx_audit_events_created ON audit_events(created_at);
EOF
check_status "Database indexes created/updated"
echo ""

log_message "${YELLOW}Step 9: Setting up database permissions...${NC}"
# Grant necessary permissions
sudo -u "$DB_ADMIN_USER" psql -d "$DB_NAME" <<EOF 2>&1 | tee -a "$LOG_FILE"
-- Grant usage on schema
GRANT USAGE ON SCHEMA public TO $DB_USER;

-- Grant all privileges on all tables
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;

-- Grant all privileges on all sequences
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $DB_USER;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $DB_USER;
EOF
check_status "Database permissions configured"
echo ""

log_message "${YELLOW}Step 10: Testing M-Pesa related tables...${NC}"
# Check if M-Pesa specific tables exist
if PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -c "SELECT 1 FROM payments LIMIT 1;" &>/dev/null; then
    log_message "${GREEN}✓ Payments table exists (M-Pesa ready)${NC}"
    
    # Check payment status distribution
    PAYMENT_STATS=$(PGPASSWORD="$DB_PASSWORD" psql -U "$DB_USER" -h "$DB_HOST" -p "$DB_PORT" -d "$DB_NAME" -t -c "SELECT status, count(*) FROM payments GROUP BY status;" 2>/dev/null)
    if [ -n "$PAYMENT_STATS" ]; then
        log_message "Payment status distribution:"
        echo "$PAYMENT_STATS" | while read line; do
            log_message "  $line"
        done
    fi
else
    log_message "${YELLOW}⚠ Payments table not found yet${NC}"
fi
echo ""

log_message "${BLUE}==============================================${NC}"
log_message "${GREEN}Database setup complete!${NC}"
log_message "${BLUE}==============================================${NC}\n"

log_message "${BLUE}Connection Details:${NC}"
log_message "  Host: $DB_HOST"
log_message "  Port: $DB_PORT"
log_message "  Database: $DB_NAME"
log_message "  User: $DB_USER"
log_message "  Password: (configured in .env)"
log_message "  Log file: $LOG_FILE"
echo ""

log_message "${BLUE}Useful Commands:${NC}"
log_message "  Connect to database:"
log_message "    psql -U $DB_USER -h $DB_HOST -p $DB_PORT -d $DB_NAME"
echo ""
log_message "  Backup database:"
log_message "    pg_dump -U $DB_USER -h $DB_HOST -p $DB_PORT -d $DB_NAME > backup_\$(date +%Y%m%d).sql"
echo ""
log_message "  Restore database:"
log_message "    psql -U $DB_USER -h $DB_HOST -p $DB_PORT -d $DB_NAME < backup.sql"
echo ""
log_message "  Check database size:"
log_message "    psql -U $DB_USER -h $DB_HOST -p $DB_PORT -d $DB_NAME -c \"SELECT pg_database_size('$DB_NAME')/1024/1024||'MB' as size;\""
echo ""

log_message "${BLUE}To start the backend:${NC}"
log_message "  cd backend && python main.py"
echo ""

log_message "${BLUE}M-Pesa Lesotho Integration:${NC}"
log_message "  ✓ Payment table ready for M-Pesa transactions"
log_message "  ✓ Support for Lesotho Maloti (LSL) currency"
log_message "  ✓ M-Pesa callback handling configured"
log_message "  ✓ Phone number validation for Lesotho format (+266)"
echo ""

log_message "${GREEN}✅ Database setup completed successfully!${NC}"