# Ocean Backend Authentication Design

## Architecture Overview

**Ocean backend uses AINative core authentication service** for user authentication and authorization.

```
┌─────────────┐      ┌──────────────────┐      ┌─────────────┐
│   Client    │─────>│  AINative Core   │      │   Ocean     │
│             │      │  Auth Service    │      │   Backend   │
│             │<─────│  /v1/auth/login  │      │             │
│             │      └──────────────────┘      │             │
│             │              │                 │             │
│             │              │ JWT Token       │             │
│             │              v                 │             │
│             │      ┌──────────────────────────────────────┐│
│             │─────>│  Authorization: Bearer <token>       ││
│             │      │  /api/v1/ocean/pages                 ││
│             │<─────│  Returns: Ocean data                 ││
│             │      └──────────────────────────────────────┘│
└─────────────┘                                │             │
                                               └─────────────┘
```

---

## Current Implementation Status

### ✅ AINative Core Auth (Production)
- **API**: `https://api.ainative.studio/v1/auth/`
- **Status**: Live and operational
- **Endpoints**: login, register, refresh, me, verify-email, forgot-password, reset-password

### ⚠️ Ocean Backend Auth (Mock - Needs Integration)
- **File**: `/Users/aideveloper/ocean-backend/app/api/deps.py:14-44`
- **Status**: Mock authentication (returns test user)
- **TODO**: Integrate with AINative core auth service

```python
# Current (Mock):
async def get_current_user(authorization: str = Header(None)):
    """
    For MVP: Returns test user for development.
    TODO: Integrate with AINative core auth service for production.
    """
    return {
        "user_id": "test-user-123",
        "organization_id": "test-org-456",
        "email": "test@example.com",
        "role": "user"
    }
```

---

## Authentication Flow

### 1. Login to AINative Core

**Endpoint**: `POST https://api.ainative.studio/v1/auth/login`

**Request Format**: OAuth2 form-encoded (NOT JSON)

```bash
curl -X POST "https://api.ainative.studio/v1/auth/login" \
  -d "username=admin@ainative.studio" \
  -d "password=Admin2025!Secure"
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Token Contents** (JWT payload):
```json
{
  "sub": "a9b717be-f449-43c6-abb4-18a1a6a0c70e",
  "email": "admin@ainative.studio",
  "role": "ADMIN",
  "exp": 1766803059
}
```

---

### 2. Use Token with Ocean Backend

**All Ocean endpoints require Authorization header**:

```bash
curl -H "Authorization: Bearer <access_token>" \
  "https://ocean-backend-production-056c.up.railway.app/api/v1/ocean/pages"
```

**Example Response**:
```json
{
  "pages": [],
  "total": 0,
  "limit": 50,
  "offset": 0
}
```

---

## Available Authentication Endpoints

### AINative Core Auth API

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| `/v1/auth/login` | POST | User login | No |
| `/v1/auth/register` | POST | User registration | No |
| `/v1/auth/refresh` | POST | Refresh access token | Yes (refresh token) |
| `/v1/auth/me` | GET | Get current user | Yes (access token) |
| `/v1/auth/verify-email` | POST | Email verification | No |
| `/v1/auth/forgot-password` | POST | Password reset request | No |
| `/v1/auth/reset-password` | POST | Password reset | No |
| `/v1/auth/logout` | POST | Logout (blacklist token) | Yes |

---

## Credentials (from .env files)

### Admin Account
```bash
Username: admin@ainative.studio
Password: Admin2025!Secure
```

### Test Token (expires 2025-12-27)
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhOWI3MTdiZS1mNDQ5LTQzYzYtYWJiNC0xOGExYTZhMGM3MGUiLCJlbWFpbCI6ImFkbWluQGFpbmF0aXZlLnN0dWRpbyIsInJvbGUiOiJBRE1JTiIsImV4cCI6MTc2NjgwMzA1OX0._RsR_NAaJsinS9f5HC05OR5iq5YQ-HeHiWMB_8lCYvY
```

---

## Ocean API Endpoints (Authenticated)

All endpoints require `Authorization: Bearer <token>` header:

### Pages
- `GET /api/v1/ocean/pages` - List all pages
- `POST /api/v1/ocean/pages` - Create new page
- `GET /api/v1/ocean/pages/{page_id}` - Get page by ID
- `PUT /api/v1/ocean/pages/{page_id}` - Update page
- `DELETE /api/v1/ocean/pages/{page_id}` - Delete page
- `POST /api/v1/ocean/pages/{page_id}/move` - Move page

### Blocks
- `GET /api/v1/ocean/blocks` - List blocks
- `POST /api/v1/ocean/blocks` - Create block
- `GET /api/v1/ocean/blocks/{block_id}` - Get block
- `PUT /api/v1/ocean/blocks/{block_id}` - Update block
- `DELETE /api/v1/ocean/blocks/{block_id}` - Delete block
- `POST /api/v1/ocean/blocks/{block_id}/move` - Move block
- `POST /api/v1/ocean/blocks/{block_id}/convert` - Convert block type

