"""
ZeroDB Embeddings API Integration Tests for Ocean Backend

Tests the three main endpoints:
1. /api/v1/embeddings/generate - Generate embeddings
2. /v1/{project_id}/embeddings/embed-and-store - Store vectors with metadata
3. /v1/{project_id}/embeddings/search - Semantic search

Issue #3: Test ZeroDB Embeddings API integration
"""

import os
import pytest
import httpx
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
API_URL = os.getenv("ZERODB_API_URL", "https://api.ainative.studio")
API_KEY = os.getenv("ZERODB_API_KEY")
PROJECT_ID = os.getenv("ZERODB_PROJECT_ID")
MODEL = "BAAI/bge-base-en-v1.5"  # 768 dimensions
EXPECTED_DIMENSIONS = 768
SIMILARITY_THRESHOLD = 0.7
TEST_NAMESPACE = "ocean_blocks_test"

# Test data
TEST_TEXTS = [
    "Ocean is a block-based knowledge workspace",
    "Test block content for Ocean",
    "Another test block for semantic search",
    "ZeroDB provides vector storage and semantic search",
    "Knowledge management with AI-powered search"
]


class TestEmbeddingsGenerate:
    """Test suite for /api/v1/embeddings/generate endpoint"""

    @pytest.mark.asyncio
    async def test_generate_single_embedding(self):
        """Test generating embeddings for a single text"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_URL}/api/v1/embeddings/generate",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "texts": ["Ocean is a block-based knowledge workspace"],
                    "model": MODEL
                }
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

            data = response.json()

            # Verify response structure
            assert "embeddings" in data
            assert "model" in data
            assert "dimensions" in data
            assert "count" in data

            # Verify embeddings
            assert len(data["embeddings"]) == 1
            assert len(data["embeddings"][0]) == EXPECTED_DIMENSIONS

            # Verify model and dimensions
            assert data["model"] == MODEL
            assert data["dimensions"] == EXPECTED_DIMENSIONS
            assert data["count"] == 1

            # Verify all embedding values are floats
            for value in data["embeddings"][0]:
                assert isinstance(value, (int, float))

            print(f"✓ Generate single embedding: {data['dimensions']} dimensions, model={data['model']}")

    @pytest.mark.asyncio
    async def test_generate_batch_embeddings(self):
        """Test generating embeddings for multiple texts in batch"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_URL}/api/v1/embeddings/generate",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "texts": TEST_TEXTS[:3],
                    "model": MODEL
                }
            )

            assert response.status_code == 200
            data = response.json()

            # Verify batch size
            assert len(data["embeddings"]) == 3
            assert data["count"] == 3

            # Verify all embeddings have correct dimensions
            for embedding in data["embeddings"]:
                assert len(embedding) == EXPECTED_DIMENSIONS

            print(f"✓ Generate batch embeddings: {data['count']} texts processed")

    @pytest.mark.asyncio
    async def test_generate_embedding_performance(self):
        """Test embedding generation performance"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_URL}/api/v1/embeddings/generate",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "texts": TEST_TEXTS,
                    "model": MODEL
                }
            )

            assert response.status_code == 200
            data = response.json()

            # Check if processing time is included
            if "processing_time_ms" in data:
                processing_time = data["processing_time_ms"]
                print(f"✓ Processing time: {processing_time:.2f}ms for {len(TEST_TEXTS)} texts")

            assert data["count"] == len(TEST_TEXTS)


class TestEmbedAndStore:
    """Test suite for /v1/{project_id}/embeddings/embed-and-store endpoint"""

    @pytest.mark.asyncio
    async def test_embed_and_store_with_metadata(self):
        """Test storing embeddings with metadata in one call"""
        metadata = [
            {
                "block_id": "test-block-1",
                "block_type": "text",
                "page_id": "test-page-1",
                "organization_id": "test-org"
            },
            {
                "block_id": "test-block-2",
                "block_type": "heading",
                "page_id": "test-page-1",
                "organization_id": "test-org"
            }
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_URL}/v1/{PROJECT_ID}/embeddings/embed-and-store",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "texts": TEST_TEXTS[:2],
                    "model": MODEL,
                    "namespace": TEST_NAMESPACE,
                    "metadata": metadata
                }
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

            data = response.json()

            # Verify response structure
            assert "success" in data
            assert "vectors_stored" in data or "vector_ids" in data
            assert "dimensions" in data
            assert "target_column" in data or "namespace" in data

            # Verify storage success
            assert data["success"] is True or data.get("vectors_stored", 0) > 0

            # Verify dimensions
            assert data["dimensions"] == EXPECTED_DIMENSIONS

            # Verify target column routing (768-dim goes to vector_768 column)
            if "target_column" in data:
                assert data["target_column"] == "vector_768"

            print(f"✓ Embed and store: {data.get('vectors_stored', len(TEST_TEXTS[:2]))} vectors stored in {data['dimensions']}-dim column")

    @pytest.mark.asyncio
    async def test_embed_and_store_without_metadata(self):
        """Test storing embeddings without metadata"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_URL}/v1/{PROJECT_ID}/embeddings/embed-and-store",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "texts": [TEST_TEXTS[0]],
                    "model": MODEL,
                    "namespace": TEST_NAMESPACE
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert data["success"] is True or data.get("vectors_stored", 0) > 0
            print(f"✓ Embed and store without metadata: Success")

    @pytest.mark.asyncio
    async def test_embed_and_store_batch(self):
        """Test batch storage of multiple vectors"""
        metadata = [
            {
                "block_id": f"test-block-{i}",
                "block_type": "text",
                "page_id": "test-page-batch",
                "organization_id": "test-org"
            }
            for i in range(len(TEST_TEXTS))
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_URL}/v1/{PROJECT_ID}/embeddings/embed-and-store",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "texts": TEST_TEXTS,
                    "model": MODEL,
                    "namespace": TEST_NAMESPACE,
                    "metadata": metadata
                }
            )

            assert response.status_code == 200
            data = response.json()

            vectors_stored = data.get("vectors_stored", len(TEST_TEXTS))
            assert vectors_stored == len(TEST_TEXTS)

            print(f"✓ Batch embed and store: {vectors_stored} vectors stored")


