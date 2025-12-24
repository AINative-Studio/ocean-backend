"""
Ocean Pages API Integration Tests

Tests comprehensive CRUD operations for Ocean pages with multi-tenant isolation.

Test Coverage:
- Create page operations (basic, nested, validation)
- Get page operations (by ID, not found, multi-tenant)
- List pages operations (basic, pagination, filtering)
- Update page operations (update fields, not found)
- Delete page operations (soft delete, not found)
- Move page operations (change parent, move to root)
- Multi-tenant isolation enforcement

Issue #6: Write integration tests for pages
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
API_V1_PREFIX = "/api/v1"
ZERODB_API_KEY = os.getenv("ZERODB_API_KEY")
ZERODB_PROJECT_ID = os.getenv("ZERODB_PROJECT_ID")

# Test organization IDs for multi-tenant testing
TEST_ORG_ID = "test-org-1"
TEST_ORG_ID_2 = "test-org-2"
TEST_USER_ID = "test-user-1"

# Test data storage (for cleanup)
created_page_ids: List[str] = []


class TestCreatePage:
    """Test suite for POST /api/v1/pages endpoint"""

    @pytest.mark.asyncio
    async def test_create_page_success(self):
        """Test creating a basic page successfully"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "organization_id": TEST_ORG_ID,
                    "user_id": TEST_USER_ID,
                    "title": "Test Page - Basic",
                    "icon": "📝",
                    "metadata": {
                        "test": "basic_create",
                        "created_by": "test_suite"
                    }
                }
            )

            assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"

            data = response.json()

            # Verify response structure
            assert "page_id" in data
            assert "organization_id" in data
            assert "user_id" in data
            assert "title" in data
            assert "icon" in data
            assert "created_at" in data
            assert "updated_at" in data

            # Verify data correctness
            assert data["organization_id"] == TEST_ORG_ID
            assert data["user_id"] == TEST_USER_ID
            assert data["title"] == "Test Page - Basic"
            assert data["icon"] == "📝"
            assert data["is_archived"] is False
            assert data["is_favorite"] is False
            assert data["position"] >= 0

            # Store page_id for cleanup
            created_page_ids.append(data["page_id"])

            print(f"✓ Create basic page: page_id={data['page_id']}, position={data['position']}")

    @pytest.mark.asyncio
    async def test_create_nested_page(self):
        """Test creating a nested page with parent_page_id"""
        # First, create a parent page
        async with httpx.AsyncClient(timeout=30.0) as client:
            parent_response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "organization_id": TEST_ORG_ID,
                    "user_id": TEST_USER_ID,
                    "title": "Parent Page",
                    "icon": "📁"
                }
            )

            assert parent_response.status_code == 201
            parent_data = parent_response.json()
            parent_page_id = parent_data["page_id"]
            created_page_ids.append(parent_page_id)

            # Now create a child page
            child_response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "organization_id": TEST_ORG_ID,
                    "user_id": TEST_USER_ID,
                    "title": "Child Page",
                    "icon": "📄",
                    "parent_page_id": parent_page_id
                }
            )

            assert child_response.status_code == 201
            child_data = child_response.json()

            # Verify parent relationship
            assert child_data["parent_page_id"] == parent_page_id
            assert child_data["position"] >= 0

            created_page_ids.append(child_data["page_id"])

            print(f"✓ Create nested page: parent={parent_page_id}, child={child_data['page_id']}")

    @pytest.mark.asyncio
    async def test_create_page_validation(self):
        """Test page creation with missing required fields"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Missing title
            response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "organization_id": TEST_ORG_ID,
                    "user_id": TEST_USER_ID
                    # No title
                }
            )

            # Should return validation error (400 or 422)
            assert response.status_code in [400, 422], f"Expected validation error, got {response.status_code}"

            # Missing organization_id
            response2 = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "user_id": TEST_USER_ID,
                    "title": "Test"
                    # No organization_id
                }
            )

            assert response2.status_code in [400, 422]

            print(f"✓ Create page validation errors: {response.status_code}, {response2.status_code}")


class TestGetPage:
    """Test suite for GET /api/v1/pages/{page_id} endpoint"""

    @pytest.mark.asyncio
    async def test_get_page_by_id(self):
        """Test retrieving a page by ID"""
        # First create a page
        async with httpx.AsyncClient(timeout=30.0) as client:
            create_response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "organization_id": TEST_ORG_ID,
                    "user_id": TEST_USER_ID,
                    "title": "Test Page for Retrieval",
                    "icon": "🔍"
                }
            )

            assert create_response.status_code == 201
            page_data = create_response.json()
            page_id = page_data["page_id"]
            created_page_ids.append(page_id)

            # Now retrieve the page
            get_response = await client.get(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages/{page_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}"
                },
                params={"organization_id": TEST_ORG_ID}
            )

            assert get_response.status_code == 200
            retrieved_data = get_response.json()

            # Verify data matches
            assert retrieved_data["page_id"] == page_id
            assert retrieved_data["title"] == "Test Page for Retrieval"
            assert retrieved_data["icon"] == "🔍"
            assert retrieved_data["organization_id"] == TEST_ORG_ID

            print(f"✓ Get page by ID: page_id={page_id}, title={retrieved_data['title']}")

    @pytest.mark.asyncio
    async def test_get_page_not_found(self):
        """Test retrieving a non-existent page returns 404"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages/non-existent-page-id-xyz",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}"
                },
                params={"organization_id": TEST_ORG_ID}
            )

            assert response.status_code == 404, f"Expected 404, got {response.status_code}"

            data = response.json()
            assert "detail" in data or "error" in data

            print(f"✓ Get page not found: {response.status_code}")

    @pytest.mark.asyncio
    async def test_get_page_wrong_org(self):
        """Test multi-tenant isolation - cannot access other org's pages"""
        # Create page in ORG 1
        async with httpx.AsyncClient(timeout=30.0) as client:
            create_response = await client.post(
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

            assert create_response.status_code == 201
            page_data = create_response.json()
            page_id = page_data["page_id"]
            created_page_ids.append(page_id)

            # Try to access with ORG 2
            get_response = await client.get(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages/{page_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}"
                },
                params={"organization_id": TEST_ORG_ID_2}  # Different org
            )

            # Should return 404 (not found) due to multi-tenant isolation
            assert get_response.status_code == 404, f"Expected 404, got {get_response.status_code}"

            print(f"✓ Multi-tenant isolation enforced on GET: {get_response.status_code}")


