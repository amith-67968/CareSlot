"""
CareSlot — Shared FastAPI Dependencies
Reusable dependency injection functions for routes.
"""

from fastapi import Depends
from app.middleware.auth import verify_supabase_token, get_optional_user
from app.services.supabase_service import SupabaseService
from typing import Optional


async def get_current_user(
    user: dict = Depends(verify_supabase_token),
) -> dict:
    """
    Dependency that requires authentication.
    Returns user dict with: user_id, email, role, token.
    """
    return user


async def get_current_user_optional(
    user: Optional[dict] = Depends(get_optional_user),
) -> Optional[dict]:
    """
    Dependency for optional authentication.
    Returns user dict or None.
    """
    return user


def get_supabase() -> SupabaseService:
    """Get the Supabase service singleton."""
    return SupabaseService()
