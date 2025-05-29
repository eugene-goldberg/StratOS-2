#!/usr/bin/env python3
"""
Test CEO Log Agent with direct message approach.
"""

import os
import sys
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AgentChannel

# Load environment variables
load_dotenv('.env')

# CEO Log Agent ID from deployment configuration
CEO_LOG_AGENT_ID = "asst_Cc8qg96Q0Ty1lNbpxYuodv4x"

async def test_ceo_log():
    """Test CEO Log Agent with message approach."""
    
    print("\n🚀 Testing CEO Log Agent - Message Approach")
    print("=" * 60)
    
    # Configuration
    endpoint = os.getenv("AZURE_AI_AGENT_ENDPOINT")
    api_version = os.getenv("AZURE_AI_AGENT_API_VERSION", "2024-12-01-preview")
    model_deployment = os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME", "gpt-35-turbo")
    
    print(f"CEO Log Agent ID: {CEO_LOG_AGENT_ID}")
    
    try:
        # Create settings
        settings = AzureAIAgentSettings(
            endpoint=endpoint,
            api_version=api_version,
            model_deployment_name=model_deployment
        )
        
        # Create credential
        credential = DefaultAzureCredential()
        
        # Create client
        async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
            print("✅ Connected to Azure AI Agent Service")
            
            # Get agent
            agent_def = await client.agents.get_agent(CEO_LOG_AGENT_ID)
            print(f"✅ Agent: {agent_def.name}")
            
            # Create agent instance
            agent = AzureAIAgent(client=client, definition=agent_def)
            
            # Try direct invocation with string message
            test_message = f"""
Process this CEO log entry:

Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}

Strategic Update:
Today we successfully deployed all 15 StratOS agents to Azure AI Agent Service. This marks a major milestone in our AI-driven strategic planning platform.

Key Achievements:
- All Strategic Foundation agents are operational
- Analysis Intelligence agents are processing data
- Planning Execution agents are ready for integration

Immediate Priorities:
1. Test end-to-end orchestration
2. Validate data persistence
3. Monitor performance metrics

Team Status: High morale, excited about the progress

Categories: milestone, technology, strategic_planning
            """
            
            print("\n📝 Sending CEO log entry...")
            print("-" * 60)
            
            # Invoke agent directly with string
            print("\n🤖 CEO LOG AGENT RESPONSE:")
            print("-" * 60)
            
            try:
                # Try invoking with just the message string
                response_count = 0
                async for response in agent.invoke(messages=test_message):
                    response_count += 1
                    if hasattr(response, 'content') and response.content:
                        print(response.content, end="", flush=True)
                    elif isinstance(response, str):
                        print(response, end="", flush=True)
                    else:
                        print(f"[Response type: {type(response)}]")
                
                if response_count == 0:
                    print("❌ No responses received from agent")
                else:
                    print(f"\n✅ Received {response_count} response(s)")
                    
            except Exception as e:
                print(f"❌ Invocation error: {type(e).__name__}: {str(e)}")
            
            print("\n" + "-" * 60)
            
            # Try another approach - using the agent's instruction format
            print("\n📝 Trying instruction-based format...")
            
            instruction_message = """
I need you to process the following CEO log entry and provide insights:

"Today marks a significant achievement - all 15 StratOS agents are now deployed and operational on Azure AI Agent Service. The team has worked tirelessly to reach this milestone. I'm particularly impressed with how the multi-agent architecture has come together."

Please analyze this entry and identify:
1. Key achievements mentioned
2. Emotional tone
3. Strategic implications
"""
            
            try:
                async for response in agent.invoke(messages=instruction_message):
                    if hasattr(response, 'content') and response.content:
                        print(response.content, end="", flush=True)
                print()
            except Exception as e:
                print(f"❌ Error: {str(e)}")
            
            print(f"\n✅ Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ceo_log())