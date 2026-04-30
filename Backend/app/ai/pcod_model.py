"""
CareSlot — PCOD/PCOS Risk Assessment Model
Uses HuggingFace zero-shot classification for hormonal health risk assessment.
"""

from typing import Dict, Any, List
from app.config import get_settings
import logging

logger = logging.getLogger(__name__)

_classifier = None

# Risk factor weights for scoring
RISK_WEIGHTS = {
    "irregular_periods": 0.15,
    "weight_gain": 0.10,
    "acne": 0.08,
    "facial_hair_growth": 0.12,
    "hair_thinning": 0.08,
    "fatigue": 0.06,
    "mood_swings": 0.05,
    "pelvic_pain": 0.07,
    "insulin_resistance_history": 0.12,
    "diabetes_family_history": 0.05,
    "thyroid_issues": 0.08,
    "pcos_family_history": 0.10,
    "heavy_bleeding": 0.06,
    "skin_darkening": 0.08,
    "sleep_issues": 0.04,
}

# Condition candidate labels for zero-shot classification
CONDITION_LABELS = [
    "Polycystic Ovary Syndrome (PCOS)",
    "Polycystic Ovarian Disease (PCOD)",
    "Thyroid Disorder",
    "Insulin Resistance",
    "Hormonal Imbalance",
    "Normal Hormonal Health",
]


def load_pcod_classifier():
    """Load the HuggingFace zero-shot classification pipeline."""
    global _classifier
    if _classifier is not None:
        return _classifier

    from transformers import pipeline

    logger.info("Loading HuggingFace zero-shot classification model...")
    _classifier = pipeline(
        "zero-shot-classification",
        model="facebook/bart-large-mnli",
        device=-1,  # CPU
    )
    logger.info("PCOD classifier loaded successfully")
    return _classifier


def calculate_risk_score(questionnaire: Dict[str, Any]) -> float:
    """Calculate a weighted risk score from questionnaire responses."""
    score = 0.0
    for field, weight in RISK_WEIGHTS.items():
        value = questionnaire.get(field, False)
        if isinstance(value, bool) and value:
            score += weight
    return min(score, 1.0)


def determine_risk_level(score: float) -> str:
    """Determine risk level from numerical score."""
    if score >= 0.6:
        return "high"
    elif score >= 0.35:
        return "medium"
    return "low"


def get_flagged_conditions(questionnaire: Dict[str, Any], score: float) -> List[str]:
    """Determine which conditions are flagged based on symptom patterns."""
    conditions = []

    # PCOS indicators
    pcos_symptoms = ["irregular_periods", "facial_hair_growth", "acne", "weight_gain"]
    pcos_count = sum(1 for s in pcos_symptoms if questionnaire.get(s, False))
    if pcos_count >= 3:
        conditions.append("PCOS")
    elif pcos_count >= 2:
        conditions.append("PCOD")

    # Thyroid indicators
    thyroid_symptoms = ["fatigue", "weight_gain", "hair_thinning", "mood_swings"]
    if questionnaire.get("thyroid_issues") or sum(
        1 for s in thyroid_symptoms if questionnaire.get(s, False)
    ) >= 3:
        conditions.append("Thyroid Risk")

    # Insulin resistance
    if questionnaire.get("insulin_resistance_history") or (
        questionnaire.get("diabetes_family_history")
        and questionnaire.get("weight_gain")
        and questionnaire.get("skin_darkening", False)
    ):
        conditions.append("Insulin Resistance Risk")

    # Hormonal imbalance (general)
    if score >= 0.3 and not conditions:
        conditions.append("Hormonal Imbalance")

    return conditions


def build_symptom_text(questionnaire: Dict[str, Any]) -> str:
    """Convert questionnaire responses into a descriptive text for NLP."""
    symptom_descriptions = {
        "irregular_periods": "experiencing irregular menstrual periods",
        "heavy_bleeding": "heavy menstrual bleeding",
        "weight_gain": "unexplained weight gain",
        "acne": "persistent acne breakouts",
        "facial_hair_growth": "excessive facial hair growth (hirsutism)",
        "hair_thinning": "hair thinning and hair loss",
        "skin_darkening": "dark patches on skin (acanthosis nigricans)",
        "fatigue": "chronic fatigue and low energy",
        "mood_swings": "frequent mood swings",
        "pelvic_pain": "pelvic pain and discomfort",
        "sleep_issues": "sleep disturbances and insomnia",
        "insulin_resistance_history": "history of insulin resistance",
        "diabetes_family_history": "family history of diabetes",
        "thyroid_issues": "known thyroid problems",
        "pcos_family_history": "family history of PCOS/PCOD",
    }

    active = [desc for key, desc in symptom_descriptions.items() if questionnaire.get(key, False)]

    if not active:
        return "No significant symptoms reported."

    return f"Patient is {', '.join(active)}."


