"""
CareSlot - Hospital integration bridge.

Provides a single booking-facing contract for hospitals with direct scheduling
APIs and for hospitals that need CareSlot's internal fallback queue.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import date, time
from typing import Any, Dict, List, Optional

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


SPECIALTY_LABELS = {
    "cardiologist": "Cardiologist",
    "dermatologist": "Dermatologist",
    "gynecologist": "Gynecologist",
    "endocrinologist": "Endocrinologist",
    "pulmonologist": "Pulmonologist",
    "neurologist": "Neurologist",
    "orthopedist": "Orthopedist",
    "psychiatrist": "Psychiatrist",
    "gastroenterologist": "Gastroenterologist",
    "general_physician": "General Physician",
    "emergency": "Emergency Physician",
}

SPECIALTY_DEPARTMENTS = {
    "cardiologist": ["Cardiology", "Diagnostics", "Preventive Care"],
    "dermatologist": ["Dermatology", "Cosmetology", "Skin Screening"],
    "gynecologist": ["Gynecology", "Obstetrics", "Women's Health"],
    "endocrinologist": ["Endocrinology", "Diabetes Care", "Hormonal Health"],
    "pulmonologist": ["Pulmonology", "Respiratory Care", "Sleep Medicine"],
    "neurologist": ["Neurology", "Neuro Diagnostics", "Rehabilitation"],
    "orthopedist": ["Orthopedics", "Sports Medicine", "Physiotherapy"],
    "psychiatrist": ["Psychiatry", "Counseling", "Behavioral Health"],
    "gastroenterologist": ["Gastroenterology", "Endoscopy", "Nutrition"],
    "general_physician": ["General Medicine", "Primary Care", "Diagnostics"],
    "emergency": ["Emergency", "Trauma Care", "Critical Care"],
}

DOCTOR_NAMES = {
    "cardiologist": ["Aarav Mehta", "Nisha Rao", "Kabir Sethi", "Riya Bansal", "Farhan Mir", "Ishaan Dutta"],
    "dermatologist": ["Ira Kapoor", "Rohan Menon", "Ananya Shah", "Vikram Sood", "Tanya George", "Naina Batra", "Aditi Rao", "Karan Malhotra", "Mehul Desai"],
    "gynecologist": ["Meera Iyer", "Priya Nair", "Sana Qureshi", "Kavita Rao", "Zara Thomas", "Divya Menon"],
    "endocrinologist": ["Dev Khanna", "Leena Thomas", "Ritika Sen", "Nikhil Bhat", "Maya Das", "Arvind Rao"],
    "pulmonologist": ["Arjun Batra", "Tanvi Desai", "Mihir Paul", "Reema Shah", "Kabir Nair", "Sonal Iyer"],
    "neurologist": ["Rehan Malik", "Kavya Raman", "Neel Verma", "Asha Kapoor", "Rishi Menon", "Tara Sethi"],
    "orthopedist": ["Vikram Joshi", "Pooja Das", "Aditya Rao", "Neha Kulkarni", "Rahul Iyer", "Mira Shah"],
    "psychiatrist": ["Sara Fernandes", "Maya Singh", "Kunal Arora", "Rhea Nair", "Aman George", "Leela Menon"],
    "gastroenterologist": ["Anil Sharma", "Zoya Khan", "Harsh Patel", "Meena Rao", "Vivaan Shah", "Rekha Iyer"],
    "general_physician": ["Rhea Gupta", "Sameer Kulkarni", "Tara Bose", "Amit Nair", "Nandita Rao", "Kiran Shah"],
    "emergency": ["Neha Chauhan", "Arman Ali", "Veda Krishnan", "Rohit Sinha", "Isha Paul", "Devika Menon"],
}


class HospitalIntegrationService:
    """Adapter for direct hospital APIs with an internal fallback layer."""

    def __init__(self):
        self.settings = get_settings()
        self.registry = self._load_registry()

    def _load_registry(self) -> Dict[str, Dict[str, Any]]:
        try:
            parsed = json.loads(self.settings.HOSPITAL_API_REGISTRY_JSON or "{}")
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError as exc:
            logger.warning("Invalid HOSPITAL_API_REGISTRY_JSON: %s", exc)
            return {}

    def get_integration(self, place_id: Optional[str]) -> Optional[Dict[str, Any]]:
        if not place_id:
            return None
        integration = self.registry.get(place_id)
        if integration and integration.get("base_url"):
            return integration
        return None

    def get_capabilities(self, place_id: Optional[str]) -> Dict[str, Any]:
        integration = self.get_integration(place_id)
        if integration:
            return {
                "booking_mode": "direct_api",
                "label": integration.get("label", "Direct API"),
                "supports_real_time_slots": True,
                "supports_patient_registration": bool(integration.get("patient_registration_endpoint", True)),
                "requires_staff_confirmation": False,
            }
        return {
            "booking_mode": "fallback_internal",
            "label": "CareSlot internal booking",
            "supports_real_time_slots": False,
            "supports_patient_registration": False,
            "requires_staff_confirmation": True,
        }

    async def fetch_doctors(
        self,
        hospital: Dict[str, Any],
        specialty: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch doctors from a hospital API or build an internal catalog fallback."""
        place_id = hospital.get("place_id")
        integration = self.get_integration(place_id)
        if integration:
            try:
                doctors = await self._fetch_direct_doctors(integration, hospital, specialty)
                if doctors:
                    return {
                        "booking_mode": "direct_api",
                        "capabilities": self.get_capabilities(place_id),
                        "doctors": doctors,
                    }
            except Exception as exc:
                logger.warning("Direct doctor fetch failed for %s: %s", place_id, exc)

        return {
            "booking_mode": "fallback_internal",
            "capabilities": self.get_capabilities(place_id),
            "doctors": self._build_internal_doctors(hospital, specialty),
        }

    async def fetch_slots(
        self,
        hospital_place_id: Optional[str],
        doctor_id: Optional[str],
        appointment_date: date,
        consultation_type: str,
        booked_times: Optional[set[str]] = None,
    ) -> Dict[str, Any]:
        """Fetch slots from a direct API or synthesize fallback slots."""
        integration = self.get_integration(hospital_place_id)
        if integration:
            try:
                slots = await self._fetch_direct_slots(
                    integration=integration,
                    doctor_id=doctor_id,
                    appointment_date=appointment_date,
                    consultation_type=consultation_type,
                )
                if slots:
                    return {"booking_mode": "direct_api", "slots": slots}
            except Exception as exc:
                logger.warning("Direct slot fetch failed for %s: %s", hospital_place_id, exc)

        return {
            "booking_mode": "fallback_internal",
            "slots": self._build_internal_slots(appointment_date, booked_times or set()),
        }

    async def create_external_appointment(
        self,
        hospital_place_id: Optional[str],
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create an appointment in the hospital system when a direct API exists."""
        integration = self.get_integration(hospital_place_id)
        if not integration:
            return {
                "booking_mode": "fallback_internal",
                "booking_confirmation_status": "pending_hospital_confirmation",
                "external_appointment_id": None,
                "raw": None,
            }

        endpoint = integration.get("booking_endpoint", "/appointments")
        data = await self._direct_request("POST", integration, endpoint, json_payload=payload)
        status = str(data.get("status", "confirmed")).lower()
        if status in {"booked", "scheduled", "success"}:
            status = "confirmed"
        if status not in {
            "confirmed",
            "pending_hospital_confirmation",
            "api_retry_required",
            "reschedule_requested",
            "cancelled",
            "completed",
        }:
            status = "confirmed"
        return {
            "booking_mode": "direct_api",
            "booking_confirmation_status": status,
            "external_appointment_id": data.get("appointment_id") or data.get("id"),
            "raw": data,
        }

    async def cancel_external_appointment(
        self,
        hospital_place_id: Optional[str],
        external_appointment_id: Optional[str],
    ) -> Dict[str, Any]:
        integration = self.get_integration(hospital_place_id)
        if not integration or not external_appointment_id:
            return {"cancelled": False, "mode": "fallback_internal"}

        endpoint = integration.get("cancel_endpoint", f"/appointments/{external_appointment_id}/cancel")
        data = await self._direct_request("POST", integration, endpoint)
        return {"cancelled": True, "mode": "direct_api", "raw": data}

    async def reschedule_external_appointment(
        self,
        hospital_place_id: Optional[str],
        external_appointment_id: Optional[str],
        appointment_date: date,
        appointment_time: time,
    ) -> Dict[str, Any]:
        integration = self.get_integration(hospital_place_id)
        if not integration or not external_appointment_id:
            return {"rescheduled": False, "mode": "fallback_internal"}

        endpoint = integration.get("reschedule_endpoint", f"/appointments/{external_appointment_id}/reschedule")
        data = await self._direct_request(
            "POST",
            integration,
            endpoint,
            json_payload={
                "appointment_date": str(appointment_date),
                "appointment_time": str(appointment_time),
            },
        )
        return {"rescheduled": True, "mode": "direct_api", "raw": data}

    async def _fetch_direct_doctors(
        self,
        integration: Dict[str, Any],
        hospital: Dict[str, Any],
        specialty: Optional[str],
    ) -> List[Dict[str, Any]]:
        endpoint = integration.get("doctors_endpoint", "/doctors")
        data = await self._direct_request(
            "GET",
            integration,
            endpoint,
            params={"specialty": specialty, "place_id": hospital.get("place_id")},
        )
        raw_doctors = data.get("doctors", data if isinstance(data, list) else [])
        return [self._normalize_direct_doctor(d, hospital, specialty) for d in raw_doctors]

    async def _fetch_direct_slots(
        self,
        integration: Dict[str, Any],
        doctor_id: Optional[str],
        appointment_date: date,
        consultation_type: str,
    ) -> List[Dict[str, Any]]:
        endpoint = integration.get("slots_endpoint", "/slots")
        data = await self._direct_request(
            "GET",
            integration,
            endpoint,
            params={
                "doctor_id": doctor_id,
                "date": str(appointment_date),
                "consultation_type": consultation_type,
            },
        )
        raw_slots = data.get("slots", data if isinstance(data, list) else [])
        return [self._normalize_slot(s, source="direct_api") for s in raw_slots]

    async def _direct_request(
        self,
        method: str,
        integration: Dict[str, Any],
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_payload: Optional[Dict[str, Any]] = None,
    ) -> Any:
        base_url = integration["base_url"].rstrip("/")
        url = f"{base_url}/{endpoint.lstrip('/')}"
        headers = dict(integration.get("headers", {}))
        if integration.get("api_key"):
            headers.setdefault("Authorization", f"Bearer {integration['api_key']}")

        async with httpx.AsyncClient(timeout=self.settings.HOSPITAL_API_TIMEOUT_SECONDS) as client:
            response = await client.request(
                method,
                url,
                params={k: v for k, v in (params or {}).items() if v is not None},
                json=json_payload,
                headers=headers,
            )
            response.raise_for_status()
            return response.json()

    def _normalize_direct_doctor(
        self,
        doctor: Dict[str, Any],
        hospital: Dict[str, Any],
        specialty: Optional[str],
    ) -> Dict[str, Any]:
        specialization = doctor.get("specialization") or doctor.get("specialty") or SPECIALTY_LABELS.get(
            specialty or "general_physician",
            "General Physician",
        )
        return {
            "id": str(doctor.get("id") or doctor.get("doctor_id") or doctor.get("name")),
            "name": doctor.get("name") or "Doctor",
            "specialization": specialization,
            "experience_years": doctor.get("experience_years") or doctor.get("experience") or 8,
            "consultation_types": doctor.get("consultation_types") or ["in-person"],
            "rating": doctor.get("rating") or 4.7,
            "available_timings": doctor.get("available_timings") or ["09:00-13:00", "15:00-18:00"],
            "consultation_fee": doctor.get("consultation_fee") or doctor.get("fee"),
            "hospital_place_id": hospital.get("place_id"),
            "hospital_name": hospital.get("name"),
            "booking_mode": "direct_api",
            "next_available": doctor.get("next_available"),
        }

    def _normalize_slot(self, slot: Any, source: str) -> Dict[str, Any]:
        if isinstance(slot, str):
            value = slot
            available = True
        else:
            value = slot.get("time") or slot.get("start_time") or slot.get("slot")
            available = slot.get("available", True)
        value = value[:5] if isinstance(value, str) else value
        return {
            "time": value,
            "available": bool(available),
            "source": source,
            "unavailable_reason": None if available else "Already reserved",
        }

    def _build_internal_doctors(self, hospital: Dict[str, Any], specialty: Optional[str]) -> List[Dict[str, Any]]:
        specialty_key = specialty or "general_physician"
        names = DOCTOR_NAMES.get(specialty_key, DOCTOR_NAMES["general_physician"])
        label = SPECIALTY_LABELS.get(specialty_key, "General Physician")
        seed = hospital.get("place_id") or hospital.get("name") or "careslot"
        offset = self._stable_int(f"{seed}:{specialty_key}:name-offset")
        doctors = []

        for idx in range(min(3, len(names))):
            name = names[(offset + idx * 2) % len(names)]
            stable = self._stable_int(f"{seed}:{specialty_key}:{idx}")
            doctors.append(
                {
                    "id": f"{seed}:{specialty_key}:{idx + 1}",
                    "name": f"Dr. {name}",
                    "specialization": label,
                    "experience_years": 6 + stable % 18,
                    "consultation_types": ["in-person", "video"] if idx == 0 else ["in-person"],
                    "rating": round(4.4 + ((stable % 50) / 100), 1),
                    "available_timings": ["09:00-13:00", "15:00-18:00"],
                    "consultation_fee": 600 + (stable % 9) * 100,
                    "hospital_place_id": hospital.get("place_id"),
                    "hospital_name": hospital.get("name"),
                    "booking_mode": "fallback_internal",
                    "next_available": "Today",
                }
            )

        return doctors

    def _build_internal_slots(self, appointment_date: date, booked_times: set[str]) -> List[Dict[str, Any]]:
        base_slots = [
            time(9, 0),
            time(9, 30),
            time(10, 0),
            time(10, 30),
            time(11, 30),
            time(14, 0),
            time(14, 30),
            time(15, 0),
            time(16, 0),
            time(17, 0),
        ]
        slots = []
        for slot in base_slots:
            value = slot.strftime("%H:%M")
            is_available = value not in booked_times and f"{value}:00" not in booked_times
            slots.append(
                {
                    "time": value,
                    "available": is_available,
                    "source": "fallback_internal",
                    "unavailable_reason": None if is_available else "Already requested",
                }
            )
        return slots

    def departments_for_specialty(self, specialty: Optional[str]) -> List[str]:
        if specialty and specialty in SPECIALTY_DEPARTMENTS:
            return SPECIALTY_DEPARTMENTS[specialty]
        return ["General Medicine", "Diagnostics", "Primary Care"]

    def _stable_int(self, value: str) -> int:
        return int(hashlib.sha256(value.encode("utf-8")).hexdigest()[:8], 16)
