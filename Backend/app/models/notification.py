"""
CareSlot — Notification & Reminder Pydantic Models
Request/response schemas for notifications and reminders.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class NotificationType(str, Enum):
    APPOINTMENT = "appointment"
    FOLLOW_UP = "follow_up"
    MEDICINE = "medicine"
    HEALTH_CHECK = "health_check"
    GENERAL = "general"


class ReminderType(str, Enum):
    APPOINTMENT = "appointment"
    FOLLOW_UP = "follow_up"
    MEDICINE = "medicine"
    HEALTH_CHECK = "health_check"


class ReminderStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    CANCELLED = "cancelled"


class Recurrence(str, Enum):
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


# ─── Notification Schemas ─────────────────────────────────────────────

class NotificationResponse(BaseModel):
    """Single notification record."""
    id: str
    user_id: str
    title: str
    body: str
    type: str
    is_read: bool = False
    reference_id: Optional[str] = None
    created_at: Optional[datetime] = None

class NotificationListResponse(BaseModel):
    """List of notifications."""
    notifications: List[NotificationResponse]
    total: int
    unread_count: int


# ─── Reminder Schemas ─────────────────────────────────────────────────

class ReminderCreate(BaseModel):
    """Create a new reminder."""
    title: str = Field(..., min_length=2)
    description: Optional[str] = None
    reminder_type: ReminderType
    scheduled_at: datetime
    reference_id: Optional[str] = Field(None, description="Linked appointment/prediction ID")
    recurrence: Recurrence = Recurrence.NONE
    delivery_channels: List[str] = Field(default_factory=lambda: ["email"])

class ReminderUpdate(BaseModel):
    """Update an existing reminder."""
    title: Optional[str] = None
    description: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    status: Optional[ReminderStatus] = None
    recurrence: Optional[Recurrence] = None

class ReminderResponse(BaseModel):
    """Single reminder record."""
    id: str
    user_id: str
    title: str
    description: Optional[str] = None
    reminder_type: str
    scheduled_at: datetime
    status: str
    reference_id: Optional[str] = None
    recurrence: str = "none"
    delivery_channels: Optional[List[str]] = None
    email_status: Optional[str] = None
    sms_status: Optional[str] = None
    sent_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

class ReminderListResponse(BaseModel):
    """List of reminders."""
    reminders: List[ReminderResponse]
    total: int
