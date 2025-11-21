# notifications/__init__.py
"""
Notification system for restaurant backend.
Supports WhatsApp (Twilio), Firebase FCM, and Pushover.
"""

from .notification_utils import (
    send_whatsapp_message,
    send_fcm_notification,
    send_pushover_notification,
    send_unified_notification,
    validate_notification_config,
)

__all__ = [
    "send_whatsapp_message",
    "send_fcm_notification",
    "send_pushover_notification",
    "send_unified_notification",
    "validate_notification_config",
]
