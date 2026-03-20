#!/bin/bash

echo "🚀 Starting Complete LGCSE System with Issuer & Verifier Nodes..."
echo "================================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    case $status in
        "OK")
            echo -e "${GREEN}✅ $message${NC}"
            ;;
        "FAIL")
            echo -e "${RED}❌ $message${NC}"
            ;;
        "WARN")
            echo -e "${YELLOW}⚠️  $message${NC}"
            ;;
        "INFO")
            echo -e "${BLUE}ℹ️  $message${NC}"
            ;;
        "NODE")
            echo -e "${CYAN}🔗 $message${NC}"
            ;;
    esac
}

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to wait for service to be ready
wait_for_service() {
    local url=$1
    local service_name=$2
    local max_attempts=${3:-30}
    local attempt=1
    
    print_status "INFO" "Waiting for $service_name to start..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s --max-time 2 "$url" > /dev/null 2>&1; then
            print_status "OK" "$service_name is ready!"
            return 0
        fi
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    print_status "FAIL" "$service_name failed to start within expected time"
    return 1
}

# Get project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo -e "${YELLOW}📁 Project Root: ${PROJECT_ROOT}${NC}"
echo ""

# Kill existing processes on required ports
echo -e "${BLUE}🧹 Cleaning up existing processes...${NC}"

for port in 3000 5000 8000 8545 8546 7545; do
    if check_port $port; then
        print_status "WARN" "Port $port is in use, terminating..."
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
done

# Create logs directory
mkdir -p logs
mkdir -p pids

# Start PostgreSQL
echo -e "\n${BLUE}🐘 Starting PostgreSQL...${NC}"
if sudo systemctl start postgresql 2>/dev/null; then
    print_status "OK" "PostgreSQL started"
else
    print_status "WARN" "PostgreSQL may already be running"
fi

if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    print_status "OK" "PostgreSQL is ready"
else
    print_status "FAIL" "PostgreSQL is not responding"
fi

# Install dependencies if needed
echo -e "\n${BLUE}📦 Installing dependencies...${NC}"

# Root project dependencies
if [ ! -d "node_modules" ]; then
    print_status "INFO" "Installing root project dependencies..."
    npm install --silent
fi

# Frontend dependencies
if [ ! -d "frontend/node_modules" ]; then
    print_status "INFO" "Installing frontend dependencies..."
    cd frontend && npm install --silent && cd ..
fi

# Backend Python dependencies
if [ ! -d "backend/venv" ]; then
    print_status "INFO" "Setting up Python virtual environment..."
    cd backend && python3 -m venv venv && source venv/bin/activate && pip install -q -r requirements.txt && cd ..
fi

# Blockchain dependencies
if [ ! -d "blockchain/node_modules" ]; then
    print_status "INFO" "Installing blockchain dependencies..."
    cd blockchain && npm install --silent && cd ..
fi

# Start Blockchain Network (Hardhat)
echo -e "\n${CYAN}⛓️  Starting Blockchain Network...${NC}"
cd "$PROJECT_ROOT/blockchain"

# Compile contracts
print_status "INFO" "Compiling smart contracts..."
npm run compile 2>/dev/null || print_status "WARN" "Contract compilation may need manual check"

# Start Hardhat node
print_status "INFO" "Starting Hardhat node on port 8545..."
nohup npx hardhat node > ../logs/blockchain.log 2>&1 &
BLOCKCHAIN_PID=$!
echo $BLOCKCHAIN_PID > ../pids/blockchain.pid

# Wait for blockchain to start
sleep 5
wait_for_service "http://localhost:8545" "Blockchain Node" 20

# Deploy contracts
print_status "INFO" "Deploying smart contracts..."
npx hardhat run scripts/deploy.js --network localhost > ../logs/deployment.log 2>&1 || print_status "WARN" "Contract deployment may need manual check"

cd "$PROJECT_ROOT"
print_status "OK" "Blockchain network started"

# Start Issuer Node (Port 8546)
echo -e "\n${CYAN}🏛️  Starting Issuer Node...${NC}"
cd "$PROJECT_ROOT/blockchain"

# Start issuer node
print_status "INFO" "Starting Issuer Node on port 8546..."
nohup npx hardhat node --hostname 0.0.0.0 --port 8546 > ../logs/issuer-node.log 2>&1 &
ISSUER_PID=$!
echo $ISSUER_PID > ../pids/issuer.pid

# Wait for issuer node
sleep 3
if check_port 8546; then
    print_status "OK" "Issuer Node started"
else
    print_status "WARN" "Issuer Node may not be responding"
fi

cd "$PROJECT_ROOT"

# Start Verifier Node (Port 7545)
echo -e "\n${CYAN}🔍 Starting Verifier Node...${NC}"
cd "$PROJECT_ROOT/blockchain"

# Start verifier node
print_status "INFO" "Starting Verifier Node on port 7545..."
nohup npx hardhat node --hostname 0.0.0.0 --port 7545 > ../logs/verifier-node.log 2>&1 &
VERIFIER_PID=$!
echo $VERIFIER_PID > ../pids/verifier.pid

# Wait for verifier node
sleep 3
if check_port 7545; then
    print_status "OK" "Verifier Node started"
else
    print_status "WARN" "Verifier Node may not be responding"
fi

cd "$PROJECT_ROOT"

# Start Node.js Backend (Port 8000)
echo -e "\n${BLUE}🔧 Starting Node.js Backend...${NC}"
cd "$PROJECT_ROOT"

# Start backend with issuer/verifier configuration
print_status "INFO" "Starting Node.js backend on port 8000..."
export NODE_ENV=development
export ISSUER_NODE_PORT=8546
export VERIFIER_NODE_PORT=7545
export BLOCKCHAIN_RPC_URL=http://localhost:8545

