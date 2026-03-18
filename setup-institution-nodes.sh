#!/bin/bash

# LGCSE Certificate Verification System - Institution Nodes Setup
# This script sets up and starts nodes for each participating institution

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FABRIC_DIR="$PROJECT_ROOT/hyperledger-fabric"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  LGCSE Institution Nodes Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Institution configuration
declare -A INSTITUTIONS=(
    ["ECOL"]="Ecol University|Issuer|peer0.ecol.example.com|7051|8054|ca_ecol"
    ["LIMKOWING"]="Limkokwing University|Verifier|peer0.limkokwing.example.com|9051|9054|ca_limkokwing"
    ["BOTHO"]="Botho University|Verifier|peer0.botho.example.com|11051|10054|ca_botho"
    ["NUL"]="National University of Lesotho|Verifier|peer0.nul.example.com|12051|11054|ca_nul"
)

echo -e "${CYAN}🏛️  Participating Institutions:${NC}"
echo ""
for key in "${!INSTITUTIONS[@]}"; do
    IFS='|' read -r name role peer_host peer_port ca_port container_name <<< "${INSTITUTIONS[$key]}"
    echo -e "${YELLOW}• $name${NC}"
    echo "  Role: $role"
    echo "  Peer: $peer_host:$peer_port"
    echo "  CA Port: $ca_port"
    echo "  Container: $container_name"
    echo ""
done

# Function to check if Fabric network is running
check_fabric_network() {
    if [ -f "$FABRIC_DIR/docker-compose.yaml" ]; then
        cd "$FABRIC_DIR"
        if docker-compose ps | grep -q "Up"; then
            return 0
        fi
    fi
    return 1
}

# Function to start institution node
start_institution_node() {
    local inst_code="$1"
    local inst_info="${INSTITUTIONS[$inst_code]}"
    
    IFS='|' read -r name role peer_host peer_port ca_port container_name <<< "$inst_info"
    
    echo -e "${BLUE}🚀 Starting node for $name...${NC}"
    
    cd "$FABRIC_DIR"
    
    # Check if institution's CA is running
    if ! docker ps | grep -q "$container_name"; then
        echo -e "${YELLOW}⚠ CA for $name is not running. Starting CA first...${NC}"
        docker-compose up -d "$container_name"
        sleep 3
    fi
    
    # Check if institution's peer is running
    local peer_container="peer0.${inst_code,,}.example.com"
    if ! docker ps | grep -q "$peer_container"; then
        echo -e "${YELLOW}⚠ Peer for $name is not running. Starting peer...${NC}"
        docker-compose up -d "$peer_container"
        sleep 3
    fi
    
    echo -e "${GREEN}✓ $name node is running${NC}"
    echo "  Peer: $peer_host:$peer_port"
    echo "  CA: localhost:$ca_port"
    echo ""
}

# Function to setup institution CLI
setup_institution_cli() {
    local inst_code="$1"
    local inst_info="${INSTITUTIONS[$inst_code]}"
    
    IFS='|' read -r name role peer_host peer_port ca_port container_name <<< "$inst_info"
    
    echo -e "${BLUE}🔧 Setting up CLI for $name...${NC}"
    
    cd "$FABRIC_DIR"
    
    # Create institution-specific CLI environment
    local cli_dir="$FABRIC_DIR/cli-${inst_code,,}"
    mkdir -p "$cli_dir"
    
    # Copy connection profiles and scripts
    cp -r "$FABRIC_DIR/config" "$cli_dir/"
    cp -r "$FABRIC_DIR/organizations" "$cli_dir/"
    
    # Create institution-specific scripts
    cat > "$cli_dir/institution-commands.sh" << EOF
#!/bin/bash

# $name - Institution CLI Commands
# Peer: $peer_host:$peer_port
# Role: $role

export FABRIC_CFG_PATH=\$PWD/config
export CORE_PEER_TLS_ENABLED=true
export CORE_PEER_LOCALMSPID="${inst_code}OrgMSP"
export CORE_PEER_TLS_ROOTCERT_FILE=\$PWD/organizations/peerOrganizations/${inst_code,,}.example.com/peers/peer0.${inst_code,,}.example.com/tls/ca.crt
export CORE_PEER_MSPCONFIGPATH=\$PWD/organizations/peerOrganizations/${inst_code,,}.example.com/users/Admin@${inst_code,,}.example.com/msp
export CORE_PEER_ADDRESS="$peer_host"

echo "=== $name CLI Environment ==="
echo "Peer: \$CORE_PEER_ADDRESS"
echo "MSP ID: \$CORE_PEER_LOCALMSPID"
echo "Role: $role"
echo ""

# Common commands
echo "Available commands:"
echo "1. Query channel: peer channel list"
echo "2. Query installed chaincodes: peer lifecycle chaincode queryinstalled"
echo "3. Query certificates: peer chaincode query -C lgcse-channel -n certificate-chaincode -c '{\"Args\":[\"GetAllCertificates\"]}'"
echo "4. Issue certificate (ECOL only): peer chaincode invoke -C lgcse-channel -n certificate-chaincode -c '{\"Args\":[\"IssueCertificate\",\"CERT_001\",\"STU001\",\"John\",\"Doe\",2023,\"[{\\\"name\\\":\\\"Mathematics\\\",\\\"grade\\\":\\\"A\\\",\\\"symbol\\\":\\\"*\\\"}]\",\"5\",\"2023-12-01\",\"$name\",\"$inst_code\",\\\"\\\"]}' --peerAddresses $peer_host --tlsRootCertFiles \$CORE_PEER_TLS_ROOTCERT_FILE"
echo "5. Verify certificate: peer chaincode invoke -C lgcse-channel -n certificate-chaincode -c '{\"Args\":[\"VerifyCertificate\",\"CERT_001\",\"VER001\",\"Alice Smith\",\"VERIFIER\",\"hash\",\"192.168.1.100\",\"Mozilla/5.0\",\\\"\\\"]}' --peerAddresses $peer_host --tlsRootCertFiles \$CORE_PEER_TLS_ROOTCERT_FILE"
EOF
    
    chmod +x "$cli_dir/institution-commands.sh"
    
    echo -e "${GREEN}✓ CLI setup complete for $name${NC}"
    echo "  CLI directory: $cli_dir"
    echo "  Commands file: $cli_dir/institution-commands.sh"
    echo ""
}

