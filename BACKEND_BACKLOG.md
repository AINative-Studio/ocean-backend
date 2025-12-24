# Ocean Backend - Development Backlog

**Project**: Ocean Backend (FastAPI + ZeroDB)
**Repository**: `ainative-studio/ocean-backend`
**Sprint Duration**: 1 week sprints
**Total Estimate**: 2-3 weeks (3 sprints)

---

## Sprint 1: Foundation & Page Operations (Week 1)

### Epic 1.1: ZeroDB Setup & Configuration
**Story Points**: 3 points

#### Issue #1: Set up ZeroDB project and environment
**Type**: Setup
**Priority**: Critical
**Estimate**: 2 points

**Description**:
Create ZeroDB project for Ocean backend and configure development environment.

**Tasks**:
- [ ] Create ZeroDB project via dashboard or API
- [ ] Generate API key and JWT tokens
- [ ] Configure `.env` file with credentials
- [ ] Set up Python virtual environment
- [ ] Install dependencies: `zerodb-mcp`, `fastapi`, `httpx`, `pydantic`
- [ ] Test connection to ZeroDB API

**Acceptance Criteria**:
- [ ] ZeroDB project created and accessible
- [ ] API credentials stored securely in `.env`
- [ ] Connection test passes (can query project info)
- [ ] All dependencies installed without errors

**Technical Notes**:
```bash
# Required env vars
ZERODB_API_URL=https://api.ainative.studio
ZERODB_PROJECT_ID=<project-id>
ZERODB_API_KEY=<api-key>
OCEAN_EMBEDDINGS_MODEL=BAAI/bge-base-en-v1.5
```

---

#### Issue #2: Create ZeroDB NoSQL tables
**Type**: Database
**Priority**: Critical
**Estimate**: 1 point

**Description**:
Create all required NoSQL tables in ZeroDB: `ocean_pages`, `ocean_blocks`, `ocean_block_links`, `ocean_tags`.

**Tasks**:
- [ ] Create `ocean_pages` table with schema
- [ ] Create `ocean_blocks` table with schema
- [ ] Create `ocean_block_links` table with schema
- [ ] Create `ocean_tags` table with schema
- [ ] Add indexes for performance
- [ ] Write table creation script (`scripts/setup_tables.py`)

**Acceptance Criteria**:
- [ ] All 4 tables created successfully
- [ ] Indexes applied correctly
- [ ] Script can be run idempotently (skip if exists)
- [ ] Tables visible in ZeroDB dashboard

**Schema Reference**:
See `ZERODB_IMPLEMENTATION_PLAN.md` Part 2 for complete schemas.

---

#### Issue #3: Test ZeroDB Embeddings API integration
**Type**: Integration
**Priority**: Critical
**Estimate**: 2 points

**Description**:
Verify ZeroDB Embeddings API works correctly with all three endpoints: generate, embed-and-store, search.

**Tasks**:
- [ ] Test `/api/v1/embeddings/generate` endpoint
- [ ] Test `/v1/{project_id}/embeddings/embed-and-store` endpoint
- [ ] Test `/v1/{project_id}/embeddings/search` endpoint
- [ ] Verify 768-dimension vectors generated correctly
- [ ] Verify model consistency (BAAI/bge-base-en-v1.5)
- [ ] Write integration test suite

**Acceptance Criteria**:
- [ ] Can generate embeddings for text
- [ ] Can store vectors with metadata
- [ ] Can search vectors with semantic similarity
- [ ] All tests pass with >0.7 similarity threshold
- [ ] Embedding dimensions = 768

---

### Epic 1.2: Page CRUD Operations
**Story Points**: 5 points

#### Issue #4: Implement OceanService - Page operations
**Type**: Feature
**Priority**: High
**Estimate**: 3 points

**Description**:
Create `OceanService` class with complete page CRUD operations using ZeroDB NoSQL tables.

**Tasks**:
- [ ] Create `src/backend/app/services/ocean_service.py`
- [ ] Implement `create_page()` method
- [ ] Implement `get_page()` method
- [ ] Implement `get_pages()` (list with pagination)
- [ ] Implement `update_page()` method
- [ ] Implement `delete_page()` method (soft delete via is_archived)
- [ ] Implement `move_page()` (change parent)
- [ ] Add multi-tenant isolation (organization_id filter)

