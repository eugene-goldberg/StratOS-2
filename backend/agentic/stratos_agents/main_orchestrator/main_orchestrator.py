"""Main Orchestrator Agent implementation for StratOS Unified MAS."""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import UUID

from semantic_kernel import Kernel
from semantic_kernel.agents import AzureAIAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.exceptions import KernelException

from .router import DeterministicRouter, RoutingDecision
from .config import (
    AgentName, WORKFLOW_DEFINITIONS, ERROR_MESSAGES, RETRY_CONFIG
)


logger = logging.getLogger(__name__)


class MainOrchestratorAgent:
    """
    Main Orchestrator Agent for the Unified StratOS Multi-Agent System.
    
    This agent serves as the primary entry point for all requests,
    routing them to appropriate specialized agents or workflows.
    """
    
    def __init__(self, 
                 kernel: Kernel,
                 agent_client: Any,  # Azure AI Agent Service client
                 config: Optional[Dict] = None):
        """
        Initialize the Main Orchestrator Agent.
        
        Args:
            kernel: Semantic Kernel instance
            agent_client: Azure AI Agent Service client for invoking other agents
            config: Optional configuration overrides
        """
        self.kernel = kernel
        self.agent_client = agent_client
        self.config = config or {}
        self.router = DeterministicRouter()
        self._initialize_agent_registry()
        
        # Track active workflows
        self.active_workflows: Dict[str, Dict] = {}
        
        logger.info("Main Orchestrator Agent initialized")
    
    def _initialize_agent_registry(self):
        """Initialize registry of available agents."""
        self.agent_registry = {
            agent.value: {
                "name": agent.value,
                "available": True,  # Will be updated based on health checks
                "last_health_check": None
            }
            for agent in AgentName
        }
    
    async def process_request(self,
                            request: Dict,
                            session_context: Optional[Dict] = None) -> Dict:
        """
        Process an incoming request by routing to appropriate agent(s).
        
        Args:
            request: The incoming request dictionary with:
                - user_id: User identifier
                - session_id/thread_id: Conversation identifier
                - task_type: Optional explicit task type
                - payload: Request data
                - user_query: Optional natural language query
            session_context: Optional session context with conversation history
            
        Returns:
            Response dictionary with results
        """
        start_time = datetime.utcnow()
        
        try:
            # Validate request
            validation_error = self._validate_request(request)
            if validation_error:
                return self._create_error_response(validation_error)
            
            # Get routing decision
            decision = self.router.route(request, session_context)
            logger.info(f"Routing decision: {decision.to_dict()}")
            
            # Handle based on route type
            if decision.route_type == "agent":
                response = await self._invoke_agent(decision, request, session_context)
            elif decision.route_type == "workflow":
                response = await self._execute_workflow(decision, request, session_context)
            elif decision.route_type == "clarification":
                response = self._create_clarification_response(decision)
            else:  # error
                response = self._create_error_response(decision.error_message)
            
            # Add metadata
            response["metadata"] = {
                "orchestrator_version": "1.0",
                "routing_confidence": decision.confidence,
                "routing_reasoning": decision.reasoning,
                "processing_time_ms": int((datetime.utcnow() - start_time).total_seconds() * 1000)
            }
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}", exc_info=True)
            return self._create_error_response(ERROR_MESSAGES["general_error"])
    
    async def _invoke_agent(self,
                          decision: RoutingDecision,
                          request: Dict,
                          session_context: Optional[Dict]) -> Dict:
        """Invoke a single agent."""
        agent_name = decision.target
        
        # Check agent availability
        if not self._is_agent_available(agent_name):
            return self._create_error_response(
                ERROR_MESSAGES["agent_not_available"]
            )
        
        # Prepare agent request
        agent_request = {
            "user_id": request.get("user_id"),
            "thread_id": request.get("thread_id") or request.get("session_id"),
            "action": request.get("task_type", "process"),
            "data": decision.params,
            "context": session_context
        }
        
        # Invoke agent with retry logic
        for attempt in range(RETRY_CONFIG["max_retries"]):
            try:
                logger.info(f"Invoking agent {agent_name} (attempt {attempt + 1})")
                
                # Use Azure AI Agent Service to invoke the agent
                response = await self.agent_client.invoke_agent(
                    agent_name=agent_name,
                    request_body=agent_request
                )
                
                # Process response
                if response.get("success", False):
                    return {
                        "success": True,
                        "agent": agent_name,
                        "result": response.get("result"),
                        "data": response.get("data", {})
                    }
                else:
                    error_msg = response.get("error", "Agent returned unsuccessful response")
                    logger.warning(f"Agent {agent_name} returned error: {error_msg}")
                    
                    # Don't retry for logical errors
                    if "validation" in error_msg.lower():
                        return self._create_error_response(error_msg)
                
            except Exception as e:
                logger.error(f"Error invoking agent {agent_name}: {str(e)}")
                
                # Check if we should retry
                if attempt < RETRY_CONFIG["max_retries"] - 1:
                    wait_time = RETRY_CONFIG["backoff_factor"] ** attempt
                    logger.info(f"Retrying after {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    return self._create_error_response(
                        f"Failed to invoke agent after {RETRY_CONFIG['max_retries']} attempts"
                    )
        
        return self._create_error_response(ERROR_MESSAGES["agent_not_available"])
    
    async def _execute_workflow(self,
                              decision: RoutingDecision,
                              request: Dict,
                              session_context: Optional[Dict]) -> Dict:
        """Execute a multi-step workflow."""
        workflow_name = decision.target
        workflow_def = WORKFLOW_DEFINITIONS.get(workflow_name)
        
        if not workflow_def:
            return self._create_error_response(f"Workflow {workflow_name} not found")
        
        # Create workflow instance ID
        workflow_id = f"{workflow_name}_{request.get('session_id', 'default')}_{datetime.utcnow().isoformat()}"
        
        # Initialize workflow tracking
        self.active_workflows[workflow_id] = {
            "name": workflow_name,
            "started_at": datetime.utcnow(),
            "current_step": 0,
            "results": [],
            "status": "running"
        }
        
        try:
            workflow_results = []
            workflow_context = {
                **(session_context or {}),
                "workflow_id": workflow_id,
                "workflow_name": workflow_name
            }
            
            # Execute each step in the workflow
            for step_idx, step in enumerate(workflow_def["steps"]):
                self.active_workflows[workflow_id]["current_step"] = step_idx
                
                agent_name = step["agent"].value
                action = step.get("action", "process")
                
                logger.info(f"Workflow {workflow_id} - Step {step_idx + 1}: {agent_name}.{action}")
                
                # Prepare step request
                step_request = {
                    "user_id": request.get("user_id"),
                    "thread_id": request.get("thread_id") or request.get("session_id"),
                    "action": action,
                    "data": {
                        **decision.params,
                        "workflow_context": workflow_context,
                        "previous_results": workflow_results
                    }
                }
                
                # Create routing decision for the step
                step_decision = RoutingDecision(
                    route_type="agent",
                    target=agent_name,
                    params=step_request["data"]
                )
                
                # Invoke the agent
                step_response = await self._invoke_agent(
                    step_decision,
                    step_request,
                    workflow_context
                )
                
                if not step_response.get("success"):
                    # Workflow step failed
                    self.active_workflows[workflow_id]["status"] = "failed"
                    return self._create_error_response(
                        f"Workflow failed at step {step_idx + 1}: {step_response.get('error')}"
                    )
                
                # Store step result
                workflow_results.append({
                    "step": step_idx + 1,
                    "agent": agent_name,
                    "action": action,
                    "result": step_response.get("result")
                })
                
                # Update workflow context with step results
                workflow_context[f"step_{step_idx + 1}_result"] = step_response.get("result")
            
            # Workflow completed successfully
            self.active_workflows[workflow_id]["status"] = "completed"
            self.active_workflows[workflow_id]["results"] = workflow_results
            
            # Aggregate results
            aggregated_result = self._aggregate_workflow_results(
                workflow_name,
                workflow_results
            )
            
            return {
                "success": True,
                "workflow": workflow_name,
                "workflow_id": workflow_id,
                "result": aggregated_result,
                "steps_completed": len(workflow_results),
                "detailed_results": workflow_results
            }
            
        except Exception as e:
            logger.error(f"Workflow {workflow_id} failed: {str(e)}", exc_info=True)
            self.active_workflows[workflow_id]["status"] = "error"
            return self._create_error_response(ERROR_MESSAGES["workflow_error"])
        
        finally:
            # Clean up completed workflow after some time
            # In production, this would be handled by a background task
            if workflow_id in self.active_workflows:
                if self.active_workflows[workflow_id]["status"] in ["completed", "failed", "error"]:
                    # Schedule cleanup (simplified for this example)
                    pass
    
    def _aggregate_workflow_results(self,
                                  workflow_name: str,
                                  results: List[Dict]) -> Dict:
        """Aggregate results from workflow steps into a unified response."""
        # Workflow-specific aggregation logic
        if workflow_name == "STRATEGIC_PLANNING_WORKFLOW":
            return {
                "context": results[0]["result"] if results else {},
                "analysis": results[1]["result"] if len(results) > 1 else {},
                "initiatives": results[2]["result"] if len(results) > 2 else [],
                "summary": results[3]["result"] if len(results) > 3 else ""
            }
        elif workflow_name == "FULL_STRATEGIC_REVIEW_WORKFLOW":
            return {
                "recent_logs": results[0]["result"] if results else [],
                "alignment_status": results[1]["result"] if len(results) > 1 else {},
                "swot_analysis": results[2]["result"] if len(results) > 2 else {},
                "new_initiatives": results[3]["result"] if len(results) > 3 else []
            }
        else:
            # Generic aggregation
            return {
                f"step_{i+1}": result["result"]
                for i, result in enumerate(results)
            }
    
    def _is_agent_available(self, agent_name: str) -> bool:
        """Check if an agent is available."""
        # In production, this would perform actual health checks
        # For now, assume all registered agents are available
        return agent_name in self.agent_registry
    
    def _validate_request(self, request: Dict) -> Optional[str]:
        """Validate incoming request."""
        if not request:
            return "Request cannot be empty"
        
        if "user_id" not in request:
            return "user_id is required"
        
        # Must have either task_type, user_query, or payload
        if not any(k in request for k in ["task_type", "user_query", "payload"]):
            return "Request must include task_type, user_query, or payload"
        
        return None
    
    def _create_error_response(self, error_message: str) -> Dict:
        """Create a standardized error response."""
        return {
            "success": False,
            "error": error_message,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _create_clarification_response(self, decision: RoutingDecision) -> Dict:
        """Create a clarification response."""
        return {
            "success": True,
            "requires_clarification": True,
            "clarification_question": decision.clarification_question,
            "routing_confidence": decision.confidence,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_workflow_status(self, workflow_id: str) -> Dict:
        """Get the status of an active workflow."""
        if workflow_id not in self.active_workflows:
            return {
                "success": False,
                "error": f"Workflow {workflow_id} not found"
            }
        
        workflow = self.active_workflows[workflow_id]
        return {
            "success": True,
            "workflow_id": workflow_id,
            "name": workflow["name"],
            "status": workflow["status"],
            "current_step": workflow["current_step"],
            "started_at": workflow["started_at"].isoformat(),
            "results_count": len(workflow["results"])
        }
    
    async def health_check(self) -> Dict:
        """Perform health check on the orchestrator and registered agents."""
        health_status = {
            "orchestrator": "healthy",
            "router": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "agents": {}
        }
        
        # Check each registered agent
        # In production, this would make actual health check calls
        for agent_name in self.agent_registry:
            health_status["agents"][agent_name] = {
                "status": "healthy",  # Simplified for now
                "available": True
            }
        
        return health_status