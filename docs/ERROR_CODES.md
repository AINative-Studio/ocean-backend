# Ocean API Error Codes Reference

**Version:** 0.1.0
**Last Updated:** 2025-12-24

---

## Table of Contents

1. [Error Response Format](#error-response-format)
2. [HTTP Status Codes](#http-status-codes)
3. [Error Categories](#error-categories)
   - [2xx Success](#2xx-success)
   - [4xx Client Errors](#4xx-client-errors)
   - [5xx Server Errors](#5xx-server-errors)
4. [Common Error Scenarios](#common-error-scenarios)
5. [Troubleshooting Guide](#troubleshooting-guide)
6. [Error Handling Best Practices](#error-handling-best-practices)

---

## Error Response Format

All API errors return a consistent JSON structure with a `detail` field explaining the error.

**Standard Error Response:**

```json
{
  "detail": "Error message describing what went wrong"
}
```

**Validation Error Response:**

```json
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

---

## HTTP Status Codes

Ocean API uses standard HTTP status codes to indicate request success or failure.

| Code | Status | Meaning | Typical Cause |
|------|--------|---------|---------------|
| **200** | OK | Successful GET/PUT request | Resource retrieved or updated |
| **201** | Created | Successful POST request | New resource created |
| **204** | No Content | Successful DELETE request | Resource deleted |
| **400** | Bad Request | Client sent invalid data | Missing fields, validation errors, circular references |
| **401** | Unauthorized | Authentication failed | Missing/invalid JWT token, expired token |
| **404** | Not Found | Resource doesn't exist | Invalid ID, wrong organization |
| **422** | Unprocessable Entity | Validation error | Invalid field types, constraint violations |
| **500** | Internal Server Error | Server-side error | Database errors, embedding failures, unexpected exceptions |

---

## Error Categories

### 2xx Success

#### 200 OK

**Meaning:** Request succeeded, response body contains data

**Endpoints:**
- `GET /pages`, `GET /pages/{page_id}`
- `PUT /pages/{page_id}`, `PUT /blocks/{block_id}`
- `POST /pages/{page_id}/move`, `POST /blocks/{block_id}/move`
- `GET /search`

**Response Example:**

```json
{
  "page_id": "page_123",
  "title": "Product Roadmap",
  ...
}
```

---

#### 201 Created

**Meaning:** Resource successfully created

**Endpoints:**
- `POST /pages`
- `POST /blocks`, `POST /blocks/batch`
- `POST /links`
- `POST /tags`

**Response Example:**

```json
{
  "page_id": "page_123",
  "organization_id": "org-456",
  "created_at": "2025-12-24T10:00:00Z",
  ...
}
```

---

#### 204 No Content

**Meaning:** Resource successfully deleted, no response body

**Endpoints:**
- `DELETE /pages/{page_id}`
- `DELETE /blocks/{block_id}`
- `DELETE /links/{link_id}`

**Response:** Empty body (no JSON)

---

### 4xx Client Errors

#### 400 Bad Request

**Meaning:** Invalid request data sent by client

**Common Causes:**

1. **Missing Required Fields**
2. **Validation Errors**
3. **Circular References**
4. **Invalid Enum Values**
5. **No Fields Provided for Update**

---

**1. Missing Required Fields**

**Example Request:**

```bash
curl -X POST http://localhost:8000/api/v1/ocean/pages \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Error Response:**

```json
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Solution:** Include all required fields in request body.

```json
{
  "title": "Product Roadmap"
}
```

---

**2. Validation Errors**

**Example:** Title too long (>500 characters)

**Error Response:**

```json
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "ensure this value has at most 500 characters",
      "type": "value_error.any_str.max_length"
    }
  ]
}
```

**Solution:** Ensure field values meet validation constraints.

---

**3. Circular References (Links)**

**Example:** Creating a link that would form a cycle

**Request:**

```json
{
  "source_block_id": "block_A",
  "target_id": "block_B",  // block_B already links to block_A
  "link_type": "reference"
}
```

**Error Response:**

```json
{
  "detail": "Circular reference detected: block_A → block_B → block_A"
}
```

**Solution:** Remove existing circular link before creating new one.

---

**4. Invalid Enum Values**

**Example:** Invalid block_type

**Request:**

```json
{
  "block_type": "invalid_type",
  "content": {"text": "..."}
}
```

**Error Response:**

```json
{
  "detail": "block_type must be one of: text, heading, list, task, link, page_link"
}
```

**Solution:** Use valid block type from allowed list.

---

**5. No Fields Provided for Update**

**Example:** Empty update request

**Request:**

```bash
curl -X PUT http://localhost:8000/api/v1/ocean/pages/page_123 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Error Response:**

```json
{
  "detail": "No fields provided for update"
}
```

**Solution:** Include at least one field to update.

```json
{
  "title": "Updated Title"
}
```

---

#### 401 Unauthorized

**Meaning:** Authentication failed or token invalid

**Common Causes:**

1. **Missing Authorization Header**
2. **Invalid Token Format**
3. **Expired Token**
4. **Invalid Signature**
5. **Missing Token Claims**

---

**1. Missing Authorization Header**

**Example Request:**

```bash
curl -X GET http://localhost:8000/api/v1/ocean/pages
```

**Error Response:**

```json
{
  "detail": "Not authenticated"
}
```

**Solution:** Include Authorization header with Bearer token.

```bash
curl -X GET http://localhost:8000/api/v1/ocean/pages \
  -H "Authorization: Bearer eyJhbGci..."
```

---

**2. Invalid Token Format**

**Example:** Wrong header format

```bash
# ❌ Wrong
Authorization: eyJhbGci...

# ❌ Wrong
Authorization: Token eyJhbGci...

# ✅ Correct
Authorization: Bearer eyJhbGci...
```

**Error Response:**

```json
{
  "detail": "Invalid authentication credentials"
}
```

**Solution:** Use correct format: `Bearer <token>`

---

**3. Expired Token**

**Error Response:**

```json
{
  "detail": "Token has expired"
}
```

**Solution:**
- Request new token from auth service
- Implement automatic token refresh
- Use longer-lived tokens if appropriate

**Debug:**

```python
import jwt
from datetime import datetime

token = "your_token"
decoded = jwt.decode(token, options={"verify_signature": False})
exp_timestamp = decoded["exp"]
exp_datetime = datetime.fromtimestamp(exp_timestamp)

print(f"Token expires at: {exp_datetime}")
print(f"Current time: {datetime.now()}")
print(f"Expired: {datetime.now() > exp_datetime}")
```

---

**4. Invalid Signature**

**Error Response:**

```json
{
  "detail": "Invalid token signature"
}
```

**Causes:**
- Token signed with different `SECRET_KEY`
- Token tampered with manually
- Token issued by untrusted source

**Solution:**
- Verify `SECRET_KEY` matches between services
- Ensure token from trusted auth service
- Never manually edit tokens

---

**5. Missing Token Claims**

**Error Response:**

```json
{
  "detail": "Token missing required claims: user_id, organization_id"
}
```

**Causes:**
- Auth service not including required claims
- Old token format from previous version

**Solution:**
- Update auth service to include `user_id` and `organization_id`
- Request new token with correct claims

**Valid Token Payload:**

```json
{
  "user_id": "test-user-123",
  "organization_id": "test-org-456",
  "exp": 1735123456
}
```

---

#### 404 Not Found

**Meaning:** Resource doesn't exist or doesn't belong to organization

**Common Causes:**

1. **Invalid Resource ID**
2. **Resource Belongs to Different Organization**
3. **Resource Deleted**
4. **Typo in Endpoint**

---

**1. Invalid Resource ID**

**Error Response:**

```json
{
  "detail": "Page page_xyz not found or does not belong to organization"
}
```

**Solution:**
- Verify resource ID is correct
- Check for typos in ID
- Use List endpoint to find valid IDs

---

**2. Resource Belongs to Different Organization**

**Scenario:** User from org-A tries to access resource from org-B

**Error Response:**

```json
{
  "detail": "Page page_123 not found or does not belong to organization"
}
```

**Note:** Error message is intentionally vague for security (doesn't reveal resource exists in another org)

**Solution:**
- Verify logged in with correct organization
- Request token for correct organization
- Check resource ownership in database (if admin)

---

**3. Resource Deleted**

**Scenario:** Page was soft-deleted (archived)

**Error Response:**

```json
{
  "detail": "Page page_123 not found or does not belong to organization"
}
```

**Solution:**
- Check if page is archived
- Use `is_archived` filter in List endpoint
- Restore page by setting `is_archived=false`

**Check if Archived:**

```bash
curl -X GET "http://localhost:8000/api/v1/ocean/pages?is_archived=true" \
  -H "Authorization: Bearer <token>"
```

---

**4. Typo in Endpoint**

**Example:**

```bash
# ❌ Wrong
curl -X GET http://localhost:8000/api/v1/ocean/page/page_123

# ✅ Correct
curl -X GET http://localhost:8000/api/v1/ocean/pages/page_123
```

**Error Response:**

```json
{
  "detail": "Not Found"
}
```

**Solution:** Verify endpoint path matches API documentation.

---

#### 422 Unprocessable Entity

**Meaning:** Request syntax is valid but data fails validation

**Common Causes:**

1. **Invalid Field Types**
2. **Constraint Violations**
3. **Regex Validation Failures**

---

**Example: Invalid Field Type**

**Request:**

```json
{
  "position": "five"  // Should be integer
}
```

**Error Response:**

```json
{
  "detail": [
    {
      "loc": ["body", "position"],
      "msg": "value is not a valid integer",
      "type": "type_error.integer"
    }
  ]
}
```

**Solution:** Use correct field type (integer instead of string).

---

### 5xx Server Errors

#### 500 Internal Server Error

**Meaning:** Unexpected error occurred on server

**Common Causes:**

1. **Database Connection Failure**
2. **Embedding Generation Failure**
3. **ZeroDB API Timeout**
4. **Unhandled Exceptions**

---

**1. Database Connection Failure**

**Error Response:**

```json
{
  "detail": "Internal server error: Failed to connect to database"
}
```

**Causes:**
- ZeroDB API down
- Network connectivity issues
- Invalid API credentials

**Solution:**
- Check ZeroDB service status
- Verify `ZERODB_API_URL` and `ZERODB_API_KEY` in env
- Retry request after a few seconds

---

**2. Embedding Generation Failure**

**Error Response:**

```json
{
  "detail": "Internal server error: Failed to generate embedding for block"
}
```

**Causes:**
- Embedding model unavailable
- Input text too long
- API quota exceeded

**Solution:**
- Retry request
- Reduce block content length if very large
- Check embedding service status
- Contact support if persists

---

**3. ZeroDB API Timeout**

**Error Response:**

```json
{
  "detail": "Internal server error: Request to ZeroDB timed out"
}
```

**Causes:**
- Network latency
- ZeroDB service slow response
- Large batch operation

**Solution:**
- Retry request
- Reduce batch size (for batch operations)
- Check network connectivity
- Contact support if persists

---

**4. Unhandled Exceptions**

**Error Response:**

```json
{
  "detail": "Internal server error: <exception_message>"
}
```

**Solution:**
- Report error to support with:
  - Request details (endpoint, method, body)
  - Error message
  - Timestamp
- Include any additional context
- Check server logs if available

---

## Common Error Scenarios

### Scenario 1: Creating a Page Without Authentication

**Request:**

```bash
curl -X POST http://localhost:8000/api/v1/ocean/pages \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Page"}'
```

**Error:** `401 Unauthorized`

**Response:**

```json
{
  "detail": "Not authenticated"
}
```

**Fix:**

```bash
curl -X POST http://localhost:8000/api/v1/ocean/pages \
  -H "Authorization: Bearer <JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Page"}'
```

---

### Scenario 2: Updating Non-Existent Block

**Request:**

```bash
curl -X PUT http://localhost:8000/api/v1/ocean/blocks/invalid_id \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"content": {"text": "Updated"}}'
```

**Error:** `404 Not Found`

**Response:**

```json
{
  "detail": "Block invalid_id not found or does not belong to organization"
}
```

**Fix:**
- Verify block ID exists using `GET /blocks?page_id=...`
- Ensure block belongs to your organization
- Check for typos in block ID

---

### Scenario 3: Creating Block with Invalid Type

**Request:**

```bash
curl -X POST "http://localhost:8000/api/v1/ocean/blocks?page_id=page_123" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "block_type": "paragraph",
    "content": {"text": "Hello"}
  }'
```

**Error:** `400 Bad Request`

**Response:**

```json
{
  "detail": "block_type must be one of: text, heading, list, task, link, page_link"
}
```

**Fix:**

```json
{
  "block_type": "text",
  "content": {"text": "Hello"}
}
```

---

### Scenario 4: Circular Link Detection

**Setup:**
- block_A links to block_B
- block_B links to block_C

**Request:** Create link from block_C to block_A

```bash
curl -X POST http://localhost:8000/api/v1/ocean/links \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "source_block_id": "block_C",
    "target_id": "block_A",
    "link_type": "reference"
  }'
```

**Error:** `400 Bad Request`

**Response:**

```json
{
  "detail": "Circular reference detected: block_A → block_B → block_C → block_A"
}
```

**Fix:** Remove one of the existing links before creating new link.

---

### Scenario 5: Tag Name Conflict

**Request:** Create tag with duplicate name

```bash
curl -X POST http://localhost:8000/api/v1/ocean/tags \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"name": "important"}'
```

**Error (if tag "important" already exists):** `400 Bad Request`

**Response:**

```json
{
  "detail": "Tag with name 'important' already exists in organization"
}
```

**Fix:** Use unique tag name or update existing tag.

---

### Scenario 6: Search with Empty Query

**Request:**

```bash
curl -X GET "http://localhost:8000/api/v1/ocean/search?q=&organization_id=org-456" \
  -H "Authorization: Bearer <token>"
```

**Error:** `400 Bad Request`

**Response:**

```json
{
  "detail": "Search query cannot be empty"
}
```

**Fix:**

```bash
curl -X GET "http://localhost:8000/api/v1/ocean/search?q=machine%20learning&organization_id=org-456" \
  -H "Authorization: Bearer <token>"
```

---

## Troubleshooting Guide

### Debug Checklist

When encountering an error, follow this checklist:

**1. Check Error Code**
- What is the HTTP status code? (400, 401, 404, 500?)
- Read error message carefully

**2. Verify Authentication**
- Is Authorization header included?
- Is token format correct (`Bearer <token>`)?
- Is token expired? (check `exp` claim)

**3. Validate Request**
- Are all required fields included?
- Are field types correct (string vs integer)?
- Are field values valid (enum values, lengths)?

**4. Check Resource Existence**
- Does resource ID exist?
- Does resource belong to your organization?
- Is resource archived/deleted?

**5. Review Logs**
- Check server logs for detailed error messages
- Enable debug mode if available
- Look for stack traces

**6. Test with cURL**
- Simplify request to minimal example
- Test endpoint with known-good data
- Isolate issue to specific field or parameter

---

### Debugging Tools

**1. JWT Token Decoder**

```python
import jwt

token = "your_token_here"
decoded = jwt.decode(token, options={"verify_signature": False})
print(decoded)
```

**Online:** https://jwt.io

---

**2. API Testing with Postman**

Create Postman collection with:
- Environment variables for base URL and token
- Pre-request scripts for token refresh
- Tests for response validation

---

**3. cURL Testing**

```bash
# Test authentication
curl -v -X GET http://localhost:8000/api/v1/ocean/pages \
  -H "Authorization: Bearer <token>"

# -v flag shows request/response headers
# Verify Authorization header is being sent
```

---

**4. Python Debugging**

```python
import requests

response = requests.get(
    "http://localhost:8000/api/v1/ocean/pages",
    headers={"Authorization": f"Bearer {token}"}
)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
print(f"Headers: {response.headers}")
```

---

### When to Contact Support

Contact support if:

- Error persists after following troubleshooting steps
- Error message indicates server-side issue (500 errors)
- Unexpected behavior not explained by error message
- Security concerns or suspected vulnerabilities

**Include in Support Request:**

1. **Error Details:**
   - HTTP status code
   - Error message/response body
   - Timestamp

2. **Request Details:**
   - Endpoint URL
   - HTTP method (GET, POST, etc.)
   - Request body (sanitize sensitive data)
   - Request headers (sanitize tokens)

3. **Context:**
   - What you were trying to do
   - Steps to reproduce
   - Expected vs actual behavior

4. **Environment:**
   - Ocean API version
   - Client library/language
   - Browser (if web app)

---

## Error Handling Best Practices

### Client-Side Error Handling

**1. Always Check Status Codes**

```typescript
// TypeScript/JavaScript
async function getPages(token: string) {
  const response = await fetch('/api/v1/ocean/pages', {
    headers: { 'Authorization': `Bearer ${token}` }
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(`API Error ${response.status}: ${error.detail}`);
  }

  return await response.json();
}

// Usage
try {
  const pages = await getPages(token);
  console.log(pages);
} catch (error) {
  console.error('Failed to fetch pages:', error.message);
  // Handle error (show user message, retry, etc.)
}
```

---

**2. Implement Retry Logic for 500 Errors**

```python
import requests
import time

def api_request_with_retry(url, headers, max_retries=3):
    """Make API request with exponential backoff retry."""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers)

            if response.status_code < 500:
                # 2xx, 4xx - don't retry
                return response

            # 5xx - retry with backoff
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                print(f"Server error, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                return response

        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                print(f"Request failed, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise

    return response
```

---

**3. Handle Specific Error Cases**

```typescript
async function createPage(title: string, token: string) {
  try {
    const response = await fetch('/api/v1/ocean/pages', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ title })
    });

    const data = await response.json();

    switch (response.status) {
      case 201:
        // Success
        return data;

      case 400:
        // Validation error
        throw new ValidationError(data.detail);

      case 401:
        // Token expired - refresh and retry
        const newToken = await refreshToken();
        return createPage(title, newToken);

      case 404:
        // Not found
        throw new NotFoundError(data.detail);

      case 500:
        // Server error - retry once
        await new Promise(resolve => setTimeout(resolve, 1000));
        return createPage(title, token);

      default:
        throw new Error(`Unexpected error: ${data.detail}`);
    }
  } catch (error) {
    console.error('Failed to create page:', error);
    throw error;
  }
}
```

---

**4. User-Friendly Error Messages**

```python
def get_user_friendly_error(status_code: int, detail: str) -> str:
    """Convert API errors to user-friendly messages."""
    if status_code == 401:
        return "Your session has expired. Please log in again."
    elif status_code == 404:
        return "The requested item could not be found."
    elif status_code == 400:
        if "circular reference" in detail.lower():
            return "This action would create a circular link. Please remove existing links first."
        elif "already exists" in detail.lower():
            return "An item with this name already exists. Please use a different name."
        else:
            return f"Invalid request: {detail}"
    elif status_code >= 500:
        return "We're experiencing technical difficulties. Please try again in a moment."
    else:
        return f"An error occurred: {detail}"

# Usage
try:
    response = requests.post(...)
    response.raise_for_status()
except requests.exceptions.HTTPError as e:
    user_message = get_user_friendly_error(
        e.response.status_code,
        e.response.json().get("detail", "Unknown error")
    )
    show_error_to_user(user_message)
```

---

**5. Logging and Monitoring**

```typescript
// Log all API errors for debugging
function logApiError(error: any, context: any) {
  console.error('API Error:', {
    timestamp: new Date().toISOString(),
    status: error.status,
    message: error.message,
    endpoint: context.endpoint,
    method: context.method,
    userId: context.userId,
    organizationId: context.organizationId
  });

  // Send to error tracking service (e.g., Sentry)
  if (typeof Sentry !== 'undefined') {
    Sentry.captureException(error, { extra: context });
  }
}

// Usage
try {
  const pages = await getPages(token);
} catch (error) {
  logApiError(error, {
    endpoint: '/api/v1/ocean/pages',
    method: 'GET',
    userId: currentUser.id,
    organizationId: currentOrg.id
  });

  throw error; // Re-throw for UI handling
}
```

---

## Additional Resources

- **API Reference:** [API_REFERENCE.md](./API_REFERENCE.md)
- **Authentication Guide:** [AUTHENTICATION.md](./AUTHENTICATION.md)
- **Code Examples:** [examples/](./examples/)
- **Interactive API Docs:** http://localhost:8000/docs (FastAPI Swagger UI)

---

## Support

- **GitHub Issues:** [ocean-backend/issues](https://github.com/ainative/ocean-backend/issues)
- **Email:** support@ainative.studio
- **Security Issues:** security@ainative.studio

---

**Last Updated:** 2025-12-24
**API Version:** 0.1.0
