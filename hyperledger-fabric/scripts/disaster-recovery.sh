#!/bin/bash

#
# Hyperledger Fabric Disaster Recovery and Backup Script
#
# This script provides comprehensive backup and recovery procedures for the LGCSE
# Certificate Verification System, including ledger backups, CA database backups,
# MSP configuration backups, and disaster recovery procedures.
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="/backup/fabric"
NETWORK_NAME="lgcse-network"
BACKUP_RETENTION_DAYS=30
COMPRESSION_LEVEL=6
ENCRYPTION_ENABLED=true

# Function to print colored output
print_color() {
    echo -e "${1}${2}${NC}"
}

# Function to check prerequisites
check_prerequisites() {
    print_color $BLUE "🔍 Checking prerequisites..."
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        print_color $RED "❌ Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    # Check if required tools are available
    for tool in tar gzip openssl jq; do
        if ! command -v $tool >/dev/null 2>&1; then
            print_color $RED "❌ $tool is not installed. Please install $tool and try again."
            exit 1
        fi
    done
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$BACKUP_DIR/ledger"
    mkdir -p "$BACKUP_DIR/ca-databases"
    mkdir -p "$BACKUP_DIR/msp-configs"
    mkdir -p "$BACKUP_DIR/chaincode"
    mkdir -p "$BACKUP_DIR/configs"
    mkdir -p "$BACKUP_DIR/logs"
    
    print_color $GREEN "✅ Prerequisites checked"
}

