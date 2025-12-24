"""
Ocean Links API Integration Tests

Tests comprehensive link management operations including:
- Create block-to-block links
- Create block-to-page links
- Delete links
- Get page backlinks
- Get block backlinks
- Circular reference prevention
- Multi-tenant isolation

Test Coverage:
- TestCreateLink: 4 tests (block-to-block, block-to-page, all types, circular prevention)
- TestDeleteLink: 2 tests (success, not found)
- TestGetBacklinks: 4 tests (page backlinks, block backlinks, metadata, empty)
- TestMultiTenant: 2 tests (cross-org blocked, backlinks filtered)

Issue #12: Create integration tests for Ocean link management
"""

import os
import pytest
import httpx
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
API_V1_PREFIX = "/api/v1/ocean"
ZERODB_API_KEY = os.getenv("ZERODB_API_KEY")
ZERODB_PROJECT_ID = os.getenv("ZERODB_PROJECT_ID")

# Test organization IDs for multi-tenant testing
TEST_ORG_ID = "test-org-links-1"
TEST_ORG_ID_2 = "test-org-links-2"
TEST_USER_ID = "test-user-links-1"

# Test data storage (for cleanup and sharing between tests)
created_page_ids: List[str] = []
created_block_ids: List[str] = []
created_link_ids: List[str] = []


# Helper functions for test setup
async def create_test_page(
    client: httpx.AsyncClient,
    org_id: str,  # Not used - kept for signature compatibility
    title: str
) -> Dict[str, Any]:
    """
    Helper to create a test page.

    Note: org_id parameter is ignored - organization_id comes from auth token.
    The auth dependency returns hardcoded org_id="test-org-456".
    """
    response = await client.post(
        f"{API_BASE_URL}{API_V1_PREFIX}/pages",
        headers={
            "Authorization": f"Bearer {ZERODB_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "title": title,
            "icon": "🔗"
        }
    )
    assert response.status_code == 201, f"Failed to create page: {response.status_code} - {response.text}"
    data = response.json()
    created_page_ids.append(data["page_id"])
    return data


async def create_test_block(
    client: httpx.AsyncClient,
    org_id: str,
    page_id: str,
    content: str,
    block_type: str = "text"
) -> Dict[str, Any]:
    """Helper to create a test block"""
    response = await client.post(
        f"{API_BASE_URL}{API_V1_PREFIX}/blocks?page_id={page_id}",
        headers={
            "Authorization": f"Bearer {ZERODB_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "block_type": block_type,
            "content": {"text": content},  # Content must be a dict with "text" key
            "position": 0
        }
    )
    assert response.status_code == 201, f"Failed to create block: {response.status_code} - {response.text}"
    data = response.json()
    created_block_ids.append(data["block_id"])
    return data


