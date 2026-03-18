const express = require('express');
const { Pool } = require('pg');
const crypto = require('crypto');
const QRCode = require('qrcode');
const blockchain = require('./blockchain');
const PDFDocument = require('pdfkit');
const fs = require('fs');
const authRoutes = require('./authRoutes');
const cors = require('cors');

// load environment variables from .env (if present)
require('dotenv').config();

const app = express();

// CORS configuration
app.use(cors({
    origin: ['http://localhost:3000', 'http://localhost:3001'], // React frontend ports
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization']
}));

app.use(express.json());

// PostgreSQL connection - configurable via environment variables
const pool = new Pool({
    user: process.env.POSTGRES_USER || 'diploma_admin',
    host: process.env.POSTGRES_HOST || 'localhost',
    database: process.env.POSTGRES_DB || 'diploma_verification',
    password: process.env.POSTGRES_PASSWORD || 'diploma1234',
    port: process.env.POSTGRES_PORT || 5432,
    max: parseInt(process.env.PG_MAX_CONNECTIONS || '10', 10),
    idleTimeoutMillis: parseInt(process.env.PG_IDLE_TIMEOUT || '10000', 10),
    connectionTimeoutMillis: parseInt(process.env.PG_CONNECTION_TIMEOUT || '0', 10)
});

// Create diplomas directory
if (!fs.existsSync('./diplomas')) {
    fs.mkdirSync('./diplomas');
}

// Function to generate diploma PDF
function generateDiplomaPDF(studentName, studentId, examYear, certificateHash) {
    return new Promise((resolve, reject) => {
        try {
            const doc = new PDFDocument({
                size: 'A4',
                margin: 50
            });

            const filename = `diploma_${certificateHash}.pdf`;
            const filepath = `./diplomas/${filename}`;
            const stream = fs.createWriteStream(filepath);
            doc.pipe(stream);

            // Header
            doc.fontSize(24)
               .font('Helvetica-Bold')
               .fillColor('#1976d2')
               .text('LGCSE DIPLOMA', { align: 'center' })
               .moveDown();

            doc.fontSize(18)
               .text('OFFICIAL CERTIFICATE', { align: 'center' })
               .moveDown(2);

            // Student info
            doc.fontSize(16)
               .fillColor('#333')
               .text('This certifies that', { align: 'center' })
               .moveDown();

            doc.fontSize(28)
               .font('Helvetica-Bold')
               .fillColor('#1976d2')
               .text(studentName.toUpperCase(), { align: 'center' })
               .moveDown();

            doc.fontSize(14)
               .font('Helvetica')
               .fillColor('#333')
               .text(`Student ID: ${studentId}`, { align: 'center' })
               .text(`Examination Year: ${examYear}`, { align: 'center' })
               .moveDown(2);

            // QR Code for verification
            doc.fontSize(12)
               .text('Scan to verify authenticity:', { align: 'center' })
               .moveDown();

            // Add QR code (we'll generate it separately and add as image)
            const qrPath = `./diplomas/qr_${certificateHash}.png`;
            QRCode.toFile(qrPath, certificateHash, async (err) => {
                if (!err) {
                    doc.image(qrPath, 200, 400, { width: 150, height: 150 });
                }

                // Footer
                doc.fontSize(10)
                   .fillColor('#666')
                   .text(`Certificate Hash: ${certificateHash}`, 50, 600)
                   .text('Registered on LGCSE Blockchain', 50, 615)
                   .text('Verify at: http://localhost:3001', 50, 630)
                   .moveDown();

                doc.fontSize(8)
                   .text('© 2024 LGCSE Certificate Authority | Blockchain Verified', { align: 'center' })
                   .text('Tamper-Proof | Immutable Record', { align: 'center' });

                doc.end();

                stream.on('finish', () => {
                    resolve({ filename, filepath });
                });

                stream.on('error', reject);
            });
        } catch (error) {
            reject(error);
        }
    });
}

