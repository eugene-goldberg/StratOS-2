"""
Cosmos DB client utilities
"""
import os
from typing import List, Dict, Any, Optional
from azure.cosmos import CosmosClient, PartitionKey, exceptions
import logging

logger = logging.getLogger(__name__)

# Global client instance
_cosmos_client = None
_database = None
_log_container = None
_analytics_container = None


def get_cosmos_client():
    """Get or create Cosmos DB client"""
    global _cosmos_client
    
    if not _cosmos_client:
        endpoint = os.environ.get("COSMOS_DB_ENDPOINT")
        key = os.environ.get("COSMOS_DB_KEY")
        
        if not endpoint or not key:
            raise ValueError("Cosmos DB endpoint and key must be provided")
        
        # Clear any proxy environment variables that might interfere
        # Azure Functions sometimes sets these automatically
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
        original_proxies = {}
        for var in proxy_vars:
            if var in os.environ:
                original_proxies[var] = os.environ.pop(var)
                logger.info(f"Temporarily removed {var} from environment")
        
        try:
            # Initialize client with connection_verify=False to avoid SSL issues
            _cosmos_client = CosmosClient(endpoint, key, connection_verify=False)
            logger.info("Cosmos DB client initialized")
        finally:
            # Restore proxy variables
            for var, value in original_proxies.items():
                os.environ[var] = value
    
    return _cosmos_client


def get_database():
    """Get or create database"""
    global _database
    
    if not _database:
        client = get_cosmos_client()
        database_name = os.environ.get("COSMOS_DB_DATABASE_ID", "StratOSData")
        _database = client.get_database_client(database_name)
        logger.info(f"Connected to database: {database_name}")
    
    return _database


def get_log_container():
    """Get or create log entries container"""
    global _log_container
    
    if not _log_container:
        database = get_database()
        container_name = os.environ.get("COSMOS_DB_CONTAINER_ID", "CEOLogs")
        _log_container = database.get_container_client(container_name)
        logger.info(f"Connected to container: {container_name}")
    
    return _log_container


def get_analytics_container():
    """Get or create analytics/cache container"""
    global _analytics_container
    
    if not _analytics_container:
        database = get_database()
        container_name = os.environ.get("COSMOS_DB_ANALYTICS_CONTAINER_ID", "CEOLogs")
        _analytics_container = database.get_container_client(container_name)
        logger.info(f"Connected to analytics container: {container_name}")
    
    return _analytics_container


def create_item(container, item: dict) -> dict:
    """Create an item in the container"""
    try:
        created_item = container.create_item(body=item)
        logger.info(f"Created item with id: {created_item.get('id')}")
        return created_item
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error creating item: {e}")
        raise


def upsert_item(container, item: dict) -> dict:
    """Upsert an item in the container"""
    try:
        upserted_item = container.upsert_item(body=item)
        logger.info(f"Upserted item with id: {upserted_item.get('id')}")
        return upserted_item
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error upserting item: {e}")
        raise


def get_item(container, item_id: str, partition_key: str) -> Optional[dict]:
    """Get an item from the container"""
    try:
        item = container.read_item(item=item_id, partition_key=partition_key)
        return item
    except exceptions.CosmosResourceNotFoundError:
        return None
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error reading item: {e}")
        raise


def query_items(container, query: str, parameters: List[Dict[str, Any]] = None) -> List[dict]:
    """Query items from the container"""
    try:
        query_spec = {
            "query": query,
            "parameters": parameters or []
        }
        
        items = list(container.query_items(
            query=query_spec,
            enable_cross_partition_query=True
        ))
        
        logger.info(f"Query returned {len(items)} items")
        return items
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error querying items: {e}")
        raise


def delete_item(container, item_id: str, partition_key: str):
    """Delete an item from the container"""
    try:
        container.delete_item(item=item_id, partition_key=partition_key)
        logger.info(f"Deleted item with id: {item_id}")
    except exceptions.CosmosResourceNotFoundError:
        logger.warning(f"Item not found for deletion: {item_id}")
    except exceptions.CosmosHttpResponseError as e:
        logger.error(f"Error deleting item: {e}")
        raise