#!/usr/bin/env python3
"""
Test script for StratOS agent orchestration.
Demonstrates function calling and agent delegation pattern from semantic_kernel_multi_agent.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from agents.strategic_foundation.ceo_log_agent import CEOLogAgent
from agents.strategic_foundation.north_star_agent import NorthStarAgent
from common.orchestration import AgentOrchestrator
from config.settings import get_settings


async def test_direct_agent_usage():
    """Test using agents directly without orchestration."""
    print("\n=== Testing Direct Agent Usage ===\n")
    
    # Create kernel
    settings = get_settings()
    kernel = Kernel()
    
    # Add Azure OpenAI service
    kernel.add_service(
        AzureChatCompletion(
            service_id="chat",
            deployment_name=settings.azure_openai_deployment_name,
            endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version
        )
    )
    
    # Create CEO Log Agent
    print("1. Testing CEO Log Agent:")
    ceo_log_agent = CEOLogAgent(kernel)
    
    # Create a log entry
    result = await ceo_log_agent.process_request({
        "action": "create_entry",
        "data": {
            "text": "Had a great meeting with the product team today. We discussed the new AI features and how they align with our strategic vision. The team is excited about the potential impact on customer experience.",
            "category": "product_strategy",
            "is_voice": False
        }
    })
    print(f"Created entry: {result}")
    
    # Generate tags for text
    result = await ceo_log_agent.process_request({
        "action": "generate_tags",
        "data": {
            "text": "We need to focus on AI innovation and customer experience improvements"
        }
    })
    print(f"\nGenerated tags: {result}")
    
    # Create North Star Agent
    print("\n2. Testing North Star Agent:")
    north_star_agent = NorthStarAgent(kernel)
    
    # Set organizational purpose
    result = await north_star_agent.process_request({
        "element": "purpose",
        "action": "set",
        "data": {
            "content": "To empower organizations with AI-driven strategic planning tools that transform vision into reality"
        }
    })
    print(f"Set purpose: {result}")
    
    # Add a value
    result = await north_star_agent.process_request({
        "element": "values",
        "action": "add",
        "data": {
            "name": "Innovation",
            "description": "We constantly push boundaries to deliver cutting-edge solutions"
        }
    })
    print(f"\nAdded value: {result}")
    
    # Get North Star summary
    result = await north_star_agent.process_request({
        "element": "summary",
        "action": "get"
    })
    print(f"\nNorth Star Summary: {result}")


async def test_orchestration():
    """Test orchestration with function calling."""
    print("\n\n=== Testing Orchestration with Function Calling ===\n")
    
    # Create kernel and orchestrator
    settings = get_settings()
    kernel = Kernel()
    
    # Add Azure OpenAI service
    kernel.add_service(
        AzureChatCompletion(
            service_id="chat",
            deployment_name=settings.azure_openai_deployment_name,
            endpoint=settings.azure_openai_endpoint,
            api_key=settings.azure_openai_api_key,
            api_version=settings.azure_openai_api_version
        )
    )
    
    # Create agents and register their plugins
    ceo_log_agent = CEOLogAgent(kernel)
    north_star_agent = NorthStarAgent(kernel)
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(kernel)
    
    # Define available functions
    available_functions = [
        orchestrator.create_function_definition(
            name="SaveCEOLogEntry",
            description="Save a CEO log entry with tags and summary",
            parameters={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The log entry content"
                    },
                    "category": {
                        "type": "string",
                        "description": "Category of the entry"
                    },
                    "is_voice": {
                        "type": "boolean",
                        "description": "Whether this was a voice entry"
                    }
                },
                "required": ["content"]
            }
        ),
        orchestrator.create_function_definition(
            name="SetOrganizationalPurpose",
            description="Set the organization's purpose statement",
            parameters={
                "type": "object",
                "properties": {
                    "statement": {
                        "type": "string",
                        "description": "The purpose statement"
                    }
                },
                "required": ["statement"]
            }
        )
    ]
    
    # Test 1: Natural language request that should trigger CEO log function
    print("Test 1: CEO Log Entry via Natural Language")
    messages = [{
        "role": "user",
        "content": "I want to log this thought: We should explore partnerships with universities to strengthen our AI research capabilities. This could accelerate our innovation cycle."
    }]
    
    system_prompt = """
You are an AI assistant helping with strategic planning. You have access to functions for:
1. Saving CEO log entries (SaveCEOLogEntry)
2. Setting organizational purpose (SetOrganizationalPurpose)

When a user wants to log thoughts or entries, use SaveCEOLogEntry.
When they want to define organizational purpose, use SetOrganizationalPurpose.
"""
    
    result = await orchestrator.orchestrate_with_function_calling(
        messages=messages,
        available_functions=available_functions,
        system_prompt=system_prompt
    )
    
    print(f"Response: {result['content']}")
    if result['function_calls']:
        print(f"Functions called: {[fc['name'] for fc in result['function_calls']]}")
    
    # Test 2: Request to set organizational purpose
    print("\n\nTest 2: Set Organizational Purpose via Natural Language")
    messages = [{
        "role": "user",
        "content": "Let's define our purpose as: To democratize strategic planning through intelligent AI systems that adapt to each organization's unique culture and goals"
    }]
    
    result = await orchestrator.orchestrate_with_function_calling(
        messages=messages,
        available_functions=available_functions,
        system_prompt=system_prompt
    )
    
    print(f"Response: {result['content']}")
    if result['function_calls']:
        print(f"Functions called: {[fc['name'] for fc in result['function_calls']]}")


async def main():
    """Run all tests."""
    print("StratOS Agent Orchestration Test")
    print("================================")
    
    try:
        # Test direct agent usage
        await test_direct_agent_usage()
        
        # Test orchestration
        await test_orchestration()
        
        print("\n\nAll tests completed successfully!")
        
    except Exception as e:
        print(f"\nError during testing: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())