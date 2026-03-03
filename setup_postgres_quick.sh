#!/bin/bash

# Quick PostgreSQL Setup for LGCSE Project
# This script creates the database user and database

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔════════════════════════════════════════╗"
echo "║  LGCSE Database Setup                  ║"
echo "║  PostgreSQL Configuration              ║"
echo "╚════════════════════════════════════════╝"
echo -e "${NC}\n"

# Configuration
DB_USER="diploma_admin"
DB_PASSWORD="diploma1234"
DB_NAME="diploma_verification"

echo -e "${YELLOW}Configuration:${NC}"
echo "  User: $DB_USER"
echo "  Database: $DB_NAME"
echo "  Host: localhost:5432"
echo ""

# Step 1: Create user
echo -e "${YELLOW}Creating PostgreSQL user...${NC}"
if sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD' CREATEDB;" 2>&1 | grep -q "already exists"; then
    echo -e "${GREEN}✓ User already exists${NC}"
else
    echo -e "${GREEN}✓ User created${NC}"
fi

# Step 2: Create database
echo -e "${YELLOW}Creating database...${NC}"
if sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" 2>&1 | grep -q "already exists"; then
    echo -e "${GREEN}✓ Database already exists${NC}"
else
    echo -e "${GREEN}✓ Database created${NC}"
fi

# Step 3: Grant privileges
echo -e "${YELLOW}Granting privileges...${NC}"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" 2>&1 | grep -v "already" || true
echo -e "${GREEN}✓ Privileges configured${NC}"

# Step 4: Verify
echo -e "\n${YELLOW}Verifying connection...${NC}"
if PGPASSWORD="$DB_PASSWORD" psql -U $DB_USER -h localhost -d $DB_NAME -c "SELECT 1;" &>/dev/null; then
    echo -e "${GREEN}✓ Connection successful!${NC}"
else
    echo -e "${RED}✗ Connection failed${NC}"
    exit 1
fi

echo -e "\n${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ PostgreSQL setup complete!${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}\n"

echo -e "${BLUE}Next steps:${NC}"
echo "1. Initialize tables: cd backend && python scripts/setup_database.py"
echo "2. Start backend: python main.py"
echo ""
