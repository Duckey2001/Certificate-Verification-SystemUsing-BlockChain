// test-connection.js
const { PrismaClient } = require('@prisma/client');
const { Pool } = require('pg');

async function testConnections() {
  console.log('🔌 Testing PostgreSQL Connection...');
  
  // Test 1: Direct PG Pool Connection
  try {
    const pool = new Pool({
      user: 'certivert',
      host: 'localhost',
      database: 'CertiVert',
      password: 'your_password_here',
      port: 5432,
      ssl: false
    });
    
    const client = await pool.connect();
    const res = await client.query('SELECT NOW() as time, current_database() as db');
    console.log('✅ PG Pool Connection successful:', res.rows[0]);
    client.release();
    await pool.end();
  } catch (error) {
    console.error('❌ PG Pool Connection failed:', error.message);
  }
  
  // Test 2: Prisma Connection
  try {
    const prisma = new PrismaClient();
    
    // Test query
    const result = await prisma.$queryRaw`SELECT NOW() as time, current_database() as db`;
    console.log('✅ Prisma Connection successful:', result);
    
    // Test Institution query
    const institutions = await prisma.institution.findMany({
      take: 5
    });
    console.log(`✅ Found ${institutions.length} institutions`);
    
    await prisma.$disconnect();
  } catch (error) {
    console.error('❌ Prisma Connection failed:', error);
  }
  
  // Test 3: Check if database exists
  try {
    const pool = new Pool({
      user: 'certivert',
      host: 'localhost',
      database: 'postgres', // Connect to default database
      password: 'your_password_here',
      port: 5432
    });
    
    const client = await pool.connect();
    const res = await client.query(`
      SELECT datname FROM pg_database WHERE datname = 'CertiVert'
    `);
    
    if (res.rows.length > 0) {
      console.log('✅ Database "CertiVert" exists');
    } else {
      console.log('❌ Database "CertiVert" does not exist');
    }
    
    client.release();
    await pool.end();
  } catch (error) {
    console.error('❌ Database check failed:', error.message);
  }
}

testConnections();
