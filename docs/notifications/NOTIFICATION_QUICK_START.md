# Quick Start - Notification System

## API Endpoints Summary

### 1. **Check Service Status**
```bash
curl http://127.0.0.1:8001/notify/health
```
Returns which notification services are configured.

---

### 2. **Send Unified Notification** (WhatsApp + Push)
```bash
curl -X POST "http://127.0.0.1:8001/notify/" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Your message here",
    "title": "Optional Title"
  }'
```

---

### 3. **Send WhatsApp Only**
```bash
curl -X POST "http://127.0.0.1:8001/notify/whatsapp" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "WhatsApp message"
  }'
```

---

### 4. **Send Push Notification Only** (FCM or Pushover)
```bash
curl -X POST "http://127.0.0.1:8001/notify/push" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Push notification",
    "title": "Title"
  }'
```

---

## Setup Checklist

### ✓ For WhatsApp Notifications
- [ ] Create Twilio account (https://www.twilio.com/)
- [ ] Set up WhatsApp sandbox
- [ ] Copy `TWILIO_ACCOUNT_SID` to `.env`
- [ ] Copy `TWILIO_AUTH_TOKEN` to `.env`
- [ ] Set `TWILIO_WHATSAPP_NUMBER` (e.g., `whatsapp:+1234567890`)
- [ ] Set `ADMIN_PHONE_NUMBER` (your phone number)

### ✓ For Push Notifications (FCM)
- [ ] Create Firebase project (https://console.firebase.google.com/)
- [ ] Download service account key
- [ ] Extract `FCM_API_KEY`
- [ ] Copy `FCM_PROJECT_ID`
- [ ] Get admin device `ADMIN_FCM_TOKEN`

### ✓ For Push Notifications (Pushover - Optional)
- [ ] Create Pushover account (https://pushover.net/)
- [ ] Create application
- [ ] Set `USE_PUSHOVER=true`
- [ ] Copy `PUSHOVER_API_TOKEN`
- [ ] Copy `PUSHOVER_USER_KEY`

---

## Environment Variables

```bash
# Twilio WhatsApp
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+1234567890
ADMIN_PHONE_NUMBER=+923001234567

# Firebase FCM
FCM_API_KEY=your_api_key
FCM_PROJECT_ID=your_project_id
ADMIN_FCM_TOKEN=your_device_token

# Pushover (optional)
USE_PUSHOVER=false
PUSHOVER_API_TOKEN=your_token
PUSHOVER_USER_KEY=your_key
```

---

## Python Integration Example

### Send notification when order is created:

```python
from notifications.notification_utils import send_unified_notification

@app.post("/order", response_model=OrderCreated, status_code=201)
def post_order(payload: OrderIn) -> Dict[str, Any]:
    order = create_order(payload.name, payload.item, payload.phone)
    
    # Send notification
    send_unified_notification(
        message=f"New order: {order.item} from {order.name}",
        title="New Restaurant Order"
    )
    
    return {"id": order.id, "status": "created"}
```

---

## Test the System

```bash
# Run tests
python test_notifications.py

# Check logs while testing
python -m uvicorn main:app --reload --log-level debug
```

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| "No notification services configured" | Add credentials to `.env` |
| "Twilio WhatsApp not configured" | Check TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN |
| "FCM API key not configured" | Check FCM_API_KEY in `.env` |
| "Admin phone number not set" | Set ADMIN_PHONE_NUMBER |
| "Admin FCM token not configured" | Get FCM token from device |

---

**For detailed setup, see: `NOTIFICATION_SETUP.md`**
