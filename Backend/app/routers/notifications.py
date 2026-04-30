"""
CareSlot — Notifications Router
Endpoints for notifications and reminders.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from app.models.notification import (
    NotificationListResponse, ReminderCreate, ReminderListResponse,
    ReminderResponse, ReminderUpdate,
)
from app.models.user import MessageResponse
from app.config import get_settings
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
        delivery_channels=data.delivery_channels,
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


@router.post("/reminders/process-due")
async def process_due_reminders(request: Request, batch_size: int = 50):
    """Cron endpoint for processing due email/SMS/in-app reminders."""
    settings = get_settings()
    if settings.CRON_SECRET:
        provided = request.headers.get("x-cron-secret")
        if provided != settings.CRON_SECRET:
            raise HTTPException(403, "Invalid cron secret")
    elif settings.APP_ENV.lower() in {"production", "prod"}:
        raise HTTPException(503, "CRON_SECRET must be configured in production")

    service = NotificationService()
    return await service.process_due_reminders(batch_size=batch_size)
