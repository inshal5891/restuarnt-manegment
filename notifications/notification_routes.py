# notification_routes.py
"""
API endpoints for sending notifications.
Includes WhatsApp and push notification endpoints.
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from .notification_utils import (
    send_unified_notification,
    validate_notification_config
)
from .notification_schemas import NotificationRequest, NotificationResponse, HealthCheckResponse

# Initialize router
router = APIRouter(prefix="/notify", tags=["Notifications"])

# Configure logger
logger = logging.getLogger("uvicorn.error")


# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

@router.get("/health", response_model=HealthCheckResponse)
def notification_health_check() -> Dict[str, Any]:
    """
    Check if notification services are configured and healthy.
    
    Returns:
        HealthCheckResponse with service status
    """
    services_status = validate_notification_config()
    
    return {
        "status": "healthy" if any(services_status.values()) else "no_services_configured",
        "services_configured": services_status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


# ============================================================================
# MAIN NOTIFICATION ENDPOINT
# ============================================================================

@router.post("/", response_model=NotificationResponse, status_code=200)
def send_notification(payload: NotificationRequest) -> Dict[str, Any]:
    """
    Send a notification to admin via WhatsApp and/or push notification.
    
    This endpoint sends the message through all configured notification channels:
    - WhatsApp (via Twilio)
    - Firebase Cloud Messaging (FCM)
    - Pushover (optional)
    
    Args:
        payload: NotificationRequest with message and optional overrides
    
    Returns:
        NotificationResponse with results from each service
    
    Raises:
        HTTPException 503: If no notification services are configured
    """
    
    # Validate that at least one service is configured
    services_config = validate_notification_config()
    if not any(services_config.values()):
        logger.error("No notification services configured")
        raise HTTPException(
            status_code=503,
            detail="No notification services are configured. Set up Twilio WhatsApp, FCM, or Pushover credentials in .env"
        )
    
    try:
        # Send notification through unified function
        result = send_unified_notification(
            message=payload.message,
            title=payload.title or "Restaurant Admin",
            to_number=payload.to_number,
            fcm_token=payload.fcm_token
        )
        
        if result["overall_success"]:
            return {
                "overall_success": result["overall_success"],
                "services": result["services"],
                "timestamp": result["timestamp"],
                "message": "Notification sent successfully"
            }
        else:
            logger.warning("All notification services failed")
            raise HTTPException(
                status_code=500,
                detail="Failed to send notification through all configured services"
            )
    
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error sending unified notification")
        raise HTTPException(
            status_code=500,
            detail=f"Notification error: {str(exc)}"
        )


# ============================================================================
# WHATSAPP ONLY ENDPOINT
# ============================================================================

@router.post("/whatsapp", status_code=200)
def send_whatsapp_only(payload: NotificationRequest) -> Dict[str, Any]:
    """
    Send a message via WhatsApp only (skips push notifications).
    
    Args:
        payload: NotificationRequest with message
    
    Returns:
        Dict with WhatsApp send result
    """
    
    try:
        from .notification_utils import send_whatsapp_message
        
        result = send_whatsapp_message(
            message=payload.message,
            to_number=payload.to_number
        )
        
        if result["success"]:
            return {
                "success": True,
                "service": "whatsapp",
                "message_sid": result.get("message_sid"),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to send WhatsApp message")
            )
    
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error sending WhatsApp message")
        raise HTTPException(
            status_code=500,
            detail=f"WhatsApp error: {str(exc)}"
        )


# ============================================================================
# PUSH NOTIFICATION ONLY ENDPOINT
# ============================================================================

@router.post("/push", status_code=200)
def send_push_only(payload: NotificationRequest) -> Dict[str, Any]:
    """
    Send notification via push notification only (skips WhatsApp).
    
    Supports FCM (Firebase Cloud Messaging) and/or Pushover.
    
    Args:
        payload: NotificationRequest with message and title
    
    Returns:
        Dict with push notification results
    """
    
    try:
        from .notification_utils import send_fcm_notification, send_pushover_notification, USE_PUSHOVER
        
        results = {}
        
        # Try FCM first
        fcm_result = send_fcm_notification(
            title=payload.title or "Restaurant Admin",
            body=payload.message,
            fcm_token=payload.fcm_token
        )
        results["fcm"] = fcm_result
        
        # Try Pushover if enabled
        if USE_PUSHOVER:
            pushover_result = send_pushover_notification(
                message=payload.message,
                title=payload.title or "Restaurant Admin"
            )
            results["pushover"] = pushover_result
        
        # Check if any succeeded
        any_success = any(r.get("success", False) for r in results.values())  # type: ignore
        
        if not any_success:
            raise HTTPException(
                status_code=500,
                detail="Failed to send push notification through all available services"
            )
        
        return {
            "success": True,
            "services": results,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Error sending push notification")
        raise HTTPException(
            status_code=500,
            detail=f"Push notification error: {str(exc)}"
        )
