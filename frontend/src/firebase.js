// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getMessaging, getToken, onMessage } from "firebase/messaging";
import { getAnalytics } from "firebase/analytics";

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: "AIzaSyBCqsILSyXatW4dv4F1N0Ik00nyd9nnX64",
  authDomain: "certivert-25289.firebaseapp.com",
  projectId: "certivert-25289",
  storageBucket: "certivert-25289.firebasestorage.app",
  messagingSenderId: "674326105550",
  appId: "1:674326105550:web:b225ffecb57fb3508f6f9f",
  measurementId: "G-W7JWVT63H2"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);

// Initialize Firebase Cloud Messaging
const messaging = getMessaging(app);

// VAPID key for web push notifications
const VAPID_KEY = "BB9Jbr7pI1VFnqp1P7rmfnygiCTHb1Kmfxle6rVGBq66gjLAlj0yv6BuCwYfPuOVX8FQCA3a7ptuFdnXrcwWRtE";

// Request notification permission and get token
export const requestNotificationPermission = async () => {
  try {
    const permission = await Notification.requestPermission();
    if (permission === 'granted') {
      console.log('Notification permission granted.');
      const token = await getToken(messaging, { vapidKey: VAPID_KEY });
      return token;
    } else {
      console.log('Unable to get permission to notify.');
      return null;
    }
  } catch (error) {
    console.error('Error requesting notification permission:', error);
    return null;
  }
};

// Handle incoming messages
export const onMessageListener = () =>
  new Promise((resolve) => {
    onMessage(messaging, (payload) => {
      resolve(payload);
    });
  });

// Export Firebase instances
export { app, messaging, analytics };
