#!/bin/bash

#
# Hyperledger Fabric Chaincode Deployment Script for LGCSE Certificate Verification
#
# This script handles the complete chaincode lifecycle: package, install, approve, commit, and invoke
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

# Configuration
CHAINCODE_NAME="certificate-chaincode"
CHAINCODE_VERSION="1.0.0"
CHAINCODE_PATH="chaincode/certificate-chaincode"
CHANNEL_NAME="lgcse-channel"
SEQUENCE="1"

# Organizations and their peers
declare -A ORGANIZATIONS=(
    ["Ecol"]="peer0.ecol.example.com:7051"
    ["Limkokwing"]="peer0.limkokwing.example.com:9051"
    ["Botho"]="peer0.botho.example.com:11051"
    ["Nul"]="peer0.nul.example.com:12051"
)

declare -A ORG_MSPS=(
    ["Ecol"]="EcolOrgMSP"
    ["Limkokwing"]="LimkokwingOrgMSP"
    ["Botho"]="BothoOrgMSP"
    ["Nul"]="NulOrgMSP"
)

declare -A ORG_DOMAINS=(
    ["Ecol"]="ecol.example.com"
    ["Limkokwing"]="limkokwing.example.com"
    ["Botho"]="botho.example.com"
    ["Nul"]="nul.example.com"
)

# Function to check prerequisites
check_prerequisites() {
    print_color $BLUE "🔍 Checking prerequisites..."
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        print_color $RED "❌ Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    # Check if channel exists
    if ! docker exec -e CORE_PEER_TLS_ENABLED=true -e CORE_PEER_LOCALMSPID=EcolOrgMSP -e CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/ecol.example.com/peers/peer0.ecol.example.com/tls/ca.crt -e CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/ecol.example.com/users/Admin@ecol.example.com/msp -e CORE_PEER_ADDRESS=peer0.ecol.example.com:7051 cli peer channel list | grep -q $CHANNEL_NAME; then
        print_color $RED "❌ Channel $CHANNEL_NAME not found. Please run create-channel.sh first."
        exit 1
    fi
    
    # Check if chaincode directory exists
    if [ ! -d "$CHAINCODE_PATH" ]; then
        print_color $RED "❌ Chaincode directory $CHAINCODE_PATH not found."
        exit 1
    fi
    
    print_color $GREEN "✅ Prerequisites checked"
}

# Function to build chaincode
build_chaincode() {
    print_color $BLUE "🔧 Building chaincode..."
    
    # Check if Go is installed
    if ! command -v go >/dev/null 2>&1; then
        print_color $RED "❌ Go is not installed. Please install Go and try again."
        exit 1
    fi
    
    # Build chaincode
    cd $CHAINCODE_PATH
    go mod tidy
    go build -o /tmp/chaincode/certificate-chaincode .
    cd - >/dev/null
    
    print_color $GREEN "✅ Chaincode built successfully"
}

# Function to package chaincode
package_chaincode() {
    local org=$1
    local peer_address=${ORGANIZATIONS[$org]}
    local org_msp=${ORG_MSPS[$org]}
    local org_domain=${ORG_DOMAINS[$org]}
    
    print_color $BLUE "📦 Packaging chaincode for $org..."
    
    # Create chaincode package
    docker exec -e CORE_PEER_TLS_ENABLED=true -e CORE_PEER_LOCALMSPID=$org_msp -e CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/$org_domain/peers/peer0.$org_domain/tls/ca.crt -e CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/$org_domain/users/Admin@$org_domain/msp -e CORE_PEER_ADDRESS=$peer_address cli peer lifecycle chaincode package ${CHAINCODE_NAME}.tar.gz --path $CHAINCODE_PATH --label ${CHAINCODE_NAME}_${CHAINCODE_VERSION}
    
    # Copy package to host
    docker cp $(docker ps -q -f name=peer0.${org,,}.example.com):/opt/gopath/src/github.com/hyperledger/fabric/peer/${CHAINCODE_NAME}.tar.gz ./${CHAINCODE_NAME}_${org}.tar.gz
    
    print_color $GREEN "✅ Chaincode packaged for $org"
}

# Function to install chaincode on peer
install_chaincode() {
    local org=$1
    local peer_address=${ORGANIZATIONS[$org]}
    local org_msp=${ORG_MSPS[$org]}
    local org_domain=${ORG_DOMAINS[$org]}
    
    print_color $BLUE "🔧 Installing chaincode on $org peer..."
    
    # Copy package to peer
    docker cp ./${CHAINCODE_NAME}_${org}.tar.gz $(docker ps -q -f name=peer0.${org,,}.example.com):/opt/gopath/src/github.com/hyperledger/fabric/peer/
    
    # Install chaincode
    docker exec -e CORE_PEER_TLS_ENABLED=true -e CORE_PEER_LOCALMSPID=$org_msp -e CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/$org_domain/peers/peer0.$org_domain/tls/ca.crt -e CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/$org_domain/users/Admin@$org_domain/msp -e CORE_PEER_ADDRESS=$peer_address cli peer lifecycle chaincode install ${CHAINCODE_NAME}.tar.gz
    
    print_color $GREEN "✅ Chaincode installed on $org peer"
}

# Function to get package ID
get_package_id() {
    local org=$1
    local peer_address=${ORGANIZATIONS[$org]}
    local org_msp=${ORG_MSPS[$org]}
    local org_domain=${ORG_DOMAINS[$org]}
    
    print_color $BLUE "🔍 Getting package ID for $org..."
    
    # Get package ID
    local package_id=$(docker exec -e CORE_PEER_TLS_ENABLED=true -e CORE_PEER_LOCALMSPID=$org_msp -e CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/$org_domain/peers/peer0.$org_domain/tls/ca.crt -e CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/$org_domain/users/Admin@$org_domain/msp -e CORE_PEER_ADDRESS=$peer_address cli peer lifecycle chaincode queryinstalled | jq -r ".installed_chaincodes[] | select(.label == \"${CHAINCODE_NAME}_${CHAINCODE_VERSION}\") | .package_id")
    
    echo $package_id
}

# Function to approve chaincode for organization
approve_chaincode() {
    local org=$1
    local package_id=$2
    local peer_address=${ORGANIZATIONS[$org]}
    local org_msp=${ORG_MSPS[$org]}
    local org_domain=${ORG_DOMAINS[$org]}
    
    print_color $BLUE "✅ Approving chaincode for $org..."
    
    # Approve chaincode
    docker exec -e CORE_PEER_TLS_ENABLED=true -e CORE_PEER_LOCALMSPID=$org_msp -e CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/$org_domain/peers/peer0.$org_domain/tls/ca.crt -e CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/$org_domain/users/Admin@$org_domain/msp -e CORE_PEER_ADDRESS=$peer_address cli peer lifecycle chaincode approveformyorg --channelID $CHANNEL_NAME --name $CHAINCODE_NAME --version $CHAINCODE_VERSION --package-id $package_id --sequence $SEQUENCE --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
    
    print_color $GREEN "✅ Chaincode approved by $org"
}

# Function to check approval status
check_approval_status() {
    local org=$1
    local peer_address=${ORGANIZATIONS[$org]}
    local org_msp=${ORG_MSPS[$org]}
    local org_domain=${ORG_DOMAINS[$org]}
    
    print_color $BLUE "🔍 Checking approval status for $org..."
    
    # Check approval status
    docker exec -e CORE_PEER_TLS_ENABLED=true -e CORE_PEER_LOCALMSPID=$org_msp -e CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/$org_domain/peers/peer0.$org_domain/tls/ca.crt -e CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/$org_domain/users/Admin@$org_domain/msp -e CORE_PEER_ADDRESS=$peer_address cli peer lifecycle chaincode queryapprovalstatus --channelID $CHANNEL_NAME --name $CHAINCODE_NAME --version $CHAINCODE_VERSION --sequence $SEQUENCE --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
}

# Function to commit chaincode
commit_chaincode() {
    local package_id=$1
    local peer_address=${ORGANIZATIONS["Ecol"]}
    local org_msp=${ORG_MSPS["Ecol"]}
    local org_domain=${ORG_DOMAINS["Ecol"]}
    
    print_color $BLUE "🔧 Committing chaincode to channel..."
    
    # Commit chaincode
    docker exec -e CORE_PEER_TLS_ENABLED=true -e CORE_PEER_LOCALMSPID=$org_msp -e CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/$org_domain/peers/peer0.$org_domain/tls/ca.crt -e CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/$org_domain/users/Admin@$org_domain/msp -e CORE_PEER_ADDRESS=$peer_address cli peer lifecycle chaincode commit --channelID $CHANNEL_NAME --name $CHAINCODE_NAME --version $CHAINCODE_VERSION --package-id $package_id --sequence $SEQUENCE --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem --peerAddresses peer0.ecol.example.com:7051,peer0.limkokwing.example.com:9051,peer0.botho.example.com:11051,peer0.nul.example.com:12051 --tlsRootCertFiles /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/ecol.example.com/peers/peer0.ecol.example.com/tls/ca.crt,/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/limkokwing.example.com/peers/peer0.limkokwing.example.com/tls/ca.crt,/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/botho.example.com/peers/peer0.botho.example.com/tls/ca.crt,/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/nul.example.com/peers/peer0.nul.example.com/tls/ca.crt
    
    print_color $GREEN "✅ Chaincode committed to channel"
}

# Function to initialize chaincode
init_chaincode() {
    local peer_address=${ORGANIZATIONS["Ecol"]}
    local org_msp=${ORG_MSPS["Ecol"]}
    local org_domain=${ORG_DOMAINS["Ecol"]}
    
    print_color $BLUE "🚀 Initializing chaincode..."
    
    # Initialize chaincode
    docker exec -e CORE_PEER_TLS_ENABLED=true -e CORE_PEER_LOCALMSPID=$org_msp -e CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/$org_domain/peers/peer0.$org_domain/tls/ca.crt -e CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/$org_domain/users/Admin@$org_domain/msp -e CORE_PEER_ADDRESS=$peer_address cli peer chaincode invoke -o orderer.example.com:7050 --ordererTLSHostnameOverride orderer.example.com --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem -C $CHANNEL_NAME -n $CHAINCODE_NAME --peerAddresses peer0.ecol.example.com:7051,peer0.limkokwing.example.com:9051,peer0.botho.example.com:11051,peer0.nul.example.com:12051 --tlsRootCertFiles /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/ecol.example.com/peers/peer0.ecol.example.com/tls/ca.crt,/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/limkokwing.example.com/peers/peer0.limkokwing.example.com/tls/ca.crt,/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/botho.example.com/peers/peer0.botho.example.com/tls/ca.crt,/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/nul.example.com/peers/peer0.nul.example.com/tls/ca.crt -c '{"Args":["InitLedger"]}'
    
    print_color $GREEN "✅ Chaincode initialized"
}

# Function to query chaincode
query_chaincode() {
    local org=$1
    local function_name=$2
    local args=$3
    local peer_address=${ORGANIZATIONS[$org]}
    local org_msp=${ORG_MSPS[$org]}
    local org_domain=${ORG_DOMAINS[$org]}
    
    print_color $BLUE "🔍 Querying chaincode from $org: $function_name"
    
    # Query chaincode
    docker exec -e CORE_PEER_TLS_ENABLED=true -e CORE_PEER_LOCALMSPID=$org_msp -e CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/$org_domain/peers/peer0.$org_domain/tls/ca.crt -e CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/$org_domain/users/Admin@$org_domain/msp -e CORE_PEER_ADDRESS=$peer_address cli peer chaincode query -C $CHANNEL_NAME -n $CHAINCODE_NAME -c '{"Args":["'$function_name'",$args]}' --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem
}

