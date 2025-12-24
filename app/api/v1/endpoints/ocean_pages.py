"""
Ocean Pages API Endpoints.

This module provides REST API endpoints for Ocean page management:
- Create, read, update, delete pages
- List pages with filtering and pagination
- Move pages to different parents
- Soft deletion (archiving)

All operations enforce multi-tenant isolation via organization_id.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import Optional, Dict, Any

from app.schemas.ocean import (
    PageCreate,
    PageUpdate,
    PageMove,
    PageResponse,
    PageListResponse,
    ErrorResponse
)
from app.services.ocean_service import OceanService
from app.api.deps import get_current_user, get_ocean_service

# Create router
router = APIRouter()


@router.post(
    "/pages",
    response_model=PageResponse,
    status_code=201,
    summary="Create new page",
    description="Create a new Ocean page in the workspace",
    responses={
        201: {"description": "Page created successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request data"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def create_page(
    page_data: PageCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: OceanService = Depends(get_ocean_service)
) -> PageResponse:
    """
    Create a new page in the workspace.

    **Request Body:**
    - `title` (required): Page title (1-500 characters)
    - `icon` (optional): Emoji or icon identifier
    - `cover_image` (optional): Cover image URL or file_id
    - `parent_page_id` (optional): Parent page ID for nesting
    - `metadata` (optional): Additional page properties

    **Returns:**
    - Complete page object with generated page_id and timestamps
    """
    try:
        result = await service.create_page(
            org_id=current_user["organization_id"],
            user_id=current_user["user_id"],
            page_data=page_data.model_dump()
        )

        if not result:
            raise HTTPException(
                status_code=500,
                detail="Failed to create page"
            )

        return PageResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/pages",
    response_model=PageListResponse,
    summary="List pages",
    description="Get all pages for the current organization with optional filtering",
    responses={
        200: {"description": "Pages retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def list_pages(
    parent_page_id: Optional[str] = Query(None, description="Filter by parent page ID"),
    is_archived: Optional[bool] = Query(None, description="Filter by archived status"),
    is_favorite: Optional[bool] = Query(None, description="Filter favorite pages"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results per page"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: OceanService = Depends(get_ocean_service)
) -> PageListResponse:
    """
    Get all pages for the current organization.

    **Query Parameters:**
    - `parent_page_id`: Filter by parent (for nested pages)
    - `is_archived`: Filter archived status (default: exclude archived)
    - `is_favorite`: Filter favorite pages
    - `limit`: Max results (1-100, default: 50)
    - `offset`: Skip results (default: 0)

    **Returns:**
    - List of pages with pagination metadata
    """
    try:
        # Build filters
        filters = {}
        if parent_page_id is not None:
            filters["parent_page_id"] = parent_page_id
        if is_archived is not None:
            filters["is_archived"] = is_archived
        if is_favorite is not None:
            filters["is_favorite"] = is_favorite

        # Get pages and total count
        pages = await service.get_pages(
            org_id=current_user["organization_id"],
            filters=filters if filters else None,
            pagination={"limit": limit, "offset": offset}
        )

        # Get total count (same filters, no pagination)
        total = await service.count_pages(
            org_id=current_user["organization_id"],
            filters=filters if filters else None
        )

        # Convert to response models
        page_responses = [PageResponse(**page) for page in pages]

        return PageListResponse(
            pages=page_responses,
            total=total,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/pages/{page_id}",
    response_model=PageResponse,
    summary="Get page by ID",
    description="Retrieve a specific page by its ID",
    responses={
        200: {"description": "Page retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Page not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_page(
    page_id: str = Path(..., description="Page ID to retrieve"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: OceanService = Depends(get_ocean_service)
) -> PageResponse:
    """
    Get a specific page by ID.

    **Path Parameters:**
    - `page_id`: Unique page identifier

    **Returns:**
    - Complete page object

    **Errors:**
    - 404: Page not found or doesn't belong to organization
    """
    try:
        page = await service.get_page(
            page_id=page_id,
            org_id=current_user["organization_id"]
        )

        if not page:
            raise HTTPException(
                status_code=404,
                detail=f"Page {page_id} not found or does not belong to organization"
            )

        return PageResponse(**page)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.put(
    "/pages/{page_id}",
    response_model=PageResponse,
    summary="Update page",
    description="Update an existing page",
    responses={
        200: {"description": "Page updated successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request data"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Page not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def update_page(
    page_id: str = Path(..., description="Page ID to update"),
    updates: PageUpdate = ...,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: OceanService = Depends(get_ocean_service)
) -> PageResponse:
    """
    Update an existing page.

    **Path Parameters:**
    - `page_id`: Unique page identifier

    **Request Body:**
    - `title` (optional): New page title
    - `icon` (optional): New page icon
    - `cover_image` (optional): New cover image
    - `is_favorite` (optional): Toggle favorite status
    - `metadata` (optional): Update metadata

    **Returns:**
    - Updated page object

    **Errors:**
    - 404: Page not found or doesn't belong to organization
    """
    try:
        # Filter out None values to only update provided fields
        update_data = {k: v for k, v in updates.model_dump().items() if v is not None}

        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="No fields provided for update"
            )

        updated_page = await service.update_page(
            page_id=page_id,
            org_id=current_user["organization_id"],
            updates=update_data
        )

        if not updated_page:
            raise HTTPException(
                status_code=404,
                detail=f"Page {page_id} not found or does not belong to organization"
            )

        return PageResponse(**updated_page)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.delete(
    "/pages/{page_id}",
    status_code=204,
    summary="Delete page",
    description="Delete a page (soft delete by archiving)",
    responses={
        204: {"description": "Page deleted successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Page not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def delete_page(
    page_id: str = Path(..., description="Page ID to delete"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: OceanService = Depends(get_ocean_service)
) -> None:
    """
    Delete a page (soft delete by archiving).

    **Path Parameters:**
    - `page_id`: Unique page identifier

    **Notes:**
    - This is a soft delete - sets `is_archived=true`
    - Page can be restored by updating `is_archived` back to `false`
    - Archived pages are excluded from default listings

    **Errors:**
    - 404: Page not found or doesn't belong to organization
    """
    try:
        success = await service.delete_page(
            page_id=page_id,
            org_id=current_user["organization_id"]
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Page {page_id} not found or does not belong to organization"
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


@router.post(
    "/pages/{page_id}/move",
    response_model=PageResponse,
    summary="Move page",
    description="Move a page to a new parent or to root level",
    responses={
        200: {"description": "Page moved successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request data"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Page not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def move_page(
    page_id: str = Path(..., description="Page ID to move"),
    move_data: PageMove = ...,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: OceanService = Depends(get_ocean_service)
) -> PageResponse:
    """
    Move a page to a new parent or to root level.

    **Path Parameters:**
    - `page_id`: Unique page identifier

    **Request Body:**
    - `new_parent_id`: New parent page ID (null to move to root level)

    **Returns:**
    - Updated page object with new parent and position

    **Errors:**
    - 400: Invalid parent_id or circular reference
    - 404: Page or parent not found
    """
    try:
        moved_page = await service.move_page(
            page_id=page_id,
            new_parent_id=move_data.new_parent_id,
            org_id=current_user["organization_id"]
        )

        if not moved_page:
            raise HTTPException(
                status_code=404,
                detail=f"Page {page_id} not found or does not belong to organization"
            )

        return PageResponse(**moved_page)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
