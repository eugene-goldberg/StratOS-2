"""
Database initialization module for StratOS.
Creates all required Cosmos DB containers at application startup.
"""

import logging
from typing import Dict, List
from azure.cosmos.aio import CosmosClient as AsyncCosmosClient
from azure.cosmos import PartitionKey, exceptions as CosmosExceptions

from .config import settings

logger = logging.getLogger(__name__)

# Container configurations: {container_name: partition_key_path}
CONTAINER_CONFIGS = {
    # Analysis Service containers
    "analyses": "/user_id",
    "insights": "/user_id", 
    "so_linkages": "/user_id",
    "analysis_sessions": "/user_id",
    
    # Auth Service containers
    "Users": "/email",
    
    # Objective Data Service containers
    "datasets": "/id",
    "kpis": "/id",
    "datapoints": "/dataset_id",
    
    # Planning Service containers
    "StrategicPlans": "/id",
    "Initiatives": "/id",
    
    # Strategic Foundation Service containers
    "NorthStarConfigurations": "/id",  # user_id serves as document ID
    
    # Subjective Input Service containers
    "log_entries": "/user_id",
    "strategic_canvases": "/user_id",
    
    # Conversation Service containers
    "conversations": "/user_id",
    "conversation_messages": "/conversation_id",
    
    # Alert Service containers  
    "alerts": "/user_id"
}

async def initialize_database() -> bool:
    """
    Initialize Cosmos DB database and containers.
    
    Returns:
        bool: True if initialization successful, False otherwise
    """
    if not settings.AZURE_COSMOS_ENDPOINT or not settings.AZURE_COSMOS_KEY:
        logger.warning("Cosmos DB credentials not provided. Skipping database initialization.")
        return False
    
    try:
        # Initialize Cosmos client
        async with AsyncCosmosClient(
            url=settings.AZURE_COSMOS_ENDPOINT,
            credential=settings.AZURE_COSMOS_KEY
        ) as client:
            
            # Create or get database
            logger.info(f"Creating/getting database: {settings.AZURE_COSMOS_DATABASE_NAME}")
            database = await client.create_database_if_not_exists(
                id=settings.AZURE_COSMOS_DATABASE_NAME
            )
            
            # Create containers
            containers_created = 0
            containers_existed = 0
            
            for container_name, partition_key_path in CONTAINER_CONFIGS.items():
                try:
                    container = await database.create_container_if_not_exists(
                        id=container_name,
                        partition_key=PartitionKey(path=partition_key_path),
                        offer_throughput=400  # Minimum throughput for development
                    )
                    
                    # Check if container was just created or already existed
                    try:
                        # Try to get container properties to determine if it existed
                        await database.get_container_client(container_name).read()
                        containers_existed += 1
                        logger.debug(f"Container '{container_name}' already exists")
                    except:
                        containers_created += 1
                        logger.info(f"Created container '{container_name}' with partition key '{partition_key_path}'")
                        
                except CosmosExceptions.CosmosResourceExistsError:
                    containers_existed += 1
                    logger.debug(f"Container '{container_name}' already exists")
                except Exception as e:
                    logger.error(f"Failed to create container '{container_name}': {e}")
                    # Continue with other containers rather than failing completely
            
            total_containers = len(CONTAINER_CONFIGS)
            logger.info(
                f"Database initialization completed. "
                f"Created: {containers_created}, Existed: {containers_existed}, "
                f"Total: {total_containers}"
            )
            
            return True
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False