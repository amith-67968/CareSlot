"""
CareSlot - Appointment Pydantic models.
Schemas for dual-mode hospital booking, discovery, slots, and history.
"""

from datetime import date, time, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ConsultationType(str, Enum):
    IN_PERSON = "in-person"
    VIDEO = "video"
    PHONE = "phone"


class AppointmentStatus(str, Enum):
    PENDING_CONFIRMATION = "pending_confirmation"
    SCHEDULED = "scheduled"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no-show"
    RESCHEDULED = "rescheduled"


class BookingMode(str, Enum):
    DIRECT_API = "direct_api"
    FALLBACK_INTERNAL = "fallback_internal"


class BookingConfirmationStatus(str, Enum):
    CONFIRMED = "confirmed"
    PENDING_HOSPITAL_CONFIRMATION = "pending_hospital_confirmation"
    API_RETRY_REQUIRED = "api_retry_required"
    RESCHEDULE_REQUESTED = "reschedule_requested"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class HospitalLocation(BaseModel):
    latitude: float
    longitude: float


class HospitalPhoto(BaseModel):
    photo_reference: str
    width: int = 0
    height: int = 0


class HospitalSearchRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    specialty: Optional[str] = Field(None, description="Specialist type to prioritize")
    radius: int = Field(5000, ge=500, le=50000)
    keyword: Optional[str] = None


class HospitalSummary(BaseModel):
    place_id: str
    name: str
    address: str
    location: HospitalLocation
    rating: Optional[float] = None
    total_ratings: Optional[int] = None
    is_open_now: Optional[bool] = None
    distance_text: Optional[str] = None
    specialty_match: Optional[str] = None
    specialties_available: List[str] = Field(default_factory=list)
    photos: List[HospitalPhoto] = Field(default_factory=list)
    booking_mode: str = "fallback_internal"
    integration_label: str = "CareSlot internal booking"
    supports_real_time_slots: bool = False
    requires_staff_confirmation: bool = True


class NearbyHospitalsResponse(BaseModel):
    results: List[HospitalSummary]
    total: int
    search_location: HospitalLocation
    search_radius: int
    specialty_searched: Optional[str] = None


class DoctorSummary(BaseModel):
    id: str
    name: str
    specialization: str
    experience_years: int = 0
    consultation_types: List[str] = Field(default_factory=lambda: ["in-person"])
    rating: Optional[float] = None
    available_timings: List[str] = Field(default_factory=list)
    consultation_fee: Optional[float] = None
    hospital_place_id: Optional[str] = None
    hospital_name: Optional[str] = None
    booking_mode: str = "fallback_internal"
    next_available: Optional[str] = None


class HospitalDoctorsResponse(BaseModel):
    hospital: HospitalSummary
    doctors: List[DoctorSummary]
    booking_mode: str
    capabilities: Dict[str, Any] = Field(default_factory=dict)


class AppointmentCreate(BaseModel):
    """Create a new appointment without sending the patient to a hospital site."""

    doctor_name: str = Field(..., min_length=2)
    doctor_id: Optional[str] = None
    doctor_specialty: Optional[str] = None
    doctor_rating: Optional[float] = None
    doctor_experience_years: Optional[int] = None
    consultation_fee: Optional[float] = None
    hospital_name: str = Field(..., min_length=2)
    hospital_address: Optional[str] = None
    hospital_place_id: Optional[str] = Field(None, description="Google Maps place ID")
    appointment_date: date
    appointment_time: time
    consultation_type: ConsultationType = ConsultationType.IN_PERSON
    appointment_reason: Optional[str] = None
    symptoms_notes: Optional[str] = None
    follow_up_details: Optional[str] = None
    notes: Optional[str] = None
    source_context: Optional[Dict[str, Any]] = None
    patient_details: Optional[Dict[str, Any]] = None
    reminder_channels: List[str] = Field(default_factory=lambda: ["email"])


class AppointmentUpdate(BaseModel):
    """Update an existing appointment."""

    doctor_name: Optional[str] = None
    doctor_id: Optional[str] = None
    doctor_specialty: Optional[str] = None
    hospital_name: Optional[str] = None
    hospital_address: Optional[str] = None
    appointment_date: Optional[date] = None
    appointment_time: Optional[time] = None
    consultation_type: Optional[ConsultationType] = None
    status: Optional[AppointmentStatus] = None
    appointment_reason: Optional[str] = None
    symptoms_notes: Optional[str] = None
    follow_up_details: Optional[str] = None
    notes: Optional[str] = None
    cancellation_reason: Optional[str] = None


class AppointmentRescheduleRequest(BaseModel):
    appointment_date: date
    appointment_time: time
    reason: Optional[str] = None


class AppointmentSlotsRequest(BaseModel):
    """Request available appointment slots."""

    hospital_place_id: Optional[str] = None
    doctor_id: Optional[str] = None
    doctor_name: Optional[str] = None
    date: date
    consultation_type: ConsultationType = ConsultationType.IN_PERSON


class AppointmentResponse(BaseModel):
    """Single appointment record."""

    id: str
    user_id: str
    doctor_name: str
    doctor_id: Optional[str] = None
    doctor_specialty: Optional[str] = None
    doctor_rating: Optional[float] = None
    doctor_experience_years: Optional[int] = None
    consultation_fee: Optional[float] = None
    hospital_name: str
    hospital_address: Optional[str] = None
    hospital_place_id: Optional[str] = None
    appointment_date: date
    appointment_time: time
    consultation_type: str
    status: str
    appointment_reason: Optional[str] = None
    symptoms_notes: Optional[str] = None
    follow_up_details: Optional[str] = None
    notes: Optional[str] = None
    booking_mode: Optional[str] = None
    booking_confirmation_status: Optional[str] = None
    external_appointment_id: Optional[str] = None
    external_provider: Optional[str] = None
    reminder_status: Optional[str] = None
    reminder_channels: Optional[List[str]] = None
    hospital_staff_notified_at: Optional[datetime] = None
    confirmed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class AppointmentListResponse(BaseModel):
    appointments: List[AppointmentResponse]
    total: int


class TimeSlot(BaseModel):
    time: time
    available: bool = True
    source: str = "fallback_internal"
    unavailable_reason: Optional[str] = None


class AvailableSlotsResponse(BaseModel):
    date: date
    slots: List[TimeSlot]
    doctor_name: Optional[str] = None
    hospital_name: Optional[str] = None
    booking_mode: str = "fallback_internal"


class SpecialistRecommendationRequest(BaseModel):
    symptoms: Optional[str] = None
    diagnosis_type: Optional[str] = Field(None, description="skin, pcod, or symptom_chat")
    diagnosis_result: Optional[str] = None


class SpecialistRecommendationResponse(BaseModel):
    specialist_key: str
    specialist_label: str
    confidence: float = 0.7
    reason: str
    source: str = "symptoms"
    alternatives: List[Dict[str, Any]] = Field(default_factory=list)
    diagnosis_context: Optional[Dict[str, Any]] = None


class AppointmentStatsResponse(BaseModel):
    upcoming: int = 0
    today: int = 0
    completed: int = 0
    cancelled: int = 0
    pending_confirmation: int = 0
