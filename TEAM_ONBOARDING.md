# 🌊 Ocean - Team Onboarding Guide

> **Ocean** is a Notion-like workspace built on ZeroDB serverless infrastructure with AI-powered semantic search. Backend is live in production on Railway.

---

## 📊 Project Status

| Component | Status | URL |
|-----------|--------|-----|
| **Backend API** | ✅ **LIVE** | https://ocean-backend-production-056c.up.railway.app |
| **Health Check** | ✅ Passing | https://ocean-backend-production-056c.up.railway.app/health |
| **API Docs** | ✅ Available | https://ocean-backend-production-056c.up.railway.app/docs |
| **Frontend** | 🚧 Not started | TBD |
| **ZeroDB Integration** | ✅ Configured | Project ID: `b832ac6e-bd16-4efa-9d55-209ebf872db9` |
| **Authentication** | ⚠️ Mock (needs integration) | Uses AINative core auth |

---

## 🎯 What is Ocean?

**Ocean** is a collaborative workspace platform similar to Notion, featuring:

- 📝 **Pages** - Hierarchical document structure with icons and cover images
- 🧱 **Blocks** - 6 block types (text, heading, list, code, image, embed)
- 🔍 **Semantic Search** - AI-powered search using embeddings (BAAI/bge-base-en-v1.5, 768 dimensions)
- 🔗 **Block Linking** - Create relationships between blocks
- 🏷️ **Tags** - Organize content with tags
- 🏢 **Multi-tenant** - Organization-level data isolation

---

## 🏗️ Architecture

```
┌─────────────┐
│   Client    │
│  (Frontend) │
└──────┬──────┘
       │
       │ 1. Login to get JWT token
       ↓
┌──────────────────────┐
│  AINative Core Auth  │
│ api.ainative.studio  │
│   /v1/auth/login     │
└──────────────────────┘
       │
       │ 2. JWT Token
       ↓
┌──────────────────────┐
│   Ocean Backend      │
│   Railway (Python)   │
│   FastAPI + ZeroDB   │
└──────────────────────┘
       │
       │ 3. Data operations
       ↓
┌──────────────────────┐
│      ZeroDB          │
│  Serverless NoSQL    │
│  + Vector Search     │
└──────────────────────┘
```

**Tech Stack:**
- **Backend**: Python 3.11+ • FastAPI • Uvicorn
- **Database**: ZeroDB (serverless NoSQL + vector search)
- **Embeddings**: BAAI/bge-base-en-v1.5 (768 dimensions)
- **Auth**: AINative core auth service (JWT)
- **Deployment**: Railway (EU West region)

---

## 🚀 For Frontend Developers

### Quick Start

**Base URL (Production):**
```
https://ocean-backend-production-056c.up.railway.app
```

### 1️⃣ Authentication Flow

#### Step 1: Login to get access token

```javascript
// POST to AINative core auth
const response = await fetch('https://api.ainative.studio/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({
    username: 'admin@ainative.studio',
    password: 'Admin2025!Secure'
  })
});

const { access_token, expires_in } = await response.json();
// Store access_token in localStorage or state management
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### Step 2: Use token with Ocean API

```javascript
// All Ocean API calls require Authorization header
const pages = await fetch('https://ocean-backend-production-056c.up.railway.app/api/v1/ocean/pages', {
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  }
});

const data = await pages.json();
```

### 2️⃣ API Endpoints

**Base:** `/api/v1/ocean`

#### Pages

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/pages` | List all pages (with pagination, filtering) |
| `POST` | `/pages` | Create new page |
| `GET` | `/pages/{page_id}` | Get page by ID |
| `PUT` | `/pages/{page_id}` | Update page |
| `DELETE` | `/pages/{page_id}` | Delete page (soft delete) |
| `POST` | `/pages/{page_id}/move` | Move page to different parent |

**Example: Create Page**
```javascript
const newPage = await fetch('https://ocean-backend-production-056c.up.railway.app/api/v1/ocean/pages', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    title: 'My First Page',
    icon: '📄',
    cover_image: null,
    parent_page_id: null
  })
});
```

