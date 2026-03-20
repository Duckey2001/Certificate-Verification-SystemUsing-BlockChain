const express = require('express');
const { Pool } = require('pg');
const cors = require('cors');
const crypto = require('crypto');
const QRCode = require('qrcode');

// Load environment variables
require('dotenv').config();

const app = express();

// CORS configuration
app.use(cors({
    origin: ['http://localhost:3000', 'http://localhost:3001'],
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization']
}));

app.use(express.json());

// PostgreSQL connection
const pool = new Pool({
    user: process.env.POSTGRES_USER || 'diploma_admin',
    host: process.env.POSTGRES_HOST || 'localhost',
    database: process.env.POSTGRES_DB || 'diploma_verification',
    password: process.env.POSTGRES_PASSWORD || 'diploma1234',
    port: process.env.POSTGRES_PORT || 5432,
    max: 10,
    idleTimeoutMillis: 10000,
    connectionTimeoutMillis: 0
});

// Database initialization
async function initializeDatabase() {
    try {
        console.log('🔧 Initializing database...');
        
        // Users table
        await pool.query(`
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                name VARCHAR(255),
                role VARCHAR(50) DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        `);

        // Diplomas table
        await pool.query(`
            CREATE TABLE IF NOT EXISTS diplomas (
                id SERIAL PRIMARY KEY,
                certificate_hash VARCHAR(255) UNIQUE NOT NULL,
                student_id VARCHAR(50) NOT NULL,
                student_name VARCHAR(255) NOT NULL,
                exam_year INTEGER NOT NULL,
                subjects JSONB,
                issued_by VARCHAR(100) DEFAULT 'LGCSE',
                issue_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                revoked BOOLEAN DEFAULT FALSE,
                qr_code TEXT,
                pdf_path VARCHAR(500),
                status VARCHAR(50) DEFAULT 'active'
            )
        `);

        // Verifications table
        await pool.query(`
            CREATE TABLE IF NOT EXISTS verifications (
                id SERIAL PRIMARY KEY,
                certificate_hash VARCHAR(255),
                verifier VARCHAR(100),
                verification_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_valid BOOLEAN,
                verification_method VARCHAR(50)
            )
        `);

        // Insert sample data if tables are empty
        const userCount = await pool.query('SELECT COUNT(*) FROM users');
        if (parseInt(userCount.rows[0].count) === 0) {
            await pool.query(`
                INSERT INTO users (email, password, name, role) VALUES
                ('admin@lgcse.org', '$2b$10$example.hash.here', 'System Administrator', 'admin'),
                ('issuer@lgcse.org', '$2b$10$example.hash.here', 'Certificate Issuer', 'issuer'),
                ('verifier@lgcse.org', '$2b$10$example.hash.here', 'Certificate Verifier', 'verifier'),
                ('student@example.com', '$2b$10$example.hash.here', 'John Student', 'student')
            `);
            console.log('✅ Sample users inserted');
        }

        const diplomaCount = await pool.query('SELECT COUNT(*) FROM diplomas');
        if (parseInt(diplomaCount.rows[0].count) === 0) {
            await pool.query(`
                INSERT INTO diplomas (certificate_hash, student_id, student_name, exam_year, subjects, status) VALUES
                ('LGCSE-2024-001', 'STU001', 'Alice Johnson', 2024, '["Mathematics", "English", "Science", "History"]', 'active'),
                ('LGCSE-2024-002', 'STU002', 'Bob Smith', 2024, '["Mathematics", "Physics", "Chemistry", "Biology"]', 'active'),
                ('LGCSE-2024-003', 'STU003', 'Carol Davis', 2023, '["English", "Literature", "History", "Geography"]', 'active'),
                ('LGCSE-2024-004', 'STU004', 'David Wilson', 2023, '["Computer Science", "Mathematics", "Physics"]', 'active'),
                ('LGCSE-2024-005', 'STU005', 'Emma Brown', 2024, '["Art", "Music", "Drama", "English"]', 'active')
            `);
            console.log('✅ Sample diplomas inserted');
        }

        const verificationCount = await pool.query('SELECT COUNT(*) FROM verifications');
        if (parseInt(verificationCount.rows[0].count) === 0) {
            await pool.query(`
                INSERT INTO verifications (certificate_hash, verifier, is_valid, verification_method) VALUES
                ('LGCSE-2024-001', 'System Administrator', true, 'blockchain'),
                ('LGCSE-2024-002', 'Certificate Verifier', true, 'manual'),
                ('LGCSE-2024-003', 'Certificate Verifier', true, 'blockchain'),
                ('LGCSE-2024-004', 'System Administrator', true, 'manual'),
                ('LGCSE-2024-005', 'Certificate Verifier', true, 'blockchain')
            `);
            console.log('✅ Sample verifications inserted');
        }

        console.log('✅ Database initialized successfully');
        return true;
    } catch (error) {
        console.error('❌ Database initialization error:', error);
        return false;
    }
}

