-- Fix permissions for diploma_admin user
-- Change ownership of tables to diploma_admin
ALTER TABLE IF EXISTS users OWNER TO diploma_admin;
ALTER TABLE IF EXISTS certificates OWNER TO diploma_admin;
ALTER TABLE IF EXISTS verification_requests OWNER TO diploma_admin;
ALTER TABLE IF EXISTS verification_logs OWNER TO diploma_admin;
ALTER TABLE IF EXISTS institutions OWNER TO diploma_admin;
ALTER TABLE IF EXISTS payments OWNER TO diploma_admin;
ALTER TABLE IF EXISTS badges OWNER TO diploma_admin;
ALTER TABLE IF EXISTS invitations OWNER TO diploma_admin;
ALTER TABLE IF EXISTS audit_events OWNER TO diploma_admin;
ALTER TABLE IF EXISTS _prisma_migrations OWNER TO diploma_admin;

-- Grant permissions on all tables in public schema
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO diploma_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO diploma_admin;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO diploma_admin;

-- Grant permissions on schema itself
GRANT ALL PRIVILEGES ON SCHEMA public TO diploma_admin;

-- Set default permissions for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO diploma_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO diploma_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON FUNCTIONS TO diploma_admin;

-- Make diploma_admin the database owner too
ALTER DATABASE diploma_verification OWNER TO diploma_admin;
