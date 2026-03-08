"""
FastAPI entry point for TestGen AI Agent.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.database import init_db
from app.routers import jira, valueedge, documents, llm, generation, settings, export


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    await init_db()
    yield
    # Shutdown
    pass


# Create FastAPI app
app = FastAPI(
    title="TestGen AI Agent",
    description="AI-Powered Test Plan & Test Case Generation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(jira.router)
app.include_router(valueedge.router)
app.include_router(documents.router)
app.include_router(llm.router)
app.include_router(generation.router)
app.include_router(settings.router)
app.include_router(export.router)


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "service": "testgen-ai-agent"
    }


@app.get("/")
async def root():
    """Root endpoint - redirect to docs."""
    return {
        "message": "TestGen AI Agent API",
        "docs": "/docs",
        "health": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True
    )