class TestListPages:
    """Test suite for GET /api/v1/pages endpoint"""

    @pytest.mark.asyncio
    async def test_list_pages(self):
        """Test listing all pages for an organization"""
        # Create a few test pages
        async with httpx.AsyncClient(timeout=30.0) as client:
            for i in range(3):
                create_response = await client.post(
                    f"{API_BASE_URL}{API_V1_PREFIX}/pages",
                    headers={
                        "Authorization": f"Bearer {ZERODB_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "organization_id": TEST_ORG_ID,
                        "user_id": TEST_USER_ID,
                        "title": f"List Test Page {i+1}"
                    }
                )
                assert create_response.status_code == 201
                created_page_ids.append(create_response.json()["page_id"])

            # Now list pages
            list_response = await client.get(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}"
                },
                params={"organization_id": TEST_ORG_ID}
            )

            assert list_response.status_code == 200
            data = list_response.json()

            # Should return array of pages
            assert isinstance(data, list) or "pages" in data

            pages = data if isinstance(data, list) else data["pages"]

            # Should have at least the 3 we created
            assert len(pages) >= 3

            # Verify all pages belong to TEST_ORG_ID
            for page in pages:
                assert page["organization_id"] == TEST_ORG_ID

            print(f"✓ List pages: {len(pages)} pages found for organization")

    @pytest.mark.asyncio
    async def test_list_pages_pagination(self):
        """Test pagination with limit and offset"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create 5 pages for pagination test
            for i in range(5):
                create_response = await client.post(
                    f"{API_BASE_URL}{API_V1_PREFIX}/pages",
                    headers={
                        "Authorization": f"Bearer {ZERODB_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "organization_id": TEST_ORG_ID,
                        "user_id": TEST_USER_ID,
                        "title": f"Pagination Test Page {i+1}"
                    }
                )
                assert create_response.status_code == 201
                created_page_ids.append(create_response.json()["page_id"])

            # Get first 2 pages
            page1_response = await client.get(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}"
                },
                params={
                    "organization_id": TEST_ORG_ID,
                    "limit": 2,
                    "offset": 0
                }
            )

            assert page1_response.status_code == 200
            page1_data = page1_response.json()
            pages_page1 = page1_data if isinstance(page1_data, list) else page1_data["pages"]

            # Get next 2 pages
            page2_response = await client.get(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}"
                },
                params={
                    "organization_id": TEST_ORG_ID,
                    "limit": 2,
                    "offset": 2
                }
            )

            assert page2_response.status_code == 200
            page2_data = page2_response.json()
            pages_page2 = page2_data if isinstance(page2_data, list) else page2_data["pages"]

            # Verify pagination works (pages should be different)
            page1_ids = {p["page_id"] for p in pages_page1}
            page2_ids = {p["page_id"] for p in pages_page2}

            assert len(page1_ids.intersection(page2_ids)) == 0, "Pagination returned duplicate pages"

            print(f"✓ List pages pagination: page1={len(pages_page1)}, page2={len(pages_page2)}, no duplicates")

    @pytest.mark.asyncio
    async def test_list_pages_filters(self):
        """Test filtering by parent_id, is_archived, is_favorite"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create parent page
            parent_response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "organization_id": TEST_ORG_ID,
                    "user_id": TEST_USER_ID,
                    "title": "Filter Test Parent"
                }
            )
            assert parent_response.status_code == 201
            parent_id = parent_response.json()["page_id"]
            created_page_ids.append(parent_id)

            # Create child pages
            for i in range(2):
                child_response = await client.post(
                    f"{API_BASE_URL}{API_V1_PREFIX}/pages",
                    headers={
                        "Authorization": f"Bearer {ZERODB_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "organization_id": TEST_ORG_ID,
                        "user_id": TEST_USER_ID,
                        "title": f"Filter Test Child {i+1}",
                        "parent_page_id": parent_id
                    }
                )
                assert child_response.status_code == 201
                created_page_ids.append(child_response.json()["page_id"])

            # Filter by parent_page_id
            filtered_response = await client.get(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}"
                },
                params={
                    "organization_id": TEST_ORG_ID,
                    "parent_page_id": parent_id
                }
            )

            assert filtered_response.status_code == 200
            filtered_data = filtered_response.json()
            filtered_pages = filtered_data if isinstance(filtered_data, list) else filtered_data["pages"]

            # Should only return child pages
            assert len(filtered_pages) == 2

            for page in filtered_pages:
                assert page["parent_page_id"] == parent_id

            print(f"✓ List pages filters: {len(filtered_pages)} child pages found for parent {parent_id}")


