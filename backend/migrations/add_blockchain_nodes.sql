-- Migration: Add Blockchain Node Support to Institutions
-- Version: 001
-- Description: Adds blockchain node fields to institutions table and creates new tables for blockchain management

-- Start transaction
BEGIN;

-- Add blockchain node fields to existing institutions table
ALTER TABLE "institutions" 
ADD COLUMN IF NOT EXISTS "blockchain_node_id" VARCHAR(100) UNIQUE,
ADD COLUMN IF NOT EXISTS "blockchain_node_url" VARCHAR(500),
ADD COLUMN IF NOT EXISTS "blockchain_node_port" INTEGER,
ADD COLUMN IF NOT EXISTS "blockchain_node_status" VARCHAR(20) DEFAULT 'inactive' CHECK (blockchain_node_status IN ('inactive', 'active', 'syncing', 'error', 'maintenance')),
ADD COLUMN IF NOT EXISTS "blockchain_network" VARCHAR(50) CHECK (blockchain_network IN ('fabric', 'ethereum', 'hyperledger', 'corda')),
ADD COLUMN IF NOT EXISTS "chaincode_version" VARCHAR(20),
ADD COLUMN IF NOT EXISTS "chaincode_name" VARCHAR(100),
ADD COLUMN IF NOT EXISTS "node_public_key" TEXT,
ADD COLUMN IF NOT EXISTS "node_private_key" TEXT,  -- Should be encrypted
ADD COLUMN IF NOT EXISTS "msp_id" VARCHAR(100),
ADD COLUMN IF NOT EXISTS "peer_id" VARCHAR(100),
ADD COLUMN IF NOT EXISTS "orderer_id" VARCHAR(100),
ADD COLUMN IF NOT EXISTS "channel_name" VARCHAR(100),
ADD COLUMN IF NOT EXISTS "chaincode_installed" BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS "chaincode_instantiated" BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS "last_sync_at" TIMESTAMP,
ADD COLUMN IF NOT EXISTS "node_config" JSONB;

-- Add indexes for new blockchain fields
CREATE INDEX IF NOT EXISTS "idx_institutions_blockchain_node_id" ON "institutions"("blockchain_node_id");
CREATE INDEX IF NOT EXISTS "idx_institutions_blockchain_status" ON "institutions"("blockchain_node_status");
CREATE INDEX IF NOT EXISTS "idx_institutions_blockchain_network" ON "institutions"("blockchain_network");

-- Create blockchain_nodes table
CREATE TABLE IF NOT EXISTS "blockchain_nodes" (
    "id" SERIAL PRIMARY KEY,
    "node_id" VARCHAR(100) UNIQUE NOT NULL,
    "institution_id" INTEGER NOT NULL REFERENCES "institutions"("id") ON DELETE CASCADE,
    "node_type" VARCHAR(50) NOT NULL CHECK (node_type IN ('peer', 'orderer', 'ca', 'validator')),
    "network_type" VARCHAR(50) NOT NULL CHECK (network_type IN ('fabric', 'ethereum', 'hyperledger', 'corda')),
    
    -- Network configuration
    "url" VARCHAR(500) NOT NULL,
    "port" INTEGER NOT NULL,
    "tls_enabled" BOOLEAN DEFAULT TRUE,
    "tls_cert_path" VARCHAR(500),
    "tls_key_path" VARCHAR(500),
    "ca_cert_path" VARCHAR(500),
    
    -- Node identity
    "msp_id" VARCHAR(100),
    "peer_id" VARCHAR(100),
    "orderer_id" VARCHAR(100),
    "node_public_key" TEXT,
    "node_private_key" TEXT,  -- Encrypted
    "node_certificates" JSONB,
    
    -- Chaincode information
    "chaincode_name" VARCHAR(100),
    "chaincode_version" VARCHAR(20),
    "chaincode_path" VARCHAR(500),
    "chaincode_installed" BOOLEAN DEFAULT FALSE,
    "chaincode_instantiated" BOOLEAN DEFAULT FALSE,
    "channel_name" VARCHAR(100),
    
    -- Node status
    "status" VARCHAR(20) DEFAULT 'inactive' CHECK (status IN ('inactive', 'active', 'syncing', 'error', 'maintenance')),
    "last_heartbeat" TIMESTAMP,
    "last_sync_at" TIMESTAMP,
    "block_height" INTEGER DEFAULT 0,
    "network_height" INTEGER DEFAULT 0,
    
    -- Configuration
    "node_config" JSONB,
    "genesis_block" TEXT,
    "configtxlator_path" VARCHAR(500),
    "cryptogen_path" VARCHAR(500),
    
    -- Timestamps
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "installed_at" TIMESTAMP
);

