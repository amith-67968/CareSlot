"""
CareSlot — Appointment Service
CRUD operations for appointment booking and management.
"""

from app.services.supabase_service import SupabaseService
from app.services.notification_service import NotificationService
from typing import Dict, Any, Optional, List
from datetime import date, time, datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class AppointmentService:
    def __init__(self):
        self.supabase = SupabaseService()
        self.notification_service = NotificationService()

    async def create_appointment(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        appointment_data = {
            "user_id": user_id,
            "doctor_name": data["doctor_name"],
            "doctor_specialty": data.get("doctor_specialty"),
            "hospital_name": data["hospital_name"],
            "hospital_address": data.get("hospital_address"),
            "hospital_place_id": data.get("hospital_place_id"),
            "appointment_date": str(data["appointment_date"]),
            "appointment_time": str(data["appointment_time"]),
            "consultation_type": data.get("consultation_type", "in-person"),
            "status": "scheduled",
            "notes": data.get("notes"),
        }
        result = self.supabase.insert("appointments", appointment_data)
        appointment = result[0] if result else None

        if appointment:
            try:
                apt_dt = datetime.combine(data["appointment_date"], data["appointment_time"])
                await self.notification_service.create_reminder(
                    user_id=user_id,
                    title=f"Reminder: Dr. {data['doctor_name']}",
                    description=f"At {data['hospital_name']} in 1 hour",
                    reminder_type="appointment",
                    scheduled_at=apt_dt - timedelta(hours=1),
                    reference_id=appointment["id"],
                )
            except Exception as e:
                logger.error(f"Reminder creation failed: {e}")
        return appointment

    async def get_appointments(self, user_id: str, status: Optional[str] = None) -> List[Dict]:
        filters = {"user_id": user_id}
        if status:
            filters["status"] = status
        return self.supabase.select("appointments", filters=filters, order_by="-appointment_date")

    async def get_appointment(self, user_id: str, appointment_id: str) -> Optional[Dict]:
        return self.supabase.select_one("appointments", filters={"id": appointment_id, "user_id": user_id})

    async def update_appointment(self, user_id: str, appointment_id: str, data: Dict) -> Optional[Dict]:
        update_data = {k: (str(v) if isinstance(v, (date, time)) else v) for k, v in data.items() if v is not None}
        if not update_data:
            return await self.get_appointment(user_id, appointment_id)
        update_data["updated_at"] = datetime.utcnow().isoformat()
        result = self.supabase.update("appointments", update_data, {"id": appointment_id, "user_id": user_id})
        return result[0] if result else None

    async def cancel_appointment(self, user_id: str, appointment_id: str) -> Optional[Dict]:
        return await self.update_appointment(user_id, appointment_id, {"status": "cancelled"})

    async def get_available_slots(self, appointment_date: date, **kwargs) -> Dict:
        slots = [{"time": str(time(h, m)), "available": True} for h in range(9, 18) for m in (0, 30)]
        return {"date": str(appointment_date), "slots": slots}