class TestUpdatePage:
    """Test suite for PATCH /api/v1/pages/{page_id} endpoint"""

    @pytest.mark.asyncio
    async def test_update_page(self):
        """Test updating page fields (title, icon, is_favorite)"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create page
            create_response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "organization_id": TEST_ORG_ID,
                    "user_id": TEST_USER_ID,
                    "title": "Original Title",
                    "icon": "📝"
                }
            )
            assert create_response.status_code == 201
            page_id = create_response.json()["page_id"]
            created_page_ids.append(page_id)

            # Update page
            update_response = await client.patch(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages/{page_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "organization_id": TEST_ORG_ID,
                    "title": "Updated Title",
                    "icon": "✨",
                    "is_favorite": True
                }
            )

            assert update_response.status_code == 200
            updated_data = update_response.json()

            # Verify updates
            assert updated_data["title"] == "Updated Title"
            assert updated_data["icon"] == "✨"
            assert updated_data["is_favorite"] is True
            assert updated_data["page_id"] == page_id

            # Verify updated_at changed
            original_updated_at = create_response.json()["updated_at"]
            assert updated_data["updated_at"] != original_updated_at

            print(f"✓ Update page: title, icon, favorite updated successfully")

    @pytest.mark.asyncio
    async def test_update_page_not_found(self):
        """Test updating a non-existent page returns 404"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.patch(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages/non-existent-page-id-xyz",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "organization_id": TEST_ORG_ID,
                    "title": "Updated Title"
                }
            )

            assert response.status_code == 404, f"Expected 404, got {response.status_code}"

            print(f"✓ Update page not found: {response.status_code}")


