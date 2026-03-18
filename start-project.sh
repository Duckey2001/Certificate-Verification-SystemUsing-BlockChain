#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if PostgreSQL is running
check_postgres() {
    if systemctl is-active --quiet postgresql; then
        return 0
    else
        return 1
    fi
}

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   LGCSE Project Startup Script${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if required directories exist
if [ ! -d ~/lgcse-project/backend ]; then
    echo -e "${RED}Error: backend directory not found at ~/lgcse-project/backend${NC}"
    exit 1
fi

if [ ! -d ~/lgcse-project/blockchain ]; then
    echo -e "${RED}Error: blockchain directory not found at ~/lgcse-project/blockchain${NC}"
    exit 1
fi

if [ ! -d ~/lgcse-project/frontend ]; then
    echo -e "${RED}Error: frontend directory not found at ~/lgcse-project/frontend${NC}"
    exit 1
fi

# Start PostgreSQL
echo -e "${YELLOW}[1/4] Starting PostgreSQL...${NC}"
sudo systemctl start postgresql

if check_postgres; then
    echo -e "${GREEN}✓ PostgreSQL started successfully${NC}"
    sudo systemctl status postgresql --no-pager | grep "Active:"
else
    echo -e "${RED}✗ Failed to start PostgreSQL${NC}"
    exit 1
fi

echo ""

# Check if ports are available
echo -e "${YELLOW}Checking port availability...${NC}"
if ss -tuln | grep -q :8000; then
    echo -e "${RED}✗ Port 8000 is already in use${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Port 8000 is available${NC}"
fi

if ss -tuln | grep -q :8545; then
    echo -e "${RED}✗ Port 8545 is already in use${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Port 8545 is available${NC}"
fi

if ss -tuln | grep -q :3000; then
    echo -e "${RED}✗ Port 3000 is already in use${NC}"
    exit 1
else
    echo -e "${GREEN}✓ Port 3000 is available${NC}"
fi

echo ""

# Open terminals for each service
echo -e "${YELLOW}[2/4] Starting Backend server...${NC}"
gnome-terminal --tab --title="Backend (Port 8000)" -- bash -c "
    cd ~/lgcse-project/backend
    echo '=== Backend Server ==='
    echo 'Directory: $(pwd)'
    echo 'Activating virtual environment...'
    source venv/bin/activate
    echo 'Starting uvicorn on port 8000...'
    echo ''
    uvicorn main:app --reload --port 8000
    exec bash"
echo -e "${GREEN}✓ Backend terminal opened${NC}"
sleep 2

echo -e "${YELLOW}[3/4] Starting Blockchain node...${NC}"
gnome-terminal --tab --title="Blockchain (Port 8545)" -- bash -c "
    cd ~/lgcse-project/blockchain
    echo '=== Blockchain Hardhat Node ==='
    echo 'Directory: $(pwd)'
    echo 'Starting Hardhat node on port 8545...'
    echo ''
    npm run node
    exec bash"
echo -e "${GREEN}✓ Blockchain terminal opened${NC}"
sleep 2

echo -e "${YELLOW}[4/4] Starting Frontend React app...${NC}"
gnome-terminal --tab --title="Frontend (Port 3000)" -- bash -c "
    cd ~/lgcse-project/frontend
    echo '=== React Frontend ==='
    echo 'Directory: $(pwd)'
    echo 'Starting React app on port 3000...'
    echo ''
    npm start
    exec bash"
echo -e "${GREEN}✓ Frontend terminal opened${NC}"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   All services started successfully!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Services running on:${NC}"
echo "  • Backend:  http://localhost:8000"
echo "  • Frontend: http://localhost:3000"
echo "  • Blockchain: http://localhost:8545"
echo ""
echo -e "${YELLOW}API Documentation:${NC}"
echo "  • Swagger UI: http://localhost:8000/docs"
echo "  • ReDoc: http://localhost:8000/redoc"
echo ""
echo -e "${YELLOW}To stop services:${NC}"
echo "  • Close individual terminal tabs"
echo "  • Or run: sudo systemctl stop postgresql"
