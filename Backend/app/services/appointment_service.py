"""
CareSlot - Appointment service.
Production-oriented booking flow with direct hospital APIs and internal fallback.
"""

from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Any, Dict, List, Optional
import logging

from app.services.doctor_service import DoctorService
from app.services.hospital_integration_service import (
    HospitalIntegrationService,
    SPECIALTY_LABELS,
)
from app.services.notification_service import NotificationService
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


class AppointmentService:
    def __init__(self):
        self.supabase = SupabaseService()
        self.notification_service = NotificationService()
        self.doctor_service = DoctorService()
        self.integration_service = HospitalIntegrationService()

    async def find_nearby_hospitals(
        self,
        latitude: float,
        longitude: float,
        specialty: Optional[str],
        radius: int,
        keyword: Optional[str],
    ) -> Dict[str, Any]:
        """Return nearby hospitals enriched with booking capabilities."""
        maps_result = await self.doctor_service.find_nearby_hospitals(
            latitude=latitude,
            longitude=longitude,
            specialty=specialty,
            radius=radius,
            keyword=keyword,
        )
        enriched = []
        for hospital in maps_result.get("results", []):
            capabilities = self.integration_service.get_capabilities(hospital.get("place_id"))
            enriched.append(
                {
                    **hospital,
                    "specialties_available": self.integration_service.departments_for_specialty(specialty),
                    "booking_mode": capabilities["booking_mode"],
                    "integration_label": capabilities["label"],
                    "supports_real_time_slots": capabilities["supports_real_time_slots"],
                    "requires_staff_confirmation": capabilities["requires_staff_confirmation"],
                }
            )

        return {
            **maps_result,
            "results": enriched,
            "total": len(enriched),
        }

    async def get_hospital_doctors(
        self,
        place_id: str,
        specialty: Optional[str] = None,
        hospital_name: Optional[str] = None,
        hospital_address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return doctors for a selected hospital through direct API or fallback catalog."""
        details = await self.doctor_service.get_place_details(place_id)
        hospital = {
            "place_id": place_id,
            "name": details.get("name") or hospital_name or "Selected Hospital",
            "address": details.get("address") or hospital_address or "",
            "location": details.get("location") or {"latitude": 0, "longitude": 0},
            "rating": details.get("rating"),
            "total_ratings": None,
            "is_open_now": details.get("is_open_now"),
            "distance_text": None,
            "specialty_match": specialty,
            "photos": details.get("photos", []),
            "specialties_available": self.integration_service.departments_for_specialty(specialty),
        }
        doctor_result = await self.integration_service.fetch_doctors(hospital, specialty)
        capabilities = doctor_result["capabilities"]
        hospital.update(
            {
                "booking_mode": capabilities["booking_mode"],
                "integration_label": capabilities["label"],
                "supports_real_time_slots": capabilities["supports_real_time_slots"],
                "requires_staff_confirmation": capabilities["requires_staff_confirmation"],
            }
        )
        return {
            "hospital": hospital,
            "doctors": doctor_result["doctors"],
            "booking_mode": doctor_result["booking_mode"],
            "capabilities": capabilities,
        }

    async def create_appointment(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Book an appointment inside CareSlot with direct API or fallback handling."""
        patient_profile = self._get_patient_profile(user_id)
        hospital_place_id = data.get("hospital_place_id")
        appointment_payload = self._build_external_payload(user_id, patient_profile, data)

        try:
            external = await self.integration_service.create_external_appointment(
                hospital_place_id=hospital_place_id,
                payload=appointment_payload,
            )
        except Exception as exc:
            logger.error("Direct hospital booking failed, routing to fallback: %s", exc)
            external = {
                "booking_mode": "fallback_internal",
                "booking_confirmation_status": "api_retry_required",
                "external_appointment_id": None,
                "raw": {"error": str(exc)},
            }

        status = "confirmed" if external["booking_mode"] == "direct_api" else "pending_confirmation"
        appointment_data = {
            "user_id": user_id,
            "doctor_name": data["doctor_name"],
            "doctor_id": data.get("doctor_id"),
            "doctor_specialty": data.get("doctor_specialty"),
            "doctor_rating": data.get("doctor_rating"),
            "doctor_experience_years": data.get("doctor_experience_years"),
            "consultation_fee": data.get("consultation_fee"),
            "hospital_name": data["hospital_name"],
            "hospital_address": data.get("hospital_address"),
            "hospital_place_id": hospital_place_id,
            "appointment_date": str(data["appointment_date"]),
            "appointment_time": self._time_to_string(data["appointment_time"]),
            "consultation_type": self._serialize_value(data.get("consultation_type", "in-person")),
            "status": status,
            "appointment_reason": data.get("appointment_reason"),
            "symptoms_notes": data.get("symptoms_notes"),
            "follow_up_details": data.get("follow_up_details"),
            "notes": data.get("notes"),
            "booking_mode": external["booking_mode"],
            "booking_confirmation_status": external["booking_confirmation_status"],
            "external_appointment_id": external.get("external_appointment_id"),
            "external_provider": self._external_provider_name(hospital_place_id),
            "api_payload": {
                "source_context": data.get("source_context"),
                "hospital_response": external.get("raw"),
            },
            "reminder_status": "pending",
            "reminder_channels": data.get("reminder_channels") or ["email", "sms"],
            "confirmed_at": datetime.utcnow().isoformat() if status == "confirmed" else None,
        }

        appointment = self._insert_appointment_safely(appointment_data)

        if appointment:
            await self._post_booking_side_effects(user_id, appointment, data, external["booking_mode"])

        return appointment

    async def get_appointments(self, user_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        filters = {"user_id": user_id}
        if status:
            filters["status"] = status
        return self.supabase.select("appointments", filters=filters, order_by="-appointment_date")

    async def get_appointment(self, user_id: str, appointment_id: str) -> Optional[Dict[str, Any]]:
        return self.supabase.select_one("appointments", filters={"id": appointment_id, "user_id": user_id})

    async def update_appointment(self, user_id: str, appointment_id: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        update_data = {k: self._serialize_value(v) for k, v in data.items() if v is not None}
        if not update_data:
            return await self.get_appointment(user_id, appointment_id)
        update_data["updated_at"] = datetime.utcnow().isoformat()
        result = self._update_appointment_safely(appointment_id, user_id, update_data)
        return result[0] if result else None

    async def reschedule_appointment(
        self,
        user_id: str,
        appointment_id: str,
        appointment_date: date,
        appointment_time: time,
        reason: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        appointment = await self.get_appointment(user_id, appointment_id)
        if not appointment:
            return None

        if appointment.get("booking_mode") == "direct_api":
            try:
                await self.integration_service.reschedule_external_appointment(
                    appointment.get("hospital_place_id"),
                    appointment.get("external_appointment_id"),
                    appointment_date,
                    appointment_time,
                )
            except Exception as exc:
                logger.warning("External reschedule failed, marking for staff review: %s", exc)

        update = {
            "appointment_date": str(appointment_date),
            "appointment_time": self._time_to_string(appointment_time),
            "status": "pending_confirmation" if appointment.get("booking_mode") != "direct_api" else "confirmed",
            "booking_confirmation_status": (
                "reschedule_requested" if appointment.get("booking_mode") != "direct_api" else "confirmed"
            ),
            "notes": reason or appointment.get("notes"),
            "updated_at": datetime.utcnow().isoformat(),
        }
        result = self._update_appointment_safely(appointment_id, user_id, update)
        updated = result[0] if result else None
        if updated:
            await self._create_appointment_reminder(user_id, updated)
        return updated

    async def cancel_appointment(self, user_id: str, appointment_id: str) -> Optional[Dict[str, Any]]:
        appointment = await self.get_appointment(user_id, appointment_id)
        if not appointment:
            return None

        if appointment.get("booking_mode") == "direct_api":
            try:
                await self.integration_service.cancel_external_appointment(
                    appointment.get("hospital_place_id"),
                    appointment.get("external_appointment_id"),
                )
            except Exception as exc:
                logger.warning("External cancellation failed: %s", exc)

        return await self.update_appointment(
            user_id,
            appointment_id,
            {
                "status": "cancelled",
                "booking_confirmation_status": "cancelled",
                "reminder_status": "cancelled",
                "cancelled_at": datetime.utcnow().isoformat(),
            },
        )

    async def get_available_slots(
        self,
        appointment_date: date,
        hospital_place_id: Optional[str] = None,
        doctor_id: Optional[str] = None,
        doctor_name: Optional[str] = None,
        consultation_type: str = "in-person",
    ) -> Dict[str, Any]:
        booked = self._get_booked_times(appointment_date, hospital_place_id, doctor_id, doctor_name)
        slot_result = await self.integration_service.fetch_slots(
            hospital_place_id=hospital_place_id,
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            consultation_type=consultation_type,
            booked_times=booked,
        )
        return {
            "date": str(appointment_date),
            "slots": slot_result["slots"],
            "doctor_name": doctor_name,
            "hospital_name": None,
            "booking_mode": slot_result["booking_mode"],
        }

    async def get_specialist_recommendation(
        self,
        user_id: str,
        symptoms: Optional[str] = None,
        diagnosis_type: Optional[str] = None,
        diagnosis_result: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Infer a recommended specialist from latest AI outputs or symptoms."""
        if diagnosis_type == "skin" or self._contains_any(diagnosis_result or "", ["skin", "rash", "lesion"]):
            return self._recommendation("dermatologist", 0.95, "Skin analysis recommends dermatology review.", "skin")

        if diagnosis_type == "pcod" or self._contains_any(diagnosis_result or "", ["pcod", "pcos", "period"]):
            return self._recommendation(
                "gynecologist",
                0.92,
                "Hormonal health assessment points to gynecology, with endocrinology as a strong alternative.",
                "pcod",
                alternatives=[{"key": "endocrinologist", "label": "Endocrinologist", "confidence": 0.84}],
            )

        latest = self._latest_diagnosis_context(user_id)
        if latest:
            specialist = latest.get("recommended_specialist", "")
            key = self._specialist_label_to_key(specialist)
            return self._recommendation(
                key,
                0.9,
                f"Based on your latest {latest['source_label']} result.",
                latest["source"],
                diagnosis_context=latest,
            )

        key = self._specialty_from_symptoms(symptoms or "")
        return self._recommendation(
            key,
            0.72 if symptoms else 0.62,
            "Matched from the symptoms you entered." if symptoms else "Start with a general physician for triage.",
            "symptoms" if symptoms else "default",
        )

    async def get_stats(self, user_id: str) -> Dict[str, int]:
        appointments = await self.get_appointments(user_id)
        today = date.today().isoformat()
        def appt_day(item: Dict[str, Any]) -> str:
            value = item.get("appointment_date")
            return value.isoformat() if isinstance(value, date) else str(value)

        return {
            "upcoming": sum(1 for a in appointments if appt_day(a) >= today and a.get("status") not in {"cancelled", "completed"}),
            "today": sum(1 for a in appointments if appt_day(a) == today and a.get("status") not in {"cancelled"}),
            "completed": sum(1 for a in appointments if a.get("status") == "completed"),
            "cancelled": sum(1 for a in appointments if a.get("status") == "cancelled"),
            "pending_confirmation": sum(
                1
                for a in appointments
                if a.get("status") == "pending_confirmation"
                or a.get("booking_confirmation_status") == "pending_hospital_confirmation"
            ),
        }

    def _get_patient_profile(self, user_id: str) -> Dict[str, Any]:
        try:
            return self.supabase.select_one("user_profiles", filters={"user_id": user_id}) or {}
        except Exception:
            return {}

    def _build_external_payload(self, user_id: str, patient_profile: Dict[str, Any], data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "patient": {
                "id": user_id,
                "full_name": patient_profile.get("full_name"),
                "email": patient_profile.get("email"),
                "phone": patient_profile.get("phone"),
                **(data.get("patient_details") or {}),
            },
            "appointment": {
                "doctor_id": data.get("doctor_id"),
                "doctor_name": data.get("doctor_name"),
                "specialty": data.get("doctor_specialty"),
                "hospital_place_id": data.get("hospital_place_id"),
                "hospital_name": data.get("hospital_name"),
                "date": str(data.get("appointment_date")),
                "time": self._time_to_string(data.get("appointment_time")),
                "consultation_type": self._serialize_value(data.get("consultation_type", "in-person")),
                "reason": data.get("appointment_reason"),
                "symptoms": data.get("symptoms_notes"),
                "follow_up_details": data.get("follow_up_details"),
            },
        }

    def _insert_appointment_safely(self, appointment_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        try:
            result = self.supabase.insert("appointments", {k: v for k, v in appointment_data.items() if v is not None})
            return result[0] if result else None
        except Exception as exc:
            logger.warning("Enhanced appointment insert failed, retrying legacy schema: %s", exc)
            legacy_keys = {
                "user_id",
                "doctor_name",
                "doctor_specialty",
                "hospital_name",
                "hospital_address",
                "hospital_place_id",
                "appointment_date",
                "appointment_time",
                "consultation_type",
                "notes",
            }
            legacy = {k: appointment_data[k] for k in legacy_keys if k in appointment_data and appointment_data[k] is not None}
            legacy["status"] = "scheduled"
            result = self.supabase.insert("appointments", legacy)
            return result[0] if result else None

    def _update_appointment_safely(self, appointment_id: str, user_id: str, update_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        try:
            return self.supabase.update("appointments", update_data, {"id": appointment_id, "user_id": user_id})
        except Exception as exc:
            logger.warning("Enhanced appointment update failed, retrying legacy fields: %s", exc)
            legacy_keys = {
                "doctor_name",
                "doctor_specialty",
                "hospital_name",
                "hospital_address",
                "appointment_date",
                "appointment_time",
                "consultation_type",
                "status",
                "notes",
                "updated_at",
            }
            legacy = {k: update_data[k] for k in legacy_keys if k in update_data}
            if legacy.get("status") == "pending_confirmation":
                legacy["status"] = "scheduled"
            return self.supabase.update("appointments", legacy, {"id": appointment_id, "user_id": user_id})

    async def _post_booking_side_effects(
        self,
        user_id: str,
        appointment: Dict[str, Any],
        request_data: Dict[str, Any],
        booking_mode: str,
    ) -> None:
        if booking_mode == "fallback_internal":
            self._create_booking_request_queue_item(user_id, appointment)

        await self._create_appointment_reminder(user_id, appointment, request_data.get("reminder_channels"))

        status_label = "confirmed" if booking_mode == "direct_api" else "sent to hospital staff for confirmation"
        try:
            await self.notification_service.create_notification(
                user_id=user_id,
                title="Appointment request received",
                body=f"Your appointment with {appointment['doctor_name']} at {appointment['hospital_name']} is {status_label}.",
                notif_type="appointment",
                reference_id=appointment["id"],
            )
        except Exception as exc:
            logger.warning("Appointment notification failed: %s", exc)

    def _create_booking_request_queue_item(self, user_id: str, appointment: Dict[str, Any]) -> None:
        try:
            self.supabase.insert(
                "hospital_booking_requests",
                {
                    "appointment_id": appointment["id"],
                    "user_id": user_id,
                    "hospital_place_id": appointment.get("hospital_place_id"),
                    "hospital_name": appointment.get("hospital_name"),
                    "status": "pending_staff_confirmation",
                    "staff_notification_status": "pending",
                    "request_payload": appointment,
                },
            )
        except Exception as exc:
            logger.info("Fallback booking queue unavailable: %s", exc)

    async def _create_appointment_reminder(
        self,
        user_id: str,
        appointment: Dict[str, Any],
        channels: Optional[List[str]] = None,
    ) -> None:
        try:
            appointment_dt = datetime.combine(
                self._coerce_date(appointment["appointment_date"]),
                self._coerce_time(appointment["appointment_time"]),
            )
            reminder_at = appointment_dt - timedelta(hours=1)
            if reminder_at < datetime.utcnow():
                reminder_at = datetime.utcnow() + timedelta(minutes=2)
            await self.notification_service.create_reminder(
                user_id=user_id,
                title=f"Appointment with {appointment['doctor_name']}",
                description=(
                    f"Your appointment with {appointment['doctor_name']} at "
                    f"{appointment['hospital_name']} is scheduled for "
                    f"{self._time_to_string(appointment['appointment_time'])} today."
                ),
                reminder_type="appointment",
                scheduled_at=reminder_at,
                reference_id=appointment["id"],
                delivery_channels=channels or appointment.get("reminder_channels") or ["email", "sms"],
            )
        except Exception as exc:
            logger.error("Reminder creation failed: %s", exc)

    def _get_booked_times(
        self,
        appointment_date: date,
        hospital_place_id: Optional[str],
        doctor_id: Optional[str],
        doctor_name: Optional[str],
    ) -> set[str]:
        try:
            filters = {"appointment_date": str(appointment_date)}
            if hospital_place_id:
                filters["hospital_place_id"] = hospital_place_id
            appointments = self.supabase.select("appointments", filters=filters)
        except Exception:
            return set()

        booked = set()
        for appointment in appointments:
            if appointment.get("status") in {"cancelled", "completed", "no-show"}:
                continue
            if doctor_id and appointment.get("doctor_id") and appointment.get("doctor_id") != doctor_id:
                continue
            if doctor_name and appointment.get("doctor_name") != doctor_name and not appointment.get("doctor_id"):
                continue
            if appointment.get("appointment_time"):
                booked.add(str(appointment["appointment_time"])[:5])
        return booked

    def _latest_diagnosis_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        candidates = []
        try:
            skin = self.supabase.select(
                "disease_predictions",
                filters={"user_id": user_id, "prediction_type": "skin_detection"},
                order_by="-created_at",
                limit=1,
            )
            if skin:
                item = skin[0]
                candidates.append(
                    {
                        "source": "skin",
                        "source_label": "skin analysis",
                        "recommended_specialist": item.get("recommended_specialist", "Dermatologist"),
                        "condition": item.get("predicted_condition"),
                        "risk_level": item.get("risk_level"),
                        "created_at": item.get("created_at"),
                    }
                )
        except Exception:
            pass

        try:
            pcod = self.supabase.select(
                "pcod_assessments",
                filters={"user_id": user_id},
                order_by="-created_at",
                limit=1,
            )
            if pcod:
                item = pcod[0]
                candidates.append(
                    {
                        "source": "pcod",
                        "source_label": "PCOD/PCOS assessment",
                        "recommended_specialist": item.get("recommended_specialist", "Gynecologist / Endocrinologist"),
                        "condition": ", ".join(item.get("conditions_flagged") or []),
                        "risk_level": item.get("risk_level"),
                        "created_at": item.get("created_at"),
                    }
                )
        except Exception:
            pass

        if not candidates:
            return None
        return sorted(candidates, key=lambda x: x.get("created_at") or "", reverse=True)[0]

    def _specialty_from_symptoms(self, symptoms: str) -> str:
        text = symptoms.lower()
        mapping = [
            ("dermatologist", ["rash", "skin", "itch", "acne", "lesion", "mole"]),
            ("gynecologist", ["period", "pcod", "pcos", "pelvic", "pregnancy", "menstrual"]),
            ("endocrinologist", ["hormone", "thyroid", "diabetes", "weight gain", "insulin"]),
            ("cardiologist", ["chest pain", "palpitation", "heart", "blood pressure"]),
            ("pulmonologist", ["cough", "breath", "wheezing", "asthma", "lung"]),
            ("neurologist", ["headache", "migraine", "seizure", "numbness", "dizziness"]),
            ("orthopedist", ["joint", "bone", "fracture", "back pain", "knee"]),
            ("gastroenterologist", ["stomach", "abdomen", "digestion", "acid", "liver"]),
            ("psychiatrist", ["anxiety", "depression", "panic", "sleep", "stress"]),
        ]
        for specialty, keywords in mapping:
            if any(keyword in text for keyword in keywords):
                return specialty
        return "general_physician"

    def _recommendation(
        self,
        key: str,
        confidence: float,
        reason: str,
        source: str,
        alternatives: Optional[List[Dict[str, Any]]] = None,
        diagnosis_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return {
            "specialist_key": key,
            "specialist_label": SPECIALTY_LABELS.get(key, "General Physician"),
            "confidence": confidence,
            "reason": reason,
            "source": source,
            "alternatives": alternatives
            or [{"key": "general_physician", "label": "General Physician", "confidence": 0.58}],
            "diagnosis_context": diagnosis_context,
        }

    def _specialist_label_to_key(self, label: str) -> str:
        text = (label or "").lower()
        if "dermat" in text:
            return "dermatologist"
        if "endocrin" in text:
            return "endocrinologist"
        if "gynec" in text or "gynaec" in text:
            return "gynecologist"
        if "cardio" in text:
            return "cardiologist"
        return "general_physician"

    def _external_provider_name(self, hospital_place_id: Optional[str]) -> Optional[str]:
        integration = self.integration_service.get_integration(hospital_place_id)
        return integration.get("label") if integration else None

    def _serialize_value(self, value: Any) -> Any:
        if isinstance(value, (date, time, datetime)):
            return str(value)
        if hasattr(value, "value"):
            return value.value
        return value

    def _time_to_string(self, value: Any) -> str:
        if isinstance(value, time):
            return value.strftime("%H:%M")
        return str(value)[:5]

    def _coerce_date(self, value: Any) -> date:
        if isinstance(value, date):
            return value
        return datetime.fromisoformat(str(value)).date()

    def _coerce_time(self, value: Any) -> time:
        if isinstance(value, time):
            return value
        return time.fromisoformat(str(value)[:5])

    def _contains_any(self, value: str, needles: List[str]) -> bool:
        text = value.lower()
        return any(needle in text for needle in needles)
