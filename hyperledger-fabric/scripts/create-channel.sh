#!/bin/bash

#
# Hyperledger Fabric Channel Creation Script for LGCSE Certificate Verification
#
# This script creates the LGCSE channel and joins all peer organizations
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_color() {
    echo -e "${1}${2}${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_color $RED "❌ Docker is not running. Please start Docker and try again."
        exit 1
    fi
    print_color $GREEN "✅ Docker is running"
}

# Function to check prerequisites
check_prerequisites() {
    print_color $BLUE "🔍 Checking prerequisites..."
    
    # Check for Docker
    check_docker
    
    # Check if cryptogen is available
    if ! command_exists cryptogen; then
        print_color $RED "❌ cryptogen is not available. Please ensure Fabric binaries are installed."
        exit 1
    fi
    print_color $GREEN "✅ cryptogen is available"
    
    # Check if configtxgen is available
    if ! command_exists configtxgen; then
        print_color $RED "❌ configtxgen is not available. Please ensure Fabric binaries are installed."
        exit 1
    fi
    print_color $GREEN "✅ configtxgen is available"
    
    # Check if peer CLI is available
    if ! command_exists peer; then
        print_color $RED "❌ peer CLI is not available. Please ensure Fabric binaries are installed."
        exit 1
    fi
    print_color $GREEN "✅ peer CLI is available"
    
    # Check if organizations directory exists
    if [ ! -d "organizations" ]; then
        print_color $RED "❌ organizations directory not found. Please run setup-ca.sh first."
        exit 1
    fi
    print_color $GREEN "✅ organizations directory found"
}

# Function to generate crypto material
generate_crypto() {
    print_color $BLUE "🔐 Generating crypto material..."
    
    # Generate crypto configuration
    if [ ! -f "crypto-config.yaml" ]; then
        print_color $RED "❌ crypto-config.yaml not found"
        exit 1
    fi
    
    # Generate crypto material
    cryptogen generate --config=crypto-config.yaml --output="organizations"
    
    print_color $GREEN "✅ Crypto material generated"
}

# Function to generate channel artifacts
generate_channel_artifacts() {
    print_color $BLUE "📄 Generating channel artifacts..."
    
    # Create channel artifacts directory
    mkdir -p channel-artifacts
    
    # Generate system channel genesis block
    print_color $YELLOW "🔧 Generating system channel genesis block..."
    configtxgen -profile LGCSESystemChannel -channelID system-channel -outputBlock ./channel-artifacts/genesis.block
    
    # Generate LGCSE channel configuration transaction
    print_color $YELLOW "🔧 Generating LGCSE channel configuration..."
    configtxgen -profile LGCSEChannel -channelID lgcse-channel -outputCreateChannelTx ./channel-artifacts/lgcse-channel.tx
    
    # Generate anchor peer updates for each organization
    print_color $YELLOW "🔧 Generating anchor peer updates..."
    
    # Ecol anchor peer update
    configtxgen -profile LGCSEChannel -channelID lgcse-channel -outputAnchorPeersUpdate ./channel-artifacts/EcolMSPanchors.tx -asOrg EcolOrgMSP
    
    # Limkokwing anchor peer update
    configtxgen -profile LGCSEChannel -channelID lgcse-channel -outputAnchorPeersUpdate ./channel-artifacts/LimkokwingMSPanchors.tx -asOrg LimkokwingOrgMSP
    
    # Botho anchor peer update
    configtxgen -profile LGCSEChannel -channelID lgcse-channel -outputAnchorPeersUpdate ./channel-artifacts/BothoMSPanchors.tx -asOrg BothoOrgMSP
    
    # Nul anchor peer update
    configtxgen -profile LGCSEChannel -channelID lgcse-channel -outputAnchorPeersUpdate ./channel-artifacts/NulMSPanchors.tx -asOrg NulOrgMSP
    
    print_color $GREEN "✅ Channel artifacts generated"
}

