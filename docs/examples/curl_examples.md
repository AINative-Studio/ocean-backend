# Ocean API - cURL Examples

**Version:** 0.1.0
**Last Updated:** 2025-12-24

Complete cURL command examples for all Ocean API endpoints. Perfect for testing and debugging.

---

## Setup

```bash
# Set environment variables (recommended)
export OCEAN_API_URL="http://localhost:8000/api/v1/ocean"
export JWT_TOKEN="your_jwt_token_here"

# Or replace in examples:
# - <JWT_TOKEN> with your actual token
# - http://localhost:8000 with your API URL
```

---

## Pages Endpoints

### Create Page

```bash
curl -X POST "${OCEAN_API_URL}/pages" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Product Roadmap",
    "icon": "🚀"
  }'
```

### List Pages

```bash
# All pages
curl -X GET "${OCEAN_API_URL}/pages" \
  -H "Authorization: Bearer ${JWT_TOKEN}"

# Favorite pages only
curl -X GET "${OCEAN_API_URL}/pages?is_favorite=true" \
  -H "Authorization: Bearer ${JWT_TOKEN}"

# Root-level pages (no parent)
curl -X GET "${OCEAN_API_URL}/pages?parent_page_id=null" \
  -H "Authorization: Bearer ${JWT_TOKEN}"

# With pagination
curl -X GET "${OCEAN_API_URL}/pages?limit=10&offset=0" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

### Get Page by ID

```bash
curl -X GET "${OCEAN_API_URL}/pages/550e8400-e29b-41d4-a716-446655440000" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

### Update Page

```bash
curl -X PUT "${OCEAN_API_URL}/pages/page_123" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Updated Product Roadmap",
    "is_favorite": true
  }'
```

### Delete Page

```bash
curl -X DELETE "${OCEAN_API_URL}/pages/page_123" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

### Move Page

```bash
# Move to a new parent
curl -X POST "${OCEAN_API_URL}/pages/page_123/move" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"new_parent_id": "parent_456"}'

# Move to root level
curl -X POST "${OCEAN_API_URL}/pages/page_123/move" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"new_parent_id": null}'
```

---

## Blocks Endpoints

### Create Block

```bash
# Text block
curl -X POST "${OCEAN_API_URL}/blocks?page_id=page_123" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "block_type": "text",
    "content": {
      "text": "This is a sample text block for semantic search testing."
    }
  }'

# Heading block
curl -X POST "${OCEAN_API_URL}/blocks?page_id=page_123" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "block_type": "heading",
    "content": {
      "text": "Section Title",
      "level": 2
    }
  }'

# Task block
curl -X POST "${OCEAN_API_URL}/blocks?page_id=page_123" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "block_type": "task",
    "content": {
      "text": "Complete documentation",
      "checked": false
    }
  }'

# List block
curl -X POST "${OCEAN_API_URL}/blocks?page_id=page_123" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "block_type": "list",
    "content": {
      "items": ["Item 1", "Item 2", "Item 3"],
      "listType": "bullet"
    }
  }'
```

### Batch Create Blocks

```bash
curl -X POST "${OCEAN_API_URL}/blocks/batch?page_id=page_123" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "blocks": [
      {
        "block_type": "text",
        "content": {"text": "First block"}
      },
      {
        "block_type": "text",
        "content": {"text": "Second block"}
      },
      {
        "block_type": "task",
        "content": {"text": "Task item", "checked": false}
      }
    ]
  }'
```

### Get Block by ID

```bash
curl -X GET "${OCEAN_API_URL}/blocks/block_789" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

### List Blocks by Page

```bash
# All blocks for a page
curl -X GET "${OCEAN_API_URL}/blocks?page_id=page_123" \
  -H "Authorization: Bearer ${JWT_TOKEN}"

# Only text blocks
curl -X GET "${OCEAN_API_URL}/blocks?page_id=page_123&block_type=text" \
  -H "Authorization: Bearer ${JWT_TOKEN}"

# With pagination
curl -X GET "${OCEAN_API_URL}/blocks?page_id=page_123&limit=50&offset=0" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

### Update Block

```bash
curl -X PUT "${OCEAN_API_URL}/blocks/block_789" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "content": {
      "text": "Updated block content"
    }
  }'
