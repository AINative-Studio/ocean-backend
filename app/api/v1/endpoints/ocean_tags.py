"""
Ocean Tags API Endpoints.

This module provides REST API endpoints for Ocean tag management:
- Create, read, update, delete tags
- List tags with sorting options
- Assign/remove tags to/from blocks
- Get block tags

All operations enforce multi-tenant isolation via organization_id.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import Optional, Dict, Any, List

from app.schemas.ocean import (
    TagCreate,
    TagUpdate,
    TagAssign,
    TagResponse,
    TagListResponse,
    ErrorResponse
)
from app.services.ocean_service import OceanService
from app.api.deps import get_current_user, get_ocean_service

# Create router
router = APIRouter()


@router.post(
    "/tags",
    response_model=TagResponse,
    status_code=201,
    summary="Create new tag",
    description="Create a new organization-scoped tag for categorizing blocks",
    responses={
        201: {"description": "Tag created successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request data or tag name already exists"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def create_tag(
    tag_data: TagCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: OceanService = Depends(get_ocean_service)
) -> TagResponse:
    """
    Create a new tag in the organization.

    Tags are used to categorize and organize blocks across pages.
    Tag names must be unique within an organization.

    Args:
        tag_data: Tag creation data (name, color, description)
        current_user: Current authenticated user (from JWT token)
        service: Ocean service instance

    Returns:
        Created tag with generated tag_id and timestamps

    Raises:
        HTTPException: 400 if tag name already exists or validation fails
        HTTPException: 500 if creation fails
    """
    try:
        tag = await service.create_tag(
            org_id=current_user["organization_id"],
            tag_data=tag_data.model_dump()
        )
        return TagResponse(**tag)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create tag: {str(e)}"
        )


@router.get(
    "/tags",
    response_model=TagListResponse,
    summary="List tags",
    description="Get all tags for the organization with optional sorting",
    responses={
        200: {"description": "Tags retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def list_tags(
    sort_by: Optional[str] = Query(
        "usage_count",
        description="Sort field: 'name' (alphabetical) or 'usage_count' (most used first)",
        regex="^(name|usage_count)$"
    ),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: OceanService = Depends(get_ocean_service)
) -> TagListResponse:
    """
    List all tags for the organization.

    Tags are returned sorted by usage count (descending) by default,
    or alphabetically by name if specified.

    Args:
        sort_by: Sort field - 'name' or 'usage_count' (default)
        current_user: Current authenticated user (from JWT token)
        service: Ocean service instance

    Returns:
        List of tags with usage counts and metadata
    """
    try:
        tags = await service.get_tags(org_id=current_user["organization_id"])

        # Re-sort if requested by name
        if sort_by == "name":
            tags.sort(key=lambda t: t.get("name", "").lower())

        return TagListResponse(
            tags=[TagResponse(**tag) for tag in tags],
            total=len(tags)
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list tags: {str(e)}"
        )


@router.put(
    "/tags/{tag_id}",
    response_model=TagResponse,
    summary="Update tag",
    description="Update a tag's properties (name, color, description)",
    responses={
        200: {"description": "Tag updated successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request data or name conflict"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Tag not found or not in organization"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def update_tag(
    tag_id: str = Path(..., description="Tag ID to update"),
    tag_data: TagUpdate = ...,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: OceanService = Depends(get_ocean_service)
) -> TagResponse:
    """
    Update a tag's properties.

    Only fields provided in the request will be updated.
    Tag name must remain unique within the organization.

    Args:
        tag_id: Tag ID to update
        tag_data: Fields to update (name, color, description)
        current_user: Current authenticated user (from JWT token)
        service: Ocean service instance

    Returns:
        Updated tag document

    Raises:
        HTTPException: 400 if new name conflicts with existing tag
        HTTPException: 404 if tag not found or not in organization
        HTTPException: 500 if update fails
    """
    try:
        # Filter out None values from update data
        updates = {k: v for k, v in tag_data.model_dump().items() if v is not None}

        if not updates:
            raise HTTPException(
                status_code=400,
                detail="At least one field must be provided for update"
            )

        updated_tag = await service.update_tag(
            tag_id=tag_id,
            org_id=current_user["organization_id"],
            updates=updates
        )

        if not updated_tag:
            raise HTTPException(
                status_code=404,
                detail=f"Tag {tag_id} not found or does not belong to your organization"
            )

        return TagResponse(**updated_tag)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update tag: {str(e)}"
        )


@router.delete(
    "/tags/{tag_id}",
    status_code=200,
    summary="Delete tag",
    description="Delete a tag and remove it from all blocks",
    responses={
        200: {"description": "Tag deleted successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Tag not found or not in organization"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def delete_tag(
    tag_id: str = Path(..., description="Tag ID to delete"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: OceanService = Depends(get_ocean_service)
) -> Dict[str, Any]:
    """
    Delete a tag and remove it from all blocks.

    This operation:
    1. Removes the tag from all blocks that use it
    2. Deletes the tag document from the database

    Args:
        tag_id: Tag ID to delete
        current_user: Current authenticated user (from JWT token)
        service: Ocean service instance

    Returns:
        Success message with tag_id

    Raises:
        HTTPException: 404 if tag not found or not in organization
        HTTPException: 500 if deletion fails
    """
    try:
        success = await service.delete_tag(
            tag_id=tag_id,
            org_id=current_user["organization_id"]
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Tag {tag_id} not found or does not belong to your organization"
            )

        return {
            "success": True,
            "message": "Tag deleted successfully",
            "tag_id": tag_id
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete tag: {str(e)}"
        )


@router.post(
    "/blocks/{block_id}/tags",
    status_code=200,
    summary="Assign tag to block",
    description="Assign a tag to a block and increment its usage count",
    responses={
        200: {"description": "Tag assigned successfully"},
        400: {"model": ErrorResponse, "description": "Tag already assigned or invalid data"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Block or tag not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def assign_tag_to_block(
    block_id: str = Path(..., description="Block ID to tag"),
    tag_assignment: TagAssign = ...,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: OceanService = Depends(get_ocean_service)
) -> Dict[str, Any]:
    """
    Assign a tag to a block.

    This operation:
    1. Adds the tag_id to the block's properties.tags array
    2. Increments the tag's usage_count

    Args:
        block_id: Block ID to tag
        tag_assignment: Tag assignment data (tag_id)
        current_user: Current authenticated user (from JWT token)
        service: Ocean service instance

    Returns:
        Success message with block_id and tag_id

    Raises:
        HTTPException: 400 if tag is already assigned to the block
        HTTPException: 404 if block or tag not found
        HTTPException: 500 if assignment fails
    """
    try:
        success = await service.assign_tag_to_block(
            block_id=block_id,
            tag_id=tag_assignment.tag_id,
            org_id=current_user["organization_id"]
        )

        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Tag {tag_assignment.tag_id} is already assigned to block {block_id}"
            )

        return {
            "success": True,
            "message": "Tag assigned to block successfully",
            "block_id": block_id,
            "tag_id": tag_assignment.tag_id
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to assign tag to block: {str(e)}"
        )


@router.delete(
    "/blocks/{block_id}/tags/{tag_id}",
    status_code=200,
    summary="Remove tag from block",
    description="Remove a tag from a block and decrement its usage count",
    responses={
        200: {"description": "Tag removed successfully"},
        400: {"model": ErrorResponse, "description": "Tag not assigned to block"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Block or tag not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def remove_tag_from_block(
    block_id: str = Path(..., description="Block ID to untag"),
    tag_id: str = Path(..., description="Tag ID to remove"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: OceanService = Depends(get_ocean_service)
) -> Dict[str, Any]:
    """
    Remove a tag from a block.

    This operation:
    1. Removes the tag_id from the block's properties.tags array
    2. Decrements the tag's usage_count

    Args:
        block_id: Block ID to untag
        tag_id: Tag ID to remove
        current_user: Current authenticated user (from JWT token)
        service: Ocean service instance

    Returns:
        Success message with block_id and tag_id

    Raises:
        HTTPException: 400 if tag is not assigned to the block
        HTTPException: 404 if block or tag not found
        HTTPException: 500 if removal fails
    """
    try:
        success = await service.remove_tag_from_block(
            block_id=block_id,
            tag_id=tag_id,
            org_id=current_user["organization_id"]
        )

        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Tag {tag_id} is not assigned to block {block_id}"
            )

        return {
            "success": True,
            "message": "Tag removed from block successfully",
            "block_id": block_id,
            "tag_id": tag_id
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove tag from block: {str(e)}"
        )


@router.get(
    "/blocks/{block_id}/tags",
    response_model=TagListResponse,
    summary="Get block tags",
    description="Get all tags assigned to a specific block",
    responses={
        200: {"description": "Block tags retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Block not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_block_tags(
    block_id: str = Path(..., description="Block ID to get tags for"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: OceanService = Depends(get_ocean_service)
) -> TagListResponse:
    """
    Get all tags assigned to a block.

    Returns full tag details (name, color, description, usage_count)
    for all tags assigned to the specified block.

    Args:
        block_id: Block ID to get tags for
        current_user: Current authenticated user (from JWT token)
        service: Ocean service instance

    Returns:
        List of tags assigned to the block

    Raises:
        HTTPException: 404 if block not found
        HTTPException: 500 if retrieval fails
    """
    try:
        # Get the block to access its tags
        block = await service.get_block(
            block_id=block_id,
            org_id=current_user["organization_id"]
        )

        if not block:
            raise HTTPException(
                status_code=404,
                detail=f"Block {block_id} not found or does not belong to your organization"
            )

        # Get tag IDs from block properties
        tag_ids = block.get("properties", {}).get("tags", [])

        if not tag_ids:
            return TagListResponse(tags=[], total=0)

        # Get all tags for the organization
        all_tags = await service.get_tags(org_id=current_user["organization_id"])

        # Filter to only tags assigned to this block
        block_tags = [tag for tag in all_tags if tag.get("tag_id") in tag_ids]

        # Sort by usage count (descending)
        block_tags.sort(key=lambda t: t.get("usage_count", 0), reverse=True)

        return TagListResponse(
            tags=[TagResponse(**tag) for tag in block_tags],
            total=len(block_tags)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get block tags: {str(e)}"
        )
