#!/bin/bash

echo "🛑 Stopping All LGCSE System Services..."
echo "========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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
    esac
}

# Function to kill process by port
kill_port() {
    local port=$1
    local service_name=$2
    
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_status "INFO" "Stopping $service_name (port $port)..."
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 2
        
        if ! lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            print_status "OK" "$service_name stopped"
        else
            print_status "WARN" "$service_name may still be running"
        fi
    else
        print_status "INFO" "$service_name was not running"
    fi
}

# Function to kill by PID file
kill_pid() {
    local pid_file=$1
    local service_name=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            print_status "INFO" "Stopping $service_name (PID: $pid)..."
            kill "$pid" 2>/dev/null || true
            sleep 2
            
            if ! kill -0 "$pid" 2>/dev/null; then
                print_status "OK" "$service_name stopped"
            else
                print_status "WARN" "Force killing $service_name..."
                kill -9 "$pid" 2>/dev/null || true
            fi
        fi
        rm -f "$pid_file"
    fi
}

echo -e "\n${BLUE}🔧 Stopping Services by Port...${NC}"

# Kill services by port
kill_port 3000 "React Frontend"
kill_port 5000 "Node.js Backend"
kill_port 8000 "Python Backend"
kill_port 8545 "Blockchain Node"

echo -e "\n${BLUE}🗂️  Cleaning Up PID Files...${NC}"

# Kill by PID files
kill_pid "pids/mpesa-service.pid" "M-Pesa Service"
kill_pid "pids/python-backend.pid" "Python Backend"
kill_pid "pids/nodejs-backend.pid" "Node.js Backend"
kill_pid "pids/frontend.pid" "React Frontend"
kill_pid "pids/blockchain.pid" "Blockchain Node"

echo -e "\n${BLUE}🧹 Cleaning Up Process Names...${NC}"

# Kill by process names
print_status "INFO" "Cleaning up remaining processes..."

# Node.js processes
pkill -f "node.*server.js" 2>/dev/null || true
pkill -f "npm.*start" 2>/dev/null || true
pkill -f "react-scripts.*start" 2>/dev/null || true

# Python processes
pkill -f "python.*app.py" 2>/dev/null || true
pkill -f "python.*main.py" 2>/dev/null || true
pkill -f "python.*mpesa-real-backend.py" 2>/dev/null || true
pkill -f "uvicorn.*main:app" 2>/dev/null || true

# Blockchain processes
pkill -f "hardhat.*node" 2>/dev/null || true
pkill -f "ganache-cli" 2>/dev/null || true
pkill -f "npx.*hardhat" 2>/dev/null || true

# Fabric processes (if running)
pkill -f "fabric-ca-server" 2>/dev/null || true
pkill -f "orderer" 2>/dev/null || true
pkill -f "peer.*node" 2>/dev/null || true

echo -e "\n${BLUE}📊 Final Status Check...${NC}"

# Check if ports are still in use
ports_still_in_use=0

for port in 3000 5000 8000 8545; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        print_status "WARN" "Port $port still in use"
        echo "   Processes: $(lsof -Pi :$port -sTCP:LISTEN | tail -n +2)"
        ((ports_still_in_use++))
    else
        print_status "OK" "Port $port is free"
    fi
done

echo -e "\n${BLUE}📝 Cleanup Summary...${NC}"

# Remove log files if they exist
if [ -f "node_backend.log" ]; then
    print_status "INFO" "Found Node.js backend log"
fi

if [ -f "backend/python_backend.log" ]; then
    print_status "INFO" "Found Python backend log"
fi

if [ -f "frontend/frontend.log" ]; then
    print_status "INFO" "Found frontend log"
fi

# Remove temporary files
rm -f *.pid
rm -f backend/*.pid
rm -f frontend/*.pid
rm -f blockchain/*.pid

if [ $ports_still_in_use -eq 0 ]; then
    print_status "OK" "All services stopped successfully! 🎉"
else
    print_status "WARN" "Some services may still be running"
    echo "   You may need to manually kill the processes shown above"
fi

echo -e "\n${BLUE}🔄 To restart the system:${NC}"
echo "   ./start-complete-system.sh"

echo -e "\n${GREEN}✨ Stop script completed!${NC}"
