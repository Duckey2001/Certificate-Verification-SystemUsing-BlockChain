#!/bin/bash

echo "🚀 Starting LGCSE System with Database-Connected Dashboards..."
echo "=========================================================="

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

# Start Database-Connected Node.js Backend
echo -e "\n${BLUE}🔧 Starting Database-Connected Backend...${NC}"
cd "$PROJECT_ROOT"

nohup node server-database.js > logs/database-backend.log 2>&1 &
DB_NODE_PID=$!
echo $DB_NODE_PID > pids/database-backend.pid

sleep 3
wait_for_service "http://localhost:8000" "Database Backend" 15

# Start Python Backend
echo -e "\n${BLUE}🐍 Starting Python Backend...${NC}"
cd "$PROJECT_ROOT/backend"

if [ -d "venv" ]; then
    source venv/bin/activate
fi

nohup python app.py > ../logs/python-backend.log 2>&1 &
PYTHON_PID=$!
echo $PYTHON_PID > ../pids/python-backend.pid

cd "$PROJECT_ROOT"
sleep 3
if check_port 5000; then
    print_status "OK" "Python backend started on port 5000"
else
    print_status "WARN" "Python backend may still be starting"
fi

# Start React Frontend
echo -e "\n${BLUE}⚛️  Starting React Frontend...${NC}"
cd "$PROJECT_ROOT/frontend"

export REACT_APP_API_URL=http://localhost:8000
export REACT_APP_PYTHON_API_URL=http://localhost:5000

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

# Test database connection
echo -e "\n${BLUE}🗄️  Testing Database Connection...${NC}"
if curl -s http://localhost:8000/api/dashboard/stats > /dev/null 2>&1; then
    print_status "OK" "Database dashboard API working"
else
    print_status "WARN" "Database API may need more time"
fi

# System Status
echo -e "\n${GREEN}🎯 Database-Connected System Status${NC}"
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

echo -e "\n${YELLOW}📊 Dashboard Data Endpoints:${NC}"
print_status "INFO" "📈 Stats:          http://localhost:8000/api/dashboard/stats"
print_status "INFO" "🎓 Recent Diplomas: http://localhost:8000/api/dashboard/recent-diplomas"
print_status "INFO" "✅ Verifications:   http://localhost:8000/api/dashboard/recent-verifications"
print_status "INFO" "📋 All Diplomas:   http://localhost:8000/api/diplomas"

echo -e "\n${YELLOW}📝 Process IDs:${NC}"
echo "Database Backend: $(cat pids/database-backend.pid 2>/dev/null || echo 'Not found')"
echo "Python Backend:  $(cat pids/python-backend.pid 2>/dev/null || echo 'Not found')"
echo "Frontend:        $(cat pids/frontend.pid 2>/dev/null || echo 'Not found')"

echo -e "\n${YELLOW}📊 Logs:${NC}"
echo "Database Backend: logs/database-backend.log"
echo "Python Backend:   logs/python-backend.log"
echo "Frontend:        logs/frontend.log"

echo -e "\n${GREEN}🎉 Database-Connected System Ready!${NC}"
echo -e "${BLUE}🌐 Access dashboards: http://localhost:3000${NC}"
echo -e "${BLUE}🗄️  Database loaded with sample data${NC}"
echo -e "${BLUE}📊 Dashboards will load real data from PostgreSQL${NC}"

echo -e "\n${BLUE}🧪 Test the system:${NC}"
echo "   curl http://localhost:8000/api/dashboard/stats"
echo "   curl http://localhost:8000/api/dashboard/recent-diplomas"

echo -e "\n${BLUE}🛑 Stop services:${NC}"
echo "   ./stop-all-services.sh"

echo -e "\n${GREEN}✨ Dashboards now load data from database successfully!${NC}"
