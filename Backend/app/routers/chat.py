"""
CareSlot — Chat Router
Endpoints for AI symptom chatbot and conversation.
"""

from fastapi import APIRouter, Depends
from app.models.chat import (
    SymptomAnalysisRequest, SymptomAnalysisResponse,
    ChatConversationRequest, ChatConversationResponse, ChatHistoryResponse,
)
from app.services.chat_service import ChatService
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/chat", tags=["AI Symptom Chatbot"])


@router.post("/symptom-analysis", response_model=SymptomAnalysisResponse)
async def analyze_symptoms(request: SymptomAnalysisRequest, user: dict = Depends(get_current_user)):
    """
    Analyze symptoms using RAG + Llama 3.1.
    Returns preliminary health guidance with risk assessment.
    """
    service = ChatService()
    result = await service.analyze_symptoms(
        user_id=user["user_id"],
        symptoms=request.symptoms,
        additional_context=request.additional_context or "",
    )
    return SymptomAnalysisResponse(**result)


@router.post("/conversation", response_model=ChatConversationResponse)
async def chat_conversation(request: ChatConversationRequest, user: dict = Depends(get_current_user)):
    """Multi-turn health conversation with AI assistant."""
    service = ChatService()
    result = await service.chat_conversation(
        user_id=user["user_id"],
        message=request.message,
        session_id=request.session_id,
    )
    return ChatConversationResponse(**result)


@router.get("/history", response_model=ChatHistoryResponse)
async def get_chat_history(limit: int = 20, user: dict = Depends(get_current_user)):
    """Get past chat sessions."""
    service = ChatService()
    return await service.get_chat_history(user["user_id"], limit=limit)
