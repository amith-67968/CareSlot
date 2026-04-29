"""
CareSlot — LangChain Chains & Prompts
Structured AI chains for symptom analysis, skin assessment, and conversations.
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.documents import Document
from app.ai.llm import get_llm
from app.ai.rag import get_retriever
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


# ─── Prompts ──────────────────────────────────────────────────────────

SYMPTOM_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are CareSlot, an AI healthcare assistant providing PRELIMINARY health guidance only.

IMPORTANT RULES:
1. NEVER provide a final medical diagnosis
2. Always recommend consulting a qualified healthcare professional
3. Provide risk assessment, precautions, and specialist recommendations
4. Be empathetic but factual
5. If symptoms suggest an emergency, clearly state the urgency

You have access to the following medical knowledge context:
{context}

Based on the user's symptoms, provide a structured JSON response with EXACTLY these fields:
{{
    "prediction": "Brief description of possible health condition(s)",
    "risk_level": "low" or "medium" or "high" or "critical",
    "precautions": ["list", "of", "precautions"],
    "home_remedies": ["list", "of", "safe", "home", "remedies"],
    "recommended_specialist": "Type of specialist doctor",
    "next_steps": ["list", "of", "recommended", "next", "steps"]
}}

Respond ONLY with valid JSON. No additional text before or after the JSON."""),
    ("human", "My symptoms are: {symptoms}\n\nAdditional context: {additional_context}"),
])


CONVERSATION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are CareSlot, a compassionate AI healthcare assistant.

IMPORTANT RULES:
1. NEVER provide a final medical diagnosis
2. Always recommend consulting a qualified healthcare professional
3. Be conversational, empathetic, and helpful
4. If symptoms sound serious, clearly recommend seeking immediate medical attention
5. Provide preliminary guidance, precautions, and lifestyle recommendations

Medical knowledge context:
{context}

You MUST respond with valid JSON in EXACTLY this format:
{{
    "summary": "A warm, empathetic response to the user. If they describe symptoms, acknowledge them. If it's a greeting or general question, respond naturally.",
    "prediction": "If health symptoms are mentioned, predict the most likely condition(s). Otherwise set to null.",
    "risk_level": "low or medium or high or critical. Set to null if no symptoms mentioned.",
    "precautions": ["List of precautions if symptoms are mentioned, otherwise empty array"],
    "home_remedies": ["List of safe home remedies if applicable, otherwise empty array"],
    "recommended_specialist": "Type of doctor to consult if symptoms mentioned, otherwise null",
    "next_steps": ["Recommended next steps if symptoms mentioned, otherwise empty array"]
}}

Respond ONLY with valid JSON. No text before or after."""),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{message}"),
])


SKIN_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are CareSlot's dermatology AI assistant providing PRELIMINARY skin health guidance.

IMPORTANT: This is NOT a diagnosis. Always recommend seeing a dermatologist for proper evaluation.

The AI image model has detected: {model_prediction} (confidence: {confidence}%)

The user has reported these symptoms:
{symptoms_text}

Based on the model prediction and reported symptoms, provide a comprehensive assessment as JSON:
{{
    "combined_assessment": "A detailed, plain-English explanation of the likely condition. Describe what it is, how it typically presents, and how the reported symptoms relate to the prediction. Be thorough but accessible. Write 3-5 sentences.",
    "severity_level": "mild" or "moderate" or "severe",
    "urgency_level": "low" or "medium" or "high",
    "possible_causes": ["list", "of", "possible", "causes", "for", "this", "condition"],
    "precautions": ["list", "of", "specific", "precautions", "to", "take"],
    "home_remedies": ["list", "of", "safe", "home", "remedies"],
    "recommended_specialist": "Dermatologist",
    "next_steps": ["list", "of", "recommended", "next", "steps"],
    "urgent": true or false,
    "doctor_consultation_needed": true or false
}}

Respond ONLY with valid JSON."""),
    ("human", "Please analyze my skin condition based on the image analysis and my symptoms."),
])


# ─── Chain Builders ───────────────────────────────────────────────────

def _format_docs(docs: List[Document]) -> str:
    """Format retrieved documents into context string."""
    if not docs:
        return "No specific medical knowledge context available."
    return "\n\n---\n\n".join(doc.page_content for doc in docs)


def get_symptom_analysis_chain():
    """
    Build the symptom analysis chain using RAG.

    Flow: symptoms → retrieve context → LLM → JSON response
    """
    llm = get_llm()
    retriever = get_retriever(k=5)

    chain = (
        {
            "context": lambda x: _format_docs(retriever.invoke(x["symptoms"])),
            "symptoms": lambda x: x["symptoms"],
            "additional_context": lambda x: x.get("additional_context", "None provided"),
        }
        | SYMPTOM_ANALYSIS_PROMPT
        | llm
        | JsonOutputParser()
    )

    return chain


