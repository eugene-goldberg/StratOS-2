#!/usr/bin/env python3
"""
Deploy CEO Log Agent with Cosmos DB Integration
Deploys the enhanced CEO Log Agent with Azure Functions tools for persistent storage
"""

import os
import sys
import json
from datetime import datetime
from openai import AzureOpenAI
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.ceo_log_cosmos_tools import CEO_LOG_COSMOS_TOOLS, CEO_LOG_COSMOS_INSTRUCTIONS

# Load environment variables
load_dotenv()

def deploy_ceo_log_cosmos_agent():
    """Deploy CEO Log Agent with Cosmos DB integration"""
    
    print("=" * 80)
    print("CEO LOG AGENT - COSMOS DB INTEGRATION DEPLOYMENT")
    print("=" * 80)
    
    # Validate environment
    required_vars = [
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "CEO_LOG_FUNCTION_URL",
        "CEO_LOG_FUNCTION_KEY"
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("\nPlease set the following in your .env file:")
        print("- AZURE_OPENAI_API_KEY: Your Azure OpenAI API key")
        print("- AZURE_OPENAI_ENDPOINT: Your Azure OpenAI endpoint")
        print("- CEO_LOG_FUNCTION_URL: Base URL for CEO Log Azure Functions")
        print("- CEO_LOG_FUNCTION_KEY: Function key for authentication")
        return None
    
    # Initialize client
    client = AzureOpenAI(
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        api_version="2024-02-15-preview",
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"]
    )
    
    # Update tools with actual Function URLs and keys
    function_base_url = os.getenv("CEO_LOG_FUNCTION_URL")
    function_key = os.getenv("CEO_LOG_FUNCTION_KEY")
    
    # Add authentication to tool URLs
    tools_with_auth = []
    for tool in CEO_LOG_COSMOS_TOOLS:
        tool_copy = tool.copy()
        if "function" in tool_copy and "url" in tool_copy["function"]:
            # Replace placeholder URL with actual URL including function key
            function_name = tool_copy["function"]["name"]
            tool_copy["function"]["url"] = f"{function_base_url}/{function_name}?code={function_key}"
        tools_with_auth.append(tool_copy)
    
    try:
        print("\n📋 Deployment Configuration:")
        print(f"- Agent Name: CEOLogAgent-CosmosDB")
        print(f"- Model: gpt-35-turbo")
        print(f"- Tools: {len(tools_with_auth)} Azure Functions")
        print(f"- Function URL: {function_base_url}")
        print(f"- Enhanced with: Cosmos DB persistence, AI analysis, caching")
        
        # List tools being deployed
        print("\n🛠️  Tools to be deployed:")
        for tool in tools_with_auth:
            if "function" in tool:
                print(f"   - {tool['function']['name']}: {tool['function']['description'][:60]}...")
        
        # Create the assistant
        print("\n🚀 Deploying CEO Log Agent with Cosmos DB integration...")
        
        assistant = client.beta.assistants.create(
            name="CEOLogAgent-CosmosDB",
            instructions=CEO_LOG_COSMOS_INSTRUCTIONS,
            model="gpt-35-turbo",
            tools=tools_with_auth
        )
        
        print(f"\n✅ CEO Log Agent deployed successfully!")
        print(f"   Assistant ID: {assistant.id}")
        
        # Save deployment info
        deployment_info = {
            "agent_name": "CEOLogAgent-CosmosDB",
            "assistant_id": assistant.id,
            "deployment_time": datetime.now().isoformat(),
            "model": "gpt-35-turbo",
            "tools": [tool["function"]["name"] for tool in tools_with_auth if "function" in tool],
            "features": [
                "Cosmos DB persistence",
                "AI-powered analysis",
                "Full-text search",
                "Advanced analytics",
                "Performance caching",
                "Relevance scoring"
            ],
            "function_url": function_base_url,
            "enhanced_capabilities": {
                "storage": "Azure Cosmos DB",
                "search": "Full-text with relevance scoring",
                "analytics": "Pattern recognition and trend analysis",
                "ai_analysis": "Sentiment, tags, insights, action items",
                "performance": "Sub-second responses with caching"
            }
        }
        
        # Save to deployment log
        deployment_file = "ceo_log_cosmos_deployment.json"
        with open(deployment_file, "w") as f:
            json.dump(deployment_info, f, indent=2)
        
        print(f"\n💾 Deployment info saved to: {deployment_file}")
        
        # Print usage instructions
        print("\n📖 Usage Instructions:")
        print("1. The CEO Log Agent is now deployed with Cosmos DB integration")
        print("2. All log entries will be permanently stored in Cosmos DB")
        print("3. Use SaveCEOLog to create entries with AI analysis")
        print("4. Use SearchCEOLogs for powerful querying capabilities")
        print("5. Use AnalyzeLogs for strategic insights and trends")
        
        print("\n🔧 Next Steps:")
        print("1. Deploy Azure Functions: cd ceo-log-functions && func azure functionapp publish <app-name>")
        print("2. Configure Cosmos DB connection in Function App settings")
        print("3. Test the integration with test_ceo_log_cosmos_integration.py")
        print("4. Monitor performance in Application Insights")
        
        return assistant.id
        
    except Exception as e:
        print(f"\n❌ Error deploying CEO Log Agent: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Verify your Azure OpenAI credentials are correct")
        print("2. Ensure you have the necessary permissions")
        print("3. Check that the Azure Functions are deployed and accessible")
        print("4. Verify the function key is correct")
        return None


def verify_deployment(assistant_id: str):
    """Verify the deployed agent"""
    if not assistant_id:
        return
    
    print("\n" + "=" * 80)
    print("VERIFYING DEPLOYMENT")
    print("=" * 80)
    
    try:
        client = AzureOpenAI(
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            api_version="2024-02-15-preview",
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"]
        )
        
        # Retrieve the assistant
        assistant = client.beta.assistants.retrieve(assistant_id)
        
        print(f"\n✅ Agent verified successfully!")
        print(f"   Name: {assistant.name}")
        print(f"   ID: {assistant.id}")
        print(f"   Model: {assistant.model}")
        print(f"   Tools: {len(assistant.tools)}")
        
        # Show tool details
        print("\n📋 Configured Tools:")
        for tool in assistant.tools:
            if hasattr(tool, 'function'):
                print(f"   - {tool.function.name}")
                if hasattr(tool.function, 'url'):
                    # Don't print the full URL with key
                    base_url = tool.function.url.split('?')[0]
                    print(f"     URL: {base_url}")
        
    except Exception as e:
        print(f"\n❌ Error verifying deployment: {str(e)}")


if __name__ == "__main__":
    print("\n🚀 Starting CEO Log Agent Cosmos DB Deployment...\n")
    
    # Deploy the agent
    assistant_id = deploy_ceo_log_cosmos_agent()
    
    # Verify deployment
    if assistant_id:
        verify_deployment(assistant_id)
        
        print("\n✨ Deployment complete! The CEO Log Agent is ready with Cosmos DB integration.")
        print("\n💡 Test the agent with: python test_ceo_log_cosmos_agent.py")
    else:
        print("\n❌ Deployment failed. Please check the errors above and try again.")
        sys.exit(1)