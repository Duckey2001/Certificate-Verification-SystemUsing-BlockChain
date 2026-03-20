#!/bin/bash
# 2-Node Blockchain Network Deployment (ECOL + 1 Verifier)

echo "🚀 Starting 2-node blockchain network deployment..."

cd /home/duckey/lgcse-project/hyperledger-fabric

# Start essential services
echo "📦 Starting Docker containers..."
docker-compose up -d ca.orderer.example.com ca.ecol.example.com ca.limkokwing.example.com
docker-compose up -d orderer.example.com couchdb0 couchdb1
docker-compose up -d peer0.ecol.example.com peer0.limkokwing.example.com

# Wait for containers to be ready
echo "⏳ Waiting for containers to initialize..."
sleep 30

# Create channel
echo "📡 Creating lgcse-channel..."
docker exec cli peer channel create -c lgcse-channel -f ./config/channel.tx --outputBlock ./config/genesis.block -o orderer.example.com:7050 --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/ordererOrganizations/example.com/orderers/orderer.example.com/msp/tlscacerts/orderer.example.com-cert.pem

# Join peers to channel
echo "🔗 Joining peers to channel..."
docker exec -e CORE_PEER_LOCALMSPID=EcolOrgMSP peer0.ecol.example.com peer channel join -b ./config/genesis.block --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/ecol.example.com/peers/peer0.ecol.example.com/msp/tlscacerts/ca.ecol.example.com-cert.pem
docker exec -e CORE_PEER_LOCALMSPID=LimkokwingOrgMSP peer0.limkokwing.example.com peer channel join -b ./config/genesis.block --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/limkokwing.example.com/peers/peer0.limkokwing.example.com/msp/tlscacerts/ca.limkokwing.example.com-cert.pem

# Install chaincode
echo "🔧 Installing chaincode..."
docker exec -e CORE_PEER_LOCALMSPID=EcolOrgMSP peer0.ecol.example.com peer lifecycle chaincode install /opt/gopath/src/github.com/chaincode/certificate.tar.gz --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/ecol.example.com/peers/peer0.ecol.example.com/msp/tlscacerts/ca.ecol.example.com-cert.pem
docker exec -e CORE_PEER_LOCALMSPID=LimkokwingOrgMSP peer0.limkokwing.example.com peer lifecycle chaincode install /opt/gopath/src/github.com/chaincode/certificate.tar.gz --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/limkokwing.example.com/peers/peer0.limkokwing.example.com/msp/tlscacerts/ca.limkokwing.example.com-cert.pem

# Instantiate chaincode
echo "⚡ Instantiating chaincode..."
docker exec -e CORE_PEER_LOCALMSPID=EcolOrgMSP peer0.ecol.example.com peer lifecycle chaincode approveformyorg --channelID lgcse-channel --name certificate_chaincode --version 1.0.0 --sequence 1 --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/peerOrganizations/ecol.example.com/peers/peer0.ecol.example.com/msp/tlscacerts/ca.ecol.example.com-cert.pem
docker exec -e CORE_PEER_LOCALMSPID=EcolOrgMSP peer0.ecol.example.com peer lifecycle chaincode commit -o orderer.example.com:7050 --channelID lgcse-channel --name certificate_chaincode --version 1.0.0 --sequence 1 --tls --cafile /opt/gopath/src/github.com/hyperledger/fabric/peer/organizations/ordererOrganizations/ecol.example.com/peers/peer0.ecol.example.com/msp/tlscacerts/ca.ecol.example.com-cert.pem

echo "✅ 2-node network deployed successfully!"
echo "📍 Network endpoints:"
echo "   ECOL (Issuer): peer0.ecol.example.com:7051"
echo "   Limkokwing (Verifier): peer0.limkokwing.example.com:9051"
echo "   Orderer: orderer.example.com:7050"
