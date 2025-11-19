"""
Main application entry point
FastAPI application with background scheduler
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.logging_config import setup_logging
from app.models import init_db
from app.scheduler import setup_scheduler, shutdown_scheduler
from app.api import router


# Setup logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown
    """
    # Startup
    print("=" * 80)
    print("BLOG AUTOMATION SYSTEM STARTING")
    print("=" * 80)

    # Initialize database
    print("Initializing database...")
    init_db()
    print("✓ Database initialized")

    # Setup and start scheduler
    print("Setting up job scheduler...")
    setup_scheduler()
    print("✓ Scheduler ready")

    print("=" * 80)
    print("APPLICATION READY")
    print("=" * 80)

    yield

    # Shutdown
    print("=" * 80)
    print("SHUTTING DOWN")
    print("=" * 80)
    shutdown_scheduler()
    print("✓ Scheduler stopped")
    print("Goodbye!")


# Create FastAPI application
app = FastAPI(
    title="Blog Automation System",
    description="Automated blog generation and publishing system with Gemini AI and Hashnode",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api", tags=["Blog Automation"])


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Blog Automation System",
        "version": "1.0.0",
        "docs": "/docs",
        "api": "/api"
    }


if __name__ == "__main__":
    import uvicorn
    import os

    # Disable reload to allow BackgroundScheduler to work properly
    # Set UVICORN_RELOAD=true in environment to enable reload for development
    reload = os.getenv("UVICORN_RELOAD", "false").lower() == "true"

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=reload
    )
