#!/usr/bin/env python3
"""Test CEO Log Agent with HTTP request monitoring."""

import os
import sys
import json
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, List
from openai import AzureOpenAI
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.projects.models import AgentStreamEvent

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Enable HTTP debugging for urllib3 (used by requests)
import http.client as http_client
http_client.HTTPConnection.debuglevel = 1

# Configure requests logging
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

# Configure httpx logging (used by OpenAI client)
httpx_log = logging.getLogger("httpx")
httpx_log.setLevel(logging.DEBUG)

# Configure OpenAI client logging
openai_log = logging.getLogger("openai")
openai_log.setLevel(logging.DEBUG)

class HTTPRequestMonitor:
    """Monitor and capture HTTP requests."""
    
    def __init__(self):
        self.requests: List[Dict[str, Any]] = []
        self.responses: List[Dict[str, Any]] = []
    
    def capture_request(self, method: str, url: str, headers: Dict, body: Any):
        """Capture outgoing request."""
        request_info = {
            "timestamp": datetime.now().isoformat(),
            "method": method,
            "url": url,
            "headers": dict(headers),
            "body": body
        }
        self.requests.append(request_info)
        print(f"\n🔵 HTTP REQUEST CAPTURED:")
        print(f"  Method: {method}")
        print(f"  URL: {url}")
        print(f"  Headers: {json.dumps(dict(headers), indent=2)}")
        if body:
            print(f"  Body: {json.dumps(body, indent=2) if isinstance(body, dict) else body}")
    
    def capture_response(self, status: int, headers: Dict, body: Any):
        """Capture incoming response."""
        response_info = {
            "timestamp": datetime.now().isoformat(),
            "status": status,
            "headers": dict(headers),
            "body": body
        }
        self.responses.append(response_info)
        print(f"\n🟢 HTTP RESPONSE CAPTURED:")
        print(f"  Status: {status}")
        print(f"  Headers: {json.dumps(dict(headers), indent=2)}")
        if body:
            print(f"  Body: {json.dumps(body, indent=2) if isinstance(body, dict) else body}")

async def test_ceo_log_agent():
    """Test CEO Log Agent with HTTP monitoring."""
    
    # Initialize HTTP monitor
    monitor = HTTPRequestMonitor()
    
    # Load environment
    from dotenv import load_dotenv
    load_dotenv()
    load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
    
    print("\n🚀 Starting CEO Log Agent HTTP Monitor Test")
    print("=" * 60)
    
    try:
        # Load deployment info
        deployment_file = os.path.join(
            os.path.dirname(__file__),
            "deployment_info.json"
        )
        
        with open(deployment_file, 'r') as f:
            deployment_info = json.load(f)
        
        ceo_log_info = deployment_info.get("ceo_log_agent", {})
        if not ceo_log_info:
            print("❌ ceo_log_agent not found in deployment info")
            return
        
        print(f"\n📋 CEO Log Agent ID: {ceo_log_info['id']}")
        
        # Initialize Azure AI Project client
        endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
        credential = DefaultAzureCredential()
        project_client = AIProjectClient(
            endpoint=endpoint,
            credential=credential
        )
        
        # Get agent
        print("\n🔍 Retrieving CEO Log Agent...")
        agent = project_client.agents.get_agent(assistant_id=ceo_log_info['id'])
        print(f"✅ Agent retrieved: {agent.name}")
        
        # Create thread
        print("\n📝 Creating conversation thread...")
        thread = project_client.agents.create_thread()
        print(f"✅ Thread created: {thread.id}")
        
        # Test message
        test_message = {
            "role": "user",
            "content": "Save this CEO log entry: 'Testing HTTP monitoring - Strategic decision to implement comprehensive request tracking for Azure Functions integration.'"
        }
        
        print(f"\n💬 Sending message: {test_message['content']}")
        
        # Add message to thread
        message = project_client.agents.create_message(
            thread_id=thread.id,
            **test_message
        )
        
        # Create run and stream response
        print("\n🏃 Running agent...")
        
        # Patch the httpx client to monitor requests
        import httpx
        original_request = httpx.Client.request
        
        def monitored_request(self, method, url, **kwargs):
            # Capture request
            monitor.capture_request(
                method=method,
                url=str(url),
                headers=kwargs.get('headers', {}),
                body=kwargs.get('json', kwargs.get('data'))
            )
            
            # Make actual request
            response = original_request(self, method, url, **kwargs)
            
            # Capture response
            try:
                response_body = response.json()
            except:
                response_body = response.text
            
            monitor.capture_response(
                status=response.status_code,
                headers=dict(response.headers),
                body=response_body
            )
            
            return response
        
        # Apply patch
        httpx.Client.request = monitored_request
        
        # Stream the response
        full_response = ""
        with project_client.agents.create_stream(
            thread_id=thread.id,
            assistant_id=ceo_log_info['id']
        ) as stream:
            for event in stream:
                if event.event == AgentStreamEvent.THREAD_MESSAGE_DELTA:
                    if event.data.delta.content:
                        for content in event.data.delta.content:
                            if content.type == "text" and content.text:
                                full_response += content.text.value
                                print(content.text.value, end='', flush=True)
                
                elif event.event == AgentStreamEvent.THREAD_RUN_REQUIRES_ACTION:
                    print("\n\n🔧 TOOL CALLS DETECTED:")
                    if event.data.required_action and event.data.required_action.submit_tool_outputs:
                        for tool_call in event.data.required_action.submit_tool_outputs.tool_calls:
                            print(f"\n  Tool: {tool_call.function.name}")
                            print(f"  Arguments: {tool_call.function.arguments}")
                            print(f"  ID: {tool_call.id}")
                
                elif event.event == AgentStreamEvent.ERROR:
                    print(f"\n❌ Error: {event.data}")
        
        print(f"\n\n✅ Full Response: {full_response}")
        
        # Summary of captured requests
        print("\n\n📊 HTTP REQUEST SUMMARY:")
        print(f"Total Requests: {len(monitor.requests)}")
        print(f"Total Responses: {len(monitor.responses)}")
        
        # Show Azure Functions requests
        print("\n🔗 Azure Functions Requests:")
        functions_requests = [
            req for req in monitor.requests 
            if 'azurewebsites.net' in req['url'] or 'azure-functions' in req['url']
        ]
        
        if functions_requests:
            for i, req in enumerate(functions_requests, 1):
                print(f"\n  Request {i}:")
                print(f"    URL: {req['url']}")
                print(f"    Method: {req['method']}")
                print(f"    Body: {json.dumps(req['body'], indent=4) if req['body'] else 'None'}")
        else:
            print("  No Azure Functions requests detected")
        
        # Clean up
        print("\n🧹 Cleaning up...")
        project_client.agents.delete_thread(thread_id=thread.id)
        print("✅ Thread deleted")
        
    except Exception as e:
        print(f"\n❌ Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_ceo_log_agent())