-- Create indexes for blockchain_nodes
CREATE INDEX IF NOT EXISTS "idx_blockchain_nodes_node_id" ON "blockchain_nodes"("node_id");
CREATE INDEX IF NOT EXISTS "idx_blockchain_nodes_institution_id" ON "blockchain_nodes"("institution_id");
CREATE INDEX IF NOT EXISTS "idx_blockchain_nodes_status" ON "blockchain_nodes"("status");
CREATE INDEX IF NOT EXISTS "idx_blockchain_nodes_network_type" ON "blockchain_nodes"("network_type");

-- Create chaincode_deployments table
CREATE TABLE IF NOT EXISTS "chaincode_deployments" (
    "id" SERIAL PRIMARY KEY,
    "deployment_id" VARCHAR(100) UNIQUE NOT NULL,
    "node_id" INTEGER NOT NULL REFERENCES "blockchain_nodes"("id") ON DELETE CASCADE,
    "institution_id" INTEGER NOT NULL REFERENCES "institutions"("id") ON DELETE CASCADE,
    
    -- Chaincode details
    "chaincode_name" VARCHAR(100) NOT NULL,
    "chaincode_version" VARCHAR(20) NOT NULL,
    "chaincode_path" VARCHAR(500) NOT NULL,
    "chaincode_language" VARCHAR(20) DEFAULT 'go' CHECK (chaincode_language IN ('go', 'java', 'node')),
    
    -- Deployment information
    "channel_name" VARCHAR(100),
    "endorsement_policy" JSONB,
    "collection_config" JSONB,  -- Private data collections
    "init_required" BOOLEAN DEFAULT TRUE,
    "init_args" JSONB,
    
    -- Status tracking
    "status" VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'installing', 'instantiating', 'instantiated', 'failed', 'active')),
    "install_tx_id" VARCHAR(200),
    "instantiate_tx_id" VARCHAR(200),
    "package_id" VARCHAR(200),
    
    -- Error handling
    "error_message" TEXT,
    "retry_count" INTEGER DEFAULT 0,
    "max_retries" INTEGER DEFAULT 3,
    
    -- Timestamps
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    "installed_at" TIMESTAMP,
    "instantiated_at" TIMESTAMP
);

-- Create indexes for chaincode_deployments
CREATE INDEX IF NOT EXISTS "idx_chaincode_deployments_deployment_id" ON "chaincode_deployments"("deployment_id");
CREATE INDEX IF NOT EXISTS "idx_chaincode_deployments_node_id" ON "chaincode_deployments"("node_id");
CREATE INDEX IF NOT EXISTS "idx_chaincode_deployments_institution_id" ON "chaincode_deployments"("institution_id");
CREATE INDEX IF NOT EXISTS "idx_chaincode_deployments_status" ON "chaincode_deployments"("status");

