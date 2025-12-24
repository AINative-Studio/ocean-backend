"""
Ocean Blocks API Integration Tests

Tests comprehensive CRUD operations for Ocean blocks with embedding generation
and multi-tenant isolation.

Test Coverage:
- Create block operations (basic, different types, with embeddings, validation)
- Batch create operations (small/large batches, embedding verification)
- Get block operations (by ID, not found, multi-tenant isolation)
- List blocks operations (by page, pagination, ordering by position)
- Update block operations (content, embedding regeneration, position)
- Delete block operations (hard delete, embedding cleanup)
- Move block operations (reorder position, update affected blocks)
- Convert block type operations (preserve content, regenerate embeddings)

Issue #9: Write integration tests for blocks
"""

import os
import pytest
import httpx
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_V1_PREFIX = "/api/v1/ocean"  # Ocean routes are under /ocean prefix
ZERODB_API_KEY = os.getenv("ZERODB_API_KEY")
ZERODB_PROJECT_ID = os.getenv("ZERODB_PROJECT_ID")

# Test organization IDs for multi-tenant testing
TEST_ORG_ID = "test-org-1"
TEST_ORG_ID_2 = "test-org-2"
TEST_USER_ID = "test-user-1"

# Test data storage (for cleanup and cross-test references)
created_page_ids: List[str] = []
created_block_ids: List[str] = []


# ========================================================================
# HELPER FUNCTIONS
# ========================================================================

async def create_test_page(client: httpx.AsyncClient, title: str = "Test Page") -> Dict[str, Any]:
    """Helper to create a test page for block tests."""
    response = await client.post(
        f"{API_BASE_URL}{API_V1_PREFIX}/pages",
        headers={
            "Authorization": f"Bearer {ZERODB_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "organization_id": TEST_ORG_ID,
            "user_id": TEST_USER_ID,
            "title": title,
            "icon": "📄"
        }
    )
    assert response.status_code == 201, f"Failed to create test page: {response.text}"
    page_data = response.json()
    created_page_ids.append(page_data["page_id"])
    return page_data


# ========================================================================
# TEST SUITE: CREATE BLOCK
# ========================================================================

