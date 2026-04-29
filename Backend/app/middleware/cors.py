"""
CareSlot — CORS Middleware Configuration
Ensures CORS headers are present on ALL responses, including error responses.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from app.config import get_settings


class CORSFixMiddleware(BaseHTTPMiddleware):
    """
    Ensures CORS headers are present on error responses.
    FastAPI's CORSMiddleware can miss adding headers when exception handlers
    return responses, causing browsers to report CORS errors instead of the
    actual 500 status.
    """

    def __init__(self, app, allowed_origins: list):
        super().__init__(app)
        self.allowed_origins = allowed_origins

    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        response = await call_next(request)

        # If the response doesn't already have CORS headers and origin is allowed
        if origin and "access-control-allow-origin" not in response.headers:
            if origin in self.allowed_origins or "*" in self.allowed_origins:
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "*"
                response.headers["Access-Control-Allow-Headers"] = "*"

        return response


def setup_cors(app: FastAPI) -> None:
    """Configure CORS middleware for the FastAPI application."""
    settings = get_settings()

    # Primary CORS middleware — handles preflight (OPTIONS) and normal requests
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-Id", "X-Process-Time"],
    )

    # Fallback — guarantees CORS headers on error responses too
    app.add_middleware(CORSFixMiddleware, allowed_origins=settings.cors_origins_list)
