# Test Execution Checklist (When Credentials Available)

**Issue #3**: Test ZeroDB Embeddings API Integration
**Prerequisites**: Issue #1 complete (credentials obtained)

---

## Pre-Execution Checklist

### 1. Verify Prerequisites

- [ ] Issue #1 is marked as COMPLETE
- [ ] `ZERODB_API_KEY` has been obtained
- [ ] `ZERODB_PROJECT_ID` has been obtained
- [ ] Both credentials are valid and active

### 2. Environment Setup

```bash
# Navigate to ocean-backend
cd /Users/aideveloper/ocean-backend

# Verify test files exist
ls -la tests/test_embeddings_api.py
ls -la tests/run_tests.sh
ls -la .env.test.example

# All files should exist
```

### 3. Install Dependencies

```bash
# Install test dependencies
pip install -r tests/requirements-test.txt

# Verify installation
python -c "import pytest, pytest_asyncio, httpx, dotenv; print('All dependencies installed')"
```

Expected output: `All dependencies installed`

### 4. Configure Credentials

```bash
# Create .env from template
cp .env.test.example .env

# Edit .env and add credentials
# vim .env  # or use your preferred editor
```

**Required in .env**:
```env
ZERODB_API_URL=https://api.ainative.studio
ZERODB_API_KEY=<your-actual-api-key-here>
ZERODB_PROJECT_ID=<your-actual-project-id-here>
```

### 5. Verify Credentials

```bash
# Check credentials are loaded
python << 'EOF'
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("ZERODB_API_KEY")
project_id = os.getenv("ZERODB_PROJECT_ID")

if not api_key or api_key == "your_api_key_here":
    print("ERROR: ZERODB_API_KEY not set correctly")
    exit(1)

if not project_id or project_id == "your_project_id_here":
    print("ERROR: ZERODB_PROJECT_ID not set correctly")
    exit(1)

print(f"✅ API Key: {api_key[:10]}...{api_key[-10:]}")
print(f"✅ Project ID: {project_id}")
print("✅ Credentials configured correctly")
EOF
```

---

## Test Execution

### Phase 1: Quick Smoke Test

```bash
# Test a single test first
pytest tests/test_embeddings_api.py::TestEmbeddingsGenerate::test_generate_single_embedding -v
```

**Expected**: ✅ PASSED

**If FAILED**: Check error message, verify credentials, check API access

### Phase 2: Test by Category

```bash
# Test embeddings generation (3 tests)
./tests/run_tests.sh generate
```
- [ ] All 3 tests PASSED
- [ ] 768 dimensions verified
- [ ] Model confirmed: BAAI/bge-base-en-v1.5

```bash
# Test embed-and-store (3 tests)
./tests/run_tests.sh store
```
- [ ] All 3 tests PASSED
- [ ] Vectors stored successfully
- [ ] Metadata attached correctly

```bash
# Test semantic search (4 tests)
./tests/run_tests.sh search
```
- [ ] All 4 tests PASSED
- [ ] Search results returned
- [ ] Similarity >= 0.7
- [ ] Metadata filtering works

```bash
# Test error handling (4 tests)
./tests/run_tests.sh errors
```
- [ ] All 4 tests PASSED
- [ ] 401 for missing auth
- [ ] 422 for invalid input
- [ ] Proper error messages

```bash
# Test dimension consistency (2 tests)
./tests/run_tests.sh dimensions
```
- [ ] All 2 tests PASSED
- [ ] 768 dimensions consistent
- [ ] Model metadata correct

### Phase 3: Full Test Suite

```bash
# Run all 17 tests
./tests/run_tests.sh all
```

**Expected Output**:
```
======================== test session starts =========================
...
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

======================== 17 passed in X.XXs =========================
```

**Verification**:
- [ ] All 17 tests PASSED (no failures)
- [ ] No errors or exceptions
- [ ] Performance acceptable (< 30 seconds total)

### Phase 4: Coverage Report

```bash
# Generate coverage report
./tests/run_tests.sh coverage
```

**Verification**:
- [ ] Coverage >= 80% (should be ~85% or higher)
- [ ] HTML report generated in `htmlcov/index.html`
- [ ] No critical code paths uncovered

---

## Post-Execution Verification

