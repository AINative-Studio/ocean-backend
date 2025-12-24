# Ocean MVP - Day 1 Setup Checklist

**Start Date**: TBD
**Goal**: Set up ZeroDB project + test embeddings integration

---

## Morning Tasks (2-3 hours)

### 1. ZeroDB Project Setup

- [ ] Create new ZeroDB project for Ocean
  - Project name: `ocean_production` (or `ocean_dev` for development)
  - Tier: Select appropriate tier
  - Settings: Enable vectors, tables, files

- [ ] Generate API credentials
  - [ ] API Key created
  - [ ] JWT Token generated (if needed)
  - [ ] Save to `.env` file:
    ```bash
    ZERODB_API_URL=https://api.ainative.studio
    ZERODB_PROJECT_ID=<your-project-id>
    ZERODB_API_KEY=<your-api-key>
    OCEAN_EMBEDDINGS_MODEL=BAAI/bge-base-en-v1.5
    ```

- [ ] Test connection
  ```bash
  python scripts/test_zerodb_connection.py
  ```

### 2. Test ZeroDB Embeddings API

- [ ] Verify embeddings generation works
  ```python
  import httpx
  import os

  async def test_embeddings():
      api_url = os.getenv("ZERODB_API_URL")
      api_key = os.getenv("ZERODB_API_KEY")

      async with httpx.AsyncClient() as client:
          # Test /api/v1/embeddings/generate
          response = await client.post(
              f"{api_url}/api/v1/embeddings/generate",
              headers={"Authorization": f"Bearer {api_key}"},
              json={
                  "texts": ["Test Ocean block content"],
                  "model": "BAAI/bge-base-en-v1.5"
              }
          )

          print(f"Status: {response.status_code}")
          result = response.json()
          print(f"Dimensions: {result['dimensions']}")
          print(f"Model: {result['model']}")
          assert result['dimensions'] == 768
          assert result['model'] == "BAAI/bge-base-en-v1.5"
          print("✅ Embeddings API works!")

  # Run test
  import asyncio
  asyncio.run(test_embeddings())
  ```

- [ ] Verify embed-and-store works
  ```python
  async def test_embed_and_store():
      project_id = os.getenv("ZERODB_PROJECT_ID")
      api_url = os.getenv("ZERODB_API_URL")
      api_key = os.getenv("ZERODB_API_KEY")

      async with httpx.AsyncClient() as client:
          response = await client.post(
              f"{api_url}/v1/{project_id}/embeddings/embed-and-store",
              headers={"Authorization": f"Bearer {api_key}"},
              json={
                  "texts": ["This is a test Ocean block"],
                  "model": "BAAI/bge-base-en-v1.5",
                  "namespace": "ocean_test",
                  "metadata": [{"test": True, "block_id": "test_001"}]
              }
          )

          print(f"Status: {response.status_code}")
          result = response.json()
          print(f"Vectors stored: {result['vectors_stored']}")
          print(f"Dimensions: {result['dimensions']}")
          print(f"Column: {result['target_column']}")
          assert result['dimensions'] == 768
          assert result['target_column'] == "vector_768"
          print("✅ Embed-and-store works!")

  asyncio.run(test_embed_and_store())
  ```

- [ ] Verify semantic search works
  ```python
  async def test_semantic_search():
      project_id = os.getenv("ZERODB_PROJECT_ID")
      api_url = os.getenv("ZERODB_API_URL")
      api_key = os.getenv("ZERODB_API_KEY")

      async with httpx.AsyncClient() as client:
          response = await client.post(
              f"{api_url}/v1/{project_id}/embeddings/search",
              headers={"Authorization": f"Bearer {api_key}"},
              json={
                  "query": "test Ocean block",
                  "model": "BAAI/bge-base-en-v1.5",
                  "namespace": "ocean_test",
                  "limit": 5
              }
          )

          print(f"Status: {response.status_code}")
          result = response.json()
          print(f"Results found: {len(result['results'])}")
          if result['results']:
              print(f"Top similarity: {result['results'][0]['similarity']:.3f}")
              print("✅ Semantic search works!")
          else:
              print("⚠️ No results (might need to wait for indexing)")

  asyncio.run(test_semantic_search())
  ```

---

## Afternoon Tasks (3-4 hours)

### 3. Create ZeroDB Tables

