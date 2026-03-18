#!/bin/bash

# LGCSE Institution Nodes Monitoring Dashboard
# This script monitors the status of all institution nodes

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}LGCSE Institution Nodes Status${NC}"
echo -e "${BLUE}==========================================${NC}"
echo ""

# Institution configuration
declare -A INSTITUTIONS=(
    ["ECOL"]="Ecol University|Issuer|peer0.ecol.example.com|7051|8054|ca_ecol"
    ["LIMKOWING"]="Limkokwing University|Verifier|peer0.limkokwing.example.com|9051|9054|ca_limkokwing"
    ["BOTHO"]="Botho University|Verifier|peer0.botho.example.com|11051|10054|ca_botho"
    ["NUL"]="National University of Lesotho|Verifier|peer0.nul.example.com|12051|11054|ca_nul"
)

# Check if Docker is running
if ! command -v docker > /dev/null; then
    echo -e "${RED}✗ Docker is not installed or not in PATH${NC}"
    exit 1
fi

if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}✗ Docker is not running${NC}"
    echo -e "${YELLOW}Please start Docker service:${NC}"
    echo "  sudo systemctl start docker"
    echo "  sudo systemctl enable docker"
    exit 1
fi

echo -e "${GREEN}✓ Docker is running${NC}"
echo ""

# Check all institution nodes
for inst_code in "${!INSTITUTIONS[@]}"; do
    inst_info="${INSTITUTIONS[$inst_code]}"
    IFS='|' read -r name role peer_host peer_port ca_port container_name <<< "$inst_info"
    
    echo -e "${CYAN}=== $name ===${NC}"
    echo -e "${YELLOW}Role: $role${NC}"
    
    # Check CA
    echo -n "CA ($container_name): "
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$container_name"; then
        ca_status=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep "$container_name" | awk '{print $2}')
        echo -e "${GREEN}✓ Running ($ca_status)${NC}"
    else
        echo -e "${RED}✗ Stopped${NC}"
        # Show how to start
        echo -e "${YELLOW}  Start with: docker-compose up -d $container_name${NC}"
    fi
    
    # Check Peer
    peer_container="peer0.${inst_code,,}.example.com"
    echo -n "Peer ($peer_container): "
    if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$peer_container"; then
        peer_status=$(docker ps --format "table {{.Names}}\t{{.Status}}" | grep "$peer_container" | awk '{print $2}')
        echo -e "${GREEN}✓ Running ($peer_status)${NC}"
    else
        echo -e "${RED}✗ Stopped${NC}"
        # Show how to start
        echo -e "${YELLOW}  Start with: docker-compose up -d $peer_container${NC}"
    fi
    
    # Check ports
    echo -n "Ports: "
    peer_open=false
    ca_open=false
    
    if ss -tuln 2>/dev/null | grep -q ":$peer_port"; then
        echo -n "Peer($peer_port) ${GREEN}✓${NC} "
        peer_open=true
    else
        echo -n "Peer($peer_port) ${RED}✗${NC} "
    fi
    
    if ss -tuln 2>/dev/null | grep -q ":$ca_port"; then
        echo -n "CA($ca_port) ${GREEN}✓${NC}"
        ca_open=true
    else
        echo -n "CA($ca_port) ${RED}✗${NC}"
    fi
    
    if ! $peer_open || ! $ca_open; then
        echo ""
        echo -e "${YELLOW}  Note: Ports may be bound to Docker containers${NC}"
    fi
    
    echo ""
done

echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}Network Summary${NC}"
echo -e "${BLUE}==========================================${NC}"

# Check orderer
echo -n "Orderer: "
orderer_count=$(docker ps --format "{{.Names}}" | grep -c "orderer" || echo "0")
if [ "$orderer_count" -gt 0 ]; then
    echo -e "${GREEN}✓ $orderer_count running${NC}"
else
    echo -e "${RED}✗ Not running${NC}"
fi

# Check CAs
echo -n "Total CAs: "
ca_count=$(docker ps --format "{{.Names}}" | grep -c "^ca_" || echo "0")
if [ "$ca_count" -gt 0 ]; then
    echo -e "${GREEN}✓ $ca_count running${NC}"
else
    echo -e "${RED}✗ None running${NC}"
fi

# Check Peers
echo -n "Total Peers: "
peer_count=$(docker ps --format "{{.Names}}" | grep -c "^peer0" || echo "0")
if [ "$peer_count" -gt 0 ]; then
    echo -e "${GREEN}✓ $peer_count running${NC}"
else
    echo -e "${RED}✗ None running${NC}"
fi

# Check Chaincode
echo -n "Chaincode: "
chaincode_count=$(docker ps --format "{{.Names}}" | grep -c "dev-peer" || echo "0")
if [ "$chaincode_count" -gt 0 ]; then
    echo -e "${GREEN}✓ $chaincode_count running${NC}"
else
    echo -e "${YELLOW}⚠ None deployed${NC}"
fi

echo ""

# Docker Compose status
echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}Docker Compose Status${NC}"
echo -e "${BLUE}==========================================${NC}"

# Find docker-compose file
fabric_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/../hyperledger-fabric"
if [ -f "$fabric_dir/docker-compose.yaml" ]; then
    echo -e "${CYAN}Docker Compose services:${NC}"
    cd "$fabric_dir"
    docker-compose ps --format "table {{.Name}}\t{{.State}}\t{{.Ports}}"
else
    echo -e "${YELLOW}⚠ Docker Compose file not found at $fabric_dir/docker-compose.yaml${NC}"
    echo -e "${YELLOW}  Make sure you're in the correct directory${NC}"
fi

echo ""
echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}Management Commands${NC}"
echo -e "${BLUE}==========================================${NC}"

echo -e "${CYAN}Start all services:${NC}"
echo "  cd hyperledger-fabric && docker-compose up -d"
echo ""
echo -e "${CYAN}Start individual institution:${NC}"
echo "  cd hyperledger-fabric"
echo "  docker-compose up -d ca_ecol peer0.ecol.example.com"
echo "  docker-compose up -d ca_limkokwing peer0.limkokwing.example.com"
echo "  docker-compose up -d ca_botho peer0.botho.example.com"
echo "  docker-compose up -d ca_nul peer0.nul.example.com"
echo ""
echo -e "${CYAN}View logs:${NC}"
echo "  cd hyperledger-fabric"
echo "  docker-compose logs -f ca_ecol"
echo "  docker-compose logs -f peer0.ecol.example.com"
echo ""
echo -e "${CYAN}Stop all services:${NC}"
echo "  cd hyperledger-fabric && docker-compose down"
echo ""
echo -e "${CYAN}Restart services:${NC}"
echo "  cd hyperledger-fabric && docker-compose restart"
echo ""
echo -e "${CYAN}Clean and rebuild:${NC}"
echo "  cd hyperledger-fabric && docker-compose down -v && docker-compose up -d"

echo ""
echo -e "${BLUE}==========================================${NC}"
echo -e "${BLUE}Port Summary${NC}"
echo -e "${BLUE}==========================================${NC}"

echo -e "${CYAN}Network Ports:${NC}"
echo "• Orderer: 7050"
echo "• Orderer CA: 7054"
echo "• Ecol Peer: 7051, CA: 8054"
echo "• Limkokwing Peer: 9051, CA: 9054"
echo "• Botho Peer: 11051, CA: 10054"
echo "• NUL Peer: 12051, CA: 11054"

echo ""
echo -e "${GREEN}Last updated: $(date)${NC}"