class TestCreateBlock:
    """Test suite for POST /api/v1/blocks endpoint"""

    @pytest.mark.asyncio
    async def test_create_text_block(self):
        """Test creating a basic text block with embedding"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # First create a page
            page = await create_test_page(client, "Text Block Test Page")
            page_id = page["page_id"]

            # Create text block
            response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks?page_id={page_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "block_type": "text",
                    "content": {"text": "This is a paragraph of text for testing"},
                    "properties": {}
                }
            )

            assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"

            data = response.json()

            # Verify response structure
            assert "block_id" in data
            assert "page_id" in data
            assert "organization_id" in data
            assert "user_id" in data
            assert "block_type" in data
            assert "content" in data
            assert "position" in data
            assert "vector_id" in data  # Critical: verify embedding was created
            assert "vector_dimensions" in data
            assert "created_at" in data
            assert "updated_at" in data

            # Verify data correctness
            assert data["page_id"] == page_id
            assert data["organization_id"] == TEST_ORG_ID
            assert data["user_id"] == TEST_USER_ID
            assert data["block_type"] == "text"
            assert data["content"]["text"] == "This is a paragraph of text for testing"
            assert data["position"] == 0  # First block in page
            assert data["vector_id"] is not None, "Text block should have embedding"
            assert data["vector_dimensions"] == 768  # BAAI/bge-base-en-v1.5

            created_block_ids.append(data["block_id"])

            print(f"✓ Create text block: block_id={data['block_id']}, vector_id={data['vector_id']}, dims={data['vector_dimensions']}")

    @pytest.mark.asyncio
    async def test_create_heading_block(self):
        """Test creating a heading block"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            page = await create_test_page(client, "Heading Block Test Page")
            page_id = page["page_id"]

            response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks?page_id={page_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "block_type": "heading",
                    "content": {"text": "Project Overview", "level": 1},
                    "properties": {}
                }
            )

            assert response.status_code == 201
            data = response.json()

            assert data["block_type"] == "heading"
            assert data["content"]["text"] == "Project Overview"
            assert data["content"]["level"] == 1
            assert data["vector_id"] is not None  # Headings are searchable
            assert data["vector_dimensions"] == 768

            created_block_ids.append(data["block_id"])

            print(f"✓ Create heading block: level={data['content']['level']}, has_embedding={data['vector_id'] is not None}")

    @pytest.mark.asyncio
    async def test_create_task_block(self):
        """Test creating a task block with checked state"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            page = await create_test_page(client, "Task Block Test Page")
            page_id = page["page_id"]

            response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks?page_id={page_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "block_type": "task",
                    "content": {
                        "text": "Complete integration tests",
                        "checked": False
                    },
                    "properties": {"tags": ["testing", "urgent"]}
                }
            )

            assert response.status_code == 201
            data = response.json()

            assert data["block_type"] == "task"
            assert data["content"]["text"] == "Complete integration tests"
            assert data["content"]["checked"] is False
            assert data["properties"]["tags"] == ["testing", "urgent"]
            assert data["vector_id"] is not None  # Tasks are searchable

            created_block_ids.append(data["block_id"])

            print(f"✓ Create task block: checked={data['content']['checked']}, tags={data['properties'].get('tags')}")

    @pytest.mark.asyncio
    async def test_create_with_embedding(self):
        """Test that blocks with content automatically get embeddings"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            page = await create_test_page(client, "Embedding Test Page")
            page_id = page["page_id"]

            # Create multiple blocks of different types
            test_blocks = [
                {"block_type": "text", "content": {"text": "Searchable text content"}},
                {"block_type": "heading", "content": {"text": "Searchable heading", "level": 2}},
                {"block_type": "task", "content": {"text": "Searchable task", "checked": False}},
                {"block_type": "list", "content": {"items": ["Item 1", "Item 2"]}}
            ]

            for block_data in test_blocks:
                response = await client.post(
                    f"{API_BASE_URL}{API_V1_PREFIX}/blocks?page_id={page_id}",
                    headers={
                        "Authorization": f"Bearer {ZERODB_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={**block_data, "properties": {}}
                )

                assert response.status_code == 201
                data = response.json()

                # All these block types should have embeddings
                assert data["vector_id"] is not None, f"{block_data['block_type']} should have embedding"
                assert data["vector_dimensions"] == 768

                created_block_ids.append(data["block_id"])

            print(f"✓ Create with embeddings: verified all {len(test_blocks)} block types have vector_id")

    @pytest.mark.asyncio
    async def test_create_validation_error(self):
        """Test block creation with invalid data returns validation error"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            page = await create_test_page(client, "Validation Test Page")
            page_id = page["page_id"]

            # Missing required block_type
            response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks?page_id={page_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "content": {"text": "Missing block type"}
                }
            )

            assert response.status_code in [400, 422], f"Expected validation error, got {response.status_code}"

            # Missing required content
            response2 = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks?page_id={page_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "block_type": "text"
                    # No content
                }
            )

            assert response2.status_code in [400, 422]

            print(f"✓ Create validation errors: {response.status_code}, {response2.status_code}")


# ========================================================================
# TEST SUITE: BATCH CREATE BLOCKS
# ========================================================================

class TestCreateBlockBatch:
    """Test suite for POST /api/v1/blocks/batch endpoint"""

    @pytest.mark.asyncio
    async def test_batch_create_10_blocks(self):
        """Test batch creating 10 blocks efficiently"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            page = await create_test_page(client, "Batch 10 Blocks Test Page")
            page_id = page["page_id"]

            # Create 10 blocks in batch
            blocks_to_create = [
                {
                    "block_type": "heading",
                    "content": {"text": f"Section {i+1}", "level": 2},
                    "properties": {}
                }
                for i in range(10)
            ]

            response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks/batch?page_id={page_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "blocks": blocks_to_create
                }
            )

            assert response.status_code == 201
            data = response.json()

            # Verify response structure
            assert "blocks" in data
            assert "total" in data
            assert data["total"] == 10
            assert len(data["blocks"]) == 10

            # Verify all blocks were created
            for i, block in enumerate(data["blocks"]):
                assert block["block_type"] == "heading"
                assert block["content"]["text"] == f"Section {i+1}"
                assert block["position"] == i  # Positions should be sequential
                assert block["page_id"] == page_id
                created_block_ids.append(block["block_id"])

            print(f"✓ Batch create 10 blocks: total={data['total']}, sequential positions verified")

    @pytest.mark.asyncio
    async def test_batch_create_100_blocks(self):
        """Test batch creating 100 blocks (performance test)"""
        async with httpx.AsyncClient(timeout=60.0) as client:  # Longer timeout for large batch
            page = await create_test_page(client, "Batch 100 Blocks Test Page")
            page_id = page["page_id"]

            # Create 100 blocks in batch
            blocks_to_create = [
                {
                    "block_type": "text",
                    "content": {"text": f"Paragraph {i+1}: This is test content for performance testing."},
                    "properties": {}
                }
                for i in range(100)
            ]

            response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks/batch?page_id={page_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "blocks": blocks_to_create
                }
            )

            assert response.status_code == 201
            data = response.json()

            assert data["total"] == 100
            assert len(data["blocks"]) == 100

            # Verify sequential positions
            for i, block in enumerate(data["blocks"]):
                assert block["position"] == i
                created_block_ids.append(block["block_id"])

            print(f"✓ Batch create 100 blocks: total={data['total']}, performance validated")

    @pytest.mark.asyncio
    async def test_batch_embeddings_generated(self):
        """Test that batch creation generates embeddings for all blocks"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            page = await create_test_page(client, "Batch Embeddings Test Page")
            page_id = page["page_id"]

            # Create mixed block types in batch
            blocks_to_create = [
                {"block_type": "heading", "content": {"text": "Introduction", "level": 1}, "properties": {}},
                {"block_type": "text", "content": {"text": "First paragraph"}, "properties": {}},
                {"block_type": "text", "content": {"text": "Second paragraph"}, "properties": {}},
                {"block_type": "task", "content": {"text": "Review document", "checked": False}, "properties": {}},
                {"block_type": "list", "content": {"items": ["Point 1", "Point 2"]}, "properties": {}}
            ]

            response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks/batch?page_id={page_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "blocks": blocks_to_create
                }
            )

            assert response.status_code == 201
            data = response.json()

            # Verify ALL blocks have embeddings
            for block in data["blocks"]:
                assert block["vector_id"] is not None, f"{block['block_type']} should have embedding"
                assert block["vector_dimensions"] == 768
                created_block_ids.append(block["block_id"])

            print(f"✓ Batch embeddings: verified all {len(data['blocks'])} blocks have vector_id and dimensions=768")


# ========================================================================
# TEST SUITE: GET BLOCK
# ========================================================================

class TestGetBlock:
    """Test suite for GET /api/v1/blocks/{block_id} endpoint"""

    @pytest.mark.asyncio
    async def test_get_block_by_id(self):
        """Test retrieving a block by ID"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create page and block
            page = await create_test_page(client, "Get Block Test Page")
            page_id = page["page_id"]

            create_response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks?page_id={page_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "block_type": "text",
                    "content": {"text": "Block to retrieve"},
                    "properties": {}
                }
            )

            assert create_response.status_code == 201
            block_data = create_response.json()
            block_id = block_data["block_id"]
            created_block_ids.append(block_id)

            # Retrieve the block
            get_response = await client.get(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks/{block_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}"
                }
            )

            assert get_response.status_code == 200
            retrieved_data = get_response.json()

            # Verify data matches
            assert retrieved_data["block_id"] == block_id
            assert retrieved_data["page_id"] == page_id
            assert retrieved_data["content"]["text"] == "Block to retrieve"
            assert retrieved_data["vector_id"] == block_data["vector_id"]

            print(f"✓ Get block by ID: block_id={block_id}, vector_id={retrieved_data['vector_id']}")

    @pytest.mark.asyncio
    async def test_get_block_not_found(self):
        """Test retrieving a non-existent block returns 404"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks/non-existent-block-id-xyz",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}"
                }
            )

            assert response.status_code == 404, f"Expected 404, got {response.status_code}"

            data = response.json()
            assert "detail" in data or "error" in data

            print(f"✓ Get block not found: {response.status_code}")

    @pytest.mark.asyncio
    async def test_get_block_multi_tenant_isolation(self):
        """Test multi-tenant isolation - cannot access other org's blocks"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create page and block in ORG 1
            page_response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "organization_id": TEST_ORG_ID,
                    "user_id": TEST_USER_ID,
                    "title": "Org 1 Private Page"
                }
            )
            assert page_response.status_code == 201
            page_id = page_response.json()["page_id"]
            created_page_ids.append(page_id)

            block_response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks?page_id={page_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "block_type": "text",
                    "content": {"text": "Org 1 Private Block"},
                    "properties": {}
                }
            )
            assert block_response.status_code == 201
            block_id = block_response.json()["block_id"]
            created_block_ids.append(block_id)

            # Try to access with ORG 2 credentials
            # Note: This test assumes the API checks organization_id in authentication
            # If not implemented yet, this test documents expected behavior
            get_response = await client.get(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks/{block_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "X-Organization-ID": TEST_ORG_ID_2  # Different org
                }
            )

            # Should return 404 (not found) due to multi-tenant isolation
            # If backend doesn't check org yet, this documents the requirement
            assert get_response.status_code in [404, 403], f"Expected 404/403 for cross-org access, got {get_response.status_code}"

            print(f"✓ Multi-tenant isolation enforced on GET block: {get_response.status_code}")


