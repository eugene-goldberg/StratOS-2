"""
Cosmos DB client for North Star data management
Following the pattern from CEO Log functions
"""

import os
from azure.cosmos import CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosResourceNotFoundError
import logging

logger = logging.getLogger(__name__)

class NorthStarCosmosClient:
    def __init__(self):
        """Initialize Cosmos DB client with connection from environment"""
        connection_string = os.environ.get("COSMOS_CONNECTION_STRING")
        if not connection_string:
            raise ValueError("COSMOS_CONNECTION_STRING environment variable is required")
        
        self.client = CosmosClient.from_connection_string(connection_string)
        self.database_name = "StratOSData"
        self.container_name = "NorthStar"
        
        try:
            self.database = self.client.get_database_client(self.database_name)
            self.container = self.database.get_container_client(self.container_name)
            logger.info(f"Connected to Cosmos DB: {self.database_name}/{self.container_name}")
        except Exception as e:
            logger.error(f"Failed to connect to Cosmos DB: {str(e)}")
            raise
    
    def get_organization_data(self, organization_id: str):
        """Get all North Star data for an organization"""
        try:
            item = self.container.read_item(
                item=organization_id,
                partition_key=organization_id
            )
            return item
        except CosmosResourceNotFoundError:
            # Return empty structure for new organizations
            return {
                "id": organization_id,
                "organizationId": organization_id,
                "purpose": None,
                "vision": None,
                "values": [],
                "strategicGoals": {},
                "goalHierarchy": {}
            }
    
    def save_organization_data(self, data: dict):
        """Save or update North Star data for an organization"""
        try:
            # Ensure required fields
            if "organizationId" not in data:
                raise ValueError("organizationId is required")
            
            data["id"] = data["organizationId"]  # id must match partition key
            
            # Upsert the document
            result = self.container.upsert_item(body=data)
            logger.info(f"Saved North Star data for organization: {data['organizationId']}")
            return result
        except Exception as e:
            logger.error(f"Failed to save North Star data: {str(e)}")
            raise
    
    def query_goals_by_status(self, organization_id: str, status: str):
        """Query strategic goals by status"""
        query = """
        SELECT g.id, g.name, g.description, g.status, g.targetDate
        FROM c
        JOIN g IN c.strategicGoals
        WHERE c.organizationId = @orgId AND g.status = @status
        """
        
        parameters = [
            {"name": "@orgId", "value": organization_id},
            {"name": "@status", "value": status}
        ]
        
        try:
            items = list(self.container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))
            return items
        except Exception as e:
            logger.error(f"Failed to query goals: {str(e)}")
            return []