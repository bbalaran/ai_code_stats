"""FastAPI application for ProdLens API backend."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from routes import auth, health, insights, metrics, profile, sessions, websocket

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.debug else logging.WARNING,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle manager."""
    # Startup
    logger.info("Starting ProdLens API backend")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Database: {settings.database_url}")

    yield

    # Shutdown
    logger.info("Shutting down ProdLens API backend")


# Create FastAPI application
app = FastAPI(
    title="ProdLens API",
    description="REST API for AI development analytics and metrics",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure CORS
logger.info(f"Configuring CORS for origins: {settings.cors_origins}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


# Include routes
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(metrics.router)
app.include_router(sessions.router)
app.include_router(profile.router)
app.include_router(insights.router)
app.include_router(websocket.router)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return JSONResponse({
        "message": "ProdLens API Backend",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "status": "running",
    })


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_level="debug" if settings.debug else "info",
    )