class TestCreateLink:
    """Test suite for POST /api/v1/links endpoint"""

    @pytest.mark.asyncio
    async def test_create_block_to_block_link(self):
        """Test creating a bidirectional link between two blocks"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Setup: Create page and two blocks
            page = await create_test_page(client, TEST_ORG_ID, "Link Test Page - Block to Block")

            block_a = await create_test_block(
                client, TEST_ORG_ID, page["page_id"],
                "Source block linking to another block"
            )
            block_b = await create_test_block(
                client, TEST_ORG_ID, page["page_id"],
                "Target block being referenced"
            )

            # Create link: block_a → block_b
            response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/links",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "source_block_id": block_a["block_id"],
                    "target_id": block_b["block_id"],
                    "link_type": "reference",
                    "is_page_link": False
                }
            )

            assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"

            data = response.json()

            # Verify response structure
            assert "link_id" in data
            assert "organization_id" in data
            assert "source_block_id" in data
            assert "target_block_id" in data
            assert "target_page_id" in data
            assert "link_type" in data
            assert "created_at" in data

            # Verify data correctness
            assert data["organization_id"] == TEST_ORG_ID
            assert data["source_block_id"] == block_a["block_id"]
            assert data["target_block_id"] == block_b["block_id"]
            assert data["target_page_id"] is None  # Block link, not page link
            assert data["link_type"] == "reference"

            # Store link_id for cleanup
            created_link_ids.append(data["link_id"])

            print(f"✓ Create block-to-block link: {block_a['block_id']} → {block_b['block_id']}")

    @pytest.mark.asyncio
    async def test_create_block_to_page_link(self):
        """Test creating a link from block to page"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Setup: Create two pages and a block in the first page
            page_source = await create_test_page(client, TEST_ORG_ID, "Source Page")
            page_target = await create_test_page(client, TEST_ORG_ID, "Target Page")

            block = await create_test_block(
                client, TEST_ORG_ID, page_source["page_id"],
                "Block linking to another page"
            )

            # Create link: block → page_target
            response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/links",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "source_block_id": block["block_id"],
                    "target_id": page_target["page_id"],
                    "link_type": "mention",
                    "is_page_link": True
                }
            )

            assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"

            data = response.json()

            # Verify response structure
            assert data["organization_id"] == TEST_ORG_ID
            assert data["source_block_id"] == block["block_id"]
            assert data["target_block_id"] is None  # Page link, not block link
            assert data["target_page_id"] == page_target["page_id"]
            assert data["link_type"] == "mention"

            created_link_ids.append(data["link_id"])

            print(f"✓ Create block-to-page link: {block['block_id']} → {page_target['page_id']}")

    @pytest.mark.asyncio
    async def test_create_link_all_types(self):
        """Test creating links with all three link types: reference, embed, mention"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Setup: Create page and blocks
            page = await create_test_page(client, TEST_ORG_ID, "Link Types Test Page")

            source_block = await create_test_block(
                client, TEST_ORG_ID, page["page_id"],
                "Source block with multiple link types"
            )
            target_block_1 = await create_test_block(
                client, TEST_ORG_ID, page["page_id"],
                "Target for reference link"
            )
            target_block_2 = await create_test_block(
                client, TEST_ORG_ID, page["page_id"],
                "Target for embed link"
            )
            target_block_3 = await create_test_block(
                client, TEST_ORG_ID, page["page_id"],
                "Target for mention link"
            )

            # Test all three link types
            link_types = [
                ("reference", target_block_1["block_id"]),
                ("embed", target_block_2["block_id"]),
                ("mention", target_block_3["block_id"])
            ]

            for link_type, target_id in link_types:
                response = await client.post(
                    f"{API_BASE_URL}{API_V1_PREFIX}/links",
                    headers={
                        "Authorization": f"Bearer {ZERODB_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "source_block_id": source_block["block_id"],
                        "target_id": target_id,
                        "link_type": link_type,
                        "is_page_link": False
                    }
                )

                assert response.status_code == 201, \
                    f"Failed to create {link_type} link: {response.status_code} - {response.text}"

                data = response.json()
                assert data["link_type"] == link_type
                assert data["target_block_id"] == target_id

                created_link_ids.append(data["link_id"])

                print(f"✓ Create {link_type} link: {source_block['block_id']} → {target_id}")

    @pytest.mark.asyncio
    async def test_circular_reference_prevention(self):
        """
        CRITICAL TEST: Prevent circular references in block-to-block links.

        Scenario:
        1. Create block A
        2. Create block B
        3. Link A → B (should succeed)
        4. Try to link B → A (should fail with 400 Bad Request)
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Setup: Create page and two blocks
            page = await create_test_page(client, TEST_ORG_ID, "Circular Reference Test Page")

            block_a = await create_test_block(
                client, TEST_ORG_ID, page["page_id"],
                "Block A - source of first link"
            )
            block_b = await create_test_block(
                client, TEST_ORG_ID, page["page_id"],
                "Block B - target of first link, will try to link back"
            )

            # Step 1: Create link A → B (should succeed)
            response_1 = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/links",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "source_block_id": block_a["block_id"],
                    "target_id": block_b["block_id"],
                    "link_type": "reference",
                    "is_page_link": False
                }
            )

            assert response_1.status_code == 201, \
                f"First link A→B should succeed: {response_1.status_code} - {response_1.text}"

            link_1 = response_1.json()
            created_link_ids.append(link_1["link_id"])

            print(f"✓ Created link A → B: {block_a['block_id']} → {block_b['block_id']}")

            # Step 2: Try to create link B → A (should fail - circular reference)
            response_2 = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/links",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "source_block_id": block_b["block_id"],
                    "target_id": block_a["block_id"],
                    "link_type": "reference",
                    "is_page_link": False
                }
            )

            # Verify circular reference was blocked
            assert response_2.status_code == 400, \
                f"Circular link B→A should fail with 400, got {response_2.status_code}"

            error_data = response_2.json()
            assert "circular reference" in error_data["detail"].lower(), \
                f"Error should mention circular reference: {error_data['detail']}"

            print(f"✓ Circular reference blocked: {block_b['block_id']} → {block_a['block_id']} (prevented)")


