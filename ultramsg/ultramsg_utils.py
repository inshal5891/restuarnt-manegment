"""notifications/ultramsg_utils.py

UltraMsg WhatsApp integration for order notifications.

Environment variables required:
  - ULTRA_INSTANCE: Your UltraMsg instance ID
  - ULTRA_TOKEN: Your UltraMsg API token
  - ADMIN_NUMBER: Admin phone number (format: +country_code_number, e.g., +923001234567)

This module sends WhatsApp messages via UltraMsg API after orders are saved.
All functions are best-effort and log failures without raising exceptions.
"""

from __future__ import annotations

import os
import logging
import requests
from typing import Any, Dict, cast

logger = logging.getLogger("uvicorn.error")

# Environment variables
ULTRA_INSTANCE = os.getenv("ULTRA_INSTANCE")
ULTRA_TOKEN = os.getenv("ULTRA_TOKEN")
ADMIN_NUMBER = os.getenv("ADMIN_NUMBER")


def _validate_ultramsg_config() -> bool:
    """Return True if UltraMsg configuration is complete."""
    if not ULTRA_INSTANCE or not ULTRA_TOKEN or not ADMIN_NUMBER:
        logger.warning(
            "UltraMsg configuration incomplete. Missing: %s",
            [
                "ULTRA_INSTANCE" if not ULTRA_INSTANCE else None,
                "ULTRA_TOKEN" if not ULTRA_TOKEN else None,
                "ADMIN_NUMBER" if not ADMIN_NUMBER else None,
            ],
        )
        return False
    return True


def format_whatsapp(order: Any) -> str:
    """Format an order object into a readable WhatsApp message.

    Args:
        order: SQLAlchemy Order object or dict-like with name, item, phone

    Returns:
        Formatted message string with order details.
    """
    try:
        # Helper to read attribute or dict key safely (helps static analyzers)
        def _get_field(obj: Any, key: str, default: Any = None) -> Any:
            if isinstance(obj, dict):
                d = cast(Dict[str, Any], obj)
                return d.get(key, default)
            return getattr(obj, key, default)

        name = _get_field(order, "name", "Unknown")
        item = _get_field(order, "item", "Unknown")
        phone = _get_field(order, "phone", "Unknown")
        order_id = _get_field(order, "id", "?")

        # Plain-ASCII message to avoid source-encoding/parser issues in some tools
        message = (
            "New Order Received\n"
            "\n"
            f"Customer: {name}\n"
            f"Phone: {phone}\n"
            f"Order ID: {order_id}\n"
            "\n"
            "Order Items:\n"
            f"- {item}\n"
            "\n"
            "Please prepare the order"
        )

        return message
    except Exception as exc:
        logger.exception("Error formatting WhatsApp message: %s", exc)
        return "New Order Received (format error)"


def send_whatsapp_to_admin(message: str, timeout: int = 10) -> Dict[str, Any]:
    """Send a WhatsApp message to the admin using UltraMsg API.

    Args:
        message: The message body to send
        timeout: Request timeout in seconds

    Returns:
        dict with keys: success(bool), message_id(str) on success, error(str) on failure
    """
    if not _validate_ultramsg_config():
        return {"success": False, "error": "UltraMsg configuration missing"}

    # Build UltraMsg endpoint
    endpoint = f"https://api.ultramsg.com/{ULTRA_INSTANCE}/messages/chat"

    payload: Dict[str, Any] = {
        "token": ULTRA_TOKEN,
        "to": ADMIN_NUMBER,
        "body": message,
    }

    try:
        response = requests.post(endpoint, json=payload, timeout=timeout)
        response.raise_for_status()

        result = response.json()
        # UltraMsg returns {"sent":"true", "message":"ok", "id":9}
        # Check if the message was sent successfully
        sent = result.get("sent")
        is_success = (sent == "true" or sent == True)
        
        if is_success:
            message_id = result.get("id", "unknown")
            logger.info("WhatsApp message sent to admin via UltraMsg. ID: %s | Response: %s", message_id, result)
            return {"success": True, "message_id": message_id}
        else:
            error = result.get("message", "Failed to send message")
            logger.error("UltraMsg API failed to send: %s | Full response: %s", error, result)
            return {"success": False, "error": error}

    except requests.exceptions.RequestException as exc:
        logger.exception("Failed to send WhatsApp via UltraMsg: %s", exc)
        return {"success": False, "error": str(exc)}
    except Exception as exc:
        logger.exception("Unexpected error sending WhatsApp: %s", exc)
        return {"success": False, "error": str(exc)}


def send_order_whatsapp(order: Any, timeout: int = 10) -> Dict[str, Any]:
    """Format an order and send it as a WhatsApp message to admin via UltraMsg.

    This is a convenience function that combines format_whatsapp() and send_whatsapp_to_admin().

    Args:
        order: SQLAlchemy Order object or dict-like with order details
        timeout: Request timeout in seconds

    Returns:
        dict with keys: success(bool), message_id(str) on success, error(str) on failure
    """
    try:
        formatted_msg = format_whatsapp(order)
        result = send_whatsapp_to_admin(formatted_msg, timeout=timeout)
        return result
    except Exception as exc:
        logger.exception("Error in send_order_whatsapp: %s", exc)
        return {"success": False, "error": str(exc)}
