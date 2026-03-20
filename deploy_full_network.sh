#!/bin/bash
# Full Blockchain Network Deployment (All Nodes)

echo "🚀 Starting full blockchain network deployment..."

cd /home/duckey/lgcse-project/hyperledger-fabric

# Start all services
echo "📦 Starting all Docker containers..."
docker-compose up -d

# Wait for containers to be ready
echo "⏳ Waiting for containers to initialize..."
sleep 45

# Create channel
echo "📡 Creating lgcse-channel..."
docker exec cli peer channel create -c lgcse-channel -f ./config/channel.tx --outputBlock ./config/genesis.block -o orderer.example.com:7050 --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/orderer.example.com-cert.pem

# Join all peers to channel
echo "🔗 Joining all peers to channel..."
docker exec -e CORE_PEER_LOCALMSPID=EcolOrgMSP peer0.ecol.example.com peer channel join -b ./config/genesis.block --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/ecol.example.com/peers/peer0.ecol.example.com/msp/tlscacerts/ca.ecol.example.com-cert.pem
docker exec -e CORE_PEER_LOCALMSPID=LimkokwingOrgMSP peer0.limkokwing.example.com peer channel join -b ./config/genesis.block --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/limkokwing.example.com/peers/peer0.limkokwing.example.com/msp/tlscacerts/ca.limkokwing.example.com-cert.pem
docker exec -e CORE_PEER_LOCALMSPID=BothoOrgMSP peer0.botho.example.com peer channel join -b ./config/genesis.block --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/botho.example.com/peers/peer0.botho.example.com/msp/tlscacerts/ca.botho.example.com-cert.pem

# Install chaincode on all peers
echo "🔧 Installing chaincode on all peers..."
docker exec -e CORE_PEER_LOCALMSPID=EcolOrgMSP peer0.ecol.example.com peer lifecycle chaincode install /opt/gopath/src/github.com/chaincode/certificate.tar.gz --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/ecol.example.com/peers/peer0.ecol.example.com/msp/tlscacerts/ca.ecol.example.com-cert.pem
docker exec -e CORE_PEER_LOCALMSPID=LimkokwingOrgMSP peer0.limkokwing.example.com peer lifecycle chaincode install /opt/gopath/src/github.com/chaincode/certificate.tar.gz --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/limkokwing.example.com/peers/peer0.limkokwing.example.com/msp/tlscacerts/ca.limkokwing.example.com-cert.pem
docker exec -e CORE_PEER_LOCALMSPID=BothoOrgMSP peer0.botho.example.com peer lifecycle chaincode install /opt/gopath/src/github.com/chaincode/certificate.tar.gz --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/botho.example.com/peers/peer0.botho.example.com/msp/tlscacerts/ca.botho.example.com-cert.pem

# Instantiate chaincode
echo "⚡ Instantiating chaincode..."
docker exec -e CORE_PEER_LOCALMSPID=EcolOrgMSP peer0.ecol.example.com peer lifecycle chaincode approveformyorg --channelID lgcse-channel --name certificate_chaincode --version 1.0.0 --sequence 1 --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/ecol.example.com/peers/peer0.ecol.example.com/msp/tlscacerts/ca.ecol.example.com-cert.pem
docker exec -e CORE_PEER_LOCALMSPID=EcolOrgMSP peer0.ecol.example.com peer lifecycle chaincode commit -o orderer.example.com:7050 --channelID lgcse-channel --name certificate_chaincode --version 1.0.0 --sequence 1 --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/ecol.example.com/peers/peer0.ecol.example.com/msp/tlscacerts/ca.ecol.example.com-cert.pem

echo "✅ Full network deployed successfully!"
echo "📍 Network endpoints:"
echo "   ECOL (Issuer): peer0.ecol.example.com:7051"
echo "   Limkokwing (Verifier): peer0.limkokwing.example.com:9051"
echo "   Botho (Verifier): peer0.botho.example.com:11051"
echo "   Orderer: orderer.example.com:7050"
