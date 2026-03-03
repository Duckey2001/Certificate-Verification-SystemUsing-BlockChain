// App configuration - uses env vars (set in .env)
// REACT_APP_API_URL should not include trailing slash
// Default backend runs on port 8002 (updated due to port conflicts)
export const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8002';
export const API_BASE = `${API_URL.replace(/\/$/, '')}/api`;
