"""
Ocean Tags Integration Tests

Tests for tag CRUD operations and block tagging functionality.

These tests verify:
1. Tag creation with unique names per organization
2. Tag retrieval and filtering
3. Tag updates (name, color, description)
4. Tag deletion with block cleanup
5. Assigning tags to blocks
6. Removing tags from blocks
7. Multi-tenant isolation
8. Tag usage counting

All operations use the fixed ZeroDB REST API endpoints.
"""

import pytest
import httpx
import os
from typing import List, Dict, Any


# Test configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8100")
TEST_ORG_1 = "test-ocean-tags-org-1"
TEST_ORG_2 = "test-ocean-tags-org-2"

# Track created resources for cleanup
created_page_ids: List[str] = []
created_block_ids: List[str] = []
created_tag_ids: List[str] = []


@pytest.fixture(scope="module")
async def test_page_id():
    """Create a test page for block tagging tests."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/v1/ocean/pages",
            json={
                "organization_id": TEST_ORG_1,
                "title": "Test Page for Tags",
                "icon": "🏷️",
                "parent_page_id": None
            },
            timeout=30.0
        )

        assert response.status_code == 201
        page = response.json()
        page_id = page["page_id"]
        created_page_ids.append(page_id)

        yield page_id


@pytest.fixture(scope="module")
async def test_block_id(test_page_id):
    """Create a test block for tagging tests."""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/v1/ocean/blocks",
            json={
                "organization_id": TEST_ORG_1,
                "page_id": test_page_id,
                "type": "text",
                "content": {"text": "Test block for tagging"},
                "properties": {"tags": []}
            },
            timeout=30.0
        )

        assert response.status_code == 201
        block = response.json()
        block_id = block["block_id"]
        created_block_ids.append(block_id)

        yield block_id


class TestCreateTag:
    """Test tag creation."""

    @pytest.mark.asyncio
    async def test_create_tag_basic(self):
        """Create a basic tag with default color."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}/api/v1/ocean/tags",
                json={
                    "organization_id": TEST_ORG_1,
                    "name": "urgent",
                    "color": "#FF0000",
                    "description": "Urgent items"
                },
                timeout=30.0
            )

            assert response.status_code == 201
            tag = response.json()

            # Verify tag structure
            assert "tag_id" in tag
            assert "row_id" in tag  # Should be populated by ZeroDB
            assert tag["name"] == "urgent"
            assert tag["color"] == "#FF0000"
            assert tag["description"] == "Urgent items"
            assert tag["organization_id"] == TEST_ORG_1
            assert tag["usage_count"] == 0
            assert "created_at" in tag
            assert "updated_at" in tag

            created_tag_ids.append(tag["tag_id"])
            print(f"✓ Created tag: {tag['tag_id']} - {tag['name']}")

    @pytest.mark.asyncio
    async def test_create_tag_duplicate_name_fails(self):
        """Creating a tag with duplicate name in same org should fail."""
        # Create first tag
        async with httpx.AsyncClient() as client:
            response1 = await client.post(
                f"{API_BASE_URL}/api/v1/ocean/tags",
                json={
                    "organization_id": TEST_ORG_1,
                    "name": "important",
                    "color": "#FFA500"
                },
                timeout=30.0
            )

            assert response1.status_code == 201
            tag1 = response1.json()
            created_tag_ids.append(tag1["tag_id"])

            # Try to create duplicate
            response2 = await client.post(
                f"{API_BASE_URL}/api/v1/ocean/tags",
                json={
                    "organization_id": TEST_ORG_1,
                    "name": "important",
                    "color": "#00FF00"
                },
                timeout=30.0
            )

            # Should fail with 400 Bad Request
            assert response2.status_code == 400
            print("✓ Duplicate tag name blocked")

    @pytest.mark.asyncio
    async def test_create_tag_multi_tenant_isolation(self):
        """Same tag name can exist in different organizations."""
        async with httpx.AsyncClient() as client:
            # Create tag in org 1
            response1 = await client.post(
                f"{API_BASE_URL}/api/v1/ocean/tags",
                json={
                    "organization_id": TEST_ORG_1,
                    "name": "feature",
                    "color": "#0000FF"
                },
                timeout=30.0
            )

            assert response1.status_code == 201
            tag1 = response1.json()
            created_tag_ids.append(tag1["tag_id"])

            # Create same tag name in org 2
            response2 = await client.post(
                f"{API_BASE_URL}/api/v1/ocean/tags",
                json={
                    "organization_id": TEST_ORG_2,
                    "name": "feature",
                    "color": "#FF00FF"
                },
                timeout=30.0
            )

            assert response2.status_code == 201
            tag2 = response2.json()
            created_tag_ids.append(tag2["tag_id"])

            # Verify they're different tags
            assert tag1["tag_id"] != tag2["tag_id"]
            assert tag1["organization_id"] != tag2["organization_id"]
            print("✓ Multi-tenant tag isolation verified")


