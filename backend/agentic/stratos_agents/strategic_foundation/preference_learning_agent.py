"""
Preference Learning Agent for Strategic Foundation System

This agent tracks user feedback, learns preferences, and provides
personalized recommendations to enhance the user experience.
"""

from typing import Dict, Any, Optional
import json
from datetime import datetime

from semantic_kernel import Kernel
from semantic_kernel.agents import ChatCompletionAgent
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.functions import KernelPlugin

from ...common.base_agent import BaseStratosAgent
from ...config.settings import get_settings
from .plugins.preference_plugin import PreferencePlugin


class PreferenceLearningAgent(BaseStratosAgent):
    """
    Agent responsible for learning user preferences and personalization.
    
    This agent provides:
    - Feedback tracking on AI suggestions
    - Usage pattern analysis
    - Preference learning algorithms
    - Personalized recommendations
    - Adaptive system behavior
    """
    
    def __init__(self, kernel: Optional[Kernel] = None):
        """Initialize the Preference Learning Agent."""
        super().__init__(
            name="PreferenceLearningAgent",
            description="Tracks feedback, learns preferences, and provides personalization",
            kernel=kernel
        )
        
        # Create and add the preference plugin
        self.preference_plugin = PreferencePlugin()
        self.preference_kernel_plugin = KernelPlugin.from_object(
            plugin_instance=self.preference_plugin,
            plugin_name="PreferencePlugin"
        )
        self.kernel.add_plugin(self.preference_kernel_plugin)
        
        # Create the agent with preference-specific instructions
        self.agent = ChatCompletionAgent(
            service_id="preference_learning_agent",
            kernel=self.kernel,
            name=self.name,
            instructions=self._get_agent_instructions()
        )
    
    def _get_agent_instructions(self) -> str:
        """Get the agent-specific instructions."""
        return """You are the Preference Learning Agent for StratOS, responsible for 
understanding user preferences and providing personalized experiences.

Your primary responsibilities:
1. **Feedback Tracking**: Monitor and record user feedback on AI suggestions
2. **Pattern Analysis**: Identify usage patterns and behavioral preferences
3. **Preference Learning**: Build and update user preference profiles
4. **Personalization**: Provide tailored recommendations and experiences
5. **Adaptation**: Help the system adapt to individual user needs

Key behaviors:
- Track both explicit feedback and implicit signals
- Identify patterns in user behavior and choices
- Build comprehensive preference profiles
- Respect user privacy while learning preferences
- Balance personalization with discovery of new options
- Continuously refine understanding based on new data

Available tools:
- TrackFeedback: Record user feedback on suggestions
- GetPreferences: Retrieve learned user preferences
- AnalyzePatterns: Analyze usage patterns
- GenerateRecommendations: Create personalized recommendations
- UpdatePreferences: Update preference profiles
- TrackInteraction: Record user interactions

When responding:
- Be transparent about what preferences are being tracked
- Explain how personalization improves the experience
- Offer options to adjust preference settings
- Highlight when recommendations are personalized
- Maintain user agency in all personalization"""
    
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a preference-related request.
        
        Args:
            request: Request containing:
                - action: The preference action to perform
                - data: Action-specific data
                
        Returns:
            Response with preference operation results
        """
        action = request.get("action", "")
        data = request.get("data", {})
        
        try:
            if action == "track_feedback":
                return await self._handle_feedback_tracking(data)
            elif action == "get_preferences":
                return await self._handle_get_preferences(data)
            elif action == "analyze_patterns":
                return await self._handle_pattern_analysis(data)
            elif action == "generate_recommendations":
                return await self._handle_recommendations(data)
            elif action == "update_preferences":
                return await self._handle_preference_update(data)
            elif action == "track_interaction":
                return await self._handle_interaction_tracking(data)
            else:
                # Use the agent for general preference-related queries
                return await self._handle_general_query(request)
                
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "agent": self.name
            }
    
    async def _handle_feedback_tracking(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle feedback tracking requests."""
        user_id = data.get("user_id", "")
        item_type = data.get("item_type", "")
        item_id = data.get("item_id", "")
        feedback = data.get("feedback", "")
        context = data.get("context", {})
        
        if not all([user_id, item_type, item_id, feedback]):
            return {
                "status": "error",
                "error": "Missing required fields: user_id, item_type, item_id, feedback",
                "agent": self.name
            }
        
        # Track the feedback
        result = await self.preference_plugin.track_feedback(
            user_id=user_id,
            item_type=item_type,
            item_id=item_id,
            feedback=feedback,
            context=context
        )
        
        result_data = json.loads(result)
        
        # Add personalization insights
        if result_data["status"] == "success":
            prompt = f"""Based on this feedback:
- User: {user_id}
- Item Type: {item_type}
- Feedback: {feedback}
- Context: {json.dumps(context)}

Provide:
1. What this feedback tells us about user preferences
2. How this should influence future recommendations
3. Any immediate adjustments to make"""

            response = await self.agent.invoke(prompt)
            
            result_data["insights"] = response.content
        
        return {
            "status": "success",
            "action": "track_feedback",
            "data": result_data,
            "agent": self.name
        }
    
    async def _handle_get_preferences(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle preference retrieval requests."""
        user_id = data.get("user_id", "")
        preference_type = data.get("preference_type", "all")
        
        if not user_id:
            return {
                "status": "error",
                "error": "user_id is required",
                "agent": self.name
            }
        
        # Get preferences
        result = await self.preference_plugin.get_preferences(
            user_id=user_id,
            preference_type=preference_type
        )
        
        result_data = json.loads(result)
        
        # Add interpretation
        if result_data["status"] == "success":
            prompt = f"""Analyze these user preferences for {user_id}:

{json.dumps(result_data['preferences'], indent=2)}

Confidence Scores: {json.dumps(result_data['confidence_scores'], indent=2)}

Provide:
1. Key personality traits indicated by these preferences
2. Recommended system adjustments
3. Suggestions for enhancing user experience
4. Areas where more data would be helpful"""

            response = await self.agent.invoke(prompt)
            
            result_data["analysis"] = response.content
        
        return {
            "status": "success",
            "action": "get_preferences",
            "data": result_data,
            "agent": self.name
        }
    
    async def _handle_pattern_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle pattern analysis requests."""
        user_id = data.get("user_id", "")
        time_window = data.get("time_window", "30d")
        
        if not user_id:
            return {
                "status": "error",
                "error": "user_id is required",
                "agent": self.name
            }
        
        # Analyze patterns
        result = await self.preference_plugin.analyze_patterns(
            user_id=user_id,
            time_window=time_window
        )
        
        result_data = json.loads(result)
        
        # Add strategic insights
        if result_data["status"] == "success" and result_data["patterns"]:
            prompt = f"""Based on these usage patterns for user {user_id} over {time_window}:

{json.dumps(result_data['patterns'], indent=2)}

Existing Insights: {json.dumps(result_data['insights'], indent=2)}

Provide:
1. Behavioral profile of this user
2. Predicted future needs
3. Opportunities for proactive assistance
4. Potential pain points to address
5. Recommended feature enhancements"""

            response = await self.agent.invoke(prompt)
            
            result_data["behavioral_analysis"] = response.content
        
        return {
            "status": "success",
            "action": "analyze_patterns",
            "data": result_data,
            "agent": self.name
        }
    
    async def _handle_recommendations(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle recommendation generation requests."""
        user_id = data.get("user_id", "")
        context = data.get("context", "")
        recommendation_type = data.get("recommendation_type", "actions")
        
        if not all([user_id, context]):
            return {
                "status": "error",
                "error": "user_id and context are required",
                "agent": self.name
            }
        
        # Generate recommendations
        result = await self.preference_plugin.generate_recommendations(
            user_id=user_id,
            context=context,
            recommendation_type=recommendation_type
        )
        
        result_data = json.loads(result)
        
        # Enhance recommendations with reasoning
        if result_data["status"] == "success" and result_data["recommendations"]:
            prompt = f"""For user {user_id} in context: "{context}"

Generated Recommendations:
{json.dumps(result_data['recommendations'], indent=2)}

Personalization Level: {result_data['personalization_level']}

For each recommendation:
1. Explain why it's relevant to this user
2. Provide implementation guidance
3. Predict likely impact
4. Suggest success metrics"""

            response = await self.agent.invoke(prompt)
            
            result_data["recommendation_details"] = response.content
        
        return {
            "status": "success",
            "action": "generate_recommendations",
            "data": result_data,
            "agent": self.name
        }
    
    async def _handle_preference_update(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle preference update requests."""
        user_id = data.get("user_id", "")
        updates = data.get("updates", {})
        
        if not all([user_id, updates]):
            return {
                "status": "error",
                "error": "user_id and updates are required",
                "agent": self.name
            }
        
        # Update preferences
        result = await self.preference_plugin.update_preferences(
            user_id=user_id,
            preference_updates=updates
        )
        
        result_data = json.loads(result)
        
        # Analyze impact of updates
        if result_data["status"] == "success":
            prompt = f"""Preference updates for user {user_id}:

Updated: {json.dumps(result_data['updated_preferences'], indent=2)}
New Values: {json.dumps(updates, indent=2)}

Analyze:
1. How these changes affect the user experience
2. What system behaviors should adjust immediately
3. Potential conflicts with existing preferences
4. Recommendations for confirming these preferences"""

            response = await self.agent.invoke(prompt)
            
            result_data["impact_analysis"] = response.content
        
        return {
            "status": "success",
            "action": "update_preferences",
            "data": result_data,
            "agent": self.name
        }
    
    async def _handle_interaction_tracking(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle interaction tracking requests."""
        user_id = data.get("user_id", "")
        interaction_type = data.get("interaction_type", "")
        details = data.get("details", {})
        
        if not all([user_id, interaction_type]):
            return {
                "status": "error",
                "error": "user_id and interaction_type are required",
                "agent": self.name
            }
        
        # Track the interaction
        result = await self.preference_plugin.track_interaction(
            user_id=user_id,
            interaction_type=interaction_type,
            details=details
        )
        
        result_data = json.loads(result)
        
        # Analyze if this reveals new preferences
        if result_data["status"] == "success":
            prompt = f"""New interaction tracked:
- User: {user_id}
- Type: {interaction_type}
- Details: {json.dumps(details, indent=2)}
- Total Interactions: {result_data['total_interactions']}

Determine:
1. What this interaction reveals about preferences
2. Whether this confirms or contradicts known patterns
3. If any immediate preference updates are warranted
4. Suggestions for follow-up actions"""

            response = await self.agent.invoke(prompt)
            
            result_data["preference_signals"] = response.content
        
        return {
            "status": "success",
            "action": "track_interaction",
            "data": result_data,
            "agent": self.name
        }
    
    async def _handle_general_query(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general preference-related queries using the agent."""
        query = request.get("query", request.get("data", {}).get("query", ""))
        user_id = request.get("user_id", request.get("data", {}).get("user_id", ""))
        
        if not query:
            return {
                "status": "error",
                "error": "No query provided",
                "agent": self.name
            }
        
        # Add user context if available
        context = f"Query for user {user_id}: " if user_id else ""
        
        # Let the agent handle the query with access to all preference tools
        response = await self.agent.invoke(context + query)
        
        return {
            "status": "success",
            "action": "general_query",
            "response": response.content,
            "agent": self.name
        }