import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.exceptions import setup_exception_handlers
from app.api.v1.api import api_router
from app.database.init_db import init_database

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events: initialize database schema & seed data on startup.
    """
    logger.info("Initializing database tables and seed data...")
    try:
        init_database(
            seed=settings.SEED_DEMO_DATA and settings.ENVIRONMENT.lower() != "production"
        )
        logger.info("Database schema and seed data initialized successfully.")
    except Exception as e:
        logger.exception("Database initialization failed on startup: %s", e)
        if settings.ENVIRONMENT.lower() == "production":
            raise
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Setup Centralized Exception Handlers
setup_exception_handlers(app)

# Configure CORS
origins = settings.cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root Health Check Endpoint (Task 9)
@app.get("/health", tags=["Health"])
def health_check():
    """
    Standard top-level health check endpoint for production load balancers and hosting monitors.
    """
    return {"status": "ok"}


# Mount API endpoints under /api (e.g., /api/health, /api/departments, /api/locations)
app.include_router(api_router, prefix="/api")

# Mount Versioned API endpoints under /api/v1 (e.g., /api/v1/health, /api/v1/departments)
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
def root_info():
    """
    Root entry point with service metadata.
    """
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "active",
        "docs": "/docs",
        "health": "/api/health",
        "endpoints": [
            "/health",
            "/api/health",
            "/api/departments",
            "/api/locations",
            "/api/reports",
        ],
    }


