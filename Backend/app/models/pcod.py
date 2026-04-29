"""
CareSlot — PCOD/PCOS Assessment Pydantic Models
Request/response schemas for hormonal health risk assessment.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class PCODRiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ─── Request Schemas ──────────────────────────────────────────────────

class PCODQuestionnaireRequest(BaseModel):
    """Structured questionnaire input for PCOD/PCOS risk assessment."""

    # Menstrual Health
    irregular_periods: bool = Field(..., description="Do you experience irregular periods?")
    period_frequency: Optional[str] = Field(None, description="How often do you get periods?")
    heavy_bleeding: bool = Field(False, description="Do you experience heavy menstrual bleeding?")

    # Physical Symptoms
    weight_gain: bool = Field(..., description="Have you experienced unexplained weight gain?")
    acne: bool = Field(..., description="Do you have persistent acne?")
    facial_hair_growth: bool = Field(..., description="Do you notice excessive facial hair growth?")
    hair_thinning: bool = Field(..., description="Are you experiencing hair thinning or loss?")
    skin_darkening: bool = Field(False, description="Do you have dark patches on skin?")

    # Systemic Symptoms
    fatigue: bool = Field(..., description="Do you experience chronic fatigue?")
    mood_swings: bool = Field(..., description="Do you have frequent mood swings?")
    pelvic_pain: bool = Field(False, description="Do you experience pelvic pain?")
    sleep_issues: bool = Field(False, description="Do you have sleep disturbances?")

    # Medical History
    insulin_resistance_history: bool = Field(False, description="History of insulin resistance?")
    diabetes_family_history: bool = Field(False, description="Family history of diabetes?")
    thyroid_issues: bool = Field(False, description="Known thyroid issues?")
    pcos_family_history: bool = Field(False, description="Family history of PCOS/PCOD?")

    # Lifestyle
    exercise_frequency: Optional[str] = Field(None, description="daily, weekly, rarely")
    stress_level: Optional[str] = Field(None, description="low, moderate, high")

    # Additional
    age: Optional[int] = Field(None, ge=10, le=60, description="Your age")
    additional_notes: Optional[str] = None


# ─── Response Schemas ─────────────────────────────────────────────────

class PCODAssessmentResponse(BaseModel):
    """PCOD/PCOS risk assessment result with LLM explanation."""
    risk_level: PCODRiskLevel = Field(..., description="Overall risk level")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Numerical risk score")
    conditions_flagged: List[str] = Field(default_factory=list)
    key_indicators: List[str] = Field(default_factory=list)
    combined_assessment: Optional[str] = Field(None, description="LLM plain-English explanation")
    urgency_level: str = Field(default="low", description="low / medium / high")
    possible_causes: List[str] = Field(default_factory=list)
    is_urgent: bool = False
    precautions: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    lifestyle_recommendations: List[str] = Field(default_factory=list)
    dietary_suggestions: List[str] = Field(default_factory=list)
    exercise_recommendations: List[str] = Field(default_factory=list)
    hormonal_insights: Optional[str] = None
    fertility_note: Optional[str] = None
    recommended_specialist: str = Field(default="Gynecologist / Endocrinologist")
    assessment_id: Optional[str] = None
    disclaimer: str = Field(
        default="This is a risk assessment tool only, NOT a diagnosis. "
                "Please consult a gynecologist or endocrinologist for proper evaluation and diagnosis.",
    )


class PCODHistoryItem(BaseModel):
    """Past PCOD assessment record."""
    id: str
    risk_level: str
    risk_score: float
    conditions_flagged: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None


class PCODHistoryResponse(BaseModel):
    """List of past PCOD assessments."""
    assessments: List[PCODHistoryItem]
    total: int


class PCODAssessmentDetailResponse(BaseModel):
    """Full detail for a single PCOD assessment report (reopening)."""
    id: str
    user_id: str
    risk_level: str
    risk_score: float
    conditions_flagged: List[str] = Field(default_factory=list)
    key_indicators: List[str] = Field(default_factory=list)
    combined_assessment: Optional[str] = None
    urgency_level: str = "low"
    possible_causes: List[str] = Field(default_factory=list)
    is_urgent: bool = False
    precautions: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    lifestyle_recommendations: List[str] = Field(default_factory=list)
    dietary_suggestions: List[str] = Field(default_factory=list)
    exercise_recommendations: List[str] = Field(default_factory=list)
    hormonal_insights: Optional[str] = None
    fertility_note: Optional[str] = None
    recommended_specialist: str = "Gynecologist / Endocrinologist"
    assessment_id: Optional[str] = None
    questionnaire_responses: Optional[Dict[str, Any]] = None
    disclaimer: str = Field(
        default="This is a risk assessment tool only, NOT a diagnosis. "
                "Please consult a gynecologist or endocrinologist for proper evaluation and diagnosis.",
    )
    created_at: Optional[datetime] = None
