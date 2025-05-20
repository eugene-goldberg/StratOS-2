from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
import os
import json
from datetime import datetime
from pydantic import BaseModel

# Import API routers
from routers import strategic_foundation, subjective_input, objective_data, analysis, planning, auth
from core.config import settings

app = FastAPI(
    title="StratOS API",
    description="API for StratOS - An AI-Powered Strategic Copilot",
    version="0.1.0"
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