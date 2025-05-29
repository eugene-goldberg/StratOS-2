"""
Fix orchestrator to show actual agent responses
Based on successful example from CEO_TELEMETRY_EVIDENCE.json
"""

import asyncio
import os
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from datetime import datetime
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Application Insights for telemetry
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace

configure_azure_monitor(
    connection_string="InstrumentationKey=c37055e8-1c8c-410d-ab37-e49f009a0d36;IngestionEndpoint=https://eastus-8.in.applicationinsights.azure.com/;LiveEndpoint=https://eastus.livediagnostics.monitor.azure.com/;ApplicationId=3f9d10f1-3df5-4c80-ab03-41e0b8a02e31"
)

tracer = trace.get_tracer(__name__)

# Azure configuration
subscription_id = "fce3ed09-9636-4ead-b7f0-53581559f0ee"
resource_group_name = "rg-multi-agent"
ai_project_name = "ai-project-multi-agent"
ai_foundry_endpoint = "https://aistudiousecentral123.api.azureml.ms"

async def test_orchestrator_with_proper_invocation():
    """Test orchestrator using the same pattern that worked in CEO_TELEMETRY_EVIDENCE.json"""
    
    credential = DefaultAzureCredential()
    
    # Create AI Project client
    project_client = AIProjectClient(
        subscription_id=subscription_id,
        resource_group_name=resource_group_name,
        ai_foundry_project_name=ai_project_name,
        endpoint=ai_foundry_endpoint,
        credential=credential
    )
    
    # Get the orchestrator
    orchestrator_id = "asst_DvAoA85m6eCsWdOT2bsTxE6i"
    
    try:
        orchestrator_agent = await project_client.agents.get_agent(orchestrator_id)
        logger.info(f"Connected to orchestrator: {orchestrator_id}")
        
        # Test queries - using exact same format as successful test
        test_queries = [
            "Generate tags for this CEO log entry: 'Team meeting went well. Discussed Q2 roadmap and AI strategy.'",
            "Log this: Board meeting successful. Approved new budget and discussed expansion plans.",
            "What are our north star metrics for customer satisfaction?"
        ]
        
        for query in test_queries:
            logger.info(f"\n{'='*80}")
            logger.info(f"Query: {query}")
            logger.info("-" * 80)
            
            with tracer.start_as_current_span(f"test_orchestrator") as span:
                span.set_attribute("query", query)
                
                try:
                    # Invoke using the same pattern as the working example
                    response = ""
                    start_time = datetime.now()
                    
                    # Use invoke method with messages parameter
                    async for part in orchestrator_agent.invoke(messages=query):
                        if hasattr(part, 'content') and part.content:
                            response += str(part.content)
                            # Log each part as it comes
                            logger.debug(f"Received part: {part.content}")
                    
                    duration = (datetime.now() - start_time).total_seconds()
                    
                    logger.info(f"\nResponse (took {duration:.1f}s):")
                    logger.info(response)
                    
                    # Analyze response
                    logger.info("\nAnalysis:")
                    
                    # Check for delegation announcement
                    has_delegation = "I'll connect you with" in response
                    logger.info(f"✓ Has delegation announcement: {'Yes' if has_delegation else 'No'}")
                    
                    # Check for actual agent response
                    # Look for patterns that indicate actual agent responses
                    response_indicators = [
                        "has been saved",
                        "has been logged",
                        "Tags:",
                        "Generated tags:",
                        "Entry saved",
                        "Strategic insights:",
                        "North star metric",
                        "Our goal",
                        "The metric"
                    ]
                    
                    has_agent_response = any(indicator in response for indicator in response_indicators)
                    logger.info(f"✓ Has agent response: {'Yes' if has_agent_response else 'No'}")
                    
                    if has_agent_response:
                        logger.info("✅ SUCCESS: Orchestrator returned BOTH delegation and agent response!")
                        # Find where the agent response starts
                        for indicator in response_indicators:
                            if indicator in response:
                                idx = response.find(indicator)
                                agent_response_part = response[idx:]
                                logger.info(f"\nAgent response portion: '{agent_response_part[:100]}...'")
                                break
                    else:
                        logger.warning("⚠️  Only delegation announcement found, no agent response")
                    
                    # Check response structure
                    if "DIRECTIVE" in response:
                        logger.info("✓ Response includes DIRECTIVE structure (like working example)")
                    
                    span.set_attribute("has_delegation", has_delegation)
                    span.set_attribute("has_agent_response", has_agent_response)
                    span.set_attribute("response_length", len(response))
                    
                except Exception as e:
                    logger.error(f"Error during invocation: {str(e)}")
                    span.record_exception(e)
            
            # Small delay between tests
            await asyncio.sleep(3)
        
        # Try alternative: Thread-based approach
        logger.info("\n\n" + "="*80)
        logger.info("TESTING THREAD-BASED APPROACH")
        logger.info("="*80)
        
        # Create thread
        thread = await project_client.agents.threads.create()
        
        # Add message
        await project_client.agents.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content="Generate tags for this CEO log entry: 'Product launch successful. Great team effort.'"
        )
        
        # Create run
        run = await project_client.agents.threads.runs.create(
            thread_id=thread.id,
            assistant_id=orchestrator_id
        )
        
        # Wait for completion
        while run.status in ["queued", "in_progress", "requires_action"]:
            await asyncio.sleep(1)
            run = await project_client.agents.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
        
        logger.info(f"Run completed with status: {run.status}")
        
        # Get all messages
        messages = await project_client.agents.threads.messages.list(thread_id=thread.id)
        
        logger.info("\nThread messages:")
        for msg in messages.data:
            if msg.role == "assistant":
                for content in msg.content:
                    if hasattr(content, 'text') and hasattr(content.text, 'value'):
                        assistant_response = content.text.value
                        logger.info(f"\nAssistant: {assistant_response}")
                        
                        # Check if this includes agent response
                        has_agent_response = any(indicator in assistant_response for indicator in response_indicators)
                        logger.info(f"\n✓ Thread approach - Has agent response: {'Yes' if has_agent_response else 'No'}")
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
    finally:
        await credential.close()
        await project_client.close()

if __name__ == "__main__":
    asyncio.run(test_orchestrator_with_proper_invocation())