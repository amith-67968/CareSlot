"""
CareSlot — PCOD Assessment Service
Orchestrates PCOD/PCOS risk assessment with HuggingFace + Ollama LLM.
"""

from app.ai.pcod_model import assess_pcod_risk, build_symptom_text
from app.services.supabase_service import SupabaseService
from app.config import get_settings
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
        symptoms_text = build_symptom_text(questionnaire)
        llm_result = _build_fast_pcod_guidance(hf_result, symptoms_text)

        if get_settings().ENABLE_LLM_EXPLANATIONS:
            try:
                from app.ai.chains import run_pcod_analysis
                llm_result = await run_pcod_analysis(
                    risk_level=hf_result["risk_level"],
                    risk_score=hf_result["risk_score"],
                    conditions_flagged=hf_result["conditions_flagged"],
                    key_indicators=hf_result["key_indicators"],
                    symptoms_text=symptoms_text,
                )
            except Exception as e:
                logger.warning(f"Ollama LLM analysis skipped: {e}")

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


def _build_fast_pcod_guidance(hf_result: Dict[str, Any], symptoms_text: str) -> Dict[str, Any]:
    """Generate PCOD/PCOS report details without waiting on an LLM."""
    risk_level = hf_result["risk_level"]
    risk_score = hf_result["risk_score"]
    conditions = hf_result.get("conditions_flagged", [])
    indicators = hf_result.get("key_indicators", [])

    condition_text = ", ".join(conditions) if conditions else "no major condition pattern"
    indicator_text = ", ".join(indicators[:4]) if indicators else "the answers provided"

    if risk_level == "high":
        urgency = "high"
        opening = "Your answers show a high PCOD/PCOS-related risk pattern."
    elif risk_level == "medium":
        urgency = "medium"
        opening = "Your answers show a moderate PCOD/PCOS-related risk pattern."
    else:
        urgency = "low"
        opening = "Your answers currently suggest a lower PCOD/PCOS-related risk pattern."

    combined = (
        f"{opening} The score is {risk_score * 100:.1f}%, with {condition_text} flagged. "
        f"The main indicators considered were {indicator_text}. {symptoms_text} "
        "This screening cannot diagnose PCOD or PCOS, but it can help you decide what to discuss "
        "with a gynecologist or endocrinologist."
    )

    causes = [
        "Hormonal imbalance involving androgens",
        "Insulin resistance or blood sugar regulation issues",
        "Family history and genetic tendency",
    ]
    if "Thyroid Risk" in conditions:
        causes.append("Possible thyroid hormone imbalance")
    if not conditions:
        causes = ["Lifestyle, stress, sleep, or temporary hormonal variation"]

    return {
        "combined_assessment": combined,
        "urgency_level": urgency,
        "possible_causes": causes,
        "lifestyle_recommendations": [
            "Track menstrual cycle patterns and symptoms",
            "Keep a consistent sleep schedule",
            "Manage stress with breathing exercises, yoga, or light activity",
        ],
        "dietary_suggestions": [
            "Prefer high-fiber meals with vegetables, pulses, and whole grains",
            "Limit refined sugar and highly processed foods",
            "Include lean protein with meals to support steady energy",
        ],
        "exercise_recommendations": [
            "Aim for 30 minutes of moderate activity most days",
            "Add strength training 2-3 times per week if comfortable",
            "Start gently if fatigue or pelvic discomfort is present",
        ],
        "hormonal_insights": (
            "PCOD/PCOS symptoms can be linked with androgen levels, ovulation patterns, insulin resistance, "
            "and sometimes thyroid function. Blood tests and clinical evaluation are needed to confirm causes."
        ),
        "fertility_note": (
            "Cycle irregularity can affect ovulation, but many people manage symptoms well with medical guidance."
            if risk_level in ("medium", "high") else
            "Not applicable"
        ),
        "doctor_consultation_needed": risk_level in ("medium", "high"),
        "urgent": risk_level == "high",
    }