// Create tables
async function initializeDatabase() {
    try {
        // Users table
        await pool.query(`
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email VARCHAR(255) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                name VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        `);

        // Check if password column exists and add it if it doesn't
        try {
            await pool.query('SELECT password FROM users LIMIT 1');
        } catch (error) {
            if (error.message.includes('column "password" does not exist')) {
                await pool.query('ALTER TABLE users ADD COLUMN password VARCHAR(255) NOT NULL DEFAULT \'\'');
                console.log('✅ Added password column to users table');
            }
        }

        // Check if name column exists and add it if it doesn't
        try {
            await pool.query('SELECT name FROM users LIMIT 1');
        } catch (error) {
            if (error.message.includes('column "name" does not exist')) {
                await pool.query('ALTER TABLE users ADD COLUMN name VARCHAR(255)');
                console.log('✅ Added name column to users table');
            }
        }

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
                blockchain_tx_id VARCHAR(255),
                block_hash VARCHAR(255)
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
                blockchain_tx_id VARCHAR(255)
            )
        `);
        
        console.log('✅ Database tables created successfully');
        
        // Print blockchain info
        const bcInfo = blockchain.getInfo();
        console.log('🔗 Blockchain initialized:');
        console.log(`   Chain length: ${bcInfo.chainLength} blocks`);
        console.log(`   Validators: ${bcInfo.validators.join(', ')}`);
        console.log(`   Chain valid: ${bcInfo.isValid ? '✅ YES' : '❌ NO'}`);
        
    } catch (error) {
        console.error('❌ Database initialization error:', error);
    }
}

// Add authentication routes
app.use('/api/auth', authRoutes);

// 1. Issue Diploma API - Now with PDF
app.post('/api/issue', async (req, res) => {
    try {
        const { student_id, student_name, exam_year, subjects } = req.body;
        
        // Generate certificate hash
        const certHash = `LGCSE-${student_id}-${Date.now()}`;
        
        // Generate QR code
        const qrCode = await QRCode.toDataURL(certHash);
        
        // Generate PDF
        const pdfResult = await generateDiplomaPDF(student_name, student_id, exam_year, certHash);
        
        // Create blockchain transaction
        const tx = blockchain.createDiplomaTransaction(
            certHash, student_id, student_name, exam_year, 'LGCSE'
        );
        
        // Save diploma to database with blockchain reference
        await pool.query(
            `INSERT INTO diplomas (certificate_hash, student_id, student_name, exam_year, 
             subjects, qr_code, pdf_path, blockchain_tx_id) 
             VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
            [certHash, student_id, student_name, exam_year, 
             JSON.stringify(subjects || []), qrCode, pdfResult.filename, tx.transactionId]
        );
        
        // Mine the transaction
        const minedBlock = await blockchain.minePendingTransactions();
        
        // Update diploma with block hash if mined
        if (minedBlock) {
            await pool.query(
                `UPDATE diplomas SET block_hash = $1 WHERE certificate_hash = $2`,
                [minedBlock.hash.substring(0, 32), certHash]
            );
        }
        
        // Get blockchain info
        const bcInfo = blockchain.getInfo();
        
        res.json({
            success: true,
            certificate_hash: certHash,
            qr_code: qrCode,
            pdf_file: pdfResult.filename,
            blockchain: {
                transaction_id: tx.transactionId,
                block_index: minedBlock ? minedBlock.index : 'pending',
                block_hash: minedBlock ? minedBlock.hash.substring(0, 32) + '...' : null,
                consensus: 'Proof of Authority (3/4 validators)',
                chain_length: bcInfo.chainLength
            },
            message: 'Diploma issued and added to blockchain'
        });
        
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// 2. Get PDF file
app.get('/api/diploma/pdf/:hash', async (req, res) => {
    try {
        const { hash } = req.params;
        
        const result = await pool.query(
            'SELECT pdf_path FROM diplomas WHERE certificate_hash = $1',
            [hash]
        );
        
        if (result.rows.length === 0) {
            return res.status(404).json({ error: 'Diploma not found' });
        }
        
        const pdfPath = `./diplomas/${result.rows[0].pdf_path}`;
        
        if (fs.existsSync(pdfPath)) {
            res.download(pdfPath);
        } else {
            res.status(404).json({ error: 'PDF file not found' });
        }
        
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// 3. Verify Diploma API
app.get('/api/verify/:cert_hash', async (req, res) => {
    try {
        const { cert_hash } = req.params;
        const verifier = req.query.verifier || 'Unknown';
        
        // Check diploma in database
        const diplomaResult = await pool.query(
            'SELECT * FROM diplomas WHERE certificate_hash = $1',
            [cert_hash]
        );
        
        if (diplomaResult.rows.length === 0) {
            return res.status(404).json({ error: 'Certificate not found' });
        }
        
        const diploma = diplomaResult.rows[0];
        const isValid = !diploma.revoked;
        
        // Create blockchain verification transaction
        const tx = blockchain.createVerificationTransaction(cert_hash, verifier, isValid);
        
        // Log verification in database
        await pool.query(
            `INSERT INTO verifications (certificate_hash, verifier, is_valid, blockchain_tx_id) 
             VALUES ($1, $2, $3, $4)`,
            [cert_hash, verifier, isValid, tx.transactionId]
        );
        
        // Mine verification transaction
        const minedBlock = await blockchain.minePendingTransactions();
        
        // Get certificate history from blockchain
        const blockchainHistory = blockchain.getCertificateHistory(cert_hash);
        
        res.json({
            certificate_hash: cert_hash,
            student_name: diploma.student_name,
            exam_year: diploma.exam_year,
            verifier: verifier,
            is_valid: isValid,
            verification_time: new Date().toISOString(),
            has_pdf: !!diploma.pdf_path,
            blockchain: {
                transaction_id: tx.transactionId,
                block_index: minedBlock ? minedBlock.index : 'pending',
                total_transactions: blockchainHistory.length,
                history: blockchainHistory.slice(0, 5)
            }
        });
        
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// 4. Get Diploma Details
app.get('/api/diploma/:cert_hash', async (req, res) => {
    try {
        const { cert_hash } = req.params;
        
        // Get from database
        const diplomaResult = await pool.query(
            'SELECT * FROM diplomas WHERE certificate_hash = $1',
            [cert_hash]
        );
        
        const verificationsResult = await pool.query(
            'SELECT * FROM verifications WHERE certificate_hash = $1 ORDER BY verification_time DESC',
            [cert_hash]
        );
        
        // Get from blockchain
        const blockchainHistory = blockchain.getCertificateHistory(cert_hash);
        const bcInfo = blockchain.getInfo();
        
        res.json({
            diploma: diplomaResult.rows[0] || null,
            verifications: verificationsResult.rows,
            blockchain: {
                history: blockchainHistory,
                total_transactions: blockchainHistory.length,
                chain_info: bcInfo
            },
            total_verifications: verificationsResult.rowCount
        });
        
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// 5. List all diplomas
app.get('/api/diplomas', async (req, res) => {
    try {
        const result = await pool.query(
            'SELECT certificate_hash, student_name, exam_year, block_hash FROM diplomas ORDER BY issue_date DESC'
        );
        res.json({ diplomas: result.rows });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// 6. Get Blockchain Info
app.get('/api/blockchain/info', (req, res) => {
    try {
        const info = blockchain.getInfo();
        blockchain.printChain();
        res.json(info);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// 7. Get Full Blockchain
app.get('/api/blockchain/chain', (req, res) => {
    try {
        const chainSummary = blockchain.chain.map(block => ({
            index: block.index,
            hash: block.hash.substring(0, 20) + '...',
            previousHash: block.previousHash.substring(0, 20) + '...',
            timestamp: new Date(block.timestamp).toLocaleString(),
            transactionCount: block.data.transactions ? block.data.transactions.length : 0
        }));
        
        res.json({
            chain: chainSummary,
            length: blockchain.chain.length,
            isValid: blockchain.isChainValid()
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// 8. Validate blockchain
app.get('/api/blockchain/validate', (req, res) => {
    try {
        const isValid = blockchain.isChainValid();
        res.json({
            isValid: isValid,
            message: isValid ? '✅ Blockchain is valid and tamper-proof' : '❌ Blockchain has been tampered with!',
            chainLength: blockchain.chain.length,
            checkedAt: new Date().toISOString()
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// 9. Download PDF endpoint
app.get('/api/download/pdf/:hash', (req, res) => {
    const { hash } = req.params;
    const filePath = `./diplomas/diploma_${hash}.pdf`;
    
    if (fs.existsSync(filePath)) {
        res.download(filePath);
    } else {
        res.status(404).json({ error: 'PDF not found' });
    }
});

// Initialize and start server
initializeDatabase().then(() => {
    app.listen(8000, "0.0.0.0", () => {
        console.log('\n🚀 LGCSE Diploma Blockchain API running on http://localhost:8000');
        console.log('📚 Available endpoints:');
        console.log('   POST /api/auth/register - Register new user');
        console.log('   POST /api/auth/login - Login user');
        console.log('   GET  /api/auth/me - Get current user');
        console.log('   POST /api/issue - Issue new diploma (with PDF & blockchain)');
        console.log('   GET  /api/verify/:hash - Verify diploma');
        console.log('   GET  /api/diploma/:hash - Get diploma details');
        console.log('   GET  /api/diplomas - List all diplomas');
        console.log('   GET  /api/blockchain/info - Get blockchain info');
        console.log('   GET  /api/blockchain/chain - Get blockchain summary');
        console.log('   GET  /api/blockchain/validate - Validate blockchain');
        console.log('   GET  /api/download/pdf/:hash - Download diploma PDF');
        console.log('\n🔗 Blockchain Consensus: Proof of Authority (PoA)');
        console.log('   Validators: LGCSE Certificate Authority, Ministry of Education, Examination Council, Independent Validators');
        console.log('   Required: 3 out of 4 validators must approve transactions');
    });
});