class TestSemanticSearch:
    """Test suite for /v1/{project_id}/embeddings/search endpoint"""

    @pytest.mark.asyncio
    async def test_search_basic(self):
        """Test basic semantic search functionality"""
        # First, store some test data
        await self._store_test_data()

        # Now search
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_URL}/v1/{PROJECT_ID}/embeddings/search",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "query": "knowledge workspace blocks",
                    "model": MODEL,
                    "namespace": TEST_NAMESPACE,
                    "limit": 10,
                    "threshold": SIMILARITY_THRESHOLD
                }
            )

            assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"

            data = response.json()

            # Verify response structure
            assert "results" in data
            assert isinstance(data["results"], list)

            # Verify we got results
            assert len(data["results"]) > 0, "Expected at least one search result"

            # Verify each result structure
            for result in data["results"]:
                assert "similarity" in result or "score" in result

                # Get similarity score
                similarity = result.get("similarity") or result.get("score", 0)

                # Verify similarity threshold
                assert similarity >= SIMILARITY_THRESHOLD, f"Result similarity {similarity} below threshold {SIMILARITY_THRESHOLD}"

                # Check for document or metadata
                assert "document" in result or "metadata" in result

            print(f"✓ Basic search: {len(data['results'])} results found with threshold {SIMILARITY_THRESHOLD}")

    @pytest.mark.asyncio
    async def test_search_with_metadata_filter(self):
        """Test semantic search with metadata filtering"""
        await self._store_test_data()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_URL}/v1/{PROJECT_ID}/embeddings/search",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "query": "block content",
                    "model": MODEL,
                    "namespace": TEST_NAMESPACE,
                    "limit": 5,
                    "threshold": 0.6,
                    "filter_metadata": {
                        "organization_id": "test-org"
                    }
                }
            )

            assert response.status_code == 200
            data = response.json()

            assert "results" in data
            print(f"✓ Search with filter: {len(data['results'])} results with organization_id=test-org")

    @pytest.mark.asyncio
    async def test_search_performance(self):
        """Test search performance (should be < 200ms)"""
        await self._store_test_data()

        import time
        start_time = time.time()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_URL}/v1/{PROJECT_ID}/embeddings/search",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "query": "semantic search",
                    "model": MODEL,
                    "namespace": TEST_NAMESPACE,
                    "limit": 10,
                    "threshold": 0.7
                }
            )

        elapsed_ms = (time.time() - start_time) * 1000

        assert response.status_code == 200

        # Check if API returns processing time
        data = response.json()
        if "processing_time_ms" in data:
            api_time = data["processing_time_ms"]
            print(f"✓ Search performance: API={api_time:.2f}ms, Total={elapsed_ms:.2f}ms")
        else:
            print(f"✓ Search performance: {elapsed_ms:.2f}ms")

        # Note: Don't assert on time as network latency varies
        # Just log the performance for monitoring

    @pytest.mark.asyncio
    async def test_search_relevance(self):
        """Test that search results are semantically relevant"""
        await self._store_test_data()

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_URL}/v1/{PROJECT_ID}/embeddings/search",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "query": "Ocean workspace knowledge",
                    "model": MODEL,
                    "namespace": TEST_NAMESPACE,
                    "limit": 5,
                    "threshold": 0.7
                }
            )

            assert response.status_code == 200
            data = response.json()

            if len(data["results"]) > 0:
                # Top result should be highly relevant
                top_result = data["results"][0]
                top_similarity = top_result.get("similarity") or top_result.get("score", 0)

                # Top result should have high similarity
                assert top_similarity >= 0.7, f"Top result similarity {top_similarity} should be >= 0.7"

                print(f"✓ Search relevance: Top result similarity={top_similarity:.3f}")

    async def _store_test_data(self):
        """Helper: Store test data for search tests"""
        metadata = [
            {
                "block_id": f"search-test-{i}",
                "block_type": "text",
                "page_id": "search-test-page",
                "organization_id": "test-org"
            }
            for i in range(len(TEST_TEXTS))
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.post(
                f"{API_URL}/v1/{PROJECT_ID}/embeddings/embed-and-store",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "texts": TEST_TEXTS,
                    "model": MODEL,
                    "namespace": TEST_NAMESPACE,
                    "metadata": metadata
                }
            )