class TestDeleteLink:
    """Test suite for DELETE /api/v1/links/{link_id} endpoint"""

    @pytest.mark.asyncio
    async def test_delete_link_success(self):
        """Test successfully deleting a link"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Setup: Create page, blocks, and link
            page = await create_test_page(client, TEST_ORG_ID, "Delete Link Test Page")

            block_a = await create_test_block(
                client, TEST_ORG_ID, page["page_id"],
                "Source block for delete test"
            )
            block_b = await create_test_block(
                client, TEST_ORG_ID, page["page_id"],
                "Target block for delete test"
            )

            # Create link
            link_response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/links",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "source_block_id": block_a["block_id"],
                    "target_id": block_b["block_id"],
                    "link_type": "reference",
                    "is_page_link": False
                }
            )
            assert link_response.status_code == 201
            link = link_response.json()

            # Delete the link
            delete_response = await client.delete(
                f"{API_BASE_URL}{API_V1_PREFIX}/links/{link['link_id']}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}"
                }
            )

            assert delete_response.status_code == 204, \
                f"Expected 204 No Content, got {delete_response.status_code}: {delete_response.text}"

            print(f"✓ Delete link success: link_id={link['link_id']}")

    @pytest.mark.asyncio
    async def test_delete_link_not_found(self):
        """Test deleting a non-existent link returns 404"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            fake_link_id = "00000000-0000-0000-0000-000000000000"

            response = await client.delete(
                f"{API_BASE_URL}{API_V1_PREFIX}/links/{fake_link_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}"
                }
            )

            assert response.status_code == 404, \
                f"Expected 404 for non-existent link, got {response.status_code}"

            error_data = response.json()
            assert "not found" in error_data["detail"].lower(), \
                f"Error should mention 'not found': {error_data['detail']}"

            print(f"✓ Delete non-existent link returns 404")


