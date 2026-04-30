"""
CareSlot — Authentication Middleware
Verifies Supabase JWT tokens and extracts user information.
"""

from fastapi import Request, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from jose.exceptions import JOSEError
from app.config import get_settings
from typing import Optional
import httpx


security = HTTPBearer()


async def verify_supabase_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Verify the Supabase JWT token from the Authorization header.
    Returns the decoded token payload with user_id.
    """
    token = credentials.credentials
    settings = get_settings()

    # Try local JWT decode first (supports HS256 and ES256)
    if settings.SUPABASE_JWT_SECRET:
        for alg in ["HS256", "ES256"]:
            try:
                payload = jwt.decode(
                    token,
                    settings.SUPABASE_JWT_SECRET,
                    algorithms=[alg],
                    audience="authenticated",
                )
                user_id = payload.get("sub") or payload.get("id")
                if user_id:
                    return {
                        "user_id": user_id,
                        "email": payload.get("email"),
                        "role": payload.get("role", "authenticated"),
                        "token": token,
                    }
            except (JWTError, JOSEError):
                continue

    # Fallback: verify via Supabase API
    try:
        async with httpx.AsyncClient(trust_env=False) as client:
            response = await client.get(
                f"{settings.SUPABASE_URL}/auth/v1/user",
                headers={
                    "Authorization": f"Bearer {token}",
                    "apikey": settings.SUPABASE_ANON_KEY,
                },
            )
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or expired token",
                )
            payload = response.json()

        user_id = payload.get("sub") or payload.get("id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing user identity",
            )

        return {
            "user_id": user_id,
            "email": payload.get("email"),
            "role": payload.get("role", "authenticated"),
            "token": token,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token verification failed: {str(e)}",
        )


async def get_optional_user(
    request: Request,
) -> Optional[dict]:
    """
    Optionally extract user from token. Returns None if no valid token.
    Useful for endpoints that work with or without authentication.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    try:
        token = auth_header.split(" ")[1]
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=token
        )
        return await verify_supabase_token(credentials)
    except HTTPException:
        return None
