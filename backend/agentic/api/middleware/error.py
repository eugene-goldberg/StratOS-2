"""
Error handling middleware for consistent error responses.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import logging
import traceback
from datetime import datetime
from uuid import uuid4

logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Global error handler middleware.
    
    Catches all unhandled exceptions and returns consistent error responses.
    """
    
    async def dispatch(self, request: Request, call_next):
        """Process the request and handle any errors."""
        request_id = str(uuid4())
        
        try:
            # Add request ID to request state
            request.state.request_id = request_id
            
            # Process request
            response = await call_next(request)
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Log the error with full traceback
            logger.error(
                f"Unhandled exception for request {request_id}: {str(e)}",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "url": str(request.url),
                    "traceback": traceback.format_exc()
                }
            )
            
            # Determine status code based on exception type
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            error_type = "internal_server_error"
            
            # Create error response
            error_response = {
                "error": {
                    "type": error_type,
                    "message": "An unexpected error occurred",
                    "request_id": request_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            
            # In development mode, include more details
            from config.settings import get_settings
            settings = get_settings()
            
            if settings.is_development:
                error_response["error"]["detail"] = str(e)
                error_response["error"]["traceback"] = traceback.format_exc().split("\n")
            
            return JSONResponse(
                status_code=status_code,
                content=error_response,
                headers={"X-Request-ID": request_id}
            )