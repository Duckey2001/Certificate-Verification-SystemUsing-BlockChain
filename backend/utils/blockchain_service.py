import os
from typing import Dict, Any
from datetime import datetime

from utils.blockchain_hardhat import HardhatCertificateRegistry

class BlockchainService:
    def __init__(self, blockchain_url: str = None):
        self.blockchain_url = blockchain_url or "http://localhost:3000"
        self._hardhat: HardhatCertificateRegistry | None = None

        # Enable real chain integration when configured (address from env or registry.json)
        if os.getenv("ISSUER_PRIVATE_KEY"):
            try:
                self._hardhat = HardhatCertificateRegistry()
            except Exception:
                self._hardhat = None
        
    def store_hash_on_blockchain(self, certificate_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store certificate hash on the blockchain"""
        try:
            cert_hash = certificate_data["certificate_hash"]
            metadata_uri = f"certivert://{cert_hash}"

            # Real chain
            if self._hardhat:
                tx = self._hardhat.issue(cert_hash, metadata_uri)
                self.notify_network(
                    event_type="certificate_uploaded",
                    payload={"certificate_hash": cert_hash, "tx_hash": tx.tx_hash, "block_number": tx.block_number},
                )
                return {
                    "success": True,
                    "transaction_id": tx.tx_hash,
                    "block_number": tx.block_number,
                    "network": "hardhat",
                    "timestamp": datetime.now().isoformat(),
                }

            # Fallback simulation
            print(f"📦 Would store on blockchain: {cert_hash}")
            self.notify_network(event_type="certificate_uploaded", payload={"certificate_hash": cert_hash})
            return {
                "success": True,
                "transaction_id": f"tx_{cert_hash[:16]}",
                "network": "simulated",
                "timestamp": datetime.now().isoformat(),
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def verify_hash_on_blockchain(self, certificate_hash: str) -> Dict[str, Any]:
        """Verify if a certificate hash exists on the blockchain"""
        try:
            if self._hardhat:
                exists = self._hardhat.exists(certificate_hash)
                return {
                    "exists": exists,
                    "certificate_hash": certificate_hash,
                    "verified": exists,
                    "network": "hardhat",
                    "timestamp": datetime.now().isoformat(),
                }

            # Simulation
            print(f"🔍 Would verify on blockchain: {certificate_hash}")
            return {
                "exists": True,
                "certificate_hash": certificate_hash,
                "verified": True,
                "network": "simulated",
                "timestamp": datetime.now().isoformat(),
            }
        except Exception as e:
            return {
                "exists": False,
                "error": str(e)
            }

    def report_tamper(self, expected_hash: str, computed_hash: str) -> Dict[str, Any]:
        try:
            if self._hardhat:
                tx = self._hardhat.report_tamper(expected_hash, computed_hash)
                self.notify_network(
                    event_type="certificate_tampered",
                    payload={
                        "certificate_hash": expected_hash,
                        "computed_hash": computed_hash,
                        "tx_hash": tx.tx_hash,
                        "block_number": tx.block_number,
                    },
                )
                return {"success": True, "transaction_id": tx.tx_hash, "network": "hardhat"}

            self.notify_network(
                event_type="certificate_tampered",
                payload={"certificate_hash": expected_hash, "computed_hash": computed_hash},
            )
            return {"success": True, "transaction_id": f"tx_tamper_{expected_hash[:16]}", "network": "simulated"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def notify_network(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Notify other nodes that something happened (upload / tamper).

        For now this is simulated by logging; later this can be replaced with:
        - Hyperledger Fabric events
        - Webhooks / message queue
        - WebSocket broadcast
        """
        try:
            print(f"📣 Network event: {event_type} | payload={payload}")
            return {"success": True, "event_type": event_type, "timestamp": datetime.now().isoformat()}
        except Exception as e:
            return {"success": False, "error": str(e)}
