# Ocean Blocks - Remaining ZeroDB API Fixes

## Status Summary

### ✅ COMPLETED (4 operations)
1. **create_block()** - Fixed: POST /rows with row_data wrapper
2. **batch_create_blocks()** - Fixed: Loop individual POST /rows
3. **get_block()** - Fixed: POST /query with row_data extraction
4. **get_blocks_by_page()** - Fixed: POST /query with row_data extraction

### ⚠️ REMAINING (5 operations + 1 helper)
5. **count_blocks_by_page()** - Needs: Fix query endpoint and response parsing
6. **update_block()** - Needs: Two-step (query for row_id, then PATCH)
7. **delete_block()** - Needs: Two-step (query for row_id, then DELETE)
8. **move_block()** - Needs: Two-step for all block position updates (2 places)
9. **convert_block_type()** - Needs: Two-step (query for row_id, then PATCH)
10. **_get_block_by_id()** (helper) - Needs: Same fix as get_block()

---

## Detailed Fixes Required

### Fix 5: count_blocks_by_page (line ~910)

**Current Code** (WRONG):
```python
async with httpx.AsyncClient() as client:
    response = await client.post(
        f"{self.api_url}/v1/public/zerodb/mcp/execute",
        headers=self.headers,
        json={
            "operation": "query_rows",
            "params": {
                "project_id": self.project_id,
                "table_name": self.blocks_table_name,
                "filter": query_filters,
                "limit": 1000  # Get all for count
            }
        },
        timeout=30.0
    )

    if response.status_code != 200:
        return 0

    result = response.json()
    if not result.get("success"):
        return 0

    rows = result.get("result", {}).get("rows", [])
    return len(rows)
```

**Fixed Code**:
```python
async with httpx.AsyncClient() as client:
    response = await client.post(
        f"{self.api_url}/v1/projects/{self.project_id}/database/tables/{self.blocks_table_name}/query",
        headers=self.headers,
        json={
            "filter": query_filters,
            "limit": 1000,
            "skip": 0
        },
        timeout=30.0
    )

    if response.status_code != 200:
        return 0

    result = response.json()
    rows_data = result.get("data", [])
    return len(rows_data)
```

---

### Fix 6: update_block (line ~1010)

**Current Code** (WRONG - one-step with filter):
```python
# Update in ZeroDB
async with httpx.AsyncClient() as client:
    response = await client.post(
        f"{self.api_url}/v1/public/zerodb/mcp/execute",
        headers=self.headers,
        json={
            "operation": "update_rows",
            "params": {
                "project_id": self.project_id,
                "table_name": self.blocks_table_name,
                "filter": {
                    "block_id": block_id,
                    "organization_id": org_id
                },
                "update": update_payload
            }
        },
        timeout=30.0
    )

    if response.status_code != 200:
        return None

# Return updated block
return await self.get_block(block_id, org_id)
```

**Fixed Code** (two-step: query + PATCH):
```python
# Update in ZeroDB (two-step process)
async with httpx.AsyncClient() as client:
    # Step 1: Query to get row_id
    query_response = await client.post(
        f"{self.api_url}/v1/projects/{self.project_id}/database/tables/{self.blocks_table_name}/query",
        headers=self.headers,
        json={
            "filter": {
                "block_id": block_id,
                "organization_id": org_id
            },
            "limit": 1
        },
        timeout=30.0
    )

    if query_response.status_code != 200:
        return None

    query_result = query_response.json()
    rows = query_result.get("data", [])
    if not rows:
        return None

    row_id = rows[0]["row_id"]

    # Step 2: Update by row_id
    response = await client.patch(
        f"{self.api_url}/v1/projects/{self.project_id}/database/tables/{self.blocks_table_name}/rows/{row_id}",
        headers=self.headers,
        json={
            "row_data": update_payload
        },
        timeout=30.0
    )

    if response.status_code != 200:
        return None

    # Return updated row_data
    result = response.json()
    return result.get("row_data")
```

---

### Fix 7: delete_block (line ~1070)