class TestGetTags:
    """Test tag retrieval and filtering."""

    @pytest.mark.asyncio
    async def test_list_tags(self):
        """List all tags for an organization."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/api/v1/ocean/tags",
                params={"organization_id": TEST_ORG_1},
                timeout=30.0
            )

            assert response.status_code == 200
            tags = response.json()

            assert isinstance(tags, list)
            assert len(tags) > 0  # Should have tags from previous tests

            # Verify all tags belong to TEST_ORG_1
            for tag in tags:
                assert tag["organization_id"] == TEST_ORG_1
                assert "tag_id" in tag
                assert "name" in tag
                assert "usage_count" in tag

            print(f"✓ Listed {len(tags)} tags for organization")

    @pytest.mark.asyncio
    async def test_list_tags_sorted_by_usage(self):
        """Tags should be sorted by usage_count descending."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{API_BASE_URL}/api/v1/ocean/tags",
                params={"organization_id": TEST_ORG_1},
                timeout=30.0
            )

            assert response.status_code == 200
            tags = response.json()

            # Verify descending order by usage_count
            usage_counts = [tag.get("usage_count", 0) for tag in tags]
            assert usage_counts == sorted(usage_counts, reverse=True)
            print("✓ Tags sorted by usage count")


class TestUpdateTag:
    """Test tag updates."""

    @pytest.mark.asyncio
    async def test_update_tag_name(self):
        """Update tag name."""
        # Create tag
        async with httpx.AsyncClient() as client:
            create_response = await client.post(
                f"{API_BASE_URL}/api/v1/ocean/tags",
                json={
                    "organization_id": TEST_ORG_1,
                    "name": "old-name",
                    "color": "#888888"
                },
                timeout=30.0
            )

            assert create_response.status_code == 201
            tag = create_response.json()
            tag_id = tag["tag_id"]
            created_tag_ids.append(tag_id)

            # Update tag
            update_response = await client.patch(
                f"{API_BASE_URL}/api/v1/ocean/tags/{tag_id}",
                json={
                    "organization_id": TEST_ORG_1,
                    "name": "new-name"
                },
                timeout=30.0
            )

            assert update_response.status_code == 200
            updated_tag = update_response.json()

            assert updated_tag["tag_id"] == tag_id
            assert updated_tag["name"] == "new-name"
            assert updated_tag["color"] == "#888888"  # Preserved
            print("✓ Tag name updated")

    @pytest.mark.asyncio
    async def test_update_tag_color_and_description(self):
        """Update tag color and description."""
        # Create tag
        async with httpx.AsyncClient() as client:
            create_response = await client.post(
                f"{API_BASE_URL}/api/v1/ocean/tags",
                json={
                    "organization_id": TEST_ORG_1,
                    "name": "test-update-color",
                    "color": "#000000",
                    "description": "Old description"
                },
                timeout=30.0
            )

            assert create_response.status_code == 201
            tag = create_response.json()
            tag_id = tag["tag_id"]
            created_tag_ids.append(tag_id)

            # Update tag
            update_response = await client.patch(
                f"{API_BASE_URL}/api/v1/ocean/tags/{tag_id}",
                json={
                    "organization_id": TEST_ORG_1,
                    "color": "#FFFFFF",
                    "description": "New description"
                },
                timeout=30.0
            )

            assert update_response.status_code == 200
            updated_tag = update_response.json()

            assert updated_tag["color"] == "#FFFFFF"
            assert updated_tag["description"] == "New description"
            assert updated_tag["name"] == "test-update-color"  # Preserved
            print("✓ Tag color and description updated")


class TestDeleteTag:
    """Test tag deletion."""

    @pytest.mark.asyncio
    async def test_delete_tag(self):
        """Delete a tag."""
        # Create tag
        async with httpx.AsyncClient() as client:
            create_response = await client.post(
                f"{API_BASE_URL}/api/v1/ocean/tags",
                json={
                    "organization_id": TEST_ORG_1,
                    "name": "to-delete",
                    "color": "#999999"
                },
                timeout=30.0
            )

            assert create_response.status_code == 201
            tag = create_response.json()
            tag_id = tag["tag_id"]

            # Delete tag
            delete_response = await client.delete(
                f"{API_BASE_URL}/api/v1/ocean/tags/{tag_id}",
                params={"organization_id": TEST_ORG_1},
                timeout=30.0
            )

            assert delete_response.status_code == 204
            print("✓ Tag deleted")

    @pytest.mark.asyncio
    async def test_delete_tag_not_found(self):
        """Deleting non-existent tag should return 404."""
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{API_BASE_URL}/api/v1/ocean/tags/non-existent-tag-id",
                params={"organization_id": TEST_ORG_1},
                timeout=30.0
            )

            assert response.status_code == 404
            print("✓ Delete non-existent tag returns 404")


