"""
Ocean Search API Endpoints

This module provides hybrid semantic search functionality across Ocean blocks,
combining vector similarity search with metadata filtering.

Issue #14: Hybrid semantic search endpoint
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
import re

from app.schemas.ocean import SearchResponse, SearchResult, ErrorResponse
from app.services.ocean_service import OceanService
from app.config import settings


router = APIRouter()


def get_ocean_service() -> OceanService:
    """
    Dependency injection for OceanService.

    Returns:
        Configured OceanService instance
    """
    return OceanService(
        api_url=settings.ZERODB_API_URL,
        api_key=settings.ZERODB_API_KEY,
        project_id=settings.ZERODB_PROJECT_ID
    )


def extract_highlights(query: str, content: dict, block_type: str) -> list[str]:
    """
    Extract matching terms from block content for highlighting.

    Args:
        query: Original search query
        content: Block content object
        block_type: Type of block

    Returns:
        List of matched terms found in content
    """
    # Extract text from content based on block type
    text = ""
    if block_type in ["text", "heading", "task"]:
        text = content.get("text", "")
    elif block_type == "list":
        items = content.get("items", [])
        text = " ".join(items) if isinstance(items, list) else ""
    elif block_type == "link":
        text = content.get("text", "")
    elif block_type == "page_link":
        text = content.get("displayText", "")

    # Tokenize query into words
    query_words = re.findall(r'\b\w+\b', query.lower())

    # Find matching words in text
    text_lower = text.lower()
    highlights = []

    for word in query_words:
        if len(word) >= 3 and word in text_lower:
            highlights.append(word)

    # Return unique highlights
    return list(set(highlights))


@router.get(
    "/search",
    response_model=SearchResponse,
    responses={
        200: {
            "description": "Search results with similarity scores",
            "model": SearchResponse
        },
        400: {
            "description": "Invalid search parameters",
            "model": ErrorResponse
        },
        500: {
            "description": "Search service error",
            "model": ErrorResponse
        }
    },
    summary="Hybrid semantic search",
    description="""
    Search blocks using hybrid semantic search combining vector similarity and metadata filtering.

    **Search Modes:**
    - `semantic`: Pure vector similarity search using embeddings
    - `metadata`: Filter-only search using metadata (no embeddings)
    - `hybrid`: Combines vector similarity with metadata filters (default)

    **Filters:**
    - `block_types`: Filter by block types (comma-separated: text,heading,task)
    - `page_id`: Filter to specific page
    - `tags`: Filter by tag IDs (comma-separated)
    - `date_from`, `date_to`: Date range filter (ISO 8601 format)

    **Scoring:**
    - Similarity scores range from 0.0 (no match) to 1.0 (perfect match)
    - Threshold parameter filters out results below minimum score
    - Results are ranked by relevance (highest score first)
    """
)
async def search_blocks(
    q: str = Query(
        ...,
        min_length=1,
        description="Search query text",
        example="machine learning algorithms"
    ),
    organization_id: str = Query(
        ...,
        description="Organization ID for multi-tenant isolation",
        example="test-org-456"
    ),
    search_type: str = Query(
        default="hybrid",
        description="Search mode: semantic|metadata|hybrid",
        regex="^(semantic|metadata|hybrid)$"
    ),
    block_types: Optional[str] = Query(
        None,
        description="Comma-separated block types to filter",
        example="text,heading,task"
    ),
    page_id: Optional[str] = Query(
        None,
        description="Filter to specific page ID",
        example="page_abc123"
    ),
    tags: Optional[str] = Query(
        None,
        description="Comma-separated tag IDs to filter",
        example="tag_123,tag_456"
    ),
    date_from: Optional[str] = Query(
        None,
        description="Start date for date range filter (ISO 8601)",
        example="2025-01-01T00:00:00Z"
    ),
    date_to: Optional[str] = Query(
        None,
        description="End date for date range filter (ISO 8601)",
        example="2025-12-31T23:59:59Z"
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Maximum results to return (1-100)"
    ),
    threshold: float = Query(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum similarity threshold (0.0-1.0)"
    ),
    service: OceanService = Depends(get_ocean_service)
) -> SearchResponse:
    """
    Search blocks using hybrid semantic search.

    Supports three search modes:
    - semantic: Pure vector similarity
    - metadata: Filter-only (no vectors)
    - hybrid: Combined approach (default)

    Args:
        q: Search query text
        organization_id: Organization ID (multi-tenant isolation)
        search_type: Search mode
        block_types: Comma-separated block types filter
        page_id: Filter to specific page
        tags: Comma-separated tag IDs
        date_from: Start date for range filter
        date_to: End date for range filter
        limit: Maximum results (1-100)
        threshold: Similarity threshold (0.0-1.0)
        service: Injected OceanService

    Returns:
        SearchResponse with results, total count, and metadata

    Raises:
        HTTPException: 400 for invalid parameters, 500 for service errors
    """
    try:
        # Build filters dictionary
        filters = {}

        # Parse block types
        if block_types:
            block_types_list = [bt.strip() for bt in block_types.split(",") if bt.strip()]
            if block_types_list:
                filters["block_types"] = block_types_list

        # Parse page_id
        if page_id:
            filters["page_id"] = page_id

        # Parse tags
        if tags:
            tags_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
            if tags_list:
                filters["tags"] = tags_list

        # Parse date range
        if date_from or date_to:
            date_range = {}
            if date_from:
                date_range["start"] = date_from
            if date_to:
                date_range["end"] = date_to
            filters["date_range"] = date_range

        # Call service search method
        results = await service.search(
            query=q,
            org_id=organization_id,
            filters=filters,
            search_type=search_type,
            limit=limit,
            threshold=threshold
        )

        # Transform service results to API response format
        search_results = []
        for result in results:
            block = result["block"]
            score = result["score"]

            # Extract highlights for metadata search
            highlights = extract_highlights(q, block["content"], block["block_type"])

            search_results.append(
                SearchResult(
                    block_id=block["block_id"],
                    content=block["content"],
                    block_type=block["block_type"],
                    page_id=block["page_id"],
                    score=score,
                    highlights=highlights,
                    created_at=block["created_at"],
                    updated_at=block["updated_at"]
                )
            )

        # Build response
        return SearchResponse(
            results=search_results,
            total=len(search_results),
            search_type=search_type,
            query=q,
            threshold=threshold,
            limit=limit
        )

    except ValueError as e:
        # Invalid parameters (e.g., empty query, invalid search_type)
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        # Service errors (e.g., embedding generation failure, API timeout)
        raise HTTPException(
            status_code=500,
            detail=f"Search service error: {str(e)}"
        )
