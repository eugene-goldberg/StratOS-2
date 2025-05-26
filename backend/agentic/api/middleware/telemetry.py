"""
FastAPI telemetry middleware for StratOS agents.
Automatically instruments all API requests and agent invocations.
"""

from fastapi import Request
import time
from typing import Callable
import json
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.telemetry import initialize_telemetry, create_span_context, add_span_attributes


class TelemetryMiddleware:
    """Middleware to add telemetry to all FastAPI requests."""
    
    def __init__(self, app):
        self.app = app
        
        # Initialize telemetry
        self.tracer = initialize_telemetry(
            service_name="StratOS.FastAPI",
            service_version="1.0.0"
        )
    
    async def __call__(self, request: Request, call_next: Callable):
        # Skip telemetry for health checks
        if request.url.path in ["/health", "/", "/docs", "/openapi.json"]:
            return await call_next(request)
        
        # Create span for the request
        span_name = f"http.{request.method} {request.url.path}"
        
        with create_span_context(span_name, {
            "http.method": request.method,
            "http.url": str(request.url),
            "http.path": request.url.path,
            "http.host": request.url.hostname,
            "user_agent": request.headers.get("user-agent", "unknown")
        }) as span:
            
            start_time = time.time()
            
            try:
                # Process request
                response = await call_next(request)
                
                # Add response attributes
                duration = time.time() - start_time
                add_span_attributes(span, {
                    "http.status_code": response.status_code,
                    "http.duration_ms": round(duration * 1000, 2),
                    "response.success": response.status_code < 400
                })
                
                return response
                
            except Exception as e:
                # Record exception
                duration = time.time() - start_time
                add_span_attributes(span, {
                    "http.status_code": 500,
                    "http.duration_ms": round(duration * 1000, 2),
                    "error": str(e),
                    "error.type": type(e).__name__
                })
                raise


def setup_telemetry_middleware(app):
    """Setup telemetry middleware on FastAPI app."""
    app.add_middleware(TelemetryMiddleware)
