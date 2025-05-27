"""SWOT/TOWS Analysis Agent

Handles SWOT analysis generation, TOWS strategy formulation, and guided analysis sessions.
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import uuid4

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatMessageContent, AuthorRole

from common.base_agent import BaseStratosAgent
from .plugins.swot_plugin import SwotPlugin


class SwotTowsAgent(BaseStratosAgent):
    """Agent responsible for SWOT/TOWS analysis and strategy generation"""
    
    def __init__(self):
        super().__init__(
            name="SWOT/TOWS Analysis Agent",
            description="Performs SWOT analysis, generates TOWS strategies, and guides analysis sessions",
            model="gpt-4"  # Use GPT-4 for complex strategic analysis
        )
        
        # Initialize SWOT plugin
        self.swot_plugin = SwotPlugin()
        self.kernel.add_plugin(self.swot_plugin, "SwotPlugin")
        
        # Session management
        self.active_sessions = {}
        
    async def _create_swot_agent(self) -> ChatCompletionAgent:
        """Create the SWOT analysis agent with specific instructions"""
        
        instructions = """You are a strategic analysis expert specializing in SWOT analysis and TOWS strategy generation.

Your capabilities include:
1. **SWOT Analysis Generation**: Create comprehensive SWOT analyses from various data sources
2. **TOWS Strategy Formulation**: Generate strategic options using TOWS matrix
3. **Guided Analysis Sessions**: Lead interactive SWOT/TOWS sessions
4. **Impact Assessment**: Score and prioritize SWOT items
5. **Pattern Recognition**: Identify strategic themes and patterns

When generating SWOT analyses:
- Draw from both subjective insights (CEO logs, feedback) and objective data (metrics, reports)
- Ensure items are specific, actionable, and strategically relevant
- Provide impact and certainty scores (1-10) for each item
- Reference source data when possible

For TOWS strategies:
- SO (Maxi-Maxi): Use strengths to maximize opportunities
- WO (Mini-Maxi): Minimize weaknesses by taking advantage of opportunities
- ST (Maxi-Mini): Use strengths to minimize threats
- WT (Mini-Mini): Minimize weaknesses and avoid threats