class TestAssignTag:
    """Test assigning tags to blocks."""

    @pytest.mark.asyncio
    async def test_assign_tag_to_block(self, test_block_id):
        """Assign a tag to a block."""
        # Create tag
        async with httpx.AsyncClient() as client:
            tag_response = await client.post(
                f"{API_BASE_URL}/api/v1/ocean/tags",
                json={
                    "organization_id": TEST_ORG_1,
                    "name": "assigned-tag",
                    "color": "#AAAAAA"
                },
                timeout=30.0
            )

            assert tag_response.status_code == 201
            tag = tag_response.json()
            tag_id = tag["tag_id"]
            created_tag_ids.append(tag_id)

            # Assign tag to block
            assign_response = await client.post(
                f"{API_BASE_URL}/api/v1/ocean/tags/{tag_id}/assign",
                json={
                    "organization_id": TEST_ORG_1,
                    "block_id": test_block_id
                },
                timeout=30.0
            )

            assert assign_response.status_code == 200

            # Verify tag was assigned (check block)
            block_response = await client.get(
                f"{API_BASE_URL}/api/v1/ocean/blocks/{test_block_id}",
                params={"organization_id": TEST_ORG_1},
                timeout=30.0
            )

            assert block_response.status_code == 200
            block = block_response.json()
            assert tag_id in block["properties"].get("tags", [])

            # Verify usage count incremented
            tags_response = await client.get(
                f"{API_BASE_URL}/api/v1/ocean/tags",
                params={"organization_id": TEST_ORG_1},
                timeout=30.0
            )
            tags = tags_response.json()
            assigned_tag = next(t for t in tags if t["tag_id"] == tag_id)
            assert assigned_tag["usage_count"] == 1

            print(f"✓ Tag {tag_id} assigned to block {test_block_id}")

    @pytest.mark.asyncio
    async def test_assign_tag_already_assigned(self, test_block_id):
        """Assigning same tag twice should return false (idempotent)."""
        # Create tag
        async with httpx.AsyncClient() as client:
            tag_response = await client.post(
                f"{API_BASE_URL}/api/v1/ocean/tags",
                json={
                    "organization_id": TEST_ORG_1,
                    "name": "duplicate-assign",
                    "color": "#BBBBBB"
                },
                timeout=30.0
            )

            assert tag_response.status_code == 201
            tag = tag_response.json()
            tag_id = tag["tag_id"]
            created_tag_ids.append(tag_id)

            # Assign tag first time
            assign1 = await client.post(
                f"{API_BASE_URL}/api/v1/ocean/tags/{tag_id}/assign",
                json={
                    "organization_id": TEST_ORG_1,
                    "block_id": test_block_id
                },
                timeout=30.0
            )
            assert assign1.status_code == 200

            # Assign tag second time (should be idempotent)
            assign2 = await client.post(
                f"{API_BASE_URL}/api/v1/ocean/tags/{tag_id}/assign",
                json={
                    "organization_id": TEST_ORG_1,
                    "block_id": test_block_id
                },
                timeout=30.0
            )
            # Should return success but not increment usage count
            assert assign2.status_code == 200
            print("✓ Duplicate tag assignment handled")


class TestRemoveTag:
    """Test removing tags from blocks."""

    @pytest.mark.asyncio
    async def test_remove_tag_from_block(self, test_block_id):
        """Remove a tag from a block."""
        # Create tag and assign it
        async with httpx.AsyncClient() as client:
            tag_response = await client.post(
                f"{API_BASE_URL}/api/v1/ocean/tags",
                json={
                    "organization_id": TEST_ORG_1,
                    "name": "to-remove",
                    "color": "#CCCCCC"
                },
                timeout=30.0
            )

            assert tag_response.status_code == 201
            tag = tag_response.json()
            tag_id = tag["tag_id"]
            created_tag_ids.append(tag_id)

            # Assign tag
            await client.post(
                f"{API_BASE_URL}/api/v1/ocean/tags/{tag_id}/assign",
                json={
                    "organization_id": TEST_ORG_1,
                    "block_id": test_block_id
                },
                timeout=30.0
            )

            # Remove tag
            remove_response = await client.post(
                f"{API_BASE_URL}/api/v1/ocean/tags/{tag_id}/remove",
                json={
                    "organization_id": TEST_ORG_1,
                    "block_id": test_block_id
                },
                timeout=30.0
            )

            assert remove_response.status_code == 200

            # Verify tag was removed (check block)
            block_response = await client.get(
                f"{API_BASE_URL}/api/v1/ocean/blocks/{test_block_id}",
                params={"organization_id": TEST_ORG_1},
                timeout=30.0
            )

            assert block_response.status_code == 200
            block = block_response.json()
            assert tag_id not in block["properties"].get("tags", [])

            # Verify usage count decremented
            tags_response = await client.get(
                f"{API_BASE_URL}/api/v1/ocean/tags",
                params={"organization_id": TEST_ORG_1},
                timeout=30.0
            )
            tags = tags_response.json()
            removed_tag = next(t for t in tags if t["tag_id"] == tag_id)
            assert removed_tag["usage_count"] == 0

            print(f"✓ Tag {tag_id} removed from block {test_block_id}")


# Cleanup after all tests
@pytest.fixture(scope="module", autouse=True)
def cleanup():
    """Cleanup created resources after all tests."""
    yield

    # Note: In production, add cleanup logic here if needed
    # For now, tests create resources in test organizations
    print(f"\n✓ Test completed - created {len(created_tag_ids)} tags")
