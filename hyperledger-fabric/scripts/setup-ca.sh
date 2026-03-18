#!/bin/bash

#
# Hyperledger Fabric CA Setup Script for LGCSE Certificate Verification
#
# This script sets up Certificate Authorities for all organizations
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

# Function to check if required tools are installed
check_prerequisites() {
    print_color $BLUE "🔍 Checking prerequisites..."
    
    # Check for Docker
    check_docker
    
    # Check for Docker Compose
    if ! command_exists docker-compose; then
        print_color $RED "❌ Docker Compose is not installed. Please install Docker Compose and try again."
        exit 1
    fi
    print_color $GREEN "✅ Docker Compose is installed"
    
    # Check for jq
    if ! command_exists jq; then
        print_color $YELLOW "⚠️  jq is not installed. Some features may not work properly."
    else
        print_color $GREEN "✅ jq is installed"
    fi
    
    # Check for curl
    if ! command_exists curl; then
        print_color $RED "❌ curl is not installed. Please install curl and try again."
        exit 1
    fi
    print_color $GREEN "✅ curl is installed"
}

# Function to create directory structure
create_directories() {
    print_color $BLUE "📁 Creating directory structure..."
    
    # Create base directories
    mkdir -p organizations/fabric-ca/ordererOrg
    mkdir -p organizations/fabric-ca/ecolOrg
    mkdir -p organizations/fabric-ca/limkokwingOrg
    mkdir -p organizations/fabric-ca/bothoOrg
    mkdir -p organizations/fabric-ca/nulOrg
    
    # Create organization directories
    mkdir -p organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp
    mkdir -p organizations/ordererOrganizations/example.com/orderers/orderer.example.com/tls
    mkdir -p organizations/peerOrganizations/ecol.example.com/peers/peer0.ecol.example.com/msp
    mkdir -p organizations/peerOrganizations/ecol.example.com/peers/peer0.ecol.example.com/tls
    mkdir -p organizations/peerOrganizations/ecol.example.com/users
    mkdir -p organizations/peerOrganizations/limkokwing.example.com/peers/peer0.limkokwing.example.com/msp
    mkdir -p organizations/peerOrganizations/limkokwing.example.com/peers/peer0.limkokwing.example.com/tls
    mkdir -p organizations/peerOrganizations/limkokwing.example.com/users
    mkdir -p organizations/peerOrganizations/botho.example.com/peers/peer0.botho.example.com/msp
    mkdir -p organizations/peerOrganizations/botho.example.com/peers/peer0.botho.example.com/tls
    mkdir -p organizations/peerOrganizations/botho.example.com/users
    mkdir -p organizations/peerOrganizations/nul.example.com/peers/peer0.nul.example.com/msp
    mkdir -p organizations/peerOrganizations/nul.example.com/peers/peer0.nul.example.com/tls
    mkdir -p organizations/peerOrganizations/nul.example.com/users
    
    print_color $GREEN "✅ Directory structure created"
}

# Function to start CA servers
start_ca_servers() {
    print_color $BLUE "🚀 Starting CA servers..."
    
    # Start all CA servers
    docker-compose -f docker-compose.yaml up -d ca.orderer.example.com ca.ecol.example.com ca.limkokwing.example.com ca.botho.example.com ca.nul.example.com
    
    # Wait for CAs to start
    print_color $YELLOW "⏳ Waiting for CA servers to start..."
    sleep 10
    
    # Check if CAs are running
    ca_servers=("ca.orderer.example.com:7054" "ca.ecol.example.com:8054" "ca.limkokwing.example.com:9054" "ca.botho.example.com:10054" "ca.nul.example.com:11054")
    
    for ca in "${ca_servers[@]}"; do
        if curl -s http://$ca/cainfo >/dev/null 2>&1; then
            print_color $GREEN "✅ CA server $ca is running"
        else
            print_color $RED "❌ CA server $ca failed to start"
            return 1
        fi
    done
    
    print_color $GREEN "✅ All CA servers are running"
}