class TestDeletePage:
    """Test suite for DELETE /api/v1/pages/{page_id} endpoint"""

    @pytest.mark.asyncio
    async def test_delete_page(self):
        """Test soft deleting a page (is_archived=True)"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create page
            create_response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "organization_id": TEST_ORG_ID,
                    "user_id": TEST_USER_ID,
                    "title": "Page to Delete"
                }
            )
            assert create_response.status_code == 201
            page_id = create_response.json()["page_id"]
            created_page_ids.append(page_id)

            # Delete page
            delete_response = await client.delete(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages/{page_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}"
                },
                params={"organization_id": TEST_ORG_ID}
            )

            assert delete_response.status_code in [200, 204], f"Expected 200/204, got {delete_response.status_code}"

            # Verify page is archived (not actually deleted)
            get_response = await client.get(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages/{page_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}"
                },
                params={
                    "organization_id": TEST_ORG_ID,
                    "include_archived": True  # Need to explicitly include archived
                }
            )

            if get_response.status_code == 200:
                page_data = get_response.json()
                assert page_data["is_archived"] is True, "Page should be archived, not deleted"

            print(f"✓ Delete page: soft delete (is_archived=True)")

    @pytest.mark.asyncio
    async def test_delete_page_not_found(self):
        """Test deleting a non-existent page returns 404"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.delete(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages/non-existent-page-id-xyz",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}"
                },
                params={"organization_id": TEST_ORG_ID}
            )

            assert response.status_code == 404, f"Expected 404, got {response.status_code}"

            print(f"✓ Delete page not found: {response.status_code}")


class TestMovePage:
    """Test suite for PATCH /api/v1/pages/{page_id}/move endpoint"""

    @pytest.mark.asyncio
    async def test_move_page(self):
        """Test moving a page to a new parent"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create parent 1
            parent1_response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "organization_id": TEST_ORG_ID,
                    "user_id": TEST_USER_ID,
                    "title": "Parent 1"
                }
            )
            assert parent1_response.status_code == 201
            parent1_id = parent1_response.json()["page_id"]
            created_page_ids.append(parent1_id)

            # Create parent 2
            parent2_response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "organization_id": TEST_ORG_ID,
                    "user_id": TEST_USER_ID,
                    "title": "Parent 2"
                }
            )
            assert parent2_response.status_code == 201
            parent2_id = parent2_response.json()["page_id"]
            created_page_ids.append(parent2_id)

            # Create child under parent 1
            child_response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "organization_id": TEST_ORG_ID,
                    "user_id": TEST_USER_ID,
                    "title": "Child to Move",
                    "parent_page_id": parent1_id
                }
            )
            assert child_response.status_code == 201
            child_id = child_response.json()["page_id"]
            created_page_ids.append(child_id)

            # Move child to parent 2
            move_response = await client.patch(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages/{child_id}/move",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "organization_id": TEST_ORG_ID,
                    "new_parent_id": parent2_id
                }
            )

            assert move_response.status_code == 200
            moved_data = move_response.json()

            # Verify parent changed
            assert moved_data["parent_page_id"] == parent2_id

            print(f"✓ Move page: child moved from {parent1_id} to {parent2_id}")

    @pytest.mark.asyncio
    async def test_move_page_to_root(self):
        """Test moving a page to root level (no parent)"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create parent
            parent_response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "organization_id": TEST_ORG_ID,
                    "user_id": TEST_USER_ID,
                    "title": "Parent for Root Move"
                }
            )
            assert parent_response.status_code == 201
            parent_id = parent_response.json()["page_id"]
            created_page_ids.append(parent_id)

            # Create child
            child_response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "organization_id": TEST_ORG_ID,
                    "user_id": TEST_USER_ID,
                    "title": "Child to Move to Root",
                    "parent_page_id": parent_id
                }
            )
            assert child_response.status_code == 201
            child_id = child_response.json()["page_id"]
            created_page_ids.append(child_id)

            # Move to root (null parent)
            move_response = await client.patch(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages/{child_id}/move",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "organization_id": TEST_ORG_ID,
                    "new_parent_id": None
                }
            )

            assert move_response.status_code == 200
            moved_data = move_response.json()

            # Verify page is now at root level
            assert moved_data["parent_page_id"] is None

            print(f"✓ Move page to root: child moved to root level")