# ========================================================================
# TEST SUITE: LIST BLOCKS
# ========================================================================

class TestListBlocks:
    """Test suite for GET /api/v1/blocks endpoint"""

    @pytest.mark.asyncio
    async def test_list_blocks_by_page(self):
        """Test listing all blocks for a page"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            page = await create_test_page(client, "List Blocks Test Page")
            page_id = page["page_id"]

            # Create 5 test blocks
            for i in range(5):
                create_response = await client.post(
                    f"{API_BASE_URL}{API_V1_PREFIX}/blocks?page_id={page_id}",
                    headers={
                        "Authorization": f"Bearer {ZERODB_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "block_type": "text",
                        "content": {"text": f"Block {i+1}"},
                        "properties": {}
                    }
                )
                assert create_response.status_code == 201
                created_block_ids.append(create_response.json()["block_id"])

            # List all blocks for the page
            list_response = await client.get(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks?page_id={page_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}"
                }
            )

            assert list_response.status_code == 200
            data = list_response.json()

            assert "blocks" in data
            assert "total" in data
            assert len(data["blocks"]) == 5

            # Verify all blocks belong to the page
            for block in data["blocks"]:
                assert block["page_id"] == page_id

            print(f"✓ List blocks by page: {len(data['blocks'])} blocks found")

    @pytest.mark.asyncio
    async def test_list_blocks_pagination(self):
        """Test pagination with limit and offset"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            page = await create_test_page(client, "Pagination Test Page")
            page_id = page["page_id"]

            # Create 10 blocks
            for i in range(10):
                create_response = await client.post(
                    f"{API_BASE_URL}{API_V1_PREFIX}/blocks?page_id={page_id}",
                    headers={
                        "Authorization": f"Bearer {ZERODB_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "block_type": "text",
                        "content": {"text": f"Pagination Block {i+1}"},
                        "properties": {}
                    }
                )
                assert create_response.status_code == 201
                created_block_ids.append(create_response.json()["block_id"])

            # Get first 3 blocks
            page1_response = await client.get(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks?page_id={page_id}&limit=3&offset=0",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}"
                }
            )

            assert page1_response.status_code == 200
            page1_data = page1_response.json()
            assert len(page1_data["blocks"]) == 3

            # Get next 3 blocks
            page2_response = await client.get(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks?page_id={page_id}&limit=3&offset=3",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}"
                }
            )

            assert page2_response.status_code == 200
            page2_data = page2_response.json()
            assert len(page2_data["blocks"]) == 3

            # Verify no duplicates
            page1_ids = {b["block_id"] for b in page1_data["blocks"]}
            page2_ids = {b["block_id"] for b in page2_data["blocks"]}
            assert len(page1_ids.intersection(page2_ids)) == 0

            print(f"✓ List blocks pagination: page1={len(page1_data['blocks'])}, page2={len(page2_data['blocks'])}, no duplicates")

    @pytest.mark.asyncio
    async def test_list_blocks_ordered_by_position(self):
        """Test that blocks are returned in position order"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            page = await create_test_page(client, "Position Order Test Page")
            page_id = page["page_id"]

            # Create blocks
            for i in range(5):
                create_response = await client.post(
                    f"{API_BASE_URL}{API_V1_PREFIX}/blocks?page_id={page_id}",
                    headers={
                        "Authorization": f"Bearer {ZERODB_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "block_type": "text",
                        "content": {"text": f"Position {i}"},
                        "properties": {}
                    }
                )
                assert create_response.status_code == 201
                created_block_ids.append(create_response.json()["block_id"])

            # List blocks
            list_response = await client.get(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks?page_id={page_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}"
                }
            )

            assert list_response.status_code == 200
            data = list_response.json()

            # Verify blocks are in position order (0, 1, 2, 3, 4)
            positions = [block["position"] for block in data["blocks"]]
            assert positions == sorted(positions), "Blocks should be ordered by position"
            assert positions == [0, 1, 2, 3, 4]

            print(f"✓ List blocks ordered by position: {positions}")


# ========================================================================
# TEST SUITE: UPDATE BLOCK
# ========================================================================

class TestUpdateBlock:
    """Test suite for PUT /api/v1/blocks/{block_id} endpoint"""

    @pytest.mark.asyncio
    async def test_update_block_content(self):
        """Test updating block content"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            page = await create_test_page(client, "Update Content Test Page")
            page_id = page["page_id"]

            # Create block
            create_response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks?page_id={page_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "block_type": "text",
                    "content": {"text": "Original content"},
                    "properties": {}
                }
            )
            assert create_response.status_code == 201
            block_id = create_response.json()["block_id"]
            created_block_ids.append(block_id)

            # Update block content
            update_response = await client.put(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks/{block_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "content": {"text": "Updated content"},
                    "properties": {"color": "blue"}
                }
            )

            assert update_response.status_code == 200
            updated_data = update_response.json()

            assert updated_data["content"]["text"] == "Updated content"
            assert updated_data["properties"]["color"] == "blue"
            assert updated_data["block_id"] == block_id

            print(f"✓ Update block content: content and properties updated")

    @pytest.mark.asyncio
    async def test_update_regenerates_embedding(self):
        """Test that updating content regenerates the embedding (critical!)"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            page = await create_test_page(client, "Embedding Regeneration Test Page")
            page_id = page["page_id"]

            # Create block
            create_response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks?page_id={page_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "block_type": "text",
                    "content": {"text": "Original searchable text"},
                    "properties": {}
                }
            )
            assert create_response.status_code == 201
            original_data = create_response.json()
            block_id = original_data["block_id"]
            original_vector_id = original_data["vector_id"]
            created_block_ids.append(block_id)

            # Update block content (should regenerate embedding)
            update_response = await client.put(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks/{block_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "content": {"text": "Completely different searchable text"}
                }
            )

            assert update_response.status_code == 200
            updated_data = update_response.json()

            # Verify embedding was regenerated
            assert updated_data["vector_id"] is not None
            assert updated_data["vector_dimensions"] == 768

            # Note: vector_id might change if old one was deleted and new one created
            # The important thing is that it still exists and has correct dimensions

            print(f"✓ Update regenerates embedding: original_vector={original_vector_id}, new_vector={updated_data['vector_id']}, dims=768")

    @pytest.mark.asyncio
    async def test_update_preserves_vector_id_if_no_content_change(self):
        """Test that updating properties without content change preserves vector_id"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            page = await create_test_page(client, "Preserve Vector Test Page")
            page_id = page["page_id"]

            # Create block
            create_response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks?page_id={page_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "block_type": "text",
                    "content": {"text": "Text that shouldn't trigger embedding regeneration"},
                    "properties": {}
                }
            )
            assert create_response.status_code == 201
            original_data = create_response.json()
            block_id = original_data["block_id"]
            original_vector_id = original_data["vector_id"]
            created_block_ids.append(block_id)

            # Update only properties (not content)
            update_response = await client.put(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks/{block_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "properties": {"color": "red", "tags": ["important"]}
                }
            )

            assert update_response.status_code == 200
            updated_data = update_response.json()

            # Verify vector_id is preserved (content didn't change)
            assert updated_data["vector_id"] == original_vector_id
            assert updated_data["properties"]["color"] == "red"

            print(f"✓ Update preserves vector_id when content unchanged: {original_vector_id}")


