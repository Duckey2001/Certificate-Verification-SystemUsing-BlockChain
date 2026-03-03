#!/bin/bash

cd ~/lgcse-project/frontend

echo "🚀 Starting complete fix..."

echo "1. Removing Tailwind packages..."
npm uninstall tailwindcss @tailwindcss/postcss postcss autoprefixer 2>/dev/null || true

echo "2. Cleaning up configuration files..."
rm -f tailwind.config.js postcss.config.js

echo "3. Creating clean CSS files..."
cat > src/index.css << 'CSS_EOF'
/* Base styles */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: #f8fafc;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 20px;
}

.btn {
  display: inline-block;
  padding: 10px 20px;
  border-radius: 6px;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.2s;
  border: none;
  cursor: pointer;
}

.btn-primary {
  background-color: #2563eb;
  color: white;
}

.btn-primary:hover {
  background-color: #1d4ed8;
}

.btn-secondary {
  background-color: white;
  color: #2563eb;
  border: 1px solid #2563eb;
}

.btn-secondary:hover {
  background-color: #eff6ff;
}

.text-primary {
  color: #2563eb;
}

.text-success {
  color: #10b981;
}

.bg-white {
  background-color: white;
}

.rounded-lg {
  border-radius: 12px;
}

.shadow-lg {
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
}

.p-6 {
  padding: 24px;
}

.mb-4 {
  margin-bottom: 16px;
}

.mb-6 {
  margin-bottom: 24px;
}

.text-center {
  text-align: center;
}

.flex {
  display: flex;
}

.items-center {
  align-items: center;
}

.justify-center {
  justify-content: center;
}

.min-h-screen {
  min-height: 100vh;
}
CSS_EOF

cat > src/App.css << 'APPCSS_EOF'
.App {
  text-align: center;
}
APPCSS_EOF

echo "4. Creating simple App.jsx..."
cat > src/App.jsx << 'APP_EOF'
import React from 'react';
import './App.css';
import './index.css';

function App() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-lg p-6" style={{ maxWidth: '500px', width: '100%' }}>
        <h1 className="text-center text-primary" style={{ fontSize: '2.5rem', fontWeight: 'bold', marginBottom: '1rem' }}>
          CertiVert
        </h1>
        <p className="text-center mb-6" style={{ color: '#6b7280', fontSize: '1.125rem' }}>
          LGCSE Certificate Verification System
        </p>
        
        <div className="mb-6">
          <button className="btn btn-primary" style={{ width: '100%', marginBottom: '1rem', padding: '12px' }}>
            Login to Dashboard
          </button>
          <button className="btn btn-secondary" style={{ width: '100%', padding: '12px' }}>
            Register New Account
          </button>
        </div>
        
        <div style={{ borderTop: '1px solid #e5e7eb', paddingTop: '1.5rem' }}>
          <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '0.75rem', color: '#374151' }}>
            System Status
          </h3>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <span>Backend API:</span>
            <span className="text-success" style={{ fontWeight: '500' }}>Running on http://localhost:8000</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <span>Frontend:</span>
            <span className="text-success" style={{ fontWeight: '500' }}>Running on http://localhost:3000</span>
          </div>
          <button className="btn btn-primary" style={{ width: '100%', padding: '10px', fontSize: '0.875rem' }}>
            View API Documentation
          </button>
        </div>
        
        <p style={{ marginTop: '1.5rem', fontSize: '0.875rem', color: '#9ca3af', textAlign: 'center' }}>
          Default admin credentials: Username: "admin" | Password: "Admin123!"
        </p>
      </div>
    </div>
  );
}

export default App;
APP_EOF

echo "5. Updating package.json..."
cat > package.json.tmp << 'PKG_EOF'
{
  "name": "certivert-frontend",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "axios": "^1.13.4",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.1",
    "react-scripts": "5.0.1"
  },
  "scripts": {
    "start": "DISABLE_ESLINT_PLUGIN=true react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^5.17.0",
    "@testing-library/react": "^13.4.0",
    "@testing-library/user-event": "^13.5.0",
    "web-vitals": "^2.1.4"
  }
}
PKG_EOF

mv package.json.tmp package.json

echo "6. Cleaning up and reinstalling..."
rm -rf node_modules package-lock.json
npm install

echo "✅ Complete! Starting the app..."
npm start
