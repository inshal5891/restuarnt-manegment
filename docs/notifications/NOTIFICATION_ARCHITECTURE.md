# Notification System Architecture

## System Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│                         CLIENT/EXTERNAL                          │
│  HTTP Request: POST /notify/                                     │
└───────────────────────┬──────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────────┐
│                    FASTAPI APPLICATION                           │
│                  notifications/notification_routes.py            │
│                                                                  │
│  Endpoints:                                                      │
│  - GET  /notify/health                                           │
│  - POST /notify/                                                 │
│  - POST /notify/whatsapp                                         │
│  - POST /notify/push                                             │
└───────────────────────┬──────────────────────────────────────────┘
                        │
                        ▼
┌──────────────────────────────────────────────────────────────────┐
│          notifications/notification_utils.py                     │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ send_unified_notification()                              │   │
│  │ - Routes to all configured services                      │   │
│  └──────────────────────────────────────────────────────────┘   │
│                        │                                          │
│       ┌────────────────┼────────────────┐                        │
│       ▼                ▼                ▼                        │
│    WhatsApp          FCM           Pushover                     │
│   (Twilio)       (Firebase)       (Optional)                    │
└──────┬──────────────┬──────────────┬──────────────────────────────┘
       │              │              │
       ▼              ▼              ▼
  ┌─────────┐    ┌─────────┐   ┌──────────┐
  │ Twilio  │    │Firebase │   │Pushover  │
  │ API     │    │ FCM API │   │API       │
  └─────────┘    └─────────┘   └──────────┘
       │              │              │
       ▼              ▼              ▼
  Admin's        Admin's        Admin's
  WhatsApp       Phone App      Device
```

---

## File Structure

```
restaurant-backend/
├── main.py                              # FastAPI app with routes
├── notifications/                       # Notification package
│   ├── __init__.py                      # Package exports
│   ├── notification_routes.py           # API endpoints
│   ├── notification_utils.py            # Core logic
│   ├── notification_schemas.py          # Pydantic models
│   ├── sms_utils.py                     # SMS utilities
│   └── README.md                        # Module docs
├── docs/notifications/                  # Documentation
│   ├── NOTIFICATION_SYSTEM_OVERVIEW.md
│   ├── NOTIFICATION_SETUP.md
│   ├── NOTIFICATION_QUICK_START.md
│   ├── NOTIFICATION_ARCHITECTURE.md
│   └── NOTIFICATION_API_REFERENCE.md
├── test_notifications.py                # Test suite
├── .env                                 # Config (not committed)
└── .env.example                         # Config template
```

---

## Data Flow - Unified Notification

```
1. Client sends: POST /notify/
   {
     "message": "New order received",
     "title": "Restaurant Order"
   }

2. FastAPI validates with Pydantic schema
   - Check message length (1-1000 chars)
   - Check title length (max 100 chars)

3. Route handler calls send_unified_notification()

4. send_unified_notification():
   ├─ Calls send_whatsapp_message()
   │  └─ Uses Twilio to send via WhatsApp
   │
   ├─ Calls send_fcm_notification()
   │  └─ Uses Firebase FCM to send push
   │
   └─ Calls send_pushover_notification()
      └─ Uses Pushover (if enabled)

5. Aggregate results:
   {
     "overall_success": true,
     "services": {
       "whatsapp": {...},
       "fcm": {...},
       "pushover": {...}
     }
   }

6. Return 200 if at least one service succeeded
```

---

## Configuration Hierarchy

```
.env (Environment Variables)
    ├─ TWILIO_ACCOUNT_SID
    ├─ TWILIO_AUTH_TOKEN
    ├─ TWILIO_WHATSAPP_NUMBER
    ├─ ADMIN_PHONE_NUMBER
    ├─ FCM_API_KEY
    ├─ FCM_PROJECT_ID
    ├─ ADMIN_FCM_TOKEN
    ├─ USE_PUSHOVER
    ├─ PUSHOVER_API_TOKEN
    └─ PUSHOVER_USER_KEY
         ↓
    notification_utils.py
    (os.getenv() loads variables)
         ↓
    validate_notification_config()
    (Checks which services available)
         ↓
    send_*_notification() functions
    (Use credentials to call APIs)
```

---

## Error Handling Flow

```
User Request
    ↓
Validate Payload (Pydantic)
    ├─ Invalid → 400 Bad Request
    │
    ├─ Valid ↓
    Check Service Config
    ├─ No Services → 503 Service Unavailable
    │
    ├─ Services Available ↓
    Send to Each Service (try-catch)
    ├─ Each failure logged, doesn't stop others
    │
    ├─ Aggregate Results ↓
    At least one success?
    ├─ Yes → 200 OK (with results)
    ├─ No  → 500 Internal Server Error
```

---

## Service Integration Points

### Twilio WhatsApp
```python
from twilio.rest import Client

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
msg = client.messages.create(
    body=message,
    from_=TWILIO_WHATSAPP_NUMBER,
    to=recipient_whatsapp
)
```

### Firebase FCM
```python
import requests

headers = {
    "Authorization": f"key={FCM_API_KEY}",
    "Content-Type": "application/json"
}
response = requests.post(FCM_ENDPOINT, json=payload, headers=headers)
```

### Pushover
```python
import requests

payload = {
    "token": PUSHOVER_API_TOKEN,
    "user": PUSHOVER_USER_KEY,
    "message": message
}
response = requests.post(PUSHOVER_ENDPOINT, data=payload)
```

---

## Response Flow

### Success Case
```
HTTP 200 OK
{
  "overall_success": true,
  "services": {
    "whatsapp": {
      "success": true,
      "message_sid": "SMxxxxxxx",
      "service": "whatsapp"
    },
    "fcm": {
      "success": true,
      "message_id": "0:1234567",
      "service": "fcm"
    }
  },
  "timestamp": "2025-11-12T12:34:56",
  "message": "Notification sent successfully"
}
```

### Error Cases
```
400 Bad Request   → Invalid schema/payload
422 Unprocessable → Validation error
500 Server Error  → All services failed
503 Unavailable   → No services configured
```

---

**Architecture Version**: 1.0.0  
**Last Updated**: November 2025  
**Status**: Production Ready ✅
