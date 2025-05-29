"""
Retry logic and error handling utilities for Cosmos DB operations
"""

import asyncio
import logging
from typing import TypeVar, Callable, Optional, Any
from functools import wraps
from azure.cosmos import exceptions as cosmos_exceptions
from azure.core.exceptions import AzureError, ServiceRequestError, ServiceResponseError

logger = logging.getLogger(__name__)

T = TypeVar('T')


class CosmosDBError(Exception):
    """Base exception for Cosmos DB operations"""
    pass


class CosmosDBRetryableError(CosmosDBError):
    """Exception for retryable Cosmos DB errors"""
    pass


class CosmosDBNonRetryableError(CosmosDBError):
    """Exception for non-retryable Cosmos DB errors"""
    pass


def is_retryable_error(error: Exception) -> bool:
    """
    Determine if an error is retryable
    
    Args:
        error: The exception to check
        
    Returns:
        True if the error is retryable, False otherwise
    """
    # Rate limiting and throttling errors
    if isinstance(error, cosmos_exceptions.CosmosHttpResponseError):
        if error.status_code in [429, 503]:  # Too Many Requests, Service Unavailable
            return True
    
    # Network errors
    if isinstance(error, (ServiceRequestError, ServiceResponseError)):
        return True
    
    # Timeout errors
    if isinstance(error, asyncio.TimeoutError):
        return True
    
    # Conflict errors (can retry with updated data)
    if isinstance(error, cosmos_exceptions.CosmosResourceExistsError):
        return False  # Don't retry conflicts
    
    return False


def cosmos_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0
):
    """
    Decorator for retrying Cosmos DB operations with exponential backoff
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds between retries
        max_delay: Maximum delay in seconds between retries
        exponential_base: Base for exponential backoff calculation
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                
                except Exception as e:
                    last_exception = e
                    
                    # Check if error is retryable
                    if not is_retryable_error(e):
                        logger.error(f"Non-retryable error in {func.__name__}: {e}")
                        raise CosmosDBNonRetryableError(str(e)) from e
                    
                    # Calculate delay with exponential backoff
                    delay = min(base_delay * (exponential_base ** attempt), max_delay)
                    
                    # Add jitter to prevent thundering herd
                    import random
                    jittered_delay = delay * (0.5 + random.random())
                    
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Retryable error in {func.__name__} (attempt {attempt + 1}/{max_attempts}): {e}. "
                            f"Retrying in {jittered_delay:.2f}s"
                        )
                        await asyncio.sleep(jittered_delay)
                    else:
                        logger.error(
                            f"Max retries reached for {func.__name__} after {max_attempts} attempts: {e}"
                        )
            
            # If we get here, all retries failed
            raise CosmosDBRetryableError(
                f"Operation failed after {max_attempts} attempts: {last_exception}"
            ) from last_exception
        
        return wrapper
    return decorator


class RateLimiter:
    """Rate limiter for Cosmos DB operations"""
    
    def __init__(self, max_requests_per_second: float = 100):
        """
        Initialize rate limiter
        
        Args:
            max_requests_per_second: Maximum requests per second
        """
        self.max_requests_per_second = max_requests_per_second
        self.min_interval = 1.0 / max_requests_per_second
        self.last_request_time = 0.0
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """Acquire permission to make a request"""
        async with self._lock:
            current_time = asyncio.get_event_loop().time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.min_interval:
                wait_time = self.min_interval - time_since_last
                await asyncio.sleep(wait_time)
            
            self.last_request_time = asyncio.get_event_loop().time()


class ConnectionPool:
    """Connection pool for Cosmos DB clients"""
    
    def __init__(self, max_connections: int = 10):
        """
        Initialize connection pool
        
        Args:
            max_connections: Maximum number of connections
        """
        self.max_connections = max_connections
        self._pool: asyncio.Queue = asyncio.Queue(maxsize=max_connections)
        self._all_connections = []
        self._closed = False
    
    async def get_connection(self):
        """Get a connection from the pool"""
        if self._closed:
            raise RuntimeError("Connection pool is closed")
        
        # Try to get existing connection
        try:
            return self._pool.get_nowait()
        except asyncio.QueueEmpty:
            # Create new connection if under limit
            if len(self._all_connections) < self.max_connections:
                # This would create a new CosmosClient instance
                # For now, we'll return None as a placeholder
                return None
            else:
                # Wait for available connection
                return await self._pool.get()
    
    async def return_connection(self, connection):
        """Return a connection to the pool"""
        if not self._closed:
            await self._pool.put(connection)
    
    async def close(self):
        """Close all connections in the pool"""
        self._closed = True
        
        # Close all connections
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                # Close the connection
                if hasattr(conn, 'close'):
                    await conn.close()
            except asyncio.QueueEmpty:
                break