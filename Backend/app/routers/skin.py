"""
CareSlot — Skin Detection Router
Endpoints for skin disease detection via image upload.
"""

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from app.models.skin import SkinSymptomsInput, SkinAnalysisResponse, SkinHistoryResponse
from app.services.skin_service import SkinService
from app.dependencies import get_current_user
import json

router = APIRouter(prefix="/api/skin", tags=["Skin Disease Detection"])

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
MAX_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/analyze", response_model=SkinAnalysisResponse)
async def analyze_skin(
    image: UploadFile = File(..., description="Skin image to analyze"),
    symptoms: str = Form(default="{}", description="JSON string of symptoms"),
    user: dict = Depends(get_current_user),
):
    """Upload a skin image + symptoms for AI-powered preliminary assessment."""
    # Validate image
    if image.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, f"Invalid image type. Allowed: {ALLOWED_TYPES}")

    image_bytes = await image.read()
    if len(image_bytes) > MAX_SIZE:
        raise HTTPException(400, "Image too large. Max 10MB.")

    # Parse symptoms JSON
    try:
        symptoms_data = SkinSymptomsInput(**json.loads(symptoms))
    except Exception:
        symptoms_data = SkinSymptomsInput()

    service = SkinService()
    result = await service.analyze_skin(
        user_id=user["user_id"],
        image_bytes=image_bytes,
        filename=image.filename or "upload.jpg",
        symptoms=symptoms_data,
        content_type=image.content_type,
    )
    return SkinAnalysisResponse(**result)


@router.get("/history", response_model=SkinHistoryResponse)
async def get_skin_history(user: dict = Depends(get_current_user)):
    """Get past skin analysis history."""
    service = SkinService()
    result = await service.get_history(user["user_id"])
    return SkinHistoryResponse(**result)
