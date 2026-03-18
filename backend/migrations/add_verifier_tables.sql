-- Migration script to add verifier credential tables
-- Run this in your PostgreSQL database to add the new verifier tables

-- Create verifier_credentials table
CREATE TABLE IF NOT EXISTS verifier_credentials (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    credential_id VARCHAR(100) NOT NULL UNIQUE,
    
    -- Professional information
    license_number VARCHAR(100) UNIQUE,
    specialization VARCHAR(100),
    qualification_level VARCHAR(50),
    institution_affiliation VARCHAR(255),
    years_experience INTEGER DEFAULT 0,
    
    -- Verification authority
    verification_scope JSONB,
    max_verification_amount DECIMAL(10,2) DEFAULT 1000.0,
    daily_verification_limit INTEGER DEFAULT 50,
    
    -- Credentials and certificates
    professional_certificates JSONB,
    background_check_status VARCHAR(20) DEFAULT 'pending',
    background_check_date TIMESTAMP,
    accreditation_status VARCHAR(20) DEFAULT 'pending',
    
    -- Blockchain integration
    blockchain_wallet_address VARCHAR(255),
    blockchain_verifier_id VARCHAR(100),
    credential_hash VARCHAR(64) UNIQUE,
    blockchain_registered BOOLEAN DEFAULT FALSE,
    blockchain_tx_id VARCHAR(200),
    blockchain_network VARCHAR(50),
    
    -- Status and metrics
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    verification_count INTEGER DEFAULT 0,
    successful_verifications INTEGER DEFAULT 0,
    reputation_score DECIMAL(5,2) DEFAULT 100.0,
    last_verification_at TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- Create verifier_attestations table
CREATE TABLE IF NOT EXISTS verifier_attestations (
    id SERIAL PRIMARY KEY,
    verifier_credential_id INTEGER NOT NULL REFERENCES verifier_credentials(id) ON DELETE CASCADE,
    attestation_type VARCHAR(50) NOT NULL,
    attestation_hash VARCHAR(64) NOT NULL UNIQUE,
    
    -- Blockchain data
    blockchain_tx_id VARCHAR(200),
    blockchain_network VARCHAR(50),
    block_number INTEGER,
    block_timestamp TIMESTAMP,
    
    -- Attestation details
    issuer VARCHAR(255),
    issuer_address VARCHAR(255),
    signature TEXT,
    metadata JSONB,
    
    -- Status
    is_valid BOOLEAN DEFAULT TRUE,
    revoked_at TIMESTAMP,
    revoke_reason TEXT,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create verifier_audit_logs table
CREATE TABLE IF NOT EXISTS verifier_audit_logs (
    id SERIAL PRIMARY KEY,
    verifier_credential_id INTEGER NOT NULL REFERENCES verifier_credentials(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Activity details
    activity_type VARCHAR(50) NOT NULL,
    action VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- Related entities
    certificate_hash VARCHAR(64),
    verification_request_id INTEGER,
    blockchain_tx_id VARCHAR(200),
    
    -- System information
    ip_address VARCHAR(100),
    user_agent TEXT,
    location VARCHAR(255),
    
    -- Results and status
    status VARCHAR(20) NOT NULL,
    error_message TEXT,
    
    -- Changes tracking
    old_values JSONB,
    new_values JSONB,
    
    -- Metadata
    metadata_json JSONB,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_verifier_credentials_user_id ON verifier_credentials(user_id);
CREATE INDEX IF NOT EXISTS idx_verifier_credentials_credential_id ON verifier_credentials(credential_id);
CREATE INDEX IF NOT EXISTS idx_verifier_credentials_accreditation_status ON verifier_credentials(accreditation_status);
CREATE INDEX IF NOT EXISTS idx_verifier_credentials_blockchain_registered ON verifier_credentials(blockchain_registered);
CREATE INDEX IF NOT EXISTS idx_verifier_credentials_credential_hash ON verifier_credentials(credential_hash);

CREATE INDEX IF NOT EXISTS idx_verifier_attestations_verifier_credential_id ON verifier_attestations(verifier_credential_id);
CREATE INDEX IF NOT EXISTS idx_verifier_attestations_attestation_hash ON verifier_attestations(attestation_hash);
CREATE INDEX IF NOT EXISTS idx_verifier_attestations_type ON verifier_attestations(attestation_type);

CREATE INDEX IF NOT EXISTS idx_verifier_audit_logs_verifier_credential_id ON verifier_audit_logs(verifier_credential_id);
CREATE INDEX IF NOT EXISTS idx_verifier_audit_logs_user_id ON verifier_audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_verifier_audit_logs_activity_type ON verifier_audit_logs(activity_type);
CREATE INDEX IF NOT EXISTS idx_verifier_audit_logs_created_at ON verifier_audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_verifier_audit_logs_certificate_hash ON verifier_audit_logs(certificate_hash);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_verifier_credentials_updated_at 
    BEFORE UPDATE ON verifier_credentials 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_verifier_attestations_updated_at 
    BEFORE UPDATE ON verifier_attestations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for testing (optional)
INSERT INTO verifier_credentials (
    user_id, credential_id, license_number, specialization, 
    qualification_level, institution_affiliation, years_experience,
    accreditation_status, is_active, is_verified
) VALUES (
    1, 
    'VER-123ABC456789', 
    'PSY-2023-001',
    'Educational Psychology',
    'Masters',
    'University of Technology',
    5,
    'approved',
    TRUE,
    TRUE
) ON CONFLICT (user_id) DO NOTHING;

-- Grant permissions (adjust as needed for your setup)
-- GRANT ALL PRIVILEGES ON verifier_credentials TO certivert;
-- GRANT ALL PRIVILEGES ON verifier_attestations TO certivert;
-- GRANT ALL PRIVILEGES ON verifier_audit_logs TO certivert;
-- GRANT USAGE, SELECT ON SEQUENCE verifier_credentials_id_seq TO certivert;
-- GRANT USAGE, SELECT ON SEQUENCE verifier_attestations_id_seq TO certivert;
-- GRANT USAGE, SELECT ON SEQUENCE verifier_audit_logs_id_seq TO certivert;

COMMIT;
