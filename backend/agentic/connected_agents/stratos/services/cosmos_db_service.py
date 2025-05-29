# services/cosmos_db_service.py
import os
import logging
from typing import Optional, List
from azure.cosmos.aio import CosmosClient
from azure.cosmos import exceptions, PartitionKey

# Assuming ceo_log_models.py is in the same directory or accessible via sys.path
from .ceo_log_models import CEOLogEntry, LogSearchQuery, LogSummaryResponse # Import your Pydantic models

# Configure logging
logger = logging.getLogger(__name__)

# --- Configuration ---
# Set these environment variables in your Azure AI Studio agent's environment
COSMOS_ENDPOINT_CEO = os.getenv("CEO_LOGS_COSMOS_ENDPOINT", os.getenv("DEFAULT_COSMOS_ENDPOINT")) # Your Cosmos DB account endpoint
COSMOS_KEY_CEO = os.getenv("CEO_LOGS_COSMOS_KEY", os.getenv("DEFAULT_COSMOS_KEY")) # Your Cosmos DB primary key
DATABASE_NAME_CEO = os.getenv("CEO_LOGS_COSMOS_DATABASE_ID", "StratOSData") # Or your specific DB name
CONTAINER_NAME_CEO = os.getenv("CEO_LOGS_COSMOS_CONTAINER_ID", "CEOLogs") # Crucial: "CEOLogs"
# CEOLogEntry model uses 'userId' as partition key
PARTITION_KEY_PATH_CEO = "/userId"


class CosmosDBService:
    def __init__(self, key_vault_name: Optional[str] = None): # key_vault_name currently unused
        self._client: Optional[CosmosClient] = None
        self._database = None
        self._container = None
        self._is_initialized = False

        if not all([COSMOS_ENDPOINT_CEO, COSMOS_KEY_CEO, DATABASE_NAME_CEO, CONTAINER_NAME_CEO]):
            logger.error("CosmosDBService (for CEOLogs): Environment variables not fully configured.")
            # raise ValueError("Cosmos DB configuration missing for CosmosDBService")

    async def initialize(self):
        if self._is_initialized:
            return
        if not COSMOS_ENDPOINT_CEO or not COSMOS_KEY_CEO:
            logger.error("CosmosDBService: Cosmos DB endpoint or key is not configured. Cannot initialize.")
            self._is_initialized = False
            return
            
        try:
            self._client = CosmosClient(url=COSMOS_ENDPOINT_CEO, credential=COSMOS_KEY_CEO)
            self._database = self._client.get_database_client(DATABASE_NAME_CEO)
            self._container = self._database.get_container_client(CONTAINER_NAME_CEO)
            await self._container.read() # Check if container exists
            self._is_initialized = True
            logger.info(f"CosmosDBService initialized for container: {DATABASE_NAME_CEO}/{CONTAINER_NAME_CEO}")
        except exceptions.CosmosResourceNotFoundError:
            logger.error(f"CosmosDBService: Database '{DATABASE_NAME_CEO}' or Container '{CONTAINER_NAME_CEO}' not found.")
            self._is_initialized = False
        except Exception as e:
            logger.error(f"CosmosDBService: Failed to initialize Cosmos DB client: {e}", exc_info=True)
            self._is_initialized = False

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None
            self._is_initialized = False
            logger.info("CosmosDBService: Cosmos DB client closed.")
            
    async def _ensure_initialized(self):
        if not self._is_initialized:
            logger.warning("CosmosDBService was not initialized. Attempting to initialize now.")
            await self.initialize()
            if not self._is_initialized:
                raise ConnectionError("CosmosDBService could not be initialized.")

    async def create_log_entry(self, log_entry: CEOLogEntry) -> Optional[CEOLogEntry]:
        await self._ensure_initialized()
        try:
            # Use the dict_for_cosmos method from your model if available, or just .dict()
            # item_to_create = log_entry.dict_for_cosmos() 
            item_to_create = log_entry.dict(exclude_none=True) # Pydantic's dict() is usually fine
            
            # Ensure 'id' is present as Cosmos DB's document ID
            if 'id' not in item_to_create or not item_to_create['id']:
                 item_to_create['id'] = str(uuid.uuid4()) # Should be handled by Pydantic default_factory

            created_item = await self._container.create_item(body=item_to_create)
            logger.info(f"CEO Log entry created: {created_item['id']}")
            return CEOLogEntry(**created_item)
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to create CEO Log entry: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"An unexpected error occurred while creating CEO log entry: {e}", exc_info=True)
        return None

    async def search_logs(self, query: LogSearchQuery) -> List[CEOLogEntry]:
        await self._ensure_initialized()
        
        # Build a query string and parameters based on LogSearchQuery
        # This is a simplified example. You'll need to construct a proper SQL-like query.
        # Example: "SELECT * FROM c WHERE c.userId = @userId AND CONTAINS(c.logEntry.content, @searchTerm)"
        # You'll need to dynamically build the query string and parameters list.
        
        # For now, returning an empty list as a placeholder for complex query logic
        # TODO: Implement actual search logic based on LogSearchQuery fields
        
        q_parts = ["SELECT * FROM c WHERE c.userId = @userId"]
        params = [{"name": "@userId", "value": query.userId}]

        if query.searchTerm:
            q_parts.append("AND CONTAINS(c.logEntry.content, @searchTerm, true)") # case-insensitive
            params.append({"name": "@searchTerm", "value": query.searchTerm})
        if query.tags:
            # This requires tags to be an array that can be checked with ARRAY_CONTAINS
            # Assuming tags is an array field in Cosmos
            for i, tag_val in enumerate(query.tags):
                param_name = f"@tag{i}"
                q_parts.append(f"AND ARRAY_CONTAINS(c.tags, {param_name})")
                params.append({"name": param_name, "value": tag_val})
        if query.startDate:
            q_parts.append("AND c.timestamp >= @startDate")
            params.append({"name": "@startDate", "value": query.startDate.isoformat()+"Z"})
        # Add more conditions for other fields in LogSearchQuery (themes, sentiment, endDate)

        final_query = " ".join(q_parts)
        
        # Apply limit using TOP (Cosmos DB doesn't directly support OFFSET in the same way as SQL)
        # You might need to adjust query for pagination if using continuation tokens
        # final_query = final_query.replace("SELECT *", f"SELECT TOP {query.limit} *")
        # Note: TOP without ORDER BY can be non-deterministic. Add ORDER BY c.timestamp DESC for recent.


        logger.info(f"Executing search query: {final_query} with params: {params}")
        
        results = []
        try:
            async for item_data in self._container.query_items(
                query=final_query,
                parameters=params,
                partition_key=query.userId, # Search within the user's partition
                max_item_count=query.limit
            ):
                results.append(CEOLogEntry(**item_data))
            logger.info(f"Search found {len(results)} log entries for user {query.userId}")
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to search logs for user {query.userId}: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"An unexpected error occurred while searching logs for {query.userId}: {e}", exc_info=True)
        return results[:query.limit] # Ensure limit is applied post-fetch if not in query

    async def get_logs_summary(self, user_id: str, days: int) -> Optional[LogSummaryResponse]:
        await self._ensure_initialized()
        # This would typically involve multiple queries or a more complex aggregation query
        # to gather total logs, sentiment counts, top tags/themes, etc.
        # For simplicity, this is a placeholder. You'll need to implement the actual logic.
        
        # TODO: Implement actual summary logic. 
        # This usually requires multiple queries or a stored procedure if aggregations are complex.
        # Example steps:
        # 1. Get logs within the date range for the user.
        # 2. Aggregate counts for sentiment.
        # 3. Aggregate counts for tags and themes.
        # 4. Get the most recent N logs.
        
        logger.warning(f"get_logs_summary for user {user_id} is a placeholder and needs full implementation.")
        
        # Fetch recent logs as a starting point
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(days=days)

        search_query_recent = LogSearchQuery(
            userId=user_id,
            startDate=start_time,
            endDate=end_time,
            limit=5 # For recent logs display
        )
        recent_logs = await self.search_logs(search_query_recent) # Uses the search_logs method

        # Dummy data for other fields
        return LogSummaryResponse(
            totalLogs=len(recent_logs), # This is just count of recent, not total for period correctly
            dateRange={"start": start_time.isoformat()+"Z", "end": end_time.isoformat()+"Z"},
            sentimentCounts={"neutral": len(recent_logs)}, # Placeholder
            topTags=[{"tag": "sample", "count": 1}],      # Placeholder
            topThemes=[{"theme": "sample", "count": 1}],  # Placeholder
            recentLogs=recent_logs,
            insights={"averageLogsPerDay": round(len(recent_logs) / days, 2) if days > 0 else 0} # Placeholder
        )