# Ocean API Authentication Guide

**Version:** 0.1.0
**Last Updated:** 2025-12-24

---

## Table of Contents

1. [Overview](#overview)
2. [JWT Token Authentication](#jwt-token-authentication)
3. [Multi-Tenant Security Model](#multi-tenant-security-model)
4. [Authentication Flow](#authentication-flow)
5. [Token Structure](#token-structure)
6. [Making Authenticated Requests](#making-authenticated-requests)
7. [Token Expiration and Refresh](#token-expiration-and-refresh)
8. [Security Best Practices](#security-best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Overview

Ocean API uses **JWT (JSON Web Token) Bearer authentication** to secure all endpoints. The authentication system is designed to:

- Verify user identity on every request
- Enforce multi-tenant isolation at the organization level
- Prevent cross-organization data access
- Support token expiration and refresh mechanisms

**Key Points:**

- All endpoints (except `/health` and `/`) require authentication
- JWT tokens are issued by the parent authentication service
- Tokens must include `user_id`, `organization_id`, and expiration
- No API keys - all auth is token-based

---

## JWT Token Authentication

### What is JWT?

JSON Web Token (JWT) is an industry-standard method for securely transmitting information between parties as a JSON object. The token is:

- **Self-contained**: Contains all user information needed for authorization
- **Signed**: Cryptographically signed to prevent tampering
- **Stateless**: Server doesn't need to store session data

### JWT Structure

A JWT token consists of three parts separated by dots (`.`):

```
header.payload.signature
```

**Example Token:**

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoidGVzdC11c2VyLTEyMyIsIm9yZ2FuaXphdGlvbl9pZCI6InRlc3Qtb3JnLTQ1NiIsImV4cCI6MTczNTEyMzQ1Nn0.signature_here
```

**Decoded Payload:**

```json
{
  "user_id": "test-user-123",
  "organization_id": "test-org-456",
  "exp": 1735123456
}
```

### Required Claims

Every JWT token used with Ocean API **must** include:

| Claim | Type | Description | Example |
|-------|------|-------------|---------|
| `user_id` | string | Unique user identifier | `"test-user-123"` |
| `organization_id` | string | Organization identifier for multi-tenancy | `"test-org-456"` |
| `exp` | integer | Expiration timestamp (Unix epoch) | `1735123456` |

**Optional Claims:**

- `iat` (issued at): Token creation timestamp
- `iss` (issuer): Token issuer identifier
- `sub` (subject): User subject (often same as user_id)

---

## Multi-Tenant Security Model

Ocean API implements **strict multi-tenant isolation** to ensure organizations can only access their own data.

### How It Works

1. **JWT Token Extraction**:
   - Every request includes a JWT token in the Authorization header
   - Ocean extracts `organization_id` from the token payload

2. **Automatic Filtering**:
   - All database queries are automatically filtered by `organization_id`
   - Users can only read/write resources belonging to their organization

3. **Cross-Organization Protection**:
   - Attempting to access another organization's resources returns `404 Not Found`
   - No error message reveals whether the resource exists in another organization

### Example Isolation

**Scenario:** User in Organization A tries to access a page from Organization B.

```bash
# User token: organization_id = "org-a"
curl -X GET http://localhost:8000/api/v1/ocean/pages/page-from-org-b \
  -H "Authorization: Bearer <ORG_A_TOKEN>"
```

**Response:** `404 Not Found`

```json
{
  "detail": "Page page-from-org-b not found or does not belong to organization"
}
```

**Security Note:** The error message doesn't reveal whether the page exists in another organization.

### Database Schema

All resources include an `organization_id` field:

**Pages Table:**

```json
{
  "page_id": "page_123",
  "organization_id": "org-a",  // ← Multi-tenant key
  "user_id": "user-456",
  "title": "Product Roadmap",
  ...
}
```

**Blocks Table:**

```json
{
  "block_id": "block_789",
  "organization_id": "org-a",  // ← Multi-tenant key
  "page_id": "page_123",
  ...
}
```

**Tags, Links, etc.:** All resources follow the same pattern.

---

## Authentication Flow

### 1. Obtaining a JWT Token

**Ocean API does NOT issue JWT tokens.** Tokens are obtained from the parent authentication service.

**Typical Flow:**

```
┌─────────┐          ┌──────────────┐          ┌──────────────┐
│ Client  │          │ Auth Service │          │  Ocean API   │
└────┬────┘          └──────┬───────┘          └──────┬───────┘
     │                      │                         │
     │ 1. POST /login       │                         │
     │─────────────────────>│                         │
     │  {email, password}   │                         │
     │                      │                         │
     │ 2. JWT Token         │                         │
     │<─────────────────────│                         │
     │  {token: "eyJ..."}   │                         │
     │                      │                         │
     │ 3. GET /pages                                  │
     │──────────────────────────────────────────────> │
     │  Authorization: Bearer eyJ...                  │
     │                      │                         │
     │                      │ 4. Validate Token       │
     │                      │ 5. Extract org_id       │
     │                      │                         │
     │ 6. Pages Response                              │
     │<────────────────────────────────────────────── │
     │  [{page_id, title, ...}]                       │
     │                      │                         │
```

### 2. Request Authentication Process

When Ocean receives a request:

1. **Extract Token**: Get token from `Authorization: Bearer <token>` header
2. **Verify Signature**: Validate token signature using `SECRET_KEY`
3. **Check Expiration**: Verify token hasn't expired (`exp` claim)
4. **Extract Claims**: Get `user_id` and `organization_id` from payload
5. **Inject Dependencies**: Pass user info to endpoint handler
6. **Filter Resources**: Apply `organization_id` filter to all queries

### 3. Dependency Injection

Ocean uses FastAPI's dependency injection to authenticate requests:

**Code Example (Internal):**

```python
from app.api.deps import get_current_user

@router.get("/pages")
async def list_pages(
    current_user: Dict[str, Any] = Depends(get_current_user),
    service: OceanService = Depends(get_ocean_service)
):
    # current_user contains:
    # {
    #   "user_id": "test-user-123",
    #   "organization_id": "test-org-456"
    # }

    pages = await service.get_pages(
        org_id=current_user["organization_id"]
    )
    ...
```

**Result:** All resources are automatically scoped to the user's organization.

---

## Token Structure

### Token Configuration

Ocean API uses the following JWT configuration:

**Algorithm:** `HS256` (HMAC with SHA-256)
**Secret Key:** Configured via `SECRET_KEY` environment variable
**Expiration:** Configurable (default: 30 minutes)

### Environment Variables

```bash
# Required for JWT validation
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

**Security:** `SECRET_KEY` must be:
- At least 32 characters long
- Cryptographically random
- Never committed to version control
- Same across all services (Auth + Ocean)

### Example Token Generation (Python)

**Note:** This is for reference only. Tokens are issued by the auth service.

```python
import jwt
from datetime import datetime, timedelta

SECRET_KEY = "your-secret-key-here"
ALGORITHM = "HS256"

payload = {
    "user_id": "test-user-123",
    "organization_id": "test-org-456",
    "exp": datetime.utcnow() + timedelta(minutes=30)
}

token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
print(token)
# Output: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Making Authenticated Requests

### Authorization Header Format

All requests must include the JWT token in the `Authorization` header:

```http
Authorization: Bearer <JWT_TOKEN>
```

**Format:**
- **Scheme:** `Bearer` (capitalized)
- **Token:** Full JWT token string (no quotes)

### Example Requests

**cURL:**

```bash
curl -X GET http://localhost:8000/api/v1/ocean/pages \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Python (requests):**

```python
import requests

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
headers = {
    "Authorization": f"Bearer {token}"
}

response = requests.get(
    "http://localhost:8000/api/v1/ocean/pages",
    headers=headers
)

print(response.json())
```

**JavaScript (fetch):**

```javascript
const token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...";

fetch("http://localhost:8000/api/v1/ocean/pages", {
  headers: {
    "Authorization": `Bearer ${token}`
  }
})
  .then(response => response.json())
  .then(data => console.log(data));
```

**TypeScript (axios):**

```typescript
import axios from 'axios';

const token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...";

const response = await axios.get(
  "http://localhost:8000/api/v1/ocean/pages",
  {
    headers: {
      Authorization: `Bearer ${token}`
    }
  }
);

console.log(response.data);
```

---

## Token Expiration and Refresh

### Token Expiration

JWT tokens expire after a configured duration (default: 30 minutes).

**Expired Token Response:**

```json
{
  "detail": "Token has expired"
}
```

**HTTP Status:** `401 Unauthorized`

### Token Refresh Flow

When a token expires, the client must obtain a new token from the auth service.

**Recommended Flow:**

```
┌─────────┐          ┌──────────────┐          ┌──────────────┐
│ Client  │          │ Auth Service │          │  Ocean API   │
└────┬────┘          └──────┬───────┘          └──────┬───────┘
     │                      │                         │
     │ 1. GET /pages                                  │
     │──────────────────────────────────────────────> │
     │  Authorization: Bearer <EXPIRED_TOKEN>         │
     │                      │                         │
     │ 2. 401 Unauthorized                            │
     │<────────────────────────────────────────────── │
     │  {"detail": "Token has expired"}               │
     │                      │                         │
     │ 3. POST /refresh     │                         │
     │─────────────────────>│                         │
     │  {refresh_token}     │                         │
     │                      │                         │
     │ 4. New Token         │                         │
     │<─────────────────────│                         │
     │  {token: "eyJ..."}   │                         │
     │                      │                         │
     │ 5. GET /pages (retry)                          │
     │──────────────────────────────────────────────> │
     │  Authorization: Bearer <NEW_TOKEN>             │
     │                      │                         │
     │ 6. Success Response                            │
     │<────────────────────────────────────────────── │
     │                      │                         │
```

### Automatic Token Refresh (Client-Side)

**Python Example:**

```python
import requests
from typing import Dict, Any

class OceanClient:
    def __init__(self, base_url: str, auth_url: str):
        self.base_url = base_url
        self.auth_url = auth_url
        self.token = None
        self.refresh_token = None

    def login(self, email: str, password: str):
        """Get initial token from auth service."""
        response = requests.post(
            f"{self.auth_url}/login",
            json={"email": email, "password": password}
        )
        data = response.json()
        self.token = data["access_token"]
        self.refresh_token = data["refresh_token"]

    def refresh(self):
        """Refresh expired token."""
        response = requests.post(
            f"{self.auth_url}/refresh",
            json={"refresh_token": self.refresh_token}
        )
        data = response.json()
        self.token = data["access_token"]

    def request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make authenticated request with automatic token refresh."""
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {self.token}"
        kwargs["headers"] = headers

        response = requests.request(
            method,
            f"{self.base_url}{endpoint}",
            **kwargs
        )

        # If token expired, refresh and retry
        if response.status_code == 401:
            self.refresh()
            headers["Authorization"] = f"Bearer {self.token}"
            response = requests.request(
                method,
                f"{self.base_url}{endpoint}",
                **kwargs
            )

        return response.json()

# Usage
client = OceanClient(
    base_url="http://localhost:8000/api/v1/ocean",
    auth_url="http://localhost:8000/api/v1/auth"
)

client.login("user@example.com", "password123")

# Automatic token refresh on expiration
pages = client.request("GET", "/pages")
```

---

## Security Best Practices

### 1. Token Storage

**Client-Side Storage:**

| Storage Method | Security Level | Use Case |
|----------------|----------------|----------|
| **Memory (variable)** | High | Single-page apps (SPA) - lost on refresh |
| **SessionStorage** | Medium | Per-tab storage, cleared on tab close |
| **LocalStorage** | Low | Persistent storage, vulnerable to XSS |
| **HttpOnly Cookie** | Highest | Server-set cookie, not accessible via JS |

**Recommendations:**

- **Web Apps:** Use memory + sessionStorage for access token, HttpOnly cookie for refresh token
- **Mobile Apps:** Use secure storage (Keychain on iOS, Keystore on Android)
- **Server-to-Server:** Use environment variables, never hardcode tokens

**Never:**
- Store tokens in URL parameters
- Log tokens to console or files
- Commit tokens to version control

### 2. HTTPS Required

**Always use HTTPS in production** to prevent token interception:

```
✅ https://ocean.ainative.studio/api/v1/ocean/pages
❌ http://ocean.ainative.studio/api/v1/ocean/pages
```

**Why:**
- HTTP transmits tokens in plaintext
- Man-in-the-middle attacks can steal tokens
- HTTPS encrypts all communication

### 3. Token Expiration

**Use short-lived access tokens:**

- **Access Token:** 15-30 minutes (short)
- **Refresh Token:** 7-30 days (long)

**Benefits:**
- Limits damage if token is compromised
- Forces regular re-authentication
- Refresh tokens allow extending sessions without re-login

### 4. CORS Configuration

Ocean API enforces CORS (Cross-Origin Resource Sharing) to prevent unauthorized domains from accessing the API.

**Allowed Origins (Development):**

```python
BACKEND_CORS_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8000"
]
```

**Production:**

```python
BACKEND_CORS_ORIGINS = [
    "https://ocean.ainative.studio",
    "https://app.ainative.studio"
]
```

**Security:** Only whitelist trusted domains.

### 5. Rate Limiting

**TODO (Issue #18):** Rate limiting will be implemented to prevent:
- Brute force attacks on authentication
- API abuse and DoS attacks
- Excessive token refresh attempts

**Planned Limits:**

- 1000 requests/hour per organization
- 10 failed auth attempts per IP per hour

---

## Troubleshooting

### Common Authentication Errors

#### 1. `401 Unauthorized: Not authenticated`

**Cause:** Missing or malformed Authorization header

**Solutions:**

- Verify header format: `Authorization: Bearer <token>`
- Check for typos: `Bearer` (not `bearer` or `Token`)
- Ensure token is included in every request

**Example Fix:**

```bash
# ❌ Wrong
curl -X GET http://localhost:8000/api/v1/ocean/pages

# ✅ Correct
curl -X GET http://localhost:8000/api/v1/ocean/pages \
  -H "Authorization: Bearer eyJhbGci..."
```

---

#### 2. `401 Unauthorized: Token has expired`

**Cause:** JWT token has passed its expiration time (`exp` claim)

**Solutions:**

- Request a new token from auth service
- Implement automatic token refresh (see examples above)
- Increase token expiration time (if appropriate)

**Debug:**

```python
import jwt

token = "your_token_here"
decoded = jwt.decode(token, options={"verify_signature": False})
print(f"Expires at: {decoded['exp']}")  # Unix timestamp
```

---

#### 3. `401 Unauthorized: Invalid token signature`

**Cause:** Token was signed with a different `SECRET_KEY`

**Solutions:**

- Verify `SECRET_KEY` matches between auth service and Ocean API
- Ensure token was issued by trusted auth service
- Check for token tampering (manual editing)

**Debug:**

```bash
# Compare SECRET_KEY across services
# Auth service .env
SECRET_KEY=abc123...

# Ocean API .env
SECRET_KEY=abc123...  # ← Must match
```

---

#### 4. `404 Not Found: Page not found or does not belong to organization`

**Cause:** Resource belongs to a different organization

**Explanation:**
- Token contains `organization_id = "org-a"`
- Requested resource belongs to `organization_id = "org-b"`
- Multi-tenant isolation blocks access

**Solutions:**

- Verify you're logged in with the correct organization
- Request a token for the correct organization
- Check resource ownership in database

---

#### 5. `422 Validation Error: Field required`

**Cause:** JWT token missing required claims (`user_id` or `organization_id`)

**Solutions:**

- Ensure auth service includes all required claims in token
- Verify token payload structure

**Debug:**

```python
import jwt

token = "your_token_here"
decoded = jwt.decode(token, options={"verify_signature": False})
print(decoded)

# Expected output:
# {
#   "user_id": "test-user-123",
#   "organization_id": "test-org-456",
#   "exp": 1735123456
# }
```

---

### Debug Mode

**Enable debug logging** to troubleshoot authentication issues:

```bash
# .env
DEBUG=True
```

**Debug Output:**

```
INFO:     JWT token received: eyJhbGci...
DEBUG:    Decoded payload: {'user_id': 'test-user-123', 'organization_id': 'test-org-456', ...}
INFO:     User authenticated: test-user-123
DEBUG:    Organization filter applied: test-org-456
```

**Warning:** Never enable debug mode in production (exposes sensitive data).

---

### Testing Authentication

**Test Token Generation:**

```python
# tests/test_auth.py
import jwt
from datetime import datetime, timedelta

SECRET_KEY = "test-secret-key"
ALGORITHM = "HS256"

def create_test_token(user_id: str, org_id: str) -> str:
    """Create test JWT token for integration tests."""
    payload = {
        "user_id": user_id,
        "organization_id": org_id,
        "exp": datetime.utcnow() + timedelta(hours=1)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# Usage in tests
token = create_test_token("test-user-123", "test-org-456")

response = client.get(
    "/api/v1/ocean/pages",
    headers={"Authorization": f"Bearer {token}"}
)

assert response.status_code == 200
```

---

## Additional Resources

- **API Reference:** [API_REFERENCE.md](./API_REFERENCE.md)
- **Error Codes:** [ERROR_CODES.md](./ERROR_CODES.md)
- **Code Examples:** [examples/](./examples/)
- **JWT Specification:** https://jwt.io/introduction
- **FastAPI Security:** https://fastapi.tiangolo.com/tutorial/security/

---

## Support

- **GitHub Issues:** [ocean-backend/issues](https://github.com/ainative/ocean-backend/issues)
- **Email:** support@ainative.studio
- **Security Issues:** security@ainative.studio (for vulnerabilities)

---

**Last Updated:** 2025-12-24
**API Version:** 0.1.0
