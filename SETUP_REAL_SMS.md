# 📱 Real SMS Setup Guide

## Current Status: ✅ SMS System Ready
The popup is working and the system can send SMS. Currently using **simulation mode** (SMS shown in console).

## 🚀 To Send Real SMS to Your Phone:

### Option 1: Africa's Talking (Recommended for Africa)
1. **Sign up**: https://www.africastalking.com/
2. **Get credentials**:
   - Username (your account username)
   - API Key (from dashboard)
3. **Update .env file**:
   ```env
   SMS_PROVIDER=africas_talking
   AFRICAS_TALKING_USERNAME=your_actual_username
   AFRICAS_TALKING_API_KEY=your_actual_api_key
   SMS_FROM_NUMBER=ECOL
   ```

### Option 2: Twilio (Global)
1. **Sign up**: https://www.twilio.com/
2. **Get credentials**:
   - Account SID
   - Auth Token  
   - Phone number (buy a number)
3. **Update .env file**:
   ```env
   SMS_PROVIDER=twilio
   TWILIO_ACCOUNT_SID=your_account_sid
   TWILIO_AUTH_TOKEN=your_auth_token
   TWILIO_PHONE_NUMBER=+1234567890
   ```

### Option 3: Clickatell (Global)
1. **Sign up**: https://www.clickatell.com/
2. **Get API Key** from dashboard
3. **Update .env file**:
   ```env
   SMS_PROVIDER=clickatell
   CLICKATELL_API_KEY=your_api_key
   CLICKATELL_FROM_NUMBER=ECOL
   ```

## 🔧 After Setup:

1. **Stop current server**: `lsof -ti:5000 | xargs kill -9`
2. **Restart server**: `source mpesa_env/bin/activate && python sms_mpesa_payment.py`
3. **Test**: Open `http://127.0.0.1:5000/simple_phone_popup.html`

## 📱 What Happens:

1. **Enter phone**: `+26657620256` in popup
2. **Click "Send SMS"**: Real SMS sent to your phone
3. **Check your phone**: You'll receive SMS with PIN
4. **Reply to SMS**: Send the PIN back
5. **Payment processed**: Confirmation SMS sent

## 💰 Cost:
- **Africa's Talking**: ~$0.007 per SMS (very cheap)
- **Twilio**: ~$0.08 per SMS 
- **Clickatell**: ~$0.05 per SMS

## 🎯 Quick Test:
For immediate testing, use **Africa's Talking** - they have free trial credits and work well in Lesotho!

**🚀 Once configured, you'll receive real SMS on your phone!**
