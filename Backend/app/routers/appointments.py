"""
CareSlot - Appointment router.
Endpoints for discovery, specialist recommendation, dual-mode booking, and history.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_current_user
from app.models.appointment import (
    AppointmentCreate,
    AppointmentListResponse,
    AppointmentResponse,
    AppointmentRescheduleRequest,
    AppointmentSlotsRequest,
    AppointmentStatsResponse,
    AppointmentUpdate,
    AvailableSlotsResponse,
    HospitalDoctorsResponse,
    HospitalSearchRequest,
    NearbyHospitalsResponse,
    SpecialistRecommendationRequest,
    SpecialistRecommendationResponse,
)
from app.services.appointment_service import AppointmentService

router = APIRouter(prefix="/api/appointments", tags=["Appointments"])


@router.post("/recommendation", response_model=SpecialistRecommendationResponse)
async def recommend_specialist(
    data: SpecialistRecommendationRequest,
    user: dict = Depends(get_current_user),
):
    """Recommend a specialist from AI diagnosis history or symptoms."""
    service = AppointmentService()
    return await service.get_specialist_recommendation(
        user_id=user["user_id"],
        symptoms=data.symptoms,
        diagnosis_type=data.diagnosis_type,
        diagnosis_result=data.diagnosis_result,
    )


@router.post("/hospitals/nearby", response_model=NearbyHospitalsResponse)
async def find_nearby_hospitals(
    data: HospitalSearchRequest,
    user: dict = Depends(get_current_user),
):
    """Find nearby hospitals/clinics using Google Maps and enrich booking modes."""
    service = AppointmentService()
    return await service.find_nearby_hospitals(
        latitude=data.latitude,
        longitude=data.longitude,
        specialty=data.specialty,
        radius=data.radius,
        keyword=data.keyword,
    )


@router.get("/hospitals/{place_id}/doctors", response_model=HospitalDoctorsResponse)
async def get_hospital_doctors(
    place_id: str,
    specialty: Optional[str] = None,
    hospital_name: Optional[str] = None,
    hospital_address: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    """Get doctors for a hospital via direct API or internal fallback catalog."""
    service = AppointmentService()
    return await service.get_hospital_doctors(place_id, specialty, hospital_name, hospital_address)


@router.get("/slots", response_model=AvailableSlotsResponse)
async def get_available_slots(
    request: AppointmentSlotsRequest = Depends(),
    user: dict = Depends(get_current_user),
):
    """Get available appointment time slots for hospital/doctor/date."""
    service = AppointmentService()
    return await service.get_available_slots(
        appointment_date=request.date,
        hospital_place_id=request.hospital_place_id,
        doctor_id=request.doctor_id,
        doctor_name=request.doctor_name,
        consultation_type=request.consultation_type.value,
    )


@router.get("/stats", response_model=AppointmentStatsResponse)
async def get_appointment_stats(user: dict = Depends(get_current_user)):
    """Appointment dashboard counters."""
    service = AppointmentService()
    return await service.get_stats(user["user_id"])


@router.post("/", response_model=AppointmentResponse, status_code=201)
async def create_appointment(data: AppointmentCreate, user: dict = Depends(get_current_user)):
    """Book a new appointment inside CareSlot."""
    service = AppointmentService()
    result = await service.create_appointment(user["user_id"], data.model_dump(mode="json"))
    if not result:
        raise HTTPException(500, "Failed to create appointment")
    return result


@router.get("/", response_model=AppointmentListResponse)
async def list_appointments(status: Optional[str] = None, user: dict = Depends(get_current_user)):
    """List user's appointments with optional status filter."""
    service = AppointmentService()
    appointments = await service.get_appointments(user["user_id"], status=status)
    return AppointmentListResponse(appointments=appointments, total=len(appointments))


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(appointment_id: str, user: dict = Depends(get_current_user)):
    """Get a specific appointment."""
    service = AppointmentService()
    result = await service.get_appointment(user["user_id"], appointment_id)
    if not result:
        raise HTTPException(404, "Appointment not found")
    return result


@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: str,
    data: AppointmentUpdate,
    user: dict = Depends(get_current_user),
):
    """Update an appointment."""
    service = AppointmentService()
    result = await service.update_appointment(
        user["user_id"],
        appointment_id,
        data.model_dump(mode="json", exclude_none=True),
    )
    if not result:
        raise HTTPException(404, "Appointment not found")
    return result


@router.put("/{appointment_id}/reschedule", response_model=AppointmentResponse)
async def reschedule_appointment(
    appointment_id: str,
    data: AppointmentRescheduleRequest,
    user: dict = Depends(get_current_user),
):
    """Reschedule an appointment through direct API or fallback staff queue."""
    service = AppointmentService()
    result = await service.reschedule_appointment(
        user_id=user["user_id"],
        appointment_id=appointment_id,
        appointment_date=data.appointment_date,
        appointment_time=data.appointment_time,
        reason=data.reason,
    )
    if not result:
        raise HTTPException(404, "Appointment not found")
    return result


@router.delete("/{appointment_id}", response_model=AppointmentResponse)
async def cancel_appointment(appointment_id: str, user: dict = Depends(get_current_user)):
    """Cancel an appointment."""
    service = AppointmentService()
    result = await service.cancel_appointment(user["user_id"], appointment_id)
    if not result:
        raise HTTPException(404, "Appointment not found")
    return result
