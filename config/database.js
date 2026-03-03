// config/database.js
const { Pool } = require('pg');

const pool = new Pool({
    user: 'certivert',
    host: 'localhost',
    database: 'CertiVert',
    password: process.env.PG_PASSWORD || 'your_password_here',
    port: 5432,
    
    // Pool settings
    max: 10, // Maximum number of clients in the pool
    idleTimeoutMillis: 10000, // Close idle clients after 10 seconds
    connectionTimeoutMillis: 0, // No timeout for connection attempts
    
    // Query timeouts (optional, may be overridden per-query)
    statement_timeout: 30000, // 30 seconds
    query_timeout: 30000, // 30 seconds
});

module.exports = pool;
