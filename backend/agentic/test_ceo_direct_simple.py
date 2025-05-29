#!/usr/bin/env python3
"""
Direct test of CEO Log Agent with simple interaction.
"""

import os
import sys
import asyncio
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings
from semantic_kernel.contents import ChatMessageContent, AuthorRole

# Load environment variables
load_dotenv('.env')

# CEO Log Agent ID from deployment configuration
CEO_LOG_AGENT_ID = "asst_Cc8qg96Q0Ty1lNbpxYuodv4x"

async def test_ceo_log():
    """Test CEO Log Agent directly."""
    
    print("\n🚀 Testing CEO Log Agent")
    print("=" * 60)
    
    # Configuration
    endpoint = os.getenv("AZURE_AI_AGENT_ENDPOINT")
    api_version = os.getenv("AZURE_AI_AGENT_API_VERSION", "2024-12-01-preview")
    model_deployment = os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME", "gpt-35-turbo")
    
    print(f"CEO Log Agent ID: {CEO_LOG_AGENT_ID}")
    print(f"Endpoint: {endpoint[:80]}...")
    
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
            print("\nRetrieving CEO Log Agent...")
            agent_def = await client.agents.get_agent(CEO_LOG_AGENT_ID)
            print(f"✅ Agent retrieved: {agent_def.name}")
            print(f"Description: {agent_def.description}")
            
            # Create agent instance
            agent = AzureAIAgent(client=client, definition=agent_def)
            
            # Create channel
            print("\nCreating conversation channel...")
            channel = await agent.create_channel()
            print("✅ Channel created")
            
            # Test message
            test_message = f"""
            CEO Log Entry - {datetime.now().strftime('%Y-%m-%d %H:%M')}
            
            Today marks a significant milestone for StratOS. We've successfully deployed all 15 agents 
            to Azure AI Agent Service. The multi-agent architecture is now fully operational.
            
            Key achievements:
            - Strategic Foundation agents deployed (CEO Log, North Star, Memory Recall)
            - Analysis Intelligence agents live (SWOT/TOWS, Risk/Opportunity)
            - Planning Execution agents ready (Initiative Generation, Resource Optimization)
            
            Next steps:
            1. Test inter-agent communication
            2. Validate data persistence
            3. Performance benchmarking
            
            Team morale is high. This positions us well for Q2 launch.
            
            Categories: milestone, technology, strategic_planning
            """
            
            print("\n📝 Sending CEO log entry...")
            print("-" * 60)
            print(test_message)
            print("-" * 60)
            
            # Send message
            user_message = ChatMessageContent(
                role=AuthorRole.USER, 
                content=test_message
            )
            
            print("\n🤖 CEO LOG AGENT RESPONSE:")
            print("-" * 60)
            
            # Get response
            response_text = ""
            async for response in channel.invoke(agent):
                if hasattr(response, 'content') and response.content:
                    chunk = str(response.content)
                    response_text += chunk
                    print(chunk, end="", flush=True)
            
            print("\n" + "-" * 60)
            
            # If no response, try a different approach
            if not response_text.strip():
                print("\n⚠️  No response received. Trying direct message...")
                
                # Try sending a simpler message
                simple_message = "Please acknowledge this CEO log entry about our successful agent deployment."
                user_message2 = ChatMessageContent(
                    role=AuthorRole.USER,
                    content=simple_message
                )
                
                async for response in channel.invoke(agent):
                    if hasattr(response, 'content') and response.content:
                        print(response.content, end="", flush=True)
                print()
            
            print(f"\n✅ Test completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ceo_log())