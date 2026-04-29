"""
CareSlot — PCOD Assessment Router
Endpoints for PCOD/PCOS risk assessment.
"""

from fastapi import APIRouter, Depends, HTTPException
from app.models.pcod import (
    PCODQuestionnaireRequest, PCODAssessmentResponse,
    PCODHistoryResponse, PCODAssessmentDetailResponse,
)
from app.services.pcod_service import PCODService
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/pcod", tags=["PCOD/PCOS Assessment"])


@router.post("/assess", response_model=PCODAssessmentResponse)
async def assess_pcod(request: PCODQuestionnaireRequest, user: dict = Depends(get_current_user)):
    """Submit PCOD/PCOS risk assessment questionnaire."""
    service = PCODService()
    result = await service.run_assessment(
        user_id=user["user_id"],
        questionnaire=request.model_dump(),
    )
    return PCODAssessmentResponse(**result)


@router.get("/history", response_model=PCODHistoryResponse)
async def get_pcod_history(user: dict = Depends(get_current_user)):
    """Get past PCOD/PCOS assessment history."""
    service = PCODService()
    result = await service.get_history(user["user_id"])
    return PCODHistoryResponse(**result)


@router.get("/assessments/{assessment_id}", response_model=PCODAssessmentDetailResponse)
async def get_assessment(assessment_id: str, user: dict = Depends(get_current_user)):
    """Get a single PCOD assessment report for reopening."""
    service = PCODService()
    result = await service.get_assessment(user["user_id"], assessment_id)
    if not result:
        raise HTTPException(404, "Assessment not found")
    return PCODAssessmentDetailResponse(**result)
