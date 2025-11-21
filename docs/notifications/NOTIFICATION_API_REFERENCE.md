# Notification API - Complete Reference

## Base URL
```
http://127.0.0.1:8001/notify
```

---

## Endpoints

### 1. Health Check

**Endpoint:** `GET /notify/health`

**Response:**
```json
{
  "status": "healthy",
  "services_configured": {
    "whatsapp": true,
    "fcm": false,
    "pushover": false
  },
  "timestamp": "2025-11-12T12:34:56.789123"
}
```

---

### 2. Send Unified Notification

**Endpoint:** `POST /notify/`

**Request Body:**
```json
{
  "message": "Your message here",
  "title": "Optional notification title",
  "to_number": "+923001234567",
  "fcm_token": "optional_device_token_override"
}
```

**Response:**
```json
{
  "overall_success": true,
  "services": {
    "whatsapp": {
      "success": true,
      "message_sid": "SMxxxxxxxxxxxxxxxxxxxxxxxx",
      "service": "whatsapp"
    },
    "fcm": {
      "success": true,
      "message_id": "0:1234567890123456789",
      "service": "fcm"
    }
  },
  "timestamp": "2025-11-12T12:34:56.789123",
  "message": "Notification sent successfully"
}
```

---

### 3. Send WhatsApp Only

**Endpoint:** `POST /notify/whatsapp`

**Request Body:**
```json
{
  "message": "Your WhatsApp message"
}
```

**Response:**
```json
{
  "success": true,
  "service": "whatsapp",
  "message_sid": "SMxxxxxxxxxxxxxxxxxxxxxxxx",
  "timestamp": "2025-11-12T12:34:56.789123"
}
```

---

### 4. Send Push Notification Only

**Endpoint:** `POST /notify/push`

**Request Body:**
```json
{
  "message": "Your notification message",
  "title": "Notification Title"
}
```

**Response:**
```json
{
  "success": true,
  "services": {
    "fcm": {
      "success": true,
      "message_id": "0:1234567890123456789",
      "service": "fcm"
    }
  },
  "timestamp": "2025-11-12T12:34:56.789123"
}
```

---

## Error Codes Reference

| Code | Meaning | Solution |
|------|---------|----------|
| 200 | Success | Notification delivered via at least one service |
| 400 | Bad Request | Check JSON syntax and required fields |
| 422 | Unprocessable Entity | Invalid field types or values |
| 500 | Internal Server Error | All services failed or unexpected error |
| 503 | Service Unavailable | No notification services configured |

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| "No notification services configured" | Add credentials to .env |
| "Twilio WhatsApp not configured" | Check TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN |
| "Admin phone number not set" | Set ADMIN_PHONE_NUMBER in .env |
| "FCM API key not configured" | Check FCM_API_KEY in .env |
| "Admin FCM token not configured" | Get FCM token from device |

---

## Python Integration

```python
import requests

# Send notification
response = requests.post(
    "http://127.0.0.1:8001/notify/",
    json={
        "message": "New order!",
        "title": "Restaurant"
    }
)

print(response.status_code)  # 200
print(response.json())
```

---

**API Version**: 1.0.0  
**Last Updated**: November 2025  
**Status**: Production Ready ✅