**Acceptance Criteria**:
- [ ] All CRUD operations work correctly
- [ ] Pages are organization-scoped (multi-tenant)
- [ ] Position ordering works for nested pages
- [ ] Soft delete (is_archived) implemented
- [ ] Code follows SSCS V2.0 standards (no ORM)

**Code Structure**:
```python
class OceanService:
    def __init__(self):
        self.client = ZeroDBClient(api_key=...)
        self.project_id = ...

    async def create_page(self, org_id, user_id, page_data):
        # Implementation
        pass
```

---

#### Issue #5: Create FastAPI endpoints for pages
**Type**: API
**Priority**: High
**Estimate**: 2 points

**Description**:
Create FastAPI router with all page endpoints at `/v1/ocean/pages`.

**Tasks**:
- [ ] Create `src/backend/app/api/v1/endpoints/ocean_pages.py`
- [ ] Create Pydantic schemas in `src/backend/app/schemas/ocean.py`
- [ ] Implement POST `/v1/ocean/pages` (create)
- [ ] Implement GET `/v1/ocean/pages` (list)
- [ ] Implement GET `/v1/ocean/pages/{page_id}` (get)
- [ ] Implement PUT `/v1/ocean/pages/{page_id}` (update)
- [ ] Implement DELETE `/v1/ocean/pages/{page_id}` (delete)
- [ ] Implement POST `/v1/ocean/pages/{page_id}/move` (move)
- [ ] Add authentication dependency (JWT)
- [ ] Add OpenAPI documentation

**Acceptance Criteria**:
- [ ] All endpoints functional and tested
- [ ] JWT authentication required
- [ ] Organization-scoped responses
- [ ] OpenAPI docs auto-generated
- [ ] Error handling comprehensive

---

#### Issue #6: Write integration tests for pages
**Type**: Testing
**Priority**: High
**Estimate**: 2 points

**Description**:
Create comprehensive integration test suite for page operations.

**Tasks**:
- [ ] Create `src/backend/tests/test_ocean_pages.py`
- [ ] Test create page (single and nested)
- [ ] Test get page by ID
- [ ] Test list pages (pagination, filters)
- [ ] Test update page
- [ ] Test delete page (soft delete)
- [ ] Test move page (change parent)
- [ ] Test multi-tenant isolation
- [ ] Achieve 80%+ test coverage

**Acceptance Criteria**:
- [ ] All tests pass
- [ ] Coverage >= 80%
- [ ] Tests use real ZeroDB (no mocks)
- [ ] Multi-tenant isolation verified

---

## Sprint 2: Block Management & Search (Week 2)

### Epic 2.1: Block CRUD Operations
**Story Points**: 8 points

#### Issue #7: Implement OceanService - Block operations
**Type**: Feature
**Priority**: High
**Estimate**: 5 points

**Description**:
Implement complete block CRUD operations with automatic embedding generation using ZeroDB Embeddings API.

**Tasks**:
- [ ] Implement `create_block()` with embedding generation
- [ ] Implement `create_block_batch()` for bulk operations
- [ ] Implement `get_block()` method
- [ ] Implement `get_blocks_by_page()` method
- [ ] Implement `update_block()` (regenerate embedding if content changed)
- [ ] Implement `delete_block()` method
- [ ] Implement `move_block()` (reorder position)
- [ ] Implement `convert_block_type()` (text → task, etc.)
- [ ] Add support for all 6 block types

**Acceptance Criteria**:
- [ ] All block types work (text, heading, list, task, link, page_link)
- [ ] Embeddings auto-generated for searchable content
- [ ] Batch operations support 100+ blocks
- [ ] Content changes trigger embedding regeneration
- [ ] Position ordering works correctly

**Block Types**:
- Text, Heading, List, Task, Link, Page Link

---

#### Issue #8: Create FastAPI endpoints for blocks
**Type**: API
**Priority**: High
**Estimate**: 3 points