# Function to backup ledger data
backup_ledger() {
    print_color $BLUE "📦 Backing up ledger data..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/ledger/ledger_backup_$timestamp.tar.gz"
    
    # Stop peers to ensure consistent backup
    print_color $YELLOW "⏸️ Stopping peers for consistent backup..."
    docker-compose -f docker-compose.yaml stop peer0.ecol.example.com peer0.limkokwing.example.com peer0.botho.example.com peer0.nul.example.com
    
    # Backup peer ledger data
    for peer in peer0.ecol.example.com peer0.limkokwing.example.com peer0.botho.example.com peer0.nul.example.com; do
        print_color $YELLOW "📋 Backing up $peer ledger..."
        
        # Copy ledger data from container
        docker cp $peer:/var/hyperledger/production/ "$BACKUP_DIR/ledger/${peer}_ledger_$timestamp/"
        
        # Backup CouchDB data
        couchdb_container=$(echo $peer | sed 's/peer0/couchdb/g')
        if docker ps | grep -q $couchdb_container; then
            docker exec $couchdb_container couchdb-dump -u admin -p adminpw -b $couchdb_container > "$BACKUP_DIR/ledger/${peer}_couchdb_$timestamp.json"
        fi
    done
    
    # Create compressed backup
    print_color $YELLOW "🗜️ Compressing ledger backup..."
    tar -czf "$backup_file" -C "$BACKUP_DIR/ledger" "${peer}_ledger_$timestamp" "${peer}_couchdb_$timestamp.json"
    
    # Encrypt backup if enabled
    if [ "$ENCRYPTION_ENABLED" = true ]; then
        print_color $YELLOW "🔐 Encrypting ledger backup..."
        openssl enc -aes-256-cbc -salt -in "$backup_file" -out "${backup_file}.enc" -pass pass:$(cat /etc/fabric-backup-key 2>/dev/null || echo "default_key")
        rm "$backup_file"
        backup_file="${backup_file}.enc"
    fi
    
    # Restart peers
    print_color $YELLOW "▶️ Restarting peers..."
    docker-compose -f docker-compose.yaml start peer0.ecol.example.com peer0.limkokwing.example.com peer0.botho.example.com peer0.nul.example.com
    
    # Wait for peers to start
    sleep 10
    
    # Cleanup temporary files
    rm -rf "$BACKUP_DIR/ledger"/*_ledger_$timestamp
    rm -f "$BACKUP_DIR/ledger"/*_couchdb_$timestamp.json
    
    print_color $GREEN "✅ Ledger backup completed: $backup_file"
}

# Function to backup CA databases
backup_ca_databases() {
    print_color $BLUE "📦 Backing up CA databases..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/ca-databases/ca_backup_$timestamp.tar.gz"
    
    # Backup each CA
    for ca in ca.orderer.example.com ca.ecol.example.com ca.limkokwing.example.com ca.botho.example.com ca.nul.example.com; do
        print_color $YELLOW "📋 Backing up $ca database..."
        
        # Extract CA database from container
        if docker ps | grep -q $ca; then
            # Backup SQLite database (default for Fabric CA)
            docker exec $ca cp /etc/hyperledger/fabric-ca-server/db/fabric-ca-server.db "/tmp/${ca}_backup_$timestamp.db"
            docker cp $ca:/tmp/${ca}_backup_$timestamp.db "$BACKUP_DIR/ca-databases/"
            
            # Backup CA certificates and keys
            docker cp $ca:/etc/hyperledger/fabric-ca-server/ "$BACKUP_DIR/ca-databases/${ca}_config_$timestamp/"
        fi
    done
    
    # Create compressed backup
    print_color $YELLOW "🗜️ Compressing CA backup..."
    tar -czf "$backup_file" -C "$BACKUP_DIR/ca-databases" "*_backup_$timestamp.db" "*_config_$timestamp"
    
    # Encrypt backup if enabled
    if [ "$ENCRYPTION_ENABLED" = true ]; then
        print_color $YELLOW "🔐 Encrypting CA backup..."
        openssl enc -aes-256-cbc -salt -in "$backup_file" -out "${backup_file}.enc" -pass pass:$(cat /etc/fabric-backup-key 2>/dev/null || echo "default_key")
        rm "$backup_file"
        backup_file="${backup_file}.enc"
    fi
    
    # Cleanup temporary files
    rm -f "$BACKUP_DIR/ca-databases"/*_backup_$timestamp.db
    rm -rf "$BACKUP_DIR/ca-databases"/*_config_$timestamp
    
    print_color $GREEN "✅ CA database backup completed: $backup_file"
}

# Function to backup MSP configurations
backup_msp_configs() {
    print_color $BLUE "📦 Backing up MSP configurations..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/msp-configs/msp_backup_$timestamp.tar.gz"
    
    # Backup organization MSPs
    for org in orderer ecol limkokwing botho nul; do
        print_color $YELLOW "📋 Backing up $org MSP configuration..."
        
        if [ -d "organizations/${org}Organizations" ]; then
            cp -r "organizations/${org}Organizations" "$BACKUP_DIR/msp-configs/${org}_msp_$timestamp/"
        fi
        
        # Backup crypto material
        if [ -d "crypto-config/peerOrganizations/${org}.example.com" ]; then
            cp -r "crypto-config/peerOrganizations/${org}.example.com" "$BACKUP_DIR/msp-configs/${org}_crypto_$timestamp/"
        fi
    done
    
    # Create compressed backup
    print_color $YELLOW "🗜️ Compressing MSP backup..."
    tar -czf "$backup_file" -C "$BACKUP_DIR/msp-configs" "*_msp_$timestamp" "*_crypto_$timestamp"
    
    # Encrypt backup if enabled
    if [ "$ENCRYPTION_ENABLED" = true ]; then
        print_color $YELLOW "🔐 Encrypting MSP backup..."
        openssl enc -aes-256-cbc -salt -in "$backup_file" -out "${backup_file}.enc" -pass pass:$(cat /etc/fabric-backup-key 2>/dev/null || echo "default_key")
        rm "$backup_file"
        backup_file="${backup_file}.enc"
    fi
    
    # Cleanup temporary files
    rm -rf "$BACKUP_DIR/msp-configs"/*_msp_$timestamp
    rm -rf "$BACKUP_DIR/msp-configs"/*_crypto_$timestamp
    
    print_color $GREEN "✅ MSP configuration backup completed: $backup_file"
}

# Function to backup chaincode
backup_chaincode() {
    print_color $BLUE "📦 Backing up chaincode..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/chaincode/chaincode_backup_$timestamp.tar.gz"
    
    # Backup chaincode source
    if [ -d "chaincode" ]; then
        cp -r chaincode "$BACKUP_DIR/chaincode/chaincode_$timestamp/"
    fi
    
    # Backup chaincode packages
    mkdir -p "$BACKUP_DIR/chaincode/packages_$timestamp"
    for peer in peer0.ecol.example.com peer0.limkokwing.example.com peer0.botho.example.com peer0.nul.example.com; do
        if docker ps | grep -q $peer; then
            docker cp $peer:/var/hyperledger/production/chaincodes/ "$BACKUP_DIR/chaincode/packages_$timestamp/${peer}_chaincodes/"
        fi
    done
    
    # Create compressed backup
    print_color $YELLOW "🗜️ Compressing chaincode backup..."
    tar -czf "$backup_file" -C "$BACKUP_DIR/chaincode" "chaincode_$timestamp" "packages_$timestamp"
    
    # Encrypt backup if enabled
    if [ "$ENCRYPTION_ENABLED" = true ]; then
        print_color $YELLOW "🔐 Encrypting chaincode backup..."
        openssl enc -aes-256-cbc -salt -in "$backup_file" -out "${backup_file}.enc" -pass pass:$(cat /etc/fabric-backup-key 2>/dev/null || echo "default_key")
        rm "$backup_file"
        backup_file="${backup_file}.enc"
    fi
    
    # Cleanup temporary files
    rm -rf "$BACKUP_DIR/chaincode/chaincode_$timestamp"
    rm -rf "$BACKUP_DIR/chaincode/packages_$timestamp"
    
    print_color $GREEN "✅ Chaincode backup completed: $backup_file"
}

# Function to backup network configurations
backup_configs() {
    print_color $BLUE "📦 Backing up network configurations..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/configs/configs_backup_$timestamp.tar.gz"
    
    # Backup configuration files
    for config_file in configtx.yaml crypto-config.yaml docker-compose.yaml config/connection-profile.json; do
        if [ -f "$config_file" ]; then
            cp "$config_file" "$BACKUP_DIR/configs/"
        fi
    done
    
    # Backup environment files
    for env_file in .env .env.*; do
        if [ -f "$env_file" ]; then
            cp "$env_file" "$BACKUP_DIR/configs/"
        fi
    done
    
    # Backup scripts
    if [ -d "scripts" ]; then
        cp -r scripts "$BACKUP_DIR/configs/"
    fi
    
    # Create compressed backup
    print_color $YELLOW "🗜️ Compressing configuration backup..."
    tar -czf "$backup_file" -C "$BACKUP_DIR/configs" .
    
    # Encrypt backup if enabled
    if [ "$ENCRYPTION_ENABLED" = true ]; then
        print_color $YELLOW "🔐 Encrypting configuration backup..."
        openssl enc -aes-256-cbc -salt -in "$backup_file" -out "${backup_file}.enc" -pass pass:$(cat /etc/fabric-backup-key 2>/dev/null || echo "default_key")
        rm "$backup_file"
        backup_file="${backup_file}.enc"
    fi
    
    print_color $GREEN "✅ Configuration backup completed: $backup_file"
}

# Function to backup logs
backup_logs() {
    print_color $BLUE "📦 Backing up logs..."
    
    local timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_file="$BACKUP_DIR/logs/logs_backup_$timestamp.tar.gz"
    
    # Backup Docker logs
    for container in orderer.example.com peer0.ecol.example.com peer0.limkokwing.example.com peer0.botho.example.com peer0.nul.example.com ca.orderer.example.com ca.ecol.example.com ca.limkokwing.example.com ca.botho.example.com ca.nul.example.com; do
        if docker ps | grep -q $container; then
            docker logs $container > "$BACKUP_DIR/logs/${container}_$timestamp.log" 2>&1
        fi
    done
    
    # Backup application logs
    for log_file in logs/*.log; do
        if [ -f "$log_file" ]; then
            cp "$log_file" "$BACKUP_DIR/logs/"
        fi
    done
    
    # Create compressed backup
    print_color $YELLOW "🗜️ Compressing logs backup..."
    tar -czf "$backup_file" -C "$BACKUP_DIR/logs" .
    
    print_color $GREEN "✅ Logs backup completed: $backup_file"
}

# Function to perform full backup
full_backup() {
    print_color $BLUE "🚀 Starting full backup..."
    
    local start_time=$(date +%s)
    local backup_date=$(date +%Y%m%d_%H%M%S)
    local backup_manifest="$BACKUP_DIR/backup_manifest_$backup_date.json"
    
    # Create backup manifest
    local manifest="{\"backup_date\":\"$backup_date\",\"backup_type\":\"full\",\"components\":["
    
    # Backup each component
    backup_ledger
    manifest+="{\"component\":\"ledger\",\"status\":\"completed\"},"
    
    backup_ca_databases
    manifest+="{\"component\":\"ca_databases\",\"status\":\"completed\"},"
    
    backup_msp_configs
    manifest+="{\"component\":\"msp_configs\",\"status\":\"completed\"},"
    
    backup_chaincode
    manifest+="{\"component\":\"chaincode\",\"status\":\"completed\"},"
    
    backup_configs
    manifest+="{\"component\":\"configs\",\"status\":\"completed\"},"
    
    backup_logs
    manifest+="{\"component\":\"logs\",\"status\":\"completed\"}"
    
    manifest+="]}"
    
    # Save backup manifest
    echo "$manifest" > "$backup_manifest"
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    print_color $GREEN "🎉 Full backup completed in ${duration} seconds"
    print_color $GREEN "📋 Backup manifest: $backup_manifest"
}

# Function to restore ledger data
restore_ledger() {
    local backup_file=$1
    
    print_color $BLUE "🔄 Restoring ledger data from $backup_file..."
    
    # Decrypt backup if encrypted
    if [[ "$backup_file" == *.enc ]]; then
        print_color $YELLOW "🔓 Decrypting backup..."
        openssl enc -aes-256-cbc -d -in "$backup_file" -out "${backup_file%.enc}" -pass pass:$(cat /etc/fabric-backup-key 2>/dev/null || echo "default_key")
        backup_file="${backup_file%.enc}"
    fi
    
    # Stop peers
    print_color $YELLOW "⏸️ Stopping peers..."
    docker-compose -f docker-compose.yaml stop peer0.ecol.example.com peer0.limkokwing.example.com peer0.botho.example.com peer0.nul.example.com
    
    # Extract and restore ledger data
    local temp_dir=$(mktemp -d)
    tar -xzf "$backup_file" -C "$temp_dir"
    
    for peer_dir in "$temp_dir"/*_ledger_*; do
        peer_name=$(basename "$peer_dir" | sed 's/_ledger_.*//')
        print_color $YELLOW "📋 Restoring $peer_name ledger..."
        
        # Remove existing ledger data
        docker exec $peer_name rm -rf /var/hyperledger/production/*
        
        # Copy restored ledger data
        docker cp "$peer_dir/." $peer_name:/var/hyperledger/production/
        
        # Restore CouchDB data if available
        couchdb_backup=$(echo "$peer_dir" | sed 's/_ledger_/_couchdb_/').json
        if [ -f "$couchdb_backup" ]; then
            couchdb_container=$(echo $peer_name | sed 's/peer0/couchdb/g')
            docker exec $couchdb_container couchdb-load -u admin -p adminpw -b $couchdb_container < "$couchdb_backup"
        fi
    done
    
    # Cleanup
    rm -rf "$temp_dir"
    
    # Restart peers
    print_color $YELLOW "▶️ Restarting peers..."
    docker-compose -f docker-compose.yaml start peer0.ecol.example.com peer0.limkokwing.example.com peer0.botho.example.com peer0.nul.example.com
    
    # Wait for peers to start
    sleep 15
    
    print_color $GREEN "✅ Ledger restore completed"
}

# Function to restore CA databases
restore_ca_databases() {
    local backup_file=$1
    
    print_color $BLUE "🔄 Restoring CA databases from $backup_file..."
    
    # Decrypt backup if encrypted
    if [[ "$backup_file" == *.enc ]]; then
        print_color $YELLOW "🔓 Decrypting backup..."
        openssl enc -aes-256-cbc -d -in "$backup_file" -out "${backup_file%.enc}" -pass pass:$(cat /etc/fabric-backup-key 2>/dev/null || echo "default_key")
        backup_file="${backup_file%.enc}"
    fi
    
    # Extract and restore CA databases
    local temp_dir=$(mktemp -d)
    tar -xzf "$backup_file" -C "$temp_dir"
    
    for db_file in "$temp_dir"/*_backup_*.db; do
        ca_name=$(basename "$db_file" | sed 's/_backup_.*.db//')
        print_color $YELLOW "📋 Restoring $ca_name database..."
        
        # Stop CA
        docker stop $ca_name
        
        # Copy database file
        docker cp "$db_file" $ca_name:/etc/hyperledger/fabric-ca-server/db/fabric-ca-server.db
        
        # Restore CA configuration
        config_dir=$(echo "$db_file" | sed 's/_backup_.*.db/_config_*/')
        if [ -d "$config_dir" ]; then
            docker cp "$config_dir/." $ca_name:/etc/hyperledger/fabric-ca-server/
        fi
        
        # Start CA
        docker start $ca_name
        
        # Wait for CA to start
        sleep 5
    done
    
    # Cleanup
    rm -rf "$temp_dir"
    
    print_color $GREEN "✅ CA database restore completed"
}

