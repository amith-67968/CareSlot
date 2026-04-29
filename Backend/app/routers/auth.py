"""
CareSlot — Auth Router
Endpoints for user authentication.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from app.models.user import SignUpRequest, SignInRequest, PasswordResetRequest, AuthResponse, MessageResponse
from app.services.auth_service import AuthService
from app.dependencies import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def sign_up(request: SignUpRequest):
    """Register a new user account."""
    try:
        service = AuthService()
        result = await service.sign_up(request.email, request.password, request.full_name)
        return AuthResponse(
            access_token=result.get("access_token", ""),
            refresh_token=result.get("refresh_token"),
            user_id=result.get("user_id", ""),
            email=request.email,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=AuthResponse)
async def sign_in(request: SignInRequest):
    """Sign in with email and password."""
    try:
        service = AuthService()
        result = await service.sign_in(request.email, request.password)
        return AuthResponse(
            access_token=result["access_token"],
            refresh_token=result.get("refresh_token"),
            user_id=result["user_id"],
            email=result["email"],
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")


@router.post("/logout", response_model=MessageResponse)
async def sign_out(user: dict = Depends(get_current_user)):
    """Sign out the current user."""
    service = AuthService()
    await service.sign_out(user["token"])
    return MessageResponse(message="Signed out successfully")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(request: PasswordResetRequest):
    """Send a password reset email."""
    service = AuthService()
    await service.reset_password(request.email)
    return MessageResponse(message="Password reset email sent")
