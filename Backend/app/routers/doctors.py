"""
CareSlot — Doctor Recommendation Router
Endpoints for finding nearby doctors/hospitals.
"""

from fastapi import APIRouter, Depends, HTTPException, Response
from app.models.doctor import NearbyDoctorRequest, NearbyDoctorResponse, SpecialtyListResponse
from app.services.doctor_service import DoctorService
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/doctors", tags=["Doctor Recommendations"])


@router.post("/nearby", response_model=NearbyDoctorResponse)
async def find_nearby_doctors(request: NearbyDoctorRequest, user: dict = Depends(get_current_user)):
    """Find nearby doctors and hospitals based on specialty and location."""
    try:
        service = DoctorService()
        result = await service.find_nearby(
            latitude=request.latitude,
            longitude=request.longitude,
            specialty=request.specialty,
            radius=request.radius,
            keyword=request.keyword,
        )
        return NearbyDoctorResponse(**result)
    except Exception as e:
        raise HTTPException(500, f"Failed to search doctors: {str(e)}")


@router.get("/place/{place_id}")
async def get_place_details(place_id: str, user: dict = Depends(get_current_user)):
    """Get detailed information about a hospital/clinic."""
    service = DoctorService()
    return await service.get_place_details(place_id)


@router.get("/photo")
async def get_place_photo(photo_reference: str, max_width: int = 900):
    """Proxy Google Places photos without exposing the Maps API key to the browser."""
    service = DoctorService()
    content, content_type = await service.fetch_photo(photo_reference, max_width=max_width)
    if not content:
        raise HTTPException(404, "Photo not available")
    return Response(content=content, media_type=content_type)


@router.get("/specialties", response_model=SpecialtyListResponse)
async def get_specialties():
    """Get list of available medical specialties for search."""
    service = DoctorService()
    return SpecialtyListResponse(specialties=service.get_specialties())
