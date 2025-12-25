# Ocean Backend

**Block-Based Knowledge Workspace - FastAPI Backend with ZeroDB Integration**

Ocean is a modern block-based knowledge management workspace similar to Notion, built with FastAPI. **All data services powered by AINative ZeroDB** - our serverless NoSQL database with built-in vector search and embeddings API.

---

## 🚀 Quick Start

```bash
# Clone repository
git clone https://github.com/AINative-Studio/ocean-backend.git
cd ocean-backend

# Follow Day 1 setup guide
cat DAY1_CHECKLIST.md

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your ZeroDB credentials

# Run development server
uvicorn app.main:app --reload
```

---

## 📋 Project Overview

Ocean Backend provides a complete REST API for managing pages, blocks, links, tags, and semantic search powered by ZeroDB's embeddings API.

### Key Features

- **Block-Based Content**: 6 block types (text, heading, list, task, link, page_link)
- **Semantic Search**: Hybrid search using ZeroDB Embeddings API (768-dim vectors, FREE)
- **Bidirectional Links**: Page and block linking with automatic backlinks
- **Multi-tenant**: Organization-scoped isolation for all data
- **Tag Management**: Flexible tagging system with color support
- **Real-time Embeddings**: Automatic vector generation on content changes

### Tech Stack

- **Framework**: FastAPI (Python 3.11+)
- **Database**: ZeroDB Serverless (NoSQL tables)
- **Embeddings**: ZeroDB Embeddings API (BAAI/bge-base-en-v1.5, 768 dimensions)
- **Authentication**: JWT via AINative core backend
- **Deployment**: Railway

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [BACKEND_BACKLOG.md](BACKEND_BACKLOG.md) | Complete development backlog (22 issues, 39 story points) |
| [ZERODB_IMPLEMENTATION_PLAN.md](ZERODB_IMPLEMENTATION_PLAN.md) | Detailed implementation guide with code examples |
| [DAY1_CHECKLIST.md](DAY1_CHECKLIST.md) | Step-by-step setup guide for first day |
| [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) | **Comprehensive Railway deployment guide** |
| [docs/RAILWAY_QUICK_START.md](docs/RAILWAY_QUICK_START.md) | **5-minute Railway deployment** |
| [EMBEDDINGS_REVISION_SUMMARY.md](EMBEDDINGS_REVISION_SUMMARY.md) | Why we use ZeroDB Embeddings API |
| [PRD.md](PRD.md) | Product requirements document |
| [.claude/CLAUDE.md](.claude/CLAUDE.md) | Project memory and coding standards |

---

## 🗂️ Project Structure

```
ocean-backend/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   │           ├── ocean_pages.py      # Page CRUD endpoints
│   │           ├── ocean_blocks.py     # Block operations
│   │           ├── ocean_links.py      # Linking system
│   │           ├── ocean_tags.py       # Tag management
│   │           └── ocean_search.py     # Hybrid search
│   ├── models/                         # Database models
│   ├── schemas/                        # Pydantic schemas
│   ├── services/
│   │   └── ocean_service.py           # Business logic
│   └── main.py                        # FastAPI app
├── scripts/
│   └── setup_tables.py                # ZeroDB table setup
├── tests/                             # Test suite
├── .claude/                           # Claude Code config
└── docs/                              # Additional documentation
```

---

## 🔑 Environment Variables

```bash
# ZeroDB Configuration
ZERODB_API_URL=https://api.ainative.studio
ZERODB_PROJECT_ID=<your-project-id>
ZERODB_API_KEY=<your-api-key>
OCEAN_EMBEDDINGS_MODEL=BAAI/bge-base-en-v1.5

# AINative Backend (for authentication)
AINATIVE_API_URL=https://api.ainative.studio

# Optional: Redis for caching
REDIS_URL=redis://localhost:6379/0
```

---

## 📊 API Endpoints

### Pages
- `POST /v1/ocean/pages` - Create page
- `GET /v1/ocean/pages` - List pages
- `GET /v1/ocean/pages/{page_id}` - Get page
- `PUT /v1/ocean/pages/{page_id}` - Update page
- `DELETE /v1/ocean/pages/{page_id}` - Delete page (soft)
- `POST /v1/ocean/pages/{page_id}/move` - Move page

### Blocks
- `POST /v1/ocean/blocks` - Create block
- `POST /v1/ocean/blocks/batch` - Create multiple blocks
- `GET /v1/ocean/blocks/{block_id}` - Get block
- `GET /v1/ocean/blocks?page_id={id}` - List blocks by page
- `PUT /v1/ocean/blocks/{block_id}` - Update block
- `DELETE /v1/ocean/blocks/{block_id}` - Delete block
- `POST /v1/ocean/blocks/{block_id}/move` - Reorder blocks
- `PUT /v1/ocean/blocks/{block_id}/convert` - Convert block type

