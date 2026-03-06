// App configuration - uses env vars (set in .env)
// REACT_APP_API_URL should not include trailing slash
// Default backend runs on port 5000 (updated due to port conflicts)
export const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';
export const API_BASE = `${API_URL.replace(/\/$/, '')}/api`;