# Function to invoke chaincode
invoke_chaincode() {
    local org=$1
    local function_name=$2
    local args=$3
    local peer_address=${ORGANIZATIONS[$org]}
    local org_msp=${ORG_MSPS[$org]}
    local org_domain=${ORG_DOMAINS[$org]}
    
    print_color $BLUE "🔧 Invoking chaincode from $org: $function_name"
    
    # Invoke chaincode
    docker exec -e CORE_PEER_TLS_ENABLED=true -e CORE_PEER_LOCALMSPID=$org_msp -e CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/$org_domain/peers/peer0.$org_domain/tls/ca.crt -e CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/$org_domain/users/Admin@$org_domain/msp -e CORE_PEER_ADDRESS=$peer_address cli peer chaincode invoke -o orderer.example.com:7050 --ordererTLSHostnameOverride orderer.example.com --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/tlsca.example.com-cert.pem -C $CHANNEL_NAME -n $CHAINCODE_NAME --peerAddresses peer0.ecol.example.com:7051,peer0.limkokwing.example.com:9051,peer0.botho.example.com:11051,peer0.nul.example.com:12051 --tlsRootCertFiles /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/ecol.example.com/peers/peer0.ecol.example.com/tls/ca.crt,/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/limkokwing.example.com/peers/peer0.limkokwing.example.com/tls/ca.crt,/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/botho.example.com/peers/peer0.botho.example.com/tls/ca.crt,/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/nul.example.com/peers/peer0.nul.example.com/tls/ca.crt -c '{"Args":["'$function_name'",$args]}'
    
    print_color $GREEN "✅ Chaincode invoked successfully"
}

# Function to test chaincode functionality
test_chaincode() {
    print_color $BLUE "🧪 Testing chaincode functionality..."
    
    # Test 1: Query all certificates (should be empty initially)
    print_color $YELLOW "📋 Test 1: Query all certificates"
    query_chaincode "Ecol" "GetAllCertificates" ""
    
    # Test 2: Issue a certificate
    print_color $YELLOW "📋 Test 2: Issue a certificate"
    local cert_hash="CERT_$(date +%s)"
    local subjects='[{"name":"Mathematics","grade":"A","symbol":"*"},{"name":"English","grade":"B","symbol":"+"}]'
    invoke_chaincode "Ecol" "IssueCertificate" "\"$cert_hash\",\"STU001\",\"John\",\"Doe\",2023,\"$subjects\",5,\"2023-12-01\",\"Ecol University\",\"ECOL\""
    
    # Test 3: Query the certificate
    print_color $YELLOW "📋 Test 3: Query the certificate"
    query_chaincode "Ecol" "GetCertificate" "\"$cert_hash\""
    
    # Test 4: Verify the certificate
    print_color $YELLOW "📋 Test 4: Verify the certificate"
    invoke_chaincode "Limkokwing" "VerifyCertificate" "\"$cert_hash\",\"VER001\",\"Alice Smith\",\"LIMKOWING\",\"hash\",\"192.168.1.100\",\"Mozilla/5.0\""
    
    # Test 5: Query verification history
    print_color $YELLOW "📋 Test 5: Query verification history"
    query_chaincode "Limkokwing" "GetVerificationHistory" "\"$cert_hash\""
    
    print_color $GREEN "✅ Chaincode functionality tests completed"
}

# Function to upgrade chaincode
upgrade_chaincode() {
    local new_version=$1
    
    print_color $BLUE "🔄 Upgrading chaincode to version $new_version..."
    
    # Update version
    CHAINCODE_VERSION=$new_version
    SEQUENCE=$((SEQUENCE + 1))
    
    # Re-package and install for all organizations
    for org in "${!ORGANIZATIONS[@]}"; do
        package_chaincode $org
        install_chaincode $org
    done
    
    # Get package ID and approve for all organizations
    local package_id=$(get_package_id "Ecol")
    for org in "${!ORGANIZATIONS[@]}"; do
        approve_chaincode $org $package_id
    done
    
    # Commit upgrade
    commit_chaincode $package_id
    
    print_color $GREEN "✅ Chaincode upgraded to version $new_version"
}