### Links
- `POST /v1/ocean/links` - Create link
- `DELETE /v1/ocean/links/{link_id}` - Delete link
- `GET /v1/ocean/pages/{page_id}/backlinks` - Get page backlinks
- `GET /v1/ocean/blocks/{block_id}/backlinks` - Get block backlinks

### Tags
- `POST /v1/ocean/tags` - Create tag
- `GET /v1/ocean/tags` - List tags
- `PUT /v1/ocean/tags/{tag_id}` - Update tag
- `DELETE /v1/ocean/tags/{tag_id}` - Delete tag
- `POST /v1/ocean/blocks/{block_id}/tags` - Assign tag to block
- `DELETE /v1/ocean/blocks/{block_id}/tags/{tag_id}` - Remove tag

### Search
- `GET /v1/ocean/search?q={query}` - Hybrid semantic + metadata search
  - Filters: `block_types`, `tags`, `date_range`
  - Search types: `semantic`, `metadata`, `hybrid`
  - Pagination: `limit`, `offset`

---

## 🏗️ Development Workflow

### Sprint Plan (3 sprints, 2-3 weeks)

**Sprint 1 (Week 1)**: Foundation & Page Operations
- Issues #1-6 (13 story points)
- ZeroDB setup, table creation, page CRUD

**Sprint 2 (Week 2)**: Block Management & Search
- Issues #7-14 (18 story points)
- Block operations with embeddings, linking, search

**Sprint 3 (Week 3)**: Tags, Polish & Deployment
- Issues #15-22 (13 story points)
- Tag management, optimization, testing, deployment

### GitHub Issues

View all issues: [https://github.com/AINative-Studio/ocean-backend/issues](https://github.com/AINative-Studio/ocean-backend/issues)

### Coding Standards

Ocean follows AINative core coding standards. See [.claude/CLAUDE.md](.claude/CLAUDE.md) for:

- **ZERO AI Attribution Policy**: No "Claude", "Anthropic", or AI references in commits
- **Issue Tracking**: NO code without a GitHub issue
- **File Placement**: Documentation in `docs/`, scripts in `scripts/`
- **Testing**: 80%+ test coverage required
- **Code Quality**: Type hints, docstrings, no ORM (direct SQL per SSCS V2.0)

---

## 🧪 Testing

![Coverage Badge](./coverage.svg)

### Quick Start

```bash
# Run all unit tests (fast, no infrastructure needed)
pytest tests/test_schemas.py tests/test_config.py tests/test_middleware.py tests/test_ocean_service_unit.py -v

# Run with coverage report
pytest tests/ --cov=app --cov-report=html --cov-report=term-missing

# View HTML coverage report
open htmlcov/index.html
```

### Test Suite Overview

**Unit Tests**: 35 passing
- ✅ `test_schemas.py` - 19 tests (100% schema coverage)
- ✅ `test_ocean_service_unit.py` - 9 tests (validation logic)
- ✅ `test_config.py` - 5 tests (100% config coverage)
- ✅ `test_middleware.py` - 2 tests (middleware init)

**Integration Tests**: 7 passing, 61 blocked
- 🟨 `test_ocean_pages.py` - 3/16 passing (ZeroDB persistence bug)
- 🟨 `test_ocean_blocks.py` - 3/24 passing (depends on pages)
- 🟨 `test_ocean_links.py` - 1/12 passing (depends on blocks)
- ❌ `test_embeddings_api.py` - 0/16 passing (routes not implemented)

### Coverage Report

**Current Coverage**: 19% (290/1,514 statements)

| Module | Coverage | Status |
|--------|----------|--------|
| schemas | 100% | ✅ Complete |
| config | 100% | ✅ Complete |
| middleware | 60% | 🟨 Partial |
| ocean_service | 9% | ❌ Blocked by ZeroDB |
| endpoints | 0% | ❌ Blocked by ZeroDB |

**Coverage Details**: See [docs/COVERAGE_REPORT.md](docs/COVERAGE_REPORT.md)

**Infrastructure Blockers**:
- ZeroDB data persistence failure blocks 61 integration tests
- Embeddings API routes missing (16 tests blocked)

**Realistic Coverage Targets**:
- Current (without infrastructure): 19-25%
- With ZeroDB fixed: 75-80%
- Maximum achievable: 85-90%

### Running Specific Tests

```bash
# Schema validation tests (100% coverage)
pytest tests/test_schemas.py -v

# Service validation tests
pytest tests/test_ocean_service_unit.py -v

# Integration tests (requires ZeroDB fix)
pytest tests/test_ocean_pages.py -v

# Load testing (1000+ concurrent requests)
locust -f tests/load_test.py
```

---

## 🚢 Deployment

### Quick Deploy to Railway

**Option 1: Automated Setup (Recommended)**

```bash
# Run setup script - prompts for env vars and deploys
./scripts/railway_setup.sh
```

**Option 2: Manual Setup**

```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link to project
railway link

# Set environment variables
railway variables set ZERODB_API_URL=https://api.ainative.studio
railway variables set ZERODB_PROJECT_ID=your_project_id
railway variables set ZERODB_API_KEY=your_api_key
railway variables set SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

# Deploy
railway up
```

### Verify Deployment

```bash
# Set your staging URL
export RAILWAY_STAGING_URL=https://your-app.up.railway.app

# Run smoke tests
./scripts/smoke_tests.sh
```

### Documentation

- **Quick Start**: [docs/RAILWAY_QUICK_START.md](docs/RAILWAY_QUICK_START.md) - 5-minute deployment
- **Full Guide**: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) - Comprehensive deployment guide
- **CI/CD**: `.github/workflows/deploy.yml` - Automated deployment pipeline

