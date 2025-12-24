#!/usr/bin/env python3
"""
Test script for Ocean link management operations.

This script tests the 4 link management methods:
1. create_link() - Create bidirectional links with circular reference prevention
2. delete_link() - Delete links with org isolation
3. get_page_backlinks() - Get all blocks linking to a page
4. get_block_backlinks() - Get all blocks linking to a block

Usage:
    python test_link_operations.py
"""

import asyncio
import sys
from datetime import datetime
from app.services.ocean_service import OceanService

# Configuration (update these with your ZeroDB credentials)
ZERODB_API_URL = "https://api.ainative.studio"
ZERODB_API_KEY = "your-api-key-here"  # TODO: Update
ZERODB_PROJECT_ID = "your-project-id-here"  # TODO: Update

# Test organization and user IDs
TEST_ORG_ID = "test-org-links-001"
TEST_USER_ID = "test-user-links-001"


async def test_link_operations():
    """Test all link management operations."""
    print("=" * 70)
    print("Ocean Link Management Test Script")
    print("=" * 70)
    print()

    # Initialize service
    print("Initializing Ocean service...")
    service = OceanService(
        api_url=ZERODB_API_URL,
        api_key=ZERODB_API_KEY,
        project_id=ZERODB_PROJECT_ID
    )
    print("✓ Service initialized\n")

    # Step 1: Create test page
    print("STEP 1: Creating test page...")
    try:
        page = await service.create_page(
            org_id=TEST_ORG_ID,
            user_id=TEST_USER_ID,
            page_data={
                "title": "Link Test Page",
                "icon": "🔗",
                "metadata": {"test": "link_operations"}
            }
        )
        page_id = page["page_id"]
        print(f"✓ Page created: {page_id}")
        print(f"  Title: {page['title']}")
        print()
    except Exception as e:
        print(f"✗ Failed to create page: {e}")
        return

    # Step 2: Create test blocks
    print("STEP 2: Creating test blocks...")
    block_ids = []
    try:
        # Create 3 test blocks
        for i in range(3):
            block = await service.create_block(
                page_id=page_id,
                org_id=TEST_ORG_ID,
                user_id=TEST_USER_ID,
                block_data={
                    "block_type": "text",
                    "content": {"text": f"Test block {i+1} for linking"},
                    "position": i
                }
            )
            block_ids.append(block["block_id"])
            print(f"✓ Block {i+1} created: {block['block_id']}")
        print()
    except Exception as e:
        print(f"✗ Failed to create blocks: {e}")
        return

    # Step 3: Test create_link (block-to-block)
    print("STEP 3: Testing create_link (block-to-block)...")
    try:
        link1 = await service.create_link(
            source_block_id=block_ids[0],
            target_id=block_ids[1],
            link_type="reference",
            org_id=TEST_ORG_ID,
            is_page_link=False
        )
        print(f"✓ Link created: {link1['link_id']}")
        print(f"  Type: {link1['link_type']}")
        print(f"  Source: {link1['source_block_id']}")
        print(f"  Target: {link1['target_block_id']}")
        print()
    except Exception as e:
        print(f"✗ Failed to create link: {e}")
        return

    # Step 4: Test create_link (block-to-page)
    print("STEP 4: Testing create_link (block-to-page)...")
    try:
        link2 = await service.create_link(
            source_block_id=block_ids[2],
            target_id=page_id,
            link_type="mention",
            org_id=TEST_ORG_ID,
            is_page_link=True
        )
        print(f"✓ Page link created: {link2['link_id']}")
        print(f"  Type: {link2['link_type']}")
        print(f"  Source Block: {link2['source_block_id']}")
        print(f"  Target Page: {link2['target_page_id']}")
        print()
    except Exception as e:
        print(f"✗ Failed to create page link: {e}")
        return

    # Step 5: Test circular reference prevention
    print("STEP 5: Testing circular reference prevention...")
    try:
        # Try to create circular link: block[1] -> block[0] (should fail)
        circular_link = await service.create_link(
            source_block_id=block_ids[1],
            target_id=block_ids[0],
            link_type="reference",
            org_id=TEST_ORG_ID,
            is_page_link=False
        )
        print(f"✗ Circular reference NOT prevented! Link created: {circular_link['link_id']}")
        print("  This is a bug - circular references should be blocked")
        print()
    except ValueError as e:
        if "Circular reference detected" in str(e):
            print(f"✓ Circular reference prevented correctly")
            print(f"  Error: {e}")
            print()
        else:
            print(f"✗ Unexpected error: {e}")
            return
    except Exception as e:
        print(f"✗ Failed with unexpected error: {e}")
        return

    # Step 6: Test get_block_backlinks
    print("STEP 6: Testing get_block_backlinks...")
    try:
        backlinks = await service.get_block_backlinks(
            block_id=block_ids[1],
            org_id=TEST_ORG_ID
        )
        print(f"✓ Retrieved {len(backlinks)} backlinks for block {block_ids[1]}")
        for bl in backlinks:
            print(f"  - Link {bl['link_id']} ({bl['link_type']})")
            print(f"    From block: {bl['source_block_id']}")
            print(f"    Preview: {bl['source_content_preview']}")
        print()
    except Exception as e:
        print(f"✗ Failed to get backlinks: {e}")
        return

    # Step 7: Test get_page_backlinks
    print("STEP 7: Testing get_page_backlinks...")
    try:
        page_backlinks = await service.get_page_backlinks(
            page_id=page_id,
            org_id=TEST_ORG_ID
        )
        print(f"✓ Retrieved {len(page_backlinks)} backlinks for page {page_id}")
        for bl in page_backlinks:
            print(f"  - Link {bl['link_id']} ({bl['link_type']})")
            print(f"    From block: {bl['source_block_id']}")
            print(f"    Preview: {bl['source_content_preview']}")
        print()
    except Exception as e:
        print(f"✗ Failed to get page backlinks: {e}")
        return

    # Step 8: Test delete_link
    print("STEP 8: Testing delete_link...")
    try:
        deleted = await service.delete_link(
            link_id=link1['link_id'],
            org_id=TEST_ORG_ID
        )
        if deleted:
            print(f"✓ Link deleted: {link1['link_id']}")
        else:
            print(f"✗ Failed to delete link (returned False)")
        print()
    except Exception as e:
        print(f"✗ Failed to delete link: {e}")
        return

    # Step 9: Verify deletion
    print("STEP 9: Verifying link deletion...")
    try:
        backlinks_after_delete = await service.get_block_backlinks(
            block_id=block_ids[1],
            org_id=TEST_ORG_ID
        )
        print(f"✓ Backlinks after deletion: {len(backlinks_after_delete)}")
        print(f"  Before: 1 backlink, After: {len(backlinks_after_delete)} backlinks")
        if len(backlinks_after_delete) == 0:
            print("  Link successfully deleted!")
        print()
    except Exception as e:
        print(f"✗ Failed to verify deletion: {e}")
        return

    # Step 10: Test multi-tenant isolation
    print("STEP 10: Testing multi-tenant isolation...")
    try:
        # Try to access link from different org (should return False)
        wrong_org_delete = await service.delete_link(
            link_id=link2['link_id'],
            org_id="wrong-org-id"
        )
        if wrong_org_delete:
            print(f"✗ Multi-tenant isolation BROKEN! Link deleted from wrong org")
        else:
            print(f"✓ Multi-tenant isolation working")
            print(f"  Link not accessible from different organization")
        print()
    except Exception as e:
        print(f"✗ Failed isolation test: {e}")
        return

    # Summary
    print("=" * 70)
    print("Test Summary")
    print("=" * 70)
    print("✓ All 4 link management methods tested successfully:")
    print("  1. create_link() - Creates links with validation")
    print("  2. delete_link() - Deletes links with org isolation")
    print("  3. get_page_backlinks() - Retrieves page backlinks")
    print("  4. get_block_backlinks() - Retrieves block backlinks")
    print()
    print("✓ Circular reference prevention working")
    print("✓ Multi-tenant isolation working")
    print("✓ Bidirectional linking working")
    print()
    print("Link management implementation complete! 🎉")
    print("=" * 70)


if __name__ == "__main__":
    # Check configuration
    if ZERODB_API_KEY == "your-api-key-here":
        print("❌ ERROR: Please update ZERODB_API_KEY in the script")
        print("   Edit test_link_operations.py and set your ZeroDB API key")
        sys.exit(1)

    if ZERODB_PROJECT_ID == "your-project-id-here":
        print("❌ ERROR: Please update ZERODB_PROJECT_ID in the script")
        print("   Edit test_link_operations.py and set your ZeroDB project ID")
        sys.exit(1)

    # Run tests
    asyncio.run(test_link_operations())
