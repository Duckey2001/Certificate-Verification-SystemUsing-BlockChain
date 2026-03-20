import requests
import os
from dotenv import load_dotenv

load_dotenv()

class RealSMSGateway:
    """Real SMS Gateway for sending actual SMS to phones"""
    
    def __init__(self):
        # You can choose from these SMS providers:
        # 1. Africa's Talking (recommended for Africa)
        # 2. Twilio (global)
        # 3. Clickatell (global)
        
        self.provider = os.getenv('SMS_PROVIDER', 'africas_talking')  # Default
        self.api_key = os.getenv('AFRICAS_TALKING_API_KEY')
        self.username = os.getenv('AFRICAS_TALKING_USERNAME')
        self.from_number = os.getenv('SMS_FROM_NUMBER', 'ECOL')
        
    def send_sms(self, phone_number, message):
        """Send real SMS to phone number"""
        
        # Clean phone number - ensure it has +266 format
        if not phone_number.startswith('+'):
            if phone_number.startswith('266'):
                phone_number = '+' + phone_number
            else:
                phone_number = '+266' + phone_number
        
        print(f"\n{'='*60}")
        print(f"📤 SENDING REAL SMS TO: {phone_number}")
        print(f"📝 MESSAGE: {message[:100]}...")
        print(f"🔧 PROVIDER: {self.provider}")
        print(f"{'='*60}\n")
        
        if self.provider == 'africas_talking':
            return self._send_africas_talking(phone_number, message)
        elif self.provider == 'twilio':
            return self._send_twilio(phone_number, message)
        else:
            return self._send_clickatell(phone_number, message)
    
    def _send_africas_talking(self, phone_number, message):
        """Send SMS via Africa's Talking"""
        try:
            url = f"https://api.africastalking.com/version1/messaging"
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Accept': 'application/json',
                'apiKey': self.api_key
            }
            
            data = {
                'username': self.username,
                'to': phone_number,
                'message': message,
                'from': self.from_number
            }
            
            response = requests.post(url, headers=headers, data=data)
            
            if response.status_code == 201:
                result = response.json()
                sms_id = result['SMSMessageData']['Recipients'][0]['messageId']
                print(f"✅ SMS sent successfully! ID: {sms_id}")
                return {
                    "status": "sent",
                    "message_id": sms_id,
                    "provider": "africas_talking"
                }
            else:
                print(f"❌ Failed to send SMS: {response.text}")
                return {"status": "failed", "error": response.text}
                
        except Exception as e:
            print(f"❌ SMS sending error: {e}")
            return {"status": "failed", "error": str(e)}
    
    def _send_twilio(self, phone_number, message):
        """Send SMS via Twilio"""
        try:
            from twilio.rest import Client
            
            account_sid = os.getenv('TWILIO_ACCOUNT_SID')
            auth_token = os.getenv('TWILIO_AUTH_TOKEN')
            twilio_number = os.getenv('TWILIO_PHONE_NUMBER')
            
            client = Client(account_sid, auth_token)
            
            message = client.messages.create(
                body=message,
                from_=twilio_number,
                to=phone_number
            )
            
            print(f"✅ SMS sent successfully! ID: {message.sid}")
            return {
                "status": "sent",
                "message_id": message.sid,
                "provider": "twilio"
            }
            
        except Exception as e:
            print(f"❌ Twilio SMS error: {e}")
            return {"status": "failed", "error": str(e)}
    
    def _send_clickatell(self, phone_number, message):
        """Send SMS via Clickatell"""
        try:
            url = f"https://platform.clickatell.com/messages"
            
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f"Bearer {os.getenv('CLICKATELL_API_KEY')}"
            }
            
            data = {
                'content': message,
                'to': [phone_number],
                'from': os.getenv('CLICKATELL_FROM_NUMBER')
            }
            
            response = requests.post(url, headers=headers, json=data)
            
            if response.status_code == 202:
                result = response.json()
                print(f"✅ SMS sent successfully! ID: {result['messages'][0]['messageId']}")
                return {
                    "status": "sent",
                    "message_id": result['messages'][0]['messageId'],
                    "provider": "clickatell"
                }
            else:
                print(f"❌ Failed to send SMS: {response.text}")
                return {"status": "failed", "error": response.text}
                
        except Exception as e:
            print(f"❌ Clickatell SMS error: {e}")
            return {"status": "failed", "error": str(e)}
