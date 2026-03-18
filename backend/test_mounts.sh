#!/bin/bash
echo "=== Testing orderer mounts ==="
docker run --rm -v $(pwd)/fabric/network/crypto-config/ordererOrganizations/certivert.com/orderers/orderer.certivert.com/msp:/mnt/msp \
  -v $(pwd)/fabric/network/crypto-config/ordererOrganizations/certivert.com/orderers/orderer.certivert.com/tls:/mnt/tls \
  alpine ls -la /mnt/msp/signcerts/ 2>/dev/null || echo "Cannot access signcerts"

echo -e "\n=== Testing peer0.org1 mounts ==="
docker run --rm -v $(pwd)/fabric/network/crypto-config/peerOrganizations/org1.certivert.com/peers/peer0.org1.certivert.com/msp:/mnt/msp \
  alpine ls -la /mnt/msp/signcerts/ 2>/dev/null || echo "Cannot access signcerts"