#### Blocks

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/blocks` | List blocks (filter by page_id) |
| `POST` | `/blocks` | Create new block |
| `GET` | `/blocks/{block_id}` | Get block by ID |
| `PUT` | `/blocks/{block_id}` | Update block |
| `DELETE` | `/blocks/{block_id}` | Delete block |
| `POST` | `/blocks/{block_id}/move` | Move block to different position/page |
| `POST` | `/blocks/{block_id}/convert` | Convert block type |

**Block Types:** `text`, `heading`, `bullet_list`, `numbered_list`, `code`, `image`, `embed`

**Example: Create Block**
```javascript
const newBlock = await fetch('https://ocean-backend-production-056c.up.railway.app/api/v1/ocean/blocks', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    page_id: 'page-uuid-here',
    block_type: 'text',
    content: 'Hello world!',
    position: 0
  })
});
```

#### Search

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/search` | Semantic search across pages and blocks |

**Example: Search**
```javascript
const results = await fetch('https://ocean-backend-production-056c.up.railway.app/api/v1/ocean/search', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${access_token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: 'machine learning',
    limit: 10,
    include_blocks: true
  })
});
```

#### Links & Tags

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/links` | Create link between blocks |
| `GET` | `/links` | Get links (filter by source/target) |
| `DELETE` | `/links/{link_id}` | Delete link |
| `POST` | `/tags` | Create tag |
| `GET` | `/tags` | List all tags |
| `PUT` | `/tags/{tag_id}` | Update tag |
| `DELETE` | `/tags/{tag_id}` | Delete tag |

### 3️⃣ API Documentation

**Interactive Swagger UI:**
https://ocean-backend-production-056c.up.railway.app/docs

**Explore all endpoints, request/response schemas, and test API calls directly in browser.**

### 4️⃣ Error Handling

All endpoints return standard HTTP status codes:

| Code | Meaning |
|------|---------|
| `200` | Success |
| `201` | Created |
| `204` | No Content (delete successful) |
| `400` | Bad Request (validation error) |
| `401` | Unauthorized (invalid/missing token) |
| `404` | Not Found |
| `500` | Internal Server Error |

**Error Response Format:**
```json
{
  "detail": "Error message here",
  "status_code": 400
}
```

### 5️⃣ CORS Configuration

Ocean backend allows requests from:
- `https://ocean.ainative.studio` (production frontend)
- `https://www.ainative.studio`
- `http://localhost:3000` (local development)
- `http://localhost:5173` (Vite default)

### 6️⃣ Recommended Frontend Libraries

**React/Next.js:**
- `axios` or `fetch` for API calls
- `react-query` or `swr` for data fetching and caching
- `zustand` or `redux` for state management
- `react-hook-form` + `zod` for forms

**Authentication:**
- Store JWT in `localStorage` or `sessionStorage`
- Implement token refresh before expiration (30 min)
- Handle 401 errors by redirecting to login

---

## 🛠️ For Backend Developers

### Repository & Setup

**Repository:** `https://github.com/AINative-Studio/ocean-backend`

```bash
# Clone repository
git clone https://github.com/AINative-Studio/ocean-backend.git
cd ocean-backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your credentials
```

### Environment Variables

Create `.env` file with these variables:

```bash
# ZeroDB Configuration (REQUIRED)
ZERODB_API_URL=https://api.ainative.studio
ZERODB_PROJECT_ID=b832ac6e-bd16-4efa-9d55-209ebf872db9
ZERODB_API_KEY=9khD3l6lpI9O7AwVOkxdl5ZOQP0upsu0vIsiQbLCUGk

# Ocean Configuration
OCEAN_EMBEDDINGS_MODEL=BAAI/bge-base-en-v1.5
OCEAN_EMBEDDINGS_DIMENSIONS=768

# API Settings
API_V1_STR=/api/v1
PROJECT_NAME=Ocean Backend
DEBUG=true  # Set to false in production

# Security
SECRET_KEY=kLPiP0bzgKJ0CnNYVt1wq3qxbs2QgDeF2XwyUnxBEOM
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS (add your frontend URL)
BACKEND_CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
```

