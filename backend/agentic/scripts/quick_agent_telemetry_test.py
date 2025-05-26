#!/usr/bin/env python3
"""
Quick agent test to generate telemetry traces.
Tests one real agent and generates clear telemetry data.
"""

import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

from azure.identity.aio import DefaultAzureCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings

# Add the agentic directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.telemetry import initialize_telemetry, create_span_context, trace_method


async def main():
    """Quick test of CEO Log Agent with telemetry."""
    
    # Load environment
    backend_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    load_dotenv(backend_env)
    root_env = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    load_dotenv(root_env, override=True)
    
    # Initialize telemetry
    tracer = initialize_telemetry(
        service_name="QuickAgentTest",
        service_version="1.0.0",
        connection_string="InstrumentationKey=189923ab-6ad8-408f-b3f6-7ae4817a3988;IngestionEndpoint=https://eastus-8.in.applicationinsights.azure.com/;LiveEndpoint=https://eastus.livediagnostics.monitor.azure.com/;ApplicationId=dfba6d9b-7df1-4bf5-af6a-2fb21f1881b2"
    )
    
    print("🚀 Quick Agent Telemetry Test")
    print("=" * 60)
    print(f"Time: {datetime.now().isoformat()}")
    
    # Test CEO Log Agent
    agent_id = "asst_N5azTOnrhdlm4K9wC6i9OtHA"
    test_message = f"Test entry at {datetime.now().strftime('%H:%M:%S')} - Market conditions look favorable for Q4"
    
    with create_span_context("test.ceo_log_quick", {
        "test.timestamp": datetime.now().isoformat(),
        "agent.id": agent_id,
        "message": test_message
    }) as span:
        
        print(f"\n📝 Testing CEO Log Agent")
        print(f"   Message: {test_message}")
        
        try:
            # Create SK client
            settings = AzureAIAgentSettings()
            
            async with DefaultAzureCredential() as credential:
                async with AzureAIAgent.create_client(credential=credential, settings=settings) as client:
                    
                    # Get agent
                    agent_def = await client.agents.get_agent(agent_id=agent_id)
                    agent = AzureAIAgent(client=client, definition=agent_def)
                    
                    # Invoke agent
                    print(f"\n   Response: ", end="", flush=True)
                    response_text = ""
                    
                    async for chunk in agent.invoke(message=test_message):
                        if hasattr(chunk, 'content') and chunk.content:
                            chunk_text = str(chunk.content)
                            print(chunk_text, end="", flush=True)
                            response_text += chunk_text
                    
                    print()
                    
                    span.set_attribute("response.length", len(response_text))
                    span.set_attribute("response.success", True)
                    
                    print(f"\n✅ Success! Response length: {len(response_text)} chars")
                    
        except Exception as e:
            span.set_attribute("error", str(e))
            print(f"\n❌ Error: {e}")
    
    print("\n📊 Telemetry data sent to Application Insights")
    print("⏱️  Data should appear within 2-5 minutes")
    print("\n🔍 To view traces:")
    print("1. Go to Azure Portal > Application Insights > stratos-multi-agent-appinsights")
    print("2. Click on 'Transaction search' or 'Logs'")
    print("3. Use query: traces | where customDimensions.['service.name'] == 'QuickAgentTest'")


if __name__ == "__main__":
    asyncio.run(main())