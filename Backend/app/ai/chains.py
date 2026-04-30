"""
CareSlot — LangChain Chains & Prompts
Structured AI chains for symptom analysis, skin assessment, and conversations.
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.documents import Document
from app.ai.llm import get_llm
from app.ai.rag import get_retriever
from app.config import get_settings
from typing import List, Dict, Any
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)

EMERGENCY_TERMS = [
    "chest pain", "chest tightness", "difficulty breathing", "shortness of breath",
    "can't breathe", "cant breathe", "stroke", "fainting", "unconscious",
    "severe bleeding", "seizure", "blue lips",
]

COMMON_FAST_TERMS = [
    "fever", "headache", "rash", "itching", "cough", "cold", "sore throat",
    "pcod", "pcos", "irregular period", "irregular periods", "acne",
    "facial hair", "hair thinning", "weight gain",
]


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
    return "\n\n---\n\n".join(doc.page_content[:900] for doc in docs)


def _retrieve_context(query: str, k: int = 5) -> str:
    """Retrieve RAG context, but never let retrieval failure block guidance."""
    normalized = " ".join((query or "").lower().split())[:240]
    return _retrieve_context_cached(normalized, k)


@lru_cache(maxsize=256)
def _retrieve_context_cached(query: str, k: int = 5) -> str:
    """Cached RAG retrieval for repeated common symptom questions."""
    try:
        retriever = get_retriever(k=k)
        return _format_docs(retriever.invoke(query))
    except Exception as e:
        logger.warning(f"RAG retrieval unavailable, continuing without context: {e}")
        return "No specific medical knowledge context available."


def _rule_based_health_fallback(message: str) -> Dict[str, Any]:
    """Deterministic safety fallback for common symptom messages."""
    text = (message or "").lower()

    if any(term in text for term in EMERGENCY_TERMS):
        return {
            "summary": (
                "Chest pain or breathing trouble can be urgent. Please seek emergency medical help now, "
                "especially if the pain is severe, spreading to your arm/jaw/back, or comes with sweating, "
                "nausea, dizziness, or shortness of breath."
            ),
            "prediction": "Possible cardiac, lung, gastrointestinal, or muscle-related chest pain; serious causes must be ruled out urgently.",
            "risk_level": "critical",
            "precautions": [
                "Stop physical activity and sit upright or rest comfortably",
                "Do not drive yourself if symptoms are significant",
                "Call local emergency services or go to the nearest emergency department",
                "Tell a nearby person what is happening if you are alone",
            ],
            "home_remedies": [],
            "recommended_specialist": "Emergency Care / Cardiologist",
            "next_steps": [
                "Seek immediate in-person medical evaluation",
                "If prescribed by your doctor for heart symptoms, follow that emergency plan",
                "Share your age, medical history, medications, and symptom timing with clinicians",
            ],
            "is_structured": True,
        }

    if "fever" in text:
        return {
            "summary": "A fever is often caused by infection or inflammation. Monitor your temperature and watch for warning signs.",
            "prediction": "Possible viral or bacterial infection",
            "risk_level": "medium",
            "precautions": ["Rest", "Drink fluids", "Monitor temperature", "Seek care if fever is high or persistent"],
            "home_remedies": ["Use light clothing", "Take lukewarm sponge baths", "Drink warm fluids"],
            "recommended_specialist": "General Physician",
            "next_steps": ["Consult a clinician if fever lasts more than 3 days or exceeds 103 F"],
            "is_structured": True,
        }

    if "headache" in text:
        return {
            "summary": "Headaches are commonly related to tension, migraine, dehydration, sinus issues, or eye strain, but severe sudden headaches need urgent care.",
            "prediction": "Possible tension headache, migraine, dehydration, sinus headache, or other cause",
            "risk_level": "low",
            "precautions": [
                "Hydrate",
                "Rest in a quiet place",
                "Avoid excess screen time",
                "Seek urgent care for sudden severe headache or neurological symptoms",
            ],
            "home_remedies": ["Cold or warm compress", "Gentle neck stretches", "Adequate sleep"],
            "recommended_specialist": "General Physician",
            "next_steps": ["Track triggers and consult a doctor if headaches are frequent or worsening"],
            "is_structured": True,
        }

    if any(term in text for term in ["rash", "itching", "skin rash", "redness"]):
        return {
            "summary": "Skin rashes can come from allergy, irritation, infection, heat, or inflammatory skin conditions. Watch for spreading, pain, fever, or pus.",
            "prediction": "Possible allergic rash, dermatitis, infection, or other skin irritation",
            "risk_level": "medium" if any(term in text for term in ["fever", "pus", "pain", "swelling"]) else "low",
            "precautions": [
                "Avoid scratching the area",
                "Keep the area clean and dry",
                "Avoid new creams, fragrances, or harsh products",
                "Seek care quickly if redness spreads, pain worsens, or fever appears",
            ],
            "home_remedies": ["Cool compress", "Gentle fragrance-free moisturizer", "Loose breathable clothing"],
            "recommended_specialist": "Dermatologist",
            "next_steps": ["Consult a dermatologist if it persists, spreads, or becomes painful"],
            "is_structured": True,
        }

    if any(term in text for term in ["pcod", "pcos", "irregular period", "irregular periods", "facial hair"]):
        return {
            "summary": "Irregular periods, acne, facial hair growth, weight changes, or fatigue can be linked with PCOD/PCOS or other hormonal issues. A screening can guide next steps, but confirmation needs a clinician.",
            "prediction": "Possible PCOD/PCOS or hormonal imbalance",
            "risk_level": "medium",
            "precautions": [
                "Track cycle dates and symptoms",
                "Maintain regular meals, sleep, and physical activity",
                "Avoid self-medicating with hormonal tablets",
            ],
            "home_remedies": ["Balanced high-fiber meals", "Regular moderate exercise", "Stress management"],
            "recommended_specialist": "Gynecologist / Endocrinologist",
            "next_steps": ["Consider the PCOD/PCOS assessment", "Ask a clinician about hormonal, thyroid, and glucose tests"],
            "is_structured": True,
        }

    if any(term in text for term in ["cough", "cold", "sore throat", "runny nose"]):
        return {
            "summary": "Cough, cold, and sore throat symptoms are often viral, but persistent fever, breathing trouble, or worsening symptoms need medical care.",
            "prediction": "Possible viral upper respiratory infection, allergy, or throat irritation",
            "risk_level": "low",
            "precautions": ["Rest", "Hydrate", "Avoid smoke and dust", "Use a mask around others if infectious symptoms are present"],
            "home_remedies": ["Warm fluids", "Salt-water gargle", "Steam inhalation if comfortable"],
            "recommended_specialist": "General Physician",
            "next_steps": ["Consult a doctor if symptoms last more than a few days, worsen, or include breathing difficulty"],
            "is_structured": True,
        }

    return {
        "summary": (
            "I could not complete the AI analysis right now, but your symptoms still deserve attention. "
            "Please monitor how you feel and consult a qualified healthcare professional for proper evaluation."
        ),
        "prediction": "Unable to determine from the available information",
        "risk_level": "medium",
        "precautions": [
            "Avoid ignoring worsening symptoms",
            "Rest and stay hydrated if appropriate",
            "Seek medical advice for proper evaluation",
        ],
        "home_remedies": [],
        "recommended_specialist": "General Physician",
        "next_steps": ["Try again shortly", "Consult a healthcare professional if symptoms persist or worsen"],
        "is_structured": True,
    }


def _apply_emergency_guardrails(result: Dict[str, Any], message: str) -> Dict[str, Any]:
    """Force emergency-safe guidance when user text contains red-flag symptoms."""
    if not any(term in (message or "").lower() for term in EMERGENCY_TERMS):
        return result

    emergency = _rule_based_health_fallback(message)
    result["summary"] = emergency["summary"]
    result["prediction"] = result.get("prediction") or emergency["prediction"]
    result["risk_level"] = "critical"
    result["recommended_specialist"] = emergency["recommended_specialist"]
    result["precautions"] = list(dict.fromkeys(
        emergency["precautions"] + (result.get("precautions") or [])
    ))
    result["next_steps"] = list(dict.fromkeys(
        emergency["next_steps"] + (result.get("next_steps") or [])
    ))
    result["home_remedies"] = result.get("home_remedies") or []
    result["is_structured"] = True
    return result


def _quick_conversation_response(message: str) -> Dict[str, Any] | None:
    """Return instant responses for simple/common chat messages."""
    text = " ".join((message or "").lower().split())
    if not text:
        return None

    greetings = {"hi", "hello", "hey", "good morning", "good afternoon", "good evening"}
    if text in greetings:
        return {
            "summary": "Hi, I am CareSlot AI. Tell me your symptoms, duration, and severity, and I can give preliminary guidance.",
            "prediction": None,
            "risk_level": None,
            "precautions": [],
            "home_remedies": [],
            "recommended_specialist": None,
            "next_steps": [],
            "is_structured": False,
        }

    if text in {"thanks", "thank you", "ok", "okay"}:
        return {
            "summary": "You are welcome. Keep monitoring your symptoms, and seek medical care if anything worsens.",
            "prediction": None,
            "risk_level": None,
            "precautions": [],
            "home_remedies": [],
            "recommended_specialist": None,
            "next_steps": [],
            "is_structured": False,
        }

    if "what is pcod" in text or "what is pcos" in text:
        return {
            "summary": "PCOD/PCOS are hormone-related conditions that can affect ovulation and menstrual cycles. Common signs include irregular periods, acne, weight changes, facial hair growth, and sometimes insulin resistance. A gynecologist or endocrinologist can confirm with history, examination, blood tests, and ultrasound when needed.",
            "prediction": None,
            "risk_level": None,
            "precautions": [],
            "home_remedies": [],
            "recommended_specialist": "Gynecologist / Endocrinologist",
            "next_steps": ["Use the PCOD/PCOS assessment if you have symptoms", "Consult a clinician for confirmation and treatment"],
            "is_structured": True,
        }

    if any(term in text for term in EMERGENCY_TERMS + COMMON_FAST_TERMS):
        return _rule_based_health_fallback(text)

    return None


def _quick_symptom_analysis(symptoms: str, additional_context: str = "") -> Dict[str, Any] | None:
    """Instant structured analysis for common symptom patterns."""
    text = f"{symptoms} {additional_context}".lower()
    if any(term in text for term in EMERGENCY_TERMS + COMMON_FAST_TERMS):
        result = _rule_based_health_fallback(text)
        return {key: result[key] for key in (
            "prediction", "risk_level", "precautions", "home_remedies",
            "recommended_specialist", "next_steps",
        )}
    return None


@lru_cache()
def get_symptom_analysis_chain():
    """
    Build the symptom analysis chain using RAG.

    Flow: symptoms → retrieve context → LLM → JSON response
    """
    llm = get_llm()

    chain = (
        {
            "context": lambda x: _retrieve_context(x["symptoms"], k=2),
            "symptoms": lambda x: x["symptoms"],
            "additional_context": lambda x: x.get("additional_context", "None provided"),
        }
        | SYMPTOM_ANALYSIS_PROMPT
        | llm
        | JsonOutputParser()
    )

    return chain


@lru_cache()
def get_conversation_chain():
    """
    Build the multi-turn conversation chain with RAG context.
    Returns structured JSON via JsonOutputParser.
    """
    llm = get_llm()

    chain = (
        {
            "context": lambda x: _retrieve_context(x["message"], k=1),
            "chat_history": lambda x: x.get("chat_history", []),
            "message": lambda x: x["message"],
        }
        | CONVERSATION_PROMPT
        | llm
        | JsonOutputParser()
    )

    return chain


@lru_cache()
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
    try:
        if get_settings().FAST_CHAT_RESPONSES:
            quick = _quick_symptom_analysis(symptoms, additional_context)
            if quick:
                return quick

        chain = get_symptom_analysis_chain()
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

        result = _apply_emergency_guardrails(result, symptoms)
        return result

    except Exception as e:
        logger.error(f"Symptom analysis chain error: {e}")
        fallback = _rule_based_health_fallback(f"{symptoms} {additional_context}")
        return {key: fallback[key] for key in (
            "prediction", "risk_level", "precautions", "home_remedies",
            "recommended_specialist", "next_steps",
        )}


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
        if get_settings().FAST_CHAT_RESPONSES:
            quick = _quick_conversation_response(message)
            if quick:
                return quick

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

        result = _apply_emergency_guardrails(result, message)

        # Determine if this is a structured health response
        result["is_structured"] = bool(
            result.get("prediction") or
            result.get("precautions") or
            result.get("home_remedies")
        )

        return result

    except Exception as e:
        logger.error(f"Conversation chain error: {e}")
        return _rule_based_health_fallback(message)


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


# ═══════════════════════════════════════════════════════════════════════
# PCOD / PCOS ANALYSIS CHAIN
# ═══════════════════════════════════════════════════════════════════════

PCOD_ANALYSIS_PROMPT = ChatPromptTemplate.from_messages([
    ("system", """You are CareSlot's women's health AI assistant providing PRELIMINARY PCOD/PCOS risk guidance.

