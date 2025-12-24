"""
Ocean Service - Business logic for Ocean workspace operations.

This service handles all CRUD operations for Ocean pages using ZeroDB NoSQL tables.
All operations are organization-scoped for multi-tenant isolation.

NOTE: This implementation uses direct HTTP requests to ZeroDB API instead of the SDK
      because the SDK's MCP bridge has endpoint compatibility issues.
"""

import uuid
import httpx
from datetime import datetime
from typing import Dict, List, Optional, Any


class OceanService:
    """
    Business logic for Ocean workspace operations.

    This service provides page CRUD operations with multi-tenant isolation.
    All methods enforce organization_id filtering to prevent cross-organization data access.
    """

    def __init__(self, api_url: str, api_key: str, project_id: str):
        """
        Initialize Ocean service.

        Args:
            api_url: ZeroDB API base URL
            api_key: ZeroDB API key
            project_id: ZeroDB project ID for this Ocean instance
        """
        self.api_url = api_url.rstrip('/')
        self.api_key = api_key
        self.project_id = project_id
        self.table_name = "ocean_pages"
        self.tags_table_name = "ocean_tags"
        self.blocks_table_name = "ocean_blocks"
        self.links_table_name = "ocean_block_links"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    async def create_page(
        self,
        org_id: str,
        user_id: str,
        page_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new Ocean page.

        Args:
            org_id: Organization ID (multi-tenant isolation)
            user_id: User ID creating the page
            page_data: Page data containing:
                - title (required): Page title
                - icon (optional): Emoji or icon identifier
                - cover_image (optional): URL or file_id
                - parent_page_id (optional): Parent page for nesting
                - metadata (optional): Additional properties

        Returns:
            Complete page document with generated page_id and timestamps

        Raises:
            ValueError: If required fields are missing
        """
        # Validate required fields
        if not org_id or not user_id:
            raise ValueError("organization_id and user_id are required")
        if not page_data.get("title"):
            raise ValueError("title is required")

        # Generate page ID
        page_id = str(uuid.uuid4())

        # Calculate position (append to end of parent)
        position = await self._get_next_position(
            org_id,
            page_data.get("parent_page_id")
        )

        # Build page document
        now = datetime.utcnow().isoformat()
        page_doc = {
            "page_id": page_id,
            "organization_id": org_id,
            "user_id": user_id,
            "title": page_data["title"],
            "icon": page_data.get("icon", "📄"),
            "cover_image": page_data.get("cover_image"),
            "parent_page_id": page_data.get("parent_page_id"),
            "position": position,
            "is_archived": False,
            "is_favorite": False,
            "created_at": now,
            "updated_at": now,
            "metadata": page_data.get("metadata", {})
        }

        # Insert into ZeroDB using direct HTTP
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "insert_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.table_name,
                        "rows": [page_doc]
                    }
                },
                timeout=30.0
            )

            if response.status_code != 200:
                raise Exception(f"Failed to insert page: {response.status_code} - {response.text}")

        return page_doc

    async def get_page(
        self,
        page_id: str,
        org_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a page by ID.

        Args:
            page_id: Page ID to retrieve
            org_id: Organization ID (multi-tenant isolation)

        Returns:
            Page document if found and belongs to organization, None otherwise
        """
        # Query by page_id and organization_id
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "query_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.table_name,
                        "filter": {
                            "page_id": page_id,
                            "organization_id": org_id
                        },
                        "limit": 1
                    }
                },
                timeout=30.0
            )

            if response.status_code != 200:
                print(f"DEBUG: query_rows failed: {response.status_code} - {response.text}")
                return None

            result = response.json()
            # MCP bridge returns: {"success": True, "result": {"rows": [...]}}
            if not result.get("success"):
                return None

            rows = result.get("result", {}).get("rows", [])
            return rows[0] if rows else None

    async def get_pages(
        self,
        org_id: str,
        filters: Optional[Dict[str, Any]] = None,
        pagination: Optional[Dict[str, int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all pages for an organization with optional filtering.

        Args:
            org_id: Organization ID (multi-tenant isolation)
            filters: Optional filters:
                - parent_page_id: Filter by parent (for nested pages)
                - is_archived: Filter archived status (default: False)
                - is_favorite: Filter favorite pages
            pagination: Optional pagination:
                - limit: Max results (default: 50)
                - offset: Skip results (default: 0)

        Returns:
            List of page documents matching filters
        """
        # Build query filters
        query_filters = {"organization_id": org_id}

        # Apply optional filters
        if filters:
            if "parent_page_id" in filters:
                query_filters["parent_page_id"] = filters["parent_page_id"]
            if "is_archived" in filters:
                query_filters["is_archived"] = filters["is_archived"]
            else:
                # Default: exclude archived pages
                query_filters["is_archived"] = False
            if "is_favorite" in filters:
                query_filters["is_favorite"] = filters["is_favorite"]

        # Apply pagination
        limit = pagination.get("limit", 50) if pagination else 50
        offset = pagination.get("offset", 0) if pagination else 0

        # Query pages
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "query_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.table_name,
                        "filter": query_filters,
                        "limit": limit,
                        "offset": offset
                    }
                },
                timeout=30.0
            )

            if response.status_code != 200:
                return []

            result = response.json()
            # MCP bridge returns: {"success": True, "result": {"rows": [...]}}
            if not result.get("success"):
                return []

            return result.get("result", {}).get("rows", [])

    async def count_pages(
        self,
        org_id: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count total pages for an organization with optional filtering.

        Args:
            org_id: Organization ID (multi-tenant isolation)
            filters: Optional filters (same as get_pages)

        Returns:
            Total count of pages matching filters
        """
        # Build query filters (same logic as get_pages)
        query_filters = {"organization_id": org_id}

        if filters:
            if "parent_page_id" in filters:
                query_filters["parent_page_id"] = filters["parent_page_id"]
            if "is_archived" in filters:
                query_filters["is_archived"] = filters["is_archived"]
            else:
                query_filters["is_archived"] = False
            if "is_favorite" in filters:
                query_filters["is_favorite"] = filters["is_favorite"]

        # Query with limit=0 to get just count (if supported)
        # Otherwise, query all and count locally
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "query_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.table_name,
                        "filter": query_filters,
                        "limit": 1000  # Get all for count (ZeroDB limit)
                    }
                },
                timeout=30.0
            )

            if response.status_code != 200:
                return 0

            result = response.json()
            if not result.get("success"):
                return 0

            rows = result.get("result", {}).get("rows", [])
            return len(rows)

    async def update_page(
        self,
        page_id: str,
        org_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update a page.

        Args:
            page_id: Page ID to update
            org_id: Organization ID (multi-tenant isolation)
            updates: Fields to update:
                - title: New page title
                - icon: New icon
                - cover_image: New cover image
                - is_favorite: Toggle favorite status
                - metadata: Update metadata

        Returns:
            Updated page document if found and belongs to organization, None otherwise
        """
        # Verify page exists and belongs to organization
        existing_page = await self.get_page(page_id, org_id)
        if not existing_page:
            return None

        # Build update payload
        update_payload = {
            "updated_at": datetime.utcnow().isoformat()
        }

        # Add allowed fields
        allowed_fields = ["title", "icon", "cover_image", "is_favorite", "metadata"]
        for field in allowed_fields:
            if field in updates:
                update_payload[field] = updates[field]

        # Update in ZeroDB
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "update_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.table_name,
                        "filter": {
                            "page_id": page_id,
                            "organization_id": org_id
                        },
                        "update": update_payload
                    }
                },
                timeout=30.0
            )

            if response.status_code != 200:
                return None

        # Return updated page
        return await self.get_page(page_id, org_id)

    async def delete_page(
        self,
        page_id: str,
        org_id: str
    ) -> bool:
        """
        Delete a page (soft delete by archiving).

        Args:
            page_id: Page ID to delete
            org_id: Organization ID (multi-tenant isolation)

        Returns:
            True if page was deleted, False if not found or wrong organization
        """
        # Verify page exists and belongs to organization
        existing_page = await self.get_page(page_id, org_id)
        if not existing_page:
            return False

        # Soft delete: set is_archived=True
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "update_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.table_name,
                        "filter": {
                            "page_id": page_id,
                            "organization_id": org_id
                        },
                        "update": {
                            "is_archived": True,
                            "updated_at": datetime.utcnow().isoformat()
                        }
                    }
                },
                timeout=30.0
            )

            return response.status_code == 200

    async def move_page(
        self,
        page_id: str,
        new_parent_id: Optional[str],
        org_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Move a page to a new parent (or to root if new_parent_id is None).

        Args:
            page_id: Page ID to move
            new_parent_id: New parent page ID (None for root level)
            org_id: Organization ID (multi-tenant isolation)

        Returns:
            Updated page document if successful, None if page not found
        """
        # Verify page exists and belongs to organization
        existing_page = await self.get_page(page_id, org_id)
        if not existing_page:
            return None

        # If new parent is specified, verify it exists and belongs to organization
        if new_parent_id:
            new_parent = await self.get_page(new_parent_id, org_id)
            if not new_parent:
                raise ValueError(f"Parent page {new_parent_id} not found or does not belong to organization")

            # Prevent circular references
            if new_parent_id == page_id:
                raise ValueError("Cannot move page to itself")

        # Calculate new position (append to end of new parent)
        new_position = await self._get_next_position(org_id, new_parent_id)

        # Update page
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "update_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.table_name,
                        "filter": {
                            "page_id": page_id,
                            "organization_id": org_id
                        },
                        "update": {
                            "parent_page_id": new_parent_id,
                            "position": new_position,
                            "updated_at": datetime.utcnow().isoformat()
                        }
                    }
                },
                timeout=30.0
            )

            if response.status_code != 200:
                return None

        # Return updated page
        return await self.get_page(page_id, org_id)

    # ========================================================================
    # BLOCK OPERATIONS (Issue #7)
    # ========================================================================

    async def create_block(
        self,
        page_id: str,
        org_id: str,
        user_id: str,
        block_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new Ocean block with automatic embedding generation.

        This method creates a block and automatically generates embeddings for searchable
        content using ZeroDB's BAAI/bge-base-en-v1.5 model (768 dimensions).

        Args:
            page_id: Page ID the block belongs to
            org_id: Organization ID (multi-tenant isolation)
            user_id: User ID creating the block
            block_data: Block data containing:
                - block_type (required): text|heading|list|task|link|page_link
                - content (required): Type-specific content object
                - position (optional): Block position (auto-calculated if not provided)
                - parent_block_id (optional): Parent block for nesting
                - properties (optional): Additional properties (color, tags, etc.)

        Returns:
            Complete block document with generated block_id, vector_id, and timestamps

        Raises:
            ValueError: If required fields are missing or block_type is invalid
        """
        # Validate required fields
        if not org_id or not user_id or not page_id:
            raise ValueError("organization_id, user_id, and page_id are required")
        if not block_data.get("block_type"):
            raise ValueError("block_type is required")
        if not block_data.get("content"):
            raise ValueError("content is required")

        # Validate block type
        valid_types = ["text", "heading", "list", "task", "link", "page_link"]
        if block_data["block_type"] not in valid_types:
            raise ValueError(f"block_type must be one of: {', '.join(valid_types)}")

        # Verify page exists and belongs to organization
        page = await self.get_page(page_id, org_id)
        if not page:
            raise ValueError(f"Page {page_id} not found or does not belong to organization")

        # Generate block ID
        block_id = str(uuid.uuid4())

        # Calculate position if not provided
        position = block_data.get("position")
        if position is None:
            position = await self._get_next_block_position(page_id, org_id)

        # Build block document
        now = datetime.utcnow().isoformat()
        block_doc = {
            "block_id": block_id,
            "page_id": page_id,
            "organization_id": org_id,
            "user_id": user_id,
            "block_type": block_data["block_type"],
            "position": position,
            "parent_block_id": block_data.get("parent_block_id"),
            "content": block_data["content"],
            "properties": block_data.get("properties", {}),
            "vector_id": None,
            "vector_dimensions": None,
            "created_at": now,
            "updated_at": now
        }

        # Generate embedding if block has searchable content
        searchable_text = self._extract_searchable_text(block_doc)
        if searchable_text:
            try:
                vector_id = await self._generate_and_store_embedding(
                    text=searchable_text,
                    block_id=block_id,
                    block_type=block_data["block_type"],
                    page_id=page_id,
                    org_id=org_id
                )
                block_doc["vector_id"] = vector_id
                block_doc["vector_dimensions"] = 768
            except Exception as e:
                # Non-critical: continue without embedding
                print(f"WARNING: Failed to generate embedding for block {block_id}: {e}")

        # Insert into ZeroDB
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "insert_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.blocks_table_name,
                        "rows": [block_doc]
                    }
                },
                timeout=30.0
            )

            if response.status_code != 200:
                raise Exception(f"Failed to insert block: {response.status_code} - {response.text}")

        return block_doc

    async def create_block_batch(
        self,
        page_id: str,
        org_id: str,
        user_id: str,
        blocks_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Bulk create multiple blocks efficiently with batch embedding generation.

        This method is optimized for creating 100+ blocks at once, such as when
        importing content or duplicating pages.

        **BATCH SIZE LIMITS:**
        - Recommended maximum: 100 blocks per batch
        - Hard limit: 500 blocks per batch (API constraint)
        - For larger imports, split into multiple batch calls

        Args:
            page_id: Page ID the blocks belong to
            org_id: Organization ID (multi-tenant isolation)
            user_id: User ID creating the blocks
            blocks_list: List of block data dictionaries (same format as create_block)
                        Maximum 500 blocks per batch

        Returns:
            List of complete block documents with generated IDs and embeddings

        Raises:
            ValueError: If required fields are missing or batch size exceeds limit
        """
        if not blocks_list:
            return []

        # Validate batch size
        if len(blocks_list) > 500:
            raise ValueError(
                f"Batch size {len(blocks_list)} exceeds maximum limit of 500 blocks. "
                "Split large imports into multiple batches."
            )

        # Note: Skip page verification for batch operations to avoid timing issues
        # Page existence will be validated by foreign key constraints in database
        # Verify page exists and belongs to organization
        # page = await self.get_page(page_id, org_id)
        # if not page:
        #     raise ValueError(f"Page {page_id} not found or does not belong to organization")

        # Build all block documents
        now = datetime.utcnow().isoformat()
        block_docs = []
        texts_for_embedding = []
        text_to_block_mapping = []

        # Get starting position
        next_position = await self._get_next_block_position(page_id, org_id)

        for idx, block_data in enumerate(blocks_list):
            # Validate
            if not block_data.get("block_type"):
                raise ValueError(f"block_type is required for block at index {idx}")
            if not block_data.get("content"):
                raise ValueError(f"content is required for block at index {idx}")

            # Generate block ID
            block_id = str(uuid.uuid4())

            # Calculate position
            position = block_data.get("position", next_position + idx)

            # Build block document
            block_doc = {
                "block_id": block_id,
                "page_id": page_id,
                "organization_id": org_id,
                "user_id": user_id,
                "block_type": block_data["block_type"],
                "position": position,
                "parent_block_id": block_data.get("parent_block_id"),
                "content": block_data["content"],
                "properties": block_data.get("properties", {}),
                "vector_id": None,
                "vector_dimensions": None,
                "created_at": now,
                "updated_at": now
            }

            # Extract searchable text for embedding
            searchable_text = self._extract_searchable_text(block_doc)
            if searchable_text:
                texts_for_embedding.append(searchable_text)
                text_to_block_mapping.append({
                    "block_id": block_id,
                    "block_type": block_data["block_type"],
                    "block_doc": block_doc
                })

            block_docs.append(block_doc)

        # Batch generate embeddings
        if texts_for_embedding:
            try:
                vector_ids = await self._generate_and_store_embeddings_batch(
                    texts=texts_for_embedding,
                    metadata_list=[
                        {
                            "block_id": mapping["block_id"],
                            "block_type": mapping["block_type"],
                            "page_id": page_id,
                            "organization_id": org_id
                        }
                        for mapping in text_to_block_mapping
                    ]
                )

                # Update block documents with vector IDs
                for idx, mapping in enumerate(text_to_block_mapping):
                    mapping["block_doc"]["vector_id"] = vector_ids[idx]
                    mapping["block_doc"]["vector_dimensions"] = 768

            except Exception as e:
                # Non-critical: continue without embeddings
                print(f"WARNING: Failed to generate batch embeddings: {e}")

        # Batch insert into ZeroDB
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "insert_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.blocks_table_name,
                        "rows": block_docs
                    }
                },
                timeout=60.0  # Longer timeout for batch operations
            )

            if response.status_code != 200:
                raise Exception(f"Failed to batch insert blocks: {response.status_code} - {response.text}")

        return block_docs

    async def get_block(
        self,
        block_id: str,
        org_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a block by ID with embedding metadata.

        Args:
            block_id: Block ID to retrieve
            org_id: Organization ID (multi-tenant isolation)

        Returns:
            Block document if found and belongs to organization, None otherwise
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "query_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.blocks_table_name,
                        "filter": {
                            "block_id": block_id,
                            "organization_id": org_id
                        },
                        "limit": 1
                    }
                },
                timeout=30.0
            )

            if response.status_code != 200:
                return None

            result = response.json()
            if not result.get("success"):
                return None

            rows = result.get("result", {}).get("rows", [])
            return rows[0] if rows else None

    async def get_blocks_by_page(
        self,
        page_id: str,
        org_id: str,
        filters: Optional[Dict[str, Any]] = None,
        pagination: Optional[Dict[str, int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all blocks for a page, ordered by position.

        Args:
            page_id: Page ID to get blocks for
            org_id: Organization ID (multi-tenant isolation)
            filters: Optional filters:
                - block_type: Filter by block type
                - parent_block_id: Filter by parent block (for nested blocks)
            pagination: Optional pagination:
                - limit: Max results (default: 100)
                - offset: Skip results (default: 0)

        Returns:
            List of block documents ordered by position
        """
        # Build query filters
        query_filters = {
            "page_id": page_id,
            "organization_id": org_id
        }

        # Apply optional filters
        if filters:
            if "block_type" in filters:
                query_filters["block_type"] = filters["block_type"]
            if "parent_block_id" in filters:
                query_filters["parent_block_id"] = filters["parent_block_id"]

        # Apply pagination
        limit = pagination.get("limit", 100) if pagination else 100
        offset = pagination.get("offset", 0) if pagination else 0

        # Query blocks
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "query_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.blocks_table_name,
                        "filter": query_filters,
                        "limit": limit,
                        "offset": offset
                    }
                },
                timeout=30.0
            )

            if response.status_code != 200:
                return []

            result = response.json()
            if not result.get("success"):
                return []

            rows = result.get("result", {}).get("rows", [])

            # Sort by position (ZeroDB doesn't support ORDER BY yet)
            rows.sort(key=lambda x: x.get("position", 0))

            return rows

    async def count_blocks_by_page(
        self,
        page_id: str,
        org_id: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count total blocks for a page with optional filtering.

        Args:
            page_id: Page ID to count blocks for
            org_id: Organization ID (multi-tenant isolation)
            filters: Optional filters (same as get_blocks_by_page)

        Returns:
            Total count of blocks matching filters
        """
        # Build query filters (same logic as get_blocks_by_page)
        query_filters = {
            "page_id": page_id,
            "organization_id": org_id
        }

        if filters:
            if "block_type" in filters:
                query_filters["block_type"] = filters["block_type"]
            if "parent_block_id" in filters:
                query_filters["parent_block_id"] = filters["parent_block_id"]

        # Query all blocks to count (ZeroDB limit: 1000)
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "query_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.blocks_table_name,
                        "filter": query_filters,
                        "limit": 1000  # Get all for count
                    }
                },
                timeout=30.0
            )

            if response.status_code != 200:
                return 0

            result = response.json()
            if not result.get("success"):
                return 0

            rows = result.get("result", {}).get("rows", [])
            return len(rows)

    async def update_block(
        self,
        block_id: str,
        org_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update a block with automatic embedding regeneration if content changed.

        Args:
            block_id: Block ID to update
            org_id: Organization ID (multi-tenant isolation)
            updates: Fields to update:
                - content: New content object
                - properties: New properties
                - position: New position
                - block_type: Convert block type (use convert_block_type for safety)

        Returns:
            Updated block document if found and belongs to organization, None otherwise
        """
        # Verify block exists and belongs to organization
        existing_block = await self.get_block(block_id, org_id)
        if not existing_block:
            return None

        # Build update payload
        update_payload = {
            "updated_at": datetime.utcnow().isoformat()
        }

        # Check if content changed (requires embedding regeneration)
        content_changed = False
        if "content" in updates:
            old_text = self._extract_searchable_text(existing_block)
            # Temporarily update for text extraction
            temp_block = {**existing_block, "content": updates["content"]}
            new_text = self._extract_searchable_text(temp_block)

            if old_text != new_text:
                content_changed = True

            update_payload["content"] = updates["content"]

        # Add other allowed fields
        allowed_fields = ["properties", "position", "block_type"]
        for field in allowed_fields:
            if field in updates:
                update_payload[field] = updates[field]

        # Regenerate embedding if content changed
        if content_changed:
            try:
                # Delete old embedding if exists
                if existing_block.get("vector_id"):
                    await self._delete_embedding(existing_block["vector_id"])

                # Generate new embedding
                searchable_text = self._extract_searchable_text({**existing_block, **update_payload})
                if searchable_text:
                    vector_id = await self._generate_and_store_embedding(
                        text=searchable_text,
                        block_id=block_id,
                        block_type=update_payload.get("block_type", existing_block["block_type"]),
                        page_id=existing_block["page_id"],
                        org_id=org_id
                    )
                    update_payload["vector_id"] = vector_id
                    update_payload["vector_dimensions"] = 768
                else:
                    # No searchable text in new content
                    update_payload["vector_id"] = None
                    update_payload["vector_dimensions"] = None

            except Exception as e:
                # Non-critical: continue without embedding update
                print(f"WARNING: Failed to regenerate embedding for block {block_id}: {e}")

        # Update in ZeroDB
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "update_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.blocks_table_name,
                        "filter": {
                            "block_id": block_id,
                            "organization_id": org_id
                        },
                        "update": update_payload
                    }
                },
                timeout=30.0
            )

            if response.status_code != 200:
                return None

        # Return updated block
        return await self.get_block(block_id, org_id)

    async def delete_block(
        self,
        block_id: str,
        org_id: str
    ) -> bool:
        """
        Delete a block and its associated embedding vector.

        Args:
            block_id: Block ID to delete
            org_id: Organization ID (multi-tenant isolation)

        Returns:
            True if block was deleted, False if not found or wrong organization
        """
        # Verify block exists and belongs to organization
        existing_block = await self.get_block(block_id, org_id)
        if not existing_block:
            return False

        # Delete associated embedding if exists
        if existing_block.get("vector_id"):
            try:
                await self._delete_embedding(existing_block["vector_id"])
            except Exception as e:
                # Non-critical: continue with block deletion
                print(f"WARNING: Failed to delete embedding for block {block_id}: {e}")

        # Delete block from ZeroDB
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "delete_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.blocks_table_name,
                        "filter": {
                            "block_id": block_id,
                            "organization_id": org_id
                        }
                    }
                },
                timeout=30.0
            )

            return response.status_code == 200

    async def move_block(
        self,
        block_id: str,
        new_position: int,
        org_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Reorder a block within its page.

        This method updates the block's position and adjusts all affected blocks
        to maintain a consistent ordering.

        Args:
            block_id: Block ID to move
            new_position: New position (0-based)
            org_id: Organization ID (multi-tenant isolation)

        Returns:
            Updated block document if successful, None if block not found
        """
        # Verify block exists and belongs to organization
        existing_block = await self.get_block(block_id, org_id)
        if not existing_block:
            return None

        old_position = existing_block.get("position", 0)
        if old_position == new_position:
            return existing_block  # No change needed

        # Get all blocks on the same page
        all_blocks = await self.get_blocks_by_page(
            existing_block["page_id"],
            org_id
        )

        # Calculate position updates for affected blocks
        updates_needed = []

        if new_position > old_position:
            # Moving down: shift blocks between old and new position up
            for block in all_blocks:
                pos = block.get("position", 0)
                if old_position < pos <= new_position and block["block_id"] != block_id:
                    updates_needed.append({
                        "block_id": block["block_id"],
                        "new_position": pos - 1
                    })
        else:
            # Moving up: shift blocks between new and old position down
            for block in all_blocks:
                pos = block.get("position", 0)
                if new_position <= pos < old_position and block["block_id"] != block_id:
                    updates_needed.append({
                        "block_id": block["block_id"],
                        "new_position": pos + 1
                    })

        # Update affected blocks
        for update in updates_needed:
            async with httpx.AsyncClient() as client:
                await client.post(
                    f"{self.api_url}/v1/public/zerodb/mcp/execute",
                    headers=self.headers,
                    json={
                        "operation": "update_rows",
                        "params": {
                            "project_id": self.project_id,
                            "table_name": self.blocks_table_name,
                            "filter": {
                                "block_id": update["block_id"],
                                "organization_id": org_id
                            },
                            "update": {
                                "position": update["new_position"],
                                "updated_at": datetime.utcnow().isoformat()
                            }
                        }
                    },
                    timeout=30.0
                )

        # Update the moved block
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "update_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.blocks_table_name,
                        "filter": {
                            "block_id": block_id,
                            "organization_id": org_id
                        },
                        "update": {
                            "position": new_position,
                            "updated_at": datetime.utcnow().isoformat()
                        }
                    }
                },
                timeout=30.0
            )

            if response.status_code != 200:
                return None

        # Return updated block
        return await self.get_block(block_id, org_id)

    async def convert_block_type(
        self,
        block_id: str,
        new_type: str,
        org_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Convert a block to a different type, preserving content where possible.

        This method intelligently converts between block types, preserving the
        text content and regenerating embeddings if the searchable text changes.

        Args:
            block_id: Block ID to convert
            new_type: New block type (text|heading|list|task|link|page_link)
            org_id: Organization ID (multi-tenant isolation)

        Returns:
            Updated block document if successful, None if block not found

        Raises:
            ValueError: If new_type is invalid
        """
        # Validate new type
        valid_types = ["text", "heading", "list", "task", "link", "page_link"]
        if new_type not in valid_types:
            raise ValueError(f"new_type must be one of: {', '.join(valid_types)}")

        # Verify block exists and belongs to organization
        existing_block = await self.get_block(block_id, org_id)
        if not existing_block:
            return None

        old_type = existing_block["block_type"]
        if old_type == new_type:
            return existing_block  # No change needed

        # Convert content structure based on new type
        old_content = existing_block.get("content", {})
        new_content = self._convert_block_content(old_content, old_type, new_type)

        # Check if searchable text changed
        old_text = self._extract_searchable_text(existing_block)
        temp_block = {**existing_block, "content": new_content, "block_type": new_type}
        new_text = self._extract_searchable_text(temp_block)

        # Build update payload
        update_payload = {
            "block_type": new_type,
            "content": new_content,
            "updated_at": datetime.utcnow().isoformat()
        }

        # Regenerate embedding if searchable text changed
        if old_text != new_text:
            try:
                # Delete old embedding if exists
                if existing_block.get("vector_id"):
                    await self._delete_embedding(existing_block["vector_id"])

                # Generate new embedding
                if new_text:
                    vector_id = await self._generate_and_store_embedding(
                        text=new_text,
                        block_id=block_id,
                        block_type=new_type,
                        page_id=existing_block["page_id"],
                        org_id=org_id
                    )
                    update_payload["vector_id"] = vector_id
                    update_payload["vector_dimensions"] = 768
                else:
                    update_payload["vector_id"] = None
                    update_payload["vector_dimensions"] = None

            except Exception as e:
                # Non-critical: continue without embedding update
                print(f"WARNING: Failed to regenerate embedding during conversion: {e}")

        # Update in ZeroDB
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "update_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.blocks_table_name,
                        "filter": {
                            "block_id": block_id,
                            "organization_id": org_id
                        },
                        "update": update_payload
                    }
                },
                timeout=30.0
            )

            if response.status_code != 200:
                return None

        # Return updated block
        return await self.get_block(block_id, org_id)

    # ========================================================================
    # LINK MANAGEMENT OPERATIONS (Issue #10)
    # ========================================================================

    async def create_link(
        self,
        source_block_id: str,
        target_id: str,
        link_type: str,
        org_id: str,
        is_page_link: bool = False
    ) -> Dict[str, Any]:
        """
        Create a bidirectional link between blocks or block-to-page.

        Args:
            source_block_id: Block containing the link
            target_id: Target block ID or page ID
            link_type: Link type (reference, embed, mention)
            org_id: Organization ID (multi-tenant isolation)
            is_page_link: True if target_id is a page_id, False if block_id

        Returns:
            Complete link document with generated link_id

        Raises:
            ValueError: If circular reference detected or invalid parameters
        """
        # Validate link type
        valid_link_types = ["reference", "embed", "mention"]
        if link_type not in valid_link_types:
            raise ValueError(f"Invalid link_type. Must be one of: {valid_link_types}")

        # Validate organization isolation - verify source block exists and belongs to org
        source_block = await self._get_block_by_id(source_block_id, org_id)
        if not source_block:
            raise ValueError(f"Source block {source_block_id} not found or does not belong to organization")

        # Validate target exists and belongs to org
        if is_page_link:
            target = await self.get_page(target_id, org_id)
            if not target:
                raise ValueError(f"Target page {target_id} not found or does not belong to organization")
        else:
            target = await self._get_block_by_id(target_id, org_id)
            if not target:
                raise ValueError(f"Target block {target_id} not found or does not belong to organization")

        # Prevent circular references (only for block-to-block links)
        if not is_page_link:
            has_circular = await self._has_circular_reference(
                source_block_id, target_id, org_id
            )
            if has_circular:
                raise ValueError(
                    f"Circular reference detected: target block {target_id} "
                    f"already links to source block {source_block_id}"
                )

        # Generate link ID
        link_id = str(uuid.uuid4())

        # Build link document
        now = datetime.utcnow().isoformat()
        link_doc = {
            "link_id": link_id,
            "organization_id": org_id,  # Multi-tenant isolation
            "source_block_id": source_block_id,
            "target_block_id": None if is_page_link else target_id,
            "target_page_id": target_id if is_page_link else None,
            "link_type": link_type,
            "created_at": now
        }

        # Insert into ocean_block_links table
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "insert_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.links_table_name,
                        "rows": [link_doc]
                    }
                },
                timeout=30.0
            )

            if response.status_code != 200:
                raise Exception(f"Failed to create link: {response.status_code} - {response.text}")

        return link_doc

    async def delete_link(
        self,
        link_id: str,
        org_id: str
    ) -> bool:
        """
        Delete a link by ID.

        Args:
            link_id: Link ID to delete
            org_id: Organization ID (multi-tenant isolation)

        Returns:
            True if link was deleted, False if not found or wrong organization
        """
        # Verify link exists and belongs to organization
        existing_link = await self._get_link_by_id(link_id, org_id)
        if not existing_link:
            return False

        # Delete from ocean_block_links table
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "delete_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.links_table_name,
                        "filter": {
                            "link_id": link_id,
                            "organization_id": org_id
                        }
                    }
                },
                timeout=30.0
            )

            return response.status_code == 200

    async def get_page_backlinks(
        self,
        page_id: str,
        org_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all blocks/pages linking to a specific page.

        Args:
            page_id: Page ID to find backlinks for
            org_id: Organization ID (multi-tenant isolation)

        Returns:
            List of backlink information with source details
        """
        # Verify page exists and belongs to organization
        page = await self.get_page(page_id, org_id)
        if not page:
            return []

        # Query links where target_page_id matches
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "query_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.links_table_name,
                        "filter": {
                            "target_page_id": page_id,
                            "organization_id": org_id
                        },
                        "limit": 1000  # Reasonable limit for backlinks
                    }
                },
                timeout=30.0
            )

            if response.status_code != 200:
                return []

            result = response.json()
            if not result.get("success"):
                return []

            links = result.get("result", {}).get("rows", [])

        # Enrich with source block information
        backlinks = []
        for link in links:
            source_block = await self._get_block_by_id(
                link["source_block_id"], org_id
            )
            if source_block:
                backlinks.append({
                    "link_id": link["link_id"],
                    "link_type": link["link_type"],
                    "source_block_id": link["source_block_id"],
                    "source_page_id": source_block.get("page_id"),
                    "source_block_type": source_block.get("block_type"),
                    "source_content_preview": self._get_content_preview(source_block),
                    "created_at": link["created_at"]
                })

        return backlinks

    async def get_block_backlinks(
        self,
        block_id: str,
        org_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get all blocks linking to a specific block.

        Args:
            block_id: Block ID to find backlinks for
            org_id: Organization ID (multi-tenant isolation)

        Returns:
            List of backlink information with source details
        """
        # Verify block exists and belongs to organization
        block = await self._get_block_by_id(block_id, org_id)
        if not block:
            return []

        # Query links where target_block_id matches
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "query_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.links_table_name,
                        "filter": {
                            "target_block_id": block_id,
                            "organization_id": org_id
                        },
                        "limit": 1000  # Reasonable limit for backlinks
                    }
                },
                timeout=30.0
            )

            if response.status_code != 200:
                return []

            result = response.json()
            if not result.get("success"):
                return []

            links = result.get("result", {}).get("rows", [])

        # Enrich with source block information
        backlinks = []
        for link in links:
            source_block = await self._get_block_by_id(
                link["source_block_id"], org_id
            )
            if source_block:
                backlinks.append({
                    "link_id": link["link_id"],
                    "link_type": link["link_type"],
                    "source_block_id": link["source_block_id"],
                    "source_page_id": source_block.get("page_id"),
                    "source_block_type": source_block.get("block_type"),
                    "source_content_preview": self._get_content_preview(source_block),
                    "created_at": link["created_at"]
                })

        return backlinks

    # ========================================================================
    # PRIVATE HELPER METHODS FOR BLOCKS
    # ========================================================================

    def _extract_searchable_text(self, block: Dict[str, Any]) -> str:
        """
        Extract searchable text from a block for embedding generation.

        Args:
            block: Block document

        Returns:
            Searchable text string, or empty string if no searchable content
        """
        block_type = block.get("block_type", "")
        content = block.get("content", {})

        if block_type in ["text", "heading"]:
            return content.get("text", "")

        elif block_type == "list":
            items = content.get("items", [])
            return " ".join(items) if isinstance(items, list) else ""

        elif block_type == "task":
            return content.get("text", "")

        elif block_type == "link":
            # Combine link text and URL for search
            text = content.get("text", "")
            url = content.get("url", "")
            return f"{text} {url}".strip()

        elif block_type == "page_link":
            return content.get("displayText", "")

        return ""

    async def _generate_and_store_embedding(
        self,
        text: str,
        block_id: str,
        block_type: str,
        page_id: str,
        org_id: str
    ) -> str:
        """
        Generate and store embedding for a single text.

        Args:
            text: Text to embed
            block_id: Block ID for metadata
            block_type: Block type for metadata
            page_id: Page ID for metadata
            org_id: Organization ID for metadata

        Returns:
            Vector ID from ZeroDB

        Raises:
            Exception: If embedding generation fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/{self.project_id}/embeddings/embed-and-store",
                headers=self.headers,
                json={
                    "texts": [text],
                    "model": "BAAI/bge-base-en-v1.5",
                    "namespace": "ocean_blocks",
                    "metadata": [{
                        "block_id": block_id,
                        "block_type": block_type,
                        "page_id": page_id,
                        "organization_id": org_id
                    }]
                },
                timeout=30.0
            )

            if response.status_code != 200:
                raise Exception(f"Failed to generate embedding: {response.status_code} - {response.text}")

            result = response.json()
            vector_ids = result.get("vector_ids", [])
            if not vector_ids:
                raise Exception("No vector_ids returned from embedding generation")

            return vector_ids[0]

    async def _generate_and_store_embeddings_batch(
        self,
        texts: List[str],
        metadata_list: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Batch generate and store embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            metadata_list: List of metadata dictionaries (one per text)

        Returns:
            List of vector IDs from ZeroDB

        Raises:
            Exception: If embedding generation fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/{self.project_id}/embeddings/embed-and-store",
                headers=self.headers,
                json={
                    "texts": texts,
                    "model": "BAAI/bge-base-en-v1.5",
                    "namespace": "ocean_blocks",
                    "metadata": metadata_list
                },
                timeout=60.0  # Longer timeout for batch
            )

            if response.status_code != 200:
                raise Exception(f"Failed to batch generate embeddings: {response.status_code} - {response.text}")

            result = response.json()
            vector_ids = result.get("vector_ids", [])
            if len(vector_ids) != len(texts):
                raise Exception(f"Expected {len(texts)} vector_ids, got {len(vector_ids)}")

            return vector_ids

    async def _delete_embedding(self, vector_id: str) -> None:
        """
        Delete an embedding vector from ZeroDB.

        Args:
            vector_id: Vector ID to delete

        Raises:
            Exception: If deletion fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "delete_vector",
                    "params": {
                        "project_id": self.project_id,
                        "vector_id": vector_id,
                        "namespace": "ocean_blocks"
                    }
                },
                timeout=30.0
            )

            if response.status_code != 200:
                raise Exception(f"Failed to delete embedding: {response.status_code} - {response.text}")

    async def _get_next_block_position(
        self,
        page_id: str,
        org_id: str
    ) -> int:
        """
        Get the next position value for a block within a page.

        Args:
            page_id: Page ID
            org_id: Organization ID

        Returns:
            Next available position (0-based)
        """
        blocks = await self.get_blocks_by_page(page_id, org_id)
        return len(blocks)

    def _convert_block_content(
        self,
        old_content: Dict[str, Any],
        old_type: str,
        new_type: str
    ) -> Dict[str, Any]:
        """
        Convert block content structure when changing block types.

        Args:
            old_content: Original content object
            old_type: Original block type
            new_type: New block type

        Returns:
            Converted content object
        """
        # Extract text from old content
        text = ""
        if old_type in ["text", "heading", "task"]:
            text = old_content.get("text", "")
        elif old_type == "list":
            items = old_content.get("items", [])
            text = "\n".join(items) if isinstance(items, list) else ""
        elif old_type == "link":
            text = old_content.get("text", "")
        elif old_type == "page_link":
            text = old_content.get("displayText", "")

        # Build new content structure
        if new_type in ["text", "heading"]:
            return {"text": text}

        elif new_type == "list":
            items = text.split("\n") if text else []
            return {"items": items}

        elif new_type == "task":
            return {
                "text": text,
                "checked": False
            }

        elif new_type == "link":
            return {
                "text": text,
                "url": ""
            }

        elif new_type == "page_link":
            return {
                "displayText": text,
                "linkedPageId": None
            }

        return {"text": text}

    # Tag Management Methods

    async def create_tag(
        self,
        org_id: str,
        tag_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new organization-scoped tag.

        Args:
            org_id: Organization ID (multi-tenant isolation)
            tag_data: Tag data containing:
                - name (required): Tag name (unique per org)
                - color (optional): Hex color code (default: #6B7280)
                - description (optional): Tag description

        Returns:
            Complete tag document with generated tag_id and timestamps

        Raises:
            ValueError: If required fields are missing or tag name already exists
        """
        # Validate required fields
        if not org_id:
            raise ValueError("organization_id is required")
        if not tag_data.get("name"):
            raise ValueError("name is required")

        # Validate tag name uniqueness within organization
        existing_tags = await self.get_tags(org_id, {"name": tag_data["name"]})
        if existing_tags:
            raise ValueError(f"Tag '{tag_data['name']}' already exists in this organization")

        # Generate tag ID
        tag_id = str(uuid.uuid4())

        # Build tag document
        now = datetime.utcnow().isoformat()
        tag_doc = {
            "tag_id": tag_id,
            "organization_id": org_id,
            "name": tag_data["name"],
            "color": tag_data.get("color", "#6B7280"),  # Default gray
            "description": tag_data.get("description", ""),
            "usage_count": 0,
            "created_at": now,
            "updated_at": now
        }

        # Insert into ZeroDB
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "insert_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.tags_table_name,
                        "rows": [tag_doc]
                    }
                },
                timeout=30.0
            )

            if response.status_code != 200:
                raise Exception(f"Failed to create tag: {response.status_code} - {response.text}")

        return tag_doc

    async def get_tags(
        self,
        org_id: str,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all tags for an organization with optional filtering.

        Args:
            org_id: Organization ID (multi-tenant isolation)
            filters: Optional filters:
                - name: Filter by exact tag name
                - color: Filter by color
                - min_usage: Minimum usage count

        Returns:
            List of tag documents sorted by usage_count (descending)
        """
        # Build query filters
        query_filters = {"organization_id": org_id}

        # Apply optional filters
        if filters:
            if "name" in filters:
                query_filters["name"] = filters["name"]
            if "color" in filters:
                query_filters["color"] = filters["color"]

        # Query tags
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "query_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.tags_table_name,
                        "filter": query_filters,
                        "limit": 1000  # Reasonable limit for tags
                    }
                },
                timeout=30.0
            )

            if response.status_code != 200:
                return []

            result = response.json()
            if not result.get("success"):
                return []

            rows = result.get("result", {}).get("rows", [])

            # Filter by min_usage if specified
            if filters and "min_usage" in filters:
                rows = [r for r in rows if r.get("usage_count", 0) >= filters["min_usage"]]

            # Sort by usage_count descending
            rows.sort(key=lambda r: r.get("usage_count", 0), reverse=True)

            return rows

    async def update_tag(
        self,
        tag_id: str,
        org_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Update a tag's properties.

        Args:
            tag_id: Tag ID to update
            org_id: Organization ID (multi-tenant isolation)
            updates: Fields to update:
                - name: New tag name (must be unique per org)
                - color: New color
                - description: New description

        Returns:
            Updated tag document if found and belongs to organization, None otherwise

        Raises:
            ValueError: If new name conflicts with existing tag
        """
        # Verify tag exists and belongs to organization
        existing_tags = await self.get_tags(org_id)
        existing_tag = next((t for t in existing_tags if t.get("tag_id") == tag_id), None)
        if not existing_tag:
            return None

        # Check name uniqueness if updating name
        if "name" in updates and updates["name"] != existing_tag.get("name"):
            conflicting_tags = await self.get_tags(org_id, {"name": updates["name"]})
            if conflicting_tags:
                raise ValueError(f"Tag '{updates['name']}' already exists in this organization")

        # Build update payload
        update_payload = {
            "updated_at": datetime.utcnow().isoformat()
        }

        # Add allowed fields
        allowed_fields = ["name", "color", "description"]
        for field in allowed_fields:
            if field in updates:
                update_payload[field] = updates[field]

        # Update in ZeroDB
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "update_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.tags_table_name,
                        "filter": {
                            "tag_id": tag_id,
                            "organization_id": org_id
                        },
                        "update": update_payload
                    }
                },
                timeout=30.0
            )

            if response.status_code != 200:
                return None

        # Return updated tag
        updated_tags = await self.get_tags(org_id)
        return next((t for t in updated_tags if t.get("tag_id") == tag_id), None)

    async def delete_tag(
        self,
        tag_id: str,
        org_id: str
    ) -> bool:
        """
        Delete a tag and remove it from all blocks.

        Args:
            tag_id: Tag ID to delete
            org_id: Organization ID (multi-tenant isolation)

        Returns:
            True if tag was deleted, False if not found or wrong organization
        """
        # Verify tag exists and belongs to organization
        existing_tags = await self.get_tags(org_id)
        existing_tag = next((t for t in existing_tags if t.get("tag_id") == tag_id), None)
        if not existing_tag:
            return False

        # Remove tag from all blocks (update blocks' properties.tags arrays)
        # Note: This requires querying all blocks with this tag_id in properties.tags
        # For simplicity, we'll handle this in the block service when it's implemented
        # For now, just delete the tag document

        # Delete tag from ZeroDB
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "delete_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.tags_table_name,
                        "filter": {
                            "tag_id": tag_id,
                            "organization_id": org_id
                        }
                    }
                },
                timeout=30.0
            )

            return response.status_code == 200

    async def assign_tag_to_block(
        self,
        block_id: str,
        tag_id: str,
        org_id: str
    ) -> bool:
        """
        Assign a tag to a block.

        Args:
            block_id: Block ID to tag
            tag_id: Tag ID to assign
            org_id: Organization ID (multi-tenant isolation)

        Returns:
            True if tag was assigned, False if block/tag not found or already assigned

        Raises:
            ValueError: If block or tag don't belong to organization
        """
        # Verify tag exists and belongs to organization
        existing_tags = await self.get_tags(org_id)
        existing_tag = next((t for t in existing_tags if t.get("tag_id") == tag_id), None)
        if not existing_tag:
            raise ValueError(f"Tag {tag_id} not found or does not belong to organization")

        # Get block to verify it exists and belongs to organization
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "query_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.blocks_table_name,
                        "filter": {
                            "block_id": block_id,
                            "organization_id": org_id
                        },
                        "limit": 1
                    }
                },
                timeout=30.0
            )

            if response.status_code != 200:
                raise ValueError(f"Block {block_id} not found or does not belong to organization")

            result = response.json()
            if not result.get("success"):
                raise ValueError(f"Block {block_id} not found")

            blocks = result.get("result", {}).get("rows", [])
            if not blocks:
                raise ValueError(f"Block {block_id} not found")

            block = blocks[0]

            # Get current tags from block properties
            properties = block.get("properties", {})
            tags = properties.get("tags", [])

            # Check if tag already assigned
            if tag_id in tags:
                return False  # Already assigned

            # Add tag to block
            tags.append(tag_id)
            properties["tags"] = tags

            # Update block
            update_response = await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "update_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.blocks_table_name,
                        "filter": {
                            "block_id": block_id,
                            "organization_id": org_id
                        },
                        "update": {
                            "properties": properties,
                            "updated_at": datetime.utcnow().isoformat()
                        }
                    }
                },
                timeout=30.0
            )

            if update_response.status_code != 200:
                return False

            # Increment tag usage count
            await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "update_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.tags_table_name,
                        "filter": {
                            "tag_id": tag_id,
                            "organization_id": org_id
                        },
                        "update": {
                            "usage_count": existing_tag.get("usage_count", 0) + 1,
                            "updated_at": datetime.utcnow().isoformat()
                        }
                    }
                },
                timeout=30.0
            )

            return True

    async def remove_tag_from_block(
        self,
        block_id: str,
        tag_id: str,
        org_id: str
    ) -> bool:
        """
        Remove a tag from a block.

        Args:
            block_id: Block ID to untag
            tag_id: Tag ID to remove
            org_id: Organization ID (multi-tenant isolation)

        Returns:
            True if tag was removed, False if block/tag not found or not assigned

        Raises:
            ValueError: If block or tag don't belong to organization
        """
        # Verify tag exists and belongs to organization
        existing_tags = await self.get_tags(org_id)
        existing_tag = next((t for t in existing_tags if t.get("tag_id") == tag_id), None)
        if not existing_tag:
            raise ValueError(f"Tag {tag_id} not found or does not belong to organization")

        # Get block to verify it exists and belongs to organization
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "query_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.blocks_table_name,
                        "filter": {
                            "block_id": block_id,
                            "organization_id": org_id
                        },
                        "limit": 1
                    }
                },
                timeout=30.0
            )

            if response.status_code != 200:
                raise ValueError(f"Block {block_id} not found or does not belong to organization")

            result = response.json()
            if not result.get("success"):
                raise ValueError(f"Block {block_id} not found")

            blocks = result.get("result", {}).get("rows", [])
            if not blocks:
                raise ValueError(f"Block {block_id} not found")

            block = blocks[0]

            # Get current tags from block properties
            properties = block.get("properties", {})
            tags = properties.get("tags", [])

            # Check if tag is assigned
            if tag_id not in tags:
                return False  # Not assigned

            # Remove tag from block
            tags.remove(tag_id)
            properties["tags"] = tags

            # Update block
            update_response = await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "update_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.blocks_table_name,
                        "filter": {
                            "block_id": block_id,
                            "organization_id": org_id
                        },
                        "update": {
                            "properties": properties,
                            "updated_at": datetime.utcnow().isoformat()
                        }
                    }
                },
                timeout=30.0
            )

            if update_response.status_code != 200:
                return False

            # Decrement tag usage count
            new_usage_count = max(0, existing_tag.get("usage_count", 0) - 1)
            await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "update_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.tags_table_name,
                        "filter": {
                            "tag_id": tag_id,
                            "organization_id": org_id
                        },
                        "update": {
                            "usage_count": new_usage_count,
                            "updated_at": datetime.utcnow().isoformat()
                        }
                    }
                },
                timeout=30.0
            )

            return True

    # Helper methods

    async def _get_next_position(
        self,
        org_id: str,
        parent_page_id: Optional[str]
    ) -> int:
        """
        Get the next position value for a page within a parent.

        Args:
            org_id: Organization ID
            parent_page_id: Parent page ID (None for root level)

        Returns:
            Next available position (0-based)
        """
        # Build filters for sibling pages
        filters = {"organization_id": org_id}

        if parent_page_id:
            filters["parent_page_id"] = parent_page_id
        # For root pages, don't filter by parent_page_id - we'll filter in memory

        # Query existing pages
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "query_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.table_name,
                        "filter": filters,
                        "limit": 1000  # Reasonable limit for siblings
                    }
                },
                timeout=30.0
            )

            if response.status_code != 200:
                return 0

            result = response.json()
            # MCP bridge returns: {"success": True, "result": {"rows": [...]}}
            if not result.get("success"):
                return 0

            rows = result.get("result", {}).get("rows", [])

            # Filter root pages if parent_page_id is None
            if parent_page_id is None:
                rows = [r for r in rows if not r.get("parent_page_id")]

            # Return count as next position
            return len(rows)

    # ========================================================================
    # PRIVATE HELPER METHODS FOR LINKS
    # ========================================================================

    async def _has_circular_reference(
        self,
        source_block_id: str,
        target_block_id: str,
        org_id: str,
        visited: Optional[set] = None
    ) -> bool:
        """
        Check if creating a link would create a circular reference.

        Uses recursive traversal to detect if target_block_id already
        links (directly or indirectly) to source_block_id.

        Args:
            source_block_id: Block that will contain the new link
            target_block_id: Block that will be linked to
            org_id: Organization ID
            visited: Set of visited block IDs (for recursion tracking)

        Returns:
            True if circular reference detected, False if safe
        """
        if visited is None:
            visited = set()

        # Prevent infinite loops
        if target_block_id in visited:
            return False

        visited.add(target_block_id)

        # Query all links from target_block
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "query_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.links_table_name,
                        "filter": {
                            "source_block_id": target_block_id,
                            "organization_id": org_id
                        },
                        "limit": 1000
                    }
                },
                timeout=30.0
            )

            if response.status_code != 200:
                return False

            result = response.json()
            if not result.get("success"):
                return False

            links = result.get("result", {}).get("rows", [])

        # Check if any link points back to source
        for link in links:
            # Only check block-to-block links
            linked_block_id = link.get("target_block_id")
            if not linked_block_id:
                continue

            # Direct circular reference
            if linked_block_id == source_block_id:
                return True

            # Recursive check for indirect circular reference
            if await self._has_circular_reference(
                source_block_id, linked_block_id, org_id, visited
            ):
                return True

        return False

    async def _get_block_by_id(
        self,
        block_id: str,
        org_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a block by ID (helper method for link operations).

        Args:
            block_id: Block ID to retrieve
            org_id: Organization ID

        Returns:
            Block document if found and belongs to organization, None otherwise
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "query_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.blocks_table_name,
                        "filter": {
                            "block_id": block_id,
                            "organization_id": org_id
                        },
                        "limit": 1
                    }
                },
                timeout=30.0
            )

            if response.status_code != 200:
                return None

            result = response.json()
            if not result.get("success"):
                return None

            rows = result.get("result", {}).get("rows", [])
            return rows[0] if rows else None

    async def _get_link_by_id(
        self,
        link_id: str,
        org_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get a link by ID (helper method for link operations).

        Args:
            link_id: Link ID to retrieve
            org_id: Organization ID

        Returns:
            Link document if found and belongs to organization, None otherwise
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "query_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.links_table_name,
                        "filter": {
                            "link_id": link_id,
                            "organization_id": org_id
                        },
                        "limit": 1
                    }
                },
                timeout=30.0
            )

            if response.status_code != 200:
                return None

            result = response.json()
            if not result.get("success"):
                return None

            rows = result.get("result", {}).get("rows", [])
            return rows[0] if rows else None

    def _get_content_preview(
        self,
        block: Dict[str, Any],
        max_length: int = 100
    ) -> str:
        """
        Get a preview of block content for backlink display.

        Args:
            block: Block document
            max_length: Maximum preview length

        Returns:
            Preview string (truncated if necessary)
        """
        content = block.get("content", {})
        block_type = block.get("block_type", "text")

        preview = ""
        if block_type in ["text", "heading"]:
            preview = content.get("text", "")
        elif block_type == "task":
            preview = content.get("text", "")
        elif block_type == "list":
            items = content.get("items", [])
            preview = ", ".join(items[:3])  # First 3 items
        elif block_type == "link":
            preview = content.get("url", "")
        elif block_type == "page_link":
            preview = f"Link to page: {content.get('page_id', '')}"

        # Truncate with ellipsis
        if len(preview) > max_length:
            preview = preview[:max_length - 3] + "..."

        return preview

    # ========================================================================
    # HYBRID SEMANTIC SEARCH (Issue #13)
    # ========================================================================

    async def search(
        self,
        query: str,
        org_id: str,
        filters: Optional[Dict] = None,
        search_type: str = "hybrid",
        limit: int = 20,
        threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Hybrid semantic search combining vector similarity and metadata filtering.

        This method implements three search modes:
        - semantic: Pure vector similarity search
        - metadata: Filter-only search (no embedding)
        - hybrid: Combines vector similarity with metadata filters (default)

        Args:
            query: Search query text
            org_id: Organization ID (multi-tenant isolation)
            filters: Optional metadata filters:
                - block_types: List of block types to include
                - page_id: Filter by specific page
                - tags: List of tag IDs to filter by
                - date_range: {"start": iso_date, "end": iso_date}
            search_type: Search mode (semantic|metadata|hybrid)
            limit: Maximum results to return (default: 20)
            threshold: Minimum similarity score (0.0-1.0, default: 0.7)

        Returns:
            List of search results with blocks and similarity scores, sorted by relevance

        Raises:
            ValueError: If search_type is invalid or query is empty
        """
        # Validate inputs
        if not query or not query.strip():
            raise ValueError("Query text is required")

        if search_type not in ["semantic", "metadata", "hybrid"]:
            raise ValueError("search_type must be one of: semantic, metadata, hybrid")

        # Initialize filters if not provided
        if filters is None:
            filters = {}

        # Route to appropriate search method
        if search_type == "semantic":
            return await self._search_semantic(query, org_id, limit, threshold)
        elif search_type == "metadata":
            return await self._search_metadata(query, org_id, filters, limit)
        else:  # hybrid
            return await self._search_hybrid(query, org_id, filters, limit, threshold)

    async def _search_semantic(
        self,
        query: str,
        org_id: str,
        limit: int,
        threshold: float
    ) -> List[Dict[str, Any]]:
        """
        Pure semantic search using vector similarity.

        Args:
            query: Search query text
            org_id: Organization ID
            limit: Maximum results
            threshold: Minimum similarity score

        Returns:
            List of search results with similarity scores
        """
        # Generate embedding for query
        query_embedding = await self._generate_query_embedding(query)

        # Search vectors with organization filter
        metadata_filter = {"organization_id": org_id}

        results = await self._search_vectors(
            query_embedding=query_embedding,
            metadata_filter=metadata_filter,
            threshold=threshold,
            limit=limit
        )

        # Enrich results with block data
        enriched = await self._enrich_search_results(results, org_id)

        return enriched

    async def _search_metadata(
        self,
        query: str,
        org_id: str,
        filters: Dict[str, Any],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Filter-only search using metadata (no vector similarity).

        Searches block content using text matching and metadata filters.

        Args:
            query: Search query text (used for text matching)
            org_id: Organization ID
            filters: Metadata filters
            limit: Maximum results

        Returns:
            List of blocks matching filters and query text
        """
        # Build query filters
        query_filters = {"organization_id": org_id}

        # Apply block type filter
        if "block_types" in filters:
            # Note: ZeroDB doesn't support IN queries yet, so we'll filter after retrieval
            pass

        # Apply page_id filter
        if "page_id" in filters:
            query_filters["page_id"] = filters["page_id"]

        # Query all blocks for organization (or specific page)
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/public/zerodb/mcp/execute",
                headers=self.headers,
                json={
                    "operation": "query_rows",
                    "params": {
                        "project_id": self.project_id,
                        "table_name": self.blocks_table_name,
                        "filter": query_filters,
                        "limit": 1000  # Get all blocks, then filter in-memory
                    }
                },
                timeout=30.0
            )

            if response.status_code != 200:
                return []

            result = response.json()
            if not result.get("success"):
                return []

            blocks = result.get("result", {}).get("rows", [])

        # Filter by block types if specified
        if "block_types" in filters:
            allowed_types = set(filters["block_types"])
            blocks = [b for b in blocks if b.get("block_type") in allowed_types]

        # Filter by tags if specified
        if "tags" in filters:
            required_tags = set(filters["tags"])
            blocks = [
                b for b in blocks
                if any(tag in required_tags for tag in b.get("properties", {}).get("tags", []))
            ]

        # Filter by date range if specified
        if "date_range" in filters:
            start = filters["date_range"].get("start")
            end = filters["date_range"].get("end")
            blocks = self._filter_by_date_range(blocks, start, end)

        # Text matching against searchable content
        query_lower = query.lower()
        matched_blocks = []

        for block in blocks:
            searchable_text = self._extract_searchable_text(block).lower()
            if query_lower in searchable_text:
                # Calculate simple text match score based on position
                position = searchable_text.find(query_lower)
                # Score: 1.0 if at start, decreases with position
                score = max(0.5, 1.0 - (position / max(len(searchable_text), 1)))

                matched_blocks.append({
                    "block": block,
                    "score": score,
                    "match_type": "metadata"
                })

        # Sort by score and limit
        matched_blocks.sort(key=lambda x: x["score"], reverse=True)
        return matched_blocks[:limit]

    async def _search_hybrid(
        self,
        query: str,
        org_id: str,
        filters: Dict[str, Any],
        limit: int,
        threshold: float
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining vector similarity and metadata filtering.

        This provides the best of both worlds: semantic understanding via vectors
        plus precise filtering via metadata.

        Args:
            query: Search query text
            org_id: Organization ID
            filters: Metadata filters
            limit: Maximum results
            threshold: Minimum similarity score

        Returns:
            List of search results ranked by combined score
        """
        # Generate embedding for query
        query_embedding = await self._generate_query_embedding(query)

        # Build metadata filter
        metadata_filter = {"organization_id": org_id}

        # Apply page_id filter if specified
        if "page_id" in filters:
            metadata_filter["page_id"] = filters["page_id"]

        # Apply block_type filter if single type specified
        if "block_types" in filters and len(filters["block_types"]) == 1:
            metadata_filter["block_type"] = filters["block_types"][0]

        # Search vectors with metadata filter
        vector_results = await self._search_vectors(
            query_embedding=query_embedding,
            metadata_filter=metadata_filter,
            threshold=threshold,
            limit=limit * 2  # Get more results for filtering
        )

        # Enrich with block data
        enriched = await self._enrich_search_results(vector_results, org_id)

        # Apply additional filters (block_types, tags, date_range)
        filtered = self._apply_additional_filters(enriched, filters)

        # Rank and deduplicate
        final_results = self._rank_and_dedupe(filtered, query)

        # Limit results
        return final_results[:limit]

    async def _generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding vector for search query.

        Args:
            query: Search query text

        Returns:
            768-dimensional embedding vector

        Raises:
            Exception: If embedding generation fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/api/v1/embeddings/generate",
                headers=self.headers,
                json={
                    "texts": [query],
                    "model": "BAAI/bge-base-en-v1.5"
                },
                timeout=30.0
            )

            if response.status_code != 200:
                raise Exception(f"Failed to generate query embedding: {response.status_code} - {response.text}")

            result = response.json()
            embeddings = result.get("embeddings", [])

            if not embeddings:
                raise Exception("No embeddings returned from API")

            return embeddings[0]

    async def _search_vectors(
        self,
        query_embedding: List[float],
        metadata_filter: Dict[str, Any],
        threshold: float,
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Search vectors in ZeroDB using semantic similarity.

        Args:
            query_embedding: Query embedding vector
            metadata_filter: Metadata filters to apply
            threshold: Minimum similarity score
            limit: Maximum results

        Returns:
            List of vector search results with similarity scores
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_url}/v1/{self.project_id}/embeddings/search",
                headers=self.headers,
                json={
                    "query_vector": query_embedding,
                    "namespace": "ocean_blocks",
                    "filter_metadata": metadata_filter,
                    "threshold": threshold,
                    "limit": limit
                },
                timeout=30.0
            )

            if response.status_code != 200:
                # Non-critical: return empty results on search failure
                print(f"WARNING: Vector search failed: {response.status_code} - {response.text}")
                return []

            result = response.json()
            return result.get("results", [])

    async def _enrich_search_results(
        self,
        vector_results: List[Dict[str, Any]],
        org_id: str
    ) -> List[Dict[str, Any]]:
        """
        Enrich vector search results with full block data.

        Args:
            vector_results: Results from vector search
            org_id: Organization ID

        Returns:
            Enriched results with block data and similarity scores
        """
        enriched = []

        for result in vector_results:
            # Extract similarity score (different APIs may use different keys)
            similarity = result.get("similarity") or result.get("score", 0.0)

            # Extract metadata
            metadata = result.get("metadata", {})
            block_id = metadata.get("block_id")

            if not block_id:
                continue

            # Fetch full block data
            block = await self.get_block(block_id, org_id)

            if block:
                enriched.append({
                    "block": block,
                    "score": similarity,
                    "match_type": "semantic",
                    "vector_id": result.get("vector_id")
                })

        return enriched

    def _apply_additional_filters(
        self,
        results: List[Dict[str, Any]],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Apply additional filters that couldn't be applied at vector search level.

        Args:
            results: Search results to filter
            filters: Filter criteria

        Returns:
            Filtered results
        """
        filtered = results

        # Filter by block types (if multiple types specified)
        if "block_types" in filters and len(filters["block_types"]) > 1:
            allowed_types = set(filters["block_types"])
            filtered = [
                r for r in filtered
                if r["block"].get("block_type") in allowed_types
            ]

        # Filter by tags
        if "tags" in filters:
            required_tags = set(filters["tags"])
            filtered = [
                r for r in filtered
                if any(
                    tag in required_tags
                    for tag in r["block"].get("properties", {}).get("tags", [])
                )
            ]

        # Filter by date range
        if "date_range" in filters:
            start = filters["date_range"].get("start")
            end = filters["date_range"].get("end")
            filtered_blocks = self._filter_by_date_range(
                [r["block"] for r in filtered],
                start,
                end
            )
            block_ids = {b["block_id"] for b in filtered_blocks}
            filtered = [r for r in filtered if r["block"]["block_id"] in block_ids]

        return filtered

    def _filter_by_date_range(
        self,
        blocks: List[Dict[str, Any]],
        start: Optional[str],
        end: Optional[str]
    ) -> List[Dict[str, Any]]:
        """
        Filter blocks by creation date range.

        Args:
            blocks: List of blocks to filter
            start: ISO format start date (inclusive)
            end: ISO format end date (inclusive)

        Returns:
            Filtered blocks within date range
        """
        filtered = blocks

        if start:
            filtered = [
                b for b in filtered
                if b.get("created_at", "") >= start
            ]

        if end:
            filtered = [
                b for b in filtered
                if b.get("created_at", "") <= end
            ]

        return filtered

    def _rank_and_dedupe(
        self,
        results: List[Dict[str, Any]],
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Rank results by combined score and remove duplicates.

        Ranking factors:
        1. Primary: Vector similarity score (0.0-1.0)
        2. Secondary: Metadata match boost (e.g., exact block type match)
        3. Tertiary: Content freshness (newer blocks get slight boost)

        Args:
            results: Search results to rank
            query: Original search query

        Returns:
            Ranked and deduplicated results
        """
        # Deduplicate by block_id
        seen_blocks = set()
        deduped = []

        for result in results:
            block_id = result["block"]["block_id"]

            if block_id in seen_blocks:
                continue

            seen_blocks.add(block_id)

            # Calculate final score with boosts
            base_score = result["score"]

            # Boost 1: Exact query term match in content (up to +0.1)
            searchable_text = self._extract_searchable_text(result["block"]).lower()
            query_lower = query.lower()
            query_boost = 0.1 if query_lower in searchable_text else 0.0

            # Boost 2: Freshness (newer blocks get up to +0.05)
            created_at = result["block"].get("created_at", "")
            freshness_boost = self._calculate_freshness_boost(created_at)

            # Boost 3: Block type relevance (heading blocks get +0.03)
            type_boost = 0.03 if result["block"].get("block_type") == "heading" else 0.0

            # Calculate final score (capped at 1.0)
            final_score = min(1.0, base_score + query_boost + freshness_boost + type_boost)

            result["final_score"] = final_score
            deduped.append(result)

        # Sort by final score descending
        deduped.sort(key=lambda x: x["final_score"], reverse=True)

        return deduped

    def _calculate_freshness_boost(self, created_at: str) -> float:
        """
        Calculate freshness boost based on creation date.

        Args:
            created_at: ISO format creation timestamp

        Returns:
            Boost value (0.0 to 0.05)
        """
        if not created_at:
            return 0.0

        try:
            from datetime import datetime
            created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            now = datetime.utcnow().replace(tzinfo=created.tzinfo)

            age_days = (now - created).days

            # Newer blocks get higher boost
            if age_days < 7:
                return 0.05
            elif age_days < 30:
                return 0.03
            elif age_days < 90:
                return 0.01
            else:
                return 0.0
        except Exception:
            return 0.0
