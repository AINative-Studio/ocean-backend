"""
Pydantic schemas for Ocean API request/response validation.

These schemas provide automatic validation, serialization, and documentation
for all Ocean page endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class PageCreate(BaseModel):
    """Schema for creating a new page."""

    title: str = Field(..., min_length=1, max_length=500, description="Page title")
    icon: Optional[str] = Field(None, description="Page icon (emoji or identifier)")
    cover_image: Optional[str] = Field(None, description="Cover image URL or file_id")
    parent_page_id: Optional[str] = Field(None, description="Parent page ID for nesting")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional page metadata")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Product Roadmap",
                    "icon": "🚀",
                    "cover_image": None,
                    "parent_page_id": None,
                    "metadata": {}
                }
            ]
        }
    }


class PageUpdate(BaseModel):
    """Schema for updating an existing page."""

    title: Optional[str] = Field(None, min_length=1, max_length=500, description="New page title")
    icon: Optional[str] = Field(None, description="New page icon")
    cover_image: Optional[str] = Field(None, description="New cover image URL or file_id")
    is_favorite: Optional[bool] = Field(None, description="Toggle favorite status")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Update page metadata")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "title": "Updated Product Roadmap",
                    "icon": "📋",
                    "is_favorite": True
                }
            ]
        }
    }


class PageMove(BaseModel):
    """Schema for moving a page to a new parent."""

    new_parent_id: Optional[str] = Field(None, description="New parent page ID (null for root level)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"new_parent_id": "abc123"},
                {"new_parent_id": None}
            ]
        }
    }


class PageResponse(BaseModel):
    """Schema for page response."""

    page_id: str = Field(..., description="Unique page identifier")
    organization_id: str = Field(..., description="Organization ID (multi-tenant isolation)")
    user_id: str = Field(..., description="User ID who created the page")
    title: str = Field(..., description="Page title")
    icon: Optional[str] = Field(None, description="Page icon")
    cover_image: Optional[str] = Field(None, description="Cover image URL or file_id")
    parent_page_id: Optional[str] = Field(None, description="Parent page ID")
    position: int = Field(..., description="Position within parent (0-based)")
    is_archived: bool = Field(..., description="Whether page is archived (soft deleted)")
    is_favorite: bool = Field(..., description="Whether page is marked as favorite")
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")
    updated_at: str = Field(..., description="Last update timestamp (ISO 8601)")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional page metadata")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "page_id": "550e8400-e29b-41d4-a716-446655440000",
                    "organization_id": "test-org-456",
                    "user_id": "test-user-123",
                    "title": "Product Roadmap",
                    "icon": "🚀",
                    "cover_image": None,
                    "parent_page_id": None,
                    "position": 0,
                    "is_archived": False,
                    "is_favorite": True,
                    "created_at": "2025-12-24T10:00:00Z",
                    "updated_at": "2025-12-24T10:00:00Z",
                    "metadata": {}
                }
            ]
        }
    }


class PageListResponse(BaseModel):
    """Schema for paginated list of pages."""

    pages: list[PageResponse] = Field(..., description="List of pages")
    total: int = Field(..., description="Total number of pages matching filters")
    limit: int = Field(..., description="Maximum results per page")
    offset: int = Field(..., description="Number of results skipped")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "pages": [
                        {
                            "page_id": "550e8400-e29b-41d4-a716-446655440000",
                            "organization_id": "test-org-456",
                            "user_id": "test-user-123",
                            "title": "Product Roadmap",
                            "icon": "🚀",
                            "cover_image": None,
                            "parent_page_id": None,
                            "position": 0,
                            "is_archived": False,
                            "is_favorite": True,
                            "created_at": "2025-12-24T10:00:00Z",
                            "updated_at": "2025-12-24T10:00:00Z",
                            "metadata": {}
                        }
                    ],
                    "total": 1,
                    "limit": 50,
                    "offset": 0
                }
            ]
        }
    }


class ErrorResponse(BaseModel):
    """Schema for error responses."""

    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Machine-readable error code")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "detail": "Page not found",
                    "error_code": "PAGE_NOT_FOUND"
                }
            ]
        }
    }