class TestMultiTenant:
    """Test suite for multi-tenant isolation enforcement"""

    @pytest.mark.asyncio
    async def test_multi_tenant_isolation(self):
        """Test that organization boundaries are enforced across all operations"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create page in ORG 1
            org1_response = await client.post(
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
            assert org1_response.status_code == 201
            org1_page_id = org1_response.json()["page_id"]
            created_page_ids.append(org1_page_id)

            # Create page in ORG 2
            org2_response = await client.post(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "organization_id": TEST_ORG_ID_2,
                    "user_id": TEST_USER_ID,
                    "title": "Org 2 Private Page"
                }
            )
            assert org2_response.status_code == 201
            org2_page_id = org2_response.json()["page_id"]
            created_page_ids.append(org2_page_id)

            # Test 1: ORG 2 cannot access ORG 1's page
            get_cross_org = await client.get(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages/{org1_page_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}"
                },
                params={"organization_id": TEST_ORG_ID_2}
            )
            assert get_cross_org.status_code == 404, "Org 2 should not access Org 1's page"

            # Test 2: ORG 1's list should not include ORG 2's pages
            list_org1 = await client.get(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}"
                },
                params={"organization_id": TEST_ORG_ID}
            )
            assert list_org1.status_code == 200
            org1_pages = list_org1.json()
            org1_pages_list = org1_pages if isinstance(org1_pages, list) else org1_pages["pages"]

            org1_page_ids = {p["page_id"] for p in org1_pages_list}
            assert org2_page_id not in org1_page_ids, "Org 1 list should not contain Org 2 pages"

            # Test 3: ORG 2 cannot update ORG 1's page
            update_cross_org = await client.patch(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages/{org1_page_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "organization_id": TEST_ORG_ID_2,
                    "title": "Hacked!"
                }
            )
            assert update_cross_org.status_code == 404, "Org 2 should not update Org 1's page"

            # Test 4: ORG 2 cannot delete ORG 1's page
            delete_cross_org = await client.delete(
                f"{API_BASE_URL}{API_V1_PREFIX}/pages/{org1_page_id}",
                headers={
                    "Authorization": f"Bearer {ZERODB_API_KEY}"
                },
                params={"organization_id": TEST_ORG_ID_2}
            )
            assert delete_cross_org.status_code == 404, "Org 2 should not delete Org 1's page"

            print(f"✓ Multi-tenant isolation: All cross-org operations blocked")


# Pytest configuration and fixtures

@pytest.fixture(scope="session", autouse=True)
def verify_credentials():
    """Verify required credentials before running tests"""
    if not ZERODB_API_KEY:
        pytest.skip("ZERODB_API_KEY not set in environment")
    if not ZERODB_PROJECT_ID:
        pytest.skip("ZERODB_PROJECT_ID not set in environment")

    print(f"\n{'='*80}")
    print(f"Ocean Pages API Test Configuration")
    print(f"{'='*80}")
    print(f"API URL: {API_BASE_URL}")
    print(f"API Version: {API_V1_PREFIX}")
    print(f"Project ID: {ZERODB_PROJECT_ID[:8]}...{ZERODB_PROJECT_ID[-8:]}")
    print(f"Test Org 1: {TEST_ORG_ID}")
    print(f"Test Org 2: {TEST_ORG_ID_2}")
    print(f"Test User: {TEST_USER_ID}")
    print(f"{'='*80}\n")


@pytest.fixture(scope="function", autouse=False)
async def cleanup_test_pages():
    """Cleanup test pages after each test (optional)"""
    yield
    # Cleanup logic can be added here if needed
    # For now, we keep test data for debugging
    # In production, you would delete test pages from ZeroDB


if __name__ == "__main__":
    # Run with: pytest tests/test_ocean_pages.py -v --cov=app --cov-report=term-missing
    pytest.main([__file__, "-v", "--tb=short"])
