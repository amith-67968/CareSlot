"""
CareSlot — Application Configuration
Loads environment variables using Pydantic Settings.
"""

from functools import lru_cache
from pydantic import field_validator
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- App ---
    APP_NAME: str = "CareSlot"
    APP_ENV: str = "development"
    DEBUG: bool = True
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # --- Supabase ---
    SUPABASE_URL: str
    SUPABASE_ANON_KEY: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_JWT_SECRET: str = ""

    # --- Ollama ---
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1:8b"
    OLLAMA_NUM_CTX: int = 2048
    OLLAMA_NUM_PREDICT: int = 450

    # --- Performance ---
    ENABLE_LLM_EXPLANATIONS: bool = False
    ENABLE_PCOD_ZERO_SHOT: bool = False
    FAST_CHAT_RESPONSES: bool = True

    # --- Google Maps ---
    GOOGLE_MAPS_API_KEY: str = ""

    # --- Hospital/EHR Booking Integrations ---
    # JSON object keyed by Google place_id, for example:
    # {"ChIJ...": {"base_url": "https://ehr.example.com/api", "api_key": "..."}}
    HOSPITAL_API_REGISTRY_JSON: str = "{}"
    HOSPITAL_API_TIMEOUT_SECONDS: float = 12.0

    # --- Scheduled Reminder Delivery ---
    CRON_SECRET: str = ""
    ENABLE_EMAIL_NOTIFICATIONS: bool = False
    ENABLE_SMS_NOTIFICATIONS: bool = False
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = "notifications@careslot.ai"
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_FROM_NUMBER: str = ""

    # --- ChromaDB ---
    CHROMA_PERSIST_DIR: str = "./chroma_db"

    # --- ML Models ---
    SKIN_MODEL_PATH: str = "./ml_models/mobilenetv2_ham10000.h5"

    # --- Embeddings ---
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value):
        """Accept common deployment strings for DEBUG instead of failing startup."""
        if isinstance(value, str) and value.lower() in {"release", "prod", "production"}:
            return False
        return value

    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