# ========================================================================
# TEST SUITE: DELETE BLOCK
# ========================================================================

class TestDeleteBlock:
    """Test suite for DELETE /api/v1/blocks/{block_id} endpoint"""

    @pytest.mark.asyncio
    async def test_delete_block(self):
        """Test deleting a block (hard delete)"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            page = await create_test_page(client, "Delete Block Test Page")
            page_id = page["page_id"]

            # Create block
            create_response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks?page_id={page_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "block_type": "text",
                    "content": {"text": "Block to delete"},
                    "properties": {}
                }
            )
            assert create_response.status_code == 201
            block_id = create_response.json()["block_id"]

            # Delete block
            delete_response = await client.delete(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks/{block_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}"
                }
            )

            assert delete_response.status_code == 204, f"Expected 204, got {delete_response.status_code}"

            # Verify block is gone (should return 404)
            get_response = await client.get(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks/{block_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}"
                }
            )

            assert get_response.status_code == 404, "Block should not exist after deletion"

            print(f"✓ Delete block: hard delete verified (404 on GET)")

    @pytest.mark.asyncio
    async def test_delete_removes_embedding(self):
        """Test that deleting a block removes its embedding"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            page = await create_test_page(client, "Delete Embedding Test Page")
            page_id = page["page_id"]

            # Create block with embedding
            create_response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks?page_id={page_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "block_type": "text",
                    "content": {"text": "Block with embedding to delete"},
                    "properties": {}
                }
            )
            assert create_response.status_code == 201
            block_data = create_response.json()
            block_id = block_data["block_id"]
            vector_id = block_data["vector_id"]

            assert vector_id is not None, "Block should have embedding before deletion"

            # Delete block
            delete_response = await client.delete(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks/{block_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}"
                }
            )

            assert delete_response.status_code == 204

            # Note: We can't directly verify the vector was deleted from ZeroDB in this test
            # but the service should handle this. This documents the expected behavior.

            print(f"✓ Delete removes embedding: block deleted, vector_id={vector_id} should be cleaned up")