### Running Locally

```bash
# Start development server
uvicorn app.main:app --reload --port 8000

# Or use the FastAPI CLI
fastapi dev app/main.py
```

**Local API:** http://localhost:8000
**Docs:** http://localhost:8000/docs

### Project Structure

```
ocean-backend/
├── app/
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration settings
│   ├── api/
│   │   ├── deps.py          # FastAPI dependencies (auth, services)
│   │   └── v1/endpoints/    # API endpoints
│   │       ├── ocean_pages.py
│   │       ├── ocean_blocks.py
│   │       ├── ocean_search.py
│   │       ├── ocean_links.py
│   │       └── ocean_tags.py
│   ├── schemas/
│   │   └── ocean.py         # Pydantic schemas (request/response models)
│   ├── services/
│   │   └── ocean_service.py # Business logic (35 operations)
│   └── middleware/          # Custom middleware
├── tests/                   # Test suite
├── requirements.txt         # Python dependencies
├── railway.json            # Railway deployment config
└── .env                    # Environment variables (not committed)
```

### Key Files

**1. API Endpoints** (`app/api/v1/endpoints/ocean_pages.py`, etc.)
- FastAPI route handlers
- Request validation with Pydantic
- Dependency injection for auth and services

**2. Business Logic** (`app/services/ocean_service.py`)
- 35 Ocean operations
- ZeroDB REST API integration
- Embedding generation
- Error handling

**3. Schemas** (`app/schemas/ocean.py`)
- Pydantic models for request/response validation
- Type safety and auto-generated API docs

**4. Authentication** (`app/api/deps.py`)
- Currently: Mock authentication (returns test user)
- **TODO**: Integrate with AINative core auth service
- Extract user_id, organization_id from JWT token

### ZeroDB Integration

Ocean uses ZeroDB REST API (not MCP):

**Endpoints Used:**
- `POST /v1/projects/{id}/database/tables/{name}/rows` - Create row
- `POST /v1/projects/{id}/database/tables/{name}/query` - Query rows
- `PATCH /v1/projects/{id}/database/tables/{name}/rows/{row_id}` - Update row
- `DELETE /v1/projects/{id}/database/tables/{name}/rows/{row_id}` - Delete row

**Tables:**
- `ocean_pages` - Page documents
- `ocean_blocks` - Content blocks
- `ocean_block_links` - Block relationships
- `ocean_tags` - Tags
- `ocean_page_tags` - Page-tag associations

### Common Development Tasks

#### Add New Endpoint

1. Create endpoint in `app/api/v1/endpoints/ocean_*.py`
2. Add Pydantic schema in `app/schemas/ocean.py`
3. Add business logic in `app/services/ocean_service.py`
4. Register router in `app/main.py` if new file
5. Test locally
6. Commit and push (Railway auto-deploys)

#### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_ocean_pages.py

# Run with coverage
pytest --cov=app tests/
```

#### Database Migrations

ZeroDB is schemaless NoSQL - no migrations needed. Tables are created automatically on first use.

### Deployment (Railway)

**Production URL:** https://ocean-backend-production-056c.up.railway.app

**Auto-deployment:**
- Push to `main` branch triggers automatic deployment
- Build time: ~2-3 minutes
- Health check: `/health` endpoint

**View Logs:**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link project
cd ocean-backend
railway link

# View logs
railway logs
```

**Environment Variables:**
Set in Railway Dashboard → ocean-backend → Variables tab

---

## 🔐 Authentication Details

### Current State: Mock Authentication

**File:** `app/api/deps.py:14-44`

```python
async def get_current_user(authorization: str = Header(None)):
    """
    For MVP: Returns test user for development.
    TODO: Integrate with AINative core auth service for production.
    """
    # Currently returns mock user for any Authorization header
    return {
        "user_id": "test-user-123",
        "organization_id": "test-org-456",
        "email": "test@example.com",
        "role": "user"
    }
```

### Target State: AINative Core Auth Integration

**Required Changes:**

