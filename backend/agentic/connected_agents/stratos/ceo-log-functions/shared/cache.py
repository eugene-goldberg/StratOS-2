"""
Caching utilities using Cosmos DB
"""
import os
import json
import time
import hashlib
from typing import Any, Optional, List
from .cosmos_client import get_analytics_container, get_item, upsert_item, query_items, delete_item
import logging

logger = logging.getLogger(__name__)

DEFAULT_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", "300"))


def generate_cache_key(operation: str, user_id: str, params: dict = None) -> str:
    """Generate a unique cache key"""
    base_key = f"{operation}_{user_id}"
    
    if not params:
        return base_key
    
    # Sort params for consistent key generation
    sorted_params = json.dumps(params, sort_keys=True)
    hash_value = hashlib.md5(sorted_params.encode()).hexdigest()[:8]
    
    return f"{base_key}_{hash_value}"


def get_cache(key: str) -> Optional[Any]:
    """Get cached value"""
    try:
        container = get_analytics_container()
        cache_entry = get_item(container, key, key)
        
        if cache_entry and cache_entry.get('expiresAt', 0) > time.time():
            logger.info(f"Cache hit for key: {key}")
            return cache_entry.get('value')
        
        logger.info(f"Cache miss for key: {key}")
        return None
    except Exception as e:
        logger.error(f"Cache get error: {e}")
        return None


def set_cache(key: str, value: Any, ttl_seconds: int = DEFAULT_TTL_SECONDS, cache_type: str = "search"):
    """Set cache value"""
    try:
        container = get_analytics_container()
        cache_entry = {
            "id": key,
            "key": key,
            "value": value,
            "expiresAt": time.time() + ttl_seconds,
            "type": cache_type,
            "ttl": ttl_seconds  # Cosmos DB TTL
        }
        
        upsert_item(container, cache_entry)
        logger.info(f"Cache set for key: {key}, TTL: {ttl_seconds}s")
    except Exception as e:
        logger.error(f"Cache set error: {e}")


def invalidate_cache(user_id: str, types: List[str] = None):
    """Invalidate cache entries for a user"""
    try:
        container = get_analytics_container()
        
        # Build query to find cache entries for user
        query = "SELECT c.id FROM c WHERE CONTAINS(c.key, @userId)"
        parameters = [{"name": "@userId", "value": user_id}]
        
        if types:
            type_conditions = " OR ".join([f"c.type = @type{i}" for i in range(len(types))])
            query += f" AND ({type_conditions})"
            for i, cache_type in enumerate(types):
                parameters.append({"name": f"@type{i}", "value": cache_type})
        
        items = query_items(container, query, parameters)
        
        # Delete all matching cache entries
        for item in items:
            delete_item(container, item['id'], item['id'])
        
        logger.info(f"Invalidated {len(items)} cache entries for user: {user_id}")
    except Exception as e:
        logger.error(f"Cache invalidation error: {e}")