- [ ] Create `ocean_pages` table
  ```python
  from zerodb_mcp import ZeroDBClient

  client = ZeroDBClient(api_key=os.getenv("ZERODB_API_KEY"))

  # Create pages table
  pages_table = await client.tables.create(
      project_id=os.getenv("ZERODB_PROJECT_ID"),
      table_name="ocean_pages",
      schema_definition={
          "page_id": "string",
          "organization_id": "string",
          "user_id": "string",
          "title": "string",
          "icon": "string",
          "cover_image": "string",
          "parent_page_id": "string",
          "position": "integer",
          "is_archived": "boolean",
          "created_at": "timestamp",
          "updated_at": "timestamp",
          "metadata": "object"
      },
      indexes=["page_id", "organization_id", "user_id", "parent_page_id"]
  )

  print(f"✅ Created table: {pages_table['table_name']}")
  ```

- [ ] Create `ocean_blocks` table
  ```python
  blocks_table = await client.tables.create(
      project_id=os.getenv("ZERODB_PROJECT_ID"),
      table_name="ocean_blocks",
      schema_definition={
          "block_id": "string",
          "page_id": "string",
          "organization_id": "string",
          "user_id": "string",
          "block_type": "string",
          "position": "integer",
          "parent_block_id": "string",
          "content": "object",
          "properties": "object",
          "vector_id": "string",
          "vector_dimensions": "integer",
          "created_at": "timestamp",
          "updated_at": "timestamp"
      },
      indexes=["block_id", "page_id", "organization_id", "block_type", "vector_id"]
  )

  print(f"✅ Created table: {blocks_table['table_name']}")
  ```

- [ ] Create `ocean_block_links` table
  ```python
  links_table = await client.tables.create(
      project_id=os.getenv("ZERODB_PROJECT_ID"),
      table_name="ocean_block_links",
      schema_definition={
          "link_id": "string",
          "source_block_id": "string",
          "target_block_id": "string",
          "target_page_id": "string",
          "link_type": "string",
          "created_at": "timestamp"
      },
      indexes=["link_id", "source_block_id", "target_block_id", "target_page_id"]
  )

  print(f"✅ Created table: {links_table['table_name']}")
  ```

- [ ] Create `ocean_tags` table
  ```python
  tags_table = await client.tables.create(
      project_id=os.getenv("ZERODB_PROJECT_ID"),
      table_name="ocean_tags",
      schema_definition={
          "tag_id": "string",
          "organization_id": "string",
          "name": "string",
          "color": "string",
          "usage_count": "integer",
          "created_at": "timestamp"
      },
      indexes=["tag_id", "organization_id", "name"]
  )

  print(f"✅ Created table: {tags_table['table_name']}")
  ```

### 4. Test Table Operations

- [ ] Insert test page
  ```python
  import uuid
  from datetime import datetime

  test_page = await client.tables.insert_rows(
      project_id=os.getenv("ZERODB_PROJECT_ID"),
      table_name="ocean_pages",
      rows=[{
          "page_id": str(uuid.uuid4()),
          "organization_id": "test_org",
          "user_id": "test_user",
          "title": "Test Page",
          "icon": "📄",
          "cover_image": None,
          "parent_page_id": None,
          "position": 0,
          "is_archived": False,
          "created_at": datetime.utcnow().isoformat(),
          "updated_at": datetime.utcnow().isoformat(),
          "metadata": {"color": "blue"}
      }]
  )

  print("✅ Inserted test page")
  ```

- [ ] Insert test block (with embedding)
  ```python
  block_id = str(uuid.uuid4())
  page_id = test_page["rows"][0]["page_id"]

  # Generate and store embedding
  block_text = "This is a test block with searchable content"

  embed_response = await httpx.AsyncClient().post(
      f"{api_url}/v1/{project_id}/embeddings/embed-and-store",
      headers={"Authorization": f"Bearer {api_key}"},
      json={
          "texts": [block_text],
          "model": "BAAI/bge-base-en-v1.5",
          "namespace": "ocean_blocks",
          "metadata": [{
              "block_id": block_id,
              "page_id": page_id,
              "organization_id": "test_org"
          }]
      }
  )

  embed_result = embed_response.json()
  vector_id = embed_result["vector_ids"][0]

  # Insert block
  test_block = await client.tables.insert_rows(
      project_id=os.getenv("ZERODB_PROJECT_ID"),
      table_name="ocean_blocks",
      rows=[{
          "block_id": block_id,
          "page_id": page_id,
          "organization_id": "test_org",
          "user_id": "test_user",
          "block_type": "text",
          "position": 0,
          "parent_block_id": None,
          "content": {"text": block_text},
          "properties": {},
          "vector_id": vector_id,
          "vector_dimensions": 768,
          "created_at": datetime.utcnow().isoformat(),
          "updated_at": datetime.utcnow().isoformat()
      }]
  )

  print("✅ Inserted test block with embedding")
  ```