# Function to start orderer
start_orderer() {
    print_color $BLUE "🚀 Starting orderer..."
    
    # Start orderer
    docker-compose -f docker-compose.yaml up -d orderer.example.com
    
    # Wait for orderer to start
    print_color $YELLOW "⏳ Waiting for orderer to start..."
    sleep 10
    
    # Check if orderer is running
    if docker ps | grep orderer.example.com >/dev/null 2>&1; then
        print_color $GREEN "✅ Orderer is running"
    else
        print_color $RED "❌ Orderer failed to start"
        exit 1
    fi
}

# Function to create system channel
create_system_channel() {
    print_color $BLUE "🔧 Creating system channel..."
    
    # Create system channel using orderer CLI
    docker exec orderer.example.com osnadmin channel join \
        --channelID system-channel \
        --config-block ./channel-artifacts/genesis.block \
        -o orderer.example.com:7053 \
        --ca-file /etc/hyperledger/fabric/tls/ca.crt \
        --client-cert /etc/hyperledger/fabric/tls/server.crt \
        --client-key /etc/hyperledger/fabric/tls/server.key
    
    print_color $GREEN "✅ System channel created"
}

# Function to start all peers
start_peers() {
    print_color $BLUE "🚀 Starting all peers..."
    
    # Start all peers
    docker-compose -f docker-compose.yaml up -d peer0.ecol.example.com peer0.limkokwing.example.com peer0.botho.example.com peer0.nul.example.com
    
    # Wait for peers to start
    print_color $YELLOW "⏳ Waiting for peers to start..."
    sleep 15
    
    # Check if all peers are running
    peers=("peer0.ecol.example.com" "peer0.limkokwing.example.com" "peer0.botho.example.com" "peer0.nul.example.com")
    
    for peer in "${peers[@]}"; do
        if docker ps | grep $peer >/dev/null 2>&1; then
            print_color $GREEN "✅ $peer is running"
        else
            print_color $RED "❌ $peer failed to start"
            exit 1
        fi
    done
    
    print_color $GREEN "✅ All peers are running"
}

# Function to create LGCSE channel
create_lgcse_channel() {
    print_color $BLUE "🔧 Creating LGCSE channel..."
    
    # Copy channel artifacts to CLI container
    docker cp channel-artifacts/lgcse-channel.tx cli:/opt/gopath/src/github.com/hyperledger/fabric/peer/
    
    # Create channel using Ecol peer
    docker exec -e CORE_PEER_TLS_ENABLED=true -e CORE_PEER_LOCALMSPID=EcolOrgMSP -e CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/ecol.example.com/peers/peer0.ecol.example.com/tls/ca.crt -e CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/ecol.example.com/users/Admin@ecol.example.com/msp -e CORE_PEER_ADDRESS=peer0.ecol.example.com:7051 cli peer channel create -o orderer.example.com:7050 -c lgcse-channel --ordererTLSHostnameOverride orderer.example.com -f ./lgcse-channel.tx --outputBlock ./lgcse-channel.block --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
    
    print_color $GREEN "✅ LGCSE channel created"
}

