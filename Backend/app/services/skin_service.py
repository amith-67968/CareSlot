"""
CareSlot — Skin Analysis Service
Orchestrates skin disease detection using MobileNetV2 + LLM.
"""

from app.ai.skin_model import predict_skin_disease
from app.ai.chains import run_skin_analysis
from app.services.supabase_service import SupabaseService
from app.models.skin import SkinSymptomsInput
from app.config import get_settings
from typing import Dict, Any, Optional
import uuid
import logging

logger = logging.getLogger(__name__)


class SkinService:
    """Service for skin disease detection and analysis."""

    def __init__(self):
        self.supabase = SupabaseService()

    async def analyze_skin(
        self,
        user_id: str,
        image_bytes: bytes,
        filename: str,
        symptoms: SkinSymptomsInput,
        content_type: str = "image/jpeg",
    ) -> Dict[str, Any]:
        """
        Full skin analysis pipeline:
        1. Upload image to Supabase Storage
        2. Run MobileNetV2 prediction
        3. Combine with symptoms via LLM
        4. Store results
        """
        # 1. Upload image to Supabase Storage
        image_id = str(uuid.uuid4())
        storage_path = f"skin-images/{user_id}/{image_id}_{filename}"

        try:
            self.supabase.upload_file("skin-uploads", storage_path, image_bytes, content_type)
            public_url = self.supabase.get_public_url("skin-uploads", storage_path)
        except Exception as e:
            logger.error(f"Image upload failed: {e}")
            public_url = None

        # Store image record
        image_record = None
        try:
            image_result = self.supabase.insert("uploaded_images", {
                "user_id": user_id,
                "storage_path": storage_path,
                "public_url": public_url,
                "image_type": "skin",
            })
            image_record = image_result[0] if image_result else None
        except Exception as e:
            logger.error(f"Image record insert failed: {e}")

        # 2. Run MobileNetV2 prediction
        model_result = predict_skin_disease(image_bytes)

        # 3. Build symptoms text for LLM
        symptoms_text = self._build_symptoms_text(symptoms)
        symptoms_summary = self._symptoms_to_list(symptoms)

        # 4. Build combined analysis. Deterministic guidance is fast and is the
        # default; local LLM explanations can be enabled when richer text matters.
        llm_result = self._build_fast_skin_analysis(model_result, symptoms_summary, symptoms_text)
        if get_settings().ENABLE_LLM_EXPLANATIONS:
            llm_result = await run_skin_analysis(
                model_prediction=model_result["predicted_condition"],
                confidence=model_result["confidence"],
                symptoms_text=symptoms_text,
            )

        # 5. Store prediction result
        prediction_data = {
            "user_id": user_id,
            "prediction_type": "skin_detection",
            "input_symptoms": symptoms_summary,
            "image_id": image_record["id"] if image_record else None,
            "predicted_condition": model_result["predicted_condition"],
            "confidence_score": model_result["confidence"],
            "risk_level": self._severity_to_risk(model_result["severity"]),
            "precautions": llm_result.get("precautions", []),
            "home_remedies": llm_result.get("home_remedies", []),
            "recommended_specialist": "Dermatologist",
            "ai_response": {
                "model_prediction": model_result,
                "llm_analysis": llm_result,
                "symptoms_summary": symptoms_summary,
            },
        }

        prediction_id = None
        try:
            stored = self.supabase.insert("disease_predictions", prediction_data)
            prediction_id = stored[0]["id"] if stored else None
        except Exception as e:
            logger.error(f"Prediction storage failed: {e}")

        # Build final response
        return {
            "predicted_condition": model_result["predicted_condition"],
            "predicted_class": model_result["predicted_class"],
            "confidence_score": model_result["confidence"],
            "severity_level": model_result["severity"],
            "combined_assessment": llm_result.get("combined_assessment", ""),
            "urgency_level": llm_result.get("urgency_level", "low"),
            "possible_causes": llm_result.get("possible_causes", []),
            "is_urgent": model_result.get("is_urgent", False) or llm_result.get("urgent", False),
            "precautions": llm_result.get("precautions", []),
            "home_remedies": llm_result.get("home_remedies", []),
            "recommended_specialist": "Dermatologist",
            "next_steps": llm_result.get("next_steps", []),
            "symptoms_summary": symptoms_summary,
            "all_predictions": model_result.get("all_predictions", {}),
            "image_url": public_url,
            "prediction_id": prediction_id,
        }

    async def get_prediction(self, user_id: str, prediction_id: str) -> Optional[Dict[str, Any]]:
        """Get a single skin analysis prediction for reopening a report."""
        record = self.supabase.select_one(
            "disease_predictions",
            filters={"id": prediction_id, "user_id": user_id},
        )
        if not record:
            return None

        ai_response = record.get("ai_response", {}) or {}
        model_pred = ai_response.get("model_prediction", {})
        llm_analysis = ai_response.get("llm_analysis", {})
        symptoms_summary = ai_response.get("symptoms_summary", record.get("input_symptoms", []))

        # Resolve image URL
        image_url = None
        if record.get("image_id"):
            try:
                img_record = self.supabase.select_one(
                    "uploaded_images",
                    filters={"id": record["image_id"]},
                )
                image_url = img_record.get("public_url") if img_record else None
            except Exception:
                pass

        return {
            "id": record["id"],
            "user_id": record["user_id"],
            "predicted_condition": record.get("predicted_condition", "Unknown"),
            "predicted_class": model_pred.get("predicted_class"),
            "confidence_score": record.get("confidence_score", 0),
            "severity_level": self._risk_to_severity(record.get("risk_level", "medium")),
            "combined_assessment": llm_analysis.get("combined_assessment"),
            "urgency_level": llm_analysis.get("urgency_level", "low"),
            "possible_causes": llm_analysis.get("possible_causes", []),
            "is_urgent": model_pred.get("is_urgent", False) or llm_analysis.get("urgent", False),
            "precautions": record.get("precautions", []),
            "home_remedies": record.get("home_remedies", []),
            "recommended_specialist": record.get("recommended_specialist", "Dermatologist"),
            "next_steps": llm_analysis.get("next_steps", []),
            "symptoms_summary": symptoms_summary,
            "all_predictions": model_pred.get("all_predictions"),
            "image_url": image_url,
            "prediction_id": record["id"],
            "created_at": record.get("created_at"),
        }

    async def get_history(self, user_id: str) -> Dict[str, Any]:
        """Get user's skin analysis history."""
        predictions = self.supabase.select(
            "disease_predictions",
            filters={"user_id": user_id, "prediction_type": "skin_detection"},
            order_by="-created_at",
        )

        # Enrich with image URLs
        items = []
        for p in predictions:
            image_url = None
            if p.get("image_id"):
                try:
                    img = self.supabase.select_one("uploaded_images", filters={"id": p["image_id"]})
                    image_url = img.get("public_url") if img else None
                except Exception:
                    pass

            items.append({
                "id": p["id"],
                "predicted_condition": p.get("predicted_condition", "Unknown"),
                "confidence_score": p.get("confidence_score", 0),
                "severity_level": self._risk_to_severity(p.get("risk_level", "medium")),
                "image_url": image_url,
                "created_at": p.get("created_at"),
            })

        return {"predictions": items, "total": len(items)}

    def _build_symptoms_text(self, symptoms: SkinSymptomsInput) -> str:
        """Build descriptive text from symptom flags."""
        parts = []
        if symptoms.itching:
            parts.append("itching")
        if symptoms.redness:
            parts.append("redness")
        if symptoms.pain:
            parts.append("pain at the site")
        if symptoms.burning_sensation:
            parts.append("burning sensation")
        if symptoms.fever:
            parts.append("fever")
        if symptoms.swelling:
            parts.append("swelling")
        if symptoms.affected_body_part:
            parts.append(f"affected area: {symptoms.affected_body_part}")
        if symptoms.duration:
            parts.append(f"duration: {symptoms.duration}")
        if symptoms.allergy_history:
            parts.append(f"allergy history: {symptoms.allergy_history}")
        if symptoms.additional_notes:
            parts.append(f"additional: {symptoms.additional_notes}")
        return ", ".join(parts) if parts else "No additional symptoms reported."

    def _symptoms_to_list(self, symptoms: SkinSymptomsInput) -> list:
        """Convert symptoms to a list of active symptom strings."""
        active = []
        for field in ["itching", "redness", "pain", "burning_sensation", "fever", "swelling"]:
            if getattr(symptoms, field, False):
                active.append(field.replace("_", " "))
        if symptoms.affected_body_part:
            active.append(f"affected: {symptoms.affected_body_part}")
        if symptoms.duration:
            active.append(f"duration: {symptoms.duration}")
        return active

    def _severity_to_risk(self, severity: str) -> str:
        """Map severity to risk level."""
        mapping = {"mild": "low", "moderate": "medium", "severe": "high"}
        return mapping.get(severity, "medium")

    def _risk_to_severity(self, risk: str) -> str:
        """Map risk level back to severity."""
        mapping = {"low": "mild", "medium": "moderate", "high": "severe"}
        return mapping.get(risk, "moderate")

    def _build_fast_skin_analysis(
        self,
        model_result: Dict[str, Any],
        symptoms_summary: list,
        symptoms_text: str,
    ) -> Dict[str, Any]:
        """Generate a useful skin report without waiting on an LLM."""
        condition = model_result["predicted_condition"]
        confidence = model_result["confidence"] * 100
        severity = model_result["severity"]
        urgent = model_result.get("is_urgent", False)

        if severity == "severe":
            urgency = "high"
            urgency_text = "This class can require prompt dermatologist review."
        elif severity == "moderate" or any(s in symptoms_summary for s in ["pain", "fever", "swelling"]):
            urgency = "medium"
            urgency_text = "A clinician review is recommended, especially if symptoms are spreading or painful."
        else:
            urgency = "low"
            urgency_text = "This often can be monitored, but a dermatologist should confirm it."

        assessment = (
            f"The image model's top match is {condition} with {confidence:.1f}% confidence. "
            f"Reported details: {symptoms_text} {urgency_text} "
            "This is not a diagnosis; skin conditions can look similar, so use this as preliminary guidance only."
        )

        precautions = [
            "Avoid scratching or picking the area",
            "Keep the area clean and dry",
            "Use sunscreen or cover the area when outdoors",
        ]
        if urgent:
            precautions.insert(0, "Arrange a dermatologist appointment as soon as possible")
        if "fever" in symptoms_summary or "swelling" in symptoms_summary:
            precautions.append("Seek care quickly if fever, swelling, warmth, or pus develops")

        return {
            "combined_assessment": assessment,
            "severity_level": severity,
            "urgency_level": urgency,
            "possible_causes": [
                "Sun exposure or UV-related skin change",
                "Inflammation or irritation",
                "Benign or malignant skin lesion pattern requiring clinical confirmation",
            ],
            "precautions": precautions,
            "home_remedies": [
                "Apply a cool compress for irritation",
                "Use a gentle fragrance-free moisturizer",
                "Avoid new harsh skincare products until reviewed",
            ],
            "recommended_specialist": "Dermatologist",
            "next_steps": [
                "Book a dermatologist consultation for confirmation",
                "Take a clear follow-up photo if the area changes",
                "Seek urgent care for rapid growth, bleeding, severe pain, fever, or spreading redness",
            ],
            "urgent": urgent,
            "doctor_consultation_needed": True,
        }
