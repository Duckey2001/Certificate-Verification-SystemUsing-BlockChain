import { requestNotificationPermission, onMessageListener } from '../firebase';
import axios from 'axios';

class NotificationService {
  constructor() {
    this.token = null;
    this.isSupported = 'Notification' in window && 'serviceWorker' in navigator;
    this.listeners = new Map();
  }

  async initialize() {
    if (!this.isSupported) {
      console.warn('Notifications are not supported in this browser');
      return false;
    }

    try {
      // Request permission and get token
      this.token = await requestNotificationPermission();
      
      if (this.token) {
        console.log('FCM Token:', this.token);
        
        // Set up message listener
        this.setupMessageListener();
        
        // Register token with backend
        await this.registerTokenWithBackend();
        
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Failed to initialize notifications:', error);
      return false;
    }
  }

  setupMessageListener() {
    onMessageListener()
      .then((payload) => {
        console.log('Received foreground message:', payload);
        this.handleIncomingMessage(payload);
      })
      .catch((error) => {
        console.error('Error setting up message listener:', error);
      });
  }

  handleIncomingMessage(payload) {
    const { notification, data } = payload;
    
    // Show notification in foreground
    if (notification && Notification.permission === 'granted') {
      const notificationOptions = {
        body: notification.body,
        icon: '/favicon.ico',
        badge: '/favicon.ico',
        tag: data?.type || 'default',
        data: data || {},
        requireInteraction: true,
        actions: this.getNotificationActions(data?.type)
      };

      const notificationInstance = new Notification(notification.title, notificationOptions);
      
      // Handle notification click
      notificationInstance.onclick = (event) => {
        event.preventDefault();
        this.handleNotificationClick(data);
        notificationInstance.close();
      };

      // Auto-close after 5 seconds
      setTimeout(() => {
        notificationInstance.close();
      }, 5000);
    }

    // Trigger event listeners
    this.triggerListeners('message', payload);
  }

  getNotificationActions(type) {
    switch (type) {
      case 'certificate_verified':
      case 'certificate_processed':
        return [
          {
            action: 'view',
            title: 'View Certificate'
          }
        ];
      case 'payment_confirmed':
        return [
          {
            action: 'view',
            title: 'View Receipt'
          }
        ];
      default:
        return [];
    }
  }

  handleNotificationClick(data) {
    const { type, action } = data;
    
    switch (type) {
      case 'certificate_verified':
      case 'certificate_processed':
        if (data.certificate_id) {
          window.location.href = `/certificates/${data.certificate_id}`;
        }
        break;
      case 'payment_confirmed':
        if (data.payment_id) {
          window.location.href = `/payments/${data.payment_id}`;
        }
        break;
      default:
        // Default action - go to dashboard
        window.location.href = '/dashboard';
    }
  }

  async registerTokenWithBackend() {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        console.warn('No auth token found, skipping FCM token registration');
        return;
      }

      await axios.post('/api/notifications/register-token', {
        fcm_token: this.token
      }, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      
      console.log('FCM token registered with backend');
    } catch (error) {
      console.error('Failed to register FCM token with backend:', error);
    }
  }

  async subscribeToTopic(topic) {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('No auth token found');
      }

      const response = await axios.post('/api/notifications/subscribe-to-topic', {
        tokens: [this.token],
        topic: topic
      }, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      console.log(`Subscribed to topic: ${topic}`);
      return response.data;
    } catch (error) {
      console.error(`Failed to subscribe to topic ${topic}:`, error);
      throw error;
    }
  }

  async unsubscribeFromTopic(topic) {
    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('No auth token found');
      }

      const response = await axios.post('/api/notifications/unsubscribe-from-topic', {
        tokens: [this.token],
        topic: topic
      }, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      console.log(`Unsubscribed from topic: ${topic}`);
      return response.data;
    } catch (error) {
      console.error(`Failed to unsubscribe from topic ${topic}:`, error);
      throw error;
    }
  }

  // Event listener management
  addEventListener(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  removeEventListener(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  triggerListeners(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('Error in notification listener:', error);
        }
      });
    }
  }

  // Test notification
  async testNotification() {
    if (!this.token) {
      throw new Error('Notification service not initialized');
    }

    try {
      const token = localStorage.getItem('access_token');
      if (!token) {
        throw new Error('No auth token found');
      }

      const response = await axios.post('/api/notifications/send-to-device', {
        token: this.token,
        title: 'Test Notification',
        body: 'This is a test notification from CertiVert',
        data: {
          type: 'test',
          timestamp: new Date().toISOString()
        }
      }, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      return response.data;
    } catch (error) {
      console.error('Failed to send test notification:', error);
      throw error;
    }
  }

  getToken() {
    return this.token;
  }

  isInitialized() {
    return this.token !== null;
  }
}

// Create singleton instance
const notificationService = new NotificationService();

export default notificationService;
