const express = require('express');
const cors = require('cors');
const morgan = require('morgan');
const http = require('http');
const WebSocket = require('ws');
const { Pool } = require('pg');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// Database connection
const pool = new Pool({
  user: 'diploma_admin',
  host: 'localhost',
  database: 'diploma_verification',
  password: 'diploma_admin',
  port: 5432,
});

// Test database connection
pool.query('SELECT NOW()', (err, res) => {
  if (err) {
    console.error('Database connection error:', err);
  } else {
    console.log('✅ Database connected successfully at:', res.rows[0].now);
  }
});

// CORS configuration
app.use(cors({
  origin: ['http://localhost:3000', 'http://localhost:3001', 'http://127.0.0.1:3000'],
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With']
}));

app.use(express.json());
app.use(morgan('dev'));

// Helper function to handle database queries
const query = async (text, params) => {
  const start = Date.now();
  try {
    const res = await pool.query(text, params);
    const duration = Date.now() - start;
    console.log('Executed query', { text, duration, rows: res.rowCount });
    return res;
  } catch (error) {
    console.error('Database query error:', error);
    throw error;
  }
};

// WebSocket handler
wss.on('connection', (ws, req) => {
  console.log('WebSocket client connected');
  
  ws.send(JSON.stringify({
    type: 'connection',
    message: 'Connected to server',
    timestamp: new Date().toISOString()
  }));
  
  ws.on('message', (message) => {
    try {
      const data = JSON.parse(message);
      ws.send(JSON.stringify({
        type: 'response',
        data: data,
        timestamp: new Date().toISOString()
      }));
    } catch (error) {
      console.error('Error parsing message:', error);
    }
  });
  
  ws.on('close', () => {
    console.log('WebSocket client disconnected');
  });
});

// API Routes
app.get('/api/health', (req, res) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() });
});

// Authentication routes
app.post('/api/auth/login', async (req, res) => {
  try {
    const { username, password } = req.body;
    
    if (!username || !password) {
      return res.status(400).json({ message: 'Username and password required' });
    }

    // Query user from database
    const result = await query(
      'SELECT id, username, email, role FROM users WHERE username = $1',
      [username]
    );

    if (result.rows.length === 0) {
      return res.status(401).json({ message: 'Invalid credentials' });
    }

    const user = result.rows[0];
    
    // For now, accept any password (in production, use bcrypt)
    const token = 'jwt-token-' + Math.random().toString(36).substring(2);
    
    res.json({
      token: token,
      user: {
        id: user.id,
        username: user.username,
        email: user.email,
        role: user.role
      },
      message: 'Login successful'
    });
  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ message: 'Login failed' });
  }
});

app.get('/api/auth/me', async (req, res) => {
  try {
    const authHeader = req.headers.authorization;
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      return res.status(401).json({ message: 'Unauthorized' });
    }

    // For now, return a mock user (in production, verify JWT)
    const result = await query(
      'SELECT id, username, email, role FROM users WHERE username = $1',
      ['test_verifier']
    );

    if (result.rows.length === 0) {
      return res.status(401).json({ message: 'User not found' });
    }

    res.json({ user: result.rows[0] });
  } catch (error) {
    console.error('Auth me error:', error);
    res.status(500).json({ message: 'Authentication failed' });
  }
});

// Verifier stats
app.get('/verifier/stats', async (req, res) => {
  try {
    const stats = {};
    
    // Get total verifications
    const verificationResult = await query('SELECT COUNT(*) as count FROM verification_logs');
    stats.totalVerifications = parseInt(verificationResult.rows[0].count);
    
    // Get valid certificates
    const validResult = await query(
      'SELECT COUNT(*) as count FROM certificates WHERE status = $1',
      ['verified']
    );
    stats.validCertificates = parseInt(validResult.rows[0].count);
    
    // Get invalid certificates
    const invalidResult = await query(
      'SELECT COUNT(*) as count FROM certificates WHERE status = $1',
      ['invalid']
    );
    stats.invalidCertificates = parseInt(invalidResult.rows[0].count);
    
    // Get total fees earned
    const feesResult = await query('SELECT COALESCE(SUM(amount), 0) as total FROM payments WHERE status = $1', ['completed']);
    stats.feesEarned = parseFloat(feesResult.rows[0].total);
    stats.currency = 'LSL';
    
    res.json(stats);
  } catch (error) {
    console.error('Verifier stats error:', error);
    res.status(500).json({ message: 'Failed to fetch stats' });
  }
});

