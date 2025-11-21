"""notifications/email_utils.py

Supabase insertion and SMTP email notification helpers.

This module uses environment variables:
  - SUPABASE_URL
  - SUPABASE_API_KEY
  - ADMIN_EMAIL (recipient)
  - EMAIL_PASSWORD (SMTP login password)

Optional environment variables (have sensible defaults):
  - SMTP_HOST (default: smtp.gmail.com)
  - SMTP_PORT (default: 587)
  - SENDER_EMAIL (default: ADMIN_EMAIL)

The Supabase insertion uses the PostgREST endpoint at <SUPABASE_URL>/rest/v1/orders
and authenticates with the API key in the headers. We use requests directly to avoid
adding a third-party supabase client dependency.

All functions are small, well-documented and return structured dict results so callers
can decide what to do on failure.
"""
from __future__ import annotations

import os
import logging
import requests
import smtplib
from email.message import EmailMessage
from typing import Any, Dict, cast

logger = logging.getLogger("uvicorn.error")

# Required environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_API_KEY = os.getenv("SUPABASE_API_KEY")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Optional SMTP settings with sensible defaults
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL") or ADMIN_EMAIL


def _validate_supabase_config() -> bool:
    """Return True if Supabase config appears present."""
    if not SUPABASE_URL or not SUPABASE_API_KEY:
        logger.warning("Supabase configuration missing (SUPABASE_URL / SUPABASE_API_KEY).")
        return False
    return True


def _validate_smtp_config() -> bool:
    """Return True if SMTP configuration appears present."""
    if not ADMIN_EMAIL or not EMAIL_PASSWORD or not SENDER_EMAIL:
        logger.warning("SMTP configuration missing (ADMIN_EMAIL / EMAIL_PASSWORD / SENDER_EMAIL).")
        return False
    return True


def insert_order_to_supabase(order: Any, timeout: int = 10) -> Dict[str, Any]:
    """Insert an order into Supabase `orders` table using the REST endpoint.

    Args:
        order: SQLAlchemy Order object or a mapping with attributes/keys: name, item, phone, status
        timeout: request timeout in seconds

    Returns:
        dict with keys: success(bool), row(dict) when success, error(str) when failed
    """
    if not _validate_supabase_config():
        return {"success": False, "error": "Supabase configuration missing"}

    # Build payload from object or mapping
    try:
        def _get_field(obj: Any, key: str, default: Any = None) -> Any:
            if isinstance(obj, dict):
                d = cast(Dict[str, Any], obj)
                return d.get(key, default)
            return getattr(obj, key, default)

        payload: Dict[str, Any] = {
            "name": _get_field(order, "name", None),
            "item": _get_field(order, "item", None),
            "phone": _get_field(order, "phone", None),
            "status": _get_field(order, "status", None),
        }
    except Exception as exc:
        logger.exception("Failed to construct Supabase payload: %s", exc)
        return {"success": False, "error": f"payload construction error: {exc}"}

    # Basic validation
    if not payload["name"] or not payload["item"]:
        return {"success": False, "error": "order payload missing required fields"}

    # At this point we validated SUPABASE_URL is present; copy to local var for type-checkers
    db_url = SUPABASE_URL
    assert db_url is not None
    endpoint = db_url.rstrip("/") + "/rest/v1/orders"
    # SUPABASE_API_KEY is validated above; assert for type-checkers
    assert SUPABASE_API_KEY is not None
    headers: Dict[str, str] = {
        "apikey": SUPABASE_API_KEY,
        "Authorization": f"Bearer {SUPABASE_API_KEY}",
        "Content-Type": "application/json",
        # Ask PostgREST to return the inserted row representation
        "Prefer": "return=representation",
    }

    try:
        resp = requests.post(endpoint, json=payload, headers=headers, timeout=timeout)
        resp.raise_for_status()
        # Supabase returns an array of inserted rows when using return=representation
        data: Any = resp.json()
        if isinstance(data, list) and data:
            inserted = cast(Dict[str, Any], data[0])
        else:
            inserted = cast(Dict[str, Any], data)

        logger.info("Inserted order into Supabase orders table: %s", inserted)
        return {"success": True, "row": inserted}

    except requests.exceptions.RequestException as exc:
        logger.exception("Supabase insert request failed: %s", exc)
        return {"success": False, "error": str(exc)}
    except Exception as exc:
        logger.exception("Unexpected error inserting to Supabase: %s", exc)
        return {"success": False, "error": str(exc)}


def send_order_email(order_row: Dict[str, Any], subject_prefix: str = "New order") -> Dict[str, Any]:
    """Send an email about a newly created order to ADMIN_EMAIL using smtplib.

    Args:
        order_row: mapping with order details (id, name, item, phone, status, ...)
        subject_prefix: prefix for the email subject

    Returns:
        dict with keys: success(bool), error(str) when failed
    """
    if not _validate_smtp_config():
        return {"success": False, "error": "SMTP configuration missing"}

    # Tell static type checkers these are str (they are validated above)
    assert SENDER_EMAIL is not None
    assert EMAIL_PASSWORD is not None

    # Compose the email
    try:
        order_id = order_row.get("id")
        name = order_row.get("name")
        item = order_row.get("item")
        phone = order_row.get("phone")
        status = order_row.get("status")

        subject = f"{subject_prefix}: {item} from {name} (id={order_id})"
        body_lines = [
            f"Order ID: {order_id}",
            f"Name: {name}",
            f"Item: {item}",
            f"Phone: {phone}",
            f"Status: {status}",
        ]
        body = "\n".join(body_lines)

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = SENDER_EMAIL
        msg["To"] = ADMIN_EMAIL
        msg.set_content(body)

        # Send via SMTP with STARTTLS
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as smtp:
            smtp.ehlo()
            # Use STARTTLS if available (most providers support it)
            try:
                smtp.starttls()
                smtp.ehlo()
            except Exception:
                logger.debug("STARTTLS not available or failed; continuing without it.")

            # Login with sender credentials. We assume sender email is the SMTP username.
            smtp.login(SENDER_EMAIL, EMAIL_PASSWORD)
            smtp.send_message(msg)

        logger.info("Order notification email sent to %s for order id=%s", ADMIN_EMAIL, order_id)
        return {"success": True}

    except smtplib.SMTPException as exc:
        logger.exception("Failed to send email via SMTP: %s", exc)
        return {"success": False, "error": str(exc)}
    except Exception as exc:
        logger.exception("Unexpected error sending order email: %s", exc)
        return {"success": False, "error": str(exc)}
