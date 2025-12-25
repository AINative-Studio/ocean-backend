# Ocean Backend - Beta Testing Guide

**Version**: 0.1.0
**Release Date**: December 24, 2024
**Test Duration**: 1-2 weeks
**Target Users**: 5-10 beta testers

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Setup Instructions](#setup-instructions)
3. [What to Test](#what-to-test)
4. [Test Scenarios](#test-scenarios)
5. [How to Report Issues](#how-to-report-issues)
6. [Feedback Survey](#feedback-survey)
7. [API Testing with Postman](#api-testing-with-postman)
8. [Expected Results](#expected-results)

---

## 🎯 Overview

Ocean Backend is a block-based knowledge workspace API built on FastAPI and ZeroDB. This beta test focuses on validating:

- **API Functionality**: All 27 endpoints working correctly
- **Performance**: Response times under load
- **Data Integrity**: Multi-tenant isolation and data consistency
- **Search Quality**: Semantic search accuracy
- **Error Handling**: Graceful failures and helpful error messages
- **Documentation**: API clarity and completeness

---

## 🚀 Setup Instructions

### Prerequisites

- **Python**: 3.11+
- **API Key**: Contact admin for beta testing credentials
- **Postman**: For API testing (optional but recommended)
- **cURL or HTTPie**: For command-line testing

### Environment Configuration

1. **Get Your Credentials**
   - Organization ID
   - API Key (JWT token)
   - ZeroDB Project ID (read-only for beta)

2. **Set Environment Variables**

```bash
# Base URL
export OCEAN_API_URL="https://ocean-backend-staging.railway.app"

# Your credentials (provided by admin)
export OCEAN_ORG_ID="your-org-id"
export OCEAN_API_KEY="your-api-key"
```

3. **Verify Connection**

```bash
curl $OCEAN_API_URL/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "ocean-backend",
  "version": "0.1.0"
}
```

### Import Postman Collection

1. Download `ocean-backend.postman_collection.json`
2. Open Postman → Import → Select file
3. Create environment with variables:
   - `base_url`: API base URL
   - `org_id`: Your organization ID
   - `api_key`: Your API key
   - `page_id`: (auto-populated by tests)
   - `block_id`: (auto-populated by tests)

---

## 🧪 What to Test

### Critical Features (Must Test)

1. **Page Management**
   - Create pages with parent-child hierarchy
   - Update page titles and properties
   - Move pages within workspace
   - Soft delete and verify data isolation

2. **Block Operations**
   - Create blocks (text, heading, list, task, link, page_link)
   - Update block content
   - Reorder blocks within a page
   - Convert block types
   - Batch create blocks

3. **Semantic Search**
   - Search for content across workspace
   - Filter by block types
   - Filter by tags
   - Date range filtering
   - Verify search relevance

4. **Linking System**
   - Create page-to-page links
   - Create block-to-block links
   - Get backlinks for pages
   - Get backlinks for blocks

5. **Tag Management**
   - Create tags with colors
   - Assign tags to blocks
   - List all tags in workspace
   - Remove tags from blocks

### Secondary Features (If Time Permits)

6. **Error Handling**
   - Test with invalid data
   - Test missing required fields
   - Test invalid IDs
   - Test rate limiting (if configured)

7. **Performance**
   - Create 100+ blocks in a page
   - Search with large result sets
   - Batch operations
   - Concurrent requests

8. **Multi-Tenant Isolation**
   - Verify you can't access other orgs' data
   - Test with wrong organization_id

---

## 📝 Test Scenarios

### Scenario 1: Create Workspace Hierarchy

**Goal**: Build a basic workspace with nested pages

**Steps**:

1. Create root page "My Workspace"
   ```bash
   POST /v1/ocean/pages
   {
     "title": "My Workspace",
     "organization_id": "{{org_id}}",
     "parent_id": null
   }
   ```

2. Create child page "Projects"
   ```bash
   POST /v1/ocean/pages
   {
     "title": "Projects",
     "organization_id": "{{org_id}}",
     "parent_id": "{{workspace_page_id}}"
   }
   ```

3. List all pages
   ```bash
   GET /v1/ocean/pages?organization_id={{org_id}}
   ```

4. Move "Projects" page to new parent
   ```bash
   POST /v1/ocean/pages/{{projects_page_id}}/move
   {
     "new_parent_id": null,
     "new_position": 0
   }
   ```

**Expected Results**:
- Pages created successfully with correct parent_id
- List returns all pages with hierarchy
- Move operation updates parent correctly
- No errors

**Report If**:
- Pages created under wrong parent
- List doesn't show all pages
- Move operation fails
- Performance issues (>500ms response)

---

### Scenario 2: Add Rich Content with Blocks

**Goal**: Create a page with multiple block types and verify embeddings

**Steps**:

1. Create a new page "Product Requirements"
   ```bash
   POST /v1/ocean/pages
   ```

2. Create heading block
   ```bash
   POST /v1/ocean/blocks
   {
     "page_id": "{{page_id}}",
     "organization_id": "{{org_id}}",
     "block_type": "heading",
     "content": "User Authentication Feature",
     "metadata": {"level": 1},
     "position": 0
   }
   ```

3. Create text block with detailed content
   ```bash
   POST /v1/ocean/blocks
   {
     "page_id": "{{page_id}}",
     "organization_id": "{{org_id}}",
     "block_type": "text",
     "content": "Implement secure user authentication using JWT tokens with refresh token rotation. Include email verification and password reset functionality.",
     "position": 1
   }
   ```

4. Create task list
   ```bash
   POST /v1/ocean/blocks/batch
   {
     "blocks": [
       {
         "page_id": "{{page_id}}",
         "organization_id": "{{org_id}}",
         "block_type": "task",
         "content": "Design database schema",
         "metadata": {"completed": false},
         "position": 2
       },
       {
         "page_id": "{{page_id}}",
         "organization_id": "{{org_id}}",
         "block_type": "task",
         "content": "Implement JWT generation",
         "metadata": {"completed": false},
         "position": 3
       }
     ]
   }
   ```

5. Get block embedding
   ```bash
   GET /v1/ocean/blocks/{{block_id}}/embedding
   ```

**Expected Results**:
- All blocks created successfully
- Position order maintained
- Embedding generated (768-dimension vector)
- Batch create returns all block IDs
- Content stored correctly

**Report If**:
- Blocks created out of order
- Embedding missing or wrong dimensions
- Batch create fails partially
- Content truncated or corrupted

---

### Scenario 3: Semantic Search

**Goal**: Test search quality and filtering

**Steps**:

1. Create multiple pages with diverse content
   - Page 1: "Authentication" (content about JWT, OAuth, security)
   - Page 2: "Database Design" (content about PostgreSQL, schemas)
   - Page 3: "API Development" (content about REST, endpoints)

2. Search for "user login security"
   ```bash
   GET /v1/ocean/search?q=user login security&organization_id={{org_id}}&search_type=semantic&limit=10
   ```

3. Search with block type filter
   ```bash
   GET /v1/ocean/search?q=authentication&organization_id={{org_id}}&block_types=heading,text&search_type=hybrid
   ```

4. Search with metadata filter
   ```bash
   GET /v1/ocean/search?q=database&organization_id={{org_id}}&search_type=metadata
   ```

**Expected Results**:
- Semantic search returns relevant results (Auth page ranked highest)
- Block type filter excludes tasks/lists
- Results include similarity scores
- Pagination works correctly
- Response time <1 second

**Report If**:
- Irrelevant results ranked highly
- Filters not applied correctly
- Missing similarity scores
- Slow search (>2 seconds)
- No results when content exists

---

### Scenario 4: Link Pages and Blocks

**Goal**: Create bidirectional links and verify backlinks

**Steps**:

1. Create two pages: "Design Doc" and "API Spec"

2. Create link from Design Doc to API Spec
   ```bash
   POST /v1/ocean/links
   {
     "organization_id": "{{org_id}}",
     "source_page_id": "{{design_doc_id}}",
     "target_page_id": "{{api_spec_id}}",
     "link_type": "reference"
   }
   ```

3. Get backlinks for API Spec
   ```bash
   GET /v1/ocean/pages/{{api_spec_id}}/backlinks?organization_id={{org_id}}
   ```

4. Create block-to-block link
   ```bash
   POST /v1/ocean/links
   {
     "organization_id": "{{org_id}}",
     "source_block_id": "{{block_a_id}}",
     "target_block_id": "{{block_b_id}}",
     "link_type": "related"
   }
   ```

5. Get block backlinks
   ```bash
   GET /v1/ocean/blocks/{{block_b_id}}/backlinks?organization_id={{org_id}}
   ```

**Expected Results**:
- Links created successfully
- Backlinks show correct source pages/blocks
- Link types stored correctly
- Deleting a link updates backlinks
- No duplicate links allowed

**Report If**:
- Backlinks missing or incorrect
- Duplicate links created
- Link deletion doesn't update backlinks
- Cross-organization links possible

---

### Scenario 5: Tag and Organize

**Goal**: Test tag management and filtering

**Steps**:

1. Create multiple tags
   ```bash
   POST /v1/ocean/tags
   {
     "organization_id": "{{org_id}}",
     "name": "urgent",
     "color": "#FF0000"
   }
   ```
   Repeat for: "feature", "bug", "documentation"

2. Assign tags to blocks
   ```bash
   POST /v1/ocean/blocks/{{block_id}}/tags
   {
     "tag_id": "{{urgent_tag_id}}"
   }
   ```

3. List all tags
   ```bash
   GET /v1/ocean/tags?organization_id={{org_id}}
   ```

4. Get blocks by tag
   ```bash
   GET /v1/ocean/blocks?organization_id={{org_id}}&tag_ids={{urgent_tag_id}}
   ```

5. Remove tag from block
   ```bash
   DELETE /v1/ocean/blocks/{{block_id}}/tags/{{urgent_tag_id}}
   ```

**Expected Results**:
- Tags created with correct colors
- Multiple tags assignable to one block
- Tag filtering returns correct blocks
- Tag removal works
- No duplicate tag assignments

**Report If**:
- Tag colors not saved
- Can't assign multiple tags
- Filtering returns wrong blocks
- Tag deletion fails

---

### Scenario 6: Performance Testing

**Goal**: Verify system handles realistic load

**Steps**:

1. Create page with 100 blocks
   ```bash
   POST /v1/ocean/blocks/batch
   {
     "blocks": [... 100 blocks ...]
   }
   ```

2. Search across large dataset
   ```bash
   GET /v1/ocean/search?q=test&limit=100
   ```

3. List all blocks for a page with 100+ blocks
   ```bash
   GET /v1/ocean/blocks?page_id={{page_id}}&limit=100
   ```

4. Update multiple blocks sequentially (10 updates)

**Expected Results**:
- Batch create completes in <5 seconds
- Search completes in <2 seconds
- List operation <1 second
- Updates complete individually <500ms
- No timeouts or 500 errors

**Report If**:
- Timeouts on batch operations
- Search takes >5 seconds
- Memory errors
- Partial failures in batch

---

### Scenario 7: Error Handling

**Goal**: Verify graceful error handling

**Steps**:

1. Create page with missing required field
   ```bash
   POST /v1/ocean/pages
   {
     "organization_id": "{{org_id}}"
     # missing title
   }
   ```

2. Get non-existent page
   ```bash
   GET /v1/ocean/pages/non-existent-id
   ```

3. Update block with invalid block_type
   ```bash
   PUT /v1/ocean/blocks/{{block_id}}
   {
     "block_type": "invalid_type"
   }
   ```

4. Create link with invalid IDs
   ```bash
   POST /v1/ocean/links
   {
     "organization_id": "{{org_id}}",
     "source_page_id": "invalid-id",
     "target_page_id": "also-invalid"
   }
   ```

**Expected Results**:
- 400 Bad Request with clear error message
- 404 Not Found for non-existent resources
- 422 Unprocessable Entity for validation errors
- Error messages indicate what's wrong
- No 500 Internal Server Errors

**Report If**:
- 500 errors for validation issues
- Unclear error messages
- Missing error details
- Stack traces exposed

---

### Scenario 8: Multi-Tenant Isolation

**Goal**: Verify data isolation between organizations

**Steps**:

1. Create page in your organization

2. Try to access with different organization_id
   ```bash
   GET /v1/ocean/pages/{{page_id}}?organization_id=different-org
   ```

3. Try to update with wrong organization_id
   ```bash
   PUT /v1/ocean/pages/{{page_id}}
   {
     "organization_id": "different-org",
     "title": "Unauthorized Update"
   }
   ```

4. Search with different organization_id
   ```bash
   GET /v1/ocean/search?q=test&organization_id=different-org
   ```

**Expected Results**:
- 404 Not Found when accessing other org's data
- 403 Forbidden on unauthorized updates
- Search returns no results from other orgs
- No data leakage between organizations

**Report If**:
- Can access other organization's data
- Can update other organization's data
- Search returns cross-org results
- ANY multi-tenant isolation breach (CRITICAL BUG)

---

### Scenario 9: Edge Cases

**Goal**: Test boundary conditions

**Steps**:

1. Create block with empty content
   ```bash
   POST /v1/ocean/blocks
   {
     "page_id": "{{page_id}}",
     "organization_id": "{{org_id}}",
     "block_type": "text",
     "content": "",
     "position": 0
   }
   ```

2. Create block with very long content (10,000 characters)

3. Create 1,000 tags

4. Assign 50 tags to one block

5. Create circular page references
   - Page A links to Page B
   - Page B links to Page C
   - Page C links to Page A

**Expected Results**:
- Empty content blocks allowed
- Long content handled correctly (no truncation)
- Large number of tags supported
- Multiple tags per block supported
- Circular links allowed (no graph cycle detection needed)

**Report If**:
- Content truncated unexpectedly
- Tag limits hit unexpectedly
- Circular references cause errors
- System hangs on large operations

---

### Scenario 10: Mobile API Usage

**Goal**: Verify API suitable for mobile clients

**Steps**:

1. Test pagination with small page sizes
   ```bash
   GET /v1/ocean/pages?organization_id={{org_id}}&limit=10&offset=0
   ```

2. Test incremental loading
   ```bash
   GET /v1/ocean/blocks?page_id={{page_id}}&limit=20&offset=0
   GET /v1/ocean/blocks?page_id={{page_id}}&limit=20&offset=20
   ```

3. Test search with limit
   ```bash
   GET /v1/ocean/search?q=test&limit=5
   ```

4. Measure response sizes (should be <100KB for typical requests)

5. Test with slow network simulation (optional)

**Expected Results**:
- Pagination works correctly
- Responses are reasonably sized
- No unnecessary data returned
- Offset/limit respected
- Works on mobile network speeds

**Report If**:
- Large response payloads (>500KB)
- Missing pagination support
- Slow responses (>3 seconds)
- Incomplete data in paginated responses

---

## 🐛 How to Report Issues

### Use GitHub Issues

**Create a new issue**: https://github.com/AINative-Studio/ocean-backend/issues/new

**Use Bug Report Template**: `.github/ISSUE_TEMPLATE/bug_report.md`

### Bug Report Should Include

1. **Title**: Clear, descriptive (e.g., "Search returns irrelevant results for exact keyword match")
2. **Severity**: Critical / High / Medium / Low
3. **Type**: [BUG] or [FEATURE REQUEST]
4. **Environment**: Staging/Production, OS, API client
5. **Steps to Reproduce**: Exact API calls with request bodies
6. **Expected Behavior**: What should happen
7. **Actual Behavior**: What actually happens
8. **API Request/Response**: Full curl command and response
9. **Screenshots**: If applicable (Postman, error messages)
10. **Impact**: How it affects your usage

### Severity Definitions

- **Critical**: Data loss, security breach, multi-tenant isolation failure, API completely down
- **High**: Major functionality broken, incorrect data returned, significant performance issue
- **Medium**: Feature partially broken, minor data issues, moderate performance degradation
- **Low**: UI/UX improvement, documentation issue, minor edge case

### Example Bug Report

```markdown
**Title**: [BUG] Search returns blocks from other organizations

**Severity**: CRITICAL

**Environment**:
- API: https://ocean-backend-staging.railway.app
- Org ID: org_12345
- Date: 2024-12-24

**Steps to Reproduce**:
1. Create block in org_12345
2. Search with org_67890: GET /v1/ocean/search?q=test&organization_id=org_67890
3. Block from org_12345 appears in results

**Expected**: No results (different org)
**Actual**: Block from org_12345 returned

**API Request**:
```bash
curl -X GET "https://ocean-backend-staging.railway.app/v1/ocean/search?q=test&organization_id=org_67890" \
  -H "Authorization: Bearer {{api_key}}"
```

**Response**:
```json
{
  "results": [
    {
      "block_id": "block_abc",
      "organization_id": "org_12345",
      "content": "test content"
    }
  ]
}
```

**Impact**: CRITICAL - Multi-tenant data leakage
```

---

## 📊 Feedback Survey

After completing testing, please fill out this survey:

### Overall Experience

1. How easy was it to set up and start testing? (1-5)
2. How clear were the test scenarios? (1-5)
3. How would you rate the API documentation? (1-5)
4. Overall satisfaction with Ocean Backend? (1-5)

### Feature-Specific Feedback

1. **Page Management**: What worked well? What needs improvement?
2. **Block Operations**: Any missing block types? Performance issues?
3. **Search Quality**: Were search results relevant? Any false positives?
4. **Linking**: Easy to understand? Any confusion?
5. **Tags**: Sufficient functionality? Missing features?

### Performance

1. Were response times acceptable? (Any slow endpoints?)
2. Did you experience any timeouts or errors?
3. How was the API performance under load?

### Documentation

1. Were error messages helpful?
2. Was the API reference clear?
3. What documentation is missing?

### Feature Requests

1. What features are missing that you expected?
2. What would make Ocean Backend more useful?
3. Any nice-to-have features?

### Open Feedback

[Your general thoughts, suggestions, concerns]

---

## 🔧 API Testing with Postman

### Import Collection

1. Open Postman
2. Import `ocean-backend.postman_collection.json`
3. Create environment:
   - `base_url`: `https://ocean-backend-staging.railway.app`
   - `org_id`: Your organization ID
   - `api_key`: Your API key

### Run Tests

1. **Individual Tests**: Click on request → Send
2. **Folder Tests**: Right-click folder → Run
3. **Full Suite**: Collection → Run → Run Ocean Backend

### Environment Variables

The collection uses these variables (auto-populated):
- `{{base_url}}`: API base URL
- `{{org_id}}`: Your organization ID
- `{{api_key}}`: Your API key
- `{{page_id}}`: Created by page tests
- `{{block_id}}`: Created by block tests
- `{{tag_id}}`: Created by tag tests
- `{{link_id}}`: Created by link tests

### Test Assertions

Each request includes test assertions to verify:
- Status code (200, 201, 404, etc.)
- Response structure
- Required fields present
- Data types correct
- Business logic (e.g., position increments)

### View Test Results

- **Tests Tab**: See which assertions passed/failed
- **Console**: View detailed request/response logs
- **Runner**: See test suite summary

---

## ✅ Expected Results Summary

### Performance Benchmarks

| Operation | Expected Time | Max Acceptable |
|-----------|--------------|----------------|
| Create page | <200ms | 500ms |
| Create block | <300ms | 800ms |
| Batch create (10 blocks) | <1s | 3s |
| Search (10 results) | <500ms | 2s |
| List pages (100 items) | <300ms | 1s |
| Update block | <200ms | 500ms |
| Delete operation | <200ms | 500ms |

### Data Integrity

- ✅ All pages have unique IDs
- ✅ Blocks maintain position order
- ✅ Embeddings generated for text blocks (768 dimensions)
- ✅ Multi-tenant isolation enforced
- ✅ Parent-child relationships maintained
- ✅ Backlinks updated on link creation/deletion
- ✅ Tags correctly assigned/removed
- ✅ Soft deletes preserve data

### Search Quality

- ✅ Semantic search returns relevant results
- ✅ Similarity scores between 0.0-1.0
- ✅ Filters applied correctly
- ✅ Results ordered by relevance (semantic) or date (metadata)
- ✅ No duplicate results

### Error Handling

- ✅ 400 for invalid requests
- ✅ 404 for not found resources
- ✅ 422 for validation errors
- ✅ 500 only for unexpected server errors
- ✅ Clear error messages with details
- ✅ No stack traces exposed in production

---

## 🆘 Support

### Questions During Testing

- **Slack**: #ocean-beta-testing
- **Email**: beta@ainative.studio
- **GitHub Discussions**: https://github.com/AINative-Studio/ocean-backend/discussions

### Report Bugs

- **GitHub Issues**: https://github.com/AINative-Studio/ocean-backend/issues
- Use bug report template

### Request Features

- **GitHub Issues**: Use `[FEATURE REQUEST]` label
- Describe use case and expected behavior

---

## 📅 Timeline

- **Beta Start**: December 24, 2024
- **Testing Period**: 1-2 weeks
- **Feedback Deadline**: January 7, 2025
- **Bug Fix Sprint**: January 8-14, 2025
- **Production Release**: January 15, 2025 (target)

---

## 🎁 Beta Tester Benefits

- **Early Access**: Use Ocean before public release
- **Free Credits**: $100 ZeroDB credits
- **Acknowledgment**: Listed as beta tester in release notes
- **Direct Input**: Your feedback shapes the product
- **Priority Support**: Fast response to your issues

---

## 📝 Checklist for Beta Testers

Before submitting feedback:

- [ ] Completed at least 5 test scenarios
- [ ] Tested all critical features (pages, blocks, search, links, tags)
- [ ] Reported any bugs found
- [ ] Filled out feedback survey
- [ ] Tested performance (response times)
- [ ] Verified error handling
- [ ] Tested multi-tenant isolation
- [ ] Tried Postman collection
- [ ] Read API documentation
- [ ] Provided at least 3 specific pieces of feedback

---

**Thank you for participating in Ocean Backend beta testing!** 🙏

Your feedback is invaluable in making Ocean the best block-based knowledge workspace API.

For any questions, contact: beta@ainative.studio
