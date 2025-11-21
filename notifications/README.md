# notifications/ - Notification System Module

This folder contains all SMS and notification-related utilities for the restaurant backend.

## 📁 Files

### Core Modules
- **`__init__.py`** - Package initialization and exports
- **`notification_utils.py`** - Core notification logic (WhatsApp, FCM, Pushover)
- **`notification_schemas.py`** - Pydantic models for validation
- **`notification_routes.py`** - FastAPI endpoints
- **`sms_utils.py`** - SMS utilities (placeholder for production SMS)

## 🚀 Usage

### From main.py or other modules:

```python
# Import SMS utilities
from notifications.sms_utils import send_sms

# Send SMS
send_sms("+923001234567", "Your message here")
```

```python
# Import notification utilities
from notifications.notification_utils import send_unified_notification

# Send notification to all channels
send_unified_notification(
    message="New order received!",
    title="Order Alert"
)
```

```python
# Import specific functions
from notifications import (
    send_whatsapp_message,
    send_fcm_notification,
    send_pushover_notification,
    send_unified_notification,
    validate_notification_config,
)
```

## 📊 Configuration

All notification services are configured via environment variables in `.env`:

```bash
# Twilio WhatsApp
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+1234567890
ADMIN_PHONE_NUMBER=+923001234567

# Firebase FCM
FCM_API_KEY=your_key
FCM_PROJECT_ID=your_project
ADMIN_FCM_TOKEN=your_device_token

# Pushover (optional)
USE_PUSHOVER=false
PUSHOVER_API_TOKEN=your_token
PUSHOVER_USER_KEY=your_key
```

## 🔌 API Endpoints

The notification routes are registered in `main.py` under `/notify/`:

- `GET /notify/health` - Check service configuration
- `POST /notify/` - Send via all services
- `POST /notify/whatsapp` - WhatsApp only
- `POST /notify/push` - Push notifications only

## 📚 Documentation

For detailed setup and usage instructions, see:
- `../NOTIFICATION_QUICK_START.md` - Quick start guide
- `../NOTIFICATION_SETUP.md` - Complete setup instructions
- `../NOTIFICATION_API_REFERENCE.md` - API documentation

## 🧪 Testing

Run tests from project root:
```bash
python test_notifications.py
```

## 🛠️ Extending

### Adding a New Service

1. Create a new function in `notification_utils.py`
2. Add validation to `validate_notification_config()`
3. Create new endpoint in `notification_routes.py` if needed
4. Add environment variables to `.env`
5. Update documentation

### Adding SMS Provider

To use real SMS (Twilio SMS):

```python
# In sms_utils.py
from twilio.rest import Client

def send_sms(to_phone: str, message: str) -> None:
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    client.messages.create(
        body=message,
        from_='+1234567890',  # Your Twilio number
        to=to_phone
    )
```

## 📦 Dependencies

- `twilio>=9.0.0` - WhatsApp and SMS
- `firebase-admin>=6.0.0` - FCM push notifications
- `requests>=2.28.0` - HTTP requests for Pushover
- `fastapi>=0.100.0` - API framework
- `pydantic>=2.0.0` - Data validation

## ✨ Features

- **WhatsApp** - Send messages via Twilio WhatsApp Business API
- **Push Notifications** - Firebase Cloud Messaging (FCM)
- **Desktop Notifications** - Pushover API (optional)
- **SMS** - Placeholder for SMS integration
- **Health Check** - Verify service configuration
- **Error Handling** - Comprehensive error management
- **Logging** - Debug and error logging

## 🔒 Security

- All credentials stored in environment variables
- No secrets in code or logs
- Input validation with Pydantic
- Safe error messages

---

**Last Updated**: November 12, 2025  
**Version**: 1.0.0  
**Status**: Production Ready ✅
