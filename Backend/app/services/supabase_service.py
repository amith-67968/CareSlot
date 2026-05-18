"""
CareSlot — Supabase Service
Singleton wrapper for Supabase client operations.
"""

from supabase import create_client, Client
from app.config import get_settings
from typing import Optional, Any, Dict, List
import logging

logger = logging.getLogger(__name__)


class SupabaseService:
    """Centralized Supabase client for database, auth, and storage operations."""

    _client: Optional[Client] = None
    _admin_client: Optional[Client] = None

    @classmethod
    def _get_client(cls) -> Client:
        """Get or create the Supabase client (anon key)."""
        if cls._client is None:
            settings = get_settings()
            cls._client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_ANON_KEY,
            )
        return cls._client

    @classmethod
    def _get_admin_client(cls) -> Client:
        """Get or create the Supabase admin client (service role key)."""
        if cls._admin_client is None:
            settings = get_settings()
            cls._admin_client = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY,
            )
        return cls._admin_client

    @property
    def client(self) -> Client:
        return self._get_client()

    @property
    def admin(self) -> Client:
        return self._get_admin_client()

    # ─── Auth Operations ───────────────────────────────────────────────

    def sign_up(self, email: str, password: str) -> Any:
        """Register a new user via Supabase Auth."""
        response = self.client.auth.sign_up(
            {"email": email, "password": password}
        )
        return response

    def sign_in(self, email: str, password: str) -> Any:
        """Sign in a user with email and password."""
        response = self.client.auth.sign_in_with_password(
            {"email": email, "password": password}
        )
        return response

    def refresh_session(self, refresh_token: str) -> Any:
        """Refresh an access token using a Supabase refresh token."""
        response = self.client.auth.refresh_session(refresh_token)
        return response

    def sign_out(self, token: str) -> None:
        """Sign out the current user."""
        self.client.auth.sign_out()

    def get_user(self, token: str) -> Any:
        """Get user details from token."""
        response = self.client.auth.get_user(token)
        return response

    def reset_password(self, email: str) -> Any:
        """Send a password reset email."""
        response = self.client.auth.reset_password_email(email)
        return response

    # ─── Database Operations ───────────────────────────────────────────

    def insert(self, table: str, data: Dict[str, Any]) -> dict:
        """Insert a row into a table."""
        response = self.admin.table(table).insert(data).execute()
        return response.data

    def select(
        self,
        table: str,
        columns: str = "*",
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[dict]:
        """Select rows from a table with optional filters."""
        query = self.admin.table(table).select(columns)

        if filters:
            for key, value in filters.items():
                query = query.eq(key, value)

        if order_by:
            desc = order_by.startswith("-")
            col = order_by.lstrip("-")
            query = query.order(col, desc=desc)

        if limit:
            query = query.limit(limit)

        response = query.execute()
        return response.data

    def update(
        self, table: str, data: Dict[str, Any], filters: Dict[str, Any]
    ) -> List[dict]:
        """Update rows in a table matching filters."""
        query = self.admin.table(table).update(data)
        for key, value in filters.items():
            query = query.eq(key, value)
        response = query.execute()
        return response.data

    def delete(self, table: str, filters: Dict[str, Any]) -> List[dict]:
        """Delete rows from a table matching filters."""
        query = self.admin.table(table).delete()
        for key, value in filters.items():
            query = query.eq(key, value)
        response = query.execute()
        return response.data

    def select_one(
        self, table: str, columns: str = "*", filters: Optional[Dict[str, Any]] = None
    ) -> Optional[dict]:
        """Select a single row from a table."""
        results = self.select(table, columns, filters, limit=1)
        return results[0] if results else None

    # ─── Storage Operations ────────────────────────────────────────────

    def upload_file(
        self, bucket: str, path: str, file_data: bytes, content_type: str = "image/jpeg"
    ) -> str:
        """Upload a file to Supabase Storage. Returns the storage path."""
        self.admin.storage.from_(bucket).upload(
            path,
            file_data,
            file_options={"content-type": content_type},
        )
        return path

    def get_public_url(self, bucket: str, path: str) -> str:
        """Get the public URL for a stored file."""
        response = self.admin.storage.from_(bucket).get_public_url(path)
        return response

    def delete_file(self, bucket: str, paths: List[str]) -> None:
        """Delete files from Supabase Storage."""
        self.admin.storage.from_(bucket).remove(paths)
