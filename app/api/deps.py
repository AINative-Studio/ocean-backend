"""
FastAPI dependencies for Ocean API endpoints.

This module provides reusable dependencies for authentication, authorization,
and service initialization.
"""

from fastapi import Header, HTTPException, Depends
from typing import Dict, Any
from app.config import settings
from app.services.ocean_service import OceanService


async def get_current_user(authorization: str = Header(None)) -> Dict[str, Any]:
    """
    Get current user from JWT token.

    For MVP: Returns test user for development.
    TODO: Integrate with AINative core auth service for production.

    Args:
        authorization: Authorization header with Bearer token

    Returns:
        Dictionary containing user_id and organization_id

    Raises:
        HTTPException: 401 if no authorization header provided
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Authorization header required."
        )

    # TODO: Validate JWT token and extract user claims
    # For MVP: Return mock user for testing
    # In production: Call AINative core auth service to validate token
    return {
        "user_id": "test-user-123",
        "organization_id": "test-org-456",
        "email": "test@example.com",
        "role": "user"
    }


def get_ocean_service() -> OceanService:
    """
    Dependency to get OceanService instance.

    This creates a new OceanService instance configured with ZeroDB
    connection details from application settings.

    Returns:
        Configured OceanService instance
    """
    return OceanService(
        api_url=settings.ZERODB_API_URL,
        api_key=settings.ZERODB_API_KEY,
        project_id=settings.ZERODB_PROJECT_ID
    )
