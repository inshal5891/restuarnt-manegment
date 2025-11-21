# notification_schemas.py
"""
Pydantic models for notification requests and responses.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class NotificationRequest(BaseModel):
    """Schema for POST /notify request"""
    message: str = Field(..., min_length=1, max_length=1000, description="Notification message content")
    title: Optional[str] = Field(None, max_length=100, description="Notification title (for push notifications)")
    to_number: Optional[str] = Field(None, description="Override default admin phone number")
    fcm_token: Optional[str] = Field(None, description="Override default FCM token")


class NotificationResponse(BaseModel):
    """Schema for notification API response"""
    overall_success: bool
    services: Dict[str, Dict[str, Any]]
    timestamp: str
    message: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """Schema for health check endpoint response"""
    status: str
    services_configured: Dict[str, bool]
    timestamp: str
