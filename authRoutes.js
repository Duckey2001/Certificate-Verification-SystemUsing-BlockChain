const express = require('express');
const router = express.Router();

// Simple auth routes for testing
router.post('/login', (req, res) => {
    res.json({
        success: true,
        token: 'test-token-123',
        user: {
            id: 1,
            email: 'test@example.com',
            name: 'Test User'
        }
    });
});

router.get('/me', (req, res) => {
    res.json({
        success: true,
        user: {
            id: 1,
            email: 'test@example.com',
            name: 'Test User'
        }
    });
});

router.post('/register', (req, res) => {
    res.json({
        success: true,
        message: 'User registered successfully',
        user: {
            id: 2,
            email: req.body.email || 'new@example.com',
            name: req.body.name || 'New User'
        }
    });
});

module.exports = router;
