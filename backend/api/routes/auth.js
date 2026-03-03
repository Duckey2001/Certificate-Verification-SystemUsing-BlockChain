const express = require('express');
const router = express.Router();
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const { PrismaClient } = require('@prisma/client');

const prisma = new PrismaClient();
const JWT_SECRET = process.env.JWT_SECRET || 'your-secret-key-change-in-production';

// Register endpoint
router.post('/register', async (req, res) => {
  try {
    const { username, email, password, institutionCode, role } = req.body;

    // Check if user already exists
    const existingUser = await prisma.user.findFirst({
      where: {
        OR: [
          { username },
          { email }
        ]
      }
    });

    if (existingUser) {
      return res.status(400).json({ 
        error: 'User already exists with this username or email' 
      });
    }

    // Hash password
    const salt = await bcrypt.genSalt(10);
    const passwordHash = await bcrypt.hash(password, salt);

    // Create user
    const user = await prisma.user.create({
      data: {
        username,
        email,
        passwordHash,
        institutionCode,
        role: role || 'user',
        isActive: true,
        createdAt: new Date(),
        updatedAt: new Date()
      },
      include: {
        institution: true
      }
    });

    // Create session
    const sessionToken = jwt.sign(
      { userId: user.id, username: user.username, role: user.role },
      JWT_SECRET,
      { expiresIn: '7d' }
    );

    // Log login activity
    await prisma.loginActivity.create({
      data: {
        userId: user.id,
        institutionCode: user.institutionCode,
        ipAddress: req.ip,
        userAgent: req.get('user-agent'),
        status: 'success',
        loginMethod: 'password'
      }
    });

    // Create session record
    await prisma.session.create({
      data: {
        sessionToken,
        userId: user.id,
        expires: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000) // 7 days
      }
    });

    res.status(201).json({
      message: 'User registered successfully',
      user: {
        id: user.id,
        username: user.username,
        email: user.email,
        role: user.role,
        institution: user.institution
      },
      sessionToken
    });

  } catch (error) {
    console.error('Registration error:', error);
    res.status(500).json({ error: 'Failed to register user' });
  }
});

// Login endpoint
router.post('/login', async (req, res) => {
  try {
    const { username, password } = req.body;

    // Find user
    const user = await prisma.user.findUnique({
      where: { username },
      include: { institution: true }
    });

    if (!user) {
      // Log failed attempt
      await prisma.loginActivity.create({
        data: {
          userId: 'unknown',
          ipAddress: req.ip,
          userAgent: req.get('user-agent'),
          status: 'failed',
          failureReason: 'User not found',
          loginMethod: 'password'
        }
      });
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    // Check if user is active
    if (!user.isActive) {
      await prisma.loginActivity.create({
        data: {
          userId: user.id,
          institutionCode: user.institutionCode,
          ipAddress: req.ip,
          userAgent: req.get('user-agent'),
          status: 'failed',
          failureReason: 'Account deactivated',
          loginMethod: 'password'
        }
      });
      return res.status(403).json({ error: 'Account is deactivated' });
    }

    // Verify password
    const isValidPassword = await bcrypt.compare(password, user.passwordHash);
    if (!isValidPassword) {
      await prisma.loginActivity.create({
        data: {
          userId: user.id,
          institutionCode: user.institutionCode,
          ipAddress: req.ip,
          userAgent: req.get('user-agent'),
          status: 'failed',
          failureReason: 'Invalid password',
          loginMethod: 'password'
        }
      });
      return res.status(401).json({ error: 'Invalid credentials' });
    }

    // Create session token
    const sessionToken = jwt.sign(
      { userId: user.id, username: user.username, role: user.role },
      JWT_SECRET,
      { expiresIn: '7d' }
    );

    // Update last login
    await prisma.user.update({
      where: { id: user.id },
      data: { lastLoginAt: new Date() }
    });

    // Log successful login
    await prisma.loginActivity.create({
      data: {
        userId: user.id,
        institutionCode: user.institutionCode,
        ipAddress: req.ip,
        userAgent: req.get('user-agent'),
        status: 'success',
        loginMethod: 'password'
      }
    });

    // Create session record
    await prisma.session.create({
      data: {
        sessionToken,
        userId: user.id,
        expires: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)
      }
    });

    res.json({
      message: 'Login successful',
      user: {
        id: user.id,
        username: user.username,
        email: user.email,
        role: user.role,
        institution: user.institution
      },
      sessionToken
    });

  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ error: 'Failed to login' });
  }
});

// Logout endpoint
router.post('/logout', async (req, res) => {
  try {
    const token = req.headers.authorization?.split(' ')[1];
    
    if (token) {
      // Delete session
      await prisma.session.deleteMany({
        where: { sessionToken: token }
      });
    }

    res.json({ message: 'Logged out successfully' });
  } catch (error) {
    console.error('Logout error:', error);
    res.status(500).json({ error: 'Failed to logout' });
  }
});

// Verify token endpoint
router.get('/verify', async (req, res) => {
  try {
    const token = req.headers.authorization?.split(' ')[1];
    
    if (!token) {
      return res.status(401).json({ error: 'No token provided' });
    }

    // Verify token
    const decoded = jwt.verify(token, JWT_SECRET);
    
    // Check if session exists
    const session = await prisma.session.findUnique({
      where: { sessionToken: token },
      include: { 
        user: {
          include: { institution: true }
        }
      }
    });

    if (!session || session.expires < new Date()) {
      return res.status(401).json({ error: 'Invalid or expired session' });
    }

    res.json({
      valid: true,
      user: {
        id: session.user.id,
        username: session.user.username,
        email: session.user.email,
        role: session.user.role,
        institution: session.user.institution
      }
    });

  } catch (error) {
    console.error('Token verification error:', error);
    res.status(401).json({ error: 'Invalid token' });
  }
});

// Get current user
router.get('/me', async (req, res) => {
  try {
    const token = req.headers.authorization?.split(' ')[1];
    
    if (!token) {
      return res.status(401).json({ error: 'No token provided' });
    }

    const decoded = jwt.verify(token, JWT_SECRET);
    
    const user = await prisma.user.findUnique({
      where: { id: decoded.userId },
      include: { institution: true }
    });

    if (!user) {
      return res.status(404).json({ error: 'User not found' });
    }

    res.json({
      id: user.id,
      username: user.username,
      email: user.email,
      role: user.role,
      institution: user.institution,
      lastLoginAt: user.lastLoginAt
    });

  } catch (error) {
    console.error('Get user error:', error);
    res.status(401).json({ error: 'Invalid token' });
  }
});

module.exports = router;