# Function to perform full restore
full_restore() {
    local backup_date=$1
    
    print_color $BLUE "🔄 Starting full restore from $backup_date..."
    
    # Find backup files
    local ledger_backup=$(find "$BACKUP_DIR/ledger" -name "ledger_backup_$backup_date*" | head -1)
    local ca_backup=$(find "$BACKUP_DIR/ca-databases" -name "ca_backup_$backup_date*" | head -1)
    local msp_backup=$(find "$BACKUP_DIR/msp-configs" -name "msp_backup_$backup_date*" | head -1)
    local chaincode_backup=$(find "$BACKUP_DIR/chaincode" -name "chaincode_backup_$backup_date*" | head -1)
    local config_backup=$(find "$BACKUP_DIR/configs" -name "configs_backup_$backup_date*" | head -1)
    
    # Stop all services
    print_color $YELLOW "⏸️ Stopping all services..."
    docker-compose -f docker-compose.yaml down
    
    # Restore components
    if [ -n "$ledger_backup" ]; then
        restore_ledger "$ledger_backup"
    fi
    
    if [ -n "$ca_backup" ]; then
        restore_ca_databases "$ca_backup"
    fi
    
    if [ -n "$msp_backup" ]; then
        print_color $YELLOW "📋 Restoring MSP configurations..."
        # Decrypt if needed
        if [[ "$msp_backup" == *.enc ]]; then
            openssl enc -aes-256-cbc -d -in "$msp_backup" -out "${msp_backup%.enc}" -pass pass:$(cat /etc/fabric-backup-key 2>/dev/null || echo "default_key")
            msp_backup="${msp_backup%.enc}"
        fi
        tar -xzf "$msp_backup" -C .
    fi
    
    if [ -n "$chaincode_backup" ]; then
        print_color $YELLOW "📋 Restoring chaincode..."
        # Decrypt if needed
        if [[ "$chaincode_backup" == *.enc ]]; then
            openssl enc -aes-256-cbc -d -in "$chaincode_backup" -out "${chaincode_backup%.enc}" -pass pass:$(cat /etc/fabric-backup-key 2>/dev/null || echo "default_key")
            chaincode_backup="${chaincode_backup%.enc}"
        fi
        tar -xzf "$chaincode_backup" -C .
    fi
    
    if [ -n "$config_backup" ]; then
        print_color $YELLOW "📋 Restoring configurations..."
        # Decrypt if needed
        if [[ "$config_backup" == *.enc ]]; then
            openssl enc -aes-256-cbc -d -in "$config_backup" -out "${config_backup%.enc}" -pass pass:$(cat /etc/fabric-backup-key 2>/dev/null || echo "default_key")
            config_backup="${config_backup%.enc}"
        fi
        tar -xzf "$config_backup" -C .
    fi
    
    # Start all services
    print_color $YELLOW "▶️ Starting all services..."
    docker-compose -f docker-compose.yaml up -d
    
    # Wait for services to start
    sleep 30
    
    print_color $GREEN "🎉 Full restore completed"
}