### Search
- `POST /api/v1/ocean/search` - Semantic search across pages/blocks

### Links
- `POST /api/v1/ocean/links` - Create block link
- `GET /api/v1/ocean/links` - Get block links
- `DELETE /api/v1/ocean/links/{link_id}` - Delete link

### Tags
- `POST /api/v1/ocean/tags` - Create tag
- `GET /api/v1/ocean/tags` - List tags
- `PUT /api/v1/ocean/tags/{tag_id}` - Update tag
- `DELETE /api/v1/ocean/tags/{tag_id}` - Delete tag

---

## Testing Authentication

### 1. Login and Get Token
```bash
TOKEN=$(curl -s -X POST "https://api.ainative.studio/v1/auth/login" \
  -d "username=admin@ainative.studio" \
  -d "password=Admin2025!Secure" \
  | jq -r .access_token)
```

### 2. Create a Page
```bash
curl -X POST "https://ocean-backend-production-056c.up.railway.app/api/v1/ocean/pages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Page",
    "icon": "📄",
    "cover_image": null,
    "parent_page_id": null
  }'
```

### 3. List Pages
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "https://ocean-backend-production-056c.up.railway.app/api/v1/ocean/pages"
```

---

## Required Integration Work

### TODO: Replace Mock Auth in Ocean Backend

**File**: `/Users/aideveloper/ocean-backend/app/api/deps.py`

**Current Implementation** (lines 14-44):
- Returns mock test user
- Accepts any Authorization header
- No JWT validation

**Required Changes**:

1. **Validate JWT token** with AINative core auth service
2. **Extract user claims** from validated token (user_id, organization_id, email, role)
3. **Check token blacklist** (for logout functionality)
4. **Handle token expiration** and return 401 errors

**Implementation Options**:

#### Option A: Call AINative Auth Service
```python
async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.replace("Bearer ", "")

    # Call AINative core auth /v1/auth/validate endpoint
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{AINATIVE_API_URL}/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid token")

        user = response.json()
        return {
            "user_id": user["id"],
            "organization_id": user["organization_id"],
            "email": user["email"],
            "role": user["role"]
        }
```

#### Option B: Local JWT Validation (Faster)
```python
from jose import jwt, JWTError
from app.config import settings

async def get_current_user(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")

    token = authorization.replace("Bearer ", "")

    try:
        # Decode JWT using shared secret
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        user_id = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role")

        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        # TODO: Get organization_id from user database
        return {
            "user_id": user_id,
            "organization_id": "TODO",  # Query from database
            "email": email,
            "role": role
        }

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
```

---

## Security Considerations

1. **Token Expiration**: Access tokens expire in 1800 seconds (30 minutes)
2. **Refresh Tokens**: Use `/v1/auth/refresh` to get new access tokens
3. **Token Blacklisting**: Logout invalidates tokens via blacklist
4. **Multi-tenant Isolation**: All Ocean operations filter by organization_id
5. **CORS**: Ocean backend allows requests from configured origins only

---

## Environment Variables Required

### Ocean Backend (.env)
```bash
# Already configured:
ZERODB_API_URL=https://api.ainative.studio
ZERODB_PROJECT_ID=b832ac6e-bd16-4efa-9d55-209ebf872db9
ZERODB_API_KEY=9khD3l6lpI9O7AwVOkxdl5ZOQP0upsu0vIsiQbLCUGk
SECRET_KEY=kLPiP0bzgKJ0CnNYVt1wq3qxbs2QgDeF2XwyUnxBEOM
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Need to add for auth integration:
AINATIVE_API_URL=https://api.ainative.studio
```

### Railway Variables
Same as above - already configured in Railway dashboard.

---

## Next Steps

1. **Create GitHub Issue** for Ocean auth integration
2. **Implement JWT validation** in `app/api/deps.py`
3. **Add organization_id lookup** from user database
4. **Test authentication flow** end-to-end
5. **Update frontend** to use proper auth flow:
   - Login via AINative auth
   - Store access token
   - Send token with Ocean API requests
   - Handle token refresh

---

## Status Summary

✅ **Working**:
- AINative core auth API (production)
- Ocean backend API (production)
- JWT token generation
- Token-based API access (via mock auth)

⚠️ **Needs Implementation**:
- Ocean backend JWT validation
- Organization ID extraction from token
- Token blacklist checking
- Proper 401/403 error handling

🎯 **Ready For**:
- Frontend integration
- User testing
- Production deployment (after auth integration)

---

**Generated**: 2025-12-27
**Status**: Authentication design documented, integration pending
