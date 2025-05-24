"""
Celery configuration for background tasks
"""
from celery import Celery
from ..core.config import settings

# Create Celery instance
celery_app = Celery(
    "stratos",
    broker=settings.REDIS_URL or "redis://localhost:6379/0",
    backend=settings.REDIS_URL or "redis://localhost:6379/0",
    include=["backend.tasks.analysis_tasks"]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task routing
    task_routes={
        "backend.tasks.analysis_tasks.*": {"queue": "analysis"},
    },
    # Beat schedule for periodic tasks
    beat_schedule={
        "periodic-risk-opportunity-scan": {
            "task": "backend.tasks.analysis_tasks.scan_for_risks_and_opportunities",
            "schedule": 300.0,  # Run every 5 minutes
            "options": {"queue": "analysis"}
        },
    }
)