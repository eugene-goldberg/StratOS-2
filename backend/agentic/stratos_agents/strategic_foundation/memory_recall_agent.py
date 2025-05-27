"""
Memory & Recall Agent for Strategic Foundation System

This agent manages semantic memory, context retrieval, pattern recognition,
and historical analysis for the StratOS platform.
"""

from typing import Dict, Any, Optional
import json
from datetime import datetime

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.functions import KernelPlugin
from semantic_kernel.memory import SemanticTextMemory
from semantic_kernel.connectors.memory.azure_ai_search import AzureAISearchMemoryStore

from ...common.base_agent import BaseStratosAgent
from ...config.settings import get_settings
from .plugins.memory_plugin import MemoryPlugin


class MemoryRecallAgent(BaseStratosAgent):
    """
    Agent responsible for memory management and context retrieval.
    
    This agent provides:
    - Semantic search across all strategic data
    - Pattern recognition in historical data
    - Context retrieval for decision support
    - Historical analysis and insights
    - Similar situation identification
    """
    
    def __init__(self, kernel: Optional[Kernel] = None):
        """Initialize the Memory & Recall Agent."""
        super().__init__(
            name="MemoryRecallAgent",
            description="Manages semantic memory, context retrieval, and pattern recognition",
            kernel=kernel
        )
        
        # Initialize memory store (will use Azure AI Search in production)
        self.memory_store = self._initialize_memory_store()
        
        # Create and add the memory plugin
        self.memory_plugin = MemoryPlugin(memory_store=self.memory_store)
        self.memory_kernel_plugin = KernelPlugin.from_object(
            plugin_instance=self.memory_plugin,
            plugin_name="MemoryPlugin"
        )
        self.kernel.add_plugin(self.memory_kernel_plugin)
        
        # Create the agent with memory-specific instructions
        self.agent = ChatCompletionAgent(
            service_id="memory_recall_agent",
            kernel=self.kernel,
            name=self.name,
            instructions=self._get_agent_instructions()
        )
    
    def _initialize_memory_store(self) -> Optional[SemanticTextMemory]:
        """Initialize the semantic memory store."""
        settings = get_settings()
        
        # In production, this would initialize Azure AI Search
        # For now, return None (plugin will handle mock data)
        if settings.use_azure_ai_search:
            try:
                # This would be the real implementation:
                # memory_store = AzureAISearchMemoryStore(
                #     endpoint=settings.azure_search_endpoint,
                #     credential=AzureKeyCredential(settings.azure_search_api_key)
                # )
                # return SemanticTextMemory(
                #     memory_store=memory_store,
                #     embeddings_generator=text_embedding_service
                # )
                return None
            except Exception as e:
                print(f"Failed to initialize Azure AI Search: {e}")
                return None
        
        return None
    
    def _get_agent_instructions(self) -> str:
        """Get the agent-specific instructions."""
        return """You are the Memory & Recall Agent for StratOS, responsible for managing 
organizational memory and providing intelligent context retrieval.

Your primary responsibilities:
1. **Context Retrieval**: Search and retrieve relevant information based on semantic queries
2. **Pattern Recognition**: Identify patterns, trends, and correlations in historical data
3. **Historical Analysis**: Provide insights from past decisions, actions, and outcomes
4. **Similarity Matching**: Find similar situations, decisions, or contexts from history
5. **Memory Management**: Store important contexts and maintain the knowledge base

Key behaviors:
- Always search for relevant context before making recommendations
- Identify patterns that could inform current decisions
- Highlight lessons learned from similar past situations
- Maintain connections between related pieces of information
- Provide evidence-based insights from historical data

Available tools:
- RetrieveContext: Search for relevant information
- RecognizePatterns: Identify patterns in data
- AnalyzeHistory: Perform historical analysis
- StoreContext: Save important information
- FindSimilar: Locate similar situations or decisions

When responding:
- Cite specific examples from memory when relevant
- Highlight patterns or trends you've identified
- Connect current situations to historical precedents
- Suggest lessons learned from past experiences
- Be explicit about confidence levels in pattern recognition"""
    
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a memory-related request.
        
        Args:
            request: Request containing:
                - action: The memory action to perform
                - data: Action-specific data
                
        Returns:
            Response with memory operation results
        """
        action = request.get("action", "")
        data = request.get("data", {})
        
        try:
            if action == "retrieve_context":
                return await self._handle_context_retrieval(data)
            elif action == "analyze_patterns":
                return await self._handle_pattern_analysis(data)
            elif action == "find_similar":
                return await self._handle_similarity_search(data)
            elif action == "store_context":
                return await self._handle_context_storage(data)
            elif action == "analyze_history":
                return await self._handle_historical_analysis(data)
            else:
                # Use the agent for general memory-related queries
                return await self._handle_general_query(request)
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "agent": self.name
            }
    
    async def _handle_context_retrieval(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle context retrieval requests."""
        query = data.get("query", "")
        context_type = data.get("context_type", "all")
        limit = data.get("limit", 5)
        
        # Use the plugin to retrieve context
        result = await self.memory_plugin.retrieve_context(
            query=query,
            limit=limit,
            context_type=context_type
        )
        
        result_data = json.loads(result)
        
        # Enhance with agent analysis if contexts were found
        if result_data["status"] == "success" and result_data["results"]:
            prompt = f"""Based on the retrieved contexts for query '{query}':

{json.dumps(result_data['results'], indent=2)}

Provide a brief analysis of:
1. Key themes across these contexts
2. Most relevant insights for current situation
3. Recommended actions based on this historical context"""

            response = await self.agent.invoke(prompt)
            
            result_data["analysis"] = response.content
        
        return {
            "status": "success",
            "action": "retrieve_context",
            "data": result_data,
            "agent": self.name
        }
    
    async def _handle_pattern_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pattern analysis requests."""
        data_type = data.get("data_type", "ceo_entries")
        time_range = data.get("time_range", "30d")
        pattern_type = data.get("pattern_type", "frequency")
        
        # Use the plugin to recognize patterns
        result = await self.memory_plugin.recognize_patterns(
            data_type=data_type,
            time_range=time_range,
            pattern_type=pattern_type
        )
        
        result_data = json.loads(result)
        
        # Add strategic interpretation
        if result_data["status"] == "success" and result_data["patterns"]:
            prompt = f"""Analyze these patterns found in {data_type} over {time_range}:

{json.dumps(result_data['patterns'], indent=2)}

Provide:
1. Strategic implications of these patterns
2. Potential risks or opportunities they indicate
3. Recommended actions based on these patterns
4. Areas requiring attention"""

            response = await self.agent.invoke(prompt)
            
            result_data["strategic_analysis"] = response.content
        
        return {
            "status": "success",
            "action": "analyze_patterns",
            "data": result_data,
            "agent": self.name
        }
    
    async def _handle_similarity_search(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle similarity search requests."""
        reference_text = data.get("reference_text", "")
        search_type = data.get("search_type", "all")
        limit = data.get("limit", 3)
        
        # Use the plugin to find similar items
        result = await self.memory_plugin.find_similar(
            reference_text=reference_text,
            search_type=search_type,
            limit=limit
        )
        
        result_data = json.loads(result)
        
        # Add lessons learned analysis
        if result_data["status"] == "success" and result_data["similar_items"]:
            prompt = f"""Based on these similar situations to '{reference_text[:100]}...':

{json.dumps(result_data['similar_items'], indent=2)}

Extract:
1. Key lessons learned from these similar situations
2. What worked well and what didn't
3. Recommendations for the current situation
4. Potential pitfalls to avoid"""

            response = await self.agent.invoke(prompt)
            
            result_data["lessons_learned"] = response.content
        
        return {
            "status": "success",
            "action": "find_similar",
            "data": result_data,
            "agent": self.name
        }
    
    async def _handle_context_storage(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle context storage requests."""
        context_text = data.get("text", "")
        context_type = data.get("type", "general")
        metadata = data.get("metadata", {})
        
        # First, analyze the context for key information
        prompt = f"""Analyze this {context_type} context for storage:

{context_text}

Extract:
1. Key concepts and entities
2. Strategic relevance
3. Potential future value
4. Related topics or areas"""

        response = await self.agent.invoke(prompt)
        
        # Add analysis to metadata
        metadata["ai_analysis"] = response.content
        metadata["stored_by"] = self.name
        
        # Store using the plugin
        result = await self.memory_plugin.store_context(
            context_text=context_text,
            context_type=context_type,
            metadata=metadata
        )
        
        result_data = json.loads(result)
        result_data["analysis"] = response.content
        
        return {
            "status": "success",
            "action": "store_context",
            "data": result_data,
            "agent": self.name
        }
    
    async def _handle_historical_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle historical analysis requests."""
        analysis_type = data.get("analysis_type", "evolution")
        entity_id = data.get("entity_id")
        time_period = data.get("time_period", "90d")
        
        # Use the plugin for historical analysis
        result = await self.memory_plugin.analyze_history(
            analysis_type=analysis_type,
            entity_id=entity_id,
            time_period=time_period
        )
        
        result_data = json.loads(result)
        
        # Add forward-looking insights
        if result_data["status"] == "success":
            prompt = f"""Based on this historical analysis of {analysis_type} over {time_period}:

{json.dumps(result_data, indent=2)}

Provide:
1. Key trends to watch going forward
2. Predicted evolution based on historical patterns
3. Strategic recommendations
4. Critical success factors for the future"""

            response = await self.agent.invoke(prompt)
            
            result_data["future_insights"] = response.content
        
        return {
            "status": "success",
            "action": "analyze_history",
            "data": result_data,
            "agent": self.name
        }
    
    async def _handle_general_query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general memory-related queries using the agent."""
        query = request.get("query", request.get("data", {}).get("query", ""))
        
        if not query:
            return {
                "status": "error",
                "error": "No query provided",
                "agent": self.name
            }
        
        # Let the agent handle the query with access to all memory tools
        response = await self.agent.invoke(query)
        
        return {
            "status": "success",
            "action": "general_query",
            "response": response.content,
            "agent": self.name
        }