# Function to generate institution enrollment scripts
generate_enrollment_scripts() {
    local inst_code="$1"
    local inst_info="${INSTITUTIONS[$inst_code]}"
    
    IFS='|' read -r name role peer_host peer_port ca_port container_name <<< "$inst_info"
    
    echo -e "${BLUE}📝 Generating enrollment scripts for $name...${NC}"
    
    local enrollment_dir="$FABRIC_DIR/enrollment-${inst_code,,}"
    mkdir -p "$enrollment_dir"
    
    # Create enrollment script
    cat > "$enrollment_dir/enroll-admin.sh" << EOF
#!/bin/bash

# $name - Admin Enrollment Script

cd "$FABRIC_DIR"

# Set environment variables
export FABRIC_CA_CLIENT_HOME=\$PWD/organizations/fabric-ca/${inst_code,,}Org
export FABRIC_CA_CLIENT_TLS_CERTFILES=\$FABRIC_CA_CLIENT_HOME/tls-cert.pem

# Enroll admin
echo "Enrolling admin for $name..."
fabric-ca-client enroll -u https://admin:adminpw@localhost:$ca_port --caname ca-${inst_code,,} --tls.certfiles \$FABRIC_CA_CLIENT_TLS_CERTFILES -M \$FABRIC_CA_CLIENT_HOME/msp

echo "Admin enrollment complete for $name"
echo "MSP directory: \$FABRIC_CA_CLIENT_HOME/msp"
EOF
    
    chmod +x "$enrollment_dir/enroll-admin.sh"
    
    # Create user registration script
    cat > "$enrollment_dir/register-user.sh" << EOF
#!/bin/bash

# $name - User Registration Script

USERNAME=\$1
if [ -z "\$USERNAME" ]; then
    echo "Usage: \$0 <username>"
    exit 1
fi

cd "$FABRIC_DIR"

# Register and enroll user
echo "Registering user: \$USERNAME for $name"
fabric-ca-client register --caname ca-${inst_code,,} --id.name \$USERNAME --id.type user --id.affiliation ${inst_code,,}.dept1 --tls.certfiles \$PWD/organizations/fabric-ca/${inst_code,,}Org/tls-cert.pem

echo "Enrolling user: \$USERNAME"
fabric-ca-client enroll -u https://\$USERNAME:\$USERNAME@localhost:$ca_port --caname ca-${inst_code,,} --tls.certfiles \$PWD/organizations/fabric-ca/${inst_code,,}Org/tls-cert.pem -M \$PWD/organizations/peerOrganizations/${inst_code,,}.example.com/users/\$USERNAME@${inst_code,,}.example.com/msp

echo "User \$USERNAME registered and enrolled for $name"
echo "MSP directory: \$PWD/organizations/peerOrganizations/${inst_code,,}.example.com/users/\$USERNAME@${inst_code,,}.example.com/msp"
EOF
    
    chmod +x "$enrollment_dir/register-user.sh"
    
    echo -e "${GREEN}✓ Enrollment scripts generated for $name${NC}"
    echo "  Directory: $enrollment_dir"
    echo "  Admin enrollment: $enrollment_dir/enroll-admin.sh"
    echo "  User registration: $enrollment_dir/register-user.sh"
    echo ""
}

