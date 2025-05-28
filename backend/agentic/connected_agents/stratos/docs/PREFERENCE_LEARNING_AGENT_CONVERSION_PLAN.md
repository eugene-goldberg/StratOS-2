# Preference Learning Agent Conversion Plan

## Overview
This document outlines the conversion of the Preference Learning Agent from a Semantic Kernel plugin-based implementation to an Azure AI Connected Agent pattern, following the exact same approach as the North Star Agent conversion.

## Current State Analysis

### Location
- **Current Plugin**: `/backend/agentic/agents/strategic_foundation/preference_learning_agent.py`
- **Plugin Location**: `/backend/agentic/agents/strategic_foundation/plugins/preference_plugin.py`

### Current Implementation
```python
# Current Semantic Kernel Plugin Pattern
@kernel_function(
    name="learn_preferences",
    description="Learn and adapt to user preferences based on interactions"
)
async def learn_preferences(self, interaction_data: str) -> str:
    """Learn from user interactions and update preference models"""
    # Implementation details
```

## Target State: Connected Agent Pattern

### Key Principles (Same as North Star)
1. **No Tools**: Connected agents don't have tools - they are tools themselves
2. **Plugin Pattern**: Agents become "plugins" that orchestrators can invoke
3. **Delegation Model**: Main orchestrator delegates to connected agents
4. **Instruction-Based**: Behavior defined through detailed instructions

## Conversion Steps

### Step 1: Create Agent Configuration
Create `/backend/agentic/connected_agents/stratos/agents/preference_learning_agent_config.py`:

```python
"""
Preference Learning Agent Configuration
Learns and adapts to user preferences based on interactions and feedback
"""

# Agent configuration
AGENT_NAME_PREFIX = "PreferenceLearningAgent"

AGENT_INSTRUCTIONS = """You are the Preference Learning Agent for StratOS, specializing in understanding and adapting to user preferences and decision-making patterns.

You have access to powerful tools for preference learning and adaptation:

Available functions:
- LearnPreferences: Analyze user interactions to identify preference patterns
- GetPreferences: Retrieve current user preferences for specific contexts
- UpdatePreferences: Update preference models based on new feedback
- PredictPreferences: Predict user preferences for new scenarios
- GenerateRecommendations: Generate personalized recommendations based on learned preferences

Your responsibilities:
1. Learn from every user interaction and decision
2. Identify patterns in user choices and feedback
3. Build accurate preference models for different contexts
4. Provide personalized recommendations and insights
5. Adapt quickly to changing user preferences

When processing interactions:
1. Analyze the context and decision made
2. Extract preference indicators:
   - decision_context: The situation requiring a decision
   - user_choice: What the user selected or decided
   - implicit_feedback: Actions taken or time spent
   - explicit_feedback: Direct ratings or comments
   - confidence_level: How certain the preference signal is

3. Update preference models appropriately
4. Provide insights about learned preferences

Example interactions:

User: "Learn from this interaction: User spent 15 minutes reviewing risk analysis before approving the aggressive growth strategy"
You: Let me analyze this interaction to learn preferences.
[Use LearnPreferences with context="strategic_planning", choice="aggressive_growth", implicit_signal="extended_review_time"]
[Response includes: preference pattern detected, model updated, confidence level]

User: "What are my preferences for strategic planning decisions?"
You: I'll retrieve your learned preferences for strategic planning.
[Use GetPreferences with context="strategic_planning"]
[Present preferences with confidence scores and supporting patterns]

User: "Generate recommendations for our market expansion based on my preferences"
You: I'll generate personalized recommendations based on your preferences.
[Use GenerateRecommendations with context="market_expansion"]
[Present recommendations aligned with learned preferences]

Response format guidelines:
- Acknowledge the learning opportunity
- Explain what preferences were detected
- Show confidence levels for learned patterns
- Connect preferences across different contexts
- Suggest how preferences might apply to future decisions

Remember: You're building a dynamic model of user preferences that improves with every interaction."""

# Model configuration
MODEL_NAME = "gpt-35-turbo"

# No tools needed - they will be added when the agent is deployed
TOOLS = []
```

### Step 2: Create Plugin Implementation
Create `/backend/agentic/connected_agents/stratos/agents/preference_learning_plugin.py`:

```python
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
```

### Step 3: Update Orchestrator Configuration
Add to `/backend/agentic/connected_agents/stratos/agents/orchestrator_agent_config.py`:

```python
# Add to the orchestrator's instructions:
"""
- Preference/learning/adaptation queries → ALWAYS use preference_learning_specialist
"""

# Add to tools configuration:
{
    "type": "connected_agent",
    "connected_agent": {
        "name": "preference_learning_specialist",
        "id": "<PREFERENCE_LEARNING_AGENT_ID>"  # Will be set during deployment
    }
}
```

### Step 4: Create Test Implementation
Create `/backend/agentic/connected_agents/stratos/tests/test_preference_learning_unified.py`:

