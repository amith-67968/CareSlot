"""
CareSlot — PCOD Assessment Service
Orchestrates PCOD/PCOS risk assessment with HuggingFace + Ollama LLM.
"""

from app.ai.pcod_model import assess_pcod_risk, build_symptom_text
from app.services.supabase_service import SupabaseService
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class PCODService:
    """Service for PCOD/PCOS risk assessment."""

    def __init__(self):
        self.supabase = SupabaseService()

    async def run_assessment(
        self, user_id: str, questionnaire: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run PCOD/PCOS risk assessment: HuggingFace + Ollama LLM."""
        # 1. Run rule-based + HuggingFace assessment
        hf_result = await assess_pcod_risk(questionnaire)

        # 2. Run Ollama LLM for explanation (optional — graceful failure)
        llm_result = {}
        try:
            from app.ai.chains import run_pcod_analysis
            symptoms_text = build_symptom_text(questionnaire)
            llm_result = await run_pcod_analysis(
                risk_level=hf_result["risk_level"],
                risk_score=hf_result["risk_score"],
                conditions_flagged=hf_result["conditions_flagged"],
                key_indicators=hf_result["key_indicators"],
                symptoms_text=symptoms_text,
            )
        except Exception as e:
            logger.warning(f"Ollama LLM analysis skipped: {e}")
            llm_result = {
                "combined_assessment": "AI explanation is temporarily unavailable. Please consult a specialist for detailed guidance.",
                "urgency_level": hf_result["risk_level"],
                "possible_causes": [],
                "lifestyle_recommendations": [],
                "dietary_suggestions": [],
                "exercise_recommendations": [],
                "hormonal_insights": "",
                "fertility_note": "",
                "doctor_consultation_needed": hf_result["risk_level"] in ("medium", "high"),
                "urgent": hf_result["risk_level"] == "high",
            }

        # 3. Store assessment in database
        assessment_data = {
            "user_id": user_id,
            "questionnaire_responses": questionnaire,
            "risk_level": hf_result["risk_level"],
            "risk_score": hf_result["risk_score"],
            "conditions_flagged": hf_result["conditions_flagged"],
            "precautions": hf_result["precautions"],
            "recommendations": hf_result["recommendations"],
            "recommended_specialist": hf_result["recommended_specialist"],
        }

        # Try storing with ai_response, fall back without it
        assessment_id = None
        try:
            assessment_data["ai_response"] = {
                "hf_result": hf_result,
                "llm_analysis": llm_result,
            }
            stored = self.supabase.insert("pcod_assessments", assessment_data)
            assessment_id = stored[0]["id"] if stored else None
        except Exception as e:
            logger.warning(f"Insert with ai_response failed, retrying without: {e}")
            try:
                assessment_data.pop("ai_response", None)
                stored = self.supabase.insert("pcod_assessments", assessment_data)
                assessment_id = stored[0]["id"] if stored else None
            except Exception as e2:
                logger.error(f"Failed to store PCOD assessment: {e2}")

        # 4. Build enriched response
        return {
            "risk_level": hf_result["risk_level"],
            "risk_score": round(hf_result["risk_score"], 3),
            "conditions_flagged": hf_result["conditions_flagged"],
            "key_indicators": hf_result.get("key_indicators", []),
            "combined_assessment": llm_result.get("combined_assessment", ""),
            "urgency_level": llm_result.get("urgency_level", hf_result["risk_level"]),
            "possible_causes": llm_result.get("possible_causes", []),
            "is_urgent": llm_result.get("urgent", False),
            "precautions": hf_result["precautions"],
            "recommendations": hf_result["recommendations"],
            "lifestyle_recommendations": llm_result.get("lifestyle_recommendations", []),
            "dietary_suggestions": llm_result.get("dietary_suggestions", []),
            "exercise_recommendations": llm_result.get("exercise_recommendations", []),
            "hormonal_insights": llm_result.get("hormonal_insights"),
            "fertility_note": llm_result.get("fertility_note"),
            "recommended_specialist": hf_result["recommended_specialist"],
            "assessment_id": assessment_id,
        }

    async def get_assessment(self, user_id: str, assessment_id: str) -> Optional[Dict[str, Any]]:
        """Get a single PCOD assessment for reopening a report."""
        record = self.supabase.select_one(
            "pcod_assessments",
            filters={"id": assessment_id, "user_id": user_id},
        )
        if not record:
            return None

        ai_response = record.get("ai_response") or {}
        hf_result = ai_response.get("hf_result", {})
        llm_analysis = ai_response.get("llm_analysis", {})

        return {
            "id": record["id"],
            "user_id": record["user_id"],
            "risk_level": record.get("risk_level", "low"),
            "risk_score": record.get("risk_score", 0),
            "conditions_flagged": record.get("conditions_flagged", []),
            "key_indicators": hf_result.get("key_indicators", []),
            "combined_assessment": llm_analysis.get("combined_assessment"),
            "urgency_level": llm_analysis.get("urgency_level", record.get("risk_level", "low")),
            "possible_causes": llm_analysis.get("possible_causes", []),
            "is_urgent": llm_analysis.get("urgent", False),
            "precautions": record.get("precautions", []),
            "recommendations": record.get("recommendations", []),
            "lifestyle_recommendations": llm_analysis.get("lifestyle_recommendations", []),
            "dietary_suggestions": llm_analysis.get("dietary_suggestions", []),
            "exercise_recommendations": llm_analysis.get("exercise_recommendations", []),
            "hormonal_insights": llm_analysis.get("hormonal_insights"),
            "fertility_note": llm_analysis.get("fertility_note"),
            "recommended_specialist": record.get("recommended_specialist", "Gynecologist"),
            "assessment_id": record["id"],
            "questionnaire_responses": record.get("questionnaire_responses"),
            "created_at": record.get("created_at"),
        }

    async def get_history(self, user_id: str) -> Dict[str, Any]:
        """Get user's PCOD assessment history."""
        assessments = self.supabase.select(
            "pcod_assessments",
            filters={"user_id": user_id},
            order_by="-created_at",
        )

        items = []
        for a in assessments:
            items.append({
                "id": a["id"],
                "risk_level": a.get("risk_level", "low"),
                "risk_score": a.get("risk_score", 0),
                "conditions_flagged": a.get("conditions_flagged", []),
                "created_at": a.get("created_at"),
            })

        return {"assessments": items, "total": len(items)}
