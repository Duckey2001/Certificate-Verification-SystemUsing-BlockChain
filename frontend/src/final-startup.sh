#!/bin/bash

echo "🚀 FINAL SYSTEM STARTUP WITH FIXED NETWORK"
echo "=========================================="

# Stop everything
echo "1. Stopping all processes..."
pkill -f "node server.js" 2>/dev/null
pkill -f "npm start" 2>/dev/null
pkill -f "ganache" 2>/dev/null
sleep 2

# Clean old networks
echo "2. Cleaning old networks..."
cd ~/certivert-blockchain
npx truffle networks --clean 2>/dev/null

# Start Ganache with fixed network ID
echo "3. Starting Ganache (Network ID: 1337)..."
cd ~/certivert-blockchain
gnome-terminal --title="⛓ GANACHE (Network:1337)" -- bash -c "
    echo '================================';
    echo 'GANACHE BLOCKCHAIN';
    echo 'Network ID: 1337';
    echo 'RPC: http://127.0.0.1:8545';
    echo '================================';
    npx ganache --server.port 8545 --database.dbPath ./ganache_data --wallet.deterministic true --chain.networkId 1337 --chain.chainId 1337;
    exec bash"

echo "   ⏳ Waiting 10 seconds for blockchain..."
sleep 10

# Deploy contract
echo "4. Deploying smart contract..."
cd ~/certivert-blockchain
npx truffle migrate --network development

sleep 3

# Start Backend
echo "5. Starting Backend Server..."
cd ~/certivert-backend
gnome-terminal --title="🔧 BACKEND (:5000)" -- bash -c "
    echo '================================';
    echo 'NODE.JS BACKEND API';
    echo 'Port: 5000';
    echo 'PostgreSQL + Blockchain';
    echo '================================';
    npm start;
    exec bash"

sleep 5

# Start Frontend
echo "6. Starting Frontend..."
cd ~/Documents/Certivert\ project/frontend
gnome-terminal --title="🌐 FRONTEND (:3000)" -- bash -c "
    echo '================================';
    echo 'REACT FRONTEND';
    echo 'Port: 3000';
    echo 'Vite + React';
    echo '================================';
    npm start;
    exec bash"

echo
echo "✅ SYSTEM STARTED!"
echo "=========================================="
echo "🌐 Frontend:   http://localhost:3000"
echo "🔧 Backend:    http://localhost:5000"
echo "⛓ Blockchain: http://127.0.0.1:8545"
echo "📡 Network ID: 1337"
echo "=========================================="
echo "🔑 Login: admin@ecol.org.ls / password123"
echo "=========================================="

# Test after 5 seconds
sleep 5
echo
echo "🧪 Running tests..."
echo "1. Testing blockchain:"
curl -X POST http://127.0.0.1:8545 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"net_version","params":[],"id":1}' \
  -s | jq '.result' 2>/dev/null || echo "Checking..."

echo "2. Testing backend login:"
curl -X POST http://localhost:5000/api/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@ecol.org.ls","password":"password123","role":"issuer"}' \
  -s | grep -o '"success":true' && echo "✅ Login works!" || echo "Checking..."

echo "3. Testing blockchain status:"
curl -s http://localhost:5000/api/blockchain-status | grep -o '"connected":true' && echo "✅ Blockchain connected!" || echo "Checking..."
