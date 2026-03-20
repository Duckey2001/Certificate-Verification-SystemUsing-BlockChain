#!/bin/bash

# Enhanced M-Pesa System Quick Start
# Launches the unified M-Pesa backend with all payment flows

echo "🚀 Enhanced M-Pesa System Quick Start"
echo "====================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed"
    exit 1
fi

# Check if required directories exist
if [ ! -f "mpesa-real-backend.py" ]; then
    echo "❌ mpesa-real-backend.py not found in current directory"
    exit 1
fi

# Check for backend directory
if [ ! -d "backend" ]; then
    echo "❌ backend directory not found"
    exit 1
fi

# Check for M-Pesa client
if [ ! -f "backend/mpesa_client.py" ]; then
    echo "❌ backend/mpesa_client.py not found"
    exit 1
fi

# Environment setup
echo "🔧 Setting up environment..."

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    if [ -f ".env.mpesa" ]; then
        cp .env.mpesa .env
        echo "✅ Environment configured from .env.mpesa"
        echo "⚠️  Please edit .env with your actual M-Pesa credentials"
    else
        echo "⚠️  No .env file found, using defaults"
    fi
else
    echo "✅ Environment file exists"
fi

# Install Python dependencies if needed
echo "📦 Checking dependencies..."

# Check for Flask
python3 -c "import flask" 2>/dev/null || {
    echo "📦 Installing Flask..."
    pip3 install flask flask-cors requests python-dotenv pycryptodome
}

# Check for other dependencies
python3 -c "import requests" 2>/dev/null || pip3 install requests
python3 -c "import Crypto" 2>/dev/null || pip3 install pycryptodome

echo "✅ Dependencies checked"

# Kill any existing processes on port 5000
echo "🧹 Cleaning up existing processes..."
pkill -f "mpesa-real-backend.py" 2>/dev/null || true
pkill -f "python.*5000" 2>/dev/null || true

# Wait a moment for cleanup
sleep 2

# Start the enhanced M-Pesa backend
echo "🚀 Starting Enhanced M-Pesa Backend..."
echo "📱 USSD Popup Flow: ✅ Available"
echo "💳 Real M-Pesa B2B: ✅ Available" 
echo "📨 SMS Gateway: ✅ Available"
echo "🔄 Legacy Compatibility: ✅ Available"
echo ""
echo "🌐 Server will be available at: http://localhost:5000"
echo "📊 Health Check: http://localhost:5000/api/health"
echo "🔧 Configuration: http://localhost:5000/api/mpesa/config"
echo ""
echo "🧪 To test the system, run:"
echo "   python3 test_mpesa_complete.py"
echo ""
echo "📱 For USSD popup test, open:"
echo "   ussd_popup_test.html"
echo ""
echo "⚠️  Press Ctrl+C to stop the server"
echo "====================================="

# Launch the backend
python3 mpesa-real-backend.py