IMPORTANT: This is a RISK ASSESSMENT, NOT a diagnosis. Always recommend consulting a gynecologist or endocrinologist.

Risk assessment results:
- Risk Level: {risk_level}
- Risk Score: {risk_score}%
- Conditions Flagged: {conditions_flagged}
- Key Indicators: {key_indicators}

Patient symptoms: {symptoms_text}

Based on this assessment, provide a comprehensive explanation as JSON:
{{
    "combined_assessment": "A detailed, plain-English explanation of the risk assessment results. Explain what the flagged conditions mean, how the symptoms relate to potential PCOD/PCOS, and what the risk level implies. Write 4-6 sentences in a caring, professional tone.",
    "urgency_level": "low" or "medium" or "high",
    "possible_causes": ["list", "of", "possible", "underlying", "causes"],
    "lifestyle_recommendations": ["list", "of", "specific", "lifestyle", "changes"],
    "dietary_suggestions": ["list", "of", "dietary", "recommendations"],
    "exercise_recommendations": ["list", "of", "exercise", "suggestions"],
    "hormonal_insights": "Brief explanation of potential hormonal factors involved.",
    "fertility_note": "Brief note about fertility implications if relevant, or 'Not applicable' if risk is low.",
    "doctor_consultation_needed": true or false,
    "urgent": true or false
}}

Respond ONLY with valid JSON."""),
    ("human", "Please explain my PCOD/PCOS risk assessment results."),
])


@lru_cache()
def get_pcod_analysis_chain():
    """Build the PCOD analysis chain."""
    llm = get_llm()
    return PCOD_ANALYSIS_PROMPT | llm | JsonOutputParser()


async def run_pcod_analysis(
    risk_level: str,
    risk_score: float,
    conditions_flagged: list,
    key_indicators: list,
    symptoms_text: str,
) -> Dict[str, Any]:
    """Execute the PCOD analysis chain for LLM explanation."""
    chain = get_pcod_analysis_chain()

    try:
        result = await chain.ainvoke({
            "risk_level": risk_level,
            "risk_score": f"{risk_score * 100:.1f}",
            "conditions_flagged": ", ".join(conditions_flagged) if conditions_flagged else "None",
            "key_indicators": ", ".join(key_indicators) if key_indicators else "None",
            "symptoms_text": symptoms_text,
        })
        return result

    except Exception as e:
        logger.error(f"PCOD analysis chain error: {e}")
        return {
            "combined_assessment": "AI explanation could not be generated. Please consult a gynecologist for proper evaluation.",
            "urgency_level": "medium",
            "possible_causes": [],
            "lifestyle_recommendations": [],
            "dietary_suggestions": [],
            "exercise_recommendations": [],
            "hormonal_insights": "",
            "fertility_note": "",
            "doctor_consultation_needed": True,
            "urgent": False,
        }
