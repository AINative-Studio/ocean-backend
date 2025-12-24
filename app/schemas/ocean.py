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


# ========================================================================
# LINK SCHEMAS (Issue #11)
# ========================================================================


class LinkCreate(BaseModel):
    """Schema for creating a new link between blocks or block-to-page."""

    source_block_id: str = Field(..., description="Block ID containing the link")
    target_id: str = Field(..., description="Target block ID or page ID")
    link_type: str = Field(..., description="Link type: reference|embed|mention")
    is_page_link: bool = Field(False, description="True if target_id is a page_id, False if block_id")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "source_block_id": "block_abc123",
                    "target_id": "block_xyz789",
                    "link_type": "reference",
                    "is_page_link": False
                },
                {
                    "source_block_id": "block_abc123",
                    "target_id": "page_xyz789",
                    "link_type": "mention",
                    "is_page_link": True
                }
            ]
        }
    }


class LinkResponse(BaseModel):
    """Schema for link response."""

    link_id: str = Field(..., description="Unique link identifier")
    organization_id: str = Field(..., description="Organization ID (multi-tenant isolation)")
    source_block_id: str = Field(..., description="Source block ID")
    target_block_id: Optional[str] = Field(None, description="Target block ID (null for page links)")
    target_page_id: Optional[str] = Field(None, description="Target page ID (null for block links)")
    link_type: str = Field(..., description="Link type: reference|embed|mention")
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "link_id": "550e8400-e29b-41d4-a716-446655440000",
                    "organization_id": "test-org-456",
                    "source_block_id": "block_abc123",
                    "target_block_id": "block_xyz789",
                    "target_page_id": None,
                    "link_type": "reference",
                    "created_at": "2025-12-24T10:00:00Z"
                }
            ]
        }
    }


class BacklinkResponse(BaseModel):
    """Schema for backlink information with source block preview."""

    link_id: str = Field(..., description="Link ID")
    link_type: str = Field(..., description="Link type: reference|embed|mention")
    source_block_id: str = Field(..., description="Block ID containing the link")
    source_page_id: str = Field(..., description="Page ID containing the source block")
    source_block_type: str = Field(..., description="Type of source block")
    source_content_preview: str = Field(..., description="Preview of source block content")
    created_at: str = Field(..., description="Link creation timestamp (ISO 8601)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "link_id": "550e8400-e29b-41d4-a716-446655440000",
                    "link_type": "reference",
                    "source_block_id": "block_abc123",
                    "source_page_id": "page_xyz789",
                    "source_block_type": "text",
                    "source_content_preview": "This paragraph references the important concept...",
                    "created_at": "2025-12-24T10:00:00Z"
                }
            ]
        }
    }


class BacklinkListResponse(BaseModel):
    """Schema for list of backlinks."""

    backlinks: list[BacklinkResponse] = Field(..., description="List of backlinks")
    total: int = Field(..., description="Total number of backlinks")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "backlinks": [
                        {
                            "link_id": "550e8400-e29b-41d4-a716-446655440000",
                            "link_type": "reference",
                            "source_block_id": "block_abc123",
                            "source_page_id": "page_xyz789",
                            "source_block_type": "text",
                            "source_content_preview": "This paragraph references...",
                            "created_at": "2025-12-24T10:00:00Z"
                        }
                    ],
                    "total": 1
                }
            ]
        }
    }


# ========================================================================
# SEARCH SCHEMAS (Issue #14)
# ========================================================================


class SearchRequest(BaseModel):
    """Schema for search query parameters."""

    q: str = Field(..., min_length=1, description="Search query text")
    search_type: str = Field(
        default="hybrid",
        description="Search mode: semantic|metadata|hybrid"
    )
    block_types: Optional[str] = Field(
        None,
        description="Comma-separated block types to filter (e.g., 'text,heading,task')"
    )
    page_id: Optional[str] = Field(
        None,
        description="Filter to specific page ID"
    )
    tags: Optional[str] = Field(
        None,
        description="Comma-separated tag IDs to filter"
    )
    date_from: Optional[str] = Field(
        None,
        description="ISO date for start of date range filter"
    )
    date_to: Optional[str] = Field(
        None,
        description="ISO date for end of date range filter"
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum results to return (1-100, default: 20)"
    )
    threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity threshold for semantic search (0.0-1.0, default: 0.7)"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "q": "machine learning algorithms",
                    "search_type": "hybrid",
                    "block_types": "text,heading",
                    "limit": 10,
                    "threshold": 0.75
                }
            ]
        }
    }