class TestErrorCases:
    """Test suite for error handling"""

    @pytest.mark.asyncio
    async def test_invalid_model_name(self):
        """Test error handling for invalid model name"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_URL}/api/v1/embeddings/generate",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "texts": ["test"],
                    "model": "invalid-model-name-xyz"
                }
            )

            # Should return error (400 or 422)
            assert response.status_code in [400, 422, 500], f"Expected error status, got {response.status_code}"

            data = response.json()
            assert "detail" in data or "error" in data

            print(f"✓ Invalid model error: {response.status_code}")

    @pytest.mark.asyncio
    async def test_missing_api_key(self):
        """Test error handling for missing API key"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_URL}/api/v1/embeddings/generate",
                headers={
                    "Content-Type": "application/json"
                    # No Authorization header
                },
                json={
                    "texts": ["test"],
                    "model": MODEL
                }
            )

            # Should return 401 Unauthorized
            assert response.status_code == 401, f"Expected 401, got {response.status_code}"

            print(f"✓ Missing API key error: {response.status_code}")

    @pytest.mark.asyncio
    async def test_invalid_project_id(self):
        """Test error handling for invalid project ID"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_URL}/v1/invalid-project-id-xyz/embeddings/embed-and-store",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "texts": ["test"],
                    "model": MODEL,
                    "namespace": TEST_NAMESPACE
                }
            )

            # Should return error (400, 404, or 422)
            assert response.status_code in [400, 404, 422], f"Expected error status, got {response.status_code}"

            print(f"✓ Invalid project ID error: {response.status_code}")

    @pytest.mark.asyncio
    async def test_empty_texts_array(self):
        """Test error handling for empty texts array"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_URL}/api/v1/embeddings/generate",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "texts": [],
                    "model": MODEL
                }
            )

            # Should return validation error (422)
            assert response.status_code in [400, 422], f"Expected validation error, got {response.status_code}"

            print(f"✓ Empty texts array error: {response.status_code}")


class TestDimensionConsistency:
    """Test suite for dimension consistency (768-dim vectors)"""

    @pytest.mark.asyncio
    async def test_768_dimension_consistency(self):
        """Test that BAAI/bge-base-en-v1.5 consistently returns 768 dimensions"""
        test_texts = [
            "Short text",
            "This is a longer text with more content to test dimension consistency",
            "Special characters: @#$%^&*()",
            "Numbers: 123456789",
            "Mixed content: Ocean is a workspace with AI-powered search!"
        ]

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_URL}/api/v1/embeddings/generate",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "texts": test_texts,
                    "model": MODEL
                }
            )

            assert response.status_code == 200
            data = response.json()

            # Verify all embeddings have exactly 768 dimensions
            for i, embedding in enumerate(data["embeddings"]):
                assert len(embedding) == 768, f"Text {i}: Expected 768 dimensions, got {len(embedding)}"

            print(f"✓ Dimension consistency: All {len(test_texts)} texts produced 768-dim vectors")

    @pytest.mark.asyncio
    async def test_model_dimension_metadata(self):
        """Test that API returns correct dimension metadata"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{API_URL}/api/v1/embeddings/generate",
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "texts": ["test"],
                    "model": MODEL
                }
            )

            assert response.status_code == 200
            data = response.json()

            # Verify metadata
            assert data["model"] == MODEL
            assert data["dimensions"] == 768

            print(f"✓ Dimension metadata: model={data['model']}, dimensions={data['dimensions']}")


# Pytest configuration
@pytest.fixture(scope="session", autouse=True)
def verify_credentials():
    """Verify that required credentials are available before running tests"""
    if not API_KEY:
        pytest.skip("ZERODB_API_KEY not set in environment")
    if not PROJECT_ID:
        pytest.skip("ZERODB_PROJECT_ID not set in environment")

    print(f"\n{'='*80}")
    print(f"ZeroDB Embeddings API Test Configuration")
    print(f"{'='*80}")
    print(f"API URL: {API_URL}")
    print(f"Project ID: {PROJECT_ID[:8]}...{PROJECT_ID[-8:]}")
    print(f"Model: {MODEL}")
    print(f"Expected Dimensions: {EXPECTED_DIMENSIONS}")
    print(f"Similarity Threshold: {SIMILARITY_THRESHOLD}")
    print(f"Test Namespace: {TEST_NAMESPACE}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_embeddings_api.py -v --cov=tests --cov-report=term-missing
    pytest.main([__file__, "-v", "--tb=short"])
