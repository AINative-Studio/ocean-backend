# Ocean Blocks API Reference

## Base URL
```
http://localhost:8000/api/v1/ocean
```

## Authentication
All endpoints require JWT token in Authorization header:
```
Authorization: Bearer <token>
```

## Endpoints

### 1. Create Single Block
```http
POST /blocks?page_id={page_id}
Content-Type: application/json

{
  "block_type": "text",
  "content": {"text": "This is a paragraph"},
  "position": null,
  "parent_block_id": null,
  "properties": {}
}
```

**Response: 201 Created**
```json
{
  "block_id": "550e8400-e29b-41d4-a716-446655440000",
  "page_id": "abc123",
  "organization_id": "test-org-456",
  "user_id": "test-user-123",
  "block_type": "text",
  "position": 0,
  "content": {"text": "This is a paragraph"},
  "properties": {},
  "vector_id": "vec_xyz789",
  "vector_dimensions": 768,
  "created_at": "2025-12-24T10:00:00Z",
  "updated_at": "2025-12-24T10:00:00Z"
}
```

### 2. Batch Create Blocks
```http
POST /blocks/batch?page_id={page_id}
Content-Type: application/json

{
  "blocks": [
    {
      "block_type": "heading",
      "content": {"text": "Project Overview"}
    },
    {
      "block_type": "text",
      "content": {"text": "This project involves..."}
    }
  ]
}
```

**Response: 201 Created**
```json
{
  "blocks": [...],
  "total": 2
}
```

### 3. Get Block by ID
```http
GET /blocks/{block_id}
```

**Response: 200 OK**
```json
{
  "block_id": "...",
  "block_type": "text",
  "content": {...},
  ...
}
```

### 4. List Blocks by Page
```http
GET /blocks?page_id={page_id}&block_type=text&limit=100&offset=0
```

**Query Parameters:**
- `page_id` (required): Page ID to get blocks for
- `block_type` (optional): Filter by type (text|heading|list|task|link|page_link)
- `parent_block_id` (optional): Filter by parent block
- `limit` (optional): Max results (default: 100, max: 500)
- `offset` (optional): Skip results (default: 0)

**Response: 200 OK**
```json
{
  "blocks": [...],
  "total": 10,
  "limit": 100,
  "offset": 0
}
```

### 5. Update Block
```http
PUT /blocks/{block_id}
Content-Type: application/json

{
  "content": {"text": "Updated text"},
  "properties": {"color": "blue"}
}
```

**Response: 200 OK**
```json
{
  "block_id": "...",
  "content": {"text": "Updated text"},
  ...
}
```

### 6. Delete Block
```http
DELETE /blocks/{block_id}
```

**Response: 204 No Content**

### 7. Move/Reorder Block
```http
POST /blocks/{block_id}/move
Content-Type: application/json

{
  "new_position": 5
}
```

**Response: 200 OK**
```json
{
  "block_id": "...",
  "position": 5,
  ...
}
```

### 8. Convert Block Type
```http
PUT /blocks/{block_id}/convert
Content-Type: application/json

{
  "new_type": "task"
}
```

**Response: 200 OK**
```json
{
  "block_id": "...",
  "block_type": "task",
  "content": {"text": "...", "checked": false},
  ...
}
```

### 9. Get Embedding Info
```http
GET /blocks/{block_id}/embedding
```

**Response: 200 OK**
```json
{
  "block_id": "...",
  "has_embedding": true,
  "vector_id": "vec_xyz789",
  "vector_dimensions": 768,
  "model": "BAAI/bge-base-en-v1.5",
  "searchable_text": "This is a paragraph of text..."
}
```

## Block Types

### text
```json
{
  "block_type": "text",
  "content": {"text": "Regular paragraph"}
}
```

### heading
```json
{
  "block_type": "heading",
  "content": {"text": "Heading Text"}
}
```

### list
```json
{
  "block_type": "list",
  "content": {"items": ["Item 1", "Item 2", "Item 3"]}
}
```

### task
```json
{
  "block_type": "task",
  "content": {"text": "Task description", "checked": false}
}
```

### link
```json
{
  "block_type": "link",
  "content": {"text": "Click here", "url": "https://example.com"}
}
```

### page_link
```json
{
  "block_type": "page_link",
  "content": {"displayText": "See documentation", "linkedPageId": "page-123"}
}
```

## Error Responses

### 400 Bad Request
```json
{
  "detail": "block_type is required",
  "error_code": "VALIDATION_ERROR"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated. Authorization header required."
}
```

### 404 Not Found
```json
{
  "detail": "Block 550e8400-... not found or does not belong to organization"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error: ..."
}
```

## Auto-Generated Documentation

Visit `/docs` for interactive Swagger UI documentation with:
- Full schema definitions
- Try-it-out functionality
- Request/response examples
- Authentication flow

## Features

- **Multi-tenant isolation**: All queries filtered by organization_id
- **Automatic embeddings**: Searchable blocks get 768-dim embeddings
- **Smart conversions**: Block type conversion preserves content intelligently
- **Position management**: Moving blocks auto-adjusts affected blocks
- **Batch operations**: Optimized for bulk imports (up to 100 blocks)
- **Embedding cleanup**: Delete operations remove associated vectors

## Next Steps

- Issue #9: Search endpoints (semantic search using embeddings)
- Issue #10: Link management (bidirectional block/page links)
- Issue #11: Tag management (assign/remove tags from blocks)