```python
"""
Test implementation for Preference Learning Agent using unified telemetry
"""

from typing import List, Dict
from base_agent_test import BaseAgentTest


class PreferenceLearningAgentTest(BaseAgentTest):
    """Test implementation for Preference Learning Agent"""
    
    def __init__(self):
        super().__init__("Preference Learning Agent")
    
    def get_test_scenarios(self) -> List[Dict[str, str]]:
        return [
            {
                "name": "learn_interaction",
                "query": "Learn from this: User reviewed 3 conservative options before selecting moderate risk strategy with 85% confidence"
            },
            {
                "name": "retrieve_preferences",
                "query": "What are my learned preferences for strategic planning decisions?"
            },
            {
                "name": "predict_preference",
                "query": "Based on my preferences, how would I likely approach a new market entry decision?"
            },
            {
                "name": "generate_recommendations",
                "query": "Generate personalized recommendations for resource allocation based on my past decisions"
            }
        ]
```

### Step 5: Create Deployment Script
Create `/backend/agentic/connected_agents/stratos/deployment/deploy_preference_learning_agent.py`:

```python
"""
Deploy Preference Learning Agent as a connected agent
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from agents import preference_learning_agent_config

# Load environment variables
load_dotenv(Path(__file__).parent.parent.parent / '.env')


async def deploy_preference_learning_agent():
    """Deploy the Preference Learning agent"""
    
    connection_string = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    if not connection_string:
        print("Error: AZURE_AI_PROJECT_CONNECTION_STRING not found")
        return None
    
    async with DefaultAzureCredential() as credential:
        async with AIProjectClient(
            endpoint=connection_string,
            credential=credential
        ) as client:
            # Create the agent
            print(f"Deploying {preference_learning_agent_config.AGENT_NAME_PREFIX}...")
            
            agent = await client.agents.create_agent(
                model=preference_learning_agent_config.MODEL_NAME,
                name=f"{preference_learning_agent_config.AGENT_NAME_PREFIX}-001",
                instructions=preference_learning_agent_config.AGENT_INSTRUCTIONS,
                tools=preference_learning_agent_config.TOOLS
            )
            
            print(f"✅ Agent deployed successfully!")
            print(f"   Name: {agent.name}")
            print(f"   ID: {agent.id}")
            
            return agent.id


if __name__ == "__main__":
    agent_id = asyncio.run(deploy_preference_learning_agent())
    if agent_id:
        print(f"\nAdd this to your orchestrator configuration:")
        print(f'PREFERENCE_LEARNING_AGENT_ID = "{agent_id}"')
```

## Implementation Timeline

### Phase 1: Basic Setup (2 hours)
1. Create agent configuration file
2. Create plugin implementation
3. Set up test structure

### Phase 2: Deployment (1 hour)
1. Deploy preference learning agent
2. Update orchestrator configuration
3. Test basic delegation

### Phase 3: Testing & Validation (2 hours)
1. Run simple tests with telemetry
2. Run comprehensive tests
3. Validate delegation patterns
4. Verify telemetry capture

### Phase 4: Integration (1 hour)
1. Update full cycle test scripts
2. Add to unified test suite
3. Document in UNIFIED_TESTING_README.md

## Key Differences from Plugin Pattern

### Before (Semantic Kernel Plugin):
```python
@kernel_function(name="learn_preferences")
async def learn_preferences(self, interaction_data: str) -> str:
    # Direct function implementation
```

### After (Connected Agent):
```python
# Agent receives natural language query
# "Learn from this interaction: User spent 15 minutes..."
# Agent interprets and responds appropriately
```

## Success Criteria

1. **Delegation Working**: Orchestrator successfully routes preference-related queries
2. **Natural Language**: Agent understands varied phrasings of preference queries
3. **Telemetry Captured**: All interactions logged with delegation confirmation
4. **Test Coverage**: All 4 test scenarios pass with proper delegation
5. **Response Quality**: Agent provides meaningful preference insights

## Common Patterns to Follow

1. **Announcement Pattern**: "I'll connect you with the Preference Learning specialist..."
2. **No Direct Tools**: Agent has no tools in config (TOOLS = [])
3. **Instruction-Based**: Detailed instructions define all behavior
4. **Scenario Testing**: Multiple test scenarios covering main use cases
5. **Telemetry Integration**: Use unified telemetry system for all tests

## Troubleshooting Guide

### If delegation fails:
1. Check orchestrator instructions include preference routing rules
2. Verify agent ID is correctly set in orchestrator config
3. Ensure query contains preference-related keywords

### If tests fail:
1. Add delays between tests (10+ seconds)
2. Check for rate limiting errors
3. Verify agent is deployed and accessible

### If telemetry missing:
1. Ensure using unified test base class
2. Check telemetry capture is initialized
3. Verify delegation patterns are detected

## Next Steps

After successful conversion:
1. Add agent to `test_all_agents_unified.py`
2. Update deployment scripts to include preference learning
3. Add to full cycle test suite
4. Update documentation with preference learning examples
5. Consider adding more sophisticated preference analysis in plugin

This plan follows the exact same patterns and approach as the North Star Agent conversion, ensuring consistency across all StratOS connected agents.