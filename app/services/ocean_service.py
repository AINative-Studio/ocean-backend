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
