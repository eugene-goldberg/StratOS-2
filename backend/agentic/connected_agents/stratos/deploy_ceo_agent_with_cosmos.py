#!/usr/bin/env python3
"""Deploy CEO Log Agent with Cosmos DB integration via Azure Functions"""

import asyncio
import os
from typing import Dict, Any
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
import json

# Project configuration
PROJECT_CONNECTION_STRING = "eastus2.api.azureml.ms;0a7a2d58-80d4-4d62-9c71-f87740c9b9f1;semantic-kernel-multi-agent;semantic-kernel-multi-agent-rg"

# Agent configuration
AGENT_NAME = "CEOLogAgent"
MODEL_NAME = "gpt-35-turbo"

# Azure Functions URLs
AZURE_FUNCTIONS = {
    "SaveCEOLog": "https://stratos-ceo-log-functions.azurewebsites.net/api/saveceolog?code=I3c897PZMtJp1goBaxPwGlXa3Ni6ZsM09t1F7roTLVZeAzFu69TeKA==",
    "SearchCEOLogs": "https://stratos-ceo-log-functions.azurewebsites.net/api/searchceologs?code=uXjWD5crSSJYH_7eL3IcQq_ebEqVqO9D2QaC24UKa_RNAzFuVD7gkg==",
    "AnalyzeLogs": "https://stratos-ceo-log-functions.azurewebsites.net/api/analyzelogs?code=1ALdM_XHFGwQ5XtC5BBsnJ-_j_w30lef9DsjGWVrpNJfAzFuEHzbmg==",
    "GetInsights": "https://stratos-ceo-log-functions.azurewebsites.net/api/getinsights?code=Rx3WeFi1SoWXpbiZtsOCBVyswP06bUskqSYKK5HdntHBAzFuqJ56aw=="
}

# Updated instructions with Azure Functions
INSTRUCTIONS = f"""You are the CEO Log Agent for StratOS, specializing in processing executive thoughts and strategic reflections.

You have access to Azure Functions for managing CEO log entries in Cosmos DB:

1. SaveCEOLog - Save new entries with AI analysis
   URL: {AZURE_FUNCTIONS['SaveCEOLog']}
   
2. SearchCEOLogs - Search through past entries
   URL: {AZURE_FUNCTIONS['SearchCEOLogs']}
   
3. AnalyzeLogs - Analyze patterns and generate insights
   URL: {AZURE_FUNCTIONS['AnalyzeLogs']}
   
4. GetInsights - Get recent metrics and summaries
   URL: {AZURE_FUNCTIONS['GetInsights']}

When users interact with you:
- For new log entries: Use SaveCEOLog to persist to Cosmos DB
- For searches: Use SearchCEOLogs to find relevant entries
- For analysis: Use AnalyzeLogs to identify patterns
- For summaries: Use GetInsights for quick overview

Always use userId "ceo-001" unless specified otherwise.

Categories: strategic_planning, team_leadership, market_analysis, risk_assessment, innovation, operations, financial, customer_insights, general

Example responses:
- When saving: "I've saved your strategic observation about [topic]. Key tags: [tags]. This has been marked as [urgent/normal] priority."
- When searching: "I found [X] entries about [topic]. Here are the most relevant..."
- When analyzing: "Based on your recent entries, I've identified these patterns..."
"""

