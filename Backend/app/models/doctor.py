"""
CareSlot — Doctor Recommendation Pydantic Models
Request/response schemas for doctor/hospital search via Google Maps.
"""

from pydantic import BaseModel, Field
from typing import Optional, List


# ─── Request Schemas ──────────────────────────────────────────────────

class NearbyDoctorRequest(BaseModel):
    """Request to find nearby doctors/hospitals."""
    latitude: float = Field(..., ge=-90, le=90, description="User's latitude")
    longitude: float = Field(..., ge=-180, le=180, description="User's longitude")
    specialty: Optional[str] = Field(
        None,
        description="Doctor specialty to search for (e.g., 'dermatologist', 'cardiologist')",
    )
    radius: int = Field(
        5000,
        ge=500,
        le=50000,
        description="Search radius in meters (default 5km)",
    )
    keyword: Optional[str] = Field(
        None,
        description="Additional search keyword (e.g., 'emergency', 'clinic')",
    )


# ─── Response Schemas ─────────────────────────────────────────────────

class DoctorLocation(BaseModel):
    """Location coordinates."""
    latitude: float
    longitude: float

class DoctorPhoto(BaseModel):
    """Photo reference from Google Maps."""
    photo_reference: str
    width: int
    height: int

class DoctorResult(BaseModel):
    """Single doctor/hospital result from Google Maps."""
    place_id: str
    name: str
    address: str
    location: DoctorLocation
    rating: Optional[float] = None
    total_ratings: Optional[int] = None
    is_open_now: Optional[bool] = None
    specialty_match: Optional[str] = None
    distance_text: Optional[str] = None
    phone_number: Optional[str] = None
    website: Optional[str] = None
    photos: List[DoctorPhoto] = Field(default_factory=list)
    types: List[str] = Field(default_factory=list)

class NearbyDoctorResponse(BaseModel):
    """Response with list of nearby doctors/hospitals."""
    results: List[DoctorResult]
    total: int
    search_location: DoctorLocation
    search_radius: int
    specialty_searched: Optional[str] = None

class SpecialtyListResponse(BaseModel):
    """List of available specialties for search."""
    specialties: List[dict] = Field(
        default_factory=lambda: [
            {"key": "cardiologist", "label": "Cardiologist", "keywords": ["cardiology", "heart"]},
            {"key": "dermatologist", "label": "Dermatologist", "keywords": ["dermatology", "skin"]},
            {"key": "gynecologist", "label": "Gynecologist", "keywords": ["gynecology", "obgyn"]},
            {"key": "endocrinologist", "label": "Endocrinologist", "keywords": ["endocrinology", "hormone"]},
            {"key": "pulmonologist", "label": "Pulmonologist", "keywords": ["pulmonology", "lung"]},
            {"key": "neurologist", "label": "Neurologist", "keywords": ["neurology", "brain"]},
            {"key": "orthopedist", "label": "Orthopedist", "keywords": ["orthopedic", "bone"]},
            {"key": "psychiatrist", "label": "Psychiatrist", "keywords": ["psychiatry", "mental health"]},
            {"key": "general_physician", "label": "General Physician", "keywords": ["general", "physician"]},
            {"key": "emergency", "label": "Emergency Care", "keywords": ["emergency", "hospital", "ER"]},
        ]
    )
