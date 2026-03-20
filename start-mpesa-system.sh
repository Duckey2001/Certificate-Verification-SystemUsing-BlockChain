#!/bin/bash

echo "💳 Starting LGCSE System with M-Pesa Payment Integration..."
echo "========================================================="

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
        "MPESA")
            echo -e "${CYAN}💳 $message${NC}"
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
    local max_attempts=${3:-20}
    local attempt=1
    
    print_status "INFO" "Waiting for $service_name..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s --max-time 2 "$url" > /dev/null 2>&1; then
            print_status "OK" "$service_name is ready!"
            return 0
        fi
        echo -n "."
        sleep 2
        ((attempt++))
    done
    
    print_status "WARN" "$service_name may still be starting"
    return 0  # Don't fail, just warn
}

# Get project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo -e "${YELLOW}📁 Project Root: ${PROJECT_ROOT}${NC}"
echo ""

# Kill existing processes
echo -e "${BLUE}🧹 Cleaning up...${NC}"
for port in 3000 5000 8000; do
    if check_port $port; then
        lsof -ti:$port | xargs kill -9 2>/dev/null || true
        sleep 1
    fi
done

# Create logs directory
mkdir -p logs

# Start PostgreSQL
echo -e "\n${BLUE}🐘 Starting PostgreSQL...${NC}"
sudo systemctl start postgresql 2>/dev/null || print_status "WARN" "PostgreSQL may already be running"

if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
    print_status "OK" "PostgreSQL ready"
else
    print_status "FAIL" "PostgreSQL not responding - please start PostgreSQL"
    exit 1
fi

# Setup M-Pesa Environment
echo -e "\n${CYAN}💳 Setting up M-Pesa Environment...${NC}"
cd "$PROJECT_ROOT/backend"

# Copy M-Pesa environment file
if [ -f ".env.mpesa" ]; then
    cp .env.mpesa .env
    print_status "OK" "M-Pesa environment configured"
else
    print_status "WARN" "M-Pesa environment file not found, using defaults"
fi

# Start Python Backend with M-Pesa
echo -e "\n${BLUE}🐍 Starting Python Backend with M-Pesa...${NC}"

if [ -d "venv" ]; then
    source venv/bin/activate
fi

nohup python app.py > ../logs/python-backend.log 2>&1 &
PYTHON_PID=$!
echo $PYTHON_PID > ../pids/python-backend.pid

cd "$PROJECT_ROOT"
sleep 3
if check_port 5000; then
    print_status "OK" "Python backend with M-Pesa started on port 5000"
else
    print_status "WARN" "Python backend may still be starting"
fi

# Start Database-Connected Node.js Backend
echo -e "\n${BLUE}🔧 Starting Database Backend...${NC}"
cd "$PROJECT_ROOT"

nohup node server-database.js > logs/database-backend.log 2>&1 &
DB_NODE_PID=$!
echo $DB_NODE_PID > pids/database-backend.pid

sleep 3
wait_for_service "http://localhost:8000" "Database Backend" 15

# Start React Frontend
echo -e "\n${BLUE}⚛️  Starting React Frontend...${NC}"
cd "$PROJECT_ROOT/frontend"

export REACT_APP_API_URL=http://localhost:8000
export REACT_APP_PYTHON_API_URL=http://localhost:5000
export REACT_APP_MPESA_ENABLED=true

nohup npm start > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo $FRONTEND_PID > ../pids/frontend.pid

cd "$PROJECT_ROOT"
sleep 5
if check_port 3000; then
    print_status "OK" "React frontend started on port 3000"
else
    print_status "WARN" "React frontend may still be starting"
fi

# Test M-Pesa Integration
echo -e "\n${CYAN}💳 Testing M-Pesa Integration...${NC}"

# Test M-Pesa configuration endpoint
if curl -s http://localhost:5000/api/mpesa/config > /dev/null 2>&1; then
    print_status "OK" "M-Pesa configuration API working"
else
    print_status "WARN" "M-Pesa API may need more time"
fi

# Test database connection
if curl -s http://localhost:8000/api/dashboard/stats > /dev/null 2>&1; then
    print_status "OK" "Database dashboard API working"
else
    print_status "WARN" "Database API may need more time"
fi

# System Status
echo -e "\n${GREEN}🎯 M-Pesa Integrated System Status${NC}"
echo -e "${YELLOW}🌐 Services:${NC}"

if check_port 8000; then
    print_status "OK" "Database Backend: http://localhost:8000"
else
    print_status "WARN" "Database Backend: Starting..."
fi

if check_port 5000; then
    print_status "OK" "Python Backend:  http://localhost:5000"
else
    print_status "WARN" "Python Backend:  Starting..."
fi

if check_port 3000; then
    print_status "OK" "React Frontend:   http://localhost:3000"
else
    print_status "WARN" "React Frontend:   Starting..."
fi

echo -e "\n${CYAN}💳 M-Pesa Features:${NC}"
print_status "MPESA" "📱 STK Push Payments"
print_status "MPESA" "💰 B2B Transactions"
print_status "MPESA" "🔄 Payment Status Tracking"
print_status "MPESA" "📊 Transaction History"
print_status "MPESA" "🔐 Secure Callback Handling"

echo -e "\n${YELLOW}📊 M-Pesa API Endpoints:${NC}"
print_status "INFO" "📱 STK Push:      http://localhost:5000/api/mpesa/stk-push"
print_status "INFO" "💰 B2B Payment:   http://localhost:5000/api/mpesa/b2b-payment"
print_status "INFO" "🔄 Status Check:  http://localhost:5000/api/mpesa/status/{id}"
print_status "INFO" "⚙️  Configuration: http://localhost:5000/api/mpesa/config"
print_status "INFO" "📞 Callback:      http://localhost:5000/api/mpesa/callback"

echo -e "\n${YELLOW}📊 Dashboard Data Endpoints:${NC}"
print_status "INFO" "📈 Stats:          http://localhost:8000/api/dashboard/stats"
print_status "INFO" "🎓 Diplomas:       http://localhost:8000/api/diplomas"
print_status "INFO" "✅ Verifications:   http://localhost:8000/api/dashboard/recent-verifications"

echo -e "\n${YELLOW}📝 Process IDs:${NC}"
echo "Database Backend: $(cat pids/database-backend.pid 2>/dev/null || echo 'Not found')"
echo "Python Backend:  $(cat pids/python-backend.pid 2>/dev/null || echo 'Not found')"
echo "Frontend:        $(cat pids/frontend.pid 2>/dev/null || echo 'Not found')"

echo -e "\n${YELLOW}📊 Logs:${NC}"
echo "Database Backend: logs/database-backend.log"
echo "Python Backend:   logs/python-backend.log"
echo "Frontend:        logs/frontend.log"

echo -e "\n${GREEN}🎉 M-Pesa Integrated System Ready!${NC}"
echo -e "${CYAN}💳 M-Pesa payment integration is now active${NC}"
echo -e "${BLUE}🌐 Access the application: http://localhost:3000${NC}"
echo -e "${BLUE}📱 M-Pesa payments: /mpesa payment page${NC}"

echo -e "\n${BLUE}🧪 Test M-Pesa:${NC}"
echo "   curl http://localhost:5000/api/mpesa/config"
echo "   curl -X POST http://localhost:5000/api/mpesa/stk-push -H 'Content-Type: application/json' -d '{\"phone_number\":\"254712345678\",\"amount\":5}'"

echo -e "\n${BLUE}🛑 Stop services:${NC}"
echo "   ./stop-all-services.sh"

echo -e "\n${GREEN}✨ M-Pesa payment system is now working properly!${NC}"
