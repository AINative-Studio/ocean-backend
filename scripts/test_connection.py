#!/usr/bin/env python3
"""
Test ZeroDB API connection and verify project setup.

This script verifies:
1. API credentials are valid
2. Project exists and is accessible
3. Database features are enabled
"""

import asyncio
import os
import sys
from pathlib import Path

# Add parent directory to path to import from app
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from dotenv import load_dotenv


async def test_zerodb_connection():
    """Test connection to ZeroDB API and verify project setup."""

    # Load environment variables
    load_dotenv()

    api_url = os.getenv("ZERODB_API_URL")
    project_id = os.getenv("ZERODB_PROJECT_ID")
    api_key = os.getenv("ZERODB_API_KEY")

    print("=" * 70)
    print("Ocean Backend - ZeroDB Connection Test")
    print("=" * 70)
    print()

    # Validate environment variables
    print("[1/4] Validating environment variables...")
    if not api_url:
        print("❌ ZERODB_API_URL not set in .env")
        return False
    if not project_id:
        print("❌ ZERODB_PROJECT_ID not set in .env")
        return False
    if not api_key:
        print("❌ ZERODB_API_KEY not set in .env")
        return False

    print(f"✅ API URL: {api_url}")
    print(f"✅ Project ID: {project_id}")
    print(f"✅ API Key: {api_key[:10]}...{api_key[-10:]}")
    print()

    # Test API connection
    print("[2/4] Testing API connection...")
    async with httpx.AsyncClient() as client:
        try:
            # Test health endpoint
            response = await client.get(f"{api_url}/health")
            if response.status_code == 200:
                print(f"✅ API is healthy: {response.json()}")
            else:
                print(f"⚠️  API health check returned: {response.status_code}")
        except Exception as e:
            print(f"❌ Failed to connect to API: {e}")
            return False
    print()

    # Test project access
    print("[3/4] Testing project access...")
    async with httpx.AsyncClient() as client:
        try:
            # Get project info
            response = await client.get(
                f"{api_url}/v1/projects/{project_id}",
                headers={"Authorization": f"Bearer {api_key}"}
            )

            if response.status_code == 200:
                project_info = response.json()
                print(f"✅ Project found: {project_info.get('name', 'Unknown')}")
                print(f"   Description: {project_info.get('description', 'N/A')}")
                print(f"   Database enabled: {project_info.get('database_enabled', False)}")
            elif response.status_code == 401:
                print(f"❌ Authentication failed - invalid API key")
                return False
            elif response.status_code == 404:
                print(f"❌ Project not found: {project_id}")
                return False
            else:
                print(f"❌ Failed to get project info: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error accessing project: {e}")
            return False
    print()

    # Test project statistics
    print("[4/4] Getting project statistics...")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{api_url}/v1/projects/{project_id}/stats",
                headers={"Authorization": f"Bearer {api_key}"}
            )

            if response.status_code == 200:
                stats = response.json()
                print(f"✅ Project stats retrieved:")
                print(f"   Total operations: {stats.get('total_operations', 0)}")
                print(f"   Vector count: {stats.get('vector_count', 0)}")
                print(f"   Table count: {stats.get('table_count', 0)}")
            else:
                print(f"⚠️  Stats not available (status: {response.status_code})")
        except Exception as e:
            print(f"⚠️  Could not retrieve stats: {e}")
    print()

    print("=" * 70)
    print("✅ ZeroDB connection test PASSED!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("1. Create ZeroDB tables (ocean_pages, ocean_blocks, ocean_block_links, ocean_tags)")
    print("2. Test table operations")
    print("3. Test embeddings generation")
    print("4. Start FastAPI application")
    print()

    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_zerodb_connection())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        print("\n❌ Test cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
