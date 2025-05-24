"""
Agent invocation endpoints for the multi-agent system.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from datetime import datetime

from api.middleware.auth import get_current_user
from services.agent_client import StratOSAgentClient
from config.settings import get_settings

router = APIRouter()
settings = get_settings()


class AgentRequest(BaseModel):
    """Request model for agent invocation."""
    system: str = Field(..., description="Target agent system (strategic-foundation, analysis-intelligence, planning-execution)")
    type: str = Field(..., description="Request type for routing")
    action: Optional[str] = Field(None, description="Specific action to perform")
    data: Dict[str, Any] = Field(default_factory=dict, description="Request data")
    thread_id: Optional[UUID] = Field(None, description="Conversation thread ID for context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "system": "strategic-foundation",
                "type": "ceo_log",
                "action": "create_entry",
                "data": {
                    "text": "Met with board today. Key focus on AI transformation.",
                    "category": "strategic_planning"
                }
            }
        }


class AgentResponse(BaseModel):
    """Response model for agent invocation."""
    request_id: UUID = Field(default_factory=uuid4)
    system: str
    agent: str
    status: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Initialize agent client (will be properly initialized with lifespan)
agent_client: Optional[StratOSAgentClient] = None


@router.post("/invoke", response_model=AgentResponse)
async def invoke_agent(
    request: AgentRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> AgentResponse:
    """
    Invoke an agent in one of the three multi-agent systems.
    
    The request is routed to the appropriate system's router agent,
    which then delegates to specialized agents as needed.
    """
    if not agent_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent service not initialized"
        )
    
    try:
        # Add user context to request
        enriched_request = {
            **request.model_dump(),
            "user_context": {
                "user_id": current_user["sub"],
                "email": current_user.get("email"),
                "tenant_id": current_user.get("tid")
            }
        }
        
        # Invoke the agent system
        result = await agent_client.invoke_agent_system(
            system=request.system,
            request=enriched_request
        )
        
        return AgentResponse(
            system=request.system,
            agent=result.get("agent", "unknown"),
            status="success",
            data=result.get("data", {}),
            metadata={
                "duration_ms": result.get("duration_ms"),
                "tokens_used": result.get("tokens_used"),
                "model": result.get("model"),
                "thread_id": str(request.thread_id) if request.thread_id else None
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Log the error
        # TODO: Add proper logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent invocation failed: {str(e)}"
        )


@router.get("/systems")
async def list_agent_systems(
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """List available agent systems and their capabilities."""
    return {
        "systems": [
            {
                "id": "strategic-foundation",
                "name": "Strategic Foundation & Insights System",
                "description": "Manages CEO logs, vision/values, memory, and preferences",
                "agents": [
                    "StrategicContextRouter",
                    "CEOLogAgent",
                    "NorthStarAgent",
                    "MemoryRecallAgent",
                    "PreferenceLearningAgent"
                ]
            },
            {
                "id": "analysis-intelligence",
                "name": "Analysis & Intelligence System",
                "description": "Performs SWOT analysis, risk detection, and data linkage",
                "agents": [
                    "AnalysisOrchestrator",
                    "SWOTTOWSAgent",
                    "RiskOpportunityAgent",
                    "SOLinkageAgent"
                ]
            },
            {
                "id": "planning-execution",
                "name": "Planning & Execution System",
                "description": "Creates plans, manages resources, and tracks execution",
                "agents": [
                    "PlanningCoordinator",
                    "InitiativeGenerationAgent",
                    "ResourceOptimizationAgent",
                    "CanvasVisualizationAgent",
                    "AlignmentScoringAgent",
                    "ActionPlanningAgent"
                ]
            }
        ]
    }


@router.get("/threads/{thread_id}")
async def get_thread_history(
    thread_id: UUID,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Get conversation thread history."""
    if not agent_client:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Agent service not initialized"
        )
    
    try:
        # TODO: Implement thread history retrieval
        # This will fetch from Cosmos DB thread-message-store
        return {
            "thread_id": str(thread_id),
            "messages": [],
            "metadata": {
                "created_at": datetime.utcnow().isoformat(),
                "user_id": current_user["sub"]
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve thread history: {str(e)}"
        )