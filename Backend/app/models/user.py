"""
CareSlot — User Pydantic Models
Request/response schemas for user authentication and profiles.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict
from datetime import date, datetime
from enum import Enum


# ─── Enums ────────────────────────────────────────────────────────────

class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"
    PREFER_NOT_TO_SAY = "prefer_not_to_say"


# ─── Auth Schemas ─────────────────────────────────────────────────────

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    full_name: str = Field(..., min_length=2)
    phone: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None

class SignInRequest(BaseModel):
    email: EmailStr
    password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class TokenRefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)

class AuthResponse(BaseModel):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user_id: Optional[str] = None
    email: Optional[str] = None
    expires_at: Optional[int] = None
    expires_in: Optional[int] = None
    message: Optional[str] = None

class MessageResponse(BaseModel):
    message: str
    success: bool = True


# ─── Profile Schemas ──────────────────────────────────────────────────

class AddressSchema(BaseModel):
    street: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip: Optional[str] = None
    country: Optional[str] = None

class EmergencyContactSchema(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    relationship: Optional[str] = None

class UserProfileCreate(BaseModel):
    full_name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    blood_group: Optional[str] = None
    address: Optional[AddressSchema] = None
    emergency_contact: Optional[EmergencyContactSchema] = None

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[Gender] = None
    blood_group: Optional[str] = None
    avatar_url: Optional[str] = None
    address: Optional[AddressSchema] = None
    emergency_contact: Optional[EmergencyContactSchema] = None

class UserProfileResponse(BaseModel):
    id: str
    user_id: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    avatar_url: Optional[str] = None
    address: Optional[Dict] = None
    emergency_contact: Optional[Dict] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ─── Medical History ──────────────────────────────────────────────────

class MedicalHistoryCreate(BaseModel):
    condition_name: str
    diagnosed_date: Optional[date] = None
    status: Optional[str] = "active"
    medications: Optional[list] = None
    allergies: Optional[list] = None
    notes: Optional[str] = None

class MedicalHistoryResponse(BaseModel):
    id: str
    user_id: str
    condition_name: str
    diagnosed_date: Optional[date] = None
    status: Optional[str] = None
    medications: Optional[list] = None
    allergies: Optional[list] = None
    notes: Optional[str] = None
    created_at: Optional[datetime] = None
