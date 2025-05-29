"""Deploy orchestrator with enhanced response handling to show actual agent responses"""

import os
import asyncio
from openai import AsyncAzureOpenAI
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
# ConnectionConfig imported inline if needed
import json
from datetime import datetime

# Environment configuration
subscription_id = "fce3ed09-9636-4ead-b7f0-53581559f0ee"
resource_group_name = "rg-multi-agent"  
ai_project_name = "ai-project-multi-agent"
ai_foundry_endpoint = "https://aistudiousecentral123.api.azureml.ms"
openai_deployment_name = "gpt-4o"

ORCHESTRATOR_INSTRUCTIONS = """You are the StratOS Main Orchestrator, responsible for routing strategic planning requests to specialized agents.

Your specialists include:
1. CEO Log Agent - For logging business updates, meeting summaries, and capturing organizational knowledge
2. North Star Agent - For defining and managing high-level strategic goals
3. Memory Recall Agent - For retrieving historical information and past experiences
4. Preference Learning Agent - For understanding and adapting to leadership preferences

CRITICAL RESPONSE INSTRUCTIONS:
When a user makes a request:

1. First analyze which specialist is best suited
2. Announce the delegation: "I'll connect you with the [Specialist] specialist..."
3. Invoke the appropriate tool
4. WAIT for the tool response
5. ALWAYS include the tool's response in your output with this format:
   
   "I'll connect you with the [Specialist] specialist..."
   
   [Specialist]'s response:
   [INCLUDE THE COMPLETE TOOL RESPONSE HERE]

IMPORTANT: You MUST include the tool's response in your output. Do not end your response with just the delegation announcement.

Example:
User: "Log today's board meeting"
You: "I'll connect you with the CEO Log specialist to log this board meeting update.

CEO Log specialist's response:
[ACTUAL RESPONSE FROM THE TOOL]"
"""

async def deploy_enhanced_orchestrator():
    """Deploy orchestrator with enhanced response handling"""
    
    credential = DefaultAzureCredential()
    
    # Create AI Project client
    project_client = AIProjectClient(
        subscription_id=subscription_id,
        resource_group_name=resource_group_name,
        ai_foundry_project_name=ai_project_name,
        endpoint=ai_foundry_endpoint,
        credential=credential
    )
    
    # Create OpenAI client
    openai_conn = await project_client.connections.get(name="sk-multi-agent-openai")
    openai_conn_id = openai_conn.id
    
    # Extract connection details
    api_key = openai_conn.properties.credentials.key if hasattr(openai_conn.properties, 'credentials') else openai_conn.properties.api_key
    endpoint = openai_conn.properties.target
    
    openai_client = AsyncAzureOpenAI(
        api_key=api_key,
        azure_endpoint=endpoint,
        api_version="2024-10-01-preview"
    )
    
    # Delete existing orchestrator if it exists
    print("Checking for existing orchestrator...")
    try:
        existing = await openai_client.beta.assistants.retrieve(
            assistant_id="asst_DvAoA85m6eCsWdOT2bsTxE6i"
        )
        if existing:
            print("Deleting existing orchestrator...")
            await openai_client.beta.assistants.delete(
                assistant_id="asst_DvAoA85m6eCsWdOT2bsTxE6i"
            )
            print("Existing orchestrator deleted.")
    except:
        print("No existing orchestrator found.")
    
    # Create new orchestrator with enhanced instructions
    print("\nCreating enhanced orchestrator...")
    orchestrator = await openai_client.beta.assistants.create(
        model=openai_deployment_name,
        name="StratOS Main Orchestrator Enhanced",
        instructions=ORCHESTRATOR_INSTRUCTIONS,
        tools=[
            {
                "type": "connected_agent",
                "agent_id": "asst_T01KHUc5FoIupJR2C7RCxOhO"  # CEO Log Agent
            },
            {
                "type": "connected_agent", 
                "agent_id": "asst_mGfN5IYqsL17Jx7s6hEGlnQA"  # North Star Agent
            },
            {
                "type": "connected_agent",
                "agent_id": "asst_qbgCLx2XgO9E4W9vJCHAWoQw"  # Memory Recall Agent
            },
            {
                "type": "connected_agent",
                "agent_id": "asst_JxEgAcYJN42LIXKT8X1Jvz60"  # Preference Learning Agent
            }
        ],
        metadata={
            "type": "orchestrator",
            "enhanced_response_handling": "true",
            "version": "2.0",
            "deployment_time": datetime.now().isoformat()
        }
    )
    
    print(f"\n✅ Enhanced orchestrator deployed successfully!")
    print(f"ID: {orchestrator.id}")
    print(f"Name: {orchestrator.name}")
    print(f"Enhanced response handling: Enabled")
    
    # Save deployment info
    deployment_info = {
        "orchestrator_id": orchestrator.id,
        "enhanced_response_handling": True,
        "deployment_time": datetime.now().isoformat(),
        "instructions_snippet": "ALWAYS include the tool's response in your output"
    }
    
    with open("enhanced_orchestrator_deployment.json", "w") as f:
        json.dump(deployment_info, f, indent=2)
    
    print("\nDeployment info saved to enhanced_orchestrator_deployment.json")
    
    await credential.close()
    await openai_client.close()
    await project_client.close()

if __name__ == "__main__":
    asyncio.run(deploy_enhanced_orchestrator())