"""
Preference Learning Plugin for Strategic Foundation System

This plugin tracks user feedback, learns preferences, and provides
personalized recommendations based on usage patterns.
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
from collections import defaultdict
from uuid import UUID

from semantic_kernel.functions import kernel_function
from semantic_kernel.kernel_pydantic import KernelBaseModel


class PreferencePlugin(KernelBaseModel):
    """Plugin for preference learning and personalization in the Strategic Foundation system."""
    
    def __init__(self):
        """Initialize the preference plugin."""
        super().__init__()
        # In production, this would connect to a real preference store
        self._preference_store: Dict[str, Dict[str, Any]] = {}
        self._feedback_history: List[Dict[str, Any]] = []
        self._interaction_patterns: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    
    @kernel_function(
        description="Track user feedback on AI suggestions or actions",
        name="TrackFeedback"
    )
    async def track_feedback(
        self,
        user_id: str,
        item_type: str,
        item_id: str,
        feedback: str,
        context: Dict[str, Any] = None
    ) -> str:
        """
        Track user feedback on AI suggestions, recommendations, or actions.
        
        Args:
            user_id: ID of the user providing feedback
            item_type: Type of item (suggestion, recommendation, analysis, action)
            item_id: ID of the specific item
            feedback: Feedback type (accepted, rejected, modified, rated)
            context: Additional context about the feedback
        
        Returns:
            JSON string confirming feedback tracking
        """
        try:
            feedback_entry = {
                "id": f"feedback_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                "user_id": user_id,
                "item_type": item_type,
                "item_id": item_id,
                "feedback": feedback,
                "timestamp": datetime.utcnow().isoformat(),
                "context": context or {}
            }
            
            self._feedback_history.append(feedback_entry)
            
            # Update preference scores based on feedback
            await self._update_preferences(user_id, item_type, feedback, context)
            
            return json.dumps({
                "status": "success",
                "feedback_id": feedback_entry["id"],
                "message": "Feedback tracked successfully",
                "preference_updated": True
            })
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to track feedback: {str(e)}"
            })
    
    @kernel_function(
        description="Get learned preferences for a user",
        name="GetPreferences"
    )
    async def get_preferences(
        self,
        user_id: str,
        preference_type: str = "all"
    ) -> str:
        """
        Retrieve learned preferences for a specific user.
        
        Args:
            user_id: ID of the user
            preference_type: Type of preferences to retrieve (all, communication, analysis, planning)
        
        Returns:
            JSON string containing user preferences
        """
        try:
            user_prefs = self._preference_store.get(user_id, {})
            
            if preference_type != "all":
                user_prefs = {k: v for k, v in user_prefs.items() 
                             if k.startswith(preference_type)}
            
            # Calculate preference summary
            preference_summary = {
                "communication_style": user_prefs.get("communication_style", "balanced"),
                "detail_level": user_prefs.get("detail_level", "medium"),
                "risk_tolerance": user_prefs.get("risk_tolerance", "moderate"),
                "decision_speed": user_prefs.get("decision_speed", "deliberate"),
                "preferred_formats": user_prefs.get("preferred_formats", ["text", "charts"]),
                "focus_areas": user_prefs.get("focus_areas", []),
                "avoided_topics": user_prefs.get("avoided_topics", [])
            }
            
            return json.dumps({
                "status": "success",
                "user_id": user_id,
                "preferences": preference_summary,
                "confidence_scores": self._calculate_confidence_scores(user_id),
                "last_updated": user_prefs.get("last_updated", "never")
            })
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to retrieve preferences: {str(e)}"
            })
    
    @kernel_function(
        description="Analyze usage patterns to identify preferences",
        name="AnalyzePatterns"
    )
    async def analyze_patterns(
        self,
        user_id: str,
        time_window: str = "30d"
    ) -> str:
        """
        Analyze user interaction patterns to identify preferences.
        
        Args:
            user_id: ID of the user
            time_window: Time window for analysis (7d, 30d, 90d)
        
        Returns:
            JSON string containing pattern analysis
        """
        try:
            # Get user interactions
            user_interactions = self._interaction_patterns.get(user_id, [])
            
            # Filter by time window
            cutoff_date = datetime.utcnow() - self._parse_time_window(time_window)
            recent_interactions = [i for i in user_interactions 
                                 if datetime.fromisoformat(i['timestamp']) > cutoff_date]
            
            # Analyze patterns
            patterns = {
                "interaction_frequency": self._analyze_frequency(recent_interactions),
                "preferred_times": self._analyze_time_preferences(recent_interactions),
                "feature_usage": self._analyze_feature_usage(recent_interactions),
                "content_preferences": self._analyze_content_preferences(recent_interactions),
                "workflow_patterns": self._analyze_workflows(recent_interactions)
            }
            
            # Generate insights
            insights = self._generate_pattern_insights(patterns)
            
            return json.dumps({
                "status": "success",
                "user_id": user_id,
                "time_window": time_window,
                "interaction_count": len(recent_interactions),
                "patterns": patterns,
                "insights": insights
            })
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to analyze patterns: {str(e)}"
            })
    
    @kernel_function(
        description="Generate personalized recommendations based on preferences",
        name="GenerateRecommendations"
    )
    async def generate_recommendations(
        self,
        user_id: str,
        context: str,
        recommendation_type: str = "actions"
    ) -> str:
        """
        Generate personalized recommendations based on learned preferences.
        
        Args:
            user_id: ID of the user
            context: Current context for recommendations
            recommendation_type: Type of recommendations (actions, insights, formats)
        
        Returns:
            JSON string containing personalized recommendations
        """
        try:
            # Get user preferences
            user_prefs = self._preference_store.get(user_id, {})
            
            recommendations = []
            
            if recommendation_type == "actions":
                # Action recommendations based on patterns
                if user_prefs.get("decision_speed") == "quick":
                    recommendations.append({
                        "type": "action",
                        "title": "Quick Decision Framework",
                        "description": "Use rapid assessment template for faster decisions",
                        "confidence": 0.85
                    })
                
                if "innovation" in user_prefs.get("focus_areas", []):
                    recommendations.append({
                        "type": "action",
                        "title": "Innovation Sprint",
                        "description": "Schedule weekly innovation sessions based on your interest patterns",
                        "confidence": 0.78
                    })
            
            elif recommendation_type == "insights":
                # Insight recommendations based on preferences
                if user_prefs.get("detail_level") == "high":
                    recommendations.append({
                        "type": "insight",
                        "title": "Deep Dive Analysis Available",
                        "description": "Comprehensive analysis with statistical breakdowns",
                        "confidence": 0.90
                    })
            
            elif recommendation_type == "formats":
                # Format recommendations
                preferred_formats = user_prefs.get("preferred_formats", ["text"])
                if "visual" in preferred_formats:
                    recommendations.append({
                        "type": "format",
                        "title": "Visual Dashboard",
                        "description": "Interactive charts and graphs for better insights",
                        "confidence": 0.82
                    })
            
            # Add context-specific recommendations
            if "strategic planning" in context.lower():
                recommendations.append({
                    "type": "contextual",
                    "title": "Strategic Planning Template",
                    "description": "Customized template based on your planning style",
                    "confidence": 0.75
                })
            
            return json.dumps({
                "status": "success",
                "user_id": user_id,
                "recommendation_type": recommendation_type,
                "recommendations": recommendations,
                "personalization_level": self._calculate_personalization_level(user_id)
            })
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to generate recommendations: {str(e)}"
            })
    
    @kernel_function(
        description="Update user preferences based on new information",
        name="UpdatePreferences"
    )
    async def update_preferences(
        self,
        user_id: str,
        preference_updates: Dict[str, Any]
    ) -> str:
        """
        Update user preferences with new information.
        
        Args:
            user_id: ID of the user
            preference_updates: Dictionary of preference updates
        
        Returns:
            JSON string confirming preference update
        """
        try:
            if user_id not in self._preference_store:
                self._preference_store[user_id] = {}
            
            # Update preferences
            self._preference_store[user_id].update(preference_updates)
            self._preference_store[user_id]["last_updated"] = datetime.utcnow().isoformat()
            
            # Log the update
            self._interaction_patterns[user_id].append({
                "type": "preference_update",
                "updates": preference_updates,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return json.dumps({
                "status": "success",
                "user_id": user_id,
                "updated_preferences": list(preference_updates.keys()),
                "message": "Preferences updated successfully"
            })
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to update preferences: {str(e)}"
            })
    
    @kernel_function(
        description="Track user interactions for pattern learning",
        name="TrackInteraction"
    )
    async def track_interaction(
        self,
        user_id: str,
        interaction_type: str,
        details: Dict[str, Any]
    ) -> str:
        """
        Track user interactions for pattern learning.
        
        Args:
            user_id: ID of the user
            interaction_type: Type of interaction (view, create, modify, delete)
            details: Details about the interaction
        
        Returns:
            JSON string confirming interaction tracking
        """
        try:
            interaction = {
                "type": interaction_type,
                "details": details,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            self._interaction_patterns[user_id].append(interaction)
            
            # Trigger pattern analysis if enough data
            if len(self._interaction_patterns[user_id]) % 10 == 0:
                await self._analyze_recent_patterns(user_id)
            
            return json.dumps({
                "status": "success",
                "message": "Interaction tracked",
                "total_interactions": len(self._interaction_patterns[user_id])
            })
            
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Failed to track interaction: {str(e)}"
            })
    
    # Helper methods
    
    async def _update_preferences(self, user_id: str, item_type: str, 
                                  feedback: str, context: Optional[Dict[str, Any]]) -> None:
        """Update preferences based on feedback."""
        if user_id not in self._preference_store:
            self._preference_store[user_id] = {}
        
        # Update based on feedback type
        if feedback == "accepted":
            # Increase preference score for this type
            score_key = f"{item_type}_preference_score"
            current_score = self._preference_store[user_id].get(score_key, 0.5)
            self._preference_store[user_id][score_key] = min(1.0, current_score + 0.1)
        
        elif feedback == "rejected":
            # Decrease preference score
            score_key = f"{item_type}_preference_score"
            current_score = self._preference_store[user_id].get(score_key, 0.5)
            self._preference_store[user_id][score_key] = max(0.0, current_score - 0.1)
        
        # Update context-specific preferences
        if context:
            for key, value in context.items():
                if key in ["detail_level", "communication_style", "risk_tolerance"]:
                    self._preference_store[user_id][key] = value
    
    def _calculate_confidence_scores(self, user_id: str) -> Dict[str, float]:
        """Calculate confidence scores for different preference categories."""
        interactions = len(self._interaction_patterns.get(user_id, []))
        feedbacks = len([f for f in self._feedback_history if f["user_id"] == user_id])
        
        # Simple confidence calculation based on data volume
        base_confidence = min(1.0, (interactions + feedbacks) / 100)
        
        return {
            "communication_style": base_confidence * 0.8,
            "detail_level": base_confidence * 0.9,
            "risk_tolerance": base_confidence * 0.7,
            "decision_speed": base_confidence * 0.75
        }
    
    def _parse_time_window(self, window: str) -> timedelta:
        """Parse time window string to timedelta."""
        if window.endswith('d'):
            return timedelta(days=int(window[:-1]))
        elif window.endswith('h'):
            return timedelta(hours=int(window[:-1]))
        else:
            return timedelta(days=30)  # Default to 30 days
    
    def _analyze_frequency(self, interactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze interaction frequency patterns."""
        if not interactions:
            return {"avg_daily": 0, "trend": "stable"}
        
        # Group by day
        daily_counts = defaultdict(int)
        for interaction in interactions:
            date = datetime.fromisoformat(interaction['timestamp']).date()
            daily_counts[date] += 1
        
        avg_daily = sum(daily_counts.values()) / len(daily_counts) if daily_counts else 0
        
        return {
            "avg_daily": round(avg_daily, 2),
            "peak_day": max(daily_counts.values()) if daily_counts else 0,
            "trend": "increasing" if len(interactions) > avg_daily * 7 else "stable"
        }
    
    def _analyze_time_preferences(self, interactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze preferred interaction times."""
        hour_counts = defaultdict(int)
        for interaction in interactions:
            hour = datetime.fromisoformat(interaction['timestamp']).hour
            hour_counts[hour] += 1
        
        if not hour_counts:
            return {"preferred_hours": [], "time_zone_pattern": "unknown"}
        
        # Find peak hours
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        preferred_hours = [hour for hour, _ in sorted_hours[:3]]
        
        return {
            "preferred_hours": preferred_hours,
            "time_zone_pattern": "morning" if preferred_hours[0] < 12 else "afternoon"
        }
    
    def _analyze_feature_usage(self, interactions: List[Dict[str, Any]]) -> Dict[str, int]:
        """Analyze which features are used most."""
        feature_counts = defaultdict(int)
        for interaction in interactions:
            feature = interaction.get('details', {}).get('feature', 'unknown')
            feature_counts[feature] += 1
        
        return dict(feature_counts)
    
    def _analyze_content_preferences(self, interactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze content preferences from interactions."""
        content_types = defaultdict(int)
        for interaction in interactions:
            content_type = interaction.get('details', {}).get('content_type', 'unknown')
            content_types[content_type] += 1
        
        return {
            "preferred_content_types": dict(content_types),
            "diversity_score": len(content_types) / max(len(interactions), 1)
        }
    
    def _analyze_workflows(self, interactions: List[Dict[str, Any]]) -> List[List[str]]:
        """Analyze common workflow patterns."""
        # Simple workflow detection - look for sequences of actions
        workflows = []
        current_workflow = []
        
        for i, interaction in enumerate(interactions):
            action = interaction.get('type', '')
            current_workflow.append(action)
            
            # End workflow if gap > 30 minutes or end of list
            if i == len(interactions) - 1 or i < len(interactions) - 1:
                next_time = datetime.fromisoformat(interactions[i + 1]['timestamp'])
                curr_time = datetime.fromisoformat(interaction['timestamp'])
                if (next_time - curr_time).seconds > 1800:  # 30 minutes
                    if len(current_workflow) > 1:
                        workflows.append(current_workflow)
                    current_workflow = []
        
        return workflows[:5]  # Return top 5 workflows
    
    def _generate_pattern_insights(self, patterns: Dict[str, Any]) -> List[str]:
        """Generate insights from analyzed patterns."""
        insights = []
        
        # Frequency insights
        if patterns['interaction_frequency']['avg_daily'] > 5:
            insights.append("High engagement user - consider advanced features")
        
        # Time insights
        if patterns['preferred_times']['time_zone_pattern'] == "morning":
            insights.append("Prefers morning sessions - schedule important updates accordingly")
        
        # Feature insights
        top_features = sorted(patterns['feature_usage'].items(), 
                            key=lambda x: x[1], reverse=True)[:3]
        if top_features:
            insights.append(f"Most used features: {', '.join([f[0] for f in top_features])}")
        
        return insights
    
    def _calculate_personalization_level(self, user_id: str) -> str:
        """Calculate the level of personalization available."""
        interactions = len(self._interaction_patterns.get(user_id, []))
        feedbacks = len([f for f in self._feedback_history if f["user_id"] == user_id])
        
        total_data_points = interactions + feedbacks
        
        if total_data_points < 10:
            return "minimal"
        elif total_data_points < 50:
            return "basic"
        elif total_data_points < 100:
            return "moderate"
        else:
            return "advanced"
    
    async def _analyze_recent_patterns(self, user_id: str) -> None:
        """Analyze recent patterns and update preferences automatically."""
        # This would run more sophisticated ML algorithms in production
        recent_interactions = self._interaction_patterns[user_id][-50:]
        
        # Simple pattern detection
        feature_usage = self._analyze_feature_usage(recent_interactions)
        if feature_usage:
            top_feature = max(feature_usage.items(), key=lambda x: x[1])[0]
            if user_id not in self._preference_store:
                self._preference_store[user_id] = {}
            
            current_focus = self._preference_store[user_id].get("focus_areas", [])
            if top_feature not in current_focus:
                current_focus.append(top_feature)
                self._preference_store[user_id]["focus_areas"] = current_focus[-5:]  # Keep last 5