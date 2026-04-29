"""
CareSlot — PCOD Assessment Router
Endpoints for PCOD/PCOS risk assessment.
"""

from fastapi import APIRouter, Depends
from app.models.pcod import PCODQuestionnaireRequest, PCODAssessmentResponse, PCODHistoryResponse
from app.services.pcod_service import PCODService
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/pcod", tags=["PCOD/PCOS Assessment"])


@router.post("/assess", response_model=PCODAssessmentResponse)
async def assess_pcod(request: PCODQuestionnaireRequest, user: dict = Depends(get_current_user)):
    """
    Submit PCOD/PCOS risk assessment questionnaire.
    Returns risk level, flagged conditions, and specialist recommendations.
    This is a RISK ASSESSMENT, not a diagnosis.
    """
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
