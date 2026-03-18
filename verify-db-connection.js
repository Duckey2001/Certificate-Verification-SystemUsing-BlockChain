const { Pool } = require('pg');

const pool = new Pool({
  user: 'diploma_admin',
  password: 'diploma1234',
  host: 'localhost',
  port: 5432,
  database: 'diploma_verification'
});

pool.query('SELECT current_database() as db, current_user as usr, NOW() as time', (err, res) => {
  if (err) {
    console.error('❌ Connection failed:', err.message);
    process.exit(1);
  } else {
    console.log('✅ Database Connection Successful!');
    console.log('Database:', res.rows[0].db);
    console.log('User:', res.rows[0].usr);
    console.log('Timestamp:', res.rows[0].time);
    pool.end();
  }
});
