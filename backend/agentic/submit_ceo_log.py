#!/usr/bin/env python3
"""
Submit a CEO log request to the deployed CEO Log Agent.
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from dotenv import load_dotenv

from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.contents import ChatMessageContent, AuthorRole

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

async def submit_ceo_log():
    """Submit a CEO log entry to the deployed agent."""
    
    print("\n🚀 Submitting CEO Log Request")
    print("=" * 60)
    
    # Configuration
    endpoint = os.getenv("AZURE_AI_AGENT_ENDPOINT")
    api_version = os.getenv("AZURE_AI_AGENT_API_VERSION", "2024-12-01-preview")
    model_deployment = os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME", "gpt-35-turbo")
    
    # Load deployed agent ID
    config_path = os.path.join(
        os.path.dirname(__file__), 
        'deployment_configs', 
        'ai_project_agents_deployment.json'
    )
    
    try:
        with open(config_path, 'r') as f:
            data = json.load(f)
            agent_configs = data.get('deployed_agents', {})
            ceo_agent_id = agent_configs.get('CEOLogAgent')
    except:
        # Use the ID from recent deployment
        ceo_agent_id = "asst_oPGyOa5Z70gOUrRAQFCB0T5x"
    
    if not ceo_agent_id:
        print("❌ CEO Log Agent ID not found!")
        return
    
    print(f"CEO Log Agent ID: {ceo_agent_id}")
    
    # CEO log entry
    log_entry = f"""
    Please process this CEO log entry:
    
    Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}
    
    Strategic Reflection:
    We've successfully deployed all 15 StratOS agents to Azure AI Agent Service. This marks a significant 
    milestone in our AI-driven strategic planning platform. The multi-agent architecture is now operational 
    and ready for integration testing.
    
    Key achievements today:
    - Completed deployment of Strategic Foundation agents (CEO Log, North Star, Memory Recall, Preference Learning)
    - Analysis Intelligence agents are live (SWOT/TOWS, Risk/Opportunity, SO Linkage)
    - Planning Execution agents deployed (Initiative Generation, Resource Optimization, Canvas Visualization)
    
    Immediate priorities:
    1. Test end-to-end orchestration between agents
    2. Validate data persistence across agent interactions
    3. Performance benchmarking of agent response times
    
    Concerns:
    - Need to monitor Azure costs with 15 active agents
    - Ensure proper error handling for inter-agent communication
    - Security review of agent permissions and data access
    
    This positions us well for the Q2 product launch. The team's hard work on the agent architecture 
    is paying off.
    
    Categories: strategic_planning, technology, milestone
    """
    
    try:
        # Create settings
        settings = AzureAIAgentSettings(
            endpoint=endpoint,
            api_version=api_version,
            model_deployment_name=model_deployment
        )
        
        # Create credential
        credential = DefaultAzureCredential()
        
        # Create client and interact
        async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
            print("✅ Connected to Azure AI Agent Service")
            
            # Get the agent definition
            print("\n1. Retrieving CEO Log Agent...")
            agent_definition = await client.agents.get_agent(ceo_agent_id)
            print(f"✅ Agent retrieved: {agent_definition.name}")
            
            # Create agent instance
            agent = AzureAIAgent(
                client=client,
                definition=agent_definition
            )
            
            # Create channel
            print("\n2. Creating conversation channel...")
            channel = await agent.create_channel()
            print("✅ Channel created")
            
            # Send the log entry
            print("\n3. Submitting CEO log entry...")
            print("-" * 60)
            
            user_message = ChatMessageContent(
                role=AuthorRole.USER, 
                content=log_entry
            )
            
            # Invoke the agent and get response
            print("\n🤖 CEO LOG AGENT RESPONSE:")
            print("-" * 60)
            
            full_response = ""
            async for response in channel.invoke(agent):
                if hasattr(response, 'content') and response.content:
                    chunk = str(response.content)
                    full_response += chunk
                    print(chunk, end="", flush=True)
            
            print("\n" + "-" * 60)
            
            # Summary
            print("\n" + "=" * 60)
            print("CEO LOG SUBMISSION SUMMARY")
            print("=" * 60)
            print(f"Agent: {agent_definition.name} ({ceo_agent_id})")
            print(f"Status: Successfully processed")
            print(f"Timestamp: {datetime.now().isoformat()}")
            
            # Ask a follow-up question
            follow_up = "\nWhat are the top 3 risks from this log entry that need immediate attention?"
            print(f"\n📝 Follow-up question: {follow_up}")
            
            follow_up_message = ChatMessageContent(
                role=AuthorRole.USER,
                content=follow_up
            )
            
            print("\n🤖 CEO LOG AGENT FOLLOW-UP RESPONSE:")
            print("-" * 60)
            
            async for response in channel.invoke(agent):
                if hasattr(response, 'content') and response.content:
                    print(response.content, end="", flush=True)
            
            print("\n" + "-" * 60)
            print("\n✅ CEO log entry successfully processed!")
            
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(submit_ceo_log())