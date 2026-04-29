"""
CareSlot — Chat Pydantic Models
Request/response schemas for the AI symptom chatbot.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ─── Request Schemas ──────────────────────────────────────────────────

class SymptomAnalysisRequest(BaseModel):
    """Single symptom analysis request."""
    symptoms: str = Field(
        ...,
        description="Comma-separated or natural language symptoms description",
        examples=["chest pain and breathing difficulty"],
    )
    additional_context: Optional[str] = Field(
        None,
        description="Additional context like duration, severity, medical history",
    )

class ChatConversationRequest(BaseModel):
    """Multi-turn chat conversation request."""
    message: str = Field(..., description="User's message")
    session_id: Optional[str] = Field(
        None,
        description="Session ID for continuing a conversation. Omit for new session.",
    )


# ─── Response Schemas ─────────────────────────────────────────────────

class SymptomAnalysisResponse(BaseModel):
    """Structured symptom analysis result."""
    prediction: str = Field(..., description="Possible health condition identified")
    risk_level: RiskLevel = Field(..., description="Urgency/risk level assessment")
    precautions: List[str] = Field(default_factory=list, description="Recommended precautions")
    home_remedies: List[str] = Field(default_factory=list, description="Safe home remedies")
    recommended_specialist: str = Field(..., description="Type of specialist to consult")
    next_steps: List[str] = Field(default_factory=list, description="Recommended next steps")
    disclaimer: str = Field(
        default="This is preliminary guidance only. Please consult a qualified healthcare professional for proper diagnosis and treatment.",
        description="Medical disclaimer",
    )
    session_id: Optional[str] = None
    prediction_id: Optional[str] = None

class ChatMessageResponse(BaseModel):
    """Single chat message in conversation history."""
    role: str
    message: str
    metadata: Optional[dict] = None
    created_at: Optional[datetime] = None

class ChatConversationResponse(BaseModel):
    """Response for multi-turn chat."""
    response: str
    session_id: str
    risk_level: Optional[RiskLevel] = None
    recommended_specialist: Optional[str] = None
    metadata: Optional[dict] = None

class ChatHistoryResponse(BaseModel):
    """List of past chat sessions."""
    sessions: List[dict]
    total: int
