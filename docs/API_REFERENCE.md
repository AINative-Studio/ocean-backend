# Ocean API Reference

**Version:** 0.1.0
**Base URL:** `http://localhost:8000` (development) | `https://ocean.ainative.studio` (production)
**API Prefix:** `/api/v1/ocean`

---

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Pages Endpoints](#pages-endpoints) (6 endpoints)
4. [Blocks Endpoints](#blocks-endpoints) (10 endpoints)
5. [Links Endpoints](#links-endpoints) (4 endpoints)
6. [Tags Endpoints](#tags-endpoints) (6 endpoints)
7. [Search Endpoint](#search-endpoint) (1 endpoint)
8. [Response Format](#response-format)
9. [Error Handling](#error-handling)

**Total Endpoints:** 27

---

## Overview

Ocean is a Notion-like workspace built on ZeroDB serverless infrastructure. The API provides comprehensive endpoints for managing pages, blocks, links, tags, and semantic search.

### Key Features

- **Pages Management**: Create hierarchical page structures with nesting
- **Blocks Management**: Rich content blocks with automatic embedding generation
- **Semantic Search**: Hybrid vector search powered by BAAI/bge-base-en-v1.5 embeddings (768 dimensions)
- **Block Linking**: Bidirectional links between blocks and pages with circular reference detection
- **Tagging System**: Organization-scoped tags with usage tracking
- **Multi-Tenant**: Complete organization-level isolation for all resources

### Technical Stack

- **Framework**: FastAPI 0.115.6
- **Database**: ZeroDB (NoSQL tables + vector search)
- **Embeddings**: BAAI/bge-base-en-v1.5 (768 dimensions)
- **Authentication**: JWT tokens (Bearer token authentication)

---

## Authentication

All API endpoints (except `/health` and `/`) require authentication.

### Authentication Header

```http
Authorization: Bearer <JWT_TOKEN>
```

### Getting a Token

Authentication is handled by the parent authentication system. The JWT token must include:

```json
{
  "user_id": "test-user-123",
  "organization_id": "test-org-456",
  "exp": 1735123456
}
```

### Multi-Tenant Isolation

All resources are scoped to `organization_id` extracted from the JWT token. Users can only access resources belonging to their organization.

**See:** [AUTHENTICATION.md](./AUTHENTICATION.md) for detailed authentication flows.

---

## Pages Endpoints

Pages are the top-level containers in Ocean. They can be nested to create hierarchies and contain blocks.

### 1. Create Page

Create a new page in the workspace.

**Endpoint:** `POST /api/v1/ocean/pages`

**Request Body:**

```json
{
  "title": "Product Roadmap",
  "icon": "🚀",
  "cover_image": null,
  "parent_page_id": null,
  "metadata": {}
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | Yes | Page title (1-500 characters) |
| `icon` | string | No | Emoji or icon identifier |
| `cover_image` | string | No | Cover image URL or file_id |
| `parent_page_id` | string | No | Parent page ID for nesting (null = root level) |
| `metadata` | object | No | Additional page properties |

**Response:** `201 Created`

```json
{
  "page_id": "550e8400-e29b-41d4-a716-446655440000",
  "organization_id": "test-org-456",
  "user_id": "test-user-123",
  "title": "Product Roadmap",
  "icon": "🚀",
  "cover_image": null,
  "parent_page_id": null,
  "position": 0,
  "is_archived": false,
  "is_favorite": false,
  "created_at": "2025-12-24T10:00:00Z",
  "updated_at": "2025-12-24T10:00:00Z",
  "metadata": {}
}
```

**Errors:**

- `400 Bad Request` - Invalid request data (e.g., title too long)
- `401 Unauthorized` - Missing or invalid JWT token
- `500 Internal Server Error` - Failed to create page

**Example cURL:**

```bash
curl -X POST http://localhost:8000/api/v1/ocean/pages \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Product Roadmap",
    "icon": "🚀"
  }'
```

---

### 2. List Pages

Get all pages for the current organization with optional filtering and pagination.

**Endpoint:** `GET /api/v1/ocean/pages`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `parent_page_id` | string | null | Filter by parent page ID |
| `is_archived` | boolean | null | Filter by archived status |
| `is_favorite` | boolean | null | Filter favorite pages |
| `limit` | integer | 50 | Max results (1-100) |
| `offset` | integer | 0 | Skip results for pagination |

**Response:** `200 OK`

```json
{
  "pages": [
    {
      "page_id": "550e8400-e29b-41d4-a716-446655440000",
      "organization_id": "test-org-456",
      "user_id": "test-user-123",
      "title": "Product Roadmap",
      "icon": "🚀",
      "cover_image": null,
      "parent_page_id": null,
      "position": 0,
      "is_archived": false,
      "is_favorite": true,
      "created_at": "2025-12-24T10:00:00Z",
      "updated_at": "2025-12-24T10:00:00Z",
      "metadata": {}
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

**Example cURL:**

```bash
# Get all pages
curl -X GET "http://localhost:8000/api/v1/ocean/pages" \
  -H "Authorization: Bearer <JWT_TOKEN>"

# Get favorite pages only
curl -X GET "http://localhost:8000/api/v1/ocean/pages?is_favorite=true" \
  -H "Authorization: Bearer <JWT_TOKEN>"

# Get root-level pages (no parent)
curl -X GET "http://localhost:8000/api/v1/ocean/pages?parent_page_id=null" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

---

### 3. Get Page by ID

Retrieve a specific page by its ID.

**Endpoint:** `GET /api/v1/ocean/pages/{page_id}`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page_id` | string | Yes | Unique page identifier |

**Response:** `200 OK`

```json
{
  "page_id": "550e8400-e29b-41d4-a716-446655440000",
  "organization_id": "test-org-456",
  "user_id": "test-user-123",
  "title": "Product Roadmap",
  "icon": "🚀",
  "cover_image": null,
  "parent_page_id": null,
  "position": 0,
  "is_archived": false,
  "is_favorite": true,
  "created_at": "2025-12-24T10:00:00Z",
  "updated_at": "2025-12-24T10:00:00Z",
  "metadata": {}
}
```

**Errors:**

- `404 Not Found` - Page not found or doesn't belong to organization

**Example cURL:**

```bash
curl -X GET http://localhost:8000/api/v1/ocean/pages/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

---

### 4. Update Page

Update an existing page. Only fields provided in the request body will be updated.

**Endpoint:** `PUT /api/v1/ocean/pages/{page_id}`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page_id` | string | Yes | Unique page identifier |

**Request Body:**

```json
{
  "title": "Updated Product Roadmap",
  "icon": "📋",
  "is_favorite": true
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `title` | string | No | New page title |
| `icon` | string | No | New page icon |
| `cover_image` | string | No | New cover image |
| `is_favorite` | boolean | No | Toggle favorite status |
| `metadata` | object | No | Update metadata |

**Response:** `200 OK`

```json
{
  "page_id": "550e8400-e29b-41d4-a716-446655440000",
  "organization_id": "test-org-456",
  "user_id": "test-user-123",
  "title": "Updated Product Roadmap",
  "icon": "📋",
  "cover_image": null,
  "parent_page_id": null,
  "position": 0,
  "is_archived": false,
  "is_favorite": true,
  "created_at": "2025-12-24T10:00:00Z",
  "updated_at": "2025-12-24T15:30:00Z",
  "metadata": {}
}
```

**Errors:**

- `400 Bad Request` - No fields provided for update
- `404 Not Found` - Page not found or doesn't belong to organization

**Example cURL:**

```bash
curl -X PUT http://localhost:8000/api/v1/ocean/pages/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Product Roadmap",
    "is_favorite": true
  }'
```

---

### 5. Delete Page

Delete a page (soft delete by archiving).

**Endpoint:** `DELETE /api/v1/ocean/pages/{page_id}`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page_id` | string | Yes | Unique page identifier |

**Response:** `204 No Content`

**Notes:**

- This is a **soft delete** - sets `is_archived=true`
- Page can be restored by updating `is_archived` back to `false`
- Archived pages are excluded from default listings
- Blocks within the page are NOT deleted

**Errors:**

- `404 Not Found` - Page not found or doesn't belong to organization

**Example cURL:**

```bash
curl -X DELETE http://localhost:8000/api/v1/ocean/pages/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

---

### 6. Move Page

Move a page to a new parent or to root level.

**Endpoint:** `POST /api/v1/ocean/pages/{page_id}/move`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page_id` | string | Yes | Unique page identifier |

**Request Body:**

```json
{
  "new_parent_id": "abc123"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `new_parent_id` | string | Yes | New parent page ID (null to move to root) |

**Response:** `200 OK`

```json
{
  "page_id": "550e8400-e29b-41d4-a716-446655440000",
  "organization_id": "test-org-456",
  "user_id": "test-user-123",
  "title": "Product Roadmap",
  "icon": "🚀",
  "cover_image": null,
  "parent_page_id": "abc123",
  "position": 0,
  "is_archived": false,
  "is_favorite": true,
  "created_at": "2025-12-24T10:00:00Z",
  "updated_at": "2025-12-24T15:45:00Z",
  "metadata": {}
}
```

**Errors:**

- `400 Bad Request` - Invalid parent_id or circular reference
- `404 Not Found` - Page or parent page not found

**Example cURL:**

```bash
# Move to a new parent
curl -X POST http://localhost:8000/api/v1/ocean/pages/550e8400-e29b-41d4-a716-446655440000/move \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"new_parent_id": "abc123"}'

# Move to root level
curl -X POST http://localhost:8000/api/v1/ocean/pages/550e8400-e29b-41d4-a716-446655440000/move \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"new_parent_id": null}'
```

---

## Blocks Endpoints

Blocks are the content units within pages. They support multiple types (text, heading, list, task, link, page_link) and automatically generate embeddings for semantic search.

### Block Types

| Type | Description | Content Structure |
|------|-------------|-------------------|
| `text` | Plain text block | `{"text": "content"}` |
| `heading` | Heading block (H1-H3) | `{"text": "heading", "level": 1}` |
| `list` | Bullet/numbered list | `{"items": ["item1", "item2"], "listType": "bullet"}` |
| `task` | Task/checkbox item | `{"text": "task", "checked": false}` |
| `link` | External link | `{"url": "https://...", "text": "title"}` |
| `page_link` | Internal page reference | `{"linkedPageId": "page_id", "displayText": "title"}` |

### 1. Create Block

Create a new block in a page with automatic embedding generation.

**Endpoint:** `POST /api/v1/ocean/blocks?page_id={page_id}`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page_id` | string | Yes | Page ID to create the block in |

**Request Body:**

```json
{
  "block_type": "text",
  "content": {
    "text": "This is a sample text block for semantic search testing."
  },
  "position": 0,
  "parent_block_id": null,
  "properties": {
    "color": "default",
    "tags": []
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `block_type` | string | Yes | Block type (text\|heading\|list\|task\|link\|page_link) |
| `content` | object | Yes | Type-specific content object |
| `position` | integer | No | Block position (auto-calculated if not provided) |
| `parent_block_id` | string | No | Parent block for nesting |
| `properties` | object | No | Additional properties (color, tags, etc.) |

**Response:** `201 Created`

```json
{
  "block_id": "650e8400-e29b-41d4-a716-446655440000",
  "page_id": "550e8400-e29b-41d4-a716-446655440000",
  "organization_id": "test-org-456",
  "user_id": "test-user-123",
  "block_type": "text",
  "content": {
    "text": "This is a sample text block for semantic search testing."
  },
  "position": 0,
  "parent_block_id": null,
  "properties": {
    "color": "default",
    "tags": []
  },
  "vector_id": "vec_abc123",
  "vector_dimensions": 768,
  "created_at": "2025-12-24T11:00:00Z",
  "updated_at": "2025-12-24T11:00:00Z"
}
```

**Notes:**

- Blocks with searchable content automatically get embeddings (768 dimensions, BAAI/bge-base-en-v1.5)
- Position defaults to end of page if not specified
- Embedding generation happens synchronously during block creation

**Errors:**

- `400 Bad Request` - Invalid request data (e.g., invalid block_type)
- `404 Not Found` - Page not found or doesn't belong to organization
- `500 Internal Server Error` - Failed to create block or generate embedding

**Example cURL:**

```bash
curl -X POST "http://localhost:8000/api/v1/ocean/blocks?page_id=550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "block_type": "text",
    "content": {
      "text": "This is a sample text block."
    }
  }'
```

---

### 2. Batch Create Blocks

Create multiple blocks efficiently with batch embedding generation (optimized for 100+ blocks).

**Endpoint:** `POST /api/v1/ocean/blocks/batch?page_id={page_id}`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page_id` | string | Yes | Page ID to create blocks in |

**Request Body:**

```json
{
  "blocks": [
    {
      "block_type": "text",
      "content": {"text": "First block"}
    },
    {
      "block_type": "task",
      "content": {"text": "Complete documentation", "checked": false}
    },
    {
      "block_type": "heading",
      "content": {"text": "Section Title", "level": 2}
    }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `blocks` | array | Yes | List of block data (max 100 blocks) |

**Response:** `201 Created`

```json
{
  "blocks": [
    {
      "block_id": "650e8400-e29b-41d4-a716-446655440000",
      "page_id": "550e8400-e29b-41d4-a716-446655440000",
      "organization_id": "test-org-456",
      "user_id": "test-user-123",
      "block_type": "text",
      "content": {"text": "First block"},
      "position": 0,
      "parent_block_id": null,
      "properties": {},
      "vector_id": "vec_abc123",
      "vector_dimensions": 768,
      "created_at": "2025-12-24T11:00:00Z",
      "updated_at": "2025-12-24T11:00:00Z"
    }
  ],
  "total": 3
}
```

**Notes:**

- Optimized for large imports (e.g., content migration, page duplication)
- Uses batch embedding generation for efficiency
- Positions are auto-calculated in sequence

**Errors:**

- `400 Bad Request` - Invalid request data or too many blocks (>100)
- `404 Not Found` - Page not found
- `500 Internal Server Error` - Failed to create blocks

**Example cURL:**

```bash
curl -X POST "http://localhost:8000/api/v1/ocean/blocks/batch?page_id=550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "blocks": [
      {"block_type": "text", "content": {"text": "Block 1"}},
      {"block_type": "text", "content": {"text": "Block 2"}}
    ]
  }'
```

---

### 3. Get Block by ID

Retrieve a specific block by its ID.

**Endpoint:** `GET /api/v1/ocean/blocks/{block_id}`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `block_id` | string | Yes | Unique block identifier |

**Response:** `200 OK`

```json
{
  "block_id": "650e8400-e29b-41d4-a716-446655440000",
  "page_id": "550e8400-e29b-41d4-a716-446655440000",
  "organization_id": "test-org-456",
  "user_id": "test-user-123",
  "block_type": "text",
  "content": {
    "text": "This is a sample text block."
  },
  "position": 0,
  "parent_block_id": null,
  "properties": {
    "color": "default",
    "tags": []
  },
  "vector_id": "vec_abc123",
  "vector_dimensions": 768,
  "created_at": "2025-12-24T11:00:00Z",
  "updated_at": "2025-12-24T11:00:00Z"
}
```

**Errors:**

- `404 Not Found` - Block not found or doesn't belong to organization

**Example cURL:**

```bash
curl -X GET http://localhost:8000/api/v1/ocean/blocks/650e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

---

### 4. List Blocks by Page

Get all blocks for a page, ordered by position.

**Endpoint:** `GET /api/v1/ocean/blocks?page_id={page_id}`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page_id` | string | Required | Page ID to get blocks for |
| `block_type` | string | null | Filter by block type (text, heading, list, etc.) |
| `parent_block_id` | string | null | Filter by parent block (for nested blocks) |
| `limit` | integer | 100 | Max results (1-500) |
| `offset` | integer | 0 | Skip results for pagination |

**Response:** `200 OK`

```json
{
  "blocks": [
    {
      "block_id": "650e8400-e29b-41d4-a716-446655440000",
      "page_id": "550e8400-e29b-41d4-a716-446655440000",
      "organization_id": "test-org-456",
      "user_id": "test-user-123",
      "block_type": "text",
      "content": {"text": "First block"},
      "position": 0,
      "parent_block_id": null,
      "properties": {},
      "vector_id": "vec_abc123",
      "vector_dimensions": 768,
      "created_at": "2025-12-24T11:00:00Z",
      "updated_at": "2025-12-24T11:00:00Z"
    }
  ],
  "total": 1,
  "limit": 100,
  "offset": 0
}
```

**Notes:**

- Blocks are always returned in position order (0, 1, 2, ...)
- Use `parent_block_id` filter to get nested blocks

**Example cURL:**

```bash
# Get all blocks for a page
curl -X GET "http://localhost:8000/api/v1/ocean/blocks?page_id=550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer <JWT_TOKEN>"

# Get only text blocks
curl -X GET "http://localhost:8000/api/v1/ocean/blocks?page_id=550e8400-e29b-41d4-a716-446655440000&block_type=text" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

---

### 5. Update Block

Update an existing block with automatic embedding regeneration.

**Endpoint:** `PUT /api/v1/ocean/blocks/{block_id}`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `block_id` | string | Yes | Unique block identifier |

**Request Body:**

```json
{
  "content": {
    "text": "Updated block content"
  },
  "properties": {
    "color": "blue"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `content` | object | No | New content object |
| `properties` | object | No | New properties |
| `position` | integer | No | New position |
| `block_type` | string | No | New block type (recommend using /convert endpoint) |

**Response:** `200 OK`

```json
{
  "block_id": "650e8400-e29b-41d4-a716-446655440000",
  "page_id": "550e8400-e29b-41d4-a716-446655440000",
  "organization_id": "test-org-456",
  "user_id": "test-user-123",
  "block_type": "text",
  "content": {
    "text": "Updated block content"
  },
  "position": 0,
  "parent_block_id": null,
  "properties": {
    "color": "blue",
    "tags": []
  },
  "vector_id": "vec_xyz789",
  "vector_dimensions": 768,
  "created_at": "2025-12-24T11:00:00Z",
  "updated_at": "2025-12-24T12:00:00Z"
}
```

**Notes:**

- If content changes, embedding is automatically regenerated
- Old embedding is deleted before creating new one
- Use `/convert` endpoint for safer block type conversion

**Errors:**

- `400 Bad Request` - No fields provided for update
- `404 Not Found` - Block not found or doesn't belong to organization

**Example cURL:**

```bash
curl -X PUT http://localhost:8000/api/v1/ocean/blocks/650e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "content": {"text": "Updated content"}
  }'
```

---

### 6. Delete Block

Delete a block (hard delete with embedding cleanup).

**Endpoint:** `DELETE /api/v1/ocean/blocks/{block_id}`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `block_id` | string | Yes | Unique block identifier |

**Response:** `204 No Content`

**Notes:**

- This is a **hard delete** - block is permanently removed
- Associated embedding vector is also deleted
- No undo capability - use with caution

**Errors:**

- `404 Not Found` - Block not found or doesn't belong to organization

**Example cURL:**

```bash
curl -X DELETE http://localhost:8000/api/v1/ocean/blocks/650e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

---

### 7. Move/Reorder Block

Reorder a block within its page.

**Endpoint:** `POST /api/v1/ocean/blocks/{block_id}/move`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `block_id` | string | Yes | Unique block identifier |

**Request Body:**

```json
{
  "new_position": 5
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `new_position` | integer | Yes | New position (0-based) |

**Response:** `200 OK`

```json
{
  "block_id": "650e8400-e29b-41d4-a716-446655440000",
  "page_id": "550e8400-e29b-41d4-a716-446655440000",
  "organization_id": "test-org-456",
  "user_id": "test-user-123",
  "block_type": "text",
  "content": {"text": "Block content"},
  "position": 5,
  "parent_block_id": null,
  "properties": {},
  "vector_id": "vec_abc123",
  "vector_dimensions": 768,
  "created_at": "2025-12-24T11:00:00Z",
  "updated_at": "2025-12-24T12:15:00Z"
}
```

**Notes:**

- Automatically adjusts positions of affected blocks
- Moving down: blocks between old and new position shift up
- Moving up: blocks between new and old position shift down
- No-op if new_position equals current position

**Example:**

- Block at position 2 moved to position 5
- Blocks 3, 4, 5 shift to positions 2, 3, 4
- Moved block becomes position 5

**Errors:**

- `404 Not Found` - Block not found or doesn't belong to organization

**Example cURL:**

```bash
curl -X POST http://localhost:8000/api/v1/ocean/blocks/650e8400-e29b-41d4-a716-446655440000/move \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"new_position": 5}'
```

---

### 8. Convert Block Type

Convert a block to a different type, preserving content intelligently.

**Endpoint:** `PUT /api/v1/ocean/blocks/{block_id}/convert`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `block_id` | string | Yes | Unique block identifier |

**Request Body:**

```json
{
  "new_type": "task"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `new_type` | string | Yes | New block type (text\|heading\|list\|task\|link\|page_link) |

**Response:** `200 OK`

```json
{
  "block_id": "650e8400-e29b-41d4-a716-446655440000",
  "page_id": "550e8400-e29b-41d4-a716-446655440000",
  "organization_id": "test-org-456",
  "user_id": "test-user-123",
  "block_type": "task",
  "content": {
    "text": "Block content",
    "checked": false
  },
  "position": 0,
  "parent_block_id": null,
  "properties": {},
  "vector_id": "vec_abc123",
  "vector_dimensions": 768,
  "created_at": "2025-12-24T11:00:00Z",
  "updated_at": "2025-12-24T12:30:00Z"
}
```

**Conversion Logic:**

| From → To | Behavior |
|-----------|----------|
| text/heading/task → any | Preserves text content |
| list → any | Converts to/from newline-separated items |
| link → any | Extracts/adds URL field |
| page_link → any | Extracts/adds linkedPageId field |

**Notes:**

- Embedding is regenerated if searchable text changes
- Content structure is intelligently converted
- Safer than direct update with `block_type` field

**Examples:**

- `text` → `task`: Adds `checked: false` field
- `heading` → `list`: Splits text into single item
- `task` → `text`: Removes `checked` field, keeps text

**Errors:**

- `400 Bad Request` - Invalid new_type
- `404 Not Found` - Block not found or doesn't belong to organization

**Example cURL:**

```bash
curl -X PUT http://localhost:8000/api/v1/ocean/blocks/650e8400-e29b-41d4-a716-446655440000/convert \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"new_type": "task"}'
```

---

### 9. Get Block Embedding Info

Get embedding metadata for a block (useful for debugging search issues).

**Endpoint:** `GET /api/v1/ocean/blocks/{block_id}/embedding`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `block_id` | string | Yes | Unique block identifier |

**Response:** `200 OK`

```json
{
  "block_id": "650e8400-e29b-41d4-a716-446655440000",
  "has_embedding": true,
  "vector_id": "vec_abc123",
  "vector_dimensions": 768,
  "model": "BAAI/bge-base-en-v1.5",
  "searchable_text": "This is a sample text block for semantic search testing..."
}
```

| Field | Type | Description |
|-------|------|-------------|
| `block_id` | string | Block identifier |
| `has_embedding` | boolean | Whether block has an embedding |
| `vector_id` | string | ZeroDB vector ID (if exists) |
| `vector_dimensions` | integer | Embedding dimensions (768) |
| `model` | string | Embedding model used |
| `searchable_text` | string | Preview of text that was embedded (first 100 chars) |

**Use Cases:**

- Debug why block doesn't appear in search results
- Verify embedding was generated
- Check which text was used for embedding

**Errors:**

- `404 Not Found` - Block not found or doesn't belong to organization

**Example cURL:**

```bash
curl -X GET http://localhost:8000/api/v1/ocean/blocks/650e8400-e29b-41d4-a716-446655440000/embedding \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

---

## Links Endpoints

Links create bidirectional relationships between blocks or from blocks to pages. Circular reference detection is automatic for block-to-block links.

### Link Types

- `reference`: Simple reference to another block/page
- `embed`: Embedded content from another block/page
- `mention`: Mention/tag of another block/page

### 1. Create Link

Create a bidirectional link between blocks or from block to page.

**Endpoint:** `POST /api/v1/ocean/links`

**Request Body:**

```json
{
  "source_block_id": "block_abc",
  "target_id": "block_xyz",
  "link_type": "reference",
  "is_page_link": false
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_block_id` | string | Yes | Block ID containing the link |
| `target_id` | string | Yes | Target block ID or page ID |
| `link_type` | string | Yes | Link type (reference\|embed\|mention) |
| `is_page_link` | boolean | No | True if target_id is a page_id (default: false) |

**Response:** `201 Created`

```json
{
  "link_id": "750e8400-e29b-41d4-a716-446655440000",
  "source_block_id": "block_abc",
  "target_id": "block_xyz",
  "link_type": "reference",
  "is_page_link": false,
  "organization_id": "test-org-456",
  "created_at": "2025-12-24T13:00:00Z"
}
```

**Validation:**

- Validates circular references for block-to-block links
- Ensures source and target exist and belong to organization
- Prevents linking to blocks/pages in different organizations

**Errors:**

- `400 Bad Request` - Circular reference detected (block A → block B → block A)
- `404 Not Found` - Source block or target block/page not found

**Example cURL:**

```bash
# Create block-to-block link
curl -X POST http://localhost:8000/api/v1/ocean/links \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "source_block_id": "block_abc",
    "target_id": "block_xyz",
    "link_type": "reference",
    "is_page_link": false
  }'

# Create block-to-page link
curl -X POST http://localhost:8000/api/v1/ocean/links \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "source_block_id": "block_abc",
    "target_id": "page_xyz",
    "link_type": "reference",
    "is_page_link": true
  }'
```

---

### 2. Delete Link

Delete a link by ID (hard delete).

**Endpoint:** `DELETE /api/v1/ocean/links/{link_id}`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `link_id` | string | Yes | Unique link identifier |

**Response:** `204 No Content`

**Notes:**

- This is a hard delete - link is permanently removed
- No undo capability - use with caution
- Does not delete the source or target blocks/pages
- Only removes the relationship between them

**Errors:**

- `404 Not Found` - Link not found or doesn't belong to organization

**Example cURL:**

```bash
curl -X DELETE http://localhost:8000/api/v1/ocean/links/750e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

---

### 3. Get Page Backlinks

Get all blocks linking to a specific page.

**Endpoint:** `GET /api/v1/ocean/pages/{page_id}/backlinks`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page_id` | string | Yes | Unique page identifier |

**Response:** `200 OK`

```json
{
  "backlinks": [
    {
      "link_id": "750e8400-e29b-41d4-a716-446655440000",
      "link_type": "reference",
      "source_block_id": "block_abc",
      "source_page_id": "page_123",
      "source_block_type": "text",
      "source_content_preview": "Check out this related page...",
      "created_at": "2025-12-24T13:00:00Z"
    }
  ],
  "total": 1
}
```

**Use Cases:**

- Show "Referenced by" section on page
- Track page popularity/importance
- Navigate bidirectional links
- Find related content

**Notes:**

- Returns empty list if page has no backlinks
- Returns empty list if page doesn't exist
- Limited to 1000 backlinks (reasonable for most use cases)

**Example cURL:**

```bash
curl -X GET http://localhost:8000/api/v1/ocean/pages/page_xyz/backlinks \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

---

### 4. Get Block Backlinks

Get all blocks linking to a specific block.

**Endpoint:** `GET /api/v1/ocean/blocks/{block_id}/backlinks`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `block_id` | string | Yes | Unique block identifier |

**Response:** `200 OK`

```json
{
  "backlinks": [
    {
      "link_id": "750e8400-e29b-41d4-a716-446655440000",
      "link_type": "reference",
      "source_block_id": "block_abc",
      "source_page_id": "page_123",
      "source_block_type": "text",
      "source_content_preview": "See also this related block...",
      "created_at": "2025-12-24T13:00:00Z"
    }
  ],
  "total": 1
}
```

**Use Cases:**

- Show "Referenced by" section on block
- Track block importance/connections
- Navigate bidirectional links
- Find related content within workspace

**Notes:**

- Returns empty list if block has no backlinks
- Returns empty list if block doesn't exist
- Limited to 1000 backlinks (reasonable for most use cases)
- Source blocks that are deleted won't appear in backlinks

**Example cURL:**

```bash
curl -X GET http://localhost:8000/api/v1/ocean/blocks/block_xyz/backlinks \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

---

## Tags Endpoints

Tags are organization-scoped labels for categorizing and organizing blocks across pages. Each tag has a usage count that tracks how many blocks use it.

### 1. Create Tag

Create a new organization-scoped tag for categorizing blocks.

**Endpoint:** `POST /api/v1/ocean/tags`

**Request Body:**

```json
{
  "name": "important",
  "color": "red",
  "description": "High priority items"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Tag name (unique within organization) |
| `color` | string | No | Tag color for UI display |
| `description` | string | No | Tag description |

**Response:** `201 Created`

```json
{
  "tag_id": "850e8400-e29b-41d4-a716-446655440000",
  "organization_id": "test-org-456",
  "name": "important",
  "color": "red",
  "description": "High priority items",
  "usage_count": 0,
  "created_at": "2025-12-24T14:00:00Z",
  "updated_at": "2025-12-24T14:00:00Z"
}
```

**Notes:**

- Tag names must be unique within an organization
- Tags are used to categorize and organize blocks across pages

**Errors:**

- `400 Bad Request` - Tag name already exists or validation fails
- `500 Internal Server Error` - Failed to create tag

**Example cURL:**

```bash
curl -X POST http://localhost:8000/api/v1/ocean/tags \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "important",
    "color": "red",
    "description": "High priority items"
  }'
```

---

### 2. List Tags

Get all tags for the organization with optional sorting.

**Endpoint:** `GET /api/v1/ocean/tags`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sort_by` | string | usage_count | Sort field: 'name' (alphabetical) or 'usage_count' (most used first) |

**Response:** `200 OK`

```json
{
  "tags": [
    {
      "tag_id": "850e8400-e29b-41d4-a716-446655440000",
      "organization_id": "test-org-456",
      "name": "important",
      "color": "red",
      "description": "High priority items",
      "usage_count": 5,
      "created_at": "2025-12-24T14:00:00Z",
      "updated_at": "2025-12-24T14:00:00Z"
    }
  ],
  "total": 1
}
```

**Notes:**

- Tags are returned sorted by usage count (descending) by default
- Can sort alphabetically by name if specified

**Example cURL:**

```bash
# Get tags sorted by usage count (default)
curl -X GET http://localhost:8000/api/v1/ocean/tags \
  -H "Authorization: Bearer <JWT_TOKEN>"

# Get tags sorted alphabetically
curl -X GET "http://localhost:8000/api/v1/ocean/tags?sort_by=name" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

---

### 3. Update Tag

Update a tag's properties (name, color, description).

**Endpoint:** `PUT /api/v1/ocean/tags/{tag_id}`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tag_id` | string | Yes | Tag ID to update |

**Request Body:**

```json
{
  "name": "urgent",
  "color": "orange"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | No | New tag name (must remain unique) |
| `color` | string | No | New tag color |
| `description` | string | No | New tag description |

**Response:** `200 OK`

```json
{
  "tag_id": "850e8400-e29b-41d4-a716-446655440000",
  "organization_id": "test-org-456",
  "name": "urgent",
  "color": "orange",
  "description": "High priority items",
  "usage_count": 5,
  "created_at": "2025-12-24T14:00:00Z",
  "updated_at": "2025-12-24T15:00:00Z"
}
```

**Notes:**

- Only fields provided in the request will be updated
- Tag name must remain unique within the organization

**Errors:**

- `400 Bad Request` - No fields provided or new name conflicts with existing tag
- `404 Not Found` - Tag not found or not in organization
- `500 Internal Server Error` - Update failed

**Example cURL:**

```bash
curl -X PUT http://localhost:8000/api/v1/ocean/tags/850e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "urgent",
    "color": "orange"
  }'
```

---

### 4. Delete Tag

Delete a tag and remove it from all blocks.

**Endpoint:** `DELETE /api/v1/ocean/tags/{tag_id}`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tag_id` | string | Yes | Tag ID to delete |

**Response:** `200 OK`

```json
{
  "success": true,
  "message": "Tag deleted successfully",
  "tag_id": "850e8400-e29b-41d4-a716-446655440000"
}
```

**Notes:**

This operation:
1. Removes the tag from all blocks that use it
2. Deletes the tag document from the database

**Errors:**

- `404 Not Found` - Tag not found or not in organization
- `500 Internal Server Error` - Deletion failed

**Example cURL:**

```bash
curl -X DELETE http://localhost:8000/api/v1/ocean/tags/850e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

---

### 5. Assign Tag to Block

Assign a tag to a block and increment its usage count.

**Endpoint:** `POST /api/v1/ocean/blocks/{block_id}/tags`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `block_id` | string | Yes | Block ID to tag |

**Request Body:**

```json
{
  "tag_id": "850e8400-e29b-41d4-a716-446655440000"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tag_id` | string | Yes | Tag ID to assign |

**Response:** `200 OK`

```json
{
  "success": true,
  "message": "Tag assigned to block successfully",
  "block_id": "block_abc",
  "tag_id": "850e8400-e29b-41d4-a716-446655440000"
}
```

**Notes:**

This operation:
1. Adds the tag_id to the block's properties.tags array
2. Increments the tag's usage_count

**Errors:**

- `400 Bad Request` - Tag is already assigned to the block
- `404 Not Found` - Block or tag not found
- `500 Internal Server Error` - Assignment failed

**Example cURL:**

```bash
curl -X POST http://localhost:8000/api/v1/ocean/blocks/block_abc/tags \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "tag_id": "850e8400-e29b-41d4-a716-446655440000"
  }'
```

---

### 6. Remove Tag from Block

Remove a tag from a block and decrement its usage count.

**Endpoint:** `DELETE /api/v1/ocean/blocks/{block_id}/tags/{tag_id}`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `block_id` | string | Yes | Block ID to untag |
| `tag_id` | string | Yes | Tag ID to remove |

**Response:** `200 OK`

```json
{
  "success": true,
  "message": "Tag removed from block successfully",
  "block_id": "block_abc",
  "tag_id": "850e8400-e29b-41d4-a716-446655440000"
}
```

**Notes:**

This operation:
1. Removes the tag_id from the block's properties.tags array
2. Decrements the tag's usage_count

**Errors:**

- `400 Bad Request` - Tag is not assigned to the block
- `404 Not Found` - Block or tag not found
- `500 Internal Server Error` - Removal failed

**Example cURL:**

```bash
curl -X DELETE http://localhost:8000/api/v1/ocean/blocks/block_abc/tags/850e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

---

### 7. Get Block Tags

Get all tags assigned to a specific block.

**Endpoint:** `GET /api/v1/ocean/blocks/{block_id}/tags`

**Path Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `block_id` | string | Yes | Block ID to get tags for |

**Response:** `200 OK`

```json
{
  "tags": [
    {
      "tag_id": "850e8400-e29b-41d4-a716-446655440000",
      "organization_id": "test-org-456",
      "name": "important",
      "color": "red",
      "description": "High priority items",
      "usage_count": 5,
      "created_at": "2025-12-24T14:00:00Z",
      "updated_at": "2025-12-24T14:00:00Z"
    }
  ],
  "total": 1
}
```

**Notes:**

- Returns full tag details (name, color, description, usage_count)
- Tags are sorted by usage count (descending)

**Errors:**

- `404 Not Found` - Block not found
- `500 Internal Server Error` - Retrieval failed

**Example cURL:**

```bash
curl -X GET http://localhost:8000/api/v1/ocean/blocks/block_abc/tags \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

---

## Search Endpoint

Ocean provides hybrid semantic search combining vector similarity with metadata filtering. Powered by BAAI/bge-base-en-v1.5 embeddings (768 dimensions) stored in ZeroDB.

### Hybrid Semantic Search

Search blocks using hybrid semantic search combining vector similarity and metadata filtering.

**Endpoint:** `GET /api/v1/ocean/search`

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `q` | string | Required | Search query text |
| `organization_id` | string | Required | Organization ID for multi-tenant isolation |
| `search_type` | string | hybrid | Search mode: semantic\|metadata\|hybrid |
| `block_types` | string | null | Comma-separated block types to filter (e.g., "text,heading,task") |
| `page_id` | string | null | Filter to specific page ID |
| `tags` | string | null | Comma-separated tag IDs to filter |
| `date_from` | string | null | Start date for date range filter (ISO 8601) |
| `date_to` | string | null | End date for date range filter (ISO 8601) |
| `limit` | integer | 20 | Maximum results to return (1-100) |
| `threshold` | float | 0.7 | Minimum similarity threshold (0.0-1.0) |

**Search Modes:**

- `semantic`: Pure vector similarity search using embeddings
- `metadata`: Filter-only search using metadata (no embeddings)
- `hybrid`: Combines vector similarity with metadata filters (default)

**Response:** `200 OK`

```json
{
  "results": [
    {
      "block_id": "650e8400-e29b-41d4-a716-446655440000",
      "content": {
        "text": "This is a sample text block for machine learning testing."
      },
      "block_type": "text",
      "page_id": "550e8400-e29b-41d4-a716-446655440000",
      "score": 0.89,
      "highlights": ["machine", "learning"],
      "created_at": "2025-12-24T11:00:00Z",
      "updated_at": "2025-12-24T11:00:00Z"
    }
  ],
  "total": 1,
  "search_type": "hybrid",
  "query": "machine learning algorithms",
  "threshold": 0.7,
  "limit": 20
}
```

**Scoring:**

- Similarity scores range from 0.0 (no match) to 1.0 (perfect match)
- Threshold parameter filters out results below minimum score
- Results are ranked by relevance (highest score first)

**Highlights:**

- Automatically extracts matching terms from block content
- Only includes terms ≥3 characters that appear in content
- Useful for highlighting search terms in UI

**Errors:**

- `400 Bad Request` - Invalid parameters (e.g., empty query, invalid search_type)
- `500 Internal Server Error` - Search service error (e.g., embedding generation failure, API timeout)

**Example cURL:**

```bash
# Basic semantic search
curl -X GET "http://localhost:8000/api/v1/ocean/search?q=machine%20learning&organization_id=test-org-456" \
  -H "Authorization: Bearer <JWT_TOKEN>"

# Filtered search by block type
curl -X GET "http://localhost:8000/api/v1/ocean/search?q=product%20roadmap&organization_id=test-org-456&block_types=text,heading" \
  -H "Authorization: Bearer <JWT_TOKEN>"

# Search within specific page
curl -X GET "http://localhost:8000/api/v1/ocean/search?q=task&organization_id=test-org-456&page_id=page_123" \
  -H "Authorization: Bearer <JWT_TOKEN>"

# Search with tags filter
curl -X GET "http://localhost:8000/api/v1/ocean/search?q=important&organization_id=test-org-456&tags=tag_123,tag_456" \
  -H "Authorization: Bearer <JWT_TOKEN>"

# Metadata-only search (no vector similarity)
curl -X GET "http://localhost:8000/api/v1/ocean/search?q=test&organization_id=test-org-456&search_type=metadata" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

---

## Response Format

All API responses follow a consistent JSON format.

### Success Response

**Single Resource:**

```json
{
  "page_id": "550e8400-e29b-41d4-a716-446655440000",
  "organization_id": "test-org-456",
  "title": "Product Roadmap",
  ...
}
```

**List Response:**

```json
{
  "pages": [...],
  "total": 10,
  "limit": 50,
  "offset": 0
}
```

**Delete Response:**

```
HTTP 204 No Content
(No response body)
```

### Timestamps

All timestamps are in **ISO 8601 format**:

```
2025-12-24T10:00:00Z
```

### Pagination

Pagination uses `limit` and `offset` query parameters:

- `limit`: Maximum results per request (default varies by endpoint)
- `offset`: Number of results to skip (default: 0)

**Example:**

```
GET /api/v1/ocean/pages?limit=20&offset=40
```

Returns results 41-60.

---

## Error Handling

### Error Response Format

All errors return a consistent JSON structure:

```json
{
  "detail": "Page not found or does not belong to organization"
}
```

### HTTP Status Codes

| Status Code | Meaning | Common Causes |
|-------------|---------|---------------|
| `200 OK` | Successful GET/PUT request | - |
| `201 Created` | Successful POST request | Resource created |
| `204 No Content` | Successful DELETE request | Resource deleted |
| `400 Bad Request` | Invalid request data | Missing fields, validation errors, circular references |
| `401 Unauthorized` | Authentication failed | Missing or invalid JWT token |
| `404 Not Found` | Resource not found | Invalid ID, resource doesn't belong to organization |
| `500 Internal Server Error` | Server error | Database errors, embedding generation failures |

### Common Error Scenarios

**401 Unauthorized:**

```json
{
  "detail": "Not authenticated"
}
```

**Solution:** Include valid JWT token in Authorization header.

---

**400 Bad Request - Missing Required Field:**

```json
{
  "detail": "Field required: title"
}
```

**Solution:** Include all required fields in request body.

---

**400 Bad Request - Circular Reference:**

```json
{
  "detail": "Circular reference detected: block A → block B → block A"
}
```

**Solution:** Remove circular link chain before creating new link.

---

**404 Not Found:**

```json
{
  "detail": "Page 550e8400-e29b-41d4-a716-446655440000 not found or does not belong to organization"
}
```

**Solution:** Verify resource ID and ensure it belongs to your organization.

---

**500 Internal Server Error - Embedding Generation Failed:**

```json
{
  "detail": "Internal server error: Failed to generate embedding"
}
```

**Solution:** Retry request. If persists, contact support.

---

**See:** [ERROR_CODES.md](./ERROR_CODES.md) for complete error reference and troubleshooting guide.

---

## Additional Resources

- **Authentication Guide:** [AUTHENTICATION.md](./AUTHENTICATION.md)
- **Error Codes Reference:** [ERROR_CODES.md](./ERROR_CODES.md)
- **Code Examples:** [examples/](./examples/)
  - [Python Examples](./examples/python_examples.md)
  - [TypeScript/JavaScript Examples](./examples/typescript_examples.md)
  - [cURL Examples](./examples/curl_examples.md)
- **OpenAPI Spec:** Available at `/docs` when server is running

---

## Support

- **GitHub Issues:** [ocean-backend/issues](https://github.com/ainative/ocean-backend/issues)
- **Email:** support@ainative.studio
- **Interactive API Docs:** http://localhost:8000/docs (FastAPI Swagger UI)

---

**Last Updated:** 2025-12-24
**API Version:** 0.1.0
