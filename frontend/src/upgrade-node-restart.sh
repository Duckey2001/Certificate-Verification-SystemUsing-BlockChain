#!/bin/bash

echo "🔄 Upgrading Node.js and restarting frontend..."
echo

# Stop frontend
echo "1. Stopping frontend..."
pkill -f "npm start" 2>/dev/null
sleep 2

# Upgrade Node.js to version 20
echo "2. Upgrading Node.js to version 20..."
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs -y

echo "3. Verifying Node.js version..."
node --version
npm --version

# Fix frontend dependencies
echo "4. Fixing frontend dependencies..."
cd ~/Documents/Certivert\ project/frontend
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps

# Restart frontend
echo "5. Restarting frontend..."
gnome-terminal --title="🌐 FRONTEND (:3000)" -- bash -c "
    echo '================================';
    echo 'REACT FRONTEND (Node.js '$(node --version)')';
    echo 'Port: 3000';
    echo '================================';
    npm start;
    exec bash"

echo
echo "✅ Frontend should now start successfully!"
echo "🌐 Open: http://localhost:3000"
echo "🔑 Login: admin@ecol.org.ls / password123"
