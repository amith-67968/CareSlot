"""
CareSlot — Chat Service
Orchestrates AI symptom analysis and conversation management.
"""

from app.ai.chains import run_symptom_analysis, run_conversation
from app.services.supabase_service import SupabaseService
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, AIMessage
import uuid
import logging

logger = logging.getLogger(__name__)


class ChatService:
    """Service for AI-powered health chat and symptom analysis."""

    def __init__(self):
        self.supabase = SupabaseService()

    async def analyze_symptoms(
        self,
        user_id: str,
        symptoms: str,
        additional_context: str = "",
    ) -> Dict[str, Any]:
        """
        Run symptom analysis via RAG + LLM pipeline.
        Stores the result in the database.
        """
        # Run analysis
        result = await run_symptom_analysis(symptoms, additional_context)

        # Store prediction
        session_id = str(uuid.uuid4())
        prediction_data = {
            "user_id": user_id,
            "prediction_type": "symptom_chat",
            "input_symptoms": [s.strip() for s in symptoms.split(",")],
            "predicted_condition": result.get("prediction", ""),
            "risk_level": result.get("risk_level", "medium"),
            "precautions": result.get("precautions", []),
            "home_remedies": result.get("home_remedies", []),
            "recommended_specialist": result.get("recommended_specialist", ""),
            "ai_response": result,
        }

        try:
            stored = self.supabase.insert("disease_predictions", prediction_data)
            prediction_id = stored[0]["id"] if stored else None
        except Exception as e:
            logger.error(f"Failed to store prediction: {e}")
            prediction_id = None

        # Store in chat history
        try:
            self.supabase.insert("chatbot_history", {
                "user_id": user_id,
                "session_id": session_id,
                "role": "user",
                "message": symptoms,
                "metadata": {"additional_context": additional_context},
            })
            self.supabase.insert("chatbot_history", {
                "user_id": user_id,
                "session_id": session_id,
                "role": "assistant",
                "message": result.get("prediction", ""),
                "metadata": result,
            })
        except Exception as e:
            logger.error(f"Failed to store chat history: {e}")

        result["session_id"] = session_id
        result["prediction_id"] = prediction_id
        return result

    async def chat_conversation(
        self,
        user_id: str,
        message: str,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Multi-turn conversation with chat history.
        """
        if not session_id:
            session_id = str(uuid.uuid4())

        # Load chat history for this session
        chat_history = await self._get_session_messages(user_id, session_id)

        # Convert to LangChain message objects
        lc_history = []
        for msg in chat_history:
            if msg["role"] == "user":
                lc_history.append(HumanMessage(content=msg["message"]))
            else:
                lc_history.append(AIMessage(content=msg["message"]))

        # Run conversation chain
        response = await run_conversation(message, lc_history)

        # Store messages
        try:
            self.supabase.insert("chatbot_history", {
                "user_id": user_id,
                "session_id": session_id,
                "role": "user",
                "message": message,
            })
            self.supabase.insert("chatbot_history", {
                "user_id": user_id,
                "session_id": session_id,
                "role": "assistant",
                "message": response,
            })
        except Exception as e:
            logger.error(f"Failed to store chat message: {e}")

        return {
            "response": response,
            "session_id": session_id,
        }

    async def get_chat_history(self, user_id: str, limit: int = 20) -> Dict[str, Any]:
        """Get all chat sessions for a user."""
        try:
            messages = self.supabase.select(
                "chatbot_history",
                filters={"user_id": user_id},
                order_by="-created_at",
                limit=limit * 10,  # Get enough messages to cover sessions
            )

            # Group by session
            sessions = {}
            for msg in messages:
                sid = msg.get("session_id", "unknown")
                if sid not in sessions:
                    sessions[sid] = {
                        "session_id": sid,
                        "messages": [],
                        "created_at": msg.get("created_at"),
                    }
                sessions[sid]["messages"].append(msg)

            session_list = list(sessions.values())[:limit]
            return {"sessions": session_list, "total": len(session_list)}

        except Exception as e:
            logger.error(f"Failed to get chat history: {e}")
            return {"sessions": [], "total": 0}

    async def _get_session_messages(self, user_id: str, session_id: str) -> List[dict]:
        """Get all messages for a specific chat session."""
        try:
            return self.supabase.select(
                "chatbot_history",
                filters={"user_id": user_id, "session_id": session_id},
                order_by="created_at",
            )
        except Exception:
            return []