**Description**:
Create FastAPI router for block operations at `/v1/ocean/blocks`.

**Tasks**:
- [ ] Create `src/backend/app/api/v1/endpoints/ocean_blocks.py`
- [ ] Implement POST `/v1/ocean/blocks` (create single)
- [ ] Implement POST `/v1/ocean/blocks/batch` (create multiple)
- [ ] Implement GET `/v1/ocean/blocks/{block_id}` (get)
- [ ] Implement GET `/v1/ocean/blocks?page_id={id}` (list by page)
- [ ] Implement PUT `/v1/ocean/blocks/{block_id}` (update)
- [ ] Implement DELETE `/v1/ocean/blocks/{block_id}` (delete)
- [ ] Implement POST `/v1/ocean/blocks/{block_id}/move` (reorder)
- [ ] Implement PUT `/v1/ocean/blocks/{block_id}/convert` (change type)

**Acceptance Criteria**:
- [ ] All endpoints functional
- [ ] Batch endpoint supports 100+ blocks
- [ ] Embedding generation automatic
- [ ] OpenAPI docs complete

---

#### Issue #9: Write integration tests for blocks
**Type**: Testing
**Priority**: High
**Estimate**: 3 points

**Description**:
Create comprehensive test suite for block operations.

**Tasks**:
- [ ] Create `src/backend/tests/test_ocean_blocks.py`
- [ ] Test create block (all 6 types)
- [ ] Test batch create (100 blocks)
- [ ] Test get block
- [ ] Test update block (with embedding regeneration)
- [ ] Test delete block
- [ ] Test move block (position reordering)
- [ ] Test convert block type
- [ ] Verify embeddings generated correctly
- [ ] Achieve 80%+ coverage

**Acceptance Criteria**:
- [ ] All tests pass
- [ ] Coverage >= 80%
- [ ] Embedding generation verified
- [ ] All block types tested

---

### Epic 2.2: Linking & Backlinks
**Story Points**: 5 points

#### Issue #10: Implement link management
**Type**: Feature
**Priority**: Medium
**Estimate**: 3 points

**Description**:
Implement block/page linking system with bidirectional references and backlink calculation.

**Tasks**:
- [ ] Implement `create_link()` method
- [ ] Implement `delete_link()` method
- [ ] Implement `get_page_backlinks()` method
- [ ] Implement `get_block_backlinks()` method
- [ ] Add circular reference detection
- [ ] Support link types (reference, embed, mention)

**Acceptance Criteria**:
- [ ] Can create block-to-block links
- [ ] Can create block-to-page links
- [ ] Backlinks calculated correctly
- [ ] Circular references prevented
- [ ] Link deletion cascades properly

---

#### Issue #11: Create link API endpoints
**Type**: API
**Priority**: Medium
**Estimate**: 2 points

**Description**:
Create FastAPI router for link operations.

**Tasks**:
- [ ] Create `src/backend/app/api/v1/endpoints/ocean_links.py`
- [ ] Implement POST `/v1/ocean/links` (create)
- [ ] Implement DELETE `/v1/ocean/links/{link_id}` (delete)
- [ ] Implement GET `/v1/ocean/pages/{page_id}/backlinks` (page backlinks)
- [ ] Implement GET `/v1/ocean/blocks/{block_id}/backlinks` (block backlinks)

**Acceptance Criteria**:
- [ ] All endpoints functional
- [ ] Backlinks endpoint returns complete data
- [ ] Circular reference errors handled

---

#### Issue #12: Write tests for linking system
**Type**: Testing
**Priority**: Medium
**Estimate**: 2 points

**Description**:
Test linking and backlink functionality.

**Tasks**:
- [ ] Create `src/backend/tests/test_ocean_links.py`
- [ ] Test create link
- [ ] Test delete link
- [ ] Test backlink calculation
- [ ] Test circular reference detection
- [ ] Achieve 80%+ coverage

---

### Epic 2.3: Search Functionality
**Story Points**: 5 points

#### Issue #13: Implement hybrid search
**Type**: Feature
**Priority**: High
**Estimate**: 3 points

