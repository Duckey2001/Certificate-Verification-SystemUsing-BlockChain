#!/bin/bash

# CertiVert Project - Complete Installation Script
# This script installs all dependencies for backend, frontend, and blockchain

set -e  # Exit on error

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  CertiVert Project Installation${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 1. Python Backend Dependencies
echo -e "${YELLOW}[1/3] Installing Python Backend Dependencies...${NC}"
cd backend

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

echo -e "${GREEN}✓ Python backend dependencies installed${NC}"
cd ..

# 2. React Frontend Dependencies
echo -e "${YELLOW}[2/3] Installing React Frontend Dependencies...${NC}"
cd frontend
npm install --silent
echo -e "${GREEN}✓ React frontend dependencies installed${NC}"
cd ..

# 3. Blockchain Dependencies
echo -e "${YELLOW}[3/3] Installing Blockchain (Hardhat) Dependencies...${NC}"
cd blockchain
npm install --silent
echo -e "${GREEN}✓ Blockchain dependencies installed${NC}"
cd ..

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Installation Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "All dependencies have been installed successfully."
echo ""
echo "To start the project, run:"
echo "  ./start.sh"
echo ""
echo "Or start manually:"
echo "  Backend:   cd backend && source venv/bin/activate && python3 main.py"
echo "  Frontend:  cd frontend && npm start"
echo "  Blockchain: cd blockchain && npx hardhat node"
