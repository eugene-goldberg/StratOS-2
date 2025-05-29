"""Update the existing orchestrator to include response handling instructions"""

import os
import asyncio
from openai import AsyncAzureOpenAI
from azure.identity.aio import DefaultAzureCredential
import json
from datetime import datetime

# Azure OpenAI configuration from environment
api_key = os.getenv("AZURE_OPENAI_API_KEY", "f3c3d913dc4f42d78b5b6ad6bfd3de49")
endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://sk-multi-agent-openai.openai.azure.com/")
deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o")

ENHANCED_INSTRUCTIONS = """You are the StratOS Main Orchestrator, responsible for routing strategic planning requests to specialized agents.

Your specialists include:
1. CEO Log Agent - For logging business updates, meeting summaries, and capturing organizational knowledge
2. North Star Agent - For defining and managing high-level strategic goals
3. Memory Recall Agent - For retrieving historical information and past experiences
4. Preference Learning Agent - For understanding and adapting to leadership preferences

CRITICAL RESPONSE INSTRUCTIONS:
When a user makes a request:

1. First analyze which specialist is best suited
2. Announce the delegation: "I'll connect you with the [Specialist] specialist..."
3. Invoke the appropriate tool using the connected_agent tool type
4. IMPORTANT: After invoking the tool, include this message:
   "I've contacted the [Specialist] specialist. They are processing your request and will provide their response shortly."

Your response should explain what specialist you're connecting them with and why, then confirm that you've made the connection.

Note: The actual specialist response will be delivered directly to you after I process the request."""

async def update_orchestrator():
    """Update orchestrator with enhanced instructions"""
    
    openai_client = AsyncAzureOpenAI(
        api_key=api_key,
        azure_endpoint=endpoint,
        api_version="2024-10-01-preview"
    )
    
    orchestrator_id = "asst_DvAoA85m6eCsWdOT2bsTxE6i"
    
    print(f"Updating orchestrator {orchestrator_id} with enhanced instructions...")
    
    try:
        # Update the assistant
        updated = await openai_client.beta.assistants.update(
            assistant_id=orchestrator_id,
            instructions=ENHANCED_INSTRUCTIONS,
            metadata={
                "type": "orchestrator",
                "enhanced_response_handling": "true",
                "version": "2.1",
                "update_time": datetime.now().isoformat()
            }
        )
        
        print(f"\n✅ Orchestrator updated successfully!")
        print(f"ID: {updated.id}")
        print(f"Name: {updated.name}")
        print(f"Enhanced instructions: Applied")
        
        # Save update info
        update_info = {
            "orchestrator_id": updated.id,
            "enhanced_instructions_applied": True,
            "update_time": datetime.now().isoformat(),
            "key_change": "Added note about specialist responses being delivered after processing"
        }
        
        with open("orchestrator_update_info.json", "w") as f:
            json.dump(update_info, f, indent=2)
        
        print("\nUpdate info saved to orchestrator_update_info.json")
        
    except Exception as e:
        print(f"❌ Error updating orchestrator: {str(e)}")
    
    await openai_client.close()

if __name__ == "__main__":
    asyncio.run(update_orchestrator())