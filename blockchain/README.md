# LGCSE Blockchain (Smart Contracts / Chaincode)

EVM-based smart contracts for certificate issuance and verification. Uses **Hardhat** and **Solidity**.

## Contracts

| Contract | Purpose |
|----------|---------|
| `CertificateRegistry` | Stores certificate hashes on-chain; `issue`, `exists`, `reportTamper` |
| `LGCSEToken` | ERC-20 token with staking, governance, projects |

The backend uses **CertificateRegistry** for LGCSE diploma verification.

## Quick Start

### 1. Install

```bash
cd blockchain && npm install
```

### 2. Compile

```bash
npm run compile
```

### 3. Start Local Node (separate terminal)

```bash
npm run node
```

### 4. Deploy

```bash
npm run deploy
```

This deploys `CertificateRegistry`, writes `backend/blockchain/registry.json` and `CertificateRegistry.abi.json`.

### 5. Configure Backend

Copy backend env and add the Hardhat account key (local dev only):

```bash
cp ../backend/.env.example ../backend/.env
# Edit .env and ensure ISSUER_PRIVATE_KEY is set (see below)
```

**Hardhat account #0** (default deployer):
- Private key: `0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80`
- Used for local testing; **never use in production**

The backend reads the contract address from `backend/blockchain/registry.json` automatically after deploy.

## Scripts

| Command | Description |
|---------|-------------|
| `npm run node` | Start Hardhat local network (port 8545) |
| `npm run compile` | Compile Solidity contracts |
| `npm run deploy` | Deploy CertificateRegistry to localhost and sync ABI |

## Integration

- **Backend** (`backend/utils/blockchain_hardhat.py`, `blockchain_service.py`): Web3.py adapter for `CertificateRegistry`
- **Env vars**: `ISSUER_PRIVATE_KEY` (required), `CERT_REGISTRY_ADDRESS` (optional if `registry.json` exists), `HARDHAT_RPC_URL` (default `http://127.0.0.1:8545`)

## Running End-to-End

1. Terminal 1: `cd blockchain && npm run node`
2. Terminal 2: `cd blockchain && npm run deploy`
3. Terminal 3: Backend with `ISSUER_PRIVATE_KEY` set (and optional `.env` from `.env.example`)
4. Use the app to issue/verify certificates; hashes are written to the chain
