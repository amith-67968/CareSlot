"""
CareSlot — Skin Analysis Service
Orchestrates skin disease detection using MobileNetV2 + LLM.
"""

from app.ai.skin_model import predict_skin_disease
from app.ai.chains import run_skin_analysis
from app.services.supabase_service import SupabaseService
from app.models.skin import SkinSymptomsInput
from typing import Dict, Any
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

        # 4. Run combined analysis via LLM
        llm_result = await run_skin_analysis(
            model_prediction=model_result["predicted_condition"],
            confidence=model_result["confidence"],
            symptoms_text=symptoms_text,
        )

        # 5. Store prediction result
        prediction_data = {
            "user_id": user_id,
            "prediction_type": "skin_detection",
            "input_symptoms": self._symptoms_to_list(symptoms),
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
            "precautions": llm_result.get("precautions", []),
            "home_remedies": llm_result.get("home_remedies", []),
            "recommended_specialist": "Dermatologist",
            "next_steps": llm_result.get("next_steps", []),
            "image_url": public_url,
            "prediction_id": prediction_id,
            "combined_assessment": llm_result.get("combined_assessment", ""),
        }

    async def get_history(self, user_id: str) -> Dict[str, Any]:
        """Get user's skin analysis history."""
        predictions = self.supabase.select(
            "disease_predictions",
            filters={"user_id": user_id, "prediction_type": "skin_detection"},
            order_by="-created_at",
        )
        return {"predictions": predictions, "total": len(predictions)}

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
        for field in ["itching", "redness", "pain", "burning_sensation", "fever"]:
            if getattr(symptoms, field, False):
                active.append(field.replace("_", " "))
        return active

    def _severity_to_risk(self, severity: str) -> str:
        """Map severity to risk level."""
        mapping = {"mild": "low", "moderate": "medium", "severe": "high"}
        return mapping.get(severity, "medium")