# Function to join peers to channel
join_peers_to_channel() {
    print_color $BLUE "🔗 Joining peers to LGCSE channel..."
    
    # Function to join a specific peer to channel
    join_peer() {
        local peer_name=$1
        local peer_address=$2
        local peer_msp=$3
        local peer_domain=$4
        
        print_color $YELLOW "🔧 Joining $peer_name to channel..."
        
        # Copy channel block to peer
        docker cp cli:/opt/gopath/src/github.com/hyperledger/fabric/peer/lgcse-channel.block $peer_name:/tmp/
        
        # Join peer to channel
        docker exec -e CORE_PEER_TLS_ENABLED=true -e CORE_PEER_LOCALMSPID=$peer_msp -e CORE_PEER_TLS_ROOTCERT_FILE=/etc/hyperledger/fabric/tls/ca.crt -e CORE_PEER_MSPCONFIGPATH=/etc/hyperledger/fabric/msp -e CORE_PEER_ADDRESS=$peer_address $peer_name peer channel join -b /tmp/lgcse-channel.block --tls --cafile /etc/hyperledger/fabric/tls/ca.crt
        
        print_color $GREEN "✅ $peer_name joined channel"
    }
    
    # Join all peers to channel
    join_peer "peer0.ecol.example.com" "peer0.ecol.example.com:7051" "EcolOrgMSP" "ecol.example.com"
    join_peer "peer0.limkokwing.example.com" "peer0.limkokwing.example.com:9051" "LimkokwingOrgMSP" "limkokwing.example.com"
    join_peer "peer0.botho.example.com" "peer0.botho.example.com:11051" "BothoOrgMSP" "botho.example.com"
    join_peer "peer0.nul.example.com" "peer0.nul.example.com:12051" "NulOrgMSP" "nul.example.com"
    
    print_color $GREEN "✅ All peers joined channel"
}

# Function to update anchor peers
update_anchor_peers() {
    print_color $BLUE "🔧 Updating anchor peers..."
    
    # Function to update anchor peer for an organization
    update_anchor() {
        local org_name=$1
        local org_msp=$2
        local anchor_file=$3
        local peer_address=$4
        local peer_domain=$5
        
        print_color $YELLOW "🔧 Updating anchor peer for $org_name..."
        
        # Copy anchor peer update file to CLI
        docker cp channel-artifacts/$anchor_file cli:/opt/gopath/src/github.com/hyperledger/fabric/peer/
        
        # Update anchor peer
        docker exec -e CORE_PEER_TLS_ENABLED=true -e CORE_PEER_LOCALMSPID=$org_msp -e CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/$peer_domain/peers/peer0.$peer_domain/tls/ca.crt -e CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/$peer_domain/users/Admin@$peer_domain/msp -e CORE_PEER_ADDRESS=$peer_address cli peer channel update -o orderer.example.com:7050 -c lgcse-channel -f ./$anchor_file --ordererTLSHostnameOverride orderer.example.com --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
        
        print_color $GREEN "✅ Anchor peer updated for $org_name"
    }
    
    # Update anchor peers for all organizations
    update_anchor "Ecol" "EcolOrgMSP" "EcolMSPanchors.tx" "peer0.ecol.example.com:7051" "ecol.example.com"
    update_anchor "Limkokwing" "LimkokwingOrgMSP" "LimkokwingMSPanchors.tx" "peer0.limkokwing.example.com:9051" "limkokwing.example.com"
    update_anchor "Botho" "BothoOrgMSP" "BothoMSPanchors.tx" "peer0.botho.example.com:11051" "botho.example.com"
    update_anchor "Nul" "NulOrgMSP" "NulMSPanchors.tx" "peer0.nul.example.com:12051" "nul.example.com"
    
    print_color $GREEN "✅ All anchor peers updated"
}

