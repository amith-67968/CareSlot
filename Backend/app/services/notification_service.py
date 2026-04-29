"""
CareSlot — Notification & Reminder Service
Manages notifications and scheduled reminders.
"""

from app.services.supabase_service import SupabaseService
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self):
        self.supabase = SupabaseService()

    async def create_notification(self, user_id: str, title: str, body: str,
                                   notif_type: str = "general", reference_id: str = None) -> Dict:
        data = {
            "user_id": user_id, "title": title, "body": body,
            "type": notif_type, "is_read": False, "reference_id": reference_id,
        }
        result = self.supabase.insert("notifications", data)
        return result[0] if result else None

    async def get_notifications(self, user_id: str, limit: int = 50) -> Dict:
        notifs = self.supabase.select("notifications", filters={"user_id": user_id},
                                       order_by="-created_at", limit=limit)
        unread = sum(1 for n in notifs if not n.get("is_read", False))
        return {"notifications": notifs, "total": len(notifs), "unread_count": unread}

    async def mark_as_read(self, user_id: str, notification_id: str) -> Dict:
        result = self.supabase.update("notifications", {"is_read": True},
                                       {"id": notification_id, "user_id": user_id})
        return result[0] if result else None

    async def create_reminder(self, user_id: str, title: str, reminder_type: str,
                               scheduled_at: datetime, description: str = None,
                               reference_id: str = None, recurrence: str = "none") -> Dict:
        data = {
            "user_id": user_id, "title": title, "description": description,
            "reminder_type": reminder_type, "scheduled_at": scheduled_at.isoformat(),
            "status": "pending", "reference_id": reference_id, "recurrence": recurrence,
        }
        result = self.supabase.insert("reminders", data)
        return result[0] if result else None

    async def get_reminders(self, user_id: str, status: str = None) -> Dict:
        filters = {"user_id": user_id}
        if status:
            filters["status"] = status
        reminders = self.supabase.select("reminders", filters=filters, order_by="scheduled_at")
        return {"reminders": reminders, "total": len(reminders)}

    async def update_reminder(self, user_id: str, reminder_id: str, data: Dict) -> Dict:
        update = {k: v for k, v in data.items() if v is not None}
        if "scheduled_at" in update and isinstance(update["scheduled_at"], datetime):
            update["scheduled_at"] = update["scheduled_at"].isoformat()
        result = self.supabase.update("reminders", update, {"id": reminder_id, "user_id": user_id})
        return result[0] if result else None

    async def cancel_reminder(self, user_id: str, reminder_id: str) -> Dict:
        return await self.update_reminder(user_id, reminder_id, {"status": "cancelled"})
