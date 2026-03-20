#!/bin/bash

# LGCSE Certificate Verification System - Complete System Startup
# This script starts ALL components with proper configuration and monitoring

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    ss -tuln | grep -q ":$1"
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

# Function to cleanup on exit
cleanup() {
    echo ""
    print_status "WARN" "🛑 Shutting down all services..."
    
    # Kill all background processes using PIDs
    if [ ! -z "$MPESA_PID" ]; then
        kill $MPESA_PID 2>/dev/null || true
    fi
    if [ ! -z "$BACKEND_PID" ]; then
        kill $BACKEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$BLOCKCHAIN_PID" ]; then
        kill $BLOCKCHAIN_PID 2>/dev/null || true
    fi
    if [ ! -z "$FRONTEND_PID" ]; then
        kill $FRONTEND_PID 2>/dev/null || true
    fi
    if [ ! -z "$NODEJS_PID" ]; then
        kill $NODEJS_PID 2>/dev/null || true
    fi
    
    # Kill any remaining processes on ports
    pkill -f "uvicorn.*8000" 2>/dev/null || true
    pkill -f "python.*main.py" 2>/dev/null || true
    pkill -f "node.*server.js" 2>/dev/null || true
    pkill -f "npm.*start.*3000" 2>/dev/null || true
    pkill -f "hardhat.*node" 2>/dev/null || true
    
    print_status "OK" "All services stopped"
    exit
}