// Auth routes
app.post('/api/auth/login', async (req, res) => {
    try {
        const { email, password } = req.body;
        
        // Simple authentication for demo
        const result = await pool.query(
            'SELECT * FROM users WHERE email = $1',
            [email]
        );
        
        if (result.rows.length > 0) {
            const user = result.rows[0];
            res.json({
                success: true,
                token: 'demo-token-' + user.id,
                user: {
                    id: user.id,
                    email: user.email,
                    name: user.name,
                    role: user.role
                }
            });
        } else {
            res.status(401).json({ success: false, message: 'Invalid credentials' });
        }
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.get('/api/auth/me', async (req, res) => {
    try {
        res.json({
            success: true,
            user: {
                id: 1,
                email: 'admin@lgcse.org',
                name: 'System Administrator',
                role: 'admin'
            }
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Dashboard data routes
app.get('/api/dashboard/stats', async (req, res) => {
    try {
        const stats = await pool.query(`
            SELECT 
                (SELECT COUNT(*) FROM users) as total_users,
                (SELECT COUNT(*) FROM diplomas) as total_diplomas,
                (SELECT COUNT(*) FROM diplomas WHERE status = 'active') as active_diplomas,
                (SELECT COUNT(*) FROM verifications) as total_verifications,
                (SELECT COUNT(*) FROM verifications WHERE is_valid = true) as successful_verifications,
                (SELECT COUNT(*) FROM verifications WHERE verification_time >= NOW() - INTERVAL '24 hours') as verifications_today
        `);
        
        res.json({
            success: true,
            stats: stats.rows[0]
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.get('/api/dashboard/recent-diplomas', async (req, res) => {
    try {
        const result = await pool.query(`
            SELECT id, certificate_hash, student_name, exam_year, issue_date, status
            FROM diplomas 
            ORDER BY issue_date DESC 
            LIMIT 10
        `);
        
        res.json({
            success: true,
            diplomas: result.rows
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.get('/api/dashboard/recent-verifications', async (req, res) => {
    try {
        const result = await pool.query(`
            SELECT v.*, d.student_name 
            FROM verifications v
            LEFT JOIN diplomas d ON v.certificate_hash = d.certificate_hash
            ORDER BY v.verification_time DESC 
            LIMIT 10
        `);
        
        res.json({
            success: true,
            verifications: result.rows
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Certificate routes
app.get('/api/diplomas', async (req, res) => {
    try {
        const result = await pool.query(`
            SELECT id, certificate_hash, student_name, exam_year, issue_date, status
            FROM diplomas 
            ORDER BY issue_date DESC
        `);
        
        res.json({
            success: true,
            diplomas: result.rows
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.post('/api/issue', async (req, res) => {
    try {
        const { student_id, student_name, exam_year, subjects } = req.body;
        
        const certHash = `LGCSE-${Date.now()}`;
        
        const result = await pool.query(
            `INSERT INTO diplomas (certificate_hash, student_id, student_name, exam_year, subjects) 
             VALUES ($1, $2, $3, $4, $5) RETURNING *`,
            [certHash, student_id, student_name, exam_year, JSON.stringify(subjects || [])]
        );
        
        res.json({
            success: true,
            diploma: result.rows[0],
            message: 'Diploma issued successfully'
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.get('/api/verify/:cert_hash', async (req, res) => {
    try {
        const { cert_hash } = req.params;
        
        const diplomaResult = await pool.query(
            'SELECT * FROM diplomas WHERE certificate_hash = $1',
            [cert_hash]
        );
        
        if (diplomaResult.rows.length === 0) {
            return res.status(404).json({ error: 'Certificate not found' });
        }
        
        const diploma = diplomaResult.rows[0];
        
        // Log verification
        await pool.query(
            `INSERT INTO verifications (certificate_hash, verifier, is_valid, verification_method) 
             VALUES ($1, $2, $3, $4)`,
            [cert_hash, 'System', true, 'api']
        );
        
        res.json({
            success: true,
            certificate: diploma,
            is_valid: !diploma.revoked,
            verification_time: new Date().toISOString()
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Root endpoint
app.get('/', (req, res) => {
    res.json({
        message: 'LGCSE Certificate Verification System API',
        version: '2.0.0',
        status: 'running',
        database: 'connected',
        endpoints: {
            auth: '/api/auth',
            dashboard: '/api/dashboard',
            diplomas: '/api/diplomas',
            verification: '/api/verify'
        }
    });
});

// Initialize database and start server
initializeDatabase().then((success) => {
    if (success) {
        app.listen(8000, "0.0.0.0", () => {
            console.log('\n🚀 LGCSE Database-Connected API running on http://localhost:8000');
            console.log('📊 Dashboard endpoints ready:');
            console.log('   GET  /api/dashboard/stats - Dashboard statistics');
            console.log('   GET  /api/dashboard/recent-diplomas - Recent diplomas');
            console.log('   GET  /api/dashboard/recent-verifications - Recent verifications');
            console.log('   GET  /api/diplomas - All diplomas');
            console.log('   POST /api/issue - Issue new diploma');
            console.log('   GET  /api/verify/:hash - Verify certificate');
            console.log('\n🗄️  Database connected with sample data');
        });
    } else {
        console.error('❌ Failed to initialize database');
        process.exit(1);
    }
});