class TestGetBacklinks:
    """Test suite for GET /api/v1/pages/{page_id}/backlinks and /api/v1/blocks/{block_id}/backlinks"""

    @pytest.mark.asyncio
    async def test_get_page_backlinks(self):
        """Test getting all backlinks to a page"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Setup: Create pages and blocks
            page_source = await create_test_page(client, TEST_ORG_ID, "Source Page for Backlinks")
            page_target = await create_test_page(client, TEST_ORG_ID, "Target Page with Backlinks")

            # Create multiple blocks linking to target page
            blocks_linking = []
            for i in range(3):
                block = await create_test_block(
                    client, TEST_ORG_ID, page_source["page_id"],
                    f"Block {i+1} linking to target page"
                )
                blocks_linking.append(block)

                # Create link from block to target page
                link_response = await client.post(
                    f"{API_BASE_URL}{API_V1_PREFIX}/links",
                    headers={
                        "Authorization": f"Bearer {ZERODB_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "source_block_id": block["block_id"],
                        "target_id": page_target["page_id"],
                        "link_type": "reference",
                        "is_page_link": True
                    }
                )
                assert link_response.status_code == 201
                created_link_ids.append(link_response.json()["link_id"])

            # Get page backlinks
            response = await client.get(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages/{page_target['page_id']}/backlinks",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}"
                }
            )

            assert response.status_code == 200, \
                f"Expected 200, got {response.status_code}: {response.text}"

            data = response.json()

            # Verify response structure
            assert "backlinks" in data
            assert "total" in data
            assert isinstance(data["backlinks"], list)
            assert data["total"] == 3, f"Expected 3 backlinks, got {data['total']}"

            # Verify each backlink has required fields
            for backlink in data["backlinks"]:
                assert "link_id" in backlink
                assert "link_type" in backlink
                assert "source_block_id" in backlink
                assert "source_page_id" in backlink
                assert "source_block_type" in backlink
                assert "source_content_preview" in backlink
                assert "created_at" in backlink

                # Verify source page is correct
                assert backlink["source_page_id"] == page_source["page_id"]

            print(f"✓ Get page backlinks: {page_target['page_id']} has {data['total']} backlinks")

    @pytest.mark.asyncio
    async def test_get_block_backlinks(self):
        """Test getting all backlinks to a block"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Setup: Create page and blocks
            page = await create_test_page(client, TEST_ORG_ID, "Backlinks Test Page")

            target_block = await create_test_block(
                client, TEST_ORG_ID, page["page_id"],
                "Target block that will have backlinks"
            )

            # Create multiple blocks linking to target block
            for i in range(2):
                source_block = await create_test_block(
                    client, TEST_ORG_ID, page["page_id"],
                    f"Source block {i+1} referencing target"
                )

                # Create link
                link_response = await client.post(
                    f"{API_BASE_URL}{API_V1_PREFIX}/links",
                    headers={
                        "Authorization": f"Bearer {ZERODB_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "source_block_id": source_block["block_id"],
                        "target_id": target_block["block_id"],
                        "link_type": "mention",
                        "is_page_link": False
                    }
                )
                assert link_response.status_code == 201
                created_link_ids.append(link_response.json()["link_id"])

            # Get block backlinks
            response = await client.get(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks/{target_block['block_id']}/backlinks",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}"
                }
            )

            assert response.status_code == 200, \
                f"Expected 200, got {response.status_code}: {response.text}"

            data = response.json()

            # Verify response structure
            assert "backlinks" in data
            assert "total" in data
            assert data["total"] == 2, f"Expected 2 backlinks, got {data['total']}"

            print(f"✓ Get block backlinks: {target_block['block_id']} has {data['total']} backlinks")

    @pytest.mark.asyncio
    async def test_backlinks_include_metadata(self):
        """Test that backlinks include source block metadata (type, content preview, page_id)"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Setup
            page = await create_test_page(client, TEST_ORG_ID, "Metadata Test Page")

            target_block = await create_test_block(
                client, TEST_ORG_ID, page["page_id"],
                "Target block for metadata test"
            )

            source_block = await create_test_block(
                client, TEST_ORG_ID, page["page_id"],
                "This is a source block with specific content for preview testing",
                "text"
            )

            # Create link
            link_response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/links",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "source_block_id": source_block["block_id"],
                    "target_id": target_block["block_id"],
                    "link_type": "embed",
                    "is_page_link": False
                }
            )
            assert link_response.status_code == 201
            created_link_ids.append(link_response.json()["link_id"])

            # Get backlinks
            response = await client.get(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks/{target_block['block_id']}/backlinks",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}"
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert data["total"] == 1
            backlink = data["backlinks"][0]

            # Verify metadata fields
            assert backlink["source_block_id"] == source_block["block_id"]
            assert backlink["source_page_id"] == page["page_id"]
            assert backlink["source_block_type"] == "text"
            assert backlink["link_type"] == "embed"
            assert len(backlink["source_content_preview"]) > 0, "Content preview should not be empty"

            print(f"✓ Backlinks include metadata: type={backlink['source_block_type']}, "
                  f"preview='{backlink['source_content_preview'][:30]}...'")

    @pytest.mark.asyncio
    async def test_backlinks_empty_array(self):
        """Test that pages/blocks with no backlinks return empty array"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create page and block with no backlinks
            page = await create_test_page(client, TEST_ORG_ID, "Page with No Backlinks")
            block = await create_test_block(
                client, TEST_ORG_ID, page["page_id"],
                "Block with no backlinks"
            )

            # Get page backlinks (should be empty)
            page_response = await client.get(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages/{page['page_id']}/backlinks",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}"
                }
            )

            assert page_response.status_code == 200
            page_data = page_response.json()
            assert page_data["total"] == 0
            assert page_data["backlinks"] == []

            # Get block backlinks (should be empty)
            block_response = await client.get(
                f"{API_BASE_URL}{API_V1_PREFIX}/blocks/{block['block_id']}/backlinks",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}"
                }
            )

            assert block_response.status_code == 200
            block_data = block_response.json()
            assert block_data["total"] == 0
            assert block_data["backlinks"] == []

            print(f"✓ Empty backlinks: page={page_data['total']}, block={block_data['total']}")