```

### Delete Block

```bash
curl -X DELETE "${OCEAN_API_URL}/blocks/block_789" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

### Move/Reorder Block

```bash
curl -X POST "${OCEAN_API_URL}/blocks/block_789/move" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"new_position": 5}'
```

### Convert Block Type

```bash
# Convert text block to task
curl -X PUT "${OCEAN_API_URL}/blocks/block_789/convert" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"new_type": "task"}'
```

### Get Block Embedding Info

```bash
curl -X GET "${OCEAN_API_URL}/blocks/block_789/embedding" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

---

## Links Endpoints

### Create Link

```bash
# Block-to-block link
curl -X POST "${OCEAN_API_URL}/links" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "source_block_id": "block_abc",
    "target_id": "block_xyz",
    "link_type": "reference",
    "is_page_link": false
  }'

# Block-to-page link
curl -X POST "${OCEAN_API_URL}/links" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "source_block_id": "block_abc",
    "target_id": "page_123",
    "link_type": "reference",
    "is_page_link": true
  }'
```

### Delete Link

```bash
curl -X DELETE "${OCEAN_API_URL}/links/link_456" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

### Get Page Backlinks

```bash
curl -X GET "${OCEAN_API_URL}/pages/page_123/backlinks" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

### Get Block Backlinks

```bash
curl -X GET "${OCEAN_API_URL}/blocks/block_xyz/backlinks" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

---

## Tags Endpoints

### Create Tag

```bash
curl -X POST "${OCEAN_API_URL}/tags" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "important",
    "color": "red",
    "description": "High priority items"
  }'
```

### List Tags

```bash
# Sort by usage count (default)
curl -X GET "${OCEAN_API_URL}/tags" \
  -H "Authorization: Bearer ${JWT_TOKEN}"

# Sort alphabetically
curl -X GET "${OCEAN_API_URL}/tags?sort_by=name" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

### Update Tag

```bash
curl -X PUT "${OCEAN_API_URL}/tags/tag_123" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "urgent",
    "color": "orange"
  }'
```

### Delete Tag

```bash
curl -X DELETE "${OCEAN_API_URL}/tags/tag_123" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

### Assign Tag to Block

```bash
curl -X POST "${OCEAN_API_URL}/blocks/block_789/tags" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"tag_id": "tag_123"}'
```

### Remove Tag from Block

```bash
curl -X DELETE "${OCEAN_API_URL}/blocks/block_789/tags/tag_123" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

### Get Block Tags

```bash
curl -X GET "${OCEAN_API_URL}/blocks/block_789/tags" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

---

## Search Endpoint

### Basic Semantic Search

```bash
curl -X GET "${OCEAN_API_URL}/search?q=machine%20learning&organization_id=test-org-456" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

### Search with Filters

```bash
# Filter by block types
curl -X GET "${OCEAN_API_URL}/search?q=product%20roadmap&organization_id=test-org-456&block_types=text,heading" \
  -H "Authorization: Bearer ${JWT_TOKEN}"

# Search within specific page
curl -X GET "${OCEAN_API_URL}/search?q=task&organization_id=test-org-456&page_id=page_123" \
  -H "Authorization: Bearer ${JWT_TOKEN}"

# Search with tags filter
curl -X GET "${OCEAN_API_URL}/search?q=important&organization_id=test-org-456&tags=tag_123,tag_456" \
  -H "Authorization: Bearer ${JWT_TOKEN}"

# Metadata-only search (no vector similarity)
curl -X GET "${OCEAN_API_URL}/search?q=test&organization_id=test-org-456&search_type=metadata" \
  -H "Authorization: Bearer ${JWT_TOKEN}"

# Adjust similarity threshold
curl -X GET "${OCEAN_API_URL}/search?q=query&organization_id=test-org-456&threshold=0.8&limit=10" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
```

---

## Testing Script

Save this as `test_ocean_api.sh`:

```bash
#!/bin/bash

# Ocean API Testing Script
# Usage: ./test_ocean_api.sh

