"""
Health check endpoints for monitoring and liveness probes.
"""

from fastapi import APIRouter, status
from datetime import datetime
from typing import Dict, Any

from config.settings import get_settings

router = APIRouter()
settings = get_settings()


@router.get("/", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "StratOS Multi-Agent System",
        "version": "1.0.0"
    }


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check for Kubernetes/Container Apps.
    
    Checks if all required services are accessible.
    """
    # TODO: Add actual service connectivity checks
    checks = {
        "ai_foundry": await _check_ai_foundry(),
        "cosmos_db": await _check_cosmos_db(),
        "ai_search": await _check_ai_search(),
    }
    
    all_ready = all(check["status"] == "ready" for check in checks.values())
    
    return {
        "ready": all_ready,
        "timestamp": datetime.utcnow().isoformat(),
        "checks": checks
    }


@router.get("/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> Dict[str, str]:
    """
    Liveness check for Kubernetes/Container Apps.
    
    Simple check to verify the service is responsive.
    """
    return {
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }


async def _check_ai_foundry() -> Dict[str, Any]:
    """Check AI Foundry Agent Service connectivity."""
    # TODO: Implement actual connectivity check
    return {
        "status": "ready" if settings.ai_foundry_endpoint else "not_configured",
        "endpoint": settings.ai_foundry_endpoint if settings.ai_foundry_endpoint else None
    }


async def _check_cosmos_db() -> Dict[str, Any]:
    """Check Cosmos DB connectivity."""
    # TODO: Implement actual connectivity check
    return {
        "status": "ready" if settings.cosmos_endpoint else "not_configured",
        "database": settings.cosmos_database_name
    }


async def _check_ai_search() -> Dict[str, Any]:
    """Check Azure AI Search connectivity."""
    # TODO: Implement actual connectivity check
    return {
        "status": "ready" if settings.search_endpoint else "not_configured",
        "indexes": [
            settings.ceo_log_index,
            settings.strategic_docs_index,
            settings.insights_index,
            settings.canvas_index
        ] if settings.search_endpoint else []
    }