# Function to cleanup
cleanup() {
    print_color $YELLOW "🧹 Cleaning up..."
    
    # Remove package files
    rm -f ${CHAINCODE_NAME}_*.tar.gz
    
    print_color $GREEN "✅ Cleanup completed"
}

# Function to display deployment status
display_deployment_status() {
    print_color $BLUE "📊 Chaincode Deployment Status:"
    print_color $BLUE "==============================="
    
    # Query committed chaincodes
    print_color $YELLOW "📋 Committed chaincodes:"
    docker exec -e CORE_PEER_TLS_ENABLED=true -e CORE_PEER_LOCALMSPID=EcolOrgMSP -e CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/ecol.example.com/peers/peer0.ecol.example.com/tls/ca.crt -e CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/ecol.example.com/users/Admin@ecol.example.com/msp -e CORE_PEER_ADDRESS=peer0.ecol.example.com:7051 cli peer lifecycle chaincode querycommitted --channelID $CHANNEL_NAME --name $CHAINCODE_NAME
    
    # Display chaincode info
    print_color $YELLOW "📋 Chaincode info:"
    docker exec -e CORE_PEER_TLS_ENABLED=true -e CORE_PEER_LOCALMSPID=EcolOrgMSP -e CORE_PEER_TLS_ROOTCERT_FILE=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/ecol.example.com/peers/peer0.ecol.example.com/tls/ca.crt -e CORE_PEER_MSPCONFIGPATH=/opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/ecol.example.com/users/Admin@ecol.example.com/msp -e CORE_PEER_ADDRESS=peer0.ecol.example.com:7051 cli peer chaincode list --instantiated -C $CHANNEL_NAME
    
    print_color $GREEN "✅ Chaincode is ready for use"
}

# Main execution
main() {
    local action=${1:-"deploy"}
    
    print_color $BLUE "🚀 Starting Hyperledger Fabric Chaincode Deployment"
    print_color $BLUE "==============================================="
    
    case $action in
        "deploy")
            check_prerequisites
            build_chaincode
            
            # Package and install for all organizations
            for org in "${!ORGANIZATIONS[@]}"; do
                package_chaincode $org
                install_chaincode $org
            done
            
            # Get package ID and approve for all organizations
            local package_id=$(get_package_id "Ecol")
            for org in "${!ORGANIZATIONS[@]}"; do
                approve_chaincode $org $package_id
                check_approval_status $org
            done
            
            # Commit chaincode
            commit_chaincode $package_id
            
            # Initialize chaincode
            init_chaincode
            
            # Test functionality
            test_chaincode
            
            # Display status
            display_deployment_status
            
            print_color $GREEN "🎉 Chaincode deployment completed successfully!"
            ;;
        "upgrade")
            local new_version=${2:-"2.0.0"}
            upgrade_chaincode $new_version
            display_deployment_status
            ;;
        "test")
            test_chaincode
            ;;
        "status")
            display_deployment_status
            ;;
        *)
            echo "Usage: $0 {deploy|upgrade [version]|test|status}"
            exit 1
            ;;
    esac
    
    print_color $BLUE "📋 Summary:"
    print_color $BLUE "   - Chaincode: $CHAINCODE_NAME"
    print_color $BLUE "   - Version: $CHAINCODE_VERSION"
    print_color $BLUE "   - Channel: $CHANNEL_NAME"
    print_color $BLUE "   - Organizations: ${!ORGANIZizations[@]}"
    print_color $BLUE "   - Sequence: $SEQUENCE"
    print_color $BLUE ""
    print_color $BLUE "🔗 Available operations:"
    print_color $BLUE "   - IssueCertificate: Issue new certificates"
    print_color $BLUE "   - VerifyCertificate: Verify certificate authenticity"
    print_color $BLUE "   - GetCertificate: Retrieve certificate details"
    print_color $BLUE "   - GetAllCertificates: List all certificates"
    print_color $BLUE "   - GetVerificationHistory: Get verification records"
    print_color $BLUE ""
    print_color $GREEN "✨ LGCSE Certificate Verification Chaincode is ready!"
}

# Handle script interruption
trap cleanup EXIT

# Run main function
main "$@"