**Current Code** (WRONG):
```python
# Delete block from ZeroDB
async with httpx.AsyncClient() as client:
    response = await client.post(
        f"{self.api_url}/v1/public/zerodb/mcp/execute",
        headers=self.headers,
        json={
            "operation": "delete_rows",
            "params": {
                "project_id": self.project_id,
                "table_name": self.blocks_table_name,
                "filter": {
                    "block_id": block_id,
                    "organization_id": org_id
                }
            }
        },
        timeout=30.0
    )

    return response.status_code == 200
```

**Fixed Code**:
```python
# Delete block from ZeroDB (two-step process)
async with httpx.AsyncClient() as client:
    # Step 1: Query to get row_id
    query_response = await client.post(
        f"{self.api_url}/v1/projects/{self.project_id}/database/tables/{self.blocks_table_name}/query",
        headers=self.headers,
        json={
            "filter": {
                "block_id": block_id,
                "organization_id": org_id
            },
            "limit": 1
        },
        timeout=30.0
    )

    if query_response.status_code != 200:
        return False

    query_result = query_response.json()
    rows = query_result.get("data", [])
    if not rows:
        return False

    row_id = rows[0]["row_id"]

    # Step 2: Delete by row_id
    response = await client.delete(
        f"{self.api_url}/v1/projects/{self.project_id}/database/tables/{self.blocks_table_name}/rows/{row_id}",
        headers=self.headers,
        timeout=30.0
    )

    return response.status_code == 204  # Changed from 200 to 204
```

---

### Fix 8a: move_block - Update affected blocks loop (line ~1150)

**Current Code** (WRONG):
```python
# Update affected blocks
for update in updates_needed:
    async with httpx.AsyncClient() as client:
        await client.post(
            f"{self.api_url}/v1/public/zerodb/mcp/execute",
            headers=self.headers,
            json={
                "operation": "update_rows",
                "params": {
                    "project_id": self.project_id,
                    "table_name": self.blocks_table_name,
                    "filter": {
                        "block_id": update["block_id"],
                        "organization_id": org_id
                    },
                    "update": {
                        "position": update["new_position"],
                        "updated_at": datetime.utcnow().isoformat()
                    }
                }
            },
            timeout=30.0
        )
```

**Fixed Code**:
```python
# Update affected blocks (two-step for each)
async with httpx.AsyncClient() as client:
    for update in updates_needed:
        # Query to get row_id
        query_response = await client.post(
            f"{self.api_url}/v1/projects/{self.project_id}/database/tables/{self.blocks_table_name}/query",
            headers=self.headers,
            json={
                "filter": {
                    "block_id": update["block_id"],
                    "organization_id": org_id
                },
                "limit": 1
            },
            timeout=30.0
        )

        if query_response.status_code == 200:
            query_result = query_response.json()
            rows = query_result.get("data", [])
            if rows:
                row_id = rows[0]["row_id"]

                # Update by row_id
                await client.patch(
                    f"{self.api_url}/v1/projects/{self.project_id}/database/tables/{self.blocks_table_name}/rows/{row_id}",
                    headers=self.headers,
                    json={
                        "row_data": {
                            "position": update["new_position"],
                            "updated_at": datetime.utcnow().isoformat()
                        }
                    },
                    timeout=30.0
                )
```

### Fix 8b: move_block - Update moved block (line ~1175)

**Current Code** (WRONG):
```python
# Update the moved block
async with httpx.AsyncClient() as client:
    response = await client.post(
        f"{self.api_url}/v1/public/zerodb/mcp/execute",
        headers=self.headers,
        json={
            "operation": "update_rows",
            "params": {
                "project_id": self.project_id,
                "table_name": self.blocks_table_name,
                "filter": {
                    "block_id": block_id,
                    "organization_id": org_id
                },
                "update": {
                    "position": new_position,
                    "updated_at": datetime.utcnow().isoformat()
                }
            }
        },
        timeout=30.0
    )

    if response.status_code != 200:
        return None

# Return updated block
return await self.get_block(block_id, org_id)
```