-- Create node_activity_logs table
CREATE TABLE IF NOT EXISTS "node_activity_logs" (
    "id" SERIAL PRIMARY KEY,
    "node_id" INTEGER NOT NULL REFERENCES "blockchain_nodes"("id") ON DELETE CASCADE,
    "institution_id" INTEGER NOT NULL REFERENCES "institutions"("id") ON DELETE CASCADE,
    
    -- Activity details
    "activity_type" VARCHAR(50) NOT NULL CHECK (activity_type IN ('start', 'stop', 'sync', 'deploy', 'error', 'heartbeat', 'upgrade')),
    "activity_message" TEXT NOT NULL,
    "activity_data" JSONB,
    
    -- Status information
    "status_before" VARCHAR(20),
    "status_after" VARCHAR(20),
    "block_height_before" INTEGER,
    "block_height_after" INTEGER,
    
    -- Error information
    "error_code" VARCHAR(50),
    "error_message" TEXT,
    "stack_trace" TEXT,
    
    -- Metadata
    "ip_address" VARCHAR(100),
    "user_agent" VARCHAR(512),
    "triggered_by" INTEGER REFERENCES "users"("id"),
    
    "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for node_activity_logs
CREATE INDEX IF NOT EXISTS "idx_node_activity_logs_node_id" ON "node_activity_logs"("node_id");
CREATE INDEX IF NOT EXISTS "idx_node_activity_logs_institution_id" ON "node_activity_logs"("institution_id");
CREATE INDEX IF NOT EXISTS "idx_node_activity_logs_activity_type" ON "node_activity_logs"("activity_type");
CREATE INDEX IF NOT EXISTS "idx_node_activity_logs_created_at" ON "node_activity_logs"("created_at");

-- Create updated_at trigger function for all tables
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_institutions_updated_at BEFORE UPDATE ON "institutions" FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_blockchain_nodes_updated_at BEFORE UPDATE ON "blockchain_nodes" FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_chaincode_deployments_updated_at BEFORE UPDATE ON "chaincode_deployments" FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default blockchain nodes for existing institutions
INSERT INTO "blockchain_nodes" ("node_id", "institution_id", "node_type", "network_type", "url", "port", "msp_id", "peer_id", "orderer_id", "channel_name", "chaincode_name", "chaincode_version", "status", "created_at")
SELECT 
    'NODE_' || code || '_001' as node_id,
    id as institution_id,
    CASE 
        WHEN role = 'ISSUER' THEN 'peer'
        ELSE 'peer'
    END as node_type,
    'fabric' as network_type,
    'https://' || LOWER(code) || '-node.example.com' as url,
    7051 as port,
    code || 'MSP' as msp_id,
    'peer0.' || LOWER(code) || '.example.com' as peer_id,
    'orderer.example.com' as orderer_id,
    'lgcse-channel' as channel_name,
    'certificate_chaincode' as chaincode_name,
    '1.0.0' as chaincode_version,
    'inactive' as status,
    CURRENT_TIMESTAMP as created_at
FROM "institutions"
WHERE "blockchain_node_id" IS NULL;

-- Update institutions table with blockchain node references
UPDATE "institutions" 
SET 
    "blockchain_node_id" = 'NODE_' || code || '_001',
    "blockchain_node_url" = 'https://' || LOWER(code) || '-node.example.com',
    "blockchain_node_port" = 7051,
    "blockchain_network" = 'fabric',
    "chaincode_name" = 'certificate_chaincode',
    "chaincode_version" = '1.0.0',
    "msp_id" = code || 'MSP',
    "peer_id" = 'peer0.' || LOWER(code) || '.example.com',
    "orderer_id" = 'orderer.example.com',
    "channel_name" = 'lgcse-channel',
    "updated_at" = CURRENT_TIMESTAMP
WHERE "blockchain_node_id" IS NULL;

-- Create initial chaincode deployments for each node
INSERT INTO "chaincode_deployments" ("deployment_id", "node_id", "institution_id", "chaincode_name", "chaincode_version", "chaincode_path", "channel_name", "init_required", "init_args", "status", "created_at")
SELECT 
    'DEPLOY_' || bn.node_id || '_' || CURRENT_DATE as deployment_id,
    bn.id as node_id,
    bn.institution_id,
    'certificate_chaincode' as chaincode_name,
    '1.0.0' as chaincode_version,
    '/opt/gopath/src/github.com/chaincode/certificate' as chaincode_path,
    'lgcse-channel' as channel_name,
    TRUE as init_required,
    '["InitLedger"]'::jsonb as init_args,
    'pending' as status,
    CURRENT_TIMESTAMP as created_at
FROM "blockchain_nodes" bn
WHERE NOT EXISTS (
    SELECT 1 FROM "chaincode_deployments" cd 
    WHERE cd.node_id = bn.id AND cd.chaincode_name = 'certificate_chaincode'
);

-- Create view for institution blockchain status
CREATE OR REPLACE VIEW "institution_blockchain_status" AS
SELECT 
    i.id,
    i.code,
    i.name,
    i.role,
    i.blockchain_node_id,
    i.blockchain_node_status,
    i.blockchain_network,
    i.chaincode_installed,
    i.chaincode_instantiated,
    i.last_sync_at,
    bn.node_type,
    bn.status as node_status,
    bn.block_height,
    bn.network_height,
    bn.last_heartbeat,
    cd.status as deployment_status,
    cd.created_at as deployment_created_at
FROM "institutions" i
LEFT JOIN "blockchain_nodes" bn ON i.blockchain_node_id = bn.node_id
LEFT JOIN LATERAL (
    SELECT status, created_at
    FROM "chaincode_deployments"
    WHERE node_id = bn.id
    ORDER BY created_at DESC
    LIMIT 1
) cd ON true;

-- Grant necessary permissions (adjust based on your database user)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON "blockchain_nodes" TO certivert;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON "chaincode_deployments" TO certivert;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON "node_activity_logs" TO certivert;
-- GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO certivert;

-- Commit transaction
COMMIT;

-- Log migration completion
DO $$
BEGIN
    RAISE NOTICE 'Blockchain nodes migration completed successfully';
    RAISE NOTICE 'Added blockchain fields to institutions table';
    RAISE NOTICE 'Created blockchain_nodes, chaincode_deployments, and node_activity_logs tables';
    RAISE NOTICE 'Initialized default blockchain nodes for existing institutions';
    RAISE NOTICE 'Created institution_blockchain_status view';
END $$;
