"""
CareSlot — Chat Service
Orchestrates AI symptom analysis and conversation management.
"""

from app.ai.chains import run_symptom_analysis, run_conversation
from app.services.supabase_service import SupabaseService
from app.services.doctor_service import DoctorService
from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, AIMessage
import uuid
import logging
import asyncio

logger = logging.getLogger(__name__)

# Map common specialist names to DoctorService specialty keys
SPECIALIST_MAP = {
    "cardiologist": "cardiologist",
    "dermatologist": "dermatologist",
    "gynecologist": "gynecologist",
    "endocrinologist": "endocrinologist",
    "pulmonologist": "pulmonologist",
    "neurologist": "neurologist",
    "orthopedist": "orthopedist",
    "orthopedic": "orthopedist",
    "psychiatrist": "psychiatrist",
    "gastroenterologist": "gastroenterologist",
    "general physician": "general_physician",
    "general practitioner": "general_physician",
    "family doctor": "general_physician",
    "emergency": "emergency",
    "ent": "general_physician",
    "ophthalmologist": "general_physician",
    "urologist": "general_physician",
}


def _resolve_specialty(specialist_text: Optional[str]) -> Optional[str]:
    """Map LLM-recommended specialist text to a DoctorService specialty key."""
    if not specialist_text:
        return None
    lower = specialist_text.lower().strip()
    for keyword, key in SPECIALIST_MAP.items():
        if keyword in lower:
            return key
    return "general_physician"


class ChatService:
    """Service for AI-powered health chat and symptom analysis."""

    def __init__(self):
        self.supabase = SupabaseService()
        self.doctor_service = DoctorService()

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
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Multi-turn conversation with chat history.
        Now returns structured health data + nearby doctors.
        """
        if not session_id:
            session_id = str(uuid.uuid4())

        try:
            # Load chat history for this session
            chat_history = await self._get_session_messages(user_id, session_id)
            chat_history = chat_history[-6:]

            # Convert to LangChain message objects
            lc_history = []
            for msg in chat_history:
                if msg["role"] == "user":
                    lc_history.append(HumanMessage(content=msg["message"]))
                else:
                    lc_history.append(AIMessage(content=msg["message"]))

            # Run structured conversation chain
            ai_result = await run_conversation(message, lc_history)

        except Exception as e:
            logger.error(f"Conversation chain failed: {e}")
            ai_result = {
                "summary": (
                    "I'm sorry, I encountered an issue while processing your message. "
                    "Please try again in a moment."
                ),
                "prediction": None,
                "risk_level": None,
                "precautions": [],
                "home_remedies": [],
                "recommended_specialist": None,
                "next_steps": [],
                "is_structured": False,
            }

        # Build response text from summary
        response_text = ai_result.get("summary", "I received your message.")

        # Fetch nearby doctors if location provided and specialist recommended
        nearby_doctors = []
        specialist = ai_result.get("recommended_specialist")
        risk_level = ai_result.get("risk_level")
        if latitude is not None and longitude is not None and specialist and risk_level in {"high", "critical"}:
            try:
                specialty_key = _resolve_specialty(specialist)
                doctor_results = await self.doctor_service.find_nearby(
                    latitude=latitude,
                    longitude=longitude,
                    specialty=specialty_key,
                    radius=5000,
                )
                for doc in doctor_results.get("results", [])[:5]:
                    location = doc.get("location", {})
                    nearby_doctors.append({
                        "name": doc.get("name", ""),
                        "address": doc.get("address", ""),
                        "rating": doc.get("rating"),
                        "total_ratings": doc.get("total_ratings"),
                        "is_open_now": doc.get("is_open_now"),
                        "place_id": doc.get("place_id", ""),
                        "latitude": location.get("latitude"),
                        "longitude": location.get("longitude"),
                    })
            except Exception as e:
                logger.error(f"Doctor search failed: {e}")

        # Store messages after responding so Supabase writes do not slow chat.
        asyncio.create_task(self._store_chat_pair(user_id, session_id, message, response_text, ai_result))

        return {
            "response": response_text,
            "session_id": session_id,
            "prediction": ai_result.get("prediction"),
            "risk_level": ai_result.get("risk_level"),
            "precautions": ai_result.get("precautions", []),
            "home_remedies": ai_result.get("home_remedies", []),
            "recommended_specialist": specialist,
            "next_steps": ai_result.get("next_steps", []),
            "nearby_doctors": nearby_doctors,
            "is_structured": ai_result.get("is_structured", False),
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
            messages = self.supabase.select(
                "chatbot_history",
                filters={"user_id": user_id, "session_id": session_id},
                order_by="-created_at",
                limit=8,
            )
            return list(reversed(messages))
        except Exception:
            return []

    async def _store_chat_pair(
        self,
        user_id: str,
        session_id: str,
        user_message: str,
        response_text: str,
        metadata: Dict[str, Any],
    ) -> None:
        """Persist chat messages in the background."""
        try:
            await asyncio.to_thread(self.supabase.insert, "chatbot_history", {
                "user_id": user_id,
                "session_id": session_id,
                "role": "user",
                "message": user_message,
            })
            await asyncio.to_thread(self.supabase.insert, "chatbot_history", {
                "user_id": user_id,
                "session_id": session_id,
                "role": "assistant",
                "message": response_text,
                "metadata": metadata,
            })
        except Exception as e:
            logger.error(f"Failed to store chat message: {e}")
