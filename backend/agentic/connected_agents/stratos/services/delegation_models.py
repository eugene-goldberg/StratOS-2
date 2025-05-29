# services/delegation_models.py
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from enum import Enum
import uuid

class DelegationStatus(str, Enum):
    RECEIVED = "received"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class DelegationSource(str, Enum):
    ORCHESTRATOR = "orchestrator"
    USER_DIRECT = "user_direct"
    AGENT_INTERNAL = "agent_internal" # For agent-initiated sub-tasks if any
    UNKNOWN = "unknown"

class DelegationRecord(BaseModel):
    """Model for an agent delegation record in Cosmos DB"""
    # Core Fields from Decorator
    id: str = Field(default_factory=lambda: f"del_{uuid.uuid4()}", description="Unique delegation ID (partition key)")
    agentId: str = Field(..., description="Identifier of the agent executing the delegation") # Consider if this should be the partition key if many agents share the container
    agentName: Optional[str] = Field(None, description="Name of the agent")
    userId: Optional[str] = Field(None, description="User ID associated with this delegation")
    delegationQuery: Optional[str] = Field(None, description="High-level query or task description")
    source: DelegationSource = Field(DelegationSource.UNKNOWN, description="Source of the delegation")
    sourceId: Optional[str] = Field(None, description="Identifier of the source (e.g., orchestrator name/ID)")
    sessionId: Optional[str] = Field(None, description="Session ID for context")
    functionCalled: Optional[str] = Field(None, description="The specific function/tool called")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Parameters passed to the function")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context for the delegation")
    
    # Tracking Fields
    receivedAt: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when delegation was first tracked")
    status: DelegationStatus = Field(DelegationStatus.RECEIVED, description="Current status of the delegation")
    statusUpdatedAt: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of the last status update")
    
    # Execution Outcome
    responsePreview: Optional[str] = Field(None, description="Preview of the function's response")
    responseSize: Optional[int] = Field(None, description="Size of the response in bytes")
    errorMessage: Optional[str] = Field(None, description="Error message if the delegation failed")
    durationMs: Optional[float] = Field(None, description="Duration of the function execution in milliseconds")

    # Versioning and Timestamps
    etag: Optional[str] = Field(None, alias="_etag", description="Cosmos DB ETag for optimistic concurrency")
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    modifiedAt: datetime = Field(default_factory=datetime.utcnow)
    version: int = Field(1)

    class Config:
        use_enum_values = True # Store enum values as strings
        json_encoders = {
            datetime: lambda v: v.isoformat() + "Z" # ISO 8601 format with Z for UTC
        }

    def to_db_item(self) -> Dict[str, Any]:
        """Prepares the model for Cosmos DB, ensuring 'id' is the document id."""
        item = self.dict(by_alias=True) # by_alias=True handles _etag
        # Cosmos DB expects 'id' to be the document ID. Pydantic might put it inside if a field is named 'id'.
        # This model has id as a direct field, so it should be fine.
        if 'agentId' in item and 'id' in item: # Example: Ensure partition key is not also named 'id' if it's different
            pass # `id` is already the document ID, `agentId` could be partition key
        return item

class AgentMetrics(BaseModel):
    """Model for agent performance metrics derived from delegation tracking."""
    agentId: str
    agentName: str
    period: str # e.g., "last_24_hours"
    totalRequests: int = 0
    successfulRequests: int = 0
    failedRequests: int = 0
    averageResponseTimeMs: float = 0.0
    medianResponseTimeMs: float = 0.0
    p95ResponseTimeMs: float = 0.0
    p99ResponseTimeMs: float = 0.0
    successRate: float = 0.0
    errorRate: float = 0.0
    uniqueUsers: int = 0
    commonErrors: List[Dict[str, Any]] = Field(default_factory=list) # e.g., [{"error": "...", "count": ...}]
    peakHours: List[int] = Field(default_factory=list) # e.g., [10, 11, 15] (UTC hours)
    topFunctions: List[Dict[str, Any]] = Field(default_factory=list) # e.g., [{"function": "...", "count": ...}]