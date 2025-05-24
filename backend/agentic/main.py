"""
FastAPI backend for StratOS Multi-Agent System.

This serves as the primary backend interface between the React web app
and the Azure AI Foundry Agent Service.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager

from api.routes import agents, health, websocket
from api.middleware.error import ErrorHandlerMiddleware
from config.settings import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load settings
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    # Startup
    logger.info("Starting StratOS Agentic Backend...")
    logger.info(f"Environment: {settings.environment}")
    logger.info("Initializing connections to Azure services...")
    
    # TODO: Initialize Azure service clients here
    # - AI Foundry Agent Service
    # - Cosmos DB
    # - Azure AI Search
    
    yield
    
    # Shutdown
    logger.info("Shutting down StratOS Agentic Backend...")
    # TODO: Cleanup connections


# Create FastAPI app
app = FastAPI(
    title="StratOS Multi-Agent System API",
    description="Backend API for StratOS strategic planning platform with multi-agent AI capabilities",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom error handling
app.add_middleware(ErrorHandlerMiddleware)

# Include routers
app.include_router(health.router, prefix="/api/health", tags=["health"])
app.include_router(agents.router, prefix="/api/agents", tags=["agents"])
app.include_router(websocket.router, prefix="/ws", tags=["websocket"])


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "StratOS Multi-Agent System API",
        "version": "1.0.0",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.environment == "development"
    )