# Function to cleanup old backups
cleanup_old_backups() {
    print_color $BLUE "🧹 Cleaning up old backups (older than $BACKUP_RETENTION_DAYS days)..."
    
    local deleted_count=0
    
    # Cleanup ledger backups
    for backup_file in "$BACKUP_DIR/ledger"/*.tar.gz*; do
        if [ -f "$backup_file" ]; then
            local file_age=$(find "$backup_file" -mtime +$BACKUP_RETENTION_DAYS -print)
            if [ -n "$file_age" ]; then
                rm "$file_age"
                ((deleted_count++))
            fi
        fi
    done
    
    # Cleanup CA backups
    for backup_file in "$BACKUP_DIR/ca-databases"/*.tar.gz*; do
        if [ -f "$backup_file" ]; then
            local file_age=$(find "$backup_file" -mtime +$BACKUP_RETENTION_DAYS -print)
            if [ -n "$file_age" ]; then
                rm "$file_age"
                ((deleted_count++))
            fi
        fi
    done
    
    # Cleanup MSP backups
    for backup_file in "$BACKUP_DIR/msp-configs"/*.tar.gz*; do
        if [ -f "$backup_file" ]; then
            local file_age=$(find "$backup_file" -mtime +$BACKUP_RETENTION_DAYS -print)
            if [ -n "$file_age" ]; then
                rm "$file_age"
                ((deleted_count++))
            fi
        fi
    done
    
    # Cleanup chaincode backups
    for backup_file in "$BACKUP_DIR/chaincode"/*.tar.gz*; do
        if [ -f "$backup_file" ]; then
            local file_age=$(find "$backup_file" -mtime +$BACKUP_RETENTION_DAYS -print)
            if [ -n "$file_age" ]; then
                rm "$file_age"
                ((deleted_count++))
            fi
        fi
    done
    
    # Cleanup configuration backups
    for backup_file in "$BACKUP_DIR/configs"/*.tar.gz*; do
        if [ -f "$backup_file" ]; then
            local file_age=$(find "$backup_file" -mtime +$BACKUP_RETENTION_DAYS -print)
            if [ -n "$file_age" ]; then
                rm "$file_age"
                ((deleted_count++))
            fi
        fi
    done
    
    # Cleanup log backups
    for backup_file in "$BACKUP_DIR/logs"/*.tar.gz*; do
        if [ -f "$backup_file" ]; then
            local file_age=$(find "$backup_file" -mtime +$BACKUP_RETENTION_DAYS -print)
            if [ -n "$file_age" ]; then
                rm "$file_age"
                ((deleted_count++))
            fi
        fi
    done
    
    print_color $GREEN "✅ Cleanup completed. Deleted $deleted_count old backup files"
}

# Function to list available backups
list_backups() {
    print_color $BLUE "📋 Available backups:"
    print_color $BLUE "====================="
    
    # List ledger backups
    print_color $YELLOW "📦 Ledger backups:"
    ls -la "$BACKUP_DIR/ledger"/*.tar.gz* 2>/dev/null || echo "No ledger backups found"
    
    # List CA backups
    print_color $YELLOW "📦 CA database backups:"
    ls -la "$BACKUP_DIR/ca-databases"/*.tar.gz* 2>/dev/null || echo "No CA backups found"
    
    # List MSP backups
    print_color $YELLOW "📦 MSP configuration backups:"
    ls -la "$BACKUP_DIR/msp-configs"/*.tar.gz* 2>/dev/null || echo "No MSP backups found"
    
    # List chaincode backups
    print_color $YELLOW "📦 Chaincode backups:"
    ls -la "$BACKUP_DIR/chaincode"/*.tar.gz* 2>/dev/null || echo "No chaincode backups found"
    
    # List configuration backups
    print_color $YELLOW "📦 Configuration backups:"
    ls -la "$BACKUP_DIR/configs"/*.tar.gz* 2>/dev/null || echo "No configuration backups found"
    
    # List backup manifests
    print_color $YELLOW "📋 Backup manifests:"
    ls -la "$BACKUP_DIR"/backup_manifest_*.json 2>/dev/null || echo "No backup manifests found"
}

# Function to verify backup integrity
verify_backup() {
    local backup_file=$1
    
    print_color $BLUE "🔍 Verifying backup integrity: $backup_file"
    
    # Decrypt if needed
    local test_file="$backup_file"
    if [[ "$backup_file" == *.enc ]]; then
        print_color $YELLOW "🔓 Decrypting for verification..."
        openssl enc -aes-256-cbc -d -in "$backup_file" -out "${backup_file%.enc}.test" -pass pass:$(cat /etc/fabric-backup-key 2>/dev/null || echo "default_key")
        test_file="${backup_file%.enc}.test"
    fi
    
    # Test archive integrity
    if tar -tzf "$test_file" >/dev/null 2>&1; then
        print_color $GREEN "✅ Backup integrity verified"
        
        # Show archive contents
        print_color $YELLOW "📋 Archive contents:"
        tar -tzf "$test_file" | head -20
        
        # Cleanup test file
        rm -f "$test_file"
        
        return 0
    else
        print_color $RED "❌ Backup integrity check failed"
        rm -f "$test_file"
        return 1
    fi
}

# Function to create backup schedule
create_backup_schedule() {
    print_color $BLUE "📅 Creating backup schedule..."
    
    # Create cron job for daily backups
    local cron_file="/etc/cron.d/fabric-backup"
    local script_path="$(pwd)/scripts/disaster-recovery.sh"
    
    cat > "$cron_file" << EOF
# Fabric Network Backup Schedule
0 2 * * * root $script_path full_backup >/var/log/fabric-backup.log 2>&1
0 3 * * 0 root $script_path cleanup_old_backups >/var/log/fabric-cleanup.log 2>&1
EOF
    
    # Reload cron
    systemctl reload cron 2>/dev/null || service cron reload 2>/dev/null
    
    print_color $GREEN "✅ Backup schedule created"
    print_color $GREEN "📋 Daily backups scheduled for 2:00 AM"
    print_color $GREEN "📋 Cleanup scheduled for 3:00 AM on Sundays"
}

# Main execution
main() {
    local action=${1:-"help"}
    
    print_color $BLUE "🚀 Hyperledger Fabric Disaster Recovery"
    print_color $BLUE "====================================="
    
    case $action in
        "backup"|"full_backup")
            check_prerequisites
            full_backup
            ;;
        "restore")
            if [ -z "$2" ]; then
                print_color $RED "❌ Please provide backup date (format: YYYYMMDD_HHMMSS)"
                exit 1
            fi
            check_prerequisites
            full_restore "$2"
            ;;
        "ledger")
            check_prerequisites
            backup_ledger
            ;;
        "ca")
            check_prerequisites
            backup_ca_databases
            ;;
        "msp")
            check_prerequisites
            backup_msp_configs
            ;;
        "chaincode")
            check_prerequisites
            backup_chaincode
            ;;
        "configs")
            check_prerequisites
            backup_configs
            ;;
        "logs")
            backup_logs
            ;;
        "cleanup")
            cleanup_old_backups
            ;;
        "list")
            list_backups
            ;;
        "verify")
            if [ -z "$2" ]; then
                print_color $RED "❌ Please provide backup file path"
                exit 1
            fi
            verify_backup "$2"
            ;;
        "schedule")
            create_backup_schedule
            ;;
        "help"|*)
            echo "Usage: $0 {full_backup|restore|ledger|ca|msp|chaincode|configs|logs|cleanup|list|verify|schedule|help}"
            echo ""
            echo "Commands:"
            echo "  full_backup     - Perform complete backup of all components"
            echo "  restore <date>  - Restore from backup (format: YYYYMMDD_HHMMSS)"
            echo "  ledger          - Backup ledger data only"
            echo "  ca              - Backup CA databases only"
            echo "  msp             - Backup MSP configurations only"
            echo "  chaincode       - Backup chaincode only"
            echo "  configs         - Backup network configurations only"
            echo "  logs            - Backup logs only"
            echo "  cleanup         - Clean up old backups"
            echo "  list            - List available backups"
            echo "  verify <file>   - Verify backup integrity"
            echo "  schedule        - Create automated backup schedule"
            echo "  help            - Show this help message"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