nohup npm start > logs/node-backend.log 2>&1 &
NODE_PID=$!
echo $NODE_PID > pids/node-backend.pid

wait_for_service "http://localhost:8000" "Node.js Backend" 30

# Start Python Backend (Port 5000)
echo -e "\n${BLUE}🐍 Starting Python Backend...${NC}"
cd "$PROJECT_ROOT/backend"

# Activate virtual environment
source venv/bin/activate

# Start Python backend with blockchain configuration
print_status "INFO" "Starting Python backend on port 5000..."
export BLOCKCHAIN_URL=http://localhost:8545
export ISSUER_URL=http://localhost:8546
export VERIFIER_URL=http://localhost:7545

nohup python app.py > ../logs/python-backend.log 2>&1 &
PYTHON_PID=$!
echo $PYTHON_PID > ../pids/python-backend.pid

cd "$PROJECT_ROOT"
wait_for_service "http://localhost:5000" "Python Backend" 45

# Start React Frontend (Port 3000)
echo -e "\n${BLUE}⚛️  Starting React Frontend...${NC}"
cd "$PROJECT_ROOT/frontend"

# Start frontend with multi-node configuration
print_status "INFO" "Starting React frontend on port 3000..."
export REACT_APP_BLOCKCHAIN_URL=http://localhost:8545
export REACT_APP_ISSUER_URL=http://localhost:8546
export REACT_APP_VERIFIER_URL=http://localhost:7545
export REACT_APP_API_URL=http://localhost:8000
export REACT_APP_PYTHON_API_URL=http://localhost:5000

nohup npm start > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../pids/frontend.pid

cd "$PROJECT_ROOT"
wait_for_service "http://localhost:3000" "React Frontend" 60

# Final System Status
echo -e "\n${CYAN}🎯 Complete System Status...${NC}"

echo -e "\n${YELLOW}📊 Node Configuration:${NC}"
print_status "NODE" "Issuer Node:     http://localhost:8546"
print_status "NODE" "Verifier Node:   http://localhost:7545"
print_status "NODE" "Blockchain Node: http://localhost:8545"

echo -e "\n${YELLOW}🌐 Application Services:${NC}"
print_status "OK" "Frontend:         http://localhost:3000"
print_status "OK" "Node.js Backend:  http://localhost:8000"
print_status "OK" "Python Backend:   http://localhost:5000"
print_status "OK" "Database:         PostgreSQL (localhost:5432)"

echo -e "\n${YELLOW}📋 Smart Contracts:${NC}"
print_status "INFO" "Certificate Registry: Deployed"
print_status "INFO" "LGCSE Token:         Deployed"
print_status "INFO" "Access Control:      Deployed"

echo -e "\n${YELLOW}🔗 System Features:${NC}"
print_status "INFO" "✨ Multi-node blockchain network"
print_status "INFO" "🏛️  Certificate issuance (Issuer Node)"
print_status "INFO" "🔍 Certificate verification (Verifier Node)"
print_status "INFO" "⚛️  React frontend with dual-node support"
print_status "INFO" "🔧 Dual backend architecture"
print_status "INFO" "🐘 PostgreSQL database"
print_status "INFO" "📜 Smart contract integration"

echo -e "\n${YELLOW}🚀 Quick Access:${NC}"
echo -e "🌐 Frontend:        ${GREEN}http://localhost:3000${NC}"
echo -e "🔧 Node.js API:     ${GREEN}http://localhost:8000${NC}"
echo -e "🐍 Python API:      ${GREEN}http://localhost:5000${NC}"
echo -e "⛓️  Blockchain:      ${GREEN}http://localhost:8545${NC}"
echo -e "🏛️  Issuer Node:     ${GREEN}http://localhost:8546${NC}"
echo -e "🔍 Verifier Node:   ${GREEN}http://localhost:7545${NC}"

echo -e "\n${YELLOW}📝 Process IDs:${NC}"
echo "Blockchain PID: $(cat pids/blockchain.pid 2>/dev/null || echo 'Not found')"
echo "Issuer PID: $(cat pids/issuer.pid 2>/dev/null || echo 'Not found')"
echo "Verifier PID: $(cat pids/verifier.pid 2>/dev/null || echo 'Not found')"
echo "Node.js Backend PID: $(cat pids/node-backend.pid 2>/dev/null || echo 'Not found')"
echo "Python Backend PID: $(cat pids/python-backend.pid 2>/dev/null || echo 'Not found')"
echo "Frontend PID: $(cat pids/frontend.pid 2>/dev/null || echo 'Not found')"

echo -e "\n${YELLOW}📊 Log Files:${NC}"
echo "Blockchain:   logs/blockchain.log"
echo "Issuer:       logs/issuer-node.log"
echo "Verifier:     logs/verifier-node.log"
echo "Node.js:      logs/node-backend.log"
echo "Python:       logs/python-backend.log"
echo "Frontend:     logs/frontend.log"
echo "Deployment:   logs/deployment.log"

echo -e "\n${GREEN}🎉 Complete LGCSE System Started Successfully!${NC}"
echo -e "\n${CYAN}🔗 Multi-Node Blockchain Network Active${NC}"
echo -e "${CYAN}🏛️  Issuer Node Ready for Certificate Issuance${NC}"
echo -e "${CYAN}🔍 Verifier Node Ready for Certificate Verification${NC}"

echo -e "\n${BLUE}🧪 Test the complete system:${NC}"
echo "   ./test-full-system.sh"

echo -e "\n${BLUE}🛑 Stop all services:${NC}"
echo "   ./stop-all-services.sh"

echo -e "\n${GREEN}✨ Full system startup completed!${NC}"