# Function to register and enroll identities
register_identities() {
    print_color $BLUE "👥 Registering and enrolling identities..."
    
    # Function to register and enroll for an organization
    register_org() {
        local org_name=$1
        local org_domain=$2
        local ca_port=$3
        local org_msp=$4
        
        print_color $YELLOW "🔧 Setting up $org_name..."
        
        # Create CA admin client configuration
        cat > organizations/fabric-ca/${org_name}Org/fabric-ca-client-config.yaml <<EOF
url: https://ca.${org_domain}:${ca_port}
tls:
  certfiles: 
    - /home/ubuntu/fabric-ca/${org_name}Org/ca-cert.pem
  client:
    certfile: /home/ubuntu/fabric-ca/${org_name}Org/tls-cert.pem
    keyfile: /home/ubuntu/fabric-ca/${org_name}Org/tls-key.pem
    verify: false
    cacertfiles:
      - /home/ubuntu/fabric-ca/${org_name}Org/ca-cert.pem
csr:
  cn: ca-admin
  names:
    - C: LS
      ST: Maseru
      L: Maseru
      O: ${org_name}
      OU: CA
  hosts:
    - ca.${org_domain}
  ca:
    pathlen:
    pathlenzero:
    ext:
      ku:
        - digital signature
        - key cert sign
        - c rl sign
      extendedKeyUsage:
        - client auth
        - server auth
      keyUsage:
        - digital signature
        - key encipherment
        - key agreement
        - data encipherment
        - cert sign
        - crl sign
      basicConstraints:
        critical: true
        isCA: true
      subjectKeyIdentifier:
        issuer: true
id:
  name: ${org_name}Admin
  type: client
  affiliation: ""
  max_enrollments: 0
  attributes:
    - name: hf.Registrar.Roles
      value: "client,orderer,peer,user,admin"
    - name: hf.Registrar.DelegateRoles
      value: "client,orderer,peer,user,admin"
    - name: hf.Revoker
      value: true
    - name: hf.GenCRL
      value: true
    - name: hf.AffiliationMgr
      value: true
    - name: hf.IntermediateCA
      value: true
EOF
        
        # Enroll CA admin
        FABRIC_CA_CLIENT_HOME=organizations/fabric-ca/${org_name}Org fabric-ca-client enroll -u https://admin:adminpw@ca.${org_domain}:${ca_port} --caname ca-${org_name} --tls.certfiles /home/ubuntu/fabric-ca/${org_name}Org/ca-cert.pem
        
        # Register peer identity
        FABRIC_CA_CLIENT_HOME=organizations/fabric-ca/${org_name}Org fabric-ca-client register --caname ca-${org_name} --id.name peer0.${org_domain} --id.type peer --id.affiliation ${org_name} --id.maxenrollments 0 --id.attrs "hf.Revoker=true,hf.GenCRL=true,hf.Registrar.Roles=peer,hf.Registrar.DelegateRoles=peer" --tls.certfiles /home/ubuntu/fabric-ca/${org_name}Org/ca-cert.pem
        
        # Register admin user
        FABRIC_CA_CLIENT_HOME=organizations/fabric-ca/${org_name}Org fabric-ca-client register --caname ca-${org_name} --id.name Admin@${org_domain} --id.type admin --id.affiliation ${org_name} --id.maxenrollments 0 --id.attrs "hf.Revoker=true,hf.GenCRL=true,hf.Registrar.Roles=admin,hf.Registrar.DelegateRoles=admin" --tls.certfiles /home/ubuntu/fabric-ca/${org_name}Org/ca-cert.pem
        
        # Register user
        FABRIC_CA_CLIENT_HOME=organizations/fabric-ca/${org_name}Org fabric-ca-client register --caname ca-${org_name} --id.name User1@${org_domain} --id.type client --id.affiliation ${org_name} --id.maxenrollments 0 --id.attrs "hf.Revoker=true,hf.GenCRL=true" --tls.certfiles /home/ubuntu/fabric-ca/${org_name}Org/ca-cert.pem
        
        # Enroll peer identity
        mkdir -p organizations/peerOrganizations/${org_domain}/peers/peer0.${org_domain}/msp
        FABRIC_CA_CLIENT_HOME=organizations/fabric-ca/${org_name}Org fabric-ca-client enroll -u https://peer0.${org_domain}:peer0pw@ca.${org_domain}:${ca_port} --caname ca-${org_name} -M organizations/peerOrganizations/${org_domain}/peers/peer0.${org_domain}/msp --tls.certfiles /home/ubuntu/fabric-ca/${org_name}Org/ca-cert.pem
        
        # Enroll admin user
        mkdir -p organizations/peerOrganizations/${org_domain}/users/Admin@${org_domain}/msp
        FABRIC_CA_CLIENT_HOME=organizations/fabric-ca/${org_name}Org fabric-ca-client enroll -u https://Admin@${org_domain}:adminpw@ca.${org_domain}:${ca_port} --caname ca-${org_name} -M organizations/peerOrganizations/${org_domain}/users/Admin@${org_domain}/msp --tls.certfiles /home/ubuntu/fabric-ca/${org_name}Org/ca-cert.pem
        
        # Enroll user
        mkdir -p organizations/peerOrganizations/${org_domain}/users/User1@${org_domain}/msp
        FABRIC_CA_CLIENT_HOME=organizations/fabric-ca/${org_name}Org fabric-ca-client enroll -u https://User1@${org_domain}:user1pw@ca.${org_domain}:${ca_port} --caname ca-${org_name} -M organizations/peerOrganizations/${org_domain}/users/User1@${org_domain}/msp --tls.certfiles /home/ubuntu/fabric-ca/${org_name}Org/ca-cert.pem
        
        # Copy CA certificate
        cp organizations/fabric-ca/${org_name}Org/ca-cert.pem organizations/peerOrganizations/${org_domain}/peers/peer0.${org_domain}/msp/cacerts/
        cp organizations/fabric-ca/${org_name}Org/ca-cert.pem organizations/peerOrganizations/${org_domain}/users/Admin@${org_domain}/msp/cacerts/
        cp organizations/fabric-ca/${org_name}Org/ca-cert.pem organizations/peerOrganizations/${org_domain}/users/User1@${org_domain}/msp/cacerts/
        
        # Create MSP config
        cat > organizations/peerOrganizations/${org_domain}/peers/peer0.${org_domain}/msp/config.yaml <<EOF
NodeOUs:
  Client:
    Identifier: x509::/C=LS/ST=Maseru/L=Maseru/O=${org_name}/OU=client/CN=User1@${org_domain}
    OUIdentifier: client
    Administrators: true
  Peer:
    Identifier: x509::/C=LS/ST=Maseru/L=Maseru/O=${org_name}/OU=peer/CN=peer0.${org_domain}
    OUIdentifier: peer
    Administrators: true
  Admin:
    Identifier: x509::/C=LS/ST=Maseru/L=Maseru/O=${org_name}/OU=admin/CN=Admin@${org_domain}
    OUIdentifier: admin
    Administrators: true
  Orderer:
    Identifier: x509::/C=LS/ST=Maseru/L=Maseru/O=${org_name}/OU=orderer/CN=orderer.${org_domain}
    OUIdentifier: orderer
    Administrators: true
EOF
        
        print_color $GREEN "✅ $org_name setup completed"
    }
    
    # Register orderer organization
    register_org "orderer" "example.com" "7054" "OrdererMSP"
    
    # Register peer organizations
    register_org "ecol" "ecol.example.com" "8054" "EcolOrgMSP"
    register_org "limkokwing" "limkokwing.example.com" "9054" "LimkokwingOrgMSP"
    register_org "botho" "botho.example.com" "10054" "BothoOrgMSP"
    register_org "nul" "nul.example.com" "11054" "NulOrgMSP"
    
    print_color $GREEN "✅ All identities registered and enrolled"
}

