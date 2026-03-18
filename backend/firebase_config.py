import firebase_admin
from firebase_admin import credentials, messaging
import os
from typing import Optional, List
import json
import logging

logger = logging.getLogger(__name__)

class FirebaseService:
    def __init__(self):
        self.cred = None
        self.app = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            # Check if service account key file exists
            service_account_path = os.path.join(os.path.dirname(__file__), 'serviceAccountKey.json')
            
            if os.path.exists(service_account_path):
                # Use service account key file
                self.cred = credentials.Certificate(service_account_path)
            else:
                # Use environment variables for Firebase configuration
                firebase_config = {
                    "type": "service_account",
                    "project_id": os.getenv("FIREBASE_PROJECT_ID", "certivert-25289"),
                    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
                    "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace('\\n', '\n'),
                    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
                    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
                
                if all([firebase_config["private_key"], firebase_config["client_email"]]):
                    self.cred = credentials.Certificate(firebase_config)
                else:
                    logger.warning("Firebase credentials not properly configured")
                    return
            
            # Initialize Firebase app
            if not firebase_admin._apps:
                self.app = firebase_admin.initialize_app(self.cred)
                logger.info("Firebase Admin SDK initialized successfully")
            else:
                self.app = firebase_admin.get_app()
                logger.info("Firebase Admin SDK already initialized")
                
        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {str(e)}")
            self.app = None
    
    def send_notification_to_device(self, token: str, title: str, body: str, data: dict = None) -> bool:
        """Send notification to a specific device"""
        try:
            if not self.app:
                logger.error("Firebase not initialized")
                return False
            
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                token=token
            )
            
            response = messaging.send(message)
            logger.info(f"Successfully sent message: {response}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
            return False
    
    def send_notification_to_topic(self, topic: str, title: str, body: str, data: dict = None) -> bool:
        """Send notification to a topic"""
        try:
            if not self.app:
                logger.error("Firebase not initialized")
                return False
            
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                topic=topic
            )
            
            response = messaging.send(message)
            logger.info(f"Successfully sent message to topic: {response}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send notification to topic: {str(e)}")
            return False
    
    def send_multicast_notification(self, tokens: List[str], title: str, body: str, data: dict = None) -> dict:
        """Send notification to multiple devices"""
        try:
            if not self.app:
                logger.error("Firebase not initialized")
                return {"success": False, "failure": len(tokens)}
            
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                tokens=tokens
            )
            
            response = messaging.send_multicast(message)
            logger.info(f"Multicast notification sent: {response.success_count} success, {response.failure_count} failure")
            
            return {
                "success": response.success_count,
                "failure": response.failure_count,
                "invalid_tokens": self._extract_invalid_tokens(response, tokens)
            }
            
        except Exception as e:
            logger.error(f"Failed to send multicast notification: {str(e)}")
            return {"success": 0, "failure": len(tokens)}
    
    def _extract_invalid_tokens(self, response, tokens: List[str]) -> List[str]:
        """Extract invalid tokens from multicast response"""
        invalid_tokens = []
        for i, result in enumerate(response.responses):
            if not result.success:
                invalid_tokens.append(tokens[i])
        return invalid_tokens
    
    def subscribe_to_topic(self, tokens: List[str], topic: str) -> bool:
        """Subscribe devices to a topic"""
        try:
            if not self.app:
                logger.error("Firebase not initialized")
                return False
            
            response = messaging.subscribe_to_topic(tokens, topic)
            logger.info(f"Subscribed {response.success_count} devices to topic {topic}")
            return response.success_count > 0
            
        except Exception as e:
            logger.error(f"Failed to subscribe to topic: {str(e)}")
            return False
    
    def unsubscribe_from_topic(self, tokens: List[str], topic: str) -> bool:
        """Unsubscribe devices from a topic"""
        try:
            if not self.app:
                logger.error("Firebase not initialized")
                return False
            
            response = messaging.unsubscribe_from_topic(tokens, topic)
            logger.info(f"Unsubscribed {response.success_count} devices from topic {topic}")
            return response.success_count > 0
            
        except Exception as e:
            logger.error(f"Failed to unsubscribe from topic: {str(e)}")
            return False

# Global Firebase service instance
firebase_service = FirebaseService()