# Function to create institution monitoring dashboard
create_monitoring_dashboard() {
    echo -e "${BLUE}📊 Creating institution monitoring dashboard...${NC}"
    
    local monitoring_dir="$FABRIC_DIR/monitoring"
    mkdir -p "$monitoring_dir"
    
    cat > "$monitoring-dashboard.sh" << 'EOF'
#!/bin/bash

# LGCSE Institution Nodes Monitoring Dashboard

echo "=========================================="
echo "LGCSE Institution Nodes Status"
echo "=========================================="
echo ""

# Check all institution nodes
institutions=("ECOL" "LIMKOWING" "BOTHO" "NUL")

for inst in "${institutions[@]}"; do
    echo "=== $inst ==="
    
    # Check CA
    ca_container="ca_${inst,,}"
    if docker ps | grep -q "$ca_container"; then
        echo "✓ CA: Running"
    else
        echo "✗ CA: Stopped"
    fi
    
    # Check Peer
    peer_container="peer0.${inst,,}.example.com"
    if docker ps | grep -q "$peer_container"; then
        echo "✓ Peer: Running"
    else
        echo "✗ Peer: Stopped"
    fi
    
    # Check ports
    case $inst in
        "ECOL")
            ports=("7051" "8054")
            ;;
        "LIMKOWING")
            ports=("9051" "9054")
            ;;
        "BOTHO")
            ports=("11051" "10054")
            ;;
        "NUL")
            ports=("12051" "11054")
            ;;
    esac
    
    for port in "${ports[@]}"; do
        if ss -tuln | grep -q ":$port"; then
            echo "✓ Port $port: Open"
        else
            echo "✗ Port $port: Closed"
        fi
    done
    
    echo ""
done

echo "=========================================="
echo "Network Summary"
echo "=========================================="
echo "Orderer: $(docker ps | grep orderer.example.com | wc -l) running"
echo "Total CAs: $(docker ps | grep ca_ | wc -l) running"
echo "Total Peers: $(docker ps | grep peer0 | wc -l) running"
echo "Chaincode: $(docker ps | grep dev-peer | wc -l) running"
echo ""
EOF
    
    chmod +x "$monitoring-dashboard.sh"
    mv "$monitoring-dashboard.sh" "$monitoring_dir/"
    
    echo -e "${GREEN}✓ Monitoring dashboard created${NC}"
    echo "  Dashboard: $monitoring_dir/monitoring-dashboard.sh"
    echo ""
}

# Main execution
echo -e "${YELLOW}🔍 Checking Hyperledger Fabric network...${NC}"

if ! check_fabric_network; then
    echo -e "${RED}✗ Hyperledger Fabric network is not running${NC}"
    echo -e "${YELLOW}Please start the Fabric network first:${NC}"
    echo "  cd $FABRIC_DIR"
    echo "  ./scripts/deploy-menu.sh"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ Hyperledger Fabric network is running${NC}"
echo ""

# Setup all institution nodes
echo -e "${YELLOW}🏛️ Setting up institution nodes...${NC}"
echo ""

for inst_code in "${!INSTITUTIONS[@]}"; do
    start_institution_node "$inst_code"
    setup_institution_cli "$inst_code"
    generate_enrollment_scripts "$inst_code"
done

# Create monitoring dashboard
create_monitoring_dashboard

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Institution Nodes Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${CYAN}🏛️ Institution Nodes Summary:${NC}"
echo ""

for inst_code in "${!INSTITUTIONS[@]}"; do
    inst_info="${INSTITUTIONS[$inst_code]}"
    IFS='|' read -r name role peer_host peer_port ca_port container_name <<< "$inst_info"
    
    echo -e "${YELLOW}• $name${NC}"
    echo "  Role: $role"
    echo "  Peer: $peer_host:$peer_port"
    echo "  CA: localhost:$ca_port"
    echo "  CLI: $FABRIC_DIR/cli-${inst_code,,}/institution-commands.sh"
    echo "  Enrollment: $FABRIC_DIR/enrollment-${inst_code,,}/"
    echo ""
done

echo -e "${CYAN}🔧 Management Commands:${NC}"
echo "• Monitor all nodes: $FABRIC_DIR/monitoring/monitoring-dashboard.sh"
echo "• Start individual node: docker-compose up -d <container_name>"
echo "• Stop individual node: docker-compose stop <container_name>"
echo "• View logs: docker-compose logs -f <container_name>"
echo ""
echo -e "${CYAN}📚 Usage Examples:${NC}"
echo "# ECOL University CLI"
echo "cd $FABRIC_DIR/cli-ecol && ./institution-commands.sh"
echo ""
echo "# Enroll admin user"
echo "cd $FABRIC_DIR/enrollment-ecol && ./enroll-admin.sh"
echo ""
echo "# Register new user"
echo "cd $FABRIC_DIR/enrollment-ecol && ./register-user.sh john_doe"
echo ""
echo -e "${CYAN}🌐 Access Information:${NC}"
echo "• Ecol University: http://localhost:7051 (peer), http://localhost:8054 (CA)"
echo "• Limkokwing University: http://localhost:9051 (peer), http://localhost:9054 (CA)"
echo "• Botho University: http://localhost:11051 (peer), http://localhost:10054 (CA)"
echo "• NUL University: http://localhost:12051 (peer), http://localhost:11054 (CA)"
echo ""
echo -e "${GREEN}✨ All institution nodes are ready for certificate operations!${NC}"
