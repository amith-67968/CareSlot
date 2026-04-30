"""
CareSlot — Auth Service
Handles user authentication via Supabase Auth.
"""

from app.services.supabase_service import SupabaseService
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Authentication service using Supabase Auth."""

    def __init__(self):
        self.supabase = SupabaseService()

    def _format_auth_response(self, auth_response) -> Dict[str, Any]:
        """Convert a Supabase auth response into the API auth payload."""
        user = auth_response.user
        session = auth_response.session
        if not session or not user:
            return {
                "user_id": user.id if user else None,
                "email": user.email if user else None,
                "access_token": None,
                "refresh_token": None,
                "expires_at": None,
                "expires_in": None,
            }

        return {
            "user_id": user.id,
            "email": user.email,
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "expires_at": getattr(session, "expires_at", None),
            "expires_in": getattr(session, "expires_in", None),
        }

    async def sign_up(self, email: str, password: str, full_name: str, extra_profile: Dict[str, Any] = None) -> Dict[str, Any]:
        """Register a new user and create their profile."""
        try:
            auth_response = self.supabase.sign_up(email, password)
            user = auth_response.user

            if user:
                # Build profile data from signup fields
                profile_data = {
                    "full_name": full_name,
                    "email": email,
                }
                if extra_profile:
                    profile_data.update(extra_profile)

                existing = self.supabase.select_one("user_profiles", filters={"user_id": user.id})
                if not existing:
                    profile_data["user_id"] = user.id
                    self.supabase.insert("user_profiles", profile_data)
                else:
                    # Update existing profile with any new/missing fields
                    update_fields = {
                        k: v for k, v in profile_data.items()
                        if v and (not existing.get(k))
                    }
                    if update_fields:
                        self.supabase.update("user_profiles", update_fields, {"user_id": user.id})

            result = self._format_auth_response(auth_response)
            result["email"] = result.get("email") or email
            return result
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
            return self._format_auth_response(auth_response)
        except Exception as e:
            logger.error(f"Sign in error: {e}")
            raise

    async def refresh_session(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh an existing Supabase session."""
        try:
            auth_response = self.supabase.refresh_session(refresh_token)
            return self._format_auth_response(auth_response)
        except Exception as e:
            logger.error(f"Refresh session error: {e}")
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