# Function to generate TLS certificates
generate_tls_certs() {
    print_color $BLUE "🔐 Generating TLS certificates..."
    
    # Function to generate TLS for an organization
    generate_tls_org() {
        local org_name=$1
        local org_domain=$2
        local ca_port=$3
        
        print_color $YELLOW "🔧 Generating TLS for $org_name..."
        
        # Register TLS identities
        FABRIC_CA_CLIENT_HOME=organizations/fabric-ca/${org_name}Org fabric-ca-client register --caname ca-${org_name} --id.name peer0-${org_name}-tls --id.type peer --id.affiliation ${org_name} --id.maxenrollments 0 --id.attrs "hf.Revoker=true,hf.GenCRL=true" --tls.certfiles /home/ubuntu/fabric-ca/${org_name}Org/ca-cert.pem
        
        # Enroll TLS certificate
        mkdir -p organizations/peerOrganizations/${org_domain}/peers/peer0.${org_domain}/tls
        FABRIC_CA_CLIENT_HOME=organizations/fabric-ca/${org_name}Org fabric-ca-client enroll -u https://peer0-${org_name}-tls:tlspw@ca.${org_domain}:${ca_port} --caname ca-${org_name} -M organizations/peerOrganizations/${org_domain}/peers/peer0.${org_domain}/tls --enrollment.profile tls --csr.hosts peer0.${org_domain},localhost,127.0.0.1 --tls.certfiles /home/ubuntu/fabric-ca/${org_name}Org/ca-cert.pem
        
        # Copy TLS certificate and key
        cp organizations/peerOrganizations/${org_domain}/peers/peer0.${org_domain}/tls/tlscacerts/* organizations/peerOrganizations/${org_domain}/peers/peer0.${org_domain}/tls/ca.crt
        cp organizations/peerOrganizations/${org_domain}/peers/peer0.${org_domain}/tls/signcerts/* organizations/peerOrganizations/${org_domain}/peers/peer0.${org_domain}/tls/server.crt
        cp organizations/peerOrganizations/${org_domain}/peers/peer0.${org_domain}/tls/keystore/* organizations/peerOrganizations/${org_domain}/peers/peer0.${org_domain}/tls/server.key
        
        print_color $GREEN "✅ TLS certificates generated for $org_name"
    }
    
    # Generate TLS for all organizations
    generate_tls_org "ecol" "ecol.example.com" "8054"
    generate_tls_org "limkokwing" "limkokwing.example.com" "9054"
    generate_tls_org "botho" "botho.example.com" "10054"
    generate_tls_org "nul" "nul.example.com" "11054"
    
    print_color $GREEN "✅ All TLS certificates generated"
}

# Function to create MSP configurations
create_msp_configs() {
    print_color $BLUE "🔧 Creating MSP configurations..."
    
    # Function to create MSP for an organization
    create_msp_org() {
        local org_name=$1
        local org_domain=$2
        local org_msp=$3
        
        # Create admincerts directory
        mkdir -p organizations/peerOrganizations/${org_domain}/msp/admincerts
        cp organizations/peerOrganizations/${org_domain}/users/Admin@${org_domain}/msp/signcerts/* organizations/peerOrganizations/${org_domain}/msp/admincerts/
        
        # Create cacerts directory
        mkdir -p organizations/peerOrganizations/${org_domain}/msp/cacerts
        cp organizations/fabric-ca/${org_name}Org/ca-cert.pem organizations/peerOrganizations/${org_domain}/msp/cacerts/
        
        # Create config.yaml for NodeOUs
        cat > organizations/peerOrganizations/${org_domain}/msp/config.yaml <<EOF
NodeOUs:
  Client:
    Identifier: x509::/C=LS/ST=Maseru/L=Maseru/O=${org_name}/OU=client/CN=User1@${org_domain}
    OUIdentifier: client
    Administrators: true
  Peer:
    Identifier: x509::/C=LS/ST=Maseru/L=Maseru/O=${org_name}/OU=peer/CN=peer0.${org_domain}
    OUIdentifier: peer
    Administrators: true
  Admin:
    Identifier: x509::/C=LS/ST=Maseru/L=Maseru/O=${org_name}/OU=admin/CN=Admin@${org_domain}
    OUIdentifier: admin
    Administrators: true
  Orderer:
    Identifier: x509::/C=LS/ST=Maseru/L=Maseru/O=${org_name}/OU=orderer/CN=orderer.${org_domain}
    OUIdentifier: orderer
    Administrators: true
EOF
        
        print_color $GREEN "✅ MSP configuration created for $org_name"
    }
    
    # Create MSP for all organizations
    create_msp_org "ecol" "ecol.example.com" "EcolOrgMSP"
    create_msp_org "limkokwing" "limkokwing.example.com" "LimkokwingOrgMSP"
    create_msp_org "botho" "botho.example.com" "BothoOrgMSP"
    create_msp_org "nul" "nul.example.com" "NulOrgMSP"
    
    print_color $GREEN "✅ All MSP configurations created"
}

# Function to verify setup
verify_setup() {
    print_color $BLUE "🔍 Verifying CA setup..."
    
    # Check if all certificates are generated
    organizations=("ecol" "limkokwing" "botho" "nul")
    
    for org in "${organizations[@]}"; do
        domain="${org}.example.com"
        
        if [ -f "organizations/peerOrganizations/${domain}/peers/peer0.${domain}/msp/signcerts/cert.pem" ] && \
           [ -f "organizations/peerOrganizations/${domain}/peers/peer0.${domain}/tls/server.crt" ] && \
           [ -f "organizations/peerOrganizations/${domain}/users/Admin@${domain}/msp/signcerts/cert.pem" ]; then
            print_color $GREEN "✅ $org certificates verified"
        else
            print_color $RED "❌ $org certificates missing"
            return 1
        fi
    done
    
    print_color $GREEN "✅ CA setup verification completed"
}

# Function to cleanup
cleanup() {
    print_color $YELLOW "🧹 Cleaning up..."
    
    # Stop CA servers
    docker-compose -f docker-compose.yaml down
    
    print_color $GREEN "✅ Cleanup completed"
}

# Main execution
main() {
    print_color $BLUE "🚀 Starting Hyperledger Fabric CA Setup for LGCSE"
    print_color $BLUE "=================================================="
    
    # Check prerequisites
    check_prerequisites
    
    # Create directory structure
    create_directories
    
    # Start CA servers
    start_ca_servers
    
    # Register and enroll identities
    register_identities
    
    # Generate TLS certificates
    generate_tls_certs
    
    # Create MSP configurations
    create_msp_configs
    
    # Verify setup
    verify_setup
    
    print_color $GREEN "🎉 Hyperledger Fabric CA setup completed successfully!"
    print_color $BLUE "📋 Summary:"
    print_color $BLUE "   - 5 Certificate Authorities configured"
    print_color $BLUE "   - 4 Peer organizations setup"
    print_color $BLUE "   - 1 Orderer organization setup"
    print_color $BLUE "   - TLS certificates generated"
    print_color $BLUE "   - MSP configurations created"
    print_color $BLUE "   - All identities enrolled"
    print_color $BLUE ""
    print_color $BLUE "🔗 Next steps:"
    print_color $BLUE "   1. Start the network: docker-compose -f docker-compose.yaml up -d"
    print_color $BLUE "   2. Create channels and join peers"
    print_color $BLUE "   3. Deploy chaincode"
    print_color $BLUE ""
    print_color $GREEN "✨ Ready for LGCSE Certificate Verification System!"
}

# Handle script interruption
trap cleanup EXIT

# Run main function
main "$@"
