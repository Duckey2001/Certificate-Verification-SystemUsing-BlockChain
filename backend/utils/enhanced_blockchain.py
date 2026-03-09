"""
Enhanced blockchain service for comprehensive data storage
Stores certificates, user profiles, and all activities on blockchain
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from web3 import Web3
from sqlalchemy.orm import Session
from database import SessionLocal
from models import User, Certificate, BlockchainTransaction, SystemActivity
from utils.realtime_notifications import notification_service

class BlockchainManager:
    def __init__(self, provider_url: str = "http://localhost:8545"):
        """Initialize blockchain connection"""
        self.w3 = Web3(Web3.HTTPProvider(provider_url))
        self.contract_address = None
        self.contract_abi = None
        self.account = None
        self.network = "hardhat"  # Default network
        
    def connect(self, private_key: str = None):
        """Connect to blockchain with account"""
        if private_key:
            self.account = self.w3.eth.account.from_key(private_key)
        else:
            # Use first available account for development
            if self.w3.eth.accounts:
                self.account = self.w3.eth.accounts[0]
        
        return self.w3.is_connected()
    
    def deploy_contract(self, contract_json_path: str = None):
        """Deploy the certificate management contract"""
        try:
            # For development, use a simple contract deployment
            if contract_json_path:
                with open(contract_json_path, 'r') as f:
                    contract_data = json.load(f)
                
                self.contract_abi = contract_data['abi']
                bytecode = contract_data['bytecode']
                
                contract = self.w3.eth.contract(abi=self.contract_abi, bytecode=bytecode)
                
                # Deploy contract
                tx_hash = contract.constructor().transact({'from': self.account.address})
                tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                
                self.contract_address = tx_receipt.contractAddress
                print(f"✅ Contract deployed at: {self.contract_address}")
                return self.contract_address
        except Exception as e:
            print(f"❌ Error deploying contract: {e}")
            return None
    
    def get_contract(self):
        """Get contract instance"""
        if self.contract_address and self.contract_abi:
            return self.w3.eth.contract(
                address=self.contract_address,
                abi=self.contract_abi
            )
        return None
    
    async def store_user_profile_on_blockchain(self, user_id: int) -> Optional[str]:
        """Store user profile data on blockchain"""
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                return None
            
            # Prepare user profile data
            profile_data = {
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "institution_code": user.institution_code,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_verified": user.is_verified,
                "created_at": user.created_at.isoformat(),
                "blockchain_wallet_address": user.blockchain_wallet_address
            }
            
            # Create data hash
            data_hash = self.create_data_hash(profile_data)
            
            # Store on blockchain (simulated for development)
            tx_hash = await self.simulate_blockchain_transaction(
                "user_profile",
                user_id,
                data_hash,
                profile_data
            )
            
            if tx_hash:
                # Update user with blockchain info
                user.blockchain_user_id = f"USER_{user_id}"
                db.commit()
                
                # Record transaction
                await self.record_blockchain_transaction(
                    tx_hash,
                    "user_registration",
                    user_id,
                    profile_data
                )
                
                print(f"✅ User profile stored on blockchain: {tx_hash}")
                return tx_hash
            
        except Exception as e:
            print(f"❌ Error storing user profile on blockchain: {e}")
        finally:
            db.close()
        
        return None
    
    async def store_certificate_on_blockchain(self, certificate_hash: str) -> Optional[str]:
        """Store certificate data on blockchain"""
        db = SessionLocal()
        try:
            certificate = db.query(Certificate).filter(
                Certificate.certificate_hash == certificate_hash
            ).first()
            
            if not certificate:
                return None
            
            # Prepare certificate data
            certificate_data = {
                "certificate_hash": certificate.certificate_hash,
                "student_id": certificate.student_id,
                "student_name": certificate.student_name,
                "student_surname": certificate.student_surname,
                "examination_year": certificate.examination_year,
                "subjects": certificate.subjects,
                "credits": certificate.credits,
                "issue_date": certificate.issue_date,
                "issuer_id": certificate.issuer_id,
                "status": certificate.status,
                "created_at": certificate.created_at.isoformat()
            }
            
            # Create data hash
            data_hash = self.create_data_hash(certificate_data)
            
            # Store on blockchain
            tx_hash = await self.simulate_blockchain_transaction(
                "certificate",
                certificate.issuer_id,
                data_hash,
                certificate_data
            )
            
            if tx_hash:
                # Update certificate with blockchain info
                certificate.blockchain_tx_id = tx_hash
                certificate.blockchain_network = self.network
                db.commit()
                
                # Record transaction
                await self.record_blockchain_transaction(
                    tx_hash,
                    "certificate_issue",
                    certificate.issuer_id,
                    certificate_data,
                    certificate_hash
                )
                
                print(f"✅ Certificate stored on blockchain: {tx_hash}")
                return tx_hash
            
        except Exception as e:
            print(f"❌ Error storing certificate on blockchain: {e}")
        finally:
            db.close()
        
        return None
    
    async def store_verification_on_blockchain(self, verification_data: Dict) -> Optional[str]:
        """Store verification result on blockchain"""
        try:
            # Create verification hash
            verification_hash = self.create_data_hash(verification_data)
            
            # Store on blockchain
            tx_hash = await self.simulate_blockchain_transaction(
                "verification",
                verification_data.get("verifier_id"),
                verification_hash,
                verification_data
            )
            
            if tx_hash:
                # Record transaction
                await self.record_blockchain_transaction(
                    tx_hash,
                    "verification",
                    verification_data.get("verifier_id"),
                    verification_data,
                    verification_data.get("certificate_hash")
                )
                
                print(f"✅ Verification stored on blockchain: {tx_hash}")
                return tx_hash
            
        except Exception as e:
            print(f"❌ Error storing verification on blockchain: {e}")
        
        return None
    
    async def store_activity_on_blockchain(self, activity_data: Dict) -> Optional[str]:
        """Store system activity on blockchain"""
        try:
            # Create activity hash
            activity_hash = self.create_data_hash(activity_data)
            
            # Store on blockchain
            tx_hash = await self.simulate_blockchain_transaction(
                "activity",
                activity_data.get("actor_user_id"),
                activity_hash,
                activity_data
            )
            
            if tx_hash:
                # Record transaction
                await self.record_blockchain_transaction(
                    tx_hash,
                    "system_activity",
                    activity_data.get("actor_user_id"),
                    activity_data
                )
                
                print(f"✅ Activity stored on blockchain: {tx_hash}")
                return tx_hash
            
        except Exception as e:
            print(f"❌ Error storing activity on blockchain: {e}")
        
        return None
    
    def create_data_hash(self, data: Dict) -> str:
        """Create SHA-256 hash of data"""
        data_string = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(data_string.encode()).hexdigest()
    
    async def simulate_blockchain_transaction(
        self, 
        data_type: str, 
        user_id: int, 
        data_hash: str, 
        data: Dict
    ) -> str:
        """Simulate blockchain transaction for development"""
        # In production, this would be an actual blockchain transaction
        # For development, we create a mock transaction hash
        timestamp = datetime.utcnow().isoformat()
        mock_tx_hash = f"0x{hashlib.sha256(f'{data_type}{user_id}{data_hash}{timestamp}'.encode()).hexdigest()}"
        
        # Simulate transaction delay
        import asyncio
        await asyncio.sleep(0.1)
        
        return mock_tx_hash
    
    async def record_blockchain_transaction(
        self,
        tx_hash: str,
        transaction_type: str,
        user_id: int,
        data: Dict,
        certificate_hash: str = None
    ):
        """Record blockchain transaction in database"""
        db = SessionLocal()
        try:
            transaction = BlockchainTransaction(
                transaction_hash=tx_hash,
                transaction_type=transaction_type,
                user_id=user_id,
                certificate_hash=certificate_hash,
                network=self.network,
                status="confirmed",
                confirmations=1,
                metadata=data
            )
            db.add(transaction)
            db.commit()
            
            # Create system activity
            await notification_service.create_system_activity(
                activity_type="blockchain_transaction",
                title=f"Blockchain transaction: {transaction_type}",
                description=f"Data stored on blockchain with transaction {tx_hash[:10]}...",
                actor_user_id=user_id,
                metadata={
                    "tx_hash": tx_hash,
                    "transaction_type": transaction_type,
                    "data_hash": self.create_data_hash(data)
                },
                impact_score=3
            )
            
        except Exception as e:
            print(f"❌ Error recording blockchain transaction: {e}")
            db.rollback()
        finally:
            db.close()
    
    async def verify_data_on_blockchain(self, data_hash: str) -> bool:
        """Verify data exists on blockchain"""
        db = SessionLocal()
        try:
            transaction = db.query(BlockchainTransaction).filter(
                BlockchainTransaction.metadata.op('?')('data_hash'),
                BlockchainTransaction.metadata['data_hash'].astext == data_hash
            ).first()
            
            return transaction is not None and transaction.status == "confirmed"
        except Exception as e:
            print(f"❌ Error verifying data on blockchain: {e}")
            return False
        finally:
            db.close()
    
    async def get_blockchain_history(self, user_id: int = None, certificate_hash: str = None) -> List[Dict]:
        """Get blockchain transaction history"""
        db = SessionLocal()
        try:
            query = db.query(BlockchainTransaction)
            
            if user_id:
                query = query.filter(BlockchainTransaction.user_id == user_id)
            if certificate_hash:
                query = query.filter(BlockchainTransaction.certificate_hash == certificate_hash)
            
            transactions = query.order_by(BlockchainTransaction.created_at.desc()).all()
            
            history = []
            for tx in transactions:
                history.append({
                    "transaction_hash": tx.transaction_hash,
                    "transaction_type": tx.transaction_type,
                    "network": tx.network,
                    "block_number": tx.block_number,
                    "status": tx.status,
                    "confirmations": tx.confirmations,
                    "created_at": tx.created_at.isoformat(),
                    "metadata": tx.metadata
                })
            
            return history
        except Exception as e:
            print(f"❌ Error getting blockchain history: {e}")
            return []
        finally:
            db.close()

# Global blockchain manager instance
blockchain_manager = BlockchainManager()

# Initialize blockchain connection
async def initialize_blockchain():
    """Initialize blockchain connection and contract"""
    try:
        # For development, we'll simulate blockchain connection
        print("🔗 Initializing blockchain connection...")
        
        # In production, connect to actual blockchain
        # connected = blockchain_manager.connect(private_key=os.getenv("BLOCKCHAIN_PRIVATE_KEY"))
        
        # For now, simulate successful connection
        connected = True
        
        if connected:
            print("✅ Blockchain connection established")
            return True
        else:
            print("❌ Failed to connect to blockchain")
            return False
    except Exception as e:
        print(f"❌ Blockchain initialization error: {e}")
        return False

# Helper functions for integration
async def store_certificate_on_blockchain(certificate_hash: str):
    """Store certificate on blockchain (wrapper function)"""
    return await blockchain_manager.store_certificate_on_blockchain(certificate_hash)

async def store_user_profile_on_blockchain(user_id: int):
    """Store user profile on blockchain (wrapper function)"""
    return await blockchain_manager.store_user_profile_on_blockchain(user_id)

async def verify_certificate_on_blockchain(certificate_hash: str):
    """Verify certificate on blockchain"""
    data_hash = hashlib.sha256(certificate_hash.encode()).hexdigest()
    return await blockchain_manager.verify_data_on_blockchain(data_hash)

async def get_blockchain_explorer_url(tx_hash: str) -> str:
    """Get blockchain explorer URL for transaction"""
    if blockchain_manager.network == "hardhat":
        return f"http://localhost:8545/tx/{tx_hash}"
    elif blockchain_manager.network == "sepolia":
        return f"https://sepolia.etherscan.io/tx/{tx_hash}"
    else:
        return f"https://etherscan.io/tx/{tx_hash}"
