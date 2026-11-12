"""
FastAPI Application Entry Point.

Initializes the FastAPI application, mounts middlewares (CORS, Rate Limiting),
binds asynchronous lifespan events (database startup and teardown),
registers API routers under /api/v1, and configures OpenAPI metadata.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.config import get_settings
from app.core.rate_limit import custom_rate_limit_exceeded_handler, limiter
from app.database import close_db, init_db
from app.logging_config import logger
from app.routers import auth, books, users

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Asynchronous lifespan manager handling startup and shutdown events.
    Guarantees database tables are created before incoming requests are accepted,
    and connection pools are disposed cleanly on shutdown.
    """
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION} [{settings.ENVIRONMENT}]")
    await init_db()
    yield
    logger.info("Application shutdown initiated. Disposing resources...")
    await close_db()


# FastAPI Application Instance with Rich Metadata
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "## Datheon Python + FastAPI Backend Development Internship Project\n\n"
        "A complete, secure, asynchronous RESTful backend implementing:\n"
        "- **Task 1**: BookStore REST API with Pydantic V2 validation, pagination, and query filtering.\n"
        "- **Task 2**: User authentication and Role-Based Access Control (RBAC) via JWT and bcrypt.\n"
        "- **Task 3**: Asynchronous database persistence using SQLAlchemy 2.0 and SQLite (aiosqlite).\n"
        "- **Task 4**: Background tasks, IP-based rate limiting (SlowAPI), and Docker containerization.\n\n"
        "### Interactive Documentation\n"
        "- Explore interactive endpoints below using the **Authorize** button with your JWT Bearer token.\n"
        "- OpenAPI JSON specification is available at [`/openapi.json`](/openapi.json)."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Attach Rate Limiting State and Middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, custom_rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Cross-Origin Resource Sharing (CORS) Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific trusted domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers under the unified /api/v1 prefix
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(books.router, prefix=settings.API_V1_PREFIX)
app.include_router(users.router, prefix=settings.API_V1_PREFIX)


# ==============================================================================
# ROOT & SYSTEM HEALTH ENDPOINTS
# ==============================================================================

@app.get(
    "/",
    tags=["System"],
    summary="API Root Index",
    description="Returns welcome message and links to interactive documentation.",
)
async def root():
    return {
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs",
        "redoc_url": "/redoc",
        "openapi_url": "/openapi.json",
        "message": "Welcome to the Datheon BookStore Backend API.",
    }


@app.get(
    "/health",
    tags=["System"],
    summary="System Health Check",
    description="Container health check endpoint used by Docker and orchestrators.",
)
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": "connected",
    }
