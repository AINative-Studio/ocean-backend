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


# ========================================================================
# BLOCK SCHEMAS (Issue #8)
# ========================================================================


class BlockCreate(BaseModel):
    """Schema for creating a new block."""

    block_type: str = Field(..., description="Block type: text|heading|list|task|link|page_link")
    content: Dict[str, Any] = Field(..., description="Type-specific content object")
    position: Optional[int] = Field(None, ge=0, description="Block position (auto-calculated if not provided)")
    parent_block_id: Optional[str] = Field(None, description="Parent block ID for nesting")
    properties: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional properties (color, tags)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "block_type": "text",
                    "content": {"text": "This is a paragraph of text"},
                    "position": None,
                    "parent_block_id": None,
                    "properties": {}
                },
                {
                    "block_type": "task",
                    "content": {"text": "Complete API implementation", "checked": False},
                    "position": 0,
                    "properties": {"tags": ["urgent"]}
                }
            ]
        }
    }


class BlockBatchCreate(BaseModel):
    """Schema for batch creating multiple blocks."""

    blocks: list[BlockCreate] = Field(..., min_items=1, max_items=100, description="List of blocks to create (max 100)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "blocks": [
                        {
                            "block_type": "heading",
                            "content": {"text": "Project Overview"},
                            "position": 0
                        },
                        {
                            "block_type": "text",
                            "content": {"text": "This project involves..."},
                            "position": 1
                        }
                    ]
                }
            ]
        }
    }


class BlockUpdate(BaseModel):
    """Schema for updating an existing block."""

    content: Optional[Dict[str, Any]] = Field(None, description="New content object")
    properties: Optional[Dict[str, Any]] = Field(None, description="New properties")
    position: Optional[int] = Field(None, ge=0, description="New position")
    block_type: Optional[str] = Field(None, description="New block type (use convert endpoint for safety)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "content": {"text": "Updated paragraph text"},
                    "properties": {"color": "blue"}
                }
            ]
        }
    }


class BlockMove(BaseModel):
    """Schema for moving/reordering a block."""

    new_position: int = Field(..., ge=0, description="New position within the page (0-based)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"new_position": 5}
            ]
        }
    }


class BlockConvert(BaseModel):
    """Schema for converting a block to a different type."""

    new_type: str = Field(..., description="New block type: text|heading|list|task|link|page_link")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"new_type": "task"}
            ]
        }
    }


class BlockResponse(BaseModel):
    """Schema for block response."""

    block_id: str = Field(..., description="Unique block identifier")
    page_id: str = Field(..., description="Parent page ID")
    organization_id: str = Field(..., description="Organization ID (multi-tenant isolation)")
    user_id: str = Field(..., description="User ID who created the block")
    block_type: str = Field(..., description="Block type")
    position: int = Field(..., description="Position within page (0-based)")
    parent_block_id: Optional[str] = Field(None, description="Parent block ID for nesting")
    content: Dict[str, Any] = Field(..., description="Type-specific content object")
    properties: Dict[str, Any] = Field(default_factory=dict, description="Additional properties")
    vector_id: Optional[str] = Field(None, description="Embedding vector ID (if searchable)")
    vector_dimensions: Optional[int] = Field(None, description="Embedding dimensions (768 for BAAI/bge-base-en-v1.5)")
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")
    updated_at: str = Field(..., description="Last update timestamp (ISO 8601)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "block_id": "550e8400-e29b-41d4-a716-446655440000",
                    "page_id": "abc123",
                    "organization_id": "test-org-456",
                    "user_id": "test-user-123",
                    "block_type": "text",
                    "position": 0,
                    "parent_block_id": None,
                    "content": {"text": "This is a paragraph"},
                    "properties": {},
                    "vector_id": "vec_xyz789",
                    "vector_dimensions": 768,
                    "created_at": "2025-12-24T10:00:00Z",
                    "updated_at": "2025-12-24T10:00:00Z"
                }
            ]
        }
    }


class BlockBatchResponse(BaseModel):
    """Schema for batch block creation response."""

    blocks: list[BlockResponse] = Field(..., description="List of created blocks")
    total: int = Field(..., description="Total number of blocks created")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "blocks": [
                        {
                            "block_id": "550e8400-e29b-41d4-a716-446655440000",
                            "page_id": "abc123",
                            "organization_id": "test-org-456",
                            "user_id": "test-user-123",
                            "block_type": "heading",
                            "position": 0,
                            "content": {"text": "Overview"},
                            "properties": {},
                            "vector_id": "vec_xyz789",
                            "vector_dimensions": 768,
                            "created_at": "2025-12-24T10:00:00Z",
                            "updated_at": "2025-12-24T10:00:00Z"
                        }
                    ],
                    "total": 1
                }
            ]
        }
    }


class BlockListResponse(BaseModel):
    """Schema for paginated list of blocks."""

    blocks: list[BlockResponse] = Field(..., description="List of blocks")
    total: int = Field(..., description="Total number of blocks matching filters")
    limit: int = Field(..., description="Maximum results per page")
    offset: int = Field(..., description="Number of results skipped")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "blocks": [],
                    "total": 0,
                    "limit": 100,
                    "offset": 0
                }
            ]
        }
    }


class BlockEmbeddingResponse(BaseModel):
    """Schema for block embedding information."""

    block_id: str = Field(..., description="Block ID")
    has_embedding: bool = Field(..., description="Whether block has an embedding")
    vector_id: Optional[str] = Field(None, description="Vector ID if embedding exists")
    vector_dimensions: Optional[int] = Field(None, description="Embedding dimensions")
    model: str = Field(default="BAAI/bge-base-en-v1.5", description="Embedding model used")
    searchable_text: Optional[str] = Field(None, description="Text that was embedded (preview)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "block_id": "550e8400-e29b-41d4-a716-446655440000",
                    "has_embedding": True,
                    "vector_id": "vec_xyz789",
                    "vector_dimensions": 768,
                    "model": "BAAI/bge-base-en-v1.5",
                    "searchable_text": "This is a paragraph of text that was embedded..."
                }
            ]
        }
    }