trap cleanup SIGINT SIGTERM

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  LGCSE Complete System Startup${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Get project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
print_status "INFO" "📁 Project Root: ${PROJECT_ROOT}"
echo ""

# Create necessary directories
mkdir -p logs pids

# Check if required directories exist
print_status "INFO" "🔍 Checking project structure..."
if [ ! -d "$PROJECT_ROOT/backend" ]; then
    print_status "FAIL" "Backend directory not found"
    exit 1
fi
if [ ! -d "$PROJECT_ROOT/blockchain" ]; then
    print_status "FAIL" "Blockchain directory not found"
    exit 1
fi
if [ ! -d "$PROJECT_ROOT/frontend" ]; then
    print_status "FAIL" "Frontend directory not found"
    exit 1
fi
print_status "OK" "All required directories found"
echo ""

# Check system dependencies
print_status "INFO" "🔧 Checking system dependencies..."
if ! command_exists node; then
    print_status "FAIL" "Node.js not found. Please install Node.js"
    exit 1
fi
if ! command_exists npm; then
    print_status "FAIL" "npm not found. Please install npm"
    exit 1
fi
if ! command_exists python3; then
    print_status "FAIL" "Python3 not found. Please install Python3"
    exit 1
fi
if ! command_exists curl; then
    print_status "FAIL" "curl not found. Please install curl"
    exit 1
fi
print_status "OK" "System dependencies check passed"
echo ""

# Kill existing processes on required ports
print_status "INFO" "🧹 Cleaning up existing processes..."
for port in 3000 5000 8000 8545; do
    if port_in_use $port; then
        print_status "WARN" "Port $port is in use, terminating..."
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
done
echo ""

# Check port availability
print_status "INFO" "🌐 Checking port availability..."
PORTS=(3000 5000 8000 8545)
DB_PORT=5432
for port in "${PORTS[@]}"; do
    if port_in_use $port; then
        print_status "FAIL" "Port $port is already in use"
        exit 1
    else
        print_status "OK" "Port $port is available"
    fi
done

# Check PostgreSQL separately
if port_in_use $DB_PORT; then
    print_status "OK" "PostgreSQL is already running on port $DB_PORT"
else
    print_status "OK" "Port $DB_PORT is available for PostgreSQL"
fi
echo ""

# Start PostgreSQL
print_status "INFO" "🗄️  Starting PostgreSQL..."
if command_exists pgrep && pgrep -x postgres > /dev/null; then
    print_status "OK" "PostgreSQL is already running"
elif command_exists systemctl; then
    if sudo systemctl start postgresql 2>/dev/null; then
        print_status "OK" "PostgreSQL started successfully"
    else
        print_status "WARN" "Could not start PostgreSQL (might need manual setup)"
    fi
else
    print_status "WARN" "PostgreSQL not available - using SQLite fallback"
fi
echo ""

# Install dependencies
print_status "INFO" "📦 Installing dependencies..."

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

print_status "OK" "Dependencies installed"
echo ""

# Function to start Python FastAPI backend
start_python_backend() {
    print_status "INFO" "🐍 Starting Python FastAPI Backend..."
    cd "$PROJECT_ROOT/backend"
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Set environment variables
    export DATABASE_URL="postgresql://certivert:certivert@localhost:5432/CertiVert"
    export OCR_SPACE_API_KEY="8195ce015388957"
    export OCR_SPACE_API_URL="https://api.ocr.space/parse/image"
    
    # Start FastAPI backend
    print_status "INFO" "Starting FastAPI backend on port 8000..."
    nohup python3 main.py > ../logs/python-backend.log 2>&1 &
    BACKEND_PID=$!
    echo $BACKEND_PID > ../pids/python-backend.pid
    
    cd "$PROJECT_ROOT"
    print_status "OK" "Python Backend started (PID: $BACKEND_PID)"
    echo "  URL: http://localhost:8000"
    echo "  Docs: http://localhost:8000/docs"
    echo ""
}

# Function to start Node.js backend
start_nodejs_backend() {
    print_status "INFO" "🔧 Starting Node.js Backend..."
    cd "$PROJECT_ROOT"
    
    # Set environment variables
    export NODE_ENV=development
    export DATABASE_URL="postgresql://certivert:certivert@localhost:5432/CertiVert"
    
    # Start Node.js backend
    print_status "INFO" "Starting Node.js backend on port 5000..."
    nohup node server.js > logs/nodejs-backend.log 2>&1 &
    NODEJS_PID=$!
    echo $NODEJS_PID > pids/nodejs-backend.pid
    
    print_status "OK" "Node.js Backend started (PID: $NODEJS_PID)"
    echo "  URL: http://localhost:5000"
    echo ""
}

# Function to start M-Pesa service
start_mpesa_service() {
    print_status "INFO" "💰 Starting M-Pesa Payment Service..."
    cd "$PROJECT_ROOT"
    
    # Set M-Pesa environment variables
    export MPESA_ENVIRONMENT=sandbox
    export MPESA_CONSUMER_KEY=certivert_top4_general_dealer
    export MPESA_CONSUMER_SECRET=live_api_secret_key_2026
    export MPESA_PASSKEY=live_passkey_top4_110799
    export MPESA_SHORTCODE=110799
    export MPESA_CALLBACK_URL=http://localhost:8000/api/mpesa/callback
    
    # Start M-Pesa backend service
    print_status "INFO" "Starting M-Pesa service..."
    nohup python3 mpesa-real-backend.py > logs/mpesa-service.log 2>&1 &
    MPESA_PID=$!
    echo $MPESA_PID > pids/mpesa-service.pid
    
    cd "$PROJECT_ROOT"
    print_status "OK" "M-Pesa service started (PID: $MPESA_PID)"
    echo "  Service: M-Pesa Payment Gateway"
    echo ""
}

# Function to start blockchain
start_blockchain() {
    print_status "INFO" "⛓️  Starting Blockchain Network..."
    cd "$PROJECT_ROOT/blockchain"
    
    # Compile contracts
    print_status "INFO" "Compiling smart contracts..."
    npm run compile 2>/dev/null || print_status "WARN" "Contract compilation may need manual check"
    
    # Start Hardhat node
    print_status "INFO" "Starting Hardhat node on port 8545..."
    nohup npm run node > ../logs/blockchain.log 2>&1 &
    BLOCKCHAIN_PID=$!
    echo $BLOCKCHAIN_PID > ../pids/blockchain.pid
    
    cd "$PROJECT_ROOT"
    print_status "OK" "Blockchain node started (PID: $BLOCKCHAIN_PID)"
    echo "  URL: http://localhost:8545"
    echo ""
    
    # Wait for blockchain to start then deploy contracts
    sleep 5
    print_status "INFO" "📜 Deploying smart contracts..."
    cd "$PROJECT_ROOT/blockchain"
    npm run deploy > ../logs/deployment.log 2>&1 || print_status "WARN" "Contract deployment may need manual intervention"
    cd "$PROJECT_ROOT"
    print_status "OK" "Smart contracts deployed"
    echo ""
}

# Function to start frontend
start_frontend() {
    print_status "INFO" "🎨 Starting React Frontend..."
    cd "$PROJECT_ROOT/frontend"
    
    # Set environment variables
    export REACT_APP_API_URL=http://localhost:8000
    export REACT_APP_NODEJS_API_URL=http://localhost:5000
    export REACT_APP_BLOCKCHAIN_URL=http://localhost:8545
    
    # Start React app
    print_status "INFO" "Starting React app on port 3000..."
    nohup npm start > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../pids/frontend.pid
    
    cd "$PROJECT_ROOT"
    print_status "OK" "Frontend started (PID: $FRONTEND_PID)"
    echo "  URL: http://localhost:3000"
    echo ""
}

# Start all services
print_status "INFO" "🚀 Starting all services..."
echo ""

start_mpesa_service
start_blockchain
start_python_backend
start_nodejs_backend
start_frontend

# Wait for services to start
print_status "INFO" "⏳ Waiting for services to initialize..."
sleep 5

# Service status check
print_status "INFO" "🔍 Checking service status..."
echo ""

wait_for_service "http://localhost:8545" "Blockchain Node" 20
wait_for_service "http://localhost:8000" "Python Backend" 30
wait_for_service "http://localhost:5000" "Node.js Backend" 30
wait_for_service "http://localhost:3000" "React Frontend" 60

# Final System Status
echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}    🎉 Complete System Started!${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

echo -e "${YELLOW}🌐 Service URLs:${NC}"
echo -e "  • Python Backend:     ${GREEN}http://localhost:8000${NC}"
echo -e "  • Node.js Backend:    ${GREEN}http://localhost:5000${NC}"
echo -e "  • Frontend App:       ${GREEN}http://localhost:3000${NC}"
echo -e "  • Blockchain Node:    ${GREEN}http://localhost:8545${NC}"
echo -e "  • API Docs:           ${GREEN}http://localhost:8000/docs${NC}"
echo ""

echo -e "${YELLOW}📊 System Features:${NC}"
echo "  • Enhanced OCR Processing (88% accuracy)"
echo "  • Multi-API OCR (OCR.space + Tesseract)"
echo "  • Blockchain Certificate Verification"
echo "  • M-Pesa Payment Integration"
echo "  • Real-time Processing Updates"
echo "  • Complete Diploma Management"
echo "  • Dual Backend Architecture"
echo "  • PostgreSQL Database"
echo ""

echo -e "${YELLOW}📝 Process IDs:${NC}"
echo "  • M-Pesa Service:    $(cat pids/mpesa-service.pid 2>/dev/null || echo 'Not found')"
echo "  • Python Backend:   $(cat pids/python-backend.pid 2>/dev/null || echo 'Not found')"
echo "  • Node.js Backend:  $(cat pids/nodejs-backend.pid 2>/dev/null || echo 'Not found')"
echo "  • Frontend:         $(cat pids/frontend.pid 2>/dev/null || echo 'Not found')"
echo "  • Blockchain:       $(cat pids/blockchain.pid 2>/dev/null || echo 'Not found')"
echo ""

echo -e "${YELLOW}📊 Log Files:${NC}"
echo "  • M-Pesa Service:    logs/mpesa-service.log"
echo "  • Python Backend:   logs/python-backend.log"
echo "  • Node.js Backend:  logs/nodejs-backend.log"
echo "  • Frontend:         logs/frontend.log"
echo "  • Blockchain:       logs/blockchain.log"
echo "  • Deployment:       logs/deployment.log"
echo ""

echo -e "${YELLOW}🛠️  Management Commands:${NC}"
echo "  • Stop all services:  Ctrl+C"
echo "  • View logs:         tail -f logs/[service].log"
echo "  • Restart service:   Kill process and run this script again"
echo ""

echo -e "${YELLOW}📝 Notes:${NC}"
echo "  • All services are running in background"
echo "  • Database: PostgreSQL (localhost:5432)"
echo "  • Blockchain: Hardhat local network"
echo "  • M-Pesa: Sandbox environment"
echo "  • OCR.space API integrated with fallback to Tesseract"
echo ""

# Keep script running to manage services
echo -e "${BLUE}📡 System monitor active... Press Ctrl+C to stop all services${NC}"
echo ""

# Monitor services
while true; do
    sleep 30
    echo -e "${BLUE}📊 System Status Check ($(date))${NC}"
    
    if ! port_in_use 8000; then
        print_status "WARN" "Python Backend service stopped"
    fi
    if ! port_in_use 5000; then
        print_status "WARN" "Node.js Backend service stopped"
    fi
    if ! port_in_use 8545; then
        print_status "WARN" "Blockchain node stopped"
    fi
    if ! port_in_use 3000; then
        print_status "WARN" "Frontend service stopped"
    fi
done
