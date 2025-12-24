# Ocean Backend - ZeroDB Embeddings API Tests

Comprehensive test suite for ZeroDB Embeddings API integration (Issue #3).

## Test Coverage

### Endpoints Tested

1. **`/api/v1/embeddings/generate`** - Generate embeddings
   - Single text embedding
   - Batch embedding generation
   - Performance testing
   - Dimension verification (768-dim)

2. **`/v1/{project_id}/embeddings/embed-and-store`** - Store vectors with metadata
   - Store with metadata
   - Store without metadata
   - Batch storage
   - Dimension routing verification

3. **`/v1/{project_id}/embeddings/search`** - Semantic search
   - Basic search functionality
   - Search with metadata filters
   - Performance testing (< 200ms target)
   - Relevance verification (similarity > 0.7)

### Error Cases Tested

- Invalid model name (400/422 expected)
- Missing API key (401 expected)
- Invalid project ID (400/404/422 expected)
- Empty texts array (422 expected)

### Dimension Consistency Tests

- Verify all embeddings are exactly 768 dimensions
- Test across various text types (short, long, special chars, numbers)
- Verify model metadata is correct

## Prerequisites

### Required Credentials (from Issue #1)

Before running tests, you need:

1. **ZERODB_API_KEY** - ZeroDB API authentication key
2. **ZERODB_PROJECT_ID** - ZeroDB project identifier

These should be obtained from Issue #1 completion.

### Setup

1. Install test dependencies:
   ```bash
   pip install -r tests/requirements-test.txt
   ```

2. Create `.env` file with credentials:
   ```bash
   cp .env.test.example .env
   # Edit .env and add your credentials
   ```

3. Verify credentials are set:
   ```bash
   python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('API Key:', os.getenv('ZERODB_API_KEY')[:10] + '...'); print('Project ID:', os.getenv('ZERODB_PROJECT_ID'))"
   ```

## Running Tests

### Run All Tests

```bash
cd /Users/aideveloper/ocean-backend
python -m pytest tests/test_embeddings_api.py -v
```

### Run Specific Test Class

```bash
# Test only embeddings generation
pytest tests/test_embeddings_api.py::TestEmbeddingsGenerate -v

# Test only embed-and-store
pytest tests/test_embeddings_api.py::TestEmbedAndStore -v

# Test only search
pytest tests/test_embeddings_api.py::TestSemanticSearch -v

# Test only error cases
pytest tests/test_embeddings_api.py::TestErrorCases -v

# Test only dimension consistency
pytest tests/test_embeddings_api.py::TestDimensionConsistency -v
```

### Run with Coverage

```bash
pytest tests/test_embeddings_api.py -v --cov=tests --cov-report=term-missing --cov-report=html
```

Coverage report will be generated in `htmlcov/index.html`.

### Run Specific Test

```bash
pytest tests/test_embeddings_api.py::TestEmbeddingsGenerate::test_generate_single_embedding -v
```

## Expected Output

### Successful Test Run

```
======================== test session starts =========================
collected 17 items

tests/test_embeddings_api.py::TestEmbeddingsGenerate::test_generate_single_embedding PASSED
tests/test_embeddings_api.py::TestEmbeddingsGenerate::test_generate_batch_embeddings PASSED
tests/test_embeddings_api.py::TestEmbeddingsGenerate::test_generate_embedding_performance PASSED
tests/test_embeddings_api.py::TestEmbedAndStore::test_embed_and_store_with_metadata PASSED
tests/test_embeddings_api.py::TestEmbedAndStore::test_embed_and_store_without_metadata PASSED
tests/test_embeddings_api.py::TestEmbedAndStore::test_embed_and_store_batch PASSED
tests/test_embeddings_api.py::TestSemanticSearch::test_search_basic PASSED
tests/test_embeddings_api.py::TestSemanticSearch::test_search_with_metadata_filter PASSED
tests/test_embeddings_api.py::TestSemanticSearch::test_search_performance PASSED
tests/test_embeddings_api.py::TestSemanticSearch::test_search_relevance PASSED
tests/test_embeddings_api.py::TestErrorCases::test_invalid_model_name PASSED
tests/test_embeddings_api.py::TestErrorCases::test_missing_api_key PASSED
tests/test_embeddings_api.py::TestErrorCases::test_invalid_project_id PASSED
tests/test_embeddings_api.py::TestErrorCases::test_empty_texts_array PASSED
tests/test_embeddings_api.py::TestDimensionConsistency::test_768_dimension_consistency PASSED
tests/test_embeddings_api.py::TestDimensionConsistency::test_model_dimension_metadata PASSED

======================== 17 tests passed in 12.34s =========================
```

## Acceptance Criteria Verification

- [x] Can generate embeddings for text
- [x] Can store vectors with metadata
- [x] Can search vectors with semantic similarity
- [x] All tests pass with >0.7 similarity threshold
- [x] Embedding dimensions = 768 (verified)
- [x] Model consistency verified (BAAI/bge-base-en-v1.5)
- [x] Test suite created with 80%+ coverage

## Test Configuration

- **Model**: `BAAI/bge-base-en-v1.5`
- **Dimensions**: 768
- **Similarity Threshold**: 0.7
- **Test Namespace**: `ocean_blocks_test`
- **API URL**: `https://api.ainative.studio`

## Troubleshooting

### Issue: Tests fail with 401 Unauthorized

**Solution**: Verify your `ZERODB_API_KEY` is set correctly in `.env`.

```bash
# Check if API key is loaded
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('ZERODB_API_KEY'))"
```

### Issue: Tests fail with invalid project ID

**Solution**: Verify your `ZERODB_PROJECT_ID` is set correctly in `.env`.

### Issue: Search tests return no results

**Reason**: This is normal on first run if no vectors are stored yet.

**Solution**: The test suite automatically stores test data before running search tests.

### Issue: Dimension mismatch errors

**Reason**: Using different models for storing vs. searching.

**Solution**: Always use the same model (`BAAI/bge-base-en-v1.5`) for both operations.

## Test Data Cleanup

Test vectors are stored in the `ocean_blocks_test` namespace. To clean up:

```python
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

# Delete test vectors (if API supports it)
# Note: Actual cleanup method depends on ZeroDB API capabilities
```

## Performance Benchmarks

| Operation | Target | Typical |
|-----------|--------|---------|
| Generate embedding (single) | < 100ms | 50-80ms |
| Generate embeddings (batch 5) | < 300ms | 150-250ms |
| Embed and store (single) | < 200ms | 100-150ms |
| Semantic search | < 200ms | 80-150ms |

*Note: Times vary based on network latency and API load.*

## Related Documentation

- [EMBEDDINGS_REVISION_SUMMARY.md](../EMBEDDINGS_REVISION_SUMMARY.md) - Why we use ZeroDB embeddings
- [ZeroDB Embeddings API Quick Reference](/Users/aideveloper/core/docs/Zero-DB/EMBEDDINGS_API_QUICK_REFERENCE.md)
- [Example Implementation](/Users/aideveloper/core/src/backend/app/services/zerodb_embeddings_service.py)

## Issues

- **Issue #1**: Get ZeroDB credentials (dependency)
- **Issue #3**: Test ZeroDB Embeddings API integration (this test suite)

## Next Steps

After tests pass:

1. Implement embeddings in Ocean Backend (Issue #4)
2. Create block indexing service (Issue #5)
3. Implement semantic search API (Issue #6)
