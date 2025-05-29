"""Demonstrate how to get actual agent responses by invoking agents directly"""

import asyncio
from azure.ai.projects.aio import AIProjectClient
# Agent imported from client
from azure.identity.aio import DefaultAzureCredential
from datetime import datetime
import json

# Application Insights configuration
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace

configure_azure_monitor(
    connection_string="InstrumentationKey=c37055e8-1c8c-410d-ab37-e49f009a0d36;IngestionEndpoint=https://eastus-8.in.applicationinsights.azure.com/;LiveEndpoint=https://eastus.livediagnostics.monitor.azure.com/;ApplicationId=3f9d10f1-3df5-4c80-ab03-41e0b8a02e31"
)

tracer = trace.get_tracer(__name__)

# Environment configuration
subscription_id = "fce3ed09-9636-4ead-b7f0-53581559f0ee"
resource_group_name = "rg-multi-agent"
ai_project_name = "ai-project-multi-agent"
ai_foundry_endpoint = "https://aistudiousecentral123.api.azureml.ms"

# Agent IDs from deployment
AGENT_IDS = {
    "CEO Log Agent": "asst_T01KHUc5FoIupJR2C7RCxOhO",
    "North Star Agent": "asst_mGfN5IYqsL17Jx7s6hEGlnQA", 
    "Memory Recall Agent": "asst_qbgCLx2XgO9E4W9vJCHAWoQw",
    "Preference Learning Agent": "asst_JxEgAcYJN42LIXKT8X1Jvz60"
}

async def get_agent_response(project_client, agent_id, agent_name, query):
    """Get response from a specific agent"""
    
    print(f"\n🔍 Testing {agent_name}")
    print(f"Query: {query}")
    
    with tracer.start_as_current_span(f"test_{agent_name}") as span:
        span.set_attribute("agent.name", agent_name)
        span.set_attribute("agent.id", agent_id)
        span.set_attribute("query", query)
        
        # Get the agent
        agent = await project_client.agents.get_agent(agent_id)
        
        # Create thread
        thread = await project_client.agents.threads.create()
        
        # Send message
        await project_client.agents.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=query
        )
        
        # Process the request with streaming
        response = ""
        run = await project_client.agents.threads.runs.create(
            thread_id=thread.id,
            assistant_id=agent_id
        )
        
        # Wait for completion and get response
        while run.status in ["queued", "in_progress", "requires_action"]:
            await asyncio.sleep(0.5)
            run = await project_client.agents.threads.runs.retrieve(
                thread_id=thread.id,
                run_id=run.id
            )
        
        # Get messages
        messages = await project_client.agents.threads.messages.list(thread_id=thread.id)
        for msg in messages.data:
            if msg.role == "assistant":
                for content in msg.content:
                    if hasattr(content, 'text') and hasattr(content.text, 'value'):
                        response = content.text.value
                        break
                break
        
        print(f"\n✅ {agent_name} Response:")
        print("-" * 50)
        print(response)
        print("-" * 50)
        
        span.set_attribute("response.length", len(response))
        span.set_attribute("response.preview", response[:200] if response else "No response")
        
        return {
            "agent_name": agent_name,
            "agent_id": agent_id,
            "query": query,
            "response": response,
            "response_length": len(response)
        }

async def demonstrate_actual_responses():
    """Show actual responses from each agent"""
    
    credential = DefaultAzureCredential()
    
    # Create AI Project client
    project_client = AIProjectClient(
        subscription_id=subscription_id,
        resource_group_name=resource_group_name,
        ai_foundry_project_name=ai_project_name,
        endpoint=ai_foundry_endpoint,
        credential=credential
    )
    
    # Test queries for each agent
    test_cases = [
        {
            "agent": "CEO Log Agent",
            "query": "Log today's board meeting: We discussed Q4 results showing 15% revenue growth and approved the 2025 R&D budget of $5M"
        },
        {
            "agent": "North Star Agent",
            "query": "What are our current strategic goals and priorities?"
        },
        {
            "agent": "Memory Recall Agent", 
            "query": "What important decisions were made in our last board meeting?"
        },
        {
            "agent": "Preference Learning Agent",
            "query": "How does our CEO prefer to receive strategic updates?"
        }
    ]
    
    print("=" * 60)
    print("DEMONSTRATING ACTUAL AGENT RESPONSES")
    print("=" * 60)
    print("\nThis shows what each agent ACTUALLY returns when invoked directly.")
    print("Compare this to what the orchestrator shows.\n")
    
    results = []
    
    for test in test_cases:
        agent_name = test["agent"]
        agent_id = AGENT_IDS[agent_name]
        query = test["query"]
        
        try:
            result = await get_agent_response(project_client, agent_id, agent_name, query)
            results.append(result)
        except Exception as e:
            print(f"❌ Error with {agent_name}: {str(e)}")
            results.append({
                "agent_name": agent_name,
                "error": str(e)
            })
    
    # Summary
    print("\n\n📊 SUMMARY")
    print("=" * 60)
    print("\nThese are the ACTUAL responses that agents provide.")
    print("The orchestrator should be showing these responses, not just delegation announcements.")
    
    print("\nResponse lengths:")
    for result in results:
        if "error" not in result:
            print(f"- {result['agent_name']}: {result['response_length']} characters")
    
    # Save results
    report = {
        "demonstration_time": datetime.now().isoformat(),
        "purpose": "Show actual agent responses vs orchestrator delegation announcements",
        "key_finding": "Agents DO provide detailed responses when invoked directly",
        "problem": "Orchestrator only shows delegation announcements, not actual responses",
        "results": results
    }
    
    filename = f"actual_agent_responses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\nDetailed results saved to: {filename}")
    
    await credential.close()
    await project_client.close()

if __name__ == "__main__":
    asyncio.run(demonstrate_actual_responses())