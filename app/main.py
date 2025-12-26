"""
Ocean Backend - Main FastAPI Application

This is the entry point for the Ocean backend API server.
Built with FastAPI and ZeroDB serverless infrastructure.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.api.v1.endpoints import ocean_pages, ocean_blocks, ocean_links, ocean_tags, ocean_search
from app.middleware import QueryTimingMiddleware
from app.logging_config import setup_logging

# Setup logging
setup_logging(debug=settings.DEBUG)

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Ocean - Notion-like workspace built on ZeroDB serverless infrastructure",
    version="0.1.0",
    debug=settings.DEBUG,
)

# Configure middleware
# Add timing middleware first (executes last, wraps everything)
app.add_middleware(
    QueryTimingMiddleware,
    slow_query_threshold_ms=100.0  # Log queries slower than 100ms
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(
    ocean_pages.router,
    prefix=f"{settings.API_V1_STR}/ocean",
    tags=["pages"]
)

app.include_router(
    ocean_blocks.router,
    prefix=f"{settings.API_V1_STR}/ocean",
    tags=["blocks"]
)

app.include_router(
    ocean_links.router,
    prefix=f"{settings.API_V1_STR}/ocean",
    tags=["links"]
)

app.include_router(
    ocean_tags.router,
    prefix=f"{settings.API_V1_STR}/ocean",
    tags=["tags"]
)

app.include_router(
    ocean_search.router,
    prefix=f"{settings.API_V1_STR}/ocean",
    tags=["search"]
)


@app.on_event("startup")
async def startup_event():
    """Startup event - check configuration."""
    import logging
    logger = logging.getLogger("uvicorn")

    logger.info("=" * 60)
    logger.info("Ocean Backend Starting...")
    logger.info("=" * 60)

    if not settings.validate_zerodb_config():
        logger.warning("⚠️  ZeroDB credentials NOT configured!")
        logger.warning("⚠️  Set ZERODB_PROJECT_ID and ZERODB_API_KEY in Railway variables")
        logger.warning("⚠️  Ocean API endpoints will not function until configured")
    else:
        logger.info(f"✓ ZeroDB configured: Project {settings.ZERODB_PROJECT_ID}")
        logger.info(f"✓ ZeroDB API URL: {settings.ZERODB_API_URL}")

    logger.info(f"✓ CORS Origins: {settings.BACKEND_CORS_ORIGINS}")
    logger.info("=" * 60)


@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "name": settings.PROJECT_NAME,
        "version": "0.1.0",
        "description": "Ocean Backend API",
        "status": "operational",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    zerodb_configured = settings.validate_zerodb_config()

    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "ocean-backend",
            "version": "0.1.0",
            "configuration": {
                "zerodb_configured": zerodb_configured,
                "warning": None if zerodb_configured else "ZeroDB credentials not configured. Set ZERODB_PROJECT_ID and ZERODB_API_KEY environment variables."
            },
            "zerodb": {
                "project_id": settings.ZERODB_PROJECT_ID or "NOT_CONFIGURED",
                "api_url": settings.ZERODB_API_URL,
                "embeddings_model": settings.OCEAN_EMBEDDINGS_MODEL
            }
        }
    )


@app.get(f"{settings.API_V1_STR}/info")
async def api_info():
    """API v1 information endpoint."""
    return {
        "api_version": "v1",
        "features": [
            "Pages management",
            "Blocks management",
            "Semantic search",
            "Block linking",
            "Tags"
        ],
        "embeddings": {
            "model": settings.OCEAN_EMBEDDINGS_MODEL,
            "dimensions": settings.OCEAN_EMBEDDINGS_DIMENSIONS
        },
        "endpoints": {
            "pages": f"{settings.API_V1_STR}/pages",
            "blocks": f"{settings.API_V1_STR}/blocks",
            "search": f"{settings.API_V1_STR}/search",
            "tags": f"{settings.API_V1_STR}/tags"
        }
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