set -e

# Configuration
OCEAN_API_URL="${OCEAN_API_URL:-http://localhost:8000/api/v1/ocean}"
JWT_TOKEN="${JWT_TOKEN:-your_token_here}"

echo "Testing Ocean API at: ${OCEAN_API_URL}"
echo "========================================="

# Test 1: Create Page
echo -e "\n1. Creating page..."
PAGE_RESPONSE=$(curl -s -X POST "${OCEAN_API_URL}/pages" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Page", "icon": "📄"}')

PAGE_ID=$(echo "$PAGE_RESPONSE" | jq -r '.page_id')
echo "Created page: $PAGE_ID"

# Test 2: List Pages
echo -e "\n2. Listing pages..."
curl -s -X GET "${OCEAN_API_URL}/pages" \
  -H "Authorization: Bearer ${JWT_TOKEN}" | jq '.total'

# Test 3: Create Block
echo -e "\n3. Creating block..."
BLOCK_RESPONSE=$(curl -s -X POST "${OCEAN_API_URL}/blocks?page_id=${PAGE_ID}" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"block_type": "text", "content": {"text": "Test block for search"}}')

BLOCK_ID=$(echo "$BLOCK_RESPONSE" | jq -r '.block_id')
echo "Created block: $BLOCK_ID"

# Test 4: Search
echo -e "\n4. Searching blocks..."
curl -s -X GET "${OCEAN_API_URL}/search?q=test&organization_id=test-org-456" \
  -H "Authorization: Bearer ${JWT_TOKEN}" | jq '.total'

# Test 5: Create Tag
echo -e "\n5. Creating tag..."
TAG_RESPONSE=$(curl -s -X POST "${OCEAN_API_URL}/tags" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name": "test-tag", "color": "blue"}')

TAG_ID=$(echo "$TAG_RESPONSE" | jq -r '.tag_id')
echo "Created tag: $TAG_ID"

# Test 6: Assign Tag to Block
echo -e "\n6. Assigning tag to block..."
curl -s -X POST "${OCEAN_API_URL}/blocks/${BLOCK_ID}/tags" \
  -H "Authorization: Bearer ${JWT_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"tag_id\": \"${TAG_ID}\"}" | jq '.message'

# Cleanup
echo -e "\n7. Cleaning up..."
curl -s -X DELETE "${OCEAN_API_URL}/blocks/${BLOCK_ID}" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
curl -s -X DELETE "${OCEAN_API_URL}/pages/${PAGE_ID}" \
  -H "Authorization: Bearer ${JWT_TOKEN}"
curl -s -X DELETE "${OCEAN_API_URL}/tags/${TAG_ID}" \
  -H "Authorization: Bearer ${JWT_TOKEN}"

echo -e "\n========================================="
echo "All tests completed successfully!"
```

Make executable:

```bash
chmod +x test_ocean_api.sh
./test_ocean_api.sh
```

---

## Pretty Print JSON Responses

Add `| jq` to format JSON output:

```bash
curl -X GET "${OCEAN_API_URL}/pages" \
  -H "Authorization: Bearer ${JWT_TOKEN}" | jq '.'

# Show only page titles
curl -X GET "${OCEAN_API_URL}/pages" \
  -H "Authorization: Bearer ${JWT_TOKEN}" | jq '.pages[].title'

# Count total pages
curl -X GET "${OCEAN_API_URL}/pages" \
  -H "Authorization: Bearer ${JWT_TOKEN}" | jq '.total'
```

---

## Debugging with Verbose Output

Add `-v` flag to see full request/response headers:

```bash
curl -v -X GET "${OCEAN_API_URL}/pages" \
  -H "Authorization: Bearer ${JWT_TOKEN}"

# Check if Authorization header is being sent
# Look for: > Authorization: Bearer ...
```

---

## Additional Resources

- **API Reference:** [API_REFERENCE.md](../API_REFERENCE.md)
- **Python Examples:** [python_examples.md](./python_examples.md)
- **TypeScript Examples:** [typescript_examples.md](./typescript_examples.md)

---

**Last Updated:** 2025-12-24
**API Version:** 0.1.0
