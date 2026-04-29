"""
CareSlot — Profile Router
Endpoints for user profile management.
"""

from fastapi import APIRouter, HTTPException, Depends
from app.models.user import (
    UserProfileResponse, UserProfileUpdate, MedicalHistoryCreate, MedicalHistoryResponse, MessageResponse,
)
from app.services.auth_service import AuthService
from app.services.supabase_service import SupabaseService
from app.dependencies import get_current_user
from typing import List

router = APIRouter(prefix="/api/profile", tags=["User Profile"])


@router.get("/", response_model=UserProfileResponse)
async def get_profile(user: dict = Depends(get_current_user)):
    """Get the current user's profile."""
    service = AuthService()
    profile = await service.get_profile(user["user_id"])
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.put("/", response_model=UserProfileResponse)
async def update_profile(data: UserProfileUpdate, user: dict = Depends(get_current_user)):
    """Update the current user's profile."""
    service = AuthService()
    update_data = data.model_dump(exclude_none=True)
    # Convert nested models to dicts
    for key in ("address", "emergency_contact"):
        if key in update_data and update_data[key]:
            update_data[key] = dict(update_data[key])
    profile = await service.update_profile(user["user_id"], update_data)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.get("/medical-history", response_model=List[MedicalHistoryResponse])
async def get_medical_history(user: dict = Depends(get_current_user)):
    """Get user's medical history."""
    supabase = SupabaseService()
    return supabase.select("medical_history", filters={"user_id": user["user_id"]}, order_by="-created_at")


@router.post("/medical-history", response_model=MedicalHistoryResponse, status_code=201)
async def add_medical_history(data: MedicalHistoryCreate, user: dict = Depends(get_current_user)):
    """Add a medical history entry."""
    supabase = SupabaseService()
    entry = data.model_dump()
    entry["user_id"] = user["user_id"]
    if entry.get("diagnosed_date"):
        entry["diagnosed_date"] = str(entry["diagnosed_date"])
    result = supabase.insert("medical_history", entry)
    return result[0]