1. **Validate JWT token** from Authorization header
2. **Extract user claims** (user_id, email, organization_id, role)
3. **Check token expiration** and blacklist
4. **Return 401** for invalid/missing tokens

**Implementation Options:**

**Option A: Call AINative Auth Service**
```python
async with httpx.AsyncClient() as client:
    response = await client.get(
        "https://api.ainative.studio/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    # Use response to get user details
```

**Option B: Local JWT Validation** (faster)
```python
from jose import jwt, JWTError

payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
user_id = payload.get("sub")
# Extract other claims
```

### Test Credentials

**Admin Account:**
```
Username: admin@ainative.studio
Password: Admin2025!Secure
```

**Login Endpoint:**
```bash
curl -X POST "https://api.ainative.studio/v1/auth/login" \
  -d "username=admin@ainative.studio" \
  -d "password=Admin2025!Secure"
```

---

## 📋 Next Steps & Roadmap

### Immediate Tasks (Backend)

- [ ] **Implement JWT authentication** - Replace mock auth with real validation
- [ ] **Add organization_id lookup** - Query from user database
- [ ] **Create GitHub issue** for auth integration
- [ ] **Add rate limiting** per organization
- [ ] **Implement webhook support** for real-time updates

### Immediate Tasks (Frontend)

- [ ] **Set up React/Next.js project**
- [ ] **Implement authentication flow** (login, token storage, refresh)
- [ ] **Build page tree component** (hierarchical page navigation)
- [ ] **Build block editor** (6 block types with drag-and-drop)
- [ ] **Implement semantic search UI**
- [ ] **Add real-time collaboration** (websockets)

### Future Enhancements

- [ ] **File uploads** - Images, PDFs, attachments
- [ ] **Comments & mentions** - Collaborative features
- [ ] **Version history** - Track document changes
- [ ] **Templates** - Pre-built page templates
- [ ] **Export** - Markdown, PDF, HTML export
- [ ] **Public sharing** - Share pages with non-users
- [ ] **Mobile app** - iOS and Android clients

---

## 🆘 Getting Help

### Resources

- **API Documentation:** https://ocean-backend-production-056c.up.railway.app/docs
- **GitHub Repo:** https://github.com/AINative-Studio/ocean-backend
- **Health Check:** https://ocean-backend-production-056c.up.railway.app/health

### Team Contacts

- **Project Lead:** [Add name]
- **Backend Lead:** [Add name]
- **Frontend Lead:** [Add name]

### Development Chat

- **Slack/Discord:** [Add channel]

---

## 🎉 Quick Wins to Get Started

### For Frontend Devs:

1. **Login test** - Get a JWT token from auth API
2. **List pages** - Call `/api/v1/ocean/pages` with token
3. **Create page** - POST a new page
4. **Build page tree** - Display pages in hierarchical UI

### For Backend Devs:

1. **Run locally** - Get Ocean backend running on port 8000
2. **Test endpoints** - Use Swagger UI to test all operations
3. **Read ocean_service.py** - Understand the 35 operations
4. **Fix auth** - Implement JWT validation in deps.py

---

## ✅ Checklist for New Team Members

- [ ] Clone repository
- [ ] Install dependencies
- [ ] Copy .env file with credentials
- [ ] Run backend locally
- [ ] Access http://localhost:8000/docs
- [ ] Test login with admin credentials
- [ ] Create your first page via API
- [ ] Review code structure
- [ ] Join team chat
- [ ] Pick first issue to work on

---

**Last Updated:** December 27, 2025
**Backend Version:** 0.1.0
**Status:** 🟢 Production Ready (Auth integration pending)

---

## 💡 Pro Tips

> **Frontend:** Use React Query for API calls - it handles caching, refetching, and loading states automatically.

> **Backend:** All Ocean operations enforce multi-tenant isolation via organization_id - never skip this!

> **Testing:** The Swagger UI at `/docs` is your best friend for testing endpoints before building frontend.

> **Deployment:** Railway auto-deploys on push to main - check deployment logs if something breaks.

> **Search:** Semantic search uses embeddings - similar meanings match even with different words!
