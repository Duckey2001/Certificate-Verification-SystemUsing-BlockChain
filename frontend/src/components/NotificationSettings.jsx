import React, { useState, useEffect } from 'react';
import notificationService from '../services/NotificationService';
import { Bell, BellOff, Check, X, Settings } from 'lucide-react';

const NotificationSettings = () => {
  const [isSupported, setIsSupported] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const [permission, setPermission] = useState('default');
  const [isLoading, setIsLoading] = useState(false);
  const [testResult, setTestResult] = useState(null);
  const [topics, setTopics] = useState({
    certificate_updates: false,
    payment_notifications: false,
    system_alerts: false
  });

  useEffect(() => {
    // Check notification support
    const supported = 'Notification' in window && 'serviceWorker' in navigator;
    setIsSupported(supported);

    if (supported) {
      // Check current permission
      setPermission(Notification.permission);
      
      // Check if service is initialized
      setIsInitialized(notificationService.isInitialized());

      // Listen for permission changes
      const handlePermissionChange = () => {
        setPermission(Notification.permission);
      };

      Notification.requestPermission().then(handlePermissionChange);
    }
  }, []);

  const handleInitializeNotifications = async () => {
    setIsLoading(true);
    setTestResult(null);

    try {
      const success = await notificationService.initialize();
      setIsInitialized(success);
      
      if (success) {
        setPermission(Notification.permission);
        setTestResult({
          type: 'success',
          message: 'Notifications initialized successfully!'
        });
      } else {
        setTestResult({
          type: 'error',
          message: 'Failed to initialize notifications'
        });
      }
    } catch (error) {
      setTestResult({
        type: 'error',
        message: error.message
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleTestNotification = async () => {
    setIsLoading(true);
    setTestResult(null);

    try {
      await notificationService.testNotification();
      setTestResult({
        type: 'success',
        message: 'Test notification sent! Check your notifications.'
      });
    } catch (error) {
      setTestResult({
        type: 'error',
        message: error.message
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleTopicToggle = async (topic, enabled) => {
    setIsLoading(true);
    
    try {
      if (enabled) {
        await notificationService.subscribeToTopic(topic);
      } else {
        await notificationService.unsubscribeFromTopic(topic);
      }
      
      setTopics(prev => ({
        ...prev,
        [topic]: enabled
      }));
      
      setTestResult({
        type: 'success',
        message: `Successfully ${enabled ? 'subscribed to' : 'unsubscribed from'} ${topic}`
      });
    } catch (error) {
      setTestResult({
        type: 'error',
        message: error.message
      });
    } finally {
      setIsLoading(false);
    }
  };

  const requestPermission = async () => {
    setIsLoading(true);
    
    try {
      const result = await Notification.requestPermission();
      setPermission(result);
      
      if (result === 'granted') {
        setTestResult({
          type: 'success',
          message: 'Notification permission granted!'
        });
      } else {
        setTestResult({
          type: 'error',
          message: 'Notification permission denied'
        });
      }
    } catch (error) {
      setTestResult({
        type: 'error',
        message: error.message
      });
    } finally {
      setIsLoading(false);
    }
  };

  if (!isSupported) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
        <div className="flex items-center space-x-3">
          <BellOff className="w-6 h-6 text-yellow-600" />
          <div>
            <h3 className="text-lg font-medium text-yellow-800">Notifications Not Supported</h3>
            <p className="text-yellow-700">
              Your browser doesn't support push notifications. Please use a modern browser like Chrome, Firefox, or Safari.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-3">
          <Settings className="w-6 h-6 text-gray-600" />
          <h2 className="text-xl font-semibold text-gray-800">Notification Settings</h2>
        </div>
        <div className={`px-3 py-1 rounded-full text-sm font-medium ${
          isInitialized ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'
        }`}>
          {isInitialized ? 'Active' : 'Inactive'}
        </div>
      </div>

      {/* Permission Status */}
      <div className="mb-6">
        <h3 className="text-lg font-medium text-gray-700 mb-3">Permission Status</h3>
        <div className="flex items-center space-x-3">
          <div className={`w-3 h-3 rounded-full ${
            permission === 'granted' ? 'bg-green-500' : 
            permission === 'denied' ? 'bg-red-500' : 'bg-yellow-500'
          }`} />
          <span className="text-gray-600 capitalize">{permission}</span>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="space-y-3 mb-6">
        {permission === 'default' && (
          <button
            onClick={requestPermission}
            disabled={isLoading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? 'Requesting...' : 'Enable Notifications'}
          </button>
        )}

        {permission === 'granted' && !isInitialized && (
          <button
            onClick={handleInitializeNotifications}
            disabled={isLoading}
            className="w-full bg-green-600 text-white py-2 px-4 rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? 'Initializing...' : 'Initialize Notifications'}
          </button>
        )}

        {isInitialized && (
          <button
            onClick={handleTestNotification}
            disabled={isLoading}
            className="w-full bg-indigo-600 text-white py-2 px-4 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? 'Sending...' : 'Send Test Notification'}
          </button>
        )}
      </div>

      {/* Topic Subscriptions */}
      {isInitialized && (
        <div className="mb-6">
          <h3 className="text-lg font-medium text-gray-700 mb-3">Notification Topics</h3>
          <div className="space-y-3">
            {Object.entries({
              certificate_updates: 'Certificate Updates',
              payment_notifications: 'Payment Notifications',
              system_alerts: 'System Alerts'
            }).map(([key, label]) => (
              <div key={key} className="flex items-center justify-between">
                <span className="text-gray-600">{label}</span>
                <button
                  onClick={() => handleTopicToggle(key, !topics[key])}
                  disabled={isLoading}
                  className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                    topics[key] ? 'bg-blue-600' : 'bg-gray-200'
                  } disabled:opacity-50 disabled:cursor-not-allowed`}
                >
                  <span
                    className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                      topics[key] ? 'translate-x-6' : 'translate-x-1'
                    }`}
                  />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Test Result */}
      {testResult && (
        <div className={`rounded-lg p-4 ${
          testResult.type === 'success' ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
        }`}>
          <div className="flex items-center space-x-2">
            {testResult.type === 'success' ? (
              <Check className="w-5 h-5 text-green-600" />
            ) : (
              <X className="w-5 h-5 text-red-600" />
            )}
            <span className={`text-sm ${
              testResult.type === 'success' ? 'text-green-800' : 'text-red-800'
            }`}>
              {testResult.message}
            </span>
          </div>
        </div>
      )}

      {/* Info */}
      <div className="mt-6 p-4 bg-blue-50 rounded-lg">
        <div className="flex items-start space-x-3">
          <Bell className="w-5 h-5 text-blue-600 mt-0.5" />
          <div className="text-sm text-blue-800">
            <p className="font-medium mb-1">About Notifications</p>
            <p>
              Enable notifications to receive real-time updates about certificate verifications, 
              payment confirmations, and important system alerts directly in your browser.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default NotificationSettings;
