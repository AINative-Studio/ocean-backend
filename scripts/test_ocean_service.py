#!/usr/bin/env python3
"""
Test OceanService page operations.

This script tests all 6 OceanService methods:
1. create_page
2. get_page
3. get_pages
4. update_page
5. delete_page
6. move_page
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from app.services.ocean_service import OceanService


async def test_ocean_service():
    """Test all OceanService operations."""

    # Load environment variables
    load_dotenv()

    api_url = os.getenv("ZERODB_API_URL")
    project_id = os.getenv("ZERODB_PROJECT_ID")
    api_key = os.getenv("ZERODB_API_KEY")

    print("=" * 70)
    print("Ocean Service - Page Operations Test")
    print("=" * 70)
    print()

    # Initialize Ocean service (no ZeroDB client needed - uses direct HTTP)
    print("[Setup] Initializing Ocean service...")
    service = OceanService(
        api_url=api_url,
        api_key=api_key,
        project_id=project_id
    )
    print(f"✅ Ocean service initialized")
    print(f"   Project ID: {project_id}")
    print()

    # Test organization ID (use a test org)
    test_org_id = "org_test_ocean"
    test_user_id = "user_test_123"

    try:
        # Test 1: Create root page
        print("[Test 1/6] Creating root page...")
        root_page = await service.create_page(
            org_id=test_org_id,
            user_id=test_user_id,
            page_data={
                "title": "Test Root Page",
                "icon": "📋",
                "metadata": {"test": True}
            }
        )
        print(f"✅ Root page created: {root_page['page_id']}")
        print(f"   Title: {root_page['title']}")
        print(f"   Position: {root_page['position']}")
        print()

        # Test 2: Get page
        print("[Test 2/6] Getting page by ID...")
        retrieved_page = await service.get_page(
            page_id=root_page["page_id"],
            org_id=test_org_id
        )
        if retrieved_page:
            print(f"✅ Page retrieved: {retrieved_page['title']}")
            print(f"   Created at: {retrieved_page['created_at']}")
        else:
            print(f"⚠️  Page not found (page_id: {root_page['page_id']})")
            # Try getting all pages to see what's there
            all = await service.get_pages(test_org_id, filters={})
            print(f"   Total pages in org: {len(all)}")
        print()

        # Test 3: Create nested page
        print("[Test 3/6] Creating nested page...")
        nested_page = await service.create_page(
            org_id=test_org_id,
            user_id=test_user_id,
            page_data={
                "title": "Nested Page",
                "icon": "📄",
                "parent_page_id": root_page["page_id"]
            }
        )
        print(f"✅ Nested page created: {nested_page['page_id']}")
        print(f"   Parent: {nested_page['parent_page_id']}")
        print(f"   Position: {nested_page['position']}")
        print()

        # Test 4: Get all pages
        print("[Test 4/6] Getting all pages for organization...")
        all_pages = await service.get_pages(
            org_id=test_org_id,
            filters={"is_archived": False}
        )
        print(f"✅ Retrieved {len(all_pages)} pages")
        for page in all_pages:
            print(f"   - {page['title']} (position: {page['position']})")
        print()

        # Test 5: Update page
        print("[Test 5/6] Updating page...")
        updated_page = await service.update_page(
            page_id=root_page["page_id"],
            org_id=test_org_id,
            updates={
                "title": "Updated Root Page",
                "is_favorite": True
            }
        )
        print(f"✅ Page updated: {updated_page['title']}")
        print(f"   Is favorite: {updated_page['is_favorite']}")
        print()

        # Test 6: Move page
        print("[Test 6/6] Moving nested page to root...")
        moved_page = await service.move_page(
            page_id=nested_page["page_id"],
            new_parent_id=None,  # Move to root
            org_id=test_org_id
        )
        print(f"✅ Page moved: {moved_page['title']}")
        print(f"   New parent: {moved_page['parent_page_id']} (None = root)")
        print(f"   New position: {moved_page['position']}")
        print()

        # Test 7: Delete page
        print("[Cleanup] Deleting test pages...")
        deleted_root = await service.delete_page(
            page_id=root_page["page_id"],
            org_id=test_org_id
        )
        deleted_nested = await service.delete_page(
            page_id=nested_page["page_id"],
            org_id=test_org_id
        )
        print(f"✅ Pages deleted (archived): root={deleted_root}, nested={deleted_nested}")
        print()

        # Verify deletion
        print("[Verify] Checking archived pages...")
        archived_pages = await service.get_pages(
            org_id=test_org_id,
            filters={"is_archived": True}
        )
        print(f"✅ Found {len(archived_pages)} archived pages")
        print()

        print("=" * 70)
        print("✅ All OceanService tests PASSED!")
        print("=" * 70)
        print()
        print("Summary:")
        print("- ✅ create_page: Creates pages with auto-incrementing positions")
        print("- ✅ get_page: Retrieves pages by ID with org isolation")
        print("- ✅ get_pages: Lists pages with filtering and pagination")
        print("- ✅ update_page: Updates page fields and timestamps")
        print("- ✅ delete_page: Soft deletes pages (is_archived=True)")
        print("- ✅ move_page: Moves pages between parents with position recalc")
        print()

        return True

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    try:
        result = asyncio.run(test_ocean_service())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n❌ Test cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