# Function to verify channel setup
verify_channel_setup() {
    print_color $BLUE "🔍 Verifying channel setup..."
    
    # Check channel list
    print_color $YELLOW "📋 Channel list:"
    docker exec -e CORE_PEER_TLS_ENABLED=true -e CORE_PEER_LOCALMSPID=EcolOrgMSP -e CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/ecol.example.com/peers/peer0.ecol.example.com/tls/ca.crt -e CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/ecol.example.com/users/Admin@ecol.example.com/msp -e CORE_PEER_ADDRESS=peer0.ecol.example.com:7051 cli peer channel list
    
    # Get channel info
    print_color $YELLOW "📋 Channel info:"
    docker exec -e CORE_PEER_TLS_ENABLED=true -e CORE_PEER_LOCALMSPID=EcolOrgMSP -e CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/ecol.example.com/peers/peer0.ecol.example.com/tls/ca.crt -e CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/ecol.example.com/users/Admin@ecol.example.com/msp -e CORE_PEER_ADDRESS=peer0.ecol.example.com:7051 cli peer channel getinfo -c lgcse-channel
    
    # Check peer list
    print_color $YELLOW "📋 Peer list:"
    docker exec -e CORE_PEER_TLS_ENABLED=true -e CORE_PEER_LOCALMSPID=EcolOrgMSP -e CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/ecol.example.com/peers/peer0.ecol.example.com/tls/ca.crt -e CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/ecol.example.com/users/Admin@ecol.example.com/msp -e CORE_PEER_ADDRESS=peer0.ecol.example.com:7051 cli peer channel getinfo -c lgcse-channel | jq '.peers'
    
    print_color $GREEN "✅ Channel setup verification completed"
}

# Function to cleanup
cleanup() {
    print_color $YELLOW "🧹 Cleaning up..."
    
    # Stop all containers
    docker-compose -f docker-compose.yaml down
    
    # Remove channel artifacts
    rm -rf channel-artifacts
    
    print_color $GREEN "✅ Cleanup completed"
}

# Function to display network status
display_network_status() {
    print_color $BLUE "📊 Network Status:"
    print_color $BLUE "=================="
    
    # Display running containers
    print_color $YELLOW "📋 Running containers:"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    # Display channel information
    print_color $YELLOW "📋 Channel information:"
    docker exec -e CORE_PEER_TLS_ENABLED=true -e CORE_PEER_LOCALMSPID=EcolOrgMSP -e CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/ecol.example.com/peers/peer0.ecol.example.com/tls/ca.crt -e CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/ecol.example.com/users/Admin@ecol.example.com/msp -e CORE_PEER_ADDRESS=peer0.ecol.example.com:7051 cli peer channel list
    
    # Display peer organizations
    print_color $YELLOW "📋 Peer organizations:"
    echo "  - Ecol University (Issuer)"
    echo "  - Limkokwing University (Verifier)"
    echo "  - Botho University (Verifier)"
    echo "  - National University of Lesotho (Verifier)"
    
    print_color $GREEN "✅ Network is ready for chaincode deployment"
}

# Main execution
main() {
    print_color $BLUE "🚀 Starting Hyperledger Fabric Channel Creation"
    print_color $BLUE "=============================================="
    
    # Check prerequisites
    check_prerequisites
    
    # Generate crypto material
    generate_crypto
    
    # Generate channel artifacts
    generate_channel_artifacts
    
    # Start orderer
    start_orderer
    
    # Create system channel
    create_system_channel
    
    # Start peers
    start_peers
    
    # Create LGCSE channel
    create_lgcse_channel
    
    # Join peers to channel
    join_peers_to_channel
    
    # Update anchor peers
    update_anchor_peers
    
    # Verify channel setup
    verify_channel_setup
    
    # Display network status
    display_network_status
    
    print_color $GREEN "🎉 Hyperledger Fabric channel setup completed successfully!"
    print_color $BLUE "📋 Summary:"
    print_color $BLUE "   - System channel created: system-channel"
    print_color $BLUE "   - Application channel created: lgcse-channel"
    print_color $BLUE "   - 4 peers joined to channel"
    print_color $BLUE "   - Anchor peers configured"
    print_color $BLUE "   - Network is ready for chaincode deployment"
    print_color $BLUE ""
    print_color $BLUE "🔗 Next steps:"
    print_color $BLUE "   1. Deploy certificate verification chaincode"
    print_color $BLUE "   2. Test chaincode functionality"
    print_color $BLUE "   3. Integrate with backend application"
    print_color $BLUE ""
    print_color $GREEN "✨ LGCSE Certificate Verification Network is ready!"
}

# Handle script interruption
trap cleanup EXIT

# Run main function
main "$@"