**Description**:
Implement hybrid search combining ZeroDB semantic search with metadata filtering.

**Tasks**:
- [ ] Implement `search()` method with hybrid approach
- [ ] Implement semantic search using ZeroDB Embeddings API
- [ ] Implement metadata filtering (block types, tags, dates)
- [ ] Implement result ranking and deduplication
- [ ] Add search result pagination
- [ ] Optimize search performance (<200ms)

**Acceptance Criteria**:
- [ ] Semantic search works with 768-dim embeddings
- [ ] Metadata filters work correctly
- [ ] Hybrid results ranked by relevance
- [ ] Response time <200ms (p95)
- [ ] Pagination works correctly

---

#### Issue #14: Create search API endpoint
**Type**: API
**Priority**: High
**Estimate**: 2 points

**Description**:
Create search endpoint at `/v1/ocean/search`.

**Tasks**:
- [ ] Create `src/backend/app/api/v1/endpoints/ocean_search.py`
- [ ] Implement GET `/v1/ocean/search?q={query}` (search)
- [ ] Add filters: block_types, tags, date_range
- [ ] Add pagination: limit, offset
- [ ] Add search type: semantic, metadata, hybrid

**Acceptance Criteria**:
- [ ] Search endpoint functional
- [ ] All filters work correctly
- [ ] Pagination works
- [ ] Response includes relevance scores

---

## Sprint 3: Tags, Polish & Deployment (Week 3)

### Epic 3.1: Tag Management
**Story Points**: 3 points

#### Issue #15: Implement tag operations
**Type**: Feature
**Priority**: Medium
**Estimate**: 2 points

**Description**:
Implement tag CRUD and assignment functionality.

**Tasks**:
- [ ] Implement `create_tag()` method
- [ ] Implement `get_tags()` method
- [ ] Implement `update_tag()` method
- [ ] Implement `delete_tag()` method
- [ ] Implement `assign_tag_to_block()` method
- [ ] Implement `remove_tag_from_block()` method
- [ ] Track tag usage count

**Acceptance Criteria**:
- [ ] Tag CRUD works correctly
- [ ] Tags are organization-scoped
- [ ] Tag assignment works
- [ ] Usage count updated automatically

---

#### Issue #16: Create tag API endpoints
**Type**: API
**Priority**: Medium
**Estimate**: 1 point

**Description**:
Create tag endpoints at `/v1/ocean/tags`.

**Tasks**:
- [ ] Create `src/backend/app/api/v1/endpoints/ocean_tags.py`
- [ ] Implement POST `/v1/ocean/tags` (create)
- [ ] Implement GET `/v1/ocean/tags` (list)
- [ ] Implement PUT `/v1/ocean/tags/{tag_id}` (update)
- [ ] Implement DELETE `/v1/ocean/tags/{tag_id}` (delete)
- [ ] Implement POST `/v1/ocean/blocks/{block_id}/tags` (assign)
- [ ] Implement DELETE `/v1/ocean/blocks/{block_id}/tags/{tag_id}` (remove)

---

### Epic 3.2: Performance & Optimization
**Story Points**: 5 points

#### Issue #17: Optimize database queries
**Type**: Performance
**Priority**: High
**Estimate**: 2 points

**Description**:
Optimize ZeroDB queries for production performance.

**Tasks**:
- [ ] Add caching layer (Redis) for frequently accessed data
- [ ] Implement query result pagination everywhere
- [ ] Optimize batch operations
- [ ] Add database query logging
- [ ] Benchmark critical operations

**Acceptance Criteria**:
- [ ] All API endpoints respond <100ms (p95)
- [ ] Batch operations handle 100+ blocks
- [ ] Cache hit rate >50%

---

#### Issue #18: Add rate limiting via Kong
**Type**: Infrastructure
**Priority**: High
**Estimate**: 2 points

**Description**:
Configure Kong Gateway rate limiting for Ocean API endpoints.

**Tasks**:
- [ ] Configure Kong routes for `/v1/ocean/*`
- [ ] Set rate limits per endpoint
- [ ] Add API key validation
- [ ] Configure CORS settings
- [ ] Test rate limiting behavior

