"""
CareSlot — PCOD/PCOS Assessment Pydantic Models
Request/response schemas for hormonal health risk assessment.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
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
    period_frequency: Optional[str] = Field(
        None,
        description="How often do you get periods? e.g., 'monthly', 'every 2-3 months', 'rarely'",
    )
    heavy_bleeding: bool = Field(False, description="Do you experience heavy menstrual bleeding?")

    # Physical Symptoms
    weight_gain: bool = Field(..., description="Have you experienced unexplained weight gain?")
    acne: bool = Field(..., description="Do you have persistent acne?")
    facial_hair_growth: bool = Field(..., description="Do you notice excessive facial hair growth?")
    hair_thinning: bool = Field(..., description="Are you experiencing hair thinning or loss?")
    skin_darkening: bool = Field(
        False, description="Do you have dark patches on skin (acanthosis nigricans)?"
    )

    # Systemic Symptoms
    fatigue: bool = Field(..., description="Do you experience chronic fatigue?")
    mood_swings: bool = Field(..., description="Do you have frequent mood swings?")
    pelvic_pain: bool = Field(False, description="Do you experience pelvic pain?")
    sleep_issues: bool = Field(False, description="Do you have sleep disturbances?")

    # Medical History
    insulin_resistance_history: bool = Field(
        False, description="Do you have a history of insulin resistance?"
    )
    diabetes_family_history: bool = Field(
        False, description="Is there diabetes in your family history?"
    )
    thyroid_issues: bool = Field(False, description="Do you have known thyroid issues?")
    pcos_family_history: bool = Field(
        False, description="Is there PCOS/PCOD in your family history?"
    )

    # Lifestyle
    exercise_frequency: Optional[str] = Field(
        None, description="How often do you exercise? e.g., 'daily', 'weekly', 'rarely'"
    )
    stress_level: Optional[str] = Field(
        None, description="Your stress level: 'low', 'moderate', 'high'"
    )

    # Additional
    age: Optional[int] = Field(None, ge=10, le=60, description="Your age")
    additional_notes: Optional[str] = None


# ─── Response Schemas ─────────────────────────────────────────────────

class PCODAssessmentResponse(BaseModel):
    """PCOD/PCOS risk assessment result."""
    risk_level: PCODRiskLevel = Field(..., description="Overall risk level")
    risk_score: float = Field(..., ge=0.0, le=1.0, description="Numerical risk score")
    conditions_flagged: List[str] = Field(
        default_factory=list,
        description="Conditions flagged: PCOD, PCOS, thyroid risk, etc.",
    )
    key_indicators: List[str] = Field(
        default_factory=list,
        description="Key symptoms/indicators contributing to assessment",
    )
    precautions: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    recommended_specialist: str = Field(
        default="Gynecologist / Endocrinologist",
        description="Recommended specialist to consult",
    )
    assessment_id: Optional[str] = None
    disclaimer: str = Field(
        default="This is a risk assessment tool only, NOT a diagnosis. Please consult a gynecologist or endocrinologist for proper evaluation and diagnosis.",
    )

class PCODHistoryItem(BaseModel):
    """Past PCOD assessment record."""
    id: str
    risk_level: str
    risk_score: float
    conditions_flagged: List[str]
    created_at: Optional[datetime] = None

class PCODHistoryResponse(BaseModel):
    """List of past PCOD assessments."""
    assessments: List[PCODHistoryItem]
    total: int