// My verifications
app.get('/certificates/my-verifications', async (req, res) => {
  try {
    const { limit = 50, offset = 0 } = req.query;
    
    const result = await query(
      `SELECT id, certificate_hash, student_name, institution, 
              issue_date, status, verification_date
       FROM certificates 
       ORDER BY verification_date DESC 
       LIMIT $1 OFFSET $2`,
      [parseInt(limit), parseInt(offset)]
    );
    
    const countResult = await query('SELECT COUNT(*) as total FROM certificates');
    
    res.json({
      certificates: result.rows,
      total: parseInt(countResult.rows[0].total),
      limit: parseInt(limit),
      offset: parseInt(offset)
    });
  } catch (error) {
    console.error('My verifications error:', error);
    res.status(500).json({ message: 'Failed to fetch verifications' });
  }
});

// Recent activities
app.get('/activities/recent', async (req, res) => {
  try {
    const result = await query(
      `SELECT id, type, description, timestamp, user_id 
       FROM verification_logs 
       ORDER BY timestamp DESC 
       LIMIT 10`
    );
    
    res.json(result.rows);
  } catch (error) {
    console.error('Recent activities error:', error);
    res.status(500).json({ message: 'Failed to fetch activities' });
  }
});

// Payments
app.get('/payments/my', async (req, res) => {
  try {
    const result = await query(
      `SELECT id, amount, currency, status, transaction_id, timestamp, type
       FROM payments 
       ORDER BY timestamp DESC 
       LIMIT 20`
    );
    
    res.json(result.rows);
  } catch (error) {
    console.error('Payments error:', error);
    res.status(500).json({ message: 'Failed to fetch payments' });
  }
});

// Certificate verification
app.post('/certificates/verify', async (req, res) => {
  try {
    const { certificate_hash } = req.body;
    
    if (!certificate_hash) {
      return res.status(400).json({ message: 'Certificate hash required' });
    }

    // Check if certificate exists
    const certResult = await query(
      'SELECT * FROM certificates WHERE certificate_hash = $1',
      [certificate_hash]
    );

    if (certResult.rows.length === 0) {
      return res.json({
        verified: false,
        valid: false,
        message: 'Certificate not found'
      });
    }

    const certificate = certResult.rows[0];
    
    // Log verification
    await query(
      `INSERT INTO verification_logs (certificate_id, type, description, timestamp, user_id)
       VALUES ($1, $2, $3, NOW(), $4)`,
      [certificate.id, 'verification', 'Certificate verified', 1]
    );

    res.json({
      verified: true,
      valid: certificate.status === 'verified',
      blockchain_verified: certificate.blockchain_verified,
      certificate: certificate,
      message: certificate.status === 'verified' ? 'Certificate is valid' : 'Certificate verification failed'
    });
  } catch (error) {
    console.error('Certificate verification error:', error);
    res.status(500).json({ message: 'Verification failed' });
  }
});

// Error handling
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Something went wrong!' });
});

const PORT = 8000;

server.listen(PORT, () => {
  console.log(`🚀 Database-integrated server running on port ${PORT}`);
  console.log(`📡 API available at http://localhost:${PORT}/api`);
  console.log(`🔌 WebSocket server running on ws://localhost:${PORT}`);
  console.log(`🗄️ Connected to PostgreSQL database`);
});

// Graceful shutdown
process.on('SIGINT', () => {
  console.log('Shutting down gracefully...');
  pool.end(() => {
    server.close(() => {
      console.log('Server closed');
      process.exit(0);
    });
  });
});