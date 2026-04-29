"""
CareSlot — FastAPI Application Entry Point
AI-Powered Healthcare Assistant Backend
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.middleware.cors import setup_cors
from app.config import get_settings
import logging
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger("careslot")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info("🚀 Starting CareSlot Backend...")

    # Initialize ChromaDB knowledge base
    try:
        from app.ai.rag import get_vector_store, get_collection_stats
        store = get_vector_store()
        stats = get_collection_stats()
        logger.info(f"📚 ChromaDB ready: {stats['total_documents']} documents")

        if stats["total_documents"] == 0:
            logger.info("📥 Seeding knowledge base...")
            from app.ai.rag import ingest_knowledge
            count = ingest_knowledge()
            logger.info(f"✅ Ingested {count} documents into ChromaDB")
    except Exception as e:
        logger.warning(f"⚠️ ChromaDB init warning: {e}")

    # Pre-load embedding model
    try:
        from app.ai.embeddings import get_embeddings
        get_embeddings()
        logger.info("🧠 Embedding model loaded")
    except Exception as e:
        logger.warning(f"⚠️ Embedding model warning: {e}")

    logger.info("✅ CareSlot Backend ready!")
    yield
    logger.info("👋 Shutting down CareSlot Backend...")


# Create FastAPI app
settings = get_settings()

app = FastAPI(
    title="CareSlot API",
    description=(
        "AI-Powered Healthcare Assistant providing preliminary health guidance, "
        "symptom analysis, skin disease detection, PCOD/PCOS risk assessment, "
        "doctor recommendations, appointment booking, and health reminders. "
        "**This is NOT a diagnosis platform.**"
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Setup CORS
setup_cors(app)


# ─── Middleware ────────────────────────────────────────────────────────

@app.middleware("http")
async def add_request_timing(request: Request, call_next):
    """Add request processing time header."""
    start = time.time()
    response = await call_next(request)
    process_time = time.time() - start
    response.headers["X-Process-Time"] = f"{process_time:.4f}"
    return response


# ─── Global Exception Handler ─────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal error occurred. Please try again.",
            "type": type(exc).__name__,
        },
    )


# ─── Register Routers ─────────────────────────────────────────────────

from app.routers import auth, profile, chat, skin, pcod, doctors, appointments, notifications

app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(chat.router)
app.include_router(skin.router)
app.include_router(pcod.router)
app.include_router(doctors.router)
app.include_router(appointments.router)
app.include_router(notifications.router)


# ─── Health Check ──────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
async def root():
    return {
        "app": "CareSlot API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "disclaimer": "This platform provides preliminary health guidance only. Not a substitute for professional medical advice.",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check endpoint."""
    checks = {"api": True}

    # Check Supabase
    try:
        from app.services.supabase_service import SupabaseService
        sb = SupabaseService()
        sb.client  # Access to verify connection
        checks["supabase"] = True
    except Exception:
        checks["supabase"] = False

    # Check ChromaDB
    try:
        from app.ai.rag import get_collection_stats
        stats = get_collection_stats()
        checks["chromadb"] = True
        checks["chromadb_docs"] = stats["total_documents"]
    except Exception:
        checks["chromadb"] = False

    # Check Ollama
    try:
        from app.ai.llm import get_llm
        get_llm()
        checks["ollama"] = True
    except Exception:
        checks["ollama"] = False

    return {"status": "healthy" if all(v for k, v in checks.items() if isinstance(v, bool)) else "degraded", "checks": checks}
