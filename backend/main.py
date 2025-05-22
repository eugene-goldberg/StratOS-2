from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import os
import json
import logging
from datetime import datetime
from pydantic import BaseModel
from contextlib import asynccontextmanager

# Import API routers
from .routers import strategic_foundation, subjective_input, objective_data, analysis, planning, auth, conversation
from .core.config import settings
from .core.db_setup import initialize_database

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events"""
    # Startup
    logger.info("Starting StratOS API...")
    try:
        await initialize_database()
        logger.info("Database initialization completed successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Continue startup even if database initialization fails
        # Services will use in-memory fallbacks
    
    yield
    
    # Shutdown
    logger.info("Shutting down StratOS API...")

app = FastAPI(
    title="StratOS API",
    description="API for StratOS - An AI-Powered Strategic Copilot",
    version="0.1.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include auth router first (no authentication required)
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])

# Include protected routers (require authentication)
app.include_router(strategic_foundation.router, prefix="/api/foundation", tags=["Strategic Foundation"])
app.include_router(subjective_input.router, prefix="/api/subjective", tags=["Subjective Input"])
app.include_router(objective_data.router, prefix="/api/objective", tags=["Objective Data"])
app.include_router(analysis.router, prefix="/api/analysis", tags=["Analysis"])
app.include_router(planning.router, prefix="/api/planning", tags=["Planning"])
app.include_router(conversation.router, prefix="/api", tags=["Conversations"])

@app.get("/")
async def root():
    return {"message": "Welcome to StratOS API"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": app.version
    }