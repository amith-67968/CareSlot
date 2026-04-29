"""
CareSlot — Skin Detection Pydantic Models
Request/response schemas for skin disease detection.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class SeverityLevel(str, Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"


class SkinDiseaseClass(str, Enum):
    """HAM10000 dataset classes mapped to readable names."""
    AKIEC = "akiec"   # Actinic Keratoses / Intraepithelial Carcinoma
    BCC = "bcc"       # Basal Cell Carcinoma
    BKL = "bkl"       # Benign Keratosis
    DF = "df"          # Dermatofibroma
    MEL = "mel"       # Melanoma
    NV = "nv"          # Melanocytic Nevi
    VASC = "vasc"     # Vascular Lesions


# Human-readable class names
SKIN_CLASS_NAMES = {
    "akiec": "Actinic Keratoses / Intraepithelial Carcinoma",
    "bcc": "Basal Cell Carcinoma",
    "bkl": "Benign Keratosis (Solar Lentigo / Seborrheic Keratosis)",
    "df": "Dermatofibroma",
    "mel": "Melanoma",
    "nv": "Melanocytic Nevi (Mole)",
    "vasc": "Vascular Lesion (Angioma / Pyogenic Granuloma)",
}

# Severity mapping per class
SKIN_CLASS_SEVERITY = {
    "akiec": "severe",
    "bcc": "severe",
    "bkl": "mild",
    "df": "mild",
    "mel": "severe",
    "nv": "mild",
    "vasc": "moderate",
}


# ─── Request Schemas ──────────────────────────────────────────────────

class SkinSymptomsInput(BaseModel):
    """Accompanying symptoms for skin analysis."""
    itching: bool = False
    redness: bool = False
    pain: bool = False
    burning_sensation: bool = False
    fever: bool = False
    swelling: bool = False
    duration: Optional[str] = Field(None, description="e.g., '3 days', '2 weeks'")
    affected_body_part: Optional[str] = Field(None, description="e.g., 'face', 'left arm'")
    allergy_history: Optional[str] = Field(None, description="Known allergies")
    additional_notes: Optional[str] = None


# ─── Response Schemas ─────────────────────────────────────────────────

class SkinAnalysisResponse(BaseModel):
    """Complete skin disease analysis result."""
    predicted_condition: str = Field(..., description="Detected skin condition")
    predicted_class: str = Field(..., description="Model classification label")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Model confidence")
    severity_level: SeverityLevel
    combined_assessment: Optional[str] = Field(None, description="LLM plain-English explanation")
    urgency_level: str = Field(default="low", description="low / medium / high")
    possible_causes: List[str] = Field(default_factory=list)
    is_urgent: bool = False
    precautions: List[str] = Field(default_factory=list)
    home_remedies: List[str] = Field(default_factory=list)
    recommended_specialist: str = "Dermatologist"
    next_steps: List[str] = Field(default_factory=list)
    symptoms_summary: List[str] = Field(default_factory=list, description="Echo of active symptoms")
    all_predictions: Optional[Dict[str, float]] = Field(None, description="Top-N class probabilities")
    image_url: Optional[str] = None
    prediction_id: Optional[str] = None
    disclaimer: str = Field(
        default="This is a preliminary AI assessment only. It is NOT a medical diagnosis. "
                "Please consult a qualified dermatologist for accurate evaluation and treatment.",
    )


class SkinHistoryItem(BaseModel):
    """Past skin analysis record."""
    id: str
    predicted_condition: str
    confidence_score: float
    severity_level: str
    image_url: Optional[str] = None
    created_at: Optional[datetime] = None


class SkinHistoryResponse(BaseModel):
    """List of past skin analyses."""
    predictions: List[SkinHistoryItem]
    total: int


class SkinPredictionDetailResponse(BaseModel):
    """Full detail for a single skin analysis report (reopening)."""
    id: str
    user_id: str
    predicted_condition: str
    predicted_class: Optional[str] = None
    confidence_score: float
    severity_level: str
    combined_assessment: Optional[str] = None
    urgency_level: str = "low"
    possible_causes: List[str] = Field(default_factory=list)
    is_urgent: bool = False
    precautions: List[str] = Field(default_factory=list)
    home_remedies: List[str] = Field(default_factory=list)
    recommended_specialist: str = "Dermatologist"
    next_steps: List[str] = Field(default_factory=list)
    symptoms_summary: List[str] = Field(default_factory=list)
    all_predictions: Optional[Dict[str, float]] = None
    image_url: Optional[str] = None
    prediction_id: Optional[str] = None
    disclaimer: str = Field(
        default="This is a preliminary AI assessment only. It is NOT a medical diagnosis. "
                "Please consult a qualified dermatologist for accurate evaluation and treatment.",
    )
    created_at: Optional[datetime] = None