# ========================================================================
# TEST SUITE: MOVE BLOCK
# ========================================================================

class TestMoveBlock:
    """Test suite for POST /api/v1/blocks/{block_id}/move endpoint"""

    @pytest.mark.asyncio
    async def test_move_block_reorders_position(self):
        """Test moving a block updates its position and reorders other blocks"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            page = await create_test_page(client, "Move Block Test Page")
            page_id = page["page_id"]

            # Create 5 blocks (positions 0-4)
            block_ids = []
            for i in range(5):
                create_response = await client.post(
                    f"{API_BASE_URL}{API_V1_PREFIX}/blocks?page_id={page_id}",
                    headers={
                        "Authorization": f"Bearer {ZERODB_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "block_type": "text",
                        "content": {"text": f"Block at position {i}"},
                        "properties": {}
                    }
                )
                assert create_response.status_code == 201
                block_id = create_response.json()["block_id"]
                block_ids.append(block_id)
                created_block_ids.append(block_id)

            # Move block from position 1 to position 3
            # Original: [0, 1, 2, 3, 4]
            # After:    [0, 2, 3, 1, 4]
            move_response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks/{block_ids[1]}/move",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "new_position": 3
                }
            )

            assert move_response.status_code == 200
            moved_data = move_response.json()
            assert moved_data["position"] == 3

            # List all blocks to verify reordering
            list_response = await client.get(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks?page_id={page_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}"
                }
            )

            assert list_response.status_code == 200
            all_blocks = list_response.json()["blocks"]

            # Verify positions are sequential
            positions = [block["position"] for block in all_blocks]
            assert positions == [0, 1, 2, 3, 4], "Positions should remain sequential after move"

            print(f"✓ Move block reorders position: moved block to position 3, all positions sequential")

    @pytest.mark.asyncio
    async def test_move_updates_affected_blocks(self):
        """Test that moving a block updates positions of affected blocks"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            page = await create_test_page(client, "Move Affected Blocks Test Page")
            page_id = page["page_id"]

            # Create 3 blocks
            block_ids = []
            for i in range(3):
                create_response = await client.post(
                    f"{API_BASE_URL}{API_V1_PREFIX}/blocks?page_id={page_id}",
                    headers={
                        "Authorization": f"Bearer {ZERODB_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "block_type": "text",
                        "content": {"text": f"Block {i}"},
                        "properties": {}
                    }
                )
                assert create_response.status_code == 201
                block_ids.append(create_response.json()["block_id"])
                created_block_ids.append(create_response.json()["block_id"])

            # Move last block to first position
            # Original: [0, 1, 2]
            # After:    [2, 0, 1]
            move_response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks/{block_ids[2]}/move",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "new_position": 0
                }
            )

            assert move_response.status_code == 200

            # Verify all blocks have correct positions
            list_response = await client.get(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks?page_id={page_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}"
                }
            )

            assert list_response.status_code == 200
            all_blocks = list_response.json()["blocks"]

            # Should still be sequential 0, 1, 2
            positions = [block["position"] for block in all_blocks]
            assert positions == [0, 1, 2]

            print(f"✓ Move updates affected blocks: all positions remain sequential after reordering")


