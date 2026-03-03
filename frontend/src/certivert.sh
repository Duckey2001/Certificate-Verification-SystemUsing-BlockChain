#!/bin/bash

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${PURPLE}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║                                                      ║"
echo "║      🚀  C E R T I V E R T  S Y S T E M              ║"
echo "║      Certificate Verification with Blockchain        ║"
echo "║                                                      ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "\n${CYAN}[1/5]${NC} ${YELLOW}Checking System Dependencies...${NC}"

# Check PostgreSQL
if sudo systemctl is-active --quiet postgresql; then
    echo -e "   ${GREEN}✓ PostgreSQL is running${NC}"
else
    echo -e "   ${RED}✗ PostgreSQL is not running${NC}"
    echo -e "   ${YELLOW}Starting PostgreSQL...${NC}"
    sudo systemctl start postgresql
    sleep 2
fi

echo -e "\n${CYAN}[2/5]${NC} ${YELLOW}Starting Blockchain (Ganache)...${NC}"
cd ~/certivert-blockchain
gnome-terminal --title="⛓ CERTIVERT BLOCKCHAIN" \
               --geometry=80x24+0+0 \
               -- bash -c "
    echo '╔══════════════════════════════════════════════════════╗';
    echo '║               BLOCKCHAIN NODE                        ║';
    echo '║         Local Ethereum Network (Ganache)             ║';
    echo '║         http://localhost:8545                        ║';
    echo '╚══════════════════════════════════════════════════════╝';
    echo '';
    npx ganache --server.port 8545 --database.dbPath ./ganache_data --wallet.deterministic true;
    exec bash"

sleep 5

echo -e "\n${CYAN}[3/5]${NC} ${YELLOW}Deploying Smart Contract...${NC}"
echo -n "   "
npx truffle migrate --network development --quiet 2>/dev/null
CONTRACT_ADDR=$(npx truffle networks --network development 2>/dev/null | grep CertificateStore | awk '{print $4}')
echo -e "   ${GREEN}✓ Contract deployed: ${CYAN}$CONTRACT_ADDR${NC}"

echo -e "\n${CYAN}[4/5]${NC} ${YELLOW}Starting Backend Server...${NC}"
cd ~/certivert-backend
gnome-terminal --title="🔧 CERTIVERT BACKEND" \
               --geometry=80x24+800+0 \
               -- bash -c "
    echo '╔══════════════════════════════════════════════════════╗';
    echo '║               BACKEND API SERVER                     ║';
    echo '║         Node.js + Express + PostgreSQL               ║';
    echo '║         http://localhost:5000                        ║';
    echo '╚══════════════════════════════════════════════════════╝';
    echo '';
    npm start;
    exec bash"

sleep 3

echo -e "\n${CYAN}[5/5]${NC} ${YELLOW}Starting Frontend Application...${NC}"
cd ~/Documents/Certivert\ project/frontend
gnome-terminal --title="🌐 CERTIVERT FRONTEND" \
               --geometry=80x24+0+400 \
               -- bash -c "
    echo '╔══════════════════════════════════════════════════════╗';
    echo '║               REACT FRONTEND                         ║';
    echo '║         Vite + React + Tailwind CSS                  ║';
    echo '║         http://localhost:3000                        ║';
    echo '╚══════════════════════════════════════════════════════╝';
    echo '';
    npm start;
    exec bash"

echo -e "\n${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✅ CERTIVERT SYSTEM STARTED SUCCESSFULLY!${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}🌐 ${NC}Frontend:   ${GREEN}http://localhost:3000${NC}"
echo -e "${YELLOW}🔧 ${NC}Backend:    ${GREEN}http://localhost:5000${NC}"
echo -e "${YELLOW}⛓ ${NC}Blockchain: ${GREEN}http://localhost:8545${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}📊 ${NC}Database:   ${GREEN}PostgreSQL (certivert_issuer, certivert_verifier)${NC}"
echo -e "${YELLOW}📜 ${NC}Contract:   ${CYAN}$CONTRACT_ADDR${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}🔑 ${NC}Demo Credentials:"
echo -e "   ${GREEN}Issuer:   ${NC}admin@ecol.org.ls / password123"
echo -e "   ${GREEN}Verifier: ${NC}verifier@nul.ls / password123"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}📁 ${NC}Project Locations:"
echo -e "   ${GREEN}Frontend:  ${NC}~/Documents/Certivert project/frontend/"
echo -e "   ${GREEN}Backend:   ${NC}~/certivert-backend/"
echo -e "   ${GREEN}Blockchain:${NC}~/certivert-blockchain/"
echo -e "${BLUE}════════════════════════════════════════════════════════${NC}"

# Quick test
echo -e "\n${YELLOW}Running quick system test...${NC}"
sleep 2
if curl -s http://localhost:5000 > /dev/null; then
    echo -e "   ${GREEN}✓ Backend is responding${NC}"
else
    echo -e "   ${RED}✗ Backend not responding${NC}"
fi
