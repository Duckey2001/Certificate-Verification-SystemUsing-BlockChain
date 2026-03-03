#!/bin/bash

# CertiVert Project Startup Script

echo "🚀 Starting CertiVert Project..."
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null
    exit
}

trap cleanup SIGINT SIGTERM

# Start Backend
echo -e "${BLUE}📦 Starting Backend Server...${NC}"
cd backend
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt 2>/dev/null || echo "Some dependencies may need manual installation"
python3 main.py &
BACKEND_PID=$!
cd ..
echo -e "${GREEN}✓ Backend started on http://localhost:8000${NC}"
echo ""

# Wait a bit for backend to start
sleep 3

# Start Frontend
echo -e "${BLUE}🎨 Starting Frontend Server...${NC}"
cd frontend
npm install --silent 2>/dev/null
npm start &
FRONTEND_PID=$!
cd ..
echo -e "${GREEN}✓ Frontend started on http://localhost:3000${NC}"
echo ""

echo -e "${GREEN}✨ Both servers are running!${NC}"
echo "Backend API: http://localhost:8000"
echo "Frontend App: http://localhost:3000"
echo "API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for processes
wait
