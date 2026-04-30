"""
CareSlot — Notification & Reminder Service
Manages notifications and scheduled reminders.
"""

from app.services.supabase_service import SupabaseService
from app.config import get_settings
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from email.message import EmailMessage
import smtplib
import httpx
import logging

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self):
        self.supabase = SupabaseService()
        self.settings = get_settings()

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
                               reference_id: str = None, recurrence: str = "none",
                               delivery_channels: Optional[List[str]] = None) -> Dict:
        data = {
            "user_id": user_id, "title": title, "description": description,
            "reminder_type": reminder_type, "scheduled_at": scheduled_at.isoformat(),
            "status": "pending", "reference_id": reference_id, "recurrence": recurrence,
            "delivery_channels": delivery_channels or ["email"],
        }
        try:
            result = self.supabase.insert("reminders", data)
        except Exception as exc:
            logger.warning("Enhanced reminder insert failed, retrying legacy schema: %s", exc)
            data.pop("delivery_channels", None)
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

    def cancel_reminders_for_reference(self, user_id: str, reference_id: str) -> None:
        """Cancel pending reminders linked to an appointment/prediction."""
        try:
            (
                self.supabase.admin.table("reminders")
                .update({"status": "cancelled"})
                .eq("user_id", user_id)
                .eq("reference_id", reference_id)
                .eq("status", "pending")
                .execute()
            )
        except Exception as exc:
            logger.warning("Could not cancel reminders for reference %s: %s", reference_id, exc)

    async def process_due_reminders(self, batch_size: int = 50) -> Dict[str, Any]:
        """Send due reminders through in-app notification, email, and SMS."""
        now = datetime.now(timezone.utc).isoformat()
        response = (
            self.supabase.admin.table("reminders")
            .select("*")
            .eq("status", "pending")
            .lte("scheduled_at", now)
            .limit(batch_size)
            .execute()
        )
        reminders = response.data or []

        processed = 0
        failures = 0
        delivery = []

        for reminder in reminders:
            try:
                profile = self._get_recipient_profile(reminder["user_id"])
                appointment = self._get_reference_appointment(reminder.get("reference_id"))
                if appointment and appointment.get("status") in {"cancelled", "completed", "no-show"}:
                    self._update_reminder_delivery(
                        reminder["id"],
                        "cancelled",
                        {"email_status": "skipped", "sms_status": "skipped"},
                    )
                    continue
                message = self._build_reminder_message(reminder, appointment)
                channel_result = await self._deliver_reminder(reminder, profile, message)
                self._raise_for_required_email_failure(reminder, channel_result)

                await self.create_notification(
                    user_id=reminder["user_id"],
                    title=reminder["title"],
                    body=message,
                    notif_type=reminder.get("reminder_type", "appointment"),
                    reference_id=reminder.get("reference_id"),
                )

                self._update_reminder_delivery(reminder["id"], "sent", channel_result)
                self._mark_appointment_reminded(reminder.get("reference_id"))
                processed += 1
                delivery.append({"id": reminder["id"], **channel_result})
            except Exception as exc:
                failures += 1
                logger.error("Reminder processing failed for %s: %s", reminder.get("id"), exc)
                self._update_reminder_delivery(
                    reminder["id"],
                    "pending",
                    {"last_error": str(exc), "email_status": "failed", "sms_status": "failed"},
                )

        return {"processed": processed, "failures": failures, "delivery": delivery}

    async def _deliver_reminder(self, reminder: Dict[str, Any], profile: Dict[str, Any], message: str) -> Dict[str, str]:
        channels = reminder.get("delivery_channels") or ["email"]
        result = {"email_status": "skipped", "sms_status": "skipped"}

        if "email" in channels and profile.get("email"):
            result["email_status"] = await self._send_email(profile["email"], reminder["title"], message)
        elif "email" in channels:
            result["email_status"] = "skipped"

        if "sms" in channels and profile.get("phone"):
            result["sms_status"] = await self._send_sms(profile["phone"], message)

        return result

    async def _send_email(self, to_email: str, subject: str, body: str) -> str:
        if not self.settings.ENABLE_EMAIL_NOTIFICATIONS:
            return "disabled"
        provider = (self.settings.EMAIL_PROVIDER or "smtp").strip().lower()
        if provider == "resend":
            return await self._send_email_resend(to_email, subject, body)
        if provider != "smtp":
            logger.error("Unsupported email provider configured: %s", provider)
            return "not_configured"

        return await self._send_email_smtp(to_email, subject, body)

    async def _send_email_resend(self, to_email: str, subject: str, body: str) -> str:
        if not self.settings.RESEND_API_KEY:
            return "not_configured"

        try:
            async with httpx.AsyncClient(timeout=15.0, trust_env=False) as client:
                response = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {self.settings.RESEND_API_KEY}",
                        "User-Agent": "CareSlot/1.0",
                    },
                    json={
                        "from": self.settings.SMTP_FROM_EMAIL,
                        "to": [to_email],
                        "subject": subject,
                        "text": body,
                    },
                )
                response.raise_for_status()
            return "sent"
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Resend email reminder failed (%s): %s",
                exc.response.status_code,
                exc.response.text,
            )
            return "failed"
        except Exception as exc:
            logger.error("Resend email reminder failed: %s", exc)
            return "failed"

    async def _send_email_smtp(self, to_email: str, subject: str, body: str) -> str:
        if not self.settings.SMTP_HOST:
            return "not_configured"

        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.settings.SMTP_FROM_EMAIL
        msg["To"] = to_email
        msg.set_content(body)

        try:
            smtp_cls = smtplib.SMTP_SSL if self.settings.SMTP_PORT == 465 else smtplib.SMTP
            with smtp_cls(self.settings.SMTP_HOST, self.settings.SMTP_PORT, timeout=15) as smtp:
                if self.settings.SMTP_PORT != 465:
                    smtp.starttls()
                if self.settings.SMTP_USERNAME:
                    smtp.login(self.settings.SMTP_USERNAME, self.settings.SMTP_PASSWORD)
                smtp.send_message(msg)
            return "sent"
        except Exception as exc:
            logger.error("Email reminder failed: %s", exc)
            return "failed"

    async def _send_sms(self, to_phone: str, body: str) -> str:
        if not self.settings.ENABLE_SMS_NOTIFICATIONS:
            return "disabled"
        if not all([self.settings.TWILIO_ACCOUNT_SID, self.settings.TWILIO_AUTH_TOKEN, self.settings.TWILIO_FROM_NUMBER]):
            return "not_configured"

        url = f"https://api.twilio.com/2010-04-01/Accounts/{self.settings.TWILIO_ACCOUNT_SID}/Messages.json"
        try:
            async with httpx.AsyncClient(timeout=15.0, trust_env=False) as client:
                response = await client.post(
                    url,
                    data={"From": self.settings.TWILIO_FROM_NUMBER, "To": to_phone, "Body": body},
                    auth=(self.settings.TWILIO_ACCOUNT_SID, self.settings.TWILIO_AUTH_TOKEN),
                )
                response.raise_for_status()
            return "sent"
        except Exception as exc:
            logger.error("SMS reminder failed: %s", exc)
            return "failed"

    def _raise_for_required_email_failure(self, reminder: Dict[str, Any], delivery: Dict[str, str]) -> None:
        channels = reminder.get("delivery_channels") or ["email"]
        email_status = delivery.get("email_status")
        if "email" not in channels or email_status in {"sent", "disabled"}:
            return
        if self.settings.ENABLE_EMAIL_NOTIFICATIONS and email_status in {"failed", "not_configured", "skipped"}:
            raise RuntimeError(f"Email reminder was not sent: {email_status}")

    def _build_reminder_message(self, reminder: Dict[str, Any], appointment: Optional[Dict[str, Any]]) -> str:
        if appointment:
            return (
                f"Your appointment with {appointment.get('doctor_name', 'your doctor')} at "
                f"{appointment.get('hospital_name', 'the hospital')} is scheduled for "
                f"{str(appointment.get('appointment_time', ''))[:5]} today."
            )
        return reminder.get("description") or f"Reminder: {reminder['title']}"

    def _get_recipient_profile(self, user_id: str) -> Dict[str, Any]:
        """Resolve email/phone using profile first, then Supabase Auth registered email."""
        profile = {}
        try:
            profile = self.supabase.select_one("user_profiles", filters={"user_id": user_id}) or {}
        except Exception:
            profile = {}

        if profile.get("email"):
            return profile

        try:
            auth_response = self.supabase.admin.auth.admin.get_user_by_id(user_id)
            auth_user = getattr(auth_response, "user", None) or auth_response
            auth_email = getattr(auth_user, "email", None)
            if auth_email:
                profile["email"] = auth_email
        except Exception as exc:
            logger.warning("Could not resolve Supabase Auth email for reminder user %s: %s", user_id, exc)

        return profile

    def _get_reference_appointment(self, reference_id: Optional[str]) -> Optional[Dict[str, Any]]:
        if not reference_id:
            return None
        try:
            return self.supabase.select_one("appointments", filters={"id": reference_id})
        except Exception:
            return None

    def _update_reminder_delivery(self, reminder_id: str, status: str, delivery: Dict[str, Any]) -> None:
        update = {
            "status": status,
            "sent_at": datetime.now(timezone.utc).isoformat() if status == "sent" else None,
            "email_status": delivery.get("email_status"),
            "sms_status": delivery.get("sms_status"),
            "last_error": delivery.get("last_error"),
        }
        update = {k: v for k, v in update.items() if v is not None}
        try:
            self.supabase.admin.table("reminders").update(update).eq("id", reminder_id).execute()
        except Exception:
            legacy = {"status": status}
            self.supabase.admin.table("reminders").update(legacy).eq("id", reminder_id).execute()

    def _mark_appointment_reminded(self, appointment_id: Optional[str]) -> None:
        if not appointment_id:
            return
        try:
            self.supabase.admin.table("appointments").update({"reminder_status": "sent"}).eq("id", appointment_id).execute()
        except Exception:
            pass