def get_conversation_chain():
    """
    Build the multi-turn conversation chain with RAG context.
    Returns structured JSON via JsonOutputParser.
    """
    llm = get_llm()
    retriever = get_retriever(k=3)

    chain = (
        {
            "context": lambda x: _format_docs(retriever.invoke(x["message"])),
            "chat_history": lambda x: x.get("chat_history", []),
            "message": lambda x: x["message"],
        }
        | CONVERSATION_PROMPT
        | llm
        | JsonOutputParser()
    )

    return chain


def get_skin_analysis_chain():
    """
    Build the skin disease analysis chain.
    Combines MobileNetV2 prediction with symptom context via LLM.
    """
    llm = get_llm()

    chain = (
        SKIN_ANALYSIS_PROMPT
        | llm
        | JsonOutputParser()
    )

    return chain


async def run_symptom_analysis(
    symptoms: str,
    additional_context: str = "",
) -> Dict[str, Any]:
    """
    Execute the symptom analysis chain.

    Args:
        symptoms: User's symptom description.
        additional_context: Additional medical context.

    Returns:
        Structured analysis result dict.
    """
    chain = get_symptom_analysis_chain()

    try:
        result = await chain.ainvoke({
            "symptoms": symptoms,
            "additional_context": additional_context or "None provided",
        })

        # Ensure all required fields exist
        defaults = {
            "prediction": "Unable to determine",
            "risk_level": "medium",
            "precautions": [],
            "home_remedies": [],
            "recommended_specialist": "General Physician",
            "next_steps": ["Consult a healthcare professional"],
        }

        for key, default in defaults.items():
            if key not in result:
                result[key] = default

        return result

    except Exception as e:
        logger.error(f"Symptom analysis chain error: {e}")
        return {
            "prediction": "Analysis could not be completed. Please consult a healthcare professional.",
            "risk_level": "medium",
            "precautions": ["Seek medical advice for proper evaluation"],
            "home_remedies": [],
            "recommended_specialist": "General Physician",
            "next_steps": ["Visit a healthcare professional for proper diagnosis"],
        }


async def run_conversation(
    message: str,
    chat_history: list = None,
) -> Dict[str, Any]:
    """
    Execute the conversation chain.

    Args:
        message: User's message.
        chat_history: Previous messages in the conversation.

    Returns:
        Structured analysis result dict.
    """
    try:
        chain = get_conversation_chain()

        result = await chain.ainvoke({
            "message": message,
            "chat_history": chat_history or [],
        })

        # Ensure all required fields exist
        defaults = {
            "summary": "I received your message.",
            "prediction": None,
            "risk_level": None,
            "precautions": [],
            "home_remedies": [],
            "recommended_specialist": None,
            "next_steps": [],
        }

        for key, default in defaults.items():
            if key not in result or result[key] is None:
                result[key] = default

        # Determine if this is a structured health response
        result["is_structured"] = bool(
            result.get("prediction") or
            result.get("precautions") or
            result.get("home_remedies")
        )

        return result

    except Exception as e:
        logger.error(f"Conversation chain error: {e}")
        return {
            "summary": (
                "I'm sorry, I'm having trouble processing your request right now. "
                "This could be because the AI model is still loading. "
                "Please try again in a moment. If your symptoms are severe or urgent, "
                "please seek immediate medical attention."
            ),
            "prediction": None,
            "risk_level": None,
            "precautions": [],
            "home_remedies": [],
            "recommended_specialist": None,
            "next_steps": [],
            "is_structured": False,
        }


async def run_skin_analysis(
    model_prediction: str,
    confidence: float,
    symptoms_text: str,
) -> Dict[str, Any]:
    """
    Execute the skin analysis chain combining model output with symptoms.

    Args:
        model_prediction: MobileNetV2 prediction class name.
        confidence: Model confidence score.
        symptoms_text: User-reported symptoms.

    Returns:
        Combined analysis result dict.
    """
    chain = get_skin_analysis_chain()

    try:
        result = await chain.ainvoke({
            "model_prediction": model_prediction,
            "confidence": f"{confidence * 100:.1f}",
            "symptoms_text": symptoms_text,
        })
        return result

    except Exception as e:
        logger.error(f"Skin analysis chain error: {e}")
        return {
            "combined_assessment": "AI analysis could not be completed. Please consult a dermatologist.",
            "severity_level": "moderate",
            "precautions": ["Consult a dermatologist for proper evaluation"],
            "home_remedies": [],
            "recommended_specialist": "Dermatologist",
            "next_steps": ["Schedule a dermatology appointment"],
            "urgent": False,
        }
