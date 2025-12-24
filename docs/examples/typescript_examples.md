# Ocean API - TypeScript/JavaScript Examples

**Version:** 0.1.0
**Last Updated:** 2025-12-24

Complete TypeScript and JavaScript examples for all Ocean API endpoints using `fetch` and `axios`.

---

## Table of Contents

1. [Setup](#setup)
2. [Fetch API Examples](#fetch-api-examples)
3. [Axios Examples](#axios-examples)
4. [Complete TypeScript Client](#complete-typescript-client)
5. [React Hooks](#react-hooks)

---

## Setup

### TypeScript with Fetch

```typescript
// types.ts
export interface Page {
  page_id: string;
  organization_id: string;
  user_id: string;
  title: string;
  icon?: string;
  cover_image?: string;
  parent_page_id?: string;
  position: number;
  is_archived: boolean;
  is_favorite: boolean;
  created_at: string;
  updated_at: string;
  metadata?: Record<string, any>;
}

export interface Block {
  block_id: string;
  page_id: string;
  organization_id: string;
  user_id: string;
  block_type: "text" | "heading" | "list" | "task" | "link" | "page_link";
  content: Record<string, any>;
  position: number;
  parent_block_id?: string;
  properties?: Record<string, any>;
  vector_id?: string;
  vector_dimensions?: number;
  created_at: string;
  updated_at: string;
}

export interface SearchResult {
  block_id: string;
  content: Record<string, any>;
  block_type: string;
  page_id: string;
  score: number;
  highlights: string[];
  created_at: string;
  updated_at: string;
}
```

```typescript
// config.ts
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1/ocean";
export const JWT_TOKEN = process.env.NEXT_PUBLIC_JWT_TOKEN || "";

// Helper function
export async function apiCall<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      "Authorization": `Bearer ${JWT_TOKEN}`,
      "Content-Type": "application/json",
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.status === 204 ? ({} as T) : response.json();
}
```

---

## Fetch API Examples

### Pages

```typescript
// Create page
async function createPage(title: string, icon?: string): Promise<Page> {
  return apiCall<Page>("/pages", {
    method: "POST",
    body: JSON.stringify({ title, icon }),
  });
}

// List pages
async function listPages(filters?: {
  parent_page_id?: string;
  is_archived?: boolean;
  is_favorite?: boolean;
  limit?: number;
  offset?: number;
}): Promise<{ pages: Page[]; total: number; limit: number; offset: number }> {
  const params = new URLSearchParams();
  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined) params.append(key, String(value));
    });
  }

  return apiCall(`/pages?${params.toString()}`);
}

// Get page
async function getPage(pageId: string): Promise<Page> {
  return apiCall(`/pages/${pageId}`);
}

// Update page
async function updatePage(
  pageId: string,
  updates: Partial<Pick<Page, "title" | "icon" | "is_favorite">>
): Promise<Page> {
  return apiCall(`/pages/${pageId}`, {
    method: "PUT",
    body: JSON.stringify(updates),
  });
}

// Delete page
async function deletePage(pageId: string): Promise<void> {
  return apiCall(`/pages/${pageId}`, { method: "DELETE" });
}

// Move page
async function movePage(pageId: string, newParentId: string | null): Promise<Page> {
  return apiCall(`/pages/${pageId}/move`, {
    method: "POST",
    body: JSON.stringify({ new_parent_id: newParentId }),
  });
}
```

### Blocks

```typescript
// Create block
async function createBlock(
  pageId: string,
  blockType: Block["block_type"],
  content: Record<string, any>
): Promise<Block> {
  return apiCall(`/blocks?page_id=${pageId}`, {
    method: "POST",
    body: JSON.stringify({ block_type: blockType, content }),
  });
}

// Batch create blocks
async function createBlocksBatch(
  pageId: string,
  blocks: Array<{ block_type: string; content: Record<string, any> }>
): Promise<{ blocks: Block[]; total: number }> {
  return apiCall(`/blocks/batch?page_id=${pageId}`, {
    method: "POST",
    body: JSON.stringify({ blocks }),
  });
}

// List blocks
async function listBlocks(
  pageId: string,
  filters?: { block_type?: string; limit?: number; offset?: number }
): Promise<{ blocks: Block[]; total: number; limit: number; offset: number }> {
  const params = new URLSearchParams({ page_id: pageId });
  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined) params.append(key, String(value));
    });
  }

  return apiCall(`/blocks?${params.toString()}`);
}

// Update block
async function updateBlock(
  blockId: string,
  updates: { content?: Record<string, any>; properties?: Record<string, any> }
): Promise<Block> {
  return apiCall(`/blocks/${blockId}`, {
    method: "PUT",
    body: JSON.stringify(updates),
  });
}

// Delete block
async function deleteBlock(blockId: string): Promise<void> {
  return apiCall(`/blocks/${blockId}`, { method: "DELETE" });
}

// Convert block type
async function convertBlockType(blockId: string, newType: Block["block_type"]): Promise<Block> {
  return apiCall(`/blocks/${blockId}/convert`, {
    method: "PUT",
    body: JSON.stringify({ new_type: newType }),
  });
}
```

### Search

```typescript
// Semantic search
async function searchBlocks(
  query: string,
  organizationId: string,
  filters?: {
    search_type?: "semantic" | "metadata" | "hybrid";
    block_types?: string[];
    page_id?: string;
    tags?: string[];
    limit?: number;
    threshold?: number;
  }
): Promise<{
  results: SearchResult[];
  total: number;
  search_type: string;
  query: string;
  threshold: number;
  limit: number;
}> {
  const params = new URLSearchParams({
    q: query,
    organization_id: organizationId,
  });

  if (filters) {
    if (filters.search_type) params.append("search_type", filters.search_type);
    if (filters.block_types) params.append("block_types", filters.block_types.join(","));
    if (filters.page_id) params.append("page_id", filters.page_id);
    if (filters.tags) params.append("tags", filters.tags.join(","));
    if (filters.limit) params.append("limit", String(filters.limit));
    if (filters.threshold) params.append("threshold", String(filters.threshold));
  }

  return apiCall(`/search?${params.toString()}`);
}
```

---

## Axios Examples

### Setup with Axios

```typescript
import axios, { AxiosInstance, AxiosError } from "axios";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1/ocean";
const JWT_TOKEN = process.env.NEXT_PUBLIC_JWT_TOKEN || "";

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Authorization": `Bearer ${JWT_TOKEN}`,
    "Content-Type": "application/json",
  },
});

// Error interceptor
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response) {
      const detail = (error.response.data as any)?.detail || error.message;
      throw new Error(`API Error ${error.response.status}: ${detail}`);
    }
    throw error;
  }
);
```

### Pages with Axios

```typescript
class PagesAPI {
  static async create(title: string, icon?: string): Promise<Page> {
    const { data } = await api.post<Page>("/pages", { title, icon });
    return data;
  }

  static async list(filters?: any): Promise<{ pages: Page[] }> {
    const { data } = await api.get("/pages", { params: filters });
    return data;
  }

  static async get(pageId: string): Promise<Page> {
    const { data } = await api.get<Page>(`/pages/${pageId}`);
    return data;
  }

  static async update(pageId: string, updates: any): Promise<Page> {
    const { data } = await api.put<Page>(`/pages/${pageId}`, updates);
    return data;
  }

  static async delete(pageId: string): Promise<void> {
    await api.delete(`/pages/${pageId}`);
  }

  static async move(pageId: string, newParentId: string | null): Promise<Page> {
    const { data } = await api.post<Page>(`/pages/${pageId}/move`, {
      new_parent_id: newParentId,
    });
    return data;
  }
}

// Usage
const page = await PagesAPI.create("My Page", "📄");
const pages = await PagesAPI.list({ is_favorite: true });
```

### Blocks with Axios

```typescript
class BlocksAPI {
  static async create(
    pageId: string,
    blockType: string,
    content: Record<string, any>
  ): Promise<Block> {
    const { data } = await api.post<Block>(
      `/blocks?page_id=${pageId}`,
      { block_type: blockType, content }
    );
    return data;
  }

  static async createBatch(
    pageId: string,
    blocks: Array<{ block_type: string; content: any }>
  ): Promise<{ blocks: Block[]; total: number }> {
    const { data } = await api.post(`/blocks/batch?page_id=${pageId}`, { blocks });
    return data;
  }

  static async list(pageId: string, filters?: any): Promise<{ blocks: Block[] }> {
    const { data } = await api.get("/blocks", { params: { page_id: pageId, ...filters } });
    return data;
  }

  static async get(blockId: string): Promise<Block> {
    const { data } = await api.get<Block>(`/blocks/${blockId}`);
    return data;
  }

  static async update(blockId: string, updates: any): Promise<Block> {
    const { data } = await api.put<Block>(`/blocks/${blockId}`, updates);
    return data;
  }

  static async delete(blockId: string): Promise<void> {
    await api.delete(`/blocks/${blockId}`);
  }

  static async convert(blockId: string, newType: string): Promise<Block> {
    const { data} = await api.put<Block>(`/blocks/${blockId}/convert`, { new_type: newType });
    return data;
  }
}
```

---

## Complete TypeScript Client

```typescript
// ocean-client.ts
import axios, { AxiosInstance } from "axios";

export class OceanClient {
  private api: AxiosInstance;

  constructor(baseURL: string, token: string) {
    this.api = axios.create({
      baseURL,
      headers: {
        "Authorization": `Bearer ${token}`,
        "Content-Type": "application/json",
      },
    });
  }

  // Pages
  async createPage(title: string, options?: Partial<Page>): Promise<Page> {
    const { data } = await this.api.post("/pages", { title, ...options });
    return data;
  }

  async listPages(filters?: any): Promise<{ pages: Page[]; total: number }> {
    const { data } = await this.api.get("/pages", { params: filters });
    return data;
  }

  async getPage(pageId: string): Promise<Page> {
    const { data } = await this.api.get(`/pages/${pageId}`);
    return data;
  }

  async updatePage(pageId: string, updates: Partial<Page>): Promise<Page> {
    const { data } = await this.api.put(`/pages/${pageId}`, updates);
    return data;
  }

  async deletePage(pageId: string): Promise<void> {
    await this.api.delete(`/pages/${pageId}`);
  }

  async movePage(pageId: string, newParentId: string | null): Promise<Page> {
    const { data } = await this.api.post(`/pages/${pageId}/move`, { new_parent_id: newParentId });
    return data;
  }

  // Blocks
  async createBlock(
    pageId: string,
    blockType: Block["block_type"],
    content: Record<string, any>,
    options?: any
  ): Promise<Block> {
    const { data } = await this.api.post(
      `/blocks?page_id=${pageId}`,
      { block_type: blockType, content, ...options }
    );
    return data;
  }

  async createBlocksBatch(
    pageId: string,
    blocks: Array<{ block_type: string; content: any }>
  ): Promise<{ blocks: Block[]; total: number }> {
    const { data } = await this.api.post(`/blocks/batch?page_id=${pageId}`, { blocks });
    return data;
  }

  async listBlocks(pageId: string, filters?: any): Promise<{ blocks: Block[]; total: number }> {
    const { data } = await this.api.get("/blocks", { params: { page_id: pageId, ...filters } });
    return data;
  }

  async getBlock(blockId: string): Promise<Block> {
    const { data } = await this.api.get(`/blocks/${blockId}`);
    return data;
  }

  async updateBlock(blockId: string, updates: any): Promise<Block> {
    const { data } = await this.api.put(`/blocks/${blockId}`, updates);
    return data;
  }

  async deleteBlock(blockId: string): Promise<void> {
    await this.api.delete(`/blocks/${blockId}`);
  }

  async moveBlock(blockId: string, newPosition: number): Promise<Block> {
    const { data } = await this.api.post(`/blocks/${blockId}/move`, { new_position: newPosition });
    return data;
  }

  async convertBlockType(blockId: string, newType: Block["block_type"]): Promise<Block> {
    const { data } = await this.api.put(`/blocks/${blockId}/convert`, { new_type: newType });
    return data;
  }

  // Search
  async search(query: string, organizationId: string, filters?: any): Promise<any> {
    const { data } = await this.api.get("/search", {
      params: { q: query, organization_id: organizationId, ...filters },
    });
    return data;
  }

  // Tags
  async createTag(name: string, options?: any): Promise<any> {
    const { data } = await this.api.post("/tags", { name, ...options });
    return data;
  }

  async listTags(sortBy: string = "usage_count"): Promise<any> {
    const { data } = await this.api.get("/tags", { params: { sort_by: sortBy } });
    return data;
  }

  async assignTagToBlock(blockId: string, tagId: string): Promise<any> {
    const { data } = await this.api.post(`/blocks/${blockId}/tags`, { tag_id: tagId });
    return data;
  }

  async removeTagFromBlock(blockId: string, tagId: string): Promise<any> {
    const { data } = await this.api.delete(`/blocks/${blockId}/tags/${tagId}`);
    return data;
  }

  // Links
  async createLink(
    sourceBlockId: string,
    targetId: string,
    linkType: string,
    isPageLink: boolean = false
  ): Promise<any> {
    const { data } = await this.api.post("/links", {
      source_block_id: sourceBlockId,
      target_id: targetId,
      link_type: linkType,
      is_page_link: isPageLink,
    });
    return data;
  }

  async getPageBacklinks(pageId: string): Promise<any> {
    const { data } = await this.api.get(`/pages/${pageId}/backlinks`);
    return data;
  }

  async getBlockBacklinks(blockId: string): Promise<any> {
    const { data } = await this.api.get(`/blocks/${blockId}/backlinks`);
    return data;
  }
}

// Usage
const client = new OceanClient(
  "http://localhost:8000/api/v1/ocean",
  "your_jwt_token"
);

const page = await client.createPage("My Page", { icon: "📄" });
const blocks = await client.listBlocks(page.page_id);
const results = await client.search("query", "org-456");
```

---

## React Hooks

```typescript
// hooks/useOcean.ts
import { useState, useEffect } from "react";
import { OceanClient } from "../lib/ocean-client";

const client = new OceanClient(
  process.env.NEXT_PUBLIC_API_URL!,
  process.env.NEXT_PUBLIC_JWT_TOKEN!
);

export function usePages(filters?: any) {
  const [pages, setPages] = useState<Page[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    client.listPages(filters)
      .then((data) => {
        setPages(data.pages);
        setLoading(false);
      })
      .catch((err) => {
        setError(err);
        setLoading(false);
      });
  }, [JSON.stringify(filters)]);

  return { pages, loading, error };
}

export function useBlocks(pageId: string, filters?: any) {
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    client.listBlocks(pageId, filters)
      .then((data) => {
        setBlocks(data.blocks);
        setLoading(false);
      })
      .catch((err) => {
        setError(err);
        setLoading(false);
      });
  }, [pageId, JSON.stringify(filters)]);

  return { blocks, loading, error };
}

export function useSearch(query: string, organizationId: string, filters?: any) {
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    if (!query) {
      setResults([]);
      return;
    }

    setLoading(true);
    client.search(query, organizationId, filters)
      .then((data) => {
        setResults(data.results);
        setLoading(false);
      })
      .catch((err) => {
        setError(err);
        setLoading(false);
      });
  }, [query, organizationId, JSON.stringify(filters)]);

  return { results, loading, error };
}

// Usage in React components
function PagesList() {
  const { pages, loading, error } = usePages({ is_favorite: true });

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <ul>
      {pages.map((page) => (
        <li key={page.page_id}>{page.title}</li>
      ))}
    </ul>
  );
}
```

---

## Additional Resources

- **API Reference:** [API_REFERENCE.md](../API_REFERENCE.md)
- **Python Examples:** [python_examples.md](./python_examples.md)
- **cURL Examples:** [curl_examples.md](./curl_examples.md)

---

**Last Updated:** 2025-12-24
**API Version:** 0.1.0
