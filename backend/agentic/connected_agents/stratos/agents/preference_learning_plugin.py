"""
Preference Learning Plugin for Connected Agent Pattern
Provides preference learning capabilities without Semantic Kernel decorators
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class PreferenceLearningPlugin:
    """Plugin for preference learning and adaptation"""
    
    def __init__(self):
        # In-memory preference storage (would be database in production)
        self.preference_models: Dict[str, Dict[str, Any]] = {}
        self.interaction_history: List[Dict[str, Any]] = []
        
    async def learn_preferences(
        self, 
        interaction_data: str,
        context: str,
        user_id: str = "default"
    ) -> str:
        """
        Learn from user interactions to identify preference patterns
        
        Args:
            interaction_data: JSON string containing interaction details
            context: The context/domain of the interaction
            user_id: User identifier for preference tracking
            
        Returns:
            Analysis of learned preferences
        """
        try:
            # Parse interaction data
            data = json.loads(interaction_data) if isinstance(interaction_data, str) else interaction_data
            
            # Extract preference signals
            preference_signal = {
                "timestamp": datetime.utcnow().isoformat(),
                "context": context,
                "user_choice": data.get("choice"),
                "implicit_feedback": data.get("implicit_feedback", {}),
                "explicit_feedback": data.get("explicit_feedback", {}),
                "metadata": data.get("metadata", {})
            }
            
            # Store interaction
            self.interaction_history.append(preference_signal)
            
            # Update preference model
            if user_id not in self.preference_models:
                self.preference_models[user_id] = {}
            
            if context not in self.preference_models[user_id]:
                self.preference_models[user_id][context] = {
                    "patterns": [],
                    "confidence": 0.0,
                    "last_updated": datetime.utcnow().isoformat()
                }
            
            # Analyze patterns
            model = self.preference_models[user_id][context]
            model["patterns"].append(preference_signal)
            
            # Calculate confidence based on consistency
            confidence = min(len(model["patterns"]) * 0.1, 0.9)  # Max 90% confidence
            model["confidence"] = confidence
            model["last_updated"] = datetime.utcnow().isoformat()
            
            return json.dumps({
                "status": "learned",
                "context": context,
                "preference_detected": data.get("choice"),
                "confidence": confidence,
                "patterns_count": len(model["patterns"]),
                "insight": f"Preference pattern updated for {context} with {confidence:.0%} confidence"
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Error learning preferences: {e}")
            return json.dumps({
                "status": "error",
                "message": str(e)
            })
    
    async def get_preferences(
        self,
        context: str,
        user_id: str = "default"
    ) -> str:
        """
        Retrieve current user preferences for specific context
        
        Args:
            context: The context/domain to retrieve preferences for
            user_id: User identifier
            
        Returns:
            Current preference model for the context
        """
        try:
            if user_id not in self.preference_models:
                return json.dumps({
                    "status": "no_preferences",
                    "context": context,
                    "message": "No preferences learned yet for this user"
                })
            
            if context not in self.preference_models[user_id]:
                return json.dumps({
                    "status": "no_preferences",
                    "context": context,
                    "message": f"No preferences learned for context: {context}"
                })
            
            model = self.preference_models[user_id][context]
            
            # Analyze patterns to extract preferences
            preferences = self._analyze_patterns(model["patterns"])
            
            return json.dumps({
                "status": "success",
                "context": context,
                "preferences": preferences,
                "confidence": model["confidence"],
                "based_on": len(model["patterns"]),
                "last_updated": model["last_updated"]
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Error retrieving preferences: {e}")
            return json.dumps({
                "status": "error",
                "message": str(e)
            })
    
    async def update_preferences(
        self,
        feedback: str,
        context: str,
        user_id: str = "default"
    ) -> str:
        """
        Update preference models based on explicit feedback
        
        Args:
            feedback: JSON string with feedback data
            context: The context to update
            user_id: User identifier
            
        Returns:
            Update confirmation
        """
        try:
            feedback_data = json.loads(feedback) if isinstance(feedback, str) else feedback
            
            # Create explicit preference update
            preference_update = {
                "timestamp": datetime.utcnow().isoformat(),
                "context": context,
                "explicit_update": True,
                "feedback": feedback_data
            }
            
            # Apply update with higher weight
            if user_id not in self.preference_models:
                self.preference_models[user_id] = {}
            
            if context not in self.preference_models[user_id]:
                self.preference_models[user_id][context] = {
                    "patterns": [],
                    "confidence": 0.0,
                    "last_updated": datetime.utcnow().isoformat()
                }
            
            model = self.preference_models[user_id][context]
            model["patterns"].append(preference_update)
            
            # Explicit feedback increases confidence more
            model["confidence"] = min(model["confidence"] + 0.2, 0.95)
            model["last_updated"] = datetime.utcnow().isoformat()
            
            return json.dumps({
                "status": "updated",
                "context": context,
                "new_confidence": model["confidence"],
                "message": "Preferences updated based on explicit feedback"
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Error updating preferences: {e}")
            return json.dumps({
                "status": "error",
                "message": str(e)
            })
    
    async def predict_preferences(
        self,
        scenario: str,
        context: str,
        user_id: str = "default"
    ) -> str:
        """
        Predict user preferences for new scenarios
        
        Args:
            scenario: Description of the new scenario
            context: The context domain
            user_id: User identifier
            
        Returns:
            Predicted preferences with confidence
        """
        try:
            if user_id not in self.preference_models or context not in self.preference_models[user_id]:
                return json.dumps({
                    "status": "insufficient_data",
                    "message": "Not enough data to predict preferences"
                })
            
            model = self.preference_models[user_id][context]
            patterns = self._analyze_patterns(model["patterns"])
            
            # Simple prediction based on historical patterns
            prediction = {
                "scenario": scenario,
                "predicted_preferences": patterns,
                "confidence": model["confidence"] * 0.8,  # Reduce confidence for predictions
                "based_on_patterns": len(model["patterns"]),
                "recommendation": self._generate_recommendation(patterns, scenario)
            }
            
            return json.dumps(prediction, indent=2)
            
        except Exception as e:
            logger.error(f"Error predicting preferences: {e}")
            return json.dumps({
                "status": "error",
                "message": str(e)
            })
    
    async def generate_recommendations(
        self,
        context: str,
        options: Optional[List[str]] = None,
        user_id: str = "default"
    ) -> str:
        """
        Generate personalized recommendations based on learned preferences
        
        Args:
            context: The context for recommendations
            options: Optional list of options to rank
            user_id: User identifier
            
        Returns:
            Personalized recommendations
        """
        try:
            if user_id not in self.preference_models or context not in self.preference_models[user_id]:
                return json.dumps({
                    "status": "no_preferences",
                    "message": "No preferences available for recommendations",
                    "fallback": "Using default recommendations"
                })
            
            model = self.preference_models[user_id][context]
            patterns = self._analyze_patterns(model["patterns"])
            
            recommendations = {
                "context": context,
                "personalized_for": user_id,
                "recommendations": [],
                "confidence": model["confidence"],
                "reasoning": []
            }
            
            # Generate recommendations based on patterns
            if patterns.get("risk_tolerance") == "high":
                recommendations["recommendations"].append("Consider aggressive growth strategies")
                recommendations["reasoning"].append("Your history shows preference for bold moves")
            
            if patterns.get("decision_speed") == "deliberate":
                recommendations["recommendations"].append("Allocate extra time for analysis")
                recommendations["reasoning"].append("You typically prefer thorough evaluation")
            
            if patterns.get("data_preference") == "quantitative":
                recommendations["recommendations"].append("Focus on metrics and KPIs")
                recommendations["reasoning"].append("You respond well to data-driven insights")
            
            return json.dumps(recommendations, indent=2)
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return json.dumps({
                "status": "error",
                "message": str(e)
            })
    
    def _analyze_patterns(self, patterns: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze interaction patterns to extract preferences"""
        if not patterns:
            return {}
        
        # Simple pattern analysis (would be ML in production)
        preferences = {}
        
        # Analyze choices
        choices = [p.get("user_choice") for p in patterns if p.get("user_choice")]
        if choices:
            # Find most common choice
            preferences["preferred_choice"] = max(set(choices), key=choices.count)
        
        # Analyze implicit feedback
        review_times = [p.get("implicit_feedback", {}).get("review_time", 0) for p in patterns]
        avg_review_time = sum(review_times) / len(review_times) if review_times else 0
        
        if avg_review_time > 10:
            preferences["decision_speed"] = "deliberate"
        else:
            preferences["decision_speed"] = "quick"
        
        # More analysis would go here...
        
        return preferences
    
    def _generate_recommendation(self, patterns: Dict[str, Any], scenario: str) -> str:
        """Generate a recommendation based on patterns"""
        if not patterns:
            return "Insufficient data for personalized recommendation"
        
        rec_parts = []
        
        if patterns.get("decision_speed") == "deliberate":
            rec_parts.append("take time to analyze thoroughly")
        
        if patterns.get("preferred_choice"):
            rec_parts.append(f"consider {patterns['preferred_choice']} based on past preferences")
        
        return f"For {scenario}, recommend to {' and '.join(rec_parts)}" if rec_parts else "Use standard approach"


# Create a global instance
preference_learning_plugin = PreferenceLearningPlugin()