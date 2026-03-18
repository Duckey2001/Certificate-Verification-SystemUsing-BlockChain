-- init-database.sql
-- Run this to verify and initialize your database

-- Check current database
SELECT current_database(), current_user, version();

-- List all tables
SELECT 
    table_schema,
    table_name,
    table_type
FROM information_schema.tables 
WHERE table_schema = 'public'
ORDER BY table_name;

-- Count records in main tables
SELECT 'Institution' as table_name, COUNT(*) as count FROM "Institution"
UNION ALL
SELECT 'Certificate', COUNT(*) FROM "Certificate"
UNION ALL
SELECT 'VerificationLog', COUNT(*) FROM "VerificationLog"
UNION ALL
SELECT 'User', COUNT(*) FROM "User"
UNION ALL
SELECT 'Payment', COUNT(*) FROM "Payment";

-- Check for any failed migrations
SELECT * FROM _prisma_migrations 
WHERE rolled_back_at IS NOT NULL 
   OR finished_at IS NULL;