**Fixed Code**:
```python
# Update the moved block (two-step process)
async with httpx.AsyncClient() as client:
    # Query to get row_id
    query_response = await client.post(
        f"{self.api_url}/v1/projects/{self.project_id}/database/tables/{self.blocks_table_name}/query",
        headers=self.headers,
        json={
            "filter": {
                "block_id": block_id,
                "organization_id": org_id
            },
            "limit": 1
        },
        timeout=30.0
    )

    if query_response.status_code != 200:
        return None

    query_result = query_response.json()
    rows = query_result.get("data", [])
    if not rows:
        return None

    row_id = rows[0]["row_id"]

    # Update by row_id
    response = await client.patch(
        f"{self.api_url}/v1/projects/{self.project_id}/database/tables/{self.blocks_table_name}/rows/{row_id}",
        headers=self.headers,
        json={
            "row_data": {
                "position": new_position,
                "updated_at": datetime.utcnow().isoformat()
            }
        },
        timeout=30.0
    )

    if response.status_code != 200:
        return None

    # Return updated row_data
    result = response.json()
    return result.get("row_data")
```

---

### Fix 9: convert_block_type (line ~1285)

**Current Code** (WRONG):
```python
# Update in ZeroDB
async with httpx.AsyncClient() as client:
    response = await client.post(
        f"{self.api_url}/v1/public/zerodb/mcp/execute",
        headers=self.headers,
        json={
            "operation": "update_rows",
            "params": {
                "project_id": self.project_id,
                "table_name": self.blocks_table_name,
                "filter": {
                    "block_id": block_id,
                    "organization_id": org_id
                },
                "update": update_payload
            }
        },
        timeout=30.0
    )

    if response.status_code != 200:
        return None

# Return updated block
return await self.get_block(block_id, org_id)
```

**Fixed Code**:
```python
# Update in ZeroDB (two-step process)
async with httpx.AsyncClient() as client:
    # Query to get row_id
    query_response = await client.post(
        f"{self.api_url}/v1/projects/{self.project_id}/database/tables/{self.blocks_table_name}/query",
        headers=self.headers,
        json={
            "filter": {
                "block_id": block_id,
                "organization_id": org_id
            },
            "limit": 1
        },
        timeout=30.0
    )

    if query_response.status_code != 200:
        return None

    query_result = query_response.json()
    rows = query_result.get("data", [])
    if not rows:
        return None

    row_id = rows[0]["row_id"]

    # Update by row_id
    response = await client.patch(
        f"{self.api_url}/v1/projects/{self.project_id}/database/tables/{self.blocks_table_name}/rows/{row_id}",
        headers=self.headers,
        json={
            "row_data": update_payload
        },
        timeout=30.0
    )

    if response.status_code != 200:
        return None

    # Return updated row_data
    result = response.json()
    return result.get("row_data")
```

---

### Fix 10: _get_block_by_id (helper method - if exists)

This is likely a helper method that duplicates get_block logic. Apply the same fix as get_block().

---

## Testing After Fixes

Run these tests to verify:

```bash
cd /Users/aideveloper/ocean-backend

# Test all block operations
pytest tests/test_ocean_blocks.py -v

# Expected: All 24 tests should PASS (once deployed with actual API)
```

---

## Commit Message Template

```
Fix ocean_blocks ZeroDB API integration

- Update create_block to POST /rows with row_data wrapper
- Update batch_create_blocks to loop individual POST /rows calls
- Update get_block to POST /query with row_data extraction
- Update get_blocks_by_page to POST /query with row_data extraction
- Update count_blocks_by_page to use correct query endpoint
- Update update_block to two-step (query for row_id, then PATCH)
- Update delete_block to two-step (query for row_id, then DELETE)
- Update move_block to use two-step for all position updates
- Update convert_block_type to two-step (query + PATCH)

All ocean_blocks operations now use correct ZeroDB REST API endpoints
instead of non-existent /mcp/execute bridge.

Refs #388
```

---

**Last Updated**: 2025-12-24
**Status**: 4/9 operations fixed, 5 remaining
