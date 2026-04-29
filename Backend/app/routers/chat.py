"""
CareSlot — Chat Router
Endpoints for AI symptom chatbot and conversation.
"""

from fastapi import APIRouter, Depends, HTTPException
from app.models.chat import (
    SymptomAnalysisRequest, SymptomAnalysisResponse,
    ChatConversationRequest, ChatConversationResponse, ChatHistoryResponse,
)
from app.services.chat_service import ChatService
from app.dependencies import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["AI Symptom Chatbot"])


@router.post("/symptom-analysis", response_model=SymptomAnalysisResponse)
async def analyze_symptoms(request: SymptomAnalysisRequest, user: dict = Depends(get_current_user)):
    """
    Analyze symptoms using RAG + Llama 3.1.
    Returns preliminary health guidance with risk assessment.
    """
    try:
        service = ChatService()
        result = await service.analyze_symptoms(
            user_id=user["user_id"],
            symptoms=request.symptoms,
            additional_context=request.additional_context or "",
        )
        return SymptomAnalysisResponse(**result)
    except Exception as e:
        logger.error(f"Symptom analysis endpoint error: {e}", exc_info=True)
        return SymptomAnalysisResponse(
            prediction="Analysis could not be completed. Please consult a healthcare professional.",
            risk_level="medium",
            precautions=["Seek medical advice for proper evaluation"],
            home_remedies=[],
            recommended_specialist="General Physician",
            next_steps=["Visit a healthcare professional for proper diagnosis"],
        )


@router.post("/conversation", response_model=ChatConversationResponse)
async def chat_conversation(request: ChatConversationRequest, user: dict = Depends(get_current_user)):
    """Multi-turn health conversation with AI assistant."""
    try:
        service = ChatService()
        result = await service.chat_conversation(
            user_id=user["user_id"],
            message=request.message,
            session_id=request.session_id,
            latitude=request.latitude,
            longitude=request.longitude,
        )
        return ChatConversationResponse(**result)
    except Exception as e:
        logger.error(f"Chat conversation endpoint error: {e}", exc_info=True)
        return ChatConversationResponse(
            response="I'm sorry, I encountered an error. Please try again in a moment.",
            session_id=request.session_id or "error",
        )


@router.get("/history", response_model=ChatHistoryResponse)
async def get_chat_history(limit: int = 20, user: dict = Depends(get_current_user)):
    """Get past chat sessions."""
    service = ChatService()
    return await service.get_chat_history(user["user_id"], limit=limit)
