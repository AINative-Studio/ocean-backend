# ZeroDB Embeddings API Tests - Quick Start

**Issue #3**: Test ZeroDB Embeddings API integration

## 1. Setup (One-Time)

```bash
# Install test dependencies
pip install -r tests/requirements-test.txt

# Create .env file with credentials
cp .env.test.example .env

# Edit .env and add:
# - ZERODB_API_KEY (from Issue #1)
# - ZERODB_PROJECT_ID (from Issue #1)
```

## 2. Run Tests

### All Tests
```bash
./tests/run_tests.sh all
```

### By Category
```bash
./tests/run_tests.sh generate    # Test embeddings generation
./tests/run_tests.sh store       # Test vector storage
./tests/run_tests.sh search      # Test semantic search
./tests/run_tests.sh errors      # Test error handling
./tests/run_tests.sh dimensions  # Test 768-dim consistency
./tests/run_tests.sh coverage    # With coverage report
```

### Specific Test
```bash
pytest tests/test_embeddings_api.py::TestEmbeddingsGenerate::test_generate_single_embedding -v
```

## 3. Expected Results

✅ **17 tests should PASS**:
- 3 embeddings generation tests
- 3 embed-and-store tests
- 4 semantic search tests
- 4 error handling tests
- 2 dimension consistency tests

✅ **Coverage**: 80%+

✅ **All vectors**: Exactly 768 dimensions

✅ **Model**: BAAI/bge-base-en-v1.5

## 4. Troubleshooting

**401 Unauthorized**
```bash
# Check API key
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('ZERODB_API_KEY'))"
```

**No results in search**
- Normal on first run
- Tests automatically store data before searching

**Dimension mismatch**
- Always use same model for store and search
- Default: BAAI/bge-base-en-v1.5 (768-dim)

## 5. What Tests Verify

| Endpoint | Tests | Verified |
|----------|-------|----------|
| `/api/v1/embeddings/generate` | 3 | 768 dims, model, batch |
| `/v1/{project}/embeddings/embed-and-store` | 3 | Storage, metadata, routing |
| `/v1/{project}/embeddings/search` | 4 | Search, filters, relevance |
| Error cases | 4 | Auth, validation, errors |
| Consistency | 2 | 768-dim guarantee |

## 6. Next Steps

1. ⏳ Wait for Issue #1 (credentials)
2. ⏭️ Run tests with real credentials
3. ✅ Verify all 17 tests pass
4. ⏭️ Move to Issue #4 (implement embeddings service)

---

**Full Documentation**: [tests/README.md](README.md)
**Test Summary**: [EMBEDDINGS_API_TEST_SUMMARY.md](../EMBEDDINGS_API_TEST_SUMMARY.md)
