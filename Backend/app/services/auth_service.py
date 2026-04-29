"""
CareSlot — Auth Service
Handles user authentication via Supabase Auth.
"""

from app.services.supabase_service import SupabaseService
from app.models.user import UserProfileCreate
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service using Supabase Auth."""

    def __init__(self):
        self.supabase = SupabaseService()

    async def sign_up(self, email: str, password: str, full_name: str) -> Dict[str, Any]:
        """Register a new user and create their profile."""
        try:
            auth_response = self.supabase.sign_up(email, password)
            user = auth_response.user

            if user:
                # Create user profile (upsert to handle re-signups)
                existing = self.supabase.select_one("user_profiles", filters={"user_id": user.id})
                if not existing:
                    self.supabase.insert("user_profiles", {
                        "user_id": user.id,
                        "full_name": full_name,
                        "email": email,
                    })

            return {
                "user_id": user.id if user else None,
                "email": email,
                "access_token": auth_response.session.access_token if auth_response.session else None,
                "refresh_token": auth_response.session.refresh_token if auth_response.session else None,
            }
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Sign up error: {error_msg}")
            if "already" in error_msg.lower() or "duplicate" in error_msg.lower() or "23505" in error_msg:
                raise ValueError("An account with this email already exists. Please log in instead.")
            raise

    async def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        """Sign in an existing user."""
        try:
            auth_response = self.supabase.sign_in(email, password)
            user = auth_response.user
            session = auth_response.session

            return {
                "user_id": user.id,
                "email": user.email,
                "access_token": session.access_token,
                "refresh_token": session.refresh_token,
            }
        except Exception as e:
            logger.error(f"Sign in error: {e}")
            raise

    async def sign_out(self, token: str) -> None:
        """Sign out the current user."""
        self.supabase.sign_out(token)

    async def reset_password(self, email: str) -> Dict[str, Any]:
        """Send password reset email."""
        self.supabase.reset_password(email)
        return {"message": "Password reset email sent", "success": True}

    async def get_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile by user_id."""
        return self.supabase.select_one("user_profiles", filters={"user_id": user_id})

    async def update_profile(self, user_id: str, data: dict) -> Dict[str, Any]:
        """Update user profile."""
        result = self.supabase.update("user_profiles", data, {"user_id": user_id})
        return result[0] if result else None