Available functions:
- GenerateSWOT: Create SWOT items from input data
- GenerateTOWS: Create TOWS strategies from SWOT analysis
- ScoreItems: Assess impact and certainty of SWOT items
- CreateSession: Start a guided analysis session
- UpdateSession: Continue guided session with new input"""

        return ChatCompletionAgent(
            service_id="swot_tows_agent",
            kernel=self.kernel,
            name="SwotTowsExpert",
            instructions=instructions
        )
        
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process SWOT/TOWS analysis requests"""
        
        try:
            query = request.get("query", "")
            context = request.get("context", {})
            user_id = request.get("user_id")
            session_id = request.get("session_id")
            
            # Create SWOT agent
            agent = await self._create_swot_agent()
            
            # Determine request type
            request_type = self._determine_request_type(query, context)
            
            if request_type == "generate_swot":
                return await self._generate_swot(agent, query, context, user_id)
            elif request_type == "generate_tows":
                return await self._generate_tows(agent, query, context, user_id)
            elif request_type == "start_session":
                return await self._start_guided_session(agent, query, context, user_id)
            elif request_type == "continue_session":
                return await self._continue_session(agent, query, context, user_id, session_id)
            else:
                # General SWOT/TOWS query
                return await self._handle_general_query(agent, query, context, user_id)
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"SWOT/TOWS analysis failed: {str(e)}"
            }
    
    def _determine_request_type(self, query: str, context: Dict[str, Any]) -> str:
        """Determine the type of SWOT/TOWS request"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["generate swot", "create swot", "swot analysis"]):
            return "generate_swot"
        elif any(word in query_lower for word in ["tows", "strategy", "strategic options"]):
            return "generate_tows"
        elif any(word in query_lower for word in ["start session", "guided", "interactive"]):
            return "start_session"
        elif context.get("session_id"):
            return "continue_session"
        else:
            return "general"
    
    async def _generate_swot(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Generate a SWOT analysis"""
        
        # Gather relevant data
        data_sources = context.get("data_sources", {})
        topic = context.get("topic", "general business analysis")
        
        # Use plugin to generate SWOT
        swot_result = await self.swot_plugin.generate_swot(
            topic=topic,
            subjective_data=data_sources.get("subjective", ""),
            objective_data=data_sources.get("objective", ""),
            user_id=user_id
        )
        
        # Parse result
        swot_data = json.loads(swot_result)
        
        # Create SWOT analysis object
        swot_analysis = {
            "id": str(uuid4()),
            "user_id": user_id,
            "title": f"SWOT Analysis: {topic}",
            "description": f"Generated from query: {query}",
            "items": swot_data["items"],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        return {
            "status": "success",
            "analysis_type": "swot",
            "data": swot_analysis,
            "summary": self._generate_swot_summary(swot_data["items"]),
            "next_steps": [
                "Generate TOWS strategies from this analysis",
                "Start a guided session to refine the analysis",
                "Export analysis to strategic canvas"
            ]
        }
    
    async def _generate_tows(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Generate TOWS strategies from SWOT analysis"""
        
        swot_id = context.get("swot_id")
        swot_items = context.get("swot_items", {})
        
        if not swot_items:
            return {
                "status": "error",
                "message": "No SWOT analysis provided. Please generate a SWOT analysis first."
            }
        
        # Use plugin to generate TOWS
        tows_result = await self.swot_plugin.generate_tows(
            strengths=swot_items.get("strengths", []),
            weaknesses=swot_items.get("weaknesses", []),
            opportunities=swot_items.get("opportunities", []),
            threats=swot_items.get("threats", [])
        )
        
        # Parse result
        tows_data = json.loads(tows_result)
        
        return {
            "status": "success",
            "analysis_type": "tows",
            "data": {
                "id": str(uuid4()),
                "swot_id": swot_id,
                "strategies": tows_data["strategies"],
                "created_at": datetime.utcnow().isoformat()
            },
            "summary": self._generate_tows_summary(tows_data["strategies"]),
            "next_steps": [
                "Prioritize strategies by impact",
                "Create action plans for selected strategies",
                "Link strategies to initiatives"
            ]
        }
    
    async def _start_guided_session(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Start a guided SWOT/TOWS analysis session"""
        
        session_id = str(uuid4())
        session_type = context.get("session_type", "swot")
        
        # Create session
        session = {
            "id": session_id,
            "user_id": user_id,
            "type": f"guided_{session_type}",
            "status": "active",
            "current_step": "introduction",
            "progress": 0,
            "data": {},
            "created_at": datetime.utcnow().isoformat()
        }
        
        self.active_sessions[session_id] = session
        
        # Generate first guidance
        guidance = await self.swot_plugin.get_session_guidance(
            session_type=session_type,
            current_step="introduction",
            session_data={}
        )
        
        return {
            "status": "success",
            "session_id": session_id,
            "session_type": f"guided_{session_type}",
            "current_step": "introduction",
            "guidance": guidance,
            "progress": 0,
            "actions": [
                {"type": "provide_context", "label": "Describe your business context"},
                {"type": "select_focus", "label": "Choose analysis focus area"},
                {"type": "skip_intro", "label": "Skip to analysis"}
            ]
        }
    
    async def _continue_session(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str, session_id: str) -> Dict[str, Any]:
        """Continue a guided analysis session"""
        
        if session_id not in self.active_sessions:
            return {
                "status": "error",
                "message": "Session not found or expired"
            }
        
        session = self.active_sessions[session_id]
        user_input = context.get("user_input", "")
        action = context.get("action", "")
        
        # Update session based on input
        next_step, progress = self._determine_next_step(session, action, user_input)
        session["current_step"] = next_step
        session["progress"] = progress
        
        # Generate guidance for next step
        guidance = await self.swot_plugin.get_session_guidance(
            session_type=session["type"],
            current_step=next_step,
            session_data=session["data"],
            user_input=user_input
        )
        
        # Check if session is complete
        if progress >= 100:
            result = await self._complete_session(session)
            del self.active_sessions[session_id]
            return result
        
        return {
            "status": "success",
            "session_id": session_id,
            "current_step": next_step,
            "guidance": guidance,
            "progress": progress,
            "session_data": session["data"]
        }
    
    async def _handle_general_query(self, agent: ChatCompletionAgent, query: str, context: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Handle general SWOT/TOWS queries"""
        
        # Let the agent handle the query directly
        response = await agent.invoke(f"""
Query: {query}
Context: {json.dumps(context, indent=2)}

Please provide strategic analysis guidance or answer the question about SWOT/TOWS analysis.
""")
        
        return {
            "status": "success",
            "response": response.content,
            "suggestions": [
                "Generate a SWOT analysis",
                "Start a guided analysis session",
                "View existing analyses"
            ]
        }
    
    def _generate_swot_summary(self, items: List[Dict[str, Any]]) -> str:
        """Generate a summary of SWOT items"""
        categories = {"strengths": [], "weaknesses": [], "opportunities": [], "threats": []}
        
        for item in items:
            category = item["category"].lower()
            if category in categories:
                categories[category].append(item["content"])
        
        summary_parts = []
        for cat, items_list in categories.items():
            if items_list:
                summary_parts.append(f"{len(items_list)} {cat}")
        
        return f"Generated SWOT analysis with {', '.join(summary_parts)}"
    
    def _generate_tows_summary(self, strategies: Dict[str, List[str]]) -> str:
        """Generate a summary of TOWS strategies"""
        total = sum(len(strats) for strats in strategies.values())
        return f"Generated {total} TOWS strategies across {len(strategies)} categories"
    
    def _determine_next_step(self, session: Dict[str, Any], action: str, user_input: str) -> tuple:
        """Determine next step in guided session"""
        current_step = session["current_step"]
        session_type = session["type"]
        
        # Simple state machine for guided sessions
        if session_type == "guided_swot":
            steps = ["introduction", "context", "strengths", "weaknesses", "opportunities", "threats", "review"]
        else:  # guided_tows
            steps = ["introduction", "swot_review", "so_strategies", "wo_strategies", "st_strategies", "wt_strategies", "prioritization"]
        
        current_index = steps.index(current_step) if current_step in steps else 0
        
        if action == "skip_intro":
            next_index = 2  # Skip to main content
        elif action == "back":
            next_index = max(0, current_index - 1)
        else:
            next_index = min(len(steps) - 1, current_index + 1)
        
        next_step = steps[next_index]
        progress = int((next_index / (len(steps) - 1)) * 100)
        
        # Store user input in session data
        if user_input and current_step != "introduction":
            if current_step not in session["data"]:
                session["data"][current_step] = []
            session["data"][current_step].append(user_input)
        
        return next_step, progress
    
    async def _complete_session(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Complete a guided session and generate final analysis"""
        
        if session["type"] == "guided_swot":
            # Generate final SWOT from session data
            swot_items = []
            for category in ["strengths", "weaknesses", "opportunities", "threats"]:
                if category in session["data"]:
                    for item in session["data"][category]:
                        swot_items.append({
                            "category": category[:-1],  # Remove 's'
                            "content": item,
                            "source": "guided_session"
                        })
            
            return {
                "status": "completed",
                "session_id": session["id"],
                "analysis_type": "swot",
                "data": {
                    "title": "Guided SWOT Analysis",
                    "items": swot_items,
                    "session_duration": "calculated_duration"
                },
                "next_steps": ["Generate TOWS strategies", "Export to canvas"]
            }
        else:
            # Complete TOWS session
            return {
                "status": "completed", 
                "session_id": session["id"],
                "analysis_type": "tows",
                "data": session["data"],
                "next_steps": ["Create action plans", "Link to initiatives"]
            }