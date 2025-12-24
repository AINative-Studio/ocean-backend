"""
Ocean Blocks API Endpoints.

This module provides REST API endpoints for Ocean block management:
- Create single and batch blocks with automatic embedding generation
- Read blocks by ID or by page
- Update blocks with embedding regeneration
- Delete blocks with cleanup
- Reorder blocks (move position)
- Convert block types intelligently
- Get embedding metadata

All operations enforce multi-tenant isolation via organization_id.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from typing import Optional, Dict, Any, List

from app.schemas.ocean import (
    BlockCreate,
    BlockBatchCreate,
    BlockUpdate,
    BlockMove,
    BlockConvert,
    BlockResponse,
    BlockBatchResponse,
    BlockListResponse,
    BlockEmbeddingResponse,
    ErrorResponse
)
from app.services.ocean_service import OceanService
from app.api.deps import get_current_user, get_ocean_service

# Create router
router = APIRouter()


@router.post(
    "/blocks",
    response_model=BlockResponse,
    status_code=201,
    summary="Create new block",
    description="Create a new Ocean block with automatic embedding generation",
    responses={
        201: {"description": "Block created successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request data"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Page not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def create_block(
    page_id: str = Query(..., description="Page ID to create the block in"),
    block_data: BlockCreate = ...,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: OceanService = Depends(get_ocean_service)
) -> BlockResponse:
    """
    Create a new block in a page with automatic embedding generation.

    **Query Parameters:**
    - `page_id` (required): Page ID to create the block in

    **Request Body:**
    - `block_type` (required): text|heading|list|task|link|page_link
    - `content` (required): Type-specific content object
    - `position` (optional): Block position (auto-calculated if not provided)
    - `parent_block_id` (optional): Parent block for nesting
    - `properties` (optional): Additional properties (color, tags, etc.)

    **Returns:**
    - Complete block object with generated block_id, embeddings, and timestamps

    **Notes:**
    - Blocks with searchable content automatically get embeddings (768 dims, BAAI/bge-base-en-v1.5)
    - Position defaults to end of page if not specified
    """
    try:
        result = await service.create_block(
            page_id=page_id,
            org_id=current_user["organization_id"],
            user_id=current_user["user_id"],
            block_data=block_data.model_dump()
        )

        if not result:
            raise HTTPException(
                status_code=500,
                detail="Failed to create block"
            )

        return BlockResponse(**result)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.post(
    "/blocks/batch",
    response_model=BlockBatchResponse,
    status_code=201,
    summary="Batch create blocks",
    description="Create multiple blocks efficiently with batch embedding generation",
    responses={
        201: {"description": "Blocks created successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request data"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Page not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def create_blocks_batch(
    page_id: str = Query(..., description="Page ID to create blocks in"),
    batch_data: BlockBatchCreate = ...,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: OceanService = Depends(get_ocean_service)
) -> BlockBatchResponse:
    """
    Bulk create multiple blocks efficiently (optimized for 100+ blocks).

    **Query Parameters:**
    - `page_id` (required): Page ID to create blocks in

    **Request Body:**
    - `blocks` (required): List of block data (max 100 blocks)

    **Returns:**
    - List of created blocks with embeddings

    **Notes:**
    - Optimized for large imports (e.g., content migration, page duplication)
    - Uses batch embedding generation for efficiency
    - Positions are auto-calculated in sequence
    """
    try:
        blocks_list = [block.model_dump() for block in batch_data.blocks]

        results = await service.create_block_batch(
            page_id=page_id,
            org_id=current_user["organization_id"],
            user_id=current_user["user_id"],
            blocks_list=blocks_list
        )

        if not results:
            raise HTTPException(
                status_code=500,
                detail="Failed to create blocks"
            )

        block_responses = [BlockResponse(**block) for block in results]

        return BlockBatchResponse(
            blocks=block_responses,
            total=len(block_responses)
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/blocks/{block_id}",
    response_model=BlockResponse,
    summary="Get block by ID",
    description="Retrieve a specific block by its ID",
    responses={
        200: {"description": "Block retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Block not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_block(
    block_id: str = Path(..., description="Block ID to retrieve"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: OceanService = Depends(get_ocean_service)
) -> BlockResponse:
    """
    Get a specific block by ID.

    **Path Parameters:**
    - `block_id`: Unique block identifier

    **Returns:**
    - Complete block object with embedding metadata

    **Errors:**
    - 404: Block not found or doesn't belong to organization
    """
    try:
        block = await service.get_block(
            block_id=block_id,
            org_id=current_user["organization_id"]
        )

        if not block:
            raise HTTPException(
                status_code=404,
                detail=f"Block {block_id} not found or does not belong to organization"
            )

        return BlockResponse(**block)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/blocks",
    response_model=BlockListResponse,
    summary="List blocks by page",
    description="Get all blocks for a page with optional filtering and pagination",
    responses={
        200: {"description": "Blocks retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def list_blocks(
    page_id: str = Query(..., description="Page ID to get blocks for"),
    block_type: Optional[str] = Query(None, description="Filter by block type"),
    parent_block_id: Optional[str] = Query(None, description="Filter by parent block (for nested blocks)"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results per page"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: OceanService = Depends(get_ocean_service)
) -> BlockListResponse:
    """
    Get all blocks for a page, ordered by position.

    **Query Parameters:**
    - `page_id` (required): Page ID to get blocks for
    - `block_type`: Filter by block type (text, heading, list, etc.)
    - `parent_block_id`: Filter by parent block (for nested blocks)
    - `limit`: Max results (1-500, default: 100)
    - `offset`: Skip results (default: 0)

    **Returns:**
    - List of blocks ordered by position with pagination metadata

    **Notes:**
    - Blocks are always returned in position order (0, 1, 2, ...)
    - Use parent_block_id filter to get nested blocks
    """
    try:
        # Build filters
        filters = {}
        if block_type is not None:
            filters["block_type"] = block_type
        if parent_block_id is not None:
            filters["parent_block_id"] = parent_block_id

        # Get blocks
        blocks = await service.get_blocks_by_page(
            page_id=page_id,
            org_id=current_user["organization_id"],
            filters=filters if filters else None,
            pagination={"limit": limit, "offset": offset}
        )

        # Convert to response models
        block_responses = [BlockResponse(**block) for block in blocks]

        return BlockListResponse(
            blocks=block_responses,
            total=len(block_responses),  # TODO: Add count query to service
            limit=limit,
            offset=offset
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.put(
    "/blocks/{block_id}",
    response_model=BlockResponse,
    summary="Update block",
    description="Update an existing block with automatic embedding regeneration",
    responses={
        200: {"description": "Block updated successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request data"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Block not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def update_block(
    block_id: str = Path(..., description="Block ID to update"),
    updates: BlockUpdate = ...,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: OceanService = Depends(get_ocean_service)
) -> BlockResponse:
    """
    Update an existing block.

    **Path Parameters:**
    - `block_id`: Unique block identifier

    **Request Body:**
    - `content` (optional): New content object
    - `properties` (optional): New properties
    - `position` (optional): New position
    - `block_type` (optional): New block type (recommend using /convert endpoint)

    **Returns:**
    - Updated block object

    **Notes:**
    - If content changes, embedding is automatically regenerated
    - Old embedding is deleted before creating new one
    - Use /convert endpoint for safer block type conversion

    **Errors:**
    - 404: Block not found or doesn't belong to organization
    """
    try:
        # Filter out None values to only update provided fields
        update_data = {k: v for k, v in updates.model_dump().items() if v is not None}

        if not update_data:
            raise HTTPException(
                status_code=400,
                detail="No fields provided for update"
            )

        updated_block = await service.update_block(
            block_id=block_id,
            org_id=current_user["organization_id"],
            updates=update_data
        )

        if not updated_block:
            raise HTTPException(
                status_code=404,
                detail=f"Block {block_id} not found or does not belong to organization"
            )

        return BlockResponse(**updated_block)

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
    "/blocks/{block_id}",
    status_code=204,
    summary="Delete block",
    description="Delete a block and its embedding (hard delete)",
    responses={
        204: {"description": "Block deleted successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Block not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def delete_block(
    block_id: str = Path(..., description="Block ID to delete"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: OceanService = Depends(get_ocean_service)
) -> None:
    """
    Delete a block (hard delete with embedding cleanup).

    **Path Parameters:**
    - `block_id`: Unique block identifier

    **Notes:**
    - This is a hard delete - block is permanently removed
    - Associated embedding vector is also deleted
    - No undo capability - use with caution

    **Errors:**
    - 404: Block not found or doesn't belong to organization
    """
    try:
        success = await service.delete_block(
            block_id=block_id,
            org_id=current_user["organization_id"]
        )

        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Block {block_id} not found or does not belong to organization"
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
    "/blocks/{block_id}/move",
    response_model=BlockResponse,
    summary="Move/reorder block",
    description="Reorder a block within its page",
    responses={
        200: {"description": "Block moved successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request data"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Block not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def move_block(
    block_id: str = Path(..., description="Block ID to move"),
    move_data: BlockMove = ...,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: OceanService = Depends(get_ocean_service)
) -> BlockResponse:
    """
    Reorder a block within its page.

    **Path Parameters:**
    - `block_id`: Unique block identifier

    **Request Body:**
    - `new_position`: New position (0-based)

    **Returns:**
    - Updated block object with new position

    **Notes:**
    - Automatically adjusts positions of affected blocks
    - Moving down: blocks between old and new position shift up
    - Moving up: blocks between new and old position shift down
    - No-op if new_position equals current position

    **Example:**
    - Block at position 2 moved to position 5
    - Blocks 3, 4, 5 shift to positions 2, 3, 4
    - Moved block becomes position 5

    **Errors:**
    - 404: Block not found or doesn't belong to organization
    """
    try:
        moved_block = await service.move_block(
            block_id=block_id,
            new_position=move_data.new_position,
            org_id=current_user["organization_id"]
        )

        if not moved_block:
            raise HTTPException(
                status_code=404,
                detail=f"Block {block_id} not found or does not belong to organization"
            )

        return BlockResponse(**moved_block)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.put(
    "/blocks/{block_id}/convert",
    response_model=BlockResponse,
    summary="Convert block type",
    description="Convert a block to a different type, preserving content intelligently",
    responses={
        200: {"description": "Block converted successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request data"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Block not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def convert_block_type(
    block_id: str = Path(..., description="Block ID to convert"),
    convert_data: BlockConvert = ...,
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: OceanService = Depends(get_ocean_service)
) -> BlockResponse:
    """
    Convert a block to a different type, preserving content intelligently.

    **Path Parameters:**
    - `block_id`: Unique block identifier

    **Request Body:**
    - `new_type`: New block type (text|heading|list|task|link|page_link)

    **Returns:**
    - Updated block object with new type and converted content

    **Conversion Logic:**
    - text/heading/task → preserves text content
    - list → converts to/from newline-separated items
    - link → extracts/adds URL field
    - page_link → extracts/adds linkedPageId field

    **Notes:**
    - Embedding is regenerated if searchable text changes
    - Content structure is intelligently converted
    - Safer than direct update with block_type field

    **Examples:**
    - text → task: Adds checked:false field
    - heading → list: Splits text into single item
    - task → text: Removes checked field, keeps text

    **Errors:**
    - 400: Invalid new_type
    - 404: Block not found or doesn't belong to organization
    """
    try:
        converted_block = await service.convert_block_type(
            block_id=block_id,
            new_type=convert_data.new_type,
            org_id=current_user["organization_id"]
        )

        if not converted_block:
            raise HTTPException(
                status_code=404,
                detail=f"Block {block_id} not found or does not belong to organization"
            )

        return BlockResponse(**converted_block)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@router.get(
    "/blocks/{block_id}/embedding",
    response_model=BlockEmbeddingResponse,
    summary="Get block embedding info",
    description="Get embedding metadata for a block",
    responses={
        200: {"description": "Embedding info retrieved successfully"},
        401: {"model": ErrorResponse, "description": "Not authenticated"},
        404: {"model": ErrorResponse, "description": "Block not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_block_embedding(
    block_id: str = Path(..., description="Block ID to get embedding info for"),
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: OceanService = Depends(get_ocean_service)
) -> BlockEmbeddingResponse:
    """
    Get embedding metadata for a block.

    **Path Parameters:**
    - `block_id`: Unique block identifier

    **Returns:**
    - Embedding information including:
      - has_embedding: Whether block has an embedding
      - vector_id: ZeroDB vector ID (if exists)
      - vector_dimensions: Embedding dimensions (768)
      - model: Embedding model used (BAAI/bge-base-en-v1.5)
      - searchable_text: Preview of text that was embedded

    **Use Cases:**
    - Debug why block doesn't appear in search results
    - Verify embedding was generated
    - Check which text was used for embedding

    **Errors:**
    - 404: Block not found or doesn't belong to organization
    """
    try:
        block = await service.get_block(
            block_id=block_id,
            org_id=current_user["organization_id"]
        )

        if not block:
            raise HTTPException(
                status_code=404,
                detail=f"Block {block_id} not found or does not belong to organization"
            )

        # Extract searchable text preview
        searchable_text = service._extract_searchable_text(block)
        searchable_text_preview = searchable_text[:100] + "..." if len(searchable_text) > 100 else searchable_text

        return BlockEmbeddingResponse(
            block_id=block_id,
            has_embedding=block.get("vector_id") is not None,
            vector_id=block.get("vector_id"),
            vector_dimensions=block.get("vector_dimensions"),
            model="BAAI/bge-base-en-v1.5",
            searchable_text=searchable_text_preview if searchable_text else None
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )
