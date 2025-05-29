# services/delegation_tracking_service.py
import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
import uuid # Ensure uuid is imported
from azure.cosmos.aio import CosmosClient
from azure.cosmos import exceptions, PartitionKey

# Assuming delegation_models.py is in the same directory or accessible via sys.path
from .delegation_models import DelegationRecord, DelegationStatus, DelegationSource, AgentMetrics

# Configure logging
logger = logging.getLogger(__name__)

# --- Configuration ---
# Set these environment variables in your Azure AI Studio agent's environment
# MODIFIED to include fallbacks to DEFAULT_ variables
COSMOS_ENDPOINT = os.getenv("DELEGATION_COSMOS_ENDPOINT", os.getenv("DEFAULT_COSMOS_ENDPOINT"))
COSMOS_KEY = os.getenv("DELEGATION_COSMOS_KEY", os.getenv("DEFAULT_COSMOS_KEY"))
DATABASE_NAME = os.getenv("DELEGATION_COSMOS_DATABASE_ID", "StratOSData")
CONTAINER_NAME = os.getenv("DELEGATION_COSMOS_CONTAINER_ID", "AgentDelegations")
PARTITION_KEY_PATH = "/agentId" # As per previous discussion, assuming agentId is the partition key

class DelegationTrackingService:
    def __init__(self, key_vault_name: Optional[str] = None): # key_vault_name currently unused, relies on env vars
        self._client: Optional[CosmosClient] = None
        self._database = None
        self._container = None
        self._is_initialized = False

        if not all([COSMOS_ENDPOINT, COSMOS_KEY, DATABASE_NAME, CONTAINER_NAME]):
            logger.error("DelegationTrackingService: Cosmos DB environment variables not fully configured (checked DELEGATION_ and DEFAULT_ prefixes).")
            # You might raise an error here or let it fail upon initialization attempt
            # raise ValueError("Cosmos DB configuration missing for DelegationTrackingService")

    async def initialize(self):
        if self._is_initialized:
            return
        if not COSMOS_ENDPOINT or not COSMOS_KEY:
            logger.error("DelegationTrackingService: Cosmos DB endpoint or key is not configured. Cannot initialize.")
            self._is_initialized = False
            return

        try:
            self._client = CosmosClient(url=COSMOS_ENDPOINT, credential=COSMOS_KEY)
            self._database = self._client.get_database_client(DATABASE_NAME)
            self._container = self._database.get_container_client(CONTAINER_NAME)
            await self._container.read() 
            self._is_initialized = True
            logger.info(f"DelegationTrackingService initialized for container: {DATABASE_NAME}/{CONTAINER_NAME} using endpoint: {COSMOS_ENDPOINT[:20]}...") # Log partial endpoint
        except exceptions.CosmosResourceNotFoundError:
            logger.error(f"DelegationTrackingService: Database '{DATABASE_NAME}' or Container '{CONTAINER_NAME}' not found using endpoint {COSMOS_ENDPOINT[:20]}...")
            self._is_initialized = False
        except Exception as e:
            logger.error(f"DelegationTrackingService: Failed to initialize Cosmos DB client: {e}", exc_info=True)
            self._is_initialized = False

    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None
            self._is_initialized = False
            logger.info("DelegationTrackingService: Cosmos DB client closed.")

    async def _ensure_initialized(self):
        if not self._is_initialized:
            logger.warning("DelegationTrackingService was not initialized. Attempting to initialize now.")
            await self.initialize()
            if not self._is_initialized:
                raise ConnectionError("DelegationTrackingService could not be initialized.")

    async def track_delegation(
        self,
        agent_id: str,
        agent_name: Optional[str],
        user_id: Optional[str],
        delegation_query: Optional[str],
        source: DelegationSource,
        source_id: Optional[str],
        session_id: Optional[str],
        function_called: Optional[str],
        parameters: Optional[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> Optional[DelegationRecord]:
        await self._ensure_initialized()
        
        record_id = f"del_{uuid.uuid4()}"
        
        record = DelegationRecord(
            id=record_id,
            agentId=agent_id,
            agentName=agent_name,
            userId=user_id,
            delegationQuery=delegation_query,
            source=source,
            sourceId=source_id,
            sessionId=session_id,
            functionCalled=function_called,
            parameters=parameters,
            context=context,
            receivedAt=datetime.now(timezone.utc),
            status=DelegationStatus.RECEIVED,
            statusUpdatedAt=datetime.now(timezone.utc),
            createdAt=datetime.now(timezone.utc),
            modifiedAt=datetime.now(timezone.utc)
        )
        
        try:
            item_to_create = record.to_db_item()
            await self._container.create_item(body=item_to_create)
            logger.info(f"Delegation tracked: {record.id} for agent {agent_id} (function: {function_called})")
            return record
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to track delegation {record.id} (function: {function_called}): {e.message}", exc_info=False) # Log concise message
            logger.debug(f"Full error details for track_delegation {record.id}:", exc_info=True) # Log full trace for debug
        except ConnectionError as ce: # Catch specific ConnectionError from _ensure_initialized
            logger.error(f"ConnectionError during track_delegation for {record.id}: {ce}", exc_info=False)
        except Exception as e:
            logger.error(f"An unexpected error occurred while tracking delegation {record.id} (function: {function_called}): {e}", exc_info=True)
        return None

    async def update_delegation_status(
        self,
        delegation_id: str,
        agent_id: str,
        status: DelegationStatus,
        response_preview: Optional[str] = None,
        response_size: Optional[int] = None,
        error_message: Optional[str] = None,
        duration_ms: Optional[float] = None
    ) -> Optional[DelegationRecord]:
        await self._ensure_initialized()
        
        try:
            item = await self._container.read_item(item=delegation_id, partition_key=agent_id)
            
            item['status'] = status.value
            item['statusUpdatedAt'] = datetime.now(timezone.utc).isoformat() + "Z"
            item['modifiedAt'] = datetime.now(timezone.utc).isoformat() + "Z"
            item['version'] = item.get('version', 1) + 1

            if response_preview is not None:
                item['responsePreview'] = response_preview
            if response_size is not None:
                item['responseSize'] = response_size
            if error_message is not None:
                item['errorMessage'] = error_message
            if duration_ms is not None:
                item['durationMs'] = duration_ms
            
            updated_item = await self._container.replace_item(item=item, body=item)
            logger.info(f"Delegation status updated: {delegation_id} to {status.value}")
            return DelegationRecord(**updated_item)
        except exceptions.CosmosResourceNotFoundError:
            logger.error(f"Delegation record not found for update: {delegation_id} with agent_id {agent_id}")
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to update delegation {delegation_id} status: {e.message}", exc_info=False)
            logger.debug(f"Full error details for update_delegation_status {delegation_id}:", exc_info=True)
        except ConnectionError as ce:
            logger.error(f"ConnectionError during update_delegation_status for {delegation_id}: {ce}", exc_info=False)
        except Exception as e:
            logger.error(f"An unexpected error occurred while updating delegation {delegation_id}: {e}", exc_info=True)
        return None

    async def get_agent_metrics(
        self,
        agent_id: str,
        agent_name: str,
        period: str = "last_24_hours"
    ) -> Optional[AgentMetrics]:
        await self._ensure_initialized()
        
        end_time = datetime.now(timezone.utc)
        if period == "last_7_days":
            start_time = end_time - timedelta(days=7)
        elif period == "last_30_days":
            start_time = end_time - timedelta(days=30)
        else:
            start_time = end_time - timedelta(days=1)

        query = (
            "SELECT * FROM c WHERE c.agentId = @agent_id "
            "AND c.receivedAt >= @start_time AND c.receivedAt <= @end_time"
        )
        parameters = [
            {"name": "@agent_id", "value": agent_id},
            {"name": "@start_time", "value": start_time.isoformat() + "Z"},
            {"name": "@end_time", "value": end_time.isoformat() + "Z"},
        ]
        
        total_requests = 0
        successful_requests = 0
        failed_requests = 0
        response_times_ms = []
        
        try:
            items = []
            enable_cross_partition = PARTITION_KEY_PATH != "/agentId" # Only true if partition key is not agentId
            pk_value = agent_id if PARTITION_KEY_PATH == "/agentId" else None

            async for item_data in self._container.query_items(
                query=query, 
                parameters=parameters, 
                enable_cross_partition_query=enable_cross_partition, 
                partition_key=pk_value 
            ):
                items.append(DelegationRecord(**item_data))

            total_requests = len(items)
            for record in items:
                if record.status == DelegationStatus.COMPLETED:
                    successful_requests += 1
                    if record.durationMs is not None:
                        response_times_ms.append(record.durationMs)
                elif record.status == DelegationStatus.FAILED:
                    failed_requests += 1
            
            metrics = AgentMetrics(agentId=agent_id, agentName=agent_name, period=period)
            metrics.totalRequests = total_requests
            metrics.successfulRequests = successful_requests
            metrics.failedRequests = failed_requests
            
            if response_times_ms:
                response_times_ms.sort()
                metrics.averageResponseTimeMs = sum(response_times_ms) / len(response_times_ms) if response_times_ms else 0
                if response_times_ms: # Check if list is not empty before accessing indices
                    metrics.medianResponseTimeMs = response_times_ms[len(response_times_ms) // 2]
                    metrics.p95ResponseTimeMs = response_times_ms[int(len(response_times_ms) * 0.95)] if len(response_times_ms) > 19 else response_times_ms[-1]
                    metrics.p99ResponseTimeMs = response_times_ms[int(len(response_times_ms) * 0.99)] if len(response_times_ms) > 99 else response_times_ms[-1]

            if total_requests > 0:
                metrics.successRate = (successful_requests / total_requests) * 100
                metrics.errorRate = (failed_requests / total_requests) * 100
            
            logger.info(f"Retrieved metrics for agent {agent_id} for period {period}")
            return metrics
        except ConnectionError as ce:
            logger.error(f"ConnectionError during get_agent_metrics for {agent_id}: {ce}", exc_info=False)
        except exceptions.CosmosHttpResponseError as e:
            logger.error(f"Failed to get agent metrics for {agent_id}: {e.message}", exc_info=False)
            logger.debug(f"Full error details for get_agent_metrics {agent_id}:", exc_info=True)
        except Exception as e:
            logger.error(f"An unexpected error occurred while getting agent metrics for {agent_id}: {e}", exc_info=True)
        return AgentMetrics(agentId=agent_id, agentName=agent_name, period=period)
