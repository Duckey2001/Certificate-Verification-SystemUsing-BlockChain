import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from web3 import Web3


def _get_registry_address() -> str | None:
    """Get registry address from env or registry.json."""
    addr = os.getenv("CERT_REGISTRY_ADDRESS")
    if addr:
        return addr
    registry_path = os.path.join(
        os.path.dirname(__file__), "..", "blockchain", "registry.json"
    )
    registry_path = os.path.abspath(registry_path)
    if os.path.isfile(registry_path):
        with open(registry_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("address")
    return None


def _load_abi() -> list[dict[str, Any]]:
    abi_path = os.getenv(
        "CERT_REGISTRY_ABI_PATH",
        os.path.join(os.path.dirname(__file__), "..", "blockchain", "CertificateRegistry.abi.json"),
    )
    abi_path = os.path.abspath(abi_path)
    with open(abi_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _hash_to_bytes32(certificate_hash: str) -> bytes:
    h = certificate_hash.lower().replace("0x", "").strip()
    if len(h) != 64:
        raise ValueError("certificate_hash must be 64 hex chars")
    return bytes.fromhex(h)


@dataclass
class TxResult:
    tx_hash: str
    block_number: Optional[int] = None


class HardhatCertificateRegistry:
    """
    Minimal adapter for a CertificateRegistry Solidity contract on an EVM chain.
    Designed to work with local Hardhat (RPC) for development.
    """

    def __init__(self):
        self.rpc_url = os.getenv("HARDHAT_RPC_URL", "http://127.0.0.1:8545")
        self.address = _get_registry_address()
        self.private_key = os.getenv("ISSUER_PRIVATE_KEY")
        if not self.address:
            raise RuntimeError(
                "CERT_REGISTRY_ADDRESS is not set and registry.json not found. "
                "Deploy with: cd blockchain && npm run deploy"
            )
        if not self.private_key:
            raise RuntimeError(
                "ISSUER_PRIVATE_KEY is not set. "
                "For local Hardhat, use account #0 key (see .env.example)"
            )

        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        if not self.w3.is_connected():
            raise RuntimeError(f"Cannot connect to RPC at {self.rpc_url}")

        self.abi = _load_abi()
        self.contract = self.w3.eth.contract(address=Web3.to_checksum_address(self.address), abi=self.abi)
        self.account = self.w3.eth.account.from_key(self.private_key)

    def exists(self, certificate_hash: str) -> bool:
        b32 = _hash_to_bytes32(certificate_hash)
        return bool(self.contract.functions.exists(b32).call())

    def issue(self, certificate_hash: str, metadata_uri: str) -> TxResult:
        b32 = _hash_to_bytes32(certificate_hash)
        nonce = self.w3.eth.get_transaction_count(self.account.address)
        tx = self.contract.functions.issue(b32, metadata_uri).build_transaction(
            {
                "from": self.account.address,
                "nonce": nonce,
                "gas": 500_000,
                "gasPrice": self.w3.eth.gas_price,
            }
        )
        signed = self.w3.eth.account.sign_transaction(tx, private_key=self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return TxResult(tx_hash=tx_hash.hex(), block_number=getattr(receipt, "blockNumber", None))

    def report_tamper(self, expected_hash: str, computed_hash: str) -> TxResult:
        expected_b32 = _hash_to_bytes32(expected_hash)
        computed_b32 = _hash_to_bytes32(computed_hash)
        nonce = self.w3.eth.get_transaction_count(self.account.address)
        tx = self.contract.functions.reportTamper(expected_b32, computed_b32).build_transaction(
            {
                "from": self.account.address,
                "nonce": nonce,
                "gas": 500_000,
                "gasPrice": self.w3.eth.gas_price,
            }
        )
        signed = self.w3.eth.account.sign_transaction(tx, private_key=self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed.rawTransaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        return TxResult(tx_hash=tx_hash.hex(), block_number=getattr(receipt, "blockNumber", None))