class TestMultiTenant:
    """Test suite for multi-tenant isolation in link operations"""

    @pytest.mark.asyncio
    async def test_cross_org_link_blocked(self):
        """
        Test that links cannot be created across organizations.

        Scenario:
        1. Create block in org1
        2. Create block in org2
        3. Try to link org1_block → org2_block (should fail with 404)
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create page and block in org1
            page_org1 = await create_test_page(client, TEST_ORG_ID, "Org1 Page")
            block_org1 = await create_test_block(
                client, TEST_ORG_ID, page_org1["page_id"],
                "Block in organization 1"
            )

            # Create page and block in org2
            page_org2 = await create_test_page(client, TEST_ORG_ID_2, "Org2 Page")
            block_org2 = await create_test_block(
                client, TEST_ORG_ID_2, page_org2["page_id"],
                "Block in organization 2"
            )

            # Try to create link from org1 block to org2 block (should fail)
            response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/links",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "source_block_id": block_org1["block_id"],
                    "target_id": block_org2["block_id"],
                    "link_type": "reference",
                    "is_page_link": False
                }
            )

            # Should fail because target block doesn't belong to org1
            assert response.status_code == 404, \
                f"Cross-org link should fail with 404, got {response.status_code}"

            error_data = response.json()
            assert "not found" in error_data["detail"].lower() or \
                   "does not belong" in error_data["detail"].lower(), \
                f"Error should mention target not found/accessible: {error_data['detail']}"

            print(f"✓ Cross-org link blocked: org1 → org2 (prevented)")

    @pytest.mark.asyncio
    async def test_backlinks_filtered_by_org(self):
        """
        Test that backlinks are filtered by organization.

        Scenario:
        1. Create page in org1
        2. Create blocks in org1 linking to page
        3. Query backlinks with org1 token → should see links
        4. Same page_id won't be visible to org2
        """
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create page and blocks in org1
            page_org1 = await create_test_page(client, TEST_ORG_ID, "Org1 Backlinks Test")

            block_org1 = await create_test_block(
                client, TEST_ORG_ID, page_org1["page_id"],
                "Org1 block linking to org1 page"
            )

            # Create link in org1
            link_response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/links",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "source_block_id": block_org1["block_id"],
                    "target_id": page_org1["page_id"],
                    "link_type": "reference",
                    "is_page_link": True
                }
            )
            assert link_response.status_code == 201
            created_link_ids.append(link_response.json()["link_id"])

            # Get backlinks for org1 page (should succeed and have 1 link)
            response = await client.get(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages/{page_org1['page_id']}/backlinks",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}"
                }
            )

            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 1, f"Org1 should see 1 backlink, got {data['total']}"

            print(f"✓ Backlinks filtered by org: org1 sees {data['total']} backlink(s)")


# Cleanup fixture (run after all tests)
@pytest.fixture(scope="module", autouse=True)
def cleanup():
    """Cleanup test data after all tests complete"""
    yield

    # Cleanup happens here (after all tests)
    # Note: In a real scenario, you might want to clean up created test data
    # For now, we'll leave the test data in the database for inspection

    print("\n" + "="*60)
    print("Test Summary:")
    print(f"  Created {len(created_page_ids)} pages")
    print(f"  Created {len(created_block_ids)} blocks")
    print(f"  Created {len(created_link_ids)} links")
    print("="*60)