# Function calling tools
FUNCTION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "SaveCEOLog",
            "description": "Save a CEO log entry to Cosmos DB",
            "parameters": {
                "type": "object",
                "properties": {
                    "userId": {"type": "string", "default": "ceo-001"},
                    "content": {"type": "string"},
                    "category": {
                        "type": "string",
                        "enum": ["strategic_planning", "team_leadership", "market_analysis", 
                                "risk_assessment", "innovation", "operations", "financial", 
                                "customer_insights", "general"]
                    },
                    "tags": {"type": "array", "items": {"type": "string"}},
                    "metadata": {"type": "object"}
                },
                "required": ["content", "category"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "SearchCEOLogs",
            "description": "Search CEO log entries",
            "parameters": {
                "type": "object",
                "properties": {
                    "userId": {"type": "string", "default": "ceo-001"},
                    "query": {"type": "string"},
                    "category": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "AnalyzeLogs",
            "description": "Analyze CEO logs for patterns",
            "parameters": {
                "type": "object",
                "properties": {
                    "userId": {"type": "string", "default": "ceo-001"},
                    "focusArea": {
                        "type": "string",
                        "enum": ["risks", "opportunities", "team", "market", "general"]
                    },
                    "timeframe": {
                        "type": "string",
                        "enum": ["week", "month", "quarter", "all"]
                    }
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "GetInsights",
            "description": "Get CEO log insights and metrics",
            "parameters": {
                "type": "object",
                "properties": {
                    "userId": {"type": "string", "default": "ceo-001"}
                },
                "required": []
            }
        }
    }
]

async def deploy_agent():
    """Deploy CEO Log Agent with Cosmos DB integration"""
    
    with DefaultAzureCredential() as credential:
        client = AIProjectClient.from_connection_string(
            credential=credential,
            conn_str=PROJECT_CONNECTION_STRING
        )
        
        # Check if agent exists
        agents = client.agents.list_agents()
        existing_agent = None
        
        for agent in agents:
            if agent.name == AGENT_NAME:
                existing_agent = agent
                print(f"Found existing agent: {agent.id}")
                break
        
        if existing_agent:
            # Update existing agent
            print("Updating CEO Log Agent with Cosmos DB integration...")
            updated_agent = client.agents.update_agent(
                assistant_id=existing_agent.id,
                model=MODEL_NAME,
                name=AGENT_NAME,
                instructions=INSTRUCTIONS,
                tools=FUNCTION_TOOLS,
                temperature=0.7,
                top_p=0.95
            )
            print(f"✅ Updated agent: {updated_agent.id}")
        else:
            # Create new agent
            print("Creating CEO Log Agent with Cosmos DB integration...")
            new_agent = client.agents.create_agent(
                model=MODEL_NAME,
                name=AGENT_NAME,
                instructions=INSTRUCTIONS,
                tools=FUNCTION_TOOLS,
                temperature=0.7,
                top_p=0.95
            )
            print(f"✅ Created agent: {new_agent.id}")
            updated_agent = new_agent
        
        return updated_agent

async def test_agent(agent_id: str):
    """Test the deployed agent"""
    
    with DefaultAzureCredential() as credential:
        client = AIProjectClient.from_connection_string(
            credential=credential,
            conn_str=PROJECT_CONNECTION_STRING
        )
        
        # Create thread
        thread = client.agents.create_thread()
        print(f"\nCreated thread: {thread.id}")
        
        # Test 1: Save entry
        print("\n=== Test 1: Save CEO Log ===")
        message1 = client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content="I need to log a strategic observation: Our AI integration is showing promising results. The team has successfully deployed the new agent system and we're seeing improved efficiency in strategic planning. This is a major milestone."
        )
        
        run1 = client.agents.create_and_process_run(
            thread_id=thread.id,
            assistant_id=agent_id
        )
        
        # Get response
        messages = client.agents.list_messages(thread_id=thread.id)
        for msg in messages:
            if msg.role == "assistant":
                print(f"Agent: {msg.content[0].text.value}")
                break
        
        # Test 2: Search
        print("\n=== Test 2: Search Logs ===")
        message2 = client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content="Search for my entries about AI integration"
        )
        
        run2 = client.agents.create_and_process_run(
            thread_id=thread.id,
            assistant_id=agent_id
        )
        
        messages = client.agents.list_messages(thread_id=thread.id)
        for msg in messages:
            if msg.role == "assistant" and msg.created_at > message2.created_at:
                print(f"Agent: {msg.content[0].text.value[:500]}...")
                break
        
        # Test 3: Get insights
        print("\n=== Test 3: Get Insights ===")
        message3 = client.agents.create_message(
            thread_id=thread.id,
            role="user",
            content="What insights do you have from my recent entries?"
        )
        
        run3 = client.agents.create_and_process_run(
            thread_id=thread.id,
            assistant_id=agent_id
        )
        
        messages = client.agents.list_messages(thread_id=thread.id)
        for msg in messages:
            if msg.role == "assistant" and msg.created_at > message3.created_at:
                print(f"Agent: {msg.content[0].text.value}")
                break
        
        # Clean up
        client.agents.delete_thread(thread.id)
        print("\n✅ Tests completed")

async def main():
    """Main deployment and test"""
    print("=" * 60)
    print("CEO Log Agent - Cosmos DB Integration Deployment")
    print("=" * 60)
    
    # Deploy agent
    agent = await deploy_agent()
    
    # Test agent
    await test_agent(agent.id)
    
    print("\n" + "=" * 60)
    print("Deployment Complete")
    print(f"Agent ID: {agent.id}")
    print("Azure Functions: Configured")
    print("Cosmos DB: Connected")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())