### 1. Verify All Acceptance Criteria Met

- [ ] Can generate embeddings for text
- [ ] Can store vectors with metadata
- [ ] Can search vectors with semantic similarity
- [ ] All tests pass with >0.7 similarity threshold
- [ ] Embedding dimensions = 768 (verified)
- [ ] Model consistency verified (BAAI/bge-base-en-v1.5)
- [ ] Test suite has 80%+ coverage

### 2. Document Actual Results

Create `TEST_EXECUTION_RESULTS.md`:

```markdown
# Test Execution Results - Issue #3

**Execution Date**: [DATE]
**Executed By**: [NAME]
**Credentials Source**: Issue #1

## Summary

- Total Tests: 17
- Passed: [X]
- Failed: [Y]
- Skipped: [Z]
- Duration: [X.XX] seconds
- Coverage: [XX]%

## Performance Metrics

| Operation | Actual Time | Target | Status |
|-----------|-------------|--------|--------|
| Generate single | [XX]ms | <100ms | [PASS/FAIL] |
| Generate batch (5) | [XX]ms | <300ms | [PASS/FAIL] |
| Embed and store | [XX]ms | <200ms | [PASS/FAIL] |
| Semantic search | [XX]ms | <200ms | [PASS/FAIL] |

## Dimension Verification

- All embeddings: [768] dimensions ✅
- Model: BAAI/bge-base-en-v1.5 ✅
- Target column: vector_768 ✅

## Issues Discovered

[List any issues found during testing]

## Conclusion

[PASS/FAIL] - [Summary]
```

### 3. Commit Test Results

```bash
# Add test results
git add TEST_EXECUTION_RESULTS.md

# Commit (NO AI ATTRIBUTION!)
git commit -m "Add test execution results for Issue #3

- Executed 17 ZeroDB Embeddings API tests
- All tests passed with XX% coverage
- Verified 768-dimension consistency
- Confirmed model: BAAI/bge-base-en-v1.5

Refs #3"
```

### 4. Update Issue #3

On GitHub:

1. Add comment with test results summary
2. Attach coverage report (if applicable)
3. Confirm all acceptance criteria met
4. Close issue with comment: "All tests passing, 768-dim verified"

---

## Troubleshooting

### Issue: 401 Unauthorized

**Cause**: Invalid or missing API key

**Solution**:
```bash
# Verify API key is set
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('ZERODB_API_KEY'))"

# Check if API key is valid (test with curl)
curl -X POST https://api.ainative.studio/api/v1/embeddings/generate \
  -H "Authorization: Bearer ${ZERODB_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"texts":["test"],"model":"BAAI/bge-base-en-v1.5"}'
```

### Issue: 404 Project Not Found

**Cause**: Invalid project ID

**Solution**: Verify project ID with ZeroDB dashboard or Issue #1 documentation

### Issue: Search Returns No Results

**Cause**: No vectors stored yet (normal on first run)

**Solution**: Tests automatically store data before searching - this should not happen

### Issue: Dimension Mismatch

**Cause**: Using different models for store vs. search

**Solution**: All tests use `BAAI/bge-base-en-v1.5` - check test code if this occurs

### Issue: Tests Timeout

**Cause**: Network issues or API slowness

**Solution**:
- Check internet connection
- Verify API status: https://status.ainative.studio (if exists)
- Increase timeout in test code if needed

---

## Final Checklist

- [ ] All prerequisites met
- [ ] Dependencies installed
- [ ] Credentials configured
- [ ] Smoke test passed
- [ ] Category tests passed (5 categories)
- [ ] Full suite passed (17 tests)
- [ ] Coverage >= 80%
- [ ] Performance acceptable
- [ ] Results documented
- [ ] Issue #3 updated
- [ ] Ready to move to Issue #4

---

## Next Steps After Successful Execution

1. ✅ Close Issue #3
2. ⏭️ Start Issue #4: Implement Ocean embeddings service
3. ⏭️ Use test suite as reference implementation
4. ⏭️ Create `ocean_embeddings_service.py`
5. ⏭️ Implement block indexing
6. ⏭️ Add semantic search API

---

**Estimated Execution Time**: 5-10 minutes
**Prerequisites**: Issue #1 complete
**Dependencies**: pytest, httpx, python-dotenv
