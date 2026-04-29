"""
CareSlot — PCOD Assessment Service
Orchestrates PCOD/PCOS risk assessment.
"""

from app.ai.pcod_model import assess_pcod_risk
from app.services.supabase_service import SupabaseService
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class PCODService:
    """Service for PCOD/PCOS risk assessment."""

    def __init__(self):
        self.supabase = SupabaseService()

    async def run_assessment(
        self, user_id: str, questionnaire: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run PCOD/PCOS risk assessment and store results."""
        # Run the AI assessment
        result = await assess_pcod_risk(questionnaire)

        # Store assessment in database
        assessment_data = {
            "user_id": user_id,
            "questionnaire_responses": questionnaire,
            "risk_level": result["risk_level"],
            "risk_score": result["risk_score"],
            "conditions_flagged": result["conditions_flagged"],
            "precautions": result["precautions"],
            "recommendations": result["recommendations"],
            "recommended_specialist": result["recommended_specialist"],
        }

        assessment_id = None
        try:
            stored = self.supabase.insert("pcod_assessments", assessment_data)
            assessment_id = stored[0]["id"] if stored else None
        except Exception as e:
            logger.error(f"Failed to store PCOD assessment: {e}")

        result["assessment_id"] = assessment_id
        return result

    async def get_history(self, user_id: str) -> Dict[str, Any]:
        """Get user's PCOD assessment history."""
        assessments = self.supabase.select(
            "pcod_assessments",
            filters={"user_id": user_id},
            order_by="-created_at",
        )
        return {"assessments": assessments, "total": len(assessments)}
