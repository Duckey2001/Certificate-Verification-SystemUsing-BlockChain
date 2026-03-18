# CertiVert Backend - Multi-Organization Hyperledger Fabric

## Architecture:
- Issuer Organization (Org1): Issues certificates
- Verifier Organizations (Org2, Org3, Org4): Verify certificates
- Ordering Service: Single orderer for MVP
- Certificate Chaincode: Smart contract for issuing/verifying

## Onboarding Flow:
1. New institution requests to join
2. Admin approves request
3. System generates MSP and config
4. Channel config updated
5. Institution joins network