- [ ] Query blocks
  ```python
  blocks = await client.tables.query_rows(
      project_id=os.getenv("ZERODB_PROJECT_ID"),
      table_name="ocean_blocks",
      filters={"organization_id": "test_org"},
      limit=10
  )

  print(f"✅ Queried blocks: {len(blocks['rows'])} found")
  ```

- [ ] Search blocks semantically
  ```python
  search_response = await httpx.AsyncClient().post(
      f"{api_url}/v1/{project_id}/embeddings/search",
      headers={"Authorization": f"Bearer {api_key}"},
      json={
          "query": "searchable content",
          "model": "BAAI/bge-base-en-v1.5",
          "namespace": "ocean_blocks",
          "limit": 5
      }
  )

  search_results = search_response.json()
  print(f"✅ Search results: {len(search_results['results'])} found")
  if search_results['results']:
      print(f"   Top match similarity: {search_results['results'][0]['similarity']:.3f}")
  ```

---

## Evening Tasks (1-2 hours)

### 5. Set Up Service Layer

- [ ] Create `OceanService` skeleton
  ```python
  # src/backend/app/services/ocean_service.py

  from zerodb_mcp import ZeroDBClient
  import httpx
  import os

  class OceanService:
      """Business logic for Ocean workspace operations"""

      def __init__(self):
          self.client = ZeroDBClient(api_key=os.getenv("ZERODB_API_KEY"))
          self.project_id = os.getenv("ZERODB_PROJECT_ID")
          self.api_url = os.getenv("ZERODB_API_URL")
          self.embeddings_model = os.getenv("OCEAN_EMBEDDINGS_MODEL", "BAAI/bge-base-en-v1.5")

      async def create_page(self, organization_id: str, user_id: str, page_data: dict):
          """Create a new page"""
          # Implementation here
          pass

      async def create_block(self, organization_id: str, user_id: str, block_data: dict):
          """Create a new block with embedding"""
          # Implementation here
          pass

      async def search(self, organization_id: str, query: str, limit: int = 20):
          """Search pages and blocks"""
          # Implementation here
          pass
  ```

- [ ] Write first unit test
  ```python
  # src/backend/tests/test_ocean_service.py

  import pytest
  from app.services.ocean_service import OceanService

  @pytest.mark.asyncio
  async def test_create_page():
      service = OceanService()

      page = await service.create_page(
          organization_id="test_org",
          user_id="test_user",
          page_data={"title": "Test Page"}
      )

      assert page["title"] == "Test Page"
      assert page["organization_id"] == "test_org"
  ```

- [ ] Commit to Git
  ```bash
  git checkout -b feature/ocean-zerodb-setup
  git add .
  git commit -m "Initial Ocean ZeroDB setup

  - Create ZeroDB project and tables
  - Test embeddings API integration
  - Set up OceanService skeleton

  Uses ZeroDB Embeddings API (BAAI/bge-base-en-v1.5, 768 dims)

  Refs #XXX"

  git push origin feature/ocean-zerodb-setup
  ```

---

## Success Criteria

By end of Day 1, you should have:

✅ ZeroDB project created and configured
✅ Embeddings API tested (generate, embed-and-store, search)
✅ All 4 Ocean tables created (pages, blocks, links, tags)
✅ Test data inserted successfully
✅ Semantic search working with 768-dim embeddings
✅ OceanService class skeleton created
✅ First unit test passing
✅ Code committed to Git (no AI attribution!)

---

## Troubleshooting

### Issue: Embeddings API returns 401 Unauthorized
**Solution**: Check API key in `.env` file, verify it's correct

### Issue: Table creation fails
**Solution**: Verify project_id is correct, check ZeroDB dashboard for errors

### Issue: Search returns no results
**Solution**: Wait 5-10 seconds for vector indexing, try again

### Issue: Vector dimensions mismatch
**Solution**: Always use same model for store and search (BAAI/bge-base-en-v1.5)

---

## Next Steps (Day 2)

After completing Day 1 setup:

1. Implement `OceanService.create_page()` fully
2. Implement `OceanService.create_block()` with embeddings
3. Create FastAPI endpoints for pages
4. Write integration tests
5. Deploy to staging environment

---

**Ready to start Day 1!** 🚀
