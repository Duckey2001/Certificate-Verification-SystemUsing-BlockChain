#!/bin/bash

echo "🎯 FINAL FRONTEND FIX"
echo

cd ~/Documents/Certivert\ project/frontend

# 1. Fix main.jsx imports
echo "1. Fixing main.jsx..."
cat > src/main.jsx << 'MAIN_EOF'
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./Pages/App.jsx";
import "./Pages/index.css";

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>
);
MAIN_EOF

# 2. Fix App.jsx if needed
echo "2. Checking App.jsx..."
if [ ! -s "src/Pages/App.jsx" ] || [ $(stat -c%s "src/Pages/App.jsx") -lt 100 ]; then
    echo "   Updating App.jsx..."
    cat > src/Pages/App.jsx << 'APP_EOF'
import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import Login from './Login.jsx'
import IssuerDashboard from './IssuerDashboard.jsx'
import VerifierDashboard from './VerifierDashboard.jsx'
import AdminDashboard from './AdminDashboard.jsx'
import Layout from '../Layout.jsx'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" />} />
      <Route path="/login" element={<Login />} />
      <Route path="/issuer-dashboard" element={<Layout><IssuerDashboard /></Layout>} />
      <Route path="/verifier-dashboard" element={<Layout><VerifierDashboard /></Layout>} />
      <Route path="/admin-dashboard" element={<Layout><AdminDashboard /></Layout>} />
    </Routes>
  )
}

export default App
APP_EOF
fi

# 3. Create vite.config.js
echo "3. Creating vite.config.js..."
cat > vite.config.js << 'VITE_EOF'
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true,
    open: true
  }
})
VITE_EOF

# 4. Restart
echo "4. Restarting frontend..."
pkill -f "vite" 2>/dev/null
sleep 2

echo "Starting on port 3000..."
npm start

echo
echo "✅ Frontend should open automatically on http://localhost:3000"
echo "🔑 Login: admin@ecol.org.ls / password123"