class SearchResult(BaseModel):
    """Schema for individual search result."""

    block_id: str = Field(..., description="Block ID")
    content: Dict[str, Any] = Field(..., description="Block content")
    block_type: str = Field(..., description="Block type")
    page_id: str = Field(..., description="Parent page ID")
    score: float = Field(..., description="Relevance score (0.0-1.0)")
    highlights: Optional[list[str]] = Field(
        default_factory=list,
        description="Matched text snippets (for metadata search)"
    )
    created_at: str = Field(..., description="Block creation timestamp (ISO 8601)")
    updated_at: str = Field(..., description="Block last update timestamp (ISO 8601)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "block_id": "550e8400-e29b-41d4-a716-446655440000",
                    "content": {"text": "Machine learning is a subset of AI that enables systems to learn from data."},
                    "block_type": "text",
                    "page_id": "page_abc123",
                    "score": 0.92,
                    "highlights": ["machine learning", "AI"],
                    "created_at": "2025-12-24T10:00:00Z",
                    "updated_at": "2025-12-24T10:00:00Z"
                }
            ]
        }
    }


class SearchResponse(BaseModel):
    """Schema for search response."""

    results: list[SearchResult] = Field(..., description="Search results")
    total: int = Field(..., description="Total number of results found")
    search_type: str = Field(..., description="Search mode used")
    query: str = Field(..., description="Original search query")
    threshold: float = Field(..., description="Similarity threshold applied")
    limit: int = Field(..., description="Maximum results returned")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "results": [
                        {
                            "block_id": "550e8400-e29b-41d4-a716-446655440000",
                            "content": {"text": "Machine learning is a subset of AI."},
                            "block_type": "text",
                            "page_id": "page_abc123",
                            "score": 0.92,
                            "highlights": ["machine learning"],
                            "created_at": "2025-12-24T10:00:00Z",
                            "updated_at": "2025-12-24T10:00:00Z"
                        }
                    ],
                    "total": 1,
                    "search_type": "hybrid",
                    "query": "machine learning algorithms",
                    "threshold": 0.7,
                    "limit": 20
                }
            ]
        }
    }


# ========================================================================
# TAG SCHEMAS (Issue #16)
# ========================================================================


class TagCreate(BaseModel):
    """Schema for creating a new tag."""

    name: str = Field(..., min_length=1, max_length=100, description="Tag name (unique per organization)")
    color: Optional[str] = Field("#6B7280", pattern="^#[0-9A-Fa-f]{6}$", description="Hex color code (e.g., #FF5733)")
    description: Optional[str] = Field("", max_length=500, description="Tag description")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "urgent",
                    "color": "#EF4444",
                    "description": "High-priority items requiring immediate attention"
                },
                {
                    "name": "design",
                    "color": "#8B5CF6",
                    "description": "Design-related tasks and documents"
                }
            ]
        }
    }


class TagUpdate(BaseModel):
    """Schema for updating an existing tag."""

    name: Optional[str] = Field(None, min_length=1, max_length=100, description="New tag name")
    color: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$", description="New hex color code")
    description: Optional[str] = Field(None, max_length=500, description="New tag description")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "name": "high-priority",
                    "color": "#DC2626"
                },
                {
                    "description": "Updated description for the tag"
                }
            ]
        }
    }


class TagAssign(BaseModel):
    """Schema for assigning a tag to a block."""

    tag_id: str = Field(..., description="Tag ID to assign to the block")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"tag_id": "550e8400-e29b-41d4-a716-446655440000"}
            ]
        }
    }


class TagResponse(BaseModel):
    """Schema for tag response."""

    tag_id: str = Field(..., description="Unique tag identifier")
    organization_id: str = Field(..., description="Organization ID (multi-tenant isolation)")
    name: str = Field(..., description="Tag name")
    color: str = Field(..., description="Hex color code")
    description: str = Field(..., description="Tag description")
    usage_count: int = Field(..., ge=0, description="Number of blocks using this tag")
    created_at: str = Field(..., description="Creation timestamp (ISO 8601)")
    updated_at: str = Field(..., description="Last update timestamp (ISO 8601)")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "tag_id": "550e8400-e29b-41d4-a716-446655440000",
                    "organization_id": "test-org-456",
                    "name": "urgent",
                    "color": "#EF4444",
                    "description": "High-priority items",
                    "usage_count": 15,
                    "created_at": "2025-12-24T10:00:00Z",
                    "updated_at": "2025-12-24T10:00:00Z"
                }
            ]
        }
    }


class TagListResponse(BaseModel):
    """Schema for list of tags."""

    tags: list[TagResponse] = Field(..., description="List of tags sorted by usage count")
    total: int = Field(..., description="Total number of tags")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "tags": [
                        {
                            "tag_id": "550e8400-e29b-41d4-a716-446655440000",
                            "organization_id": "test-org-456",
                            "name": "urgent",
                            "color": "#EF4444",
                            "description": "High-priority items",
                            "usage_count": 15,
                            "created_at": "2025-12-24T10:00:00Z",
                            "updated_at": "2025-12-24T10:00:00Z"
                        }
                    ],
                    "total": 1
                }
            ]
        }
    }
