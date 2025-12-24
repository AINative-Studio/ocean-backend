# Ocean API - Python Examples

**Version:** 0.1.0
**Last Updated:** 2025-12-24

Complete Python examples for all Ocean API endpoints using the `requests` library.

---

## Table of Contents

1. [Setup](#setup)
2. [Authentication](#authentication)
3. [Pages Examples](#pages-examples)
4. [Blocks Examples](#blocks-examples)
5. [Links Examples](#links-examples)
6. [Tags Examples](#tags-examples)
7. [Search Examples](#search-examples)
8. [Error Handling](#error-handling)
9. [Complete Client Class](#complete-client-class)

---

## Setup

### Install Dependencies

```bash
pip install requests python-dotenv
```

### Environment Variables

Create a `.env` file:

```bash
OCEAN_API_URL=http://localhost:8000/api/v1/ocean
JWT_TOKEN=your_jwt_token_here
```

### Basic Configuration

```python
import requests
import os
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional

# Load environment variables
load_dotenv()

BASE_URL = os.getenv("OCEAN_API_URL", "http://localhost:8000/api/v1/ocean")
JWT_TOKEN = os.getenv("JWT_TOKEN")

# Create session with auth header
session = requests.Session()
session.headers.update({
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json"
})
```

---

## Authentication

### Manual Token Setup

```python
import jwt
from datetime import datetime, timedelta

def create_test_token(user_id: str, org_id: str, secret_key: str) -> str:
    """
    Create test JWT token for development.
    Note: In production, obtain tokens from auth service.
    """
    payload = {
        "user_id": user_id,
        "organization_id": org_id,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")

# Example usage
TOKEN = create_test_token(
    user_id="test-user-123",
    org_id="test-org-456",
    secret_key="your-secret-key"
)
```

### With Automatic Token Refresh

```python
class OceanClient:
    def __init__(self, base_url: str, auth_url: str):
        self.base_url = base_url
        self.auth_url = auth_url
        self.token = None
        self.refresh_token = None
        self.session = requests.Session()

    def login(self, email: str, password: str):
        """Login and get initial token."""
        response = self.session.post(
            f"{self.auth_url}/login",
            json={"email": email, "password": password}
        )
        response.raise_for_status()
        data = response.json()

        self.token = data["access_token"]
        self.refresh_token = data.get("refresh_token")
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}"
        })

    def refresh(self):
        """Refresh expired token."""
        response = self.session.post(
            f"{self.auth_url}/refresh",
            json={"refresh_token": self.refresh_token}
        )
        response.raise_for_status()
        data = response.json()

        self.token = data["access_token"]
        self.session.headers.update({
            "Authorization": f"Bearer {self.token}"
        })

    def request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request with automatic token refresh."""
        response = self.session.request(
            method,
            f"{self.base_url}{endpoint}",
            **kwargs
        )

        # Auto-refresh on 401
        if response.status_code == 401 and self.refresh_token:
            self.refresh()
            response = self.session.request(
                method,
                f"{self.base_url}{endpoint}",
                **kwargs
            )

        response.raise_for_status()
        return response.json() if response.content else None
```

---

## Pages Examples

### Create Page

```python
def create_page(title: str, icon: str = None, parent_page_id: str = None) -> Dict[str, Any]:
    """Create a new page in the workspace."""
    payload = {
        "title": title,
        "icon": icon,
        "parent_page_id": parent_page_id
    }

    response = session.post(f"{BASE_URL}/pages", json=payload)
    response.raise_for_status()
    return response.json()

# Example usage
page = create_page(
    title="Product Roadmap",
    icon="🚀"
)
print(f"Created page: {page['page_id']}")
```

### List Pages

```python
def list_pages(
    parent_page_id: Optional[str] = None,
    is_archived: Optional[bool] = None,
    is_favorite: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0
) -> Dict[str, Any]:
    """List all pages with optional filtering."""
    params = {
        "limit": limit,
        "offset": offset
    }

    if parent_page_id is not None:
        params["parent_page_id"] = parent_page_id
    if is_archived is not None:
        params["is_archived"] = is_archived
    if is_favorite is not None:
        params["is_favorite"] = is_favorite

    response = session.get(f"{BASE_URL}/pages", params=params)
    response.raise_for_status()
    return response.json()

# Example usage
all_pages = list_pages()
print(f"Total pages: {all_pages['total']}")

# Get favorite pages only
favorites = list_pages(is_favorite=True)
print(f"Favorite pages: {len(favorites['pages'])}")

# Get root-level pages
root_pages = list_pages(parent_page_id="null")
```

### Get Page by ID

```python
def get_page(page_id: str) -> Dict[str, Any]:
    """Get a specific page by ID."""
    response = session.get(f"{BASE_URL}/pages/{page_id}")
    response.raise_for_status()
    return response.json()

# Example usage
page = get_page("550e8400-e29b-41d4-a716-446655440000")
print(f"Page title: {page['title']}")
```

### Update Page

```python
def update_page(
    page_id: str,
    title: Optional[str] = None,
    icon: Optional[str] = None,
    is_favorite: Optional[bool] = None
) -> Dict[str, Any]:
    """Update an existing page."""
    payload = {}

    if title is not None:
        payload["title"] = title
    if icon is not None:
        payload["icon"] = icon
    if is_favorite is not None:
        payload["is_favorite"] = is_favorite

    response = session.put(f"{BASE_URL}/pages/{page_id}", json=payload)
    response.raise_for_status()
    return response.json()

# Example usage
updated_page = update_page(
    page_id="page_123",
    title="Updated Product Roadmap",
    is_favorite=True
)
print(f"Updated: {updated_page['title']}")
```

### Delete Page

```python
def delete_page(page_id: str) -> None:
    """Delete a page (soft delete - archives it)."""
    response = session.delete(f"{BASE_URL}/pages/{page_id}")
    response.raise_for_status()
    print(f"Page {page_id} deleted successfully")

# Example usage
delete_page("page_123")
```

### Move Page

```python
def move_page(page_id: str, new_parent_id: Optional[str]) -> Dict[str, Any]:
    """Move a page to a new parent or to root level."""
    payload = {"new_parent_id": new_parent_id}

    response = session.post(f"{BASE_URL}/pages/{page_id}/move", json=payload)
    response.raise_for_status()
    return response.json()

# Example usage
# Move to a new parent
moved_page = move_page("page_123", "parent_page_456")

# Move to root level
root_page = move_page("page_123", None)
```

---

## Blocks Examples

### Create Block

```python
def create_block(
    page_id: str,
    block_type: str,
    content: Dict[str, Any],
    position: Optional[int] = None,
    parent_block_id: Optional[str] = None,
    properties: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a new block in a page."""
    payload = {
        "block_type": block_type,
        "content": content
    }

    if position is not None:
        payload["position"] = position
    if parent_block_id is not None:
        payload["parent_block_id"] = parent_block_id
    if properties is not None:
        payload["properties"] = properties

    response = session.post(
        f"{BASE_URL}/blocks",
        params={"page_id": page_id},
        json=payload
    )
    response.raise_for_status()
    return response.json()

# Example: Text block
text_block = create_block(
    page_id="page_123",
    block_type="text",
    content={"text": "This is a sample text block for semantic search."}
)
print(f"Created text block: {text_block['block_id']}")

# Example: Heading block
heading_block = create_block(
    page_id="page_123",
    block_type="heading",
    content={"text": "Section Title", "level": 2}
)

# Example: Task block
task_block = create_block(
    page_id="page_123",
    block_type="task",
    content={"text": "Complete documentation", "checked": False}
)

# Example: List block
list_block = create_block(
    page_id="page_123",
    block_type="list",
    content={"items": ["Item 1", "Item 2", "Item 3"], "listType": "bullet"}
)
```

### Batch Create Blocks

```python
def create_blocks_batch(
    page_id: str,
    blocks: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Create multiple blocks efficiently."""
    payload = {"blocks": blocks}

    response = session.post(
        f"{BASE_URL}/blocks/batch",
        params={"page_id": page_id},
        json=payload
    )
    response.raise_for_status()
    return response.json()

# Example usage
blocks_data = [
    {"block_type": "text", "content": {"text": "First block"}},
    {"block_type": "text", "content": {"text": "Second block"}},
    {"block_type": "task", "content": {"text": "Task item", "checked": False}}
]

result = create_blocks_batch(page_id="page_123", blocks=blocks_data)
print(f"Created {result['total']} blocks")
```

### Get Block by ID

```python
def get_block(block_id: str) -> Dict[str, Any]:
    """Get a specific block by ID."""
    response = session.get(f"{BASE_URL}/blocks/{block_id}")
    response.raise_for_status()
    return response.json()

# Example usage
block = get_block("block_789")
print(f"Block type: {block['block_type']}")
print(f"Content: {block['content']}")
```

### List Blocks by Page

```python
def list_blocks(
    page_id: str,
    block_type: Optional[str] = None,
    parent_block_id: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> Dict[str, Any]:
    """List all blocks for a page."""
    params = {
        "page_id": page_id,
        "limit": limit,
        "offset": offset
    }

    if block_type is not None:
        params["block_type"] = block_type
    if parent_block_id is not None:
        params["parent_block_id"] = parent_block_id

    response = session.get(f"{BASE_URL}/blocks", params=params)
    response.raise_for_status()
    return response.json()

# Example usage
all_blocks = list_blocks(page_id="page_123")
print(f"Total blocks: {all_blocks['total']}")

# Get only text blocks
text_blocks = list_blocks(page_id="page_123", block_type="text")
```

### Update Block

```python
def update_block(
    block_id: str,
    content: Optional[Dict[str, Any]] = None,
    properties: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Update an existing block."""
    payload = {}

    if content is not None:
        payload["content"] = content
    if properties is not None:
        payload["properties"] = properties

    response = session.put(f"{BASE_URL}/blocks/{block_id}", json=payload)
    response.raise_for_status()
    return response.json()

# Example usage
updated_block = update_block(
    block_id="block_789",
    content={"text": "Updated block content"}
)
print(f"Block updated: {updated_block['updated_at']}")
```

### Delete Block

```python
def delete_block(block_id: str) -> None:
    """Delete a block (hard delete with embedding cleanup)."""
    response = session.delete(f"{BASE_URL}/blocks/{block_id}")
    response.raise_for_status()
    print(f"Block {block_id} deleted successfully")

# Example usage
delete_block("block_789")
```

### Move/Reorder Block

```python
def move_block(block_id: str, new_position: int) -> Dict[str, Any]:
    """Reorder a block within its page."""
    payload = {"new_position": new_position}

    response = session.post(f"{BASE_URL}/blocks/{block_id}/move", json=payload)
    response.raise_for_status()
    return response.json()

# Example usage
moved_block = move_block("block_789", new_position=5)
print(f"Block moved to position: {moved_block['position']}")
```

### Convert Block Type

```python
def convert_block_type(block_id: str, new_type: str) -> Dict[str, Any]:
    """Convert a block to a different type."""
    payload = {"new_type": new_type}

    response = session.put(f"{BASE_URL}/blocks/{block_id}/convert", json=payload)
    response.raise_for_status()
    return response.json()

# Example usage
# Convert text block to task
converted = convert_block_type("block_789", "task")
print(f"Converted to: {converted['block_type']}")
print(f"New content: {converted['content']}")
```

### Get Block Embedding Info

```python
def get_block_embedding(block_id: str) -> Dict[str, Any]:
    """Get embedding metadata for a block."""
    response = session.get(f"{BASE_URL}/blocks/{block_id}/embedding")
    response.raise_for_status()
    return response.json()

# Example usage
embedding_info = get_block_embedding("block_789")
print(f"Has embedding: {embedding_info['has_embedding']}")
print(f"Vector ID: {embedding_info['vector_id']}")
print(f"Searchable text: {embedding_info['searchable_text']}")
```

---

## Links Examples

### Create Link

```python
def create_link(
    source_block_id: str,
    target_id: str,
    link_type: str,
    is_page_link: bool = False
) -> Dict[str, Any]:
    """Create a bidirectional link between blocks or block to page."""
    payload = {
        "source_block_id": source_block_id,
        "target_id": target_id,
        "link_type": link_type,
        "is_page_link": is_page_link
    }

    response = session.post(f"{BASE_URL}/links", json=payload)
    response.raise_for_status()
    return response.json()

# Example: Block-to-block link
block_link = create_link(
    source_block_id="block_abc",
    target_id="block_xyz",
    link_type="reference",
    is_page_link=False
)
print(f"Created link: {block_link['link_id']}")

# Example: Block-to-page link
page_link = create_link(
    source_block_id="block_abc",
    target_id="page_123",
    link_type="reference",
    is_page_link=True
)
```

### Delete Link

```python
def delete_link(link_id: str) -> None:
    """Delete a link by ID."""
    response = session.delete(f"{BASE_URL}/links/{link_id}")
    response.raise_for_status()
    print(f"Link {link_id} deleted successfully")

# Example usage
delete_link("link_456")
```

### Get Page Backlinks

```python
def get_page_backlinks(page_id: str) -> Dict[str, Any]:
    """Get all blocks linking to a specific page."""
    response = session.get(f"{BASE_URL}/pages/{page_id}/backlinks")
    response.raise_for_status()
    return response.json()

# Example usage
backlinks = get_page_backlinks("page_123")
print(f"Total backlinks: {backlinks['total']}")

for backlink in backlinks['backlinks']:
    print(f"- {backlink['source_block_type']}: {backlink['source_content_preview']}")
```

### Get Block Backlinks

```python
def get_block_backlinks(block_id: str) -> Dict[str, Any]:
    """Get all blocks linking to a specific block."""
    response = session.get(f"{BASE_URL}/blocks/{block_id}/backlinks")
    response.raise_for_status()
    return response.json()

# Example usage
backlinks = get_block_backlinks("block_xyz")
print(f"This block is referenced by {backlinks['total']} other blocks")
```

---

## Tags Examples

### Create Tag

```python
def create_tag(
    name: str,
    color: Optional[str] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new tag in the organization."""
    payload = {"name": name}

    if color is not None:
        payload["color"] = color
    if description is not None:
        payload["description"] = description

    response = session.post(f"{BASE_URL}/tags", json=payload)
    response.raise_for_status()
    return response.json()

# Example usage
tag = create_tag(
    name="important",
    color="red",
    description="High priority items"
)
print(f"Created tag: {tag['tag_id']}")
```

### List Tags

```python
def list_tags(sort_by: str = "usage_count") -> Dict[str, Any]:
    """List all tags for the organization."""
    params = {"sort_by": sort_by}

    response = session.get(f"{BASE_URL}/tags", params=params)
    response.raise_for_status()
    return response.json()

# Example usage
tags = list_tags(sort_by="usage_count")
print(f"Total tags: {tags['total']}")

for tag in tags['tags']:
    print(f"- {tag['name']} (used {tag['usage_count']} times)")
```

### Update Tag

```python
def update_tag(
    tag_id: str,
    name: Optional[str] = None,
    color: Optional[str] = None,
    description: Optional[str] = None
) -> Dict[str, Any]:
    """Update a tag's properties."""
    payload = {}

    if name is not None:
        payload["name"] = name
    if color is not None:
        payload["color"] = color
    if description is not None:
        payload["description"] = description

    response = session.put(f"{BASE_URL}/tags/{tag_id}", json=payload)
    response.raise_for_status()
    return response.json()

# Example usage
updated_tag = update_tag(tag_id="tag_123", name="urgent", color="orange")
```

### Delete Tag

```python
def delete_tag(tag_id: str) -> Dict[str, Any]:
    """Delete a tag and remove it from all blocks."""
    response = session.delete(f"{BASE_URL}/tags/{tag_id}")
    response.raise_for_status()
    return response.json()

# Example usage
result = delete_tag("tag_123")
print(result["message"])
```

### Assign Tag to Block

```python
def assign_tag_to_block(block_id: str, tag_id: str) -> Dict[str, Any]:
    """Assign a tag to a block."""
    payload = {"tag_id": tag_id}

    response = session.post(f"{BASE_URL}/blocks/{block_id}/tags", json=payload)
    response.raise_for_status()
    return response.json()

# Example usage
result = assign_tag_to_block("block_789", "tag_123")
print(result["message"])
```

### Remove Tag from Block

```python
def remove_tag_from_block(block_id: str, tag_id: str) -> Dict[str, Any]:
    """Remove a tag from a block."""
    response = session.delete(f"{BASE_URL}/blocks/{block_id}/tags/{tag_id}")
    response.raise_for_status()
    return response.json()

# Example usage
result = remove_tag_from_block("block_789", "tag_123")
print(result["message"])
```

### Get Block Tags

```python
def get_block_tags(block_id: str) -> Dict[str, Any]:
    """Get all tags assigned to a block."""
    response = session.get(f"{BASE_URL}/blocks/{block_id}/tags")
    response.raise_for_status()
    return response.json()

# Example usage
tags = get_block_tags("block_789")
print(f"Block has {tags['total']} tags:")

for tag in tags['tags']:
    print(f"- {tag['name']} ({tag['color']})")
```

---

## Search Examples

### Basic Semantic Search

```python
def search_blocks(
    query: str,
    organization_id: str,
    search_type: str = "hybrid",
    limit: int = 20,
    threshold: float = 0.7
) -> Dict[str, Any]:
    """Search blocks using hybrid semantic search."""
    params = {
        "q": query,
        "organization_id": organization_id,
        "search_type": search_type,
        "limit": limit,
        "threshold": threshold
    }

    response = session.get(f"{BASE_URL}/search", params=params)
    response.raise_for_status()
    return response.json()

# Example usage
results = search_blocks(
    query="machine learning algorithms",
    organization_id="test-org-456"
)

print(f"Found {results['total']} results:")

for result in results['results']:
    print(f"\nBlock ID: {result['block_id']}")
    print(f"Score: {result['score']:.2f}")
    print(f"Content: {result['content']}")
    print(f"Highlights: {', '.join(result['highlights'])}")
```

### Filtered Search

```python
def search_with_filters(
    query: str,
    organization_id: str,
    block_types: Optional[List[str]] = None,
    page_id: Optional[str] = None,
    tags: Optional[List[str]] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None
) -> Dict[str, Any]:
    """Search with metadata filters."""
    params = {
        "q": query,
        "organization_id": organization_id,
        "search_type": "hybrid"
    }

    if block_types:
        params["block_types"] = ",".join(block_types)
    if page_id:
        params["page_id"] = page_id
    if tags:
        params["tags"] = ",".join(tags)
    if date_from:
        params["date_from"] = date_from
    if date_to:
        params["date_to"] = date_to

    response = session.get(f"{BASE_URL}/search", params=params)
    response.raise_for_status()
    return response.json()

# Example: Search only text and heading blocks
results = search_with_filters(
    query="product roadmap",
    organization_id="test-org-456",
    block_types=["text", "heading"]
)

# Example: Search within specific page
results = search_with_filters(
    query="task",
    organization_id="test-org-456",
    page_id="page_123"
)

# Example: Search with tags filter
results = search_with_filters(
    query="important",
    organization_id="test-org-456",
    tags=["tag_123", "tag_456"]
)
```

---

## Error Handling

### Comprehensive Error Handling

```python
from typing import Optional
import sys

def safe_api_call(
    func,
    *args,
    retry_count: int = 3,
    **kwargs
) -> Optional[Dict[str, Any]]:
    """Make API call with error handling and retry logic."""
    for attempt in range(retry_count):
        try:
            return func(*args, **kwargs)

        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code
            error_detail = e.response.json().get("detail", str(e))

            if status_code == 400:
                print(f"❌ Bad Request: {error_detail}", file=sys.stderr)
                return None  # Don't retry
            elif status_code == 401:
                print(f"❌ Unauthorized: {error_detail}", file=sys.stderr)
                return None  # Don't retry
            elif status_code == 404:
                print(f"❌ Not Found: {error_detail}", file=sys.stderr)
                return None  # Don't retry
            elif status_code >= 500:
                print(f"⚠️ Server Error (attempt {attempt + 1}/{retry_count}): {error_detail}", file=sys.stderr)
                if attempt < retry_count - 1:
                    import time
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    return None
            else:
                print(f"❌ HTTP {status_code}: {error_detail}", file=sys.stderr)
                return None

        except requests.exceptions.RequestException as e:
            print(f"⚠️ Request failed (attempt {attempt + 1}/{retry_count}): {str(e)}", file=sys.stderr)
            if attempt < retry_count - 1:
                import time
                time.sleep(2 ** attempt)
            else:
                return None

    return None

# Example usage
page = safe_api_call(create_page, title="Test Page", icon="📝")

if page:
    print(f"✅ Page created: {page['page_id']}")
else:
    print("❌ Failed to create page")
```

---

## Complete Client Class

### Full-Featured Ocean Client

```python
from typing import Dict, Any, List, Optional
import requests
from datetime import datetime, timedelta
import jwt

class OceanAPIClient:
    """Complete Ocean API client with all endpoints."""

    def __init__(self, base_url: str, jwt_token: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json"
        })

    # Pages
    def create_page(self, title: str, **kwargs) -> Dict[str, Any]:
        """Create a new page."""
        return self.session.post(
            f"{self.base_url}/pages",
            json={"title": title, **kwargs}
        ).json()

    def list_pages(self, **filters) -> Dict[str, Any]:
        """List pages with optional filters."""
        return self.session.get(f"{self.base_url}/pages", params=filters).json()

    def get_page(self, page_id: str) -> Dict[str, Any]:
        """Get page by ID."""
        return self.session.get(f"{self.base_url}/pages/{page_id}").json()

    def update_page(self, page_id: str, **updates) -> Dict[str, Any]:
        """Update page."""
        return self.session.put(f"{self.base_url}/pages/{page_id}", json=updates).json()

    def delete_page(self, page_id: str) -> None:
        """Delete page."""
        self.session.delete(f"{self.base_url}/pages/{page_id}").raise_for_status()

    def move_page(self, page_id: str, new_parent_id: Optional[str]) -> Dict[str, Any]:
        """Move page."""
        return self.session.post(
            f"{self.base_url}/pages/{page_id}/move",
            json={"new_parent_id": new_parent_id}
        ).json()

    # Blocks
    def create_block(self, page_id: str, block_type: str, content: Dict, **kwargs) -> Dict[str, Any]:
        """Create block."""
        return self.session.post(
            f"{self.base_url}/blocks",
            params={"page_id": page_id},
            json={"block_type": block_type, "content": content, **kwargs}
        ).json()

    def create_blocks_batch(self, page_id: str, blocks: List[Dict]) -> Dict[str, Any]:
        """Batch create blocks."""
        return self.session.post(
            f"{self.base_url}/blocks/batch",
            params={"page_id": page_id},
            json={"blocks": blocks}
        ).json()

    def list_blocks(self, page_id: str, **filters) -> Dict[str, Any]:
        """List blocks for page."""
        return self.session.get(
            f"{self.base_url}/blocks",
            params={"page_id": page_id, **filters}
        ).json()

    def get_block(self, block_id: str) -> Dict[str, Any]:
        """Get block by ID."""
        return self.session.get(f"{self.base_url}/blocks/{block_id}").json()

    def update_block(self, block_id: str, **updates) -> Dict[str, Any]:
        """Update block."""
        return self.session.put(f"{self.base_url}/blocks/{block_id}", json=updates).json()

    def delete_block(self, block_id: str) -> None:
        """Delete block."""
        self.session.delete(f"{self.base_url}/blocks/{block_id}").raise_for_status()

    def move_block(self, block_id: str, new_position: int) -> Dict[str, Any]:
        """Move/reorder block."""
        return self.session.post(
            f"{self.base_url}/blocks/{block_id}/move",
            json={"new_position": new_position}
        ).json()

    def convert_block_type(self, block_id: str, new_type: str) -> Dict[str, Any]:
        """Convert block type."""
        return self.session.put(
            f"{self.base_url}/blocks/{block_id}/convert",
            json={"new_type": new_type}
        ).json()

    def get_block_embedding(self, block_id: str) -> Dict[str, Any]:
        """Get block embedding info."""
        return self.session.get(f"{self.base_url}/blocks/{block_id}/embedding").json()

    # Links
    def create_link(self, source_block_id: str, target_id: str, link_type: str, is_page_link: bool = False) -> Dict[str, Any]:
        """Create link."""
        return self.session.post(
            f"{self.base_url}/links",
            json={
                "source_block_id": source_block_id,
                "target_id": target_id,
                "link_type": link_type,
                "is_page_link": is_page_link
            }
        ).json()

    def delete_link(self, link_id: str) -> None:
        """Delete link."""
        self.session.delete(f"{self.base_URL}/links/{link_id}").raise_for_status()

    def get_page_backlinks(self, page_id: str) -> Dict[str, Any]:
        """Get page backlinks."""
        return self.session.get(f"{self.base_url}/pages/{page_id}/backlinks").json()

    def get_block_backlinks(self, block_id: str) -> Dict[str, Any]:
        """Get block backlinks."""
        return self.session.get(f"{self.base_url}/blocks/{block_id}/backlinks").json()

    # Tags
    def create_tag(self, name: str, **kwargs) -> Dict[str, Any]:
        """Create tag."""
        return self.session.post(f"{self.base_url}/tags", json={"name": name, **kwargs}).json()

    def list_tags(self, sort_by: str = "usage_count") -> Dict[str, Any]:
        """List tags."""
        return self.session.get(f"{self.base_url}/tags", params={"sort_by": sort_by}).json()

    def update_tag(self, tag_id: str, **updates) -> Dict[str, Any]:
        """Update tag."""
        return self.session.put(f"{self.base_url}/tags/{tag_id}", json=updates).json()

    def delete_tag(self, tag_id: str) -> Dict[str, Any]:
        """Delete tag."""
        return self.session.delete(f"{self.base_url}/tags/{tag_id}").json()

    def assign_tag_to_block(self, block_id: str, tag_id: str) -> Dict[str, Any]:
        """Assign tag to block."""
        return self.session.post(
            f"{self.base_url}/blocks/{block_id}/tags",
            json={"tag_id": tag_id}
        ).json()

    def remove_tag_from_block(self, block_id: str, tag_id: str) -> Dict[str, Any]:
        """Remove tag from block."""
        return self.session.delete(f"{self.base_url}/blocks/{block_id}/tags/{tag_id}").json()

    def get_block_tags(self, block_id: str) -> Dict[str, Any]:
        """Get block tags."""
        return self.session.get(f"{self.base_url}/blocks/{block_id}/tags").json()

    # Search
    def search(self, query: str, organization_id: str, **filters) -> Dict[str, Any]:
        """Search blocks."""
        params = {"q": query, "organization_id": organization_id, **filters}
        return self.session.get(f"{self.base_url}/search", params=params).json()

# Example usage
client = OceanAPIClient(
    base_url="http://localhost:8000/api/v1/ocean",
    jwt_token="your_token_here"
)

# Create page
page = client.create_page(title="My Page", icon="📄")

# Create blocks
client.create_block(
    page_id=page["page_id"],
    block_type="text",
    content={"text": "Hello, Ocean!"}
)

# Search
results = client.search(
    query="hello",
    organization_id="test-org-456"
)
```

---

## Additional Resources

- **API Reference:** [API_REFERENCE.md](../API_REFERENCE.md)
- **Authentication Guide:** [AUTHENTICATION.md](../AUTHENTICATION.md)
- **Error Codes:** [ERROR_CODES.md](../ERROR_CODES.md)

---

**Last Updated:** 2025-12-24
**API Version:** 0.1.0
