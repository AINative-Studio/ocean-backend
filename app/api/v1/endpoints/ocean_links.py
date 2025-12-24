"""
Ocean Links API Endpoints.

This module provides REST API endpoints for Ocean link management:
- Create bidirectional links between blocks or block-to-page
- Delete links by ID
- Get page backlinks (all blocks linking to a page)
- Get block backlinks (all blocks linking to a block)

All operations enforce multi-tenant isolation via organization_id.
Links support circular reference detection for block-to-block links.
"""

from fastapi import APIRouter, Depends, HTTPException, Path
from typing import Dict, Any

from app.schemas.ocean import (
    LinkCreate,
    LinkResponse,
    BacklinkListResponse,
    ErrorResponse
)
from app.services.ocean_service import OceanService
from app.api.deps import get_current_user, get_ocean_service

# Create router
router = APIRouter()


@router.post(
    "/links",
    response_model=LinkResponse,
    status_code=201,
    summary="Create link",
    description="Create a bidirectional link between blocks or from block to page",
    responses={
        201: {"description": "Link created successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request data or circular reference"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Source or target not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def create_link(
    link_data: LinkCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: OceanService = Depends(get_ocean_service)
) -> LinkResponse:
    """
    Create a bidirectional link between blocks or from block to page.

    **Request Body:**
    - `source_block_id` (required): Block ID containing the link
    - `target_id` (required): Target block ID or page ID
    - `link_type` (required): Link type (reference, embed, mention)
    - `is_page_link` (optional): True if target_id is a page_id (default: False)

    **Returns:**
    - Complete link object with generated link_id and timestamps

    **Validation:**
    - Validates circular references for block-to-block links
    - Ensures source and target exist and belong to organization
    - Prevents linking to blocks/pages in different organizations

    **Link Types:**
    - `reference`: Simple reference to another block/page
    - `embed`: Embedded content from another block/page
    - `mention`: Mention/tag of another block/page

    **Errors:**
    - 400: Circular reference detected (block A → block B → block A)
    - 404: Source block or target block/page not found
    """
    try:
        result = await service.create_link(
            source_block_id=link_data.source_block_id,
            target_id=link_data.target_id,
            link_type=link_data.link_type,
            org_id=current_user["organization_id"],
            is_page_link=link_data.is_page_link
        )

        if not result:
            raise HTTPException(
                status_code=500,
                detail="Failed to create link"
            )

        return LinkResponse(**result)

    except ValueError as e:
        # ValueError is raised for invalid params, circular refs, or not found
        error_msg = str(e).lower()
        if "not found" in error_msg or "does not belong" in error_msg:
            raise HTTPException(status_code=404, detail=str(e))
        else:
            raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete(
    "/links/{link_id}",
    status_code=204,
    summary="Delete link",
    description="Delete a link by ID (hard delete)",
    responses={
        204: {"description": "Link deleted successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Link not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def delete_link(
    link_id: str = Path(..., description="Link ID to delete"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: OceanService = Depends(get_ocean_service)
) -> None:
    """
    Delete a link by ID (hard delete).

    **Path Parameters:**
    - `link_id`: Unique link identifier

    **Notes:**
    - This is a hard delete - link is permanently removed
    - No undo capability - use with caution
    - Does not delete the source or target blocks/pages
    - Only removes the relationship between them

    **Errors:**
    - 404: Link not found or doesn't belong to organization
    """
    try:
        success = await service.delete_link(
            link_id=link_id,
            org_id=current_user["organization_id"]
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Link {link_id} not found or does not belong to organization"
            )

        # Return 204 No Content on success
        return None

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/pages/{page_id}/backlinks",
    response_model=BacklinkListResponse,
    summary="Get page backlinks",
    description="Get all blocks/pages linking to a specific page",
    responses={
        200: {"description": "Backlinks retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Page not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_page_backlinks(
    page_id: str = Path(..., description="Page ID to get backlinks for"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: OceanService = Depends(get_ocean_service)
) -> BacklinkListResponse:
    """
    Get all blocks linking to a specific page.

    **Path Parameters:**
    - `page_id`: Unique page identifier

    **Returns:**
    - List of backlinks with source block preview information
    - Each backlink includes:
      - link_id: Link identifier
      - link_type: Type of link (reference, embed, mention)
      - source_block_id: Block containing the link
      - source_page_id: Page containing the source block
      - source_block_type: Type of source block
      - source_content_preview: Preview of source block content
      - created_at: Link creation timestamp

    **Use Cases:**
    - Show "Referenced by" section on page
    - Track page popularity/importance
    - Navigate bidirectional links
    - Find related content

    **Notes:**
    - Returns empty list if page has no backlinks
    - Returns empty list if page doesn't exist
    - Limited to 1000 backlinks (reasonable for most use cases)

    **Errors:**
    - 404: Page not found or doesn't belong to organization
    """
    try:
        backlinks = await service.get_page_backlinks(
            page_id=page_id,
            org_id=current_user["organization_id"]
        )

        return BacklinkListResponse(
            backlinks=backlinks,
            total=len(backlinks)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/blocks/{block_id}/backlinks",
    response_model=BacklinkListResponse,
    summary="Get block backlinks",
    description="Get all blocks linking to a specific block",
    responses={
        200: {"description": "Backlinks retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Block not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_block_backlinks(
    block_id: str = Path(..., description="Block ID to get backlinks for"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: OceanService = Depends(get_ocean_service)
) -> BacklinkListResponse:
    """
    Get all blocks linking to a specific block.

    **Path Parameters:**
    - `block_id`: Unique block identifier

    **Returns:**
    - List of backlinks with source block preview information
    - Each backlink includes:
      - link_id: Link identifier
      - link_type: Type of link (reference, embed, mention)
      - source_block_id: Block containing the link
      - source_page_id: Page containing the source block
      - source_block_type: Type of source block
      - source_content_preview: Preview of source block content
      - created_at: Link creation timestamp

    **Use Cases:**
    - Show "Referenced by" section on block
    - Track block importance/connections
    - Navigate bidirectional links
    - Find related content within workspace

    **Notes:**
    - Returns empty list if block has no backlinks
    - Returns empty list if block doesn't exist
    - Limited to 1000 backlinks (reasonable for most use cases)
    - Source blocks that are deleted won't appear in backlinks

    **Errors:**
    - 404: Block not found or doesn't belong to organization
    """
    try:
        backlinks = await service.get_block_backlinks(
            block_id=block_id,
            org_id=current_user["organization_id"]
        )

        return BacklinkListResponse(
            backlinks=backlinks,
            total=len(backlinks)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