**Acceptance Criteria**:
- [ ] Rate limiting active on all endpoints
- [ ] API key validation works
- [ ] CORS configured correctly

---

#### Issue #19: Write comprehensive API documentation
**Type**: Documentation
**Priority**: High
**Estimate**: 3 points

**Description**:
Create complete API documentation for Ocean backend.

**Tasks**:
- [ ] Write API reference with all endpoints
- [ ] Create code examples (Python, TypeScript, cURL)
- [ ] Document authentication flow
- [ ] Document error codes and responses
- [ ] Create SDK usage examples
- [ ] Add OpenAPI/Swagger UI

**Acceptance Criteria**:
- [ ] All endpoints documented
- [ ] Code examples tested and working
- [ ] Swagger UI accessible at `/docs`

---

### Epic 3.3: Testing & Deployment
**Story Points**: 5 points

#### Issue #20: Achieve 80%+ test coverage
**Type**: Testing
**Priority**: High
**Estimate**: 3 points

**Description**:
Increase test coverage across entire backend codebase.

**Tasks**:
- [ ] Write missing unit tests
- [ ] Write integration tests for all endpoints
- [ ] Add performance tests
- [ ] Add load testing (1000+ concurrent requests)
- [ ] Generate coverage report

**Acceptance Criteria**:
- [ ] Unit test coverage >= 80%
- [ ] Integration test coverage >= 80%
- [ ] All tests pass
- [ ] Load tests pass (1000 RPS)

---

#### Issue #21: Deploy to staging environment
**Type**: DevOps
**Priority**: Critical
**Estimate**: 2 points

**Description**:
Deploy Ocean backend to Railway staging environment.

**Tasks**:
- [ ] Create Railway project for Ocean backend
- [ ] Configure environment variables
- [ ] Set up CI/CD pipeline (GitHub Actions)
- [ ] Deploy to staging
- [ ] Verify all endpoints work in staging
- [ ] Run smoke tests

**Acceptance Criteria**:
- [ ] Backend deployed successfully
- [ ] All endpoints accessible
- [ ] Smoke tests pass
- [ ] Monitoring configured

---

#### Issue #22: Beta testing & bug fixes
**Type**: QA
**Priority**: High
**Estimate**: 3 points

**Description**:
Conduct beta testing and fix reported issues.

**Tasks**:
- [ ] Invite 5-10 beta users
- [ ] Collect feedback
- [ ] Fix critical bugs
- [ ] Address performance issues
- [ ] Update documentation based on feedback

**Acceptance Criteria**:
- [ ] No critical bugs reported
- [ ] Beta user satisfaction >80%
- [ ] All feedback addressed or tracked

---

## Summary

### Total Story Points: 39 points
- **Sprint 1** (Week 1): 13 points - Foundation & Pages
- **Sprint 2** (Week 2): 18 points - Blocks, Links, Search
- **Sprint 3** (Week 3): 13 points - Tags, Polish, Deploy

### Team Capacity
- **2 backend developers**: ~20-25 points/week
- **Timeline**: 2-3 weeks for MVP

### Critical Path
1. ZeroDB setup (Issues #1-3)
2. Page operations (Issues #4-6)
3. Block operations (Issues #7-9)
4. Search implementation (Issues #13-14)
5. Testing & deployment (Issues #20-21)

---

## Issue Labels

- `epic` - Epic-level issues
- `feature` - New feature implementation
- `api` - API endpoint development
- `database` - Database/ZeroDB work
- `testing` - Test development
- `performance` - Performance optimization
- `documentation` - Documentation
- `devops` - Deployment & infrastructure
- `critical` - Must-have for MVP
- `high` - Important but not blocking
- `medium` - Nice to have

---

## Dependencies

```
Issue #4 → Issue #5 → Issue #6 (Pages)
Issue #7 → Issue #8 → Issue #9 (Blocks)
Issue #10 → Issue #11 → Issue #12 (Links)
Issue #13 → Issue #14 (Search)
Issue #15 → Issue #16 (Tags)

All testing depends on implementation
Deployment depends on all features + tests
```

---

**Ready to create GitHub issues!**