### CI/CD Pipeline

Every push to `main` triggers:
1. Linting and type checking
2. Full test suite with coverage
3. Deployment to Railway staging
4. Health checks and smoke tests
5. Automatic rollback on failure

---

## 🤝 Contributing

1. **Create a GitHub issue** for your feature/bug
2. **Create a branch**: `git checkout -b feature/123-short-description`
3. **Write tests first** (TDD approach)
4. **Implement feature** following SSCS V2.0 standards
5. **Run tests**: `pytest tests/`
6. **Commit**: `git commit -m "Add feature\n\nRefs #123"`
7. **Push**: `git push origin feature/123-short-description`
8. **Create PR** linking to issue

**Important**: Read `.claude/git-rules.md` for commit message rules.

---

## 📖 ZeroDB Slash Commands

Ocean includes 29 ZeroDB slash commands for rapid development:

```bash
/zerodb-help                    # Show all commands
/zerodb-table-create           # Create NoSQL table
/zerodb-vector-search          # Semantic search
/zerodb-memory-store           # Store agent memory
/zerodb-postgres-provision     # Provision PostgreSQL
```

See `.claude/commands/` for all available commands.

---

## 🐛 Troubleshooting

### Issue: Embeddings API returns 401
**Solution**: Check `ZERODB_API_KEY` in `.env`

### Issue: Table creation fails
**Solution**: Verify `ZERODB_PROJECT_ID` is correct

### Issue: Search returns no results
**Solution**: Wait 5-10 seconds for vector indexing

### Issue: Vector dimensions mismatch
**Solution**: Always use same model (BAAI/bge-base-en-v1.5) for store and search

See [DAY1_CHECKLIST.md](DAY1_CHECKLIST.md) troubleshooting section for more.

---

## 📝 License

Proprietary - AINative Studio

---

## 🔗 Links

- **Frontend Repo**: https://github.com/AINative-Studio/ocean-frontend
- **AINative Platform**: https://www.ainative.studio
- **ZeroDB Docs**: https://www.ainative.studio/zerodb
- **API Documentation**: https://api.ainative.studio/docs

---

## 💡 Architecture Highlights

### Why ZeroDB Embeddings API?

- **100% Cost Savings**: FREE vs OpenAI's paid API
- **Better Integration**: Native to AINative platform
- **Faster Performance**: One-call embed-and-store workflow
- **Dogfooding**: Validates our own product
- **Zero Dependencies**: No external API keys needed

See [EMBEDDINGS_REVISION_SUMMARY.md](EMBEDDINGS_REVISION_SUMMARY.md) for complete analysis.

### Block Types

1. **Text**: Rich text content with formatting
2. **Heading**: H1, H2, H3 with hierarchy
3. **List**: Bullet or numbered lists
4. **Task**: Checkboxes with due dates
5. **Link**: External URL references
6. **Page Link**: Internal page references

### Data Model

- **4 NoSQL Tables**: `ocean_pages`, `ocean_blocks`, `ocean_block_links`, `ocean_tags`
- **768-Dimension Vectors**: Stored in ZeroDB `vector_768` column
- **Organization-Scoped**: All data isolated by `organization_id`

---

**Ready to build the future of knowledge management!** 🚀

For questions, see documentation or contact the team via GitHub issues.