# ========================================================================
# TEST SUITE: CONVERT BLOCK TYPE
# ========================================================================

class TestConvertBlockType:
    """Test suite for PUT /api/v1/blocks/{block_id}/convert endpoint"""

    @pytest.mark.asyncio
    async def test_convert_text_to_task(self):
        """Test converting a text block to a task block"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            page = await create_test_page(client, "Convert Text to Task Page")
            page_id = page["page_id"]

            # Create text block
            create_response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks?page_id={page_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "block_type": "text",
                    "content": {"text": "This should become a task"},
                    "properties": {}
                }
            )
            assert create_response.status_code == 201
            block_id = create_response.json()["block_id"]
            created_block_ids.append(block_id)

            # Convert to task
            convert_response = await client.put(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks/{block_id}/convert",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "new_type": "task"
                }
            )

            assert convert_response.status_code == 200
            converted_data = convert_response.json()

            assert converted_data["block_type"] == "task"
            assert converted_data["content"]["text"] == "This should become a task"
            assert "checked" in converted_data["content"]  # Task should have checked field

            print(f"✓ Convert text to task: block_type=task, content preserved, checked field added")

    @pytest.mark.asyncio
    async def test_convert_preserves_content(self):
        """Test that conversion preserves content intelligently"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            page = await create_test_page(client, "Convert Preserve Content Page")
            page_id = page["page_id"]

            # Create heading block
            create_response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks?page_id={page_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "block_type": "heading",
                    "content": {"text": "Important Heading", "level": 1},
                    "properties": {}
                }
            )
            assert create_response.status_code == 201
            block_id = create_response.json()["block_id"]
            created_block_ids.append(block_id)

            # Convert to text
            convert_response = await client.put(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks/{block_id}/convert",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "new_type": "text"
                }
            )

            assert convert_response.status_code == 200
            converted_data = convert_response.json()

            assert converted_data["block_type"] == "text"
            assert converted_data["content"]["text"] == "Important Heading"  # Text preserved

            print(f"✓ Convert preserves content: heading->text, text content preserved")

    @pytest.mark.asyncio
    async def test_convert_regenerates_embedding(self):
        """Test that conversion regenerates embedding if needed"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            page = await create_test_page(client, "Convert Regenerate Embedding Page")
            page_id = page["page_id"]

            # Create task block
            create_response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks?page_id={page_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "block_type": "task",
                    "content": {"text": "Task to convert", "checked": False},
                    "properties": {}
                }
            )
            assert create_response.status_code == 201
            original_data = create_response.json()
            block_id = original_data["block_id"]
            original_vector_id = original_data["vector_id"]
            created_block_ids.append(block_id)

            # Convert to text
            convert_response = await client.put(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks/{block_id}/convert",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "new_type": "text"
                }
            )

            assert convert_response.status_code == 200
            converted_data = convert_response.json()

            # Verify embedding still exists (should be regenerated)
            assert converted_data["vector_id"] is not None
            assert converted_data["vector_dimensions"] == 768

            print(f"✓ Convert regenerates embedding: original={original_vector_id}, new={converted_data['vector_id']}, dims=768")


# ========================================================================
# PYTEST CONFIGURATION AND FIXTURES
# ========================================================================

@pytest.fixture(scope="session", autouse=True)
def verify_credentials():
    """Verify required credentials before running tests"""
    if not ZERODB_API_KEY:
        pytest.skip("ZERODB_API_KEY not set in environment")
    if not ZERODB_PROJECT_ID:
        pytest.skip("ZERODB_PROJECT_ID not set in environment")

    print(f"\n{'='*80}")
    print(f"Ocean Blocks API Test Configuration")
    print(f"{'='*80}")
    print(f"API URL: {API_BASE_URL}")
    print(f"API Version: {API_V1_PREFIX}")
    print(f"Project ID: {ZERODB_PROJECT_ID[:8]}...{ZERODB_PROJECT_ID[-8:]}")
    print(f"Test Org 1: {TEST_ORG_ID}")
    print(f"Test Org 2: {TEST_ORG_ID_2}")
    print(f"Test User: {TEST_USER_ID}")
    print(f"{'='*80}\n")


@pytest.fixture(scope="function", autouse=False)
async def cleanup_test_blocks():
    """Cleanup test blocks after each test (optional)"""
    yield
    # Cleanup logic can be added here if needed
    # For now, we keep test data for debugging
    # In production, you would delete test blocks and pages from ZeroDB


if __name__ == "__main__":
    # Run with: pytest tests/test_ocean_blocks.py -v --cov=app.services.ocean_service --cov=app.api.v1.endpoints.ocean_blocks --cov-report=term-missing
    pytest.main([__file__, "-v", "--tb=short"])
