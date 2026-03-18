# Firebase Cloud Messaging Setup Guide

This document provides instructions for setting up Firebase Cloud Messaging (FCM) for the CertiVert project.

## ✅ Completed Setup

### Frontend Configuration
- **Firebase SDK**: Installed via npm (`firebase` package)
- **Firebase Config**: Created in `frontend/src/firebase.js` with your project credentials
- **Notification Service**: Created `frontend/src/services/NotificationService.js`
- **Settings Component**: Created `frontend/src/components/NotificationSettings.jsx`

### Backend Configuration
- **Firebase Admin SDK**: Installed via pip (`firebase-admin==7.2.0`)
- **Firebase Service**: Created `backend/firebase_config.py`
- **API Endpoints**: Created `backend/api/notifications.py`
- **Database Model**: Updated User model with `fcm_token` field

## 🔧 Required Setup Steps

### 1. Download Service Account Key

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Select your project: `certivert-25289`
3. Go to Project Settings → Service Accounts
4. Click "Generate new private key"
5. Download the JSON file and save it as `backend/serviceAccountKey.json`

### 2. Update Environment Variables

Update the `.env` file in the backend with your actual Firebase credentials:

```bash
# Firebase Configuration
FIREBASE_PROJECT_ID=certivert-25289
FIREBASE_PRIVATE_KEY_ID=your_actual_private_key_id
FIREBASE_PRIVATE_KEY="-----BEGIN PRIVATE KEY-----\nYOUR_ACTUAL_PRIVATE_KEY_CONTENT_HERE\n-----END PRIVATE KEY-----\n"
FIREBASE_CLIENT_EMAIL=firebase-adminsdk-fbsvc@certivert-25289.iam.gserviceaccount.com
FIREBASE_CLIENT_ID=674326105550
```

### 3. Database Migration

Run the following to update the database schema:

```bash
cd backend
alembic revision --autogenerate -m "Add FCM token field to users"
alembic upgrade head
```

## 🚀 Usage Instructions

### For Users

1. **Enable Notifications**: Users can enable notifications through the NotificationSettings component
2. **Permission**: Browser will request notification permission
3. **Token Registration**: FCM token is automatically registered with the backend
4. **Topic Subscription**: Users can subscribe to specific notification topics

### For Developers

#### Sending Notifications

```python
from backend.firebase_config import firebase_service

# Send to specific device
firebase_service.send_notification_to_device(
    token="user_fcm_token",
    title="Certificate Verified",
    body="Your certificate has been verified",
    data={"type": "certificate_verified", "certificate_id": "123"}
)

# Send to topic
firebase_service.send_notification_to_topic(
    topic="certificate_updates",
    title="System Update",
    body="New features available"
)
```

#### Frontend Integration

```javascript
import notificationService from './services/NotificationService';

// Initialize notifications
await notificationService.initialize();

// Subscribe to topic
await notificationService.subscribeToTopic('certificate_updates');

// Listen for notifications
notificationService.addEventListener('message', (payload) => {
    console.log('Received notification:', payload);
});
```

## 📡 API Endpoints

### Notification Management
- `POST /api/notifications/register-token` - Register FCM token
- `POST /api/notifications/send-to-device` - Send to specific device
- `POST /api/notifications/send-to-topic` - Send to topic
- `POST /api/notifications/send-multicast` - Send to multiple devices
- `POST /api/notifications/subscribe-to-topic` - Subscribe to topic
- `POST /api/notifications/unsubscribe-from-topic` - Unsubscribe from topic
- `GET /api/notifications/firebase-status` - Check Firebase status

### Certificate-specific Notifications
- `POST /api/notifications/certificate-verified` - Certificate verification notification
- `POST /api/notifications/certificate-processed` - Certificate processing notification
- `POST /api/notifications/payment-confirmed` - Payment confirmation notification

## 🔒 Security Considerations

1. **VAPID Key**: The VAPID key is already configured in the frontend
2. **Service Account**: Keep the service account key file secure and never commit it to version control
3. **Token Validation**: Backend validates user authentication before registering tokens
4. **Topic Permissions**: Users can only subscribe to topics they have access to

## 🧪 Testing

### Test Notification Setup
1. Go to the NotificationSettings component in your app
2. Click "Initialize Notifications"
3. Grant browser permission when prompted
4. Click "Send Test Notification"

### Test API Endpoints
```bash
# Test Firebase status
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/api/notifications/firebase-status

# Send test notification
curl -X POST \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{"token":"USER_FCM_TOKEN","title":"Test","body":"Test message"}' \
     http://localhost:8000/api/notifications/send-to-device
```

## 📱 Browser Compatibility

Push notifications are supported in:
- ✅ Chrome 50+
- ✅ Firefox 44+
- ✅ Safari 16+ (macOS)
- ✅ Edge 79+

## 🔧 Troubleshooting

### Common Issues

1. **Permission Denied**: Users must grant notification permission in their browser
2. **Service Worker**: Ensure service workers are enabled in your browser
3. **HTTPS Required**: Push notifications require HTTPS in production
4. **Firebase Config**: Double-check your Firebase configuration values

### Debug Logs

Enable debug logging by setting:
```javascript
// In browser console
localStorage.setItem('debug', 'firebase*');
```

## 📚 Additional Resources

- [Firebase Cloud Messaging Documentation](https://firebase.google.com/docs/cloud-messaging)
- [Web Push Notifications Guide](https://web.dev/push-notifications/)
- [Firebase Admin SDK Python](https://firebase.google.com/docs/admin/setup)
