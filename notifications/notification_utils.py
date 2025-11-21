# notification_utils.py
"""
Notification utilities for sending WhatsApp messages and push notifications.
Supports Twilio WhatsApp and FCM (Firebase Cloud Messaging) for push notifications.
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from twilio.rest import Client  # type: ignore
import requests

# Configure logger
logger = logging.getLogger("uvicorn.error")

# ============================================================================
# TWILIO WHATSAPP CONFIGURATION
# ============================================================================

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER")
ADMIN_PHONE_NUMBER = os.getenv("ADMIN_PHONE_NUMBER")

# ============================================================================
# FCM (FIREBASE CLOUD MESSAGING) CONFIGURATION
# ============================================================================

FCM_API_KEY = os.getenv("FCM_API_KEY")
FCM_PROJECT_ID = os.getenv("FCM_PROJECT_ID")
ADMIN_FCM_TOKEN = os.getenv("ADMIN_FCM_TOKEN")

FCM_ENDPOINT = "https://fcm.googleapis.com/fcm/send"

# ============================================================================
# PUSHOVER CONFIGURATION (Alternative to FCM)
# ============================================================================

USE_PUSHOVER = os.getenv("USE_PUSHOVER", "false").lower() == "true"
PUSHOVER_API_TOKEN = os.getenv("PUSHOVER_API_TOKEN")
PUSHOVER_USER_KEY = os.getenv("PUSHOVER_USER_KEY")
PUSHOVER_ENDPOINT = "https://api.pushover.net/1/messages.json"


# ============================================================================
# VALIDATION & INITIALIZATION
# ============================================================================

def validate_notification_config() -> Dict[str, bool]:
    """
    Validate that required configuration is set for each notification service.
    Returns a dictionary with service status: {service_name: is_configured}
    """
    config_status = {
        "whatsapp": bool(TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_WHATSAPP_NUMBER and ADMIN_PHONE_NUMBER),
        "fcm": bool(FCM_API_KEY and FCM_PROJECT_ID and ADMIN_FCM_TOKEN),
        "pushover": USE_PUSHOVER and bool(PUSHOVER_API_TOKEN and PUSHOVER_USER_KEY),
    }
    
    logger.info(f"Notification services configured: {config_status}")
    return config_status


# ============================================================================
# TWILIO WHATSAPP FUNCTIONS
# ============================================================================

def send_whatsapp_message(message: str, to_number: Optional[str] = None) -> Dict[str, Any]:
    """
    Send a WhatsApp message via Twilio.
    
    Args:
        message: The message content to send
        to_number: Recipient phone number (defaults to ADMIN_PHONE_NUMBER if not provided)
    
    Returns:
        Dict with 'success' (bool), 'message_sid' (str), 'error' (str if failed)
    """
    recipient = to_number or ADMIN_PHONE_NUMBER
    
    # Validate configuration
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER]):
        logger.error("Twilio WhatsApp not configured. Missing credentials.")
        return {
            "success": False,
            "error": "Twilio WhatsApp is not configured. Set TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_WHATSAPP_NUMBER in .env"
        }
    
    if not recipient:
        logger.error("Admin phone number not set.")
        return {
            "success": False,
            "error": "Admin phone number not configured. Set ADMIN_PHONE_NUMBER in .env"
        }
    
    try:
        # Initialize Twilio client
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        
        # Ensure phone number format: whatsapp:+XXXXXXXXXXX
        recipient_whatsapp = f"whatsapp:{recipient}" if not recipient.startswith("whatsapp:") else recipient
        from_whatsapp = TWILIO_WHATSAPP_NUMBER if TWILIO_WHATSAPP_NUMBER and TWILIO_WHATSAPP_NUMBER.startswith("whatsapp:") else f"whatsapp:{TWILIO_WHATSAPP_NUMBER}"
        
        # Send message
        msg = client.messages.create(
            body=message,
            from_=from_whatsapp,
            to=recipient_whatsapp
        )
        
        logger.info(f"WhatsApp message sent successfully. SID: {msg.sid}")
        return {
            "success": True,
            "message_sid": msg.sid,
            "service": "whatsapp"
        }
    
    except Exception as exc:
        error_msg = f"Failed to send WhatsApp message: {str(exc)}"
        logger.exception(error_msg)
        return {
            "success": False,
            "error": error_msg
        }


# ============================================================================
# FCM PUSH NOTIFICATION FUNCTIONS
# ============================================================================

def send_fcm_notification(title: str, body: str, fcm_token: Optional[str] = None) -> Dict[str, Any]:
    """
    Send a push notification via Firebase Cloud Messaging (FCM).
    
    Args:
        title: Notification title
        body: Notification body/message
        fcm_token: Device FCM token (defaults to ADMIN_FCM_TOKEN if not provided)
    
    Returns:
        Dict with 'success' (bool), 'message_id' (str), 'error' (str if failed)
    """
    recipient_token = fcm_token or ADMIN_FCM_TOKEN
    
    # Validate configuration
    if not FCM_API_KEY:
        logger.warning("FCM API key not configured. Skipping FCM notification.")
        return {
            "success": False,
            "error": "FCM API key not configured. Set FCM_API_KEY in .env"
        }
    
    if not recipient_token:
        logger.warning("Admin FCM token not set. Skipping FCM notification.")
        return {
            "success": False,
            "error": "Admin FCM token not configured. Set ADMIN_FCM_TOKEN in .env"
        }
    
    try:
        headers: Dict[str, str] = {
            "Authorization": f"key={FCM_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload: Dict[str, Any] = {
            "to": recipient_token,
            "notification": {
                "title": title,
                "body": body,
                "click_action": "FLUTTER_NOTIFICATION_CLICK"
            },
            "data": {
                "priority": "high"
            }
        }
        
        response = requests.post(FCM_ENDPOINT, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        if result.get("success"):
            logger.info(f"FCM notification sent successfully. Message ID: {result.get('message_id')}")
            return {
                "success": True,
                "message_id": result.get("message_id"),
                "service": "fcm"
            }
        else:
            error = result.get("error", "Unknown error")
            logger.error(f"FCM API returned error: {error}")
            return {
                "success": False,
                "error": f"FCM error: {error}"
            }
    
    except requests.exceptions.RequestException as exc:
        error_msg = f"Failed to send FCM notification: {str(exc)}"
        logger.exception(error_msg)
        return {
            "success": False,
            "error": error_msg
        }
    
    except Exception as exc:
        error_msg = f"Unexpected error sending FCM notification: {str(exc)}"
        logger.exception(error_msg)
        return {
            "success": False,
            "error": error_msg
        }


# ============================================================================
# PUSHOVER NOTIFICATION FUNCTIONS
# ============================================================================

def send_pushover_notification(message: str, title: str = "Restaurant Admin") -> Dict[str, Any]:
    """
    Send a push notification via Pushover.
    
    Args:
        message: Notification message
        title: Notification title (default: "Restaurant Admin")
    
    Returns:
        Dict with 'success' (bool), 'receipt' (str), 'error' (str if failed)
    """
    # Validate configuration
    if not USE_PUSHOVER:
        return {
            "success": False,
            "error": "Pushover is not enabled. Set USE_PUSHOVER=true in .env"
        }
    
    if not all([PUSHOVER_API_TOKEN, PUSHOVER_USER_KEY]):
        logger.warning("Pushover credentials not configured. Skipping Pushover notification.")
        return {
            "success": False,
            "error": "Pushover credentials not configured. Set PUSHOVER_API_TOKEN and PUSHOVER_USER_KEY in .env"
        }
    
    try:
        payload: Dict[str, Any] = {
            "token": PUSHOVER_API_TOKEN,
            "user": PUSHOVER_USER_KEY,
            "title": title,
            "message": message,
            "priority": 1  # High priority
        }
        
        response = requests.post(PUSHOVER_ENDPOINT, data=payload, timeout=10)
        response.raise_for_status()
        
        result = response.json()
        if result.get("status") == 1:
            logger.info(f"Pushover notification sent successfully. Receipt: {result.get('receipt')}")
            return {
                "success": True,
                "receipt": result.get("receipt"),
                "service": "pushover"
            }
        else:
            error = result.get("errors", ["Unknown error"])[0]
            logger.error(f"Pushover API returned error: {error}")
            return {
                "success": False,
                "error": f"Pushover error: {error}"
            }
    
    except requests.exceptions.RequestException as exc:
        error_msg = f"Failed to send Pushover notification: {str(exc)}"
        logger.exception(error_msg)
        return {
            "success": False,
            "error": error_msg
        }
    
    except Exception as exc:
        error_msg = f"Unexpected error sending Pushover notification: {str(exc)}"
        logger.exception(error_msg)
        return {
            "success": False,
            "error": error_msg
        }


# ============================================================================
# UNIFIED NOTIFICATION FUNCTION
# ============================================================================

def send_unified_notification(message: str, title: str = "Restaurant Admin", **kwargs: Any) -> Dict[str, Any]:
    """
    Send notifications across all configured channels (WhatsApp + Push).
    
    Args:
        message: Message content
        title: Notification title (for push notifications)
        **kwargs: Additional arguments (e.g., to_number, fcm_token)
    
    Returns:
        Dict with results from all services
    """
    results: Dict[str, Any] = {
        "overall_success": False,
        "services": {},
        "timestamp": None
    }
    
    results["timestamp"] = datetime.now(timezone.utc).isoformat()
    
    # Send WhatsApp
    whatsapp_result = send_whatsapp_message(message, kwargs.get("to_number"))
    results["services"]["whatsapp"] = whatsapp_result
    
    # Send FCM
    fcm_result = send_fcm_notification(title, message, kwargs.get("fcm_token"))
    results["services"]["fcm"] = fcm_result
    
    # Send Pushover (if enabled)
    if USE_PUSHOVER:
        pushover_result = send_pushover_notification(message, title)
        results["services"]["pushover"] = pushover_result
    
    # Overall success if at least one service succeeded
    results["overall_success"] = any(
        result.get("success", False) 
        for result in results["services"].values()
    )
    
    logger.info(f"Unified notification sent. Overall success: {results['overall_success']}")
    return results
