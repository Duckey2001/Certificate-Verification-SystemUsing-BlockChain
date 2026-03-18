from fastapi import APIRouter, HTTPException, Depends, Body
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
from firebase_config import firebase_service
from auth import get_current_user
from database import get_db
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/notifications", tags=["notifications"])

class NotificationRequest(BaseModel):
    title: str
    body: str
    data: Optional[Dict[str, str]] = None

class DeviceNotificationRequest(NotificationRequest):
    token: str

class TopicNotificationRequest(NotificationRequest):
    topic: str

class MulticastNotificationRequest(NotificationRequest):
    tokens: List[str]

class TopicSubscriptionRequest(BaseModel):
    tokens: List[str]
    topic: str

class TokenRegistrationRequest(BaseModel):
    fcm_token: str

@router.post("/send-to-device")
async def send_notification_to_device(
    request: DeviceNotificationRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send notification to a specific device"""
    try:
        success = firebase_service.send_notification_to_device(
            token=request.token,
            title=request.title,
            body=request.body,
            data=request.data
        )
        
        if success:
            return {"message": "Notification sent successfully", "success": True}
        else:
            raise HTTPException(status_code=500, detail="Failed to send notification")
            
    except Exception as e:
        logger.error(f"Error sending notification to device: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send-to-topic")
async def send_notification_to_topic(
    request: TopicNotificationRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send notification to a topic"""
    try:
        success = firebase_service.send_notification_to_topic(
            topic=request.topic,
            title=request.title,
            body=request.body,
            data=request.data
        )
        
        if success:
            return {"message": "Notification sent to topic successfully", "success": True}
        else:
            raise HTTPException(status_code=500, detail="Failed to send notification to topic")
            
    except Exception as e:
        logger.error(f"Error sending notification to topic: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/send-multicast")
async def send_multicast_notification(
    request: MulticastNotificationRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send notification to multiple devices"""
    try:
        result = firebase_service.send_multicast_notification(
            tokens=request.tokens,
            title=request.title,
            body=request.body,
            data=request.data
        )
        
        return {
            "message": "Multicast notification sent",
            "success_count": result["success"],
            "failure_count": result["failure"],
            "invalid_tokens": result.get("invalid_tokens", [])
        }
        
    except Exception as e:
        logger.error(f"Error sending multicast notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/subscribe-to-topic")
async def subscribe_to_topic(
    request: TopicSubscriptionRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Subscribe devices to a topic"""
    try:
        success = firebase_service.subscribe_to_topic(
            tokens=request.tokens,
            topic=request.topic
        )
        
        if success:
            return {"message": "Successfully subscribed to topic", "success": True}
        else:
            raise HTTPException(status_code=500, detail="Failed to subscribe to topic")
            
    except Exception as e:
        logger.error(f"Error subscribing to topic: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/unsubscribe-from-topic")
async def unsubscribe_from_topic(
    request: TopicSubscriptionRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unsubscribe devices from a topic"""
    try:
        success = firebase_service.unsubscribe_from_topic(
            tokens=request.tokens,
            topic=request.topic
        )
        
        if success:
            return {"message": "Successfully unsubscribed from topic", "success": True}
        else:
            raise HTTPException(status_code=500, detail="Failed to unsubscribe from topic")
            
    except Exception as e:
        logger.error(f"Error unsubscribing from topic: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/register-token")
async def register_fcm_token(
    request: TokenRegistrationRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Register FCM token for the current user"""
    try:
        # Store the FCM token in the user's profile
        user = db.query(User).filter(User.id == current_user["id"]).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update user's FCM token (you might want to support multiple tokens)
        user.fcm_token = request.fcm_token
        db.commit()
        
        logger.info(f"FCM token registered for user {current_user['id']}")
        return {"message": "FCM token registered successfully", "success": True}
        
    except Exception as e:
        logger.error(f"Error registering FCM token: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/firebase-status")
async def get_firebase_status(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get Firebase service status"""
    try:
        return {
            "firebase_initialized": firebase_service.app is not None,
            "service_available": firebase_service.app is not None
        }
    except Exception as e:
        logger.error(f"Error checking Firebase status: {str(e)}")
        return {
            "firebase_initialized": False,
            "service_available": False,
            "error": str(e)
        }

# Certificate-specific notification endpoints
@router.post("/certificate-verified")
async def send_certificate_verified_notification(
    certificate_id: int,
    recipient_token: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send notification when certificate is verified"""
    try:
        success = firebase_service.send_notification_to_device(
            token=recipient_token,
            title="Certificate Verified",
            body=f"Your certificate #{certificate_id} has been successfully verified",
            data={
                "type": "certificate_verified",
                "certificate_id": str(certificate_id),
                "action": "view_certificate"
            }
        )
        
        if success:
            return {"message": "Certificate verification notification sent", "success": True}
        else:
            raise HTTPException(status_code=500, detail="Failed to send notification")
            
    except Exception as e:
        logger.error(f"Error sending certificate verification notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/certificate-processed")
async def send_certificate_processed_notification(
    certificate_id: int,
    processing_status: str,
    recipient_token: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send notification when certificate processing is complete"""
    try:
        title = "Certificate Processing Complete"
        body = f"Your certificate #{certificate_id} processing is {processing_status}"
        
        success = firebase_service.send_notification_to_device(
            token=recipient_token,
            title=title,
            body=body,
            data={
                "type": "certificate_processed",
                "certificate_id": str(certificate_id),
                "status": processing_status,
                "action": "view_certificate"
            }
        )
        
        if success:
            return {"message": "Certificate processing notification sent", "success": True}
        else:
            raise HTTPException(status_code=500, detail="Failed to send notification")
            
    except Exception as e:
        logger.error(f"Error sending certificate processing notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/payment-confirmed")
async def send_payment_confirmed_notification(
    payment_id: str,
    amount: float,
    recipient_token: str,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send notification when payment is confirmed"""
    try:
        success = firebase_service.send_notification_to_device(
            token=recipient_token,
            title="Payment Confirmed",
            body=f"Your payment of {amount} LSL has been confirmed",
            data={
                "type": "payment_confirmed",
                "payment_id": payment_id,
                "amount": str(amount),
                "action": "view_receipt"
            }
        )
        
        if success:
            return {"message": "Payment confirmation notification sent", "success": True}
        else:
            raise HTTPException(status_code=500, detail="Failed to send notification")
            
    except Exception as e:
        logger.error(f"Error sending payment confirmation notification: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
