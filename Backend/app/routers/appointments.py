"""
CareSlot — Appointment Router
Endpoints for appointment booking and management.
"""

from fastapi import APIRouter, Depends, HTTPException
from app.models.appointment import (
    AppointmentCreate, AppointmentUpdate, AppointmentResponse,
    AppointmentListResponse, AppointmentSlotsRequest, AvailableSlotsResponse,
)
from app.services.appointment_service import AppointmentService
from app.dependencies import get_current_user
from typing import Optional

router = APIRouter(prefix="/api/appointments", tags=["Appointments"])


@router.post("/", response_model=AppointmentResponse, status_code=201)
async def create_appointment(data: AppointmentCreate, user: dict = Depends(get_current_user)):
    """Book a new appointment."""
    service = AppointmentService()
    result = await service.create_appointment(user["user_id"], data.model_dump())
    if not result:
        raise HTTPException(500, "Failed to create appointment")
    return result


@router.get("/", response_model=AppointmentListResponse)
async def list_appointments(status: Optional[str] = None, user: dict = Depends(get_current_user)):
    """List user's appointments with optional status filter."""
    service = AppointmentService()
    appointments = await service.get_appointments(user["user_id"], status=status)
    return AppointmentListResponse(appointments=appointments, total=len(appointments))


@router.get("/slots", response_model=AvailableSlotsResponse)
async def get_available_slots(request: AppointmentSlotsRequest = Depends(), user: dict = Depends(get_current_user)):
    """Get available appointment time slots for a given date."""
    service = AppointmentService()
    return await service.get_available_slots(request.date)


@router.get("/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(appointment_id: str, user: dict = Depends(get_current_user)):
    """Get a specific appointment."""
    service = AppointmentService()
    result = await service.get_appointment(user["user_id"], appointment_id)
    if not result:
        raise HTTPException(404, "Appointment not found")
    return result


@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(appointment_id: str, data: AppointmentUpdate, user: dict = Depends(get_current_user)):
    """Update an appointment."""
    service = AppointmentService()
    result = await service.update_appointment(user["user_id"], appointment_id, data.model_dump(exclude_none=True))
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
