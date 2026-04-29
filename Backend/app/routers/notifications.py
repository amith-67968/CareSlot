"""
CareSlot — Notifications Router
Endpoints for notifications and reminders.
"""

from fastapi import APIRouter, Depends
from app.models.notification import (
    NotificationListResponse, ReminderCreate, ReminderListResponse,
    ReminderResponse, ReminderUpdate,
)
from app.models.user import MessageResponse
from app.services.notification_service import NotificationService
from app.dependencies import get_current_user
from typing import Optional

router = APIRouter(prefix="/api/notifications", tags=["Notifications & Reminders"])


@router.get("/", response_model=NotificationListResponse)
async def get_notifications(limit: int = 50, user: dict = Depends(get_current_user)):
    """Get user's notifications."""
    service = NotificationService()
    return await service.get_notifications(user["user_id"], limit=limit)


@router.put("/{notification_id}/read", response_model=MessageResponse)
async def mark_notification_read(notification_id: str, user: dict = Depends(get_current_user)):
    """Mark a notification as read."""
    service = NotificationService()
    await service.mark_as_read(user["user_id"], notification_id)
    return MessageResponse(message="Notification marked as read")


@router.post("/reminders", response_model=ReminderResponse, status_code=201)
async def create_reminder(data: ReminderCreate, user: dict = Depends(get_current_user)):
    """Create a new reminder."""
    service = NotificationService()
    result = await service.create_reminder(
        user_id=user["user_id"],
        title=data.title,
        reminder_type=data.reminder_type.value,
        scheduled_at=data.scheduled_at,
        description=data.description,
        reference_id=data.reference_id,
        recurrence=data.recurrence.value,
    )
    return result


@router.get("/reminders", response_model=ReminderListResponse)
async def get_reminders(status: Optional[str] = None, user: dict = Depends(get_current_user)):
    """Get user's reminders."""
    service = NotificationService()
    return await service.get_reminders(user["user_id"], status=status)


@router.put("/reminders/{reminder_id}/cancel", response_model=MessageResponse)
async def cancel_reminder(reminder_id: str, user: dict = Depends(get_current_user)):
    """Cancel a reminder."""
    service = NotificationService()
    await service.cancel_reminder(user["user_id"], reminder_id)
    return MessageResponse(message="Reminder cancelled")