async def assess_pcod_risk(questionnaire: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run PCOD/PCOS risk assessment.

    Args:
        questionnaire: Dict of questionnaire responses.

    Returns:
        Assessment results with risk level, score, conditions, and recommendations.
    """
    # Calculate weighted risk score
    risk_score = calculate_risk_score(questionnaire)
    risk_level = determine_risk_level(risk_score)
    flagged_conditions = get_flagged_conditions(questionnaire, risk_score)

    # HuggingFace zero-shot classification is accurate but very slow on CPU.
    # Keep it opt-in; the weighted rule-based assessment above is the fast path.
    if get_settings().ENABLE_PCOD_ZERO_SHOT:
        symptom_text = build_symptom_text(questionnaire)
        classifier = load_pcod_classifier()

        try:
            classification = classifier(symptom_text, CONDITION_LABELS, multi_label=True)
            # Merge HF results with rule-based assessment
            hf_conditions = [
                label for label, score in zip(classification["labels"], classification["scores"])
                if score > 0.4 and "Normal" not in label
            ]

            # Combine and deduplicate
            for cond in hf_conditions:
                short_name = cond.split("(")[-1].rstrip(")") if "(" in cond else cond
                if short_name not in flagged_conditions and cond not in flagged_conditions:
                    flagged_conditions.append(short_name)

        except Exception as e:
            logger.error(f"HuggingFace classification error: {e}")

    # Build key indicators
    key_indicators = [
        key.replace("_", " ").title()
        for key, weight in sorted(RISK_WEIGHTS.items(), key=lambda x: x[1], reverse=True)
        if questionnaire.get(key, False)
    ]

    # Generate recommendations
    precautions = _get_precautions(risk_level, flagged_conditions)
    recommendations = _get_recommendations(risk_level, flagged_conditions, questionnaire)

    return {
        "risk_level": risk_level,
        "risk_score": round(risk_score, 3),
        "conditions_flagged": flagged_conditions,
        "key_indicators": key_indicators[:5],
        "precautions": precautions,
        "recommendations": recommendations,
        "recommended_specialist": _get_specialist(flagged_conditions),
    }


def _get_precautions(risk_level: str, conditions: List[str]) -> List[str]:
    """Generate precautions based on risk level and conditions."""
    precautions = [
        "Maintain a balanced diet rich in whole grains, lean protein, and vegetables",
        "Exercise regularly — aim for at least 30 minutes of moderate activity daily",
        "Manage stress through meditation, yoga, or breathing exercises",
        "Maintain a consistent sleep schedule (7-8 hours per night)",
    ]
    if risk_level in ("medium", "high"):
        precautions.extend([
            "Monitor menstrual cycle patterns and keep a health diary",
            "Limit intake of processed foods, refined sugars, and trans fats",
        ])
    if "Insulin Resistance Risk" in conditions:
        precautions.append("Monitor blood sugar levels regularly")
    if risk_level == "high":
        precautions.insert(0, "Schedule an appointment with a specialist as soon as possible")
    return precautions


def _get_recommendations(risk_level: str, conditions: List[str], q: Dict) -> List[str]:
    """Generate next-step recommendations."""
    recs = []
    if risk_level == "high":
        recs.append("Seek immediate consultation with a gynecologist or endocrinologist")
        recs.append("Request blood tests: hormonal panel, thyroid function, fasting insulin")
        recs.append("Consider pelvic ultrasound examination")
    elif risk_level == "medium":
        recs.append("Schedule a gynecologist appointment for evaluation")
        recs.append("Request basic hormonal blood work")
    else:
        recs.append("Continue healthy lifestyle practices")
        recs.append("Regular annual gynecological check-ups recommended")

    if "Thyroid Risk" in conditions:
        recs.append("Request thyroid function tests (TSH, T3, T4)")
    if q.get("insulin_resistance_history") or "Insulin Resistance" in str(conditions):
        recs.append("Consult an endocrinologist about insulin management")
    return recs


def _get_specialist(conditions: List[str]) -> str:
    """Determine recommended specialist based on conditions."""
    if "Thyroid Risk" in conditions or "Insulin Resistance Risk" in conditions:
        return "Endocrinologist"
    if any(c in str(conditions) for c in ["PCOS", "PCOD"]):
        return "Gynecologist / Endocrinologist"
    return "Gynecologist"
