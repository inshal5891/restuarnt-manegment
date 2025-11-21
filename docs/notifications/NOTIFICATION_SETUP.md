# Restaurant Backend - Notification System Setup Guide

This guide explains how to set up the WhatsApp and push notification features.

## Overview

The notification system supports three channels:
1. **WhatsApp** (via Twilio)
2. **Firebase Cloud Messaging (FCM)** - Mobile push notifications
3. **Pushover** - Desktop/Mobile push notifications

---

## 1. WhatsApp Setup (Twilio)

### Steps

#### 1.1: Create a Twilio Account
1. Sign up at https://www.twilio.com/
2. Complete the verification process
3. Go to **Twilio Console** > **Messaging** > **Try it out**

#### 1.2: Set Up WhatsApp Sandbox
1. Navigate to **Messaging** > **Whatsapp** > **Sandbox**
2. Note your sandbox number (e.g., `whatsapp:+14155238886`)
3. Copy your **Account SID** from the console dashboard
4. Copy your **Auth Token** from the console dashboard
5. Join the sandbox by sending `join XXXX-YYYY` to the sandbox number

#### 1.3: Update `.env`
```bash
TWILIO_ACCOUNT_SID=your_account_sid_here
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
ADMIN_PHONE_NUMBER=+923001234567
```

#### 1.4: Test WhatsApp
```bash
curl -X POST "http://127.0.0.1:8001/notify/whatsapp" \
  -H "Content-Type: application/json" \
  -d '{"message": "Test WhatsApp message!"}'
```

---

## 2. Firebase Cloud Messaging (FCM) Setup

### Steps

#### 2.1: Create a Firebase Project
1. Go to https://console.firebase.google.com/
2. Click **Create a new project**
3. Enter project name (e.g., "Restaurant Backend")
4. Follow the setup wizard

#### 2.2: Get FCM Credentials
1. In Firebase Console, go to **Project Settings** (⚙️ icon)
2. Select **Service Accounts** tab
3. Click **Generate New Private Key**
4. A JSON file will download - open it
5. Look for `"api_key"` value - this is your **FCM_API_KEY**
6. Copy your **Project ID** from the settings page

#### 2.3: Get Admin FCM Token
For the admin to receive notifications, you need their device FCM token:

**Option A: Android App**
```kotlin
FirebaseMessaging.getInstance().token.addOnCompleteListener { task ->
    if (task.isSuccessful) {
        val token = task.result
        Log.d("FCM", "Token: $token")
    }
}
```

**Option B: Web App (Firebase SDK)**
```javascript
import { getMessaging, getToken } from "firebase/messaging";

const messaging = getMessaging();
getToken(messaging).then((token) => {
  console.log('FCM Token:', token);
});
```

#### 2.4: Update `.env`
```bash
FCM_API_KEY=your_fcm_api_key_here
FCM_PROJECT_ID=your_firebase_project_id_here
ADMIN_FCM_TOKEN=your_admin_device_token_here
```

#### 2.5: Test FCM
```bash
curl -X POST "http://127.0.0.1:8001/notify/push" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Test FCM notification!",
    "title": "Restaurant Admin"
  }'
```

---

## 3. Pushover Setup (Optional)

#### 3.1: Create Pushover Account
1. Sign up at https://pushover.net/
2. Create an application
3. Copy the **Application/API Token**

#### 3.2: Get User Key
1. Go to your Pushover account page
2. Copy your **User Key**
3. Install Pushover app on your device

#### 3.3: Update `.env`
```bash
USE_PUSHOVER=true
PUSHOVER_API_TOKEN=your_app_token_here
PUSHOVER_USER_KEY=your_user_key_here
```

---

## API Endpoints

### 1. Health Check
```bash
curl http://127.0.0.1:8001/notify/health
```

### 2. Send Unified Notification
```bash
curl -X POST "http://127.0.0.1:8001/notify/" \
  -d '{"message":"Hello","title":"Test"}'
```

### 3. WhatsApp Only
```bash
curl -X POST "http://127.0.0.1:8001/notify/whatsapp" \
  -d '{"message":"WhatsApp message"}'
```

### 4. Push Only
```bash
curl -X POST "http://127.0.0.1:8001/notify/push" \
  -d '{"message":"Push message","title":"Title"}'
```

---

## Integration with Order System

Update `main.py`:

```python
from notifications.notification_utils import send_unified_notification

@app.post("/order", response_model=OrderCreated, status_code=201)
def post_order(payload: OrderIn) -> Dict[str, Any]:
    try:
        order = create_order(payload.name, payload.item, payload.phone)
    except RuntimeError as exc:
        logger.exception("Failed to create order")
        raise HTTPException(status_code=500, detail=str(exc))

    # Send notification to admin
    try:
        send_unified_notification(
            message=f"New order: {order.item} from {order.name}\nPhone: {order.phone}",
            title="New Order"
        )
    except Exception:
        logger.exception("Failed to send notification")

    return {"id": order.id, "status": "created"}
```

---

## Security Best Practices

1. **Never commit `.env` to git** - Use `.env.example` as template
2. **Rotate API keys regularly** - Set up key rotation in Firebase/Twilio
3. **Use environment variables** - Never hardcode credentials
4. **Monitor API usage** - Check Twilio/Firebase usage in dashboards
5. **Rate limit** - Consider adding rate limiting to `/notify` endpoints
6. **Validate input** - The API already validates message length (max 1000 chars)
7. **Use HTTPS in production** - Ensure API is only accessible via HTTPS

---

## Support & Resources

- **Twilio**: https://www.twilio.com/docs/sms/whatsapp-business-model
- **Firebase**: https://firebase.google.com/docs/cloud-messaging
- **Pushover**: https://pushover.net/api

---

**Last Updated**: November 2025
