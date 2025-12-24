# Redis Caching - Future Enhancement

**Status:** 📋 Planned (Not Implemented)
**Priority:** Medium
**Estimated Effort:** 5 story points
**Depends On:** Production traffic analysis, Redis infrastructure

---

## Overview

Redis caching is a **future enhancement** to reduce query latencies by caching frequently accessed data locally. This document outlines the strategy, implementation approach, and trade-offs.

**Why Not Implemented Now:**
- Adds deployment complexity (Redis server required)
- Requires cache invalidation logic (non-trivial with distributed systems)
- Benefits unclear without production traffic patterns
- Network latency to ZeroDB API is the bottleneck (caching helps but doesn't eliminate)

**When to Implement:**
- Production traffic reveals hot data patterns
- Read/write ratio justifies caching overhead (>80% reads ideal)
- Latency reduction becomes critical for user experience

---

## Proposed Architecture

### Cache Layers

```
Client Request
    ↓
FastAPI Endpoint
    ↓
Check Redis Cache ← [CACHE HIT: Return immediately]
    ↓ [CACHE MISS]
Query ZeroDB API
    ↓
Store in Redis Cache (with TTL)
    ↓
Return to Client
```

### Cache Keys Strategy

```python
# Page cache keys
page:{page_id}                      # Individual page data
pages:{org_id}:list:{filter_hash}   # Page lists with filters
pages:{org_id}:count:{filter_hash}  # Page counts

# Block cache keys
blocks:{page_id}:list:{filter_hash} # Block lists by page
blocks:{page_id}:count:{filter_hash} # Block counts
block:{block_id}                     # Individual block data

# Search cache keys
search:{org_id}:{query_hash}:results # Search results
```

### TTL Strategy

| Data Type | TTL | Reasoning |
|-----------|-----|-----------|
| Individual pages | 5 minutes | Pages change infrequently |
| Page lists | 1 minute | Lists change more often (new pages) |
| Individual blocks | 2 minutes | Blocks edited more frequently than pages |
| Block lists | 30 seconds | Block order/content changes often |
| Search results | 30 seconds | Content updates should reflect quickly |
| Count queries | 1 minute | Tolerable slight staleness |

---

## Implementation Plan

### Phase 1: Read-Through Cache (Pages Only)

**Goal:** Cache page reads with simple invalidation

```python
async def get_page_cached(self, page_id: str, org_id: str) -> Optional[Dict]:
    """Get page with Redis read-through cache."""

    # Check cache
    cache_key = f"page:{page_id}"
    cached = await redis.get(cache_key)
    if cached:
        # Verify organization_id matches
        page = json.loads(cached)
        if page.get("organization_id") == org_id:
            return page

    # Cache miss - query ZeroDB
    page = await self.get_page(page_id, org_id)
    if page:
        # Store in cache with TTL
        await redis.setex(
            cache_key,
            300,  # 5 minutes
            json.dumps(page)
        )

    return page
```

**Invalidation:**
```python
async def update_page_cached(self, page_id: str, org_id: str, updates: Dict) -> Optional[Dict]:
    """Update page and invalidate cache."""

    # Update in ZeroDB
    updated = await self.update_page(page_id, org_id, updates)

    if updated:
        # Invalidate cache
        cache_key = f"page:{page_id}"
        await redis.delete(cache_key)

        # Also invalidate list caches for this org
        pattern = f"pages:{org_id}:*"
        await redis_delete_pattern(pattern)

    return updated
```

### Phase 2: List and Count Caching

**Goal:** Cache paginated lists and counts

```python
async def get_pages_cached(
    self,
    org_id: str,
    filters: Optional[Dict] = None,
    pagination: Optional[Dict] = None
) -> Tuple[List[Dict], int]:
    """Get pages with list caching."""

    # Create cache key from filters
    filter_hash = hashlib.md5(
        json.dumps(filters or {}, sort_keys=True).encode()
    ).hexdigest()[:8]

    list_key = f"pages:{org_id}:list:{filter_hash}"
    count_key = f"pages:{org_id}:count:{filter_hash}"

    # Try cache
    cached_list = await redis.get(list_key)
    cached_count = await redis.get(count_key)

    if cached_list and cached_count:
        pages = json.loads(cached_list)
        total = int(cached_count)

        # Apply pagination locally
        limit = pagination.get("limit", 50) if pagination else 50
        offset = pagination.get("offset", 0) if pagination else 0
        return pages[offset:offset+limit], total

    # Cache miss - query ZeroDB
    pages = await self.get_pages(org_id, filters, pagination=None)  # Get all
    total = len(pages)

    # Cache full list and count
    await redis.setex(list_key, 60, json.dumps(pages))  # 1 min TTL
    await redis.setex(count_key, 60, str(total))

    # Apply pagination
    limit = pagination.get("limit", 50) if pagination else 50
    offset = pagination.get("offset", 0) if pagination else 0
    return pages[offset:offset+limit], total
```

### Phase 3: Write-Through Cache (Blocks)

**Goal:** Cache block lists with write-through strategy

```python
async def create_block_cached(self, page_id: str, org_id: str, user_id: str, block_data: Dict) -> Dict:
    """Create block and update cache."""

    # Create in ZeroDB
    block = await self.create_block(page_id, org_id, user_id, block_data)

    if block:
        # Invalidate block list cache for this page
        pattern = f"blocks:{page_id}:*"
        await redis_delete_pattern(pattern)

        # Optionally: Update cache with new block (write-through)
        # This is complex with pagination, usually just invalidate

    return block
```

---

## Configuration

### Redis Connection Settings

```python
# app/config.py
class Settings(BaseSettings):
    # ... existing settings ...

    # Redis Configuration (optional)
    REDIS_ENABLED: bool = False
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 10
    REDIS_SOCKET_TIMEOUT: int = 5

    # Cache TTLs (seconds)
    CACHE_PAGE_TTL: int = 300      # 5 minutes
    CACHE_PAGE_LIST_TTL: int = 60  # 1 minute
    CACHE_BLOCK_TTL: int = 120     # 2 minutes
    CACHE_BLOCK_LIST_TTL: int = 30 # 30 seconds
    CACHE_SEARCH_TTL: int = 30     # 30 seconds
```

### Dependencies

```bash
# Add to requirements.txt
redis==5.0.1
hiredis==2.3.2  # Optional: faster Redis protocol parser
```

### Docker Compose (Development)

```yaml
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  redis_data:
```

---

## Performance Impact Estimates

### Expected Latency Reduction

| Operation | Current P95 | With Cache Hit | Improvement |
|-----------|-------------|----------------|-------------|
| Page Read | 800ms | **5-10ms** | 80-160x faster |
| Page List | 749ms | **10-20ms** | 37-75x faster |
| Block List | 682ms | **10-20ms** | 34-68x faster |

**Assumptions:**
- Cache hit ratio: 80% (depends on traffic patterns)
- Redis local or same datacenter (~1ms latency)
- Cache misses still hit ZeroDB API (no improvement)

### Cache Hit Ratio Predictions

Based on typical usage patterns:

| Scenario | Expected Hit Ratio |
|----------|-------------------|
| Viewing same page repeatedly | 90-95% |
| Browsing page lists | 70-80% |
| Editing content | 30-50% (lots of writes invalidate cache) |
| Search queries | 40-60% (depends on query diversity) |

**Overall Expected:** 60-80% cache hit ratio in production

---

## Challenges and Trade-offs

### Challenges

1. **Cache Invalidation Complexity**
   - Page updates must invalidate related list caches
   - Block changes must invalidate page's block list
   - Search results must be invalidated on content changes
   - Risk of stale data if invalidation logic has bugs

2. **Memory Management**
   - Redis memory limits require eviction policies
   - Large lists (pages with 1000+ blocks) consume significant memory
   - Need monitoring for memory pressure

3. **Distributed Invalidation**
   - Multiple API instances need coordinated cache invalidation
   - Redis Pub/Sub can help but adds complexity
   - Eventual consistency issues during invalidation

4. **Cold Start Performance**
   - First request after deployment has 0% cache hit
   - May need cache warming strategies

### Trade-offs

| Benefit | Cost |
|---------|------|
| 80-90% latency reduction on hits | Cache invalidation logic complexity |
| Reduced load on ZeroDB API | Additional Redis infrastructure |
| Better user experience | Memory consumption and limits |
| Predictable low latency | Eventual consistency during invalidation |

---

## When to Implement

**Prerequisites:**
1. **Production traffic data available**
   - Read/write ratios per endpoint
   - Hot data identification (most accessed pages/blocks)
   - Query pattern analysis

2. **Latency becomes user pain point**
   - User complaints about slow page loads
   - Metrics show latency impacting conversions
   - Business case for infrastructure investment

3. **Redis infrastructure approved**
   - Budget for Redis hosting (Railway, AWS ElastiCache, etc.)
   - Team capacity for cache management
   - Monitoring tools in place

**Decision Criteria:**

Implement if **ANY** of:
- [ ] Read/write ratio >80% reads
- [ ] P95 latency >2 seconds in production
- [ ] User feedback indicates slowness
- [ ] Hot pages identified (top 20% of pages get 80% of traffic)

**Don't implement if:**
- Traffic too low to justify complexity (<100 requests/day)
- Write-heavy workload (>50% writes)
- Infrastructure budget constrained

---

## Alternative Approaches

### 1. Database Migration (Instead of Caching)
Move from ZeroDB to PostgreSQL in same datacenter:
- **Pros:** Full control, <5ms latency, no cache complexity
- **Cons:** Infrastructure management, migration effort, lose ZeroDB benefits

### 2. Co-location with ZeroDB
Deploy Ocean backend in same region as ZeroDB API:
- **Pros:** 10x latency reduction, no caching needed
- **Cons:** May still not hit <100ms targets, deployment location locked

### 3. Client-Side Caching
Cache data in browser localStorage/IndexedDB:
- **Pros:** Zero server cost, instant for cache hits
- **Cons:** Stale data risk, per-user cache (no sharing), limited to UI

### 4. HTTP Caching (CDN)
Use CDN edge caching for read-only endpoints:
- **Pros:** Global distribution, easy setup (Vercel/Cloudflare)
- **Cons:** Doesn't help authenticated requests, harder to invalidate

---

## Monitoring and Observability

### Metrics to Track (When Implemented)

```python
# Cache hit rate
cache_hit_rate = cache_hits / (cache_hits + cache_misses)

# Cache latency
cache_hit_latency_p95   # Should be <10ms
cache_miss_latency_p95  # Should match ZeroDB API latency

# Invalidation rate
cache_invalidations_per_minute

# Memory usage
redis_memory_used_mb
redis_memory_percent
```

### Alerts to Configure

- Cache hit rate drops below 60% (investigate query patterns)
- Redis memory usage >80% (increase limit or add eviction)
- Cache latency >50ms (Redis performance issue)
- High invalidation rate (may indicate thrashing)

---

## Conclusion

**Redis caching is a valuable future enhancement** but **not critical for initial deployment**. Current performance (500-1600ms p95) is acceptable for low-traffic MVP.

**Implement when:**
- Production traffic justifies complexity
- Clear hot data patterns emerge
- User experience demands faster responses

**For now:**
- Monitor query logs to identify hot endpoints
- Track cache hit ratio assumptions with analytics
- Revisit decision after 3-6 months of production data

---

**Documented:** 2024-12-24
**Status:** Future Enhancement (Not Implemented)
**Owner:** Backend Team
**Review Date:** After production deployment + 3 months
