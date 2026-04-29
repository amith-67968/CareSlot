"""
CareSlot — Appointment Pydantic Models
Request/response schemas for appointment booking system.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, time, datetime
from enum import Enum


class ConsultationType(str, Enum):
    IN_PERSON = "in-person"
    VIDEO = "video"
    PHONE = "phone"


class AppointmentStatus(str, Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no-show"


# ─── Request Schemas ──────────────────────────────────────────────────

class AppointmentCreate(BaseModel):
    """Create a new appointment."""
    doctor_name: str = Field(..., min_length=2)
    doctor_specialty: Optional[str] = None
    hospital_name: str = Field(..., min_length=2)
    hospital_address: Optional[str] = None
    hospital_place_id: Optional[str] = Field(None, description="Google Maps place ID")
    appointment_date: date
    appointment_time: time
    consultation_type: ConsultationType = ConsultationType.IN_PERSON
    notes: Optional[str] = None

class AppointmentUpdate(BaseModel):
    """Update an existing appointment."""
    doctor_name: Optional[str] = None
    doctor_specialty: Optional[str] = None
    hospital_name: Optional[str] = None
    hospital_address: Optional[str] = None
    appointment_date: Optional[date] = None
    appointment_time: Optional[time] = None
    consultation_type: Optional[ConsultationType] = None
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None

class AppointmentSlotsRequest(BaseModel):
    """Request available appointment slots."""
    hospital_place_id: Optional[str] = None
    doctor_name: Optional[str] = None
    date: date
    consultation_type: ConsultationType = ConsultationType.IN_PERSON


# ─── Response Schemas ─────────────────────────────────────────────────

class AppointmentResponse(BaseModel):
    """Single appointment record."""
    id: str
    user_id: str
    doctor_name: str
    doctor_specialty: Optional[str] = None
    hospital_name: str
    hospital_address: Optional[str] = None
    hospital_place_id: Optional[str] = None
    appointment_date: date
    appointment_time: time
    consultation_type: str
    status: str
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class AppointmentListResponse(BaseModel):
    """List of appointments."""
    appointments: List[AppointmentResponse]
    total: int

class TimeSlot(BaseModel):
    """Available appointment time slot."""
    time: time
    available: bool = True

class AvailableSlotsResponse(BaseModel):
    """Available slots for a given date."""
    date: date
    slots: List[TimeSlot]
    doctor_name: Optional[str] = None
    hospital_name: Optional[str] = None
