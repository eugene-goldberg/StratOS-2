#!/usr/bin/env python3
"""
Capture telemetry for connected agents test.
Runs a test and immediately captures the telemetry details.
"""

import asyncio
import os
import sys
import json
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import Azure SDK components
from azure.identity.aio import DefaultAzureCredential
from azure.ai.projects.aio import AIProjectClient
from semantic_kernel.agents import AzureAIAgent

# Import telemetry
from core.telemetry import initialize_telemetry, create_span_context, add_span_attributes

# Initialize telemetry
tracer = initialize_telemetry(
    service_name="connected-agents-telemetry-capture",
    service_version="1.0.0"
)

telemetry_data = {
    "test_id": f"test_{int(time.time())}",
    "start_time": datetime.now().isoformat(),
    "operations": []
}

async def capture_telemetry_test():
    """Run test and capture telemetry."""
    
    orchestrator_id = os.getenv("MAIN_ORCHESTRATOR_AGENT_ID")
    endpoint = os.getenv("AZURE_AI_PROJECT_CONNECTION_STRING")
    
    print(f"=== CONNECTED AGENTS TELEMETRY CAPTURE ===")
    print(f"Test ID: {telemetry_data['test_id']}")
    print(f"Orchestrator: {orchestrator_id}")
    print(f"Start Time: {telemetry_data['start_time']}")
    print("="*50)
    
    # Main telemetry span
    with create_span_context("connected_agents.telemetry_capture", {
        "test.id": telemetry_data["test_id"],
        "orchestrator.id": orchestrator_id
    }) as main_span:
        
        async with DefaultAzureCredential() as credential, \
                   AIProjectClient(endpoint=endpoint, credential=credential) as client:
            
            orchestrator_def = await client.agents.get_agent(agent_id=orchestrator_id)
            orchestrator_agent = AzureAIAgent(client=client, definition=orchestrator_def)
            
            # Test 1: Weather
            print("\n[TEST 1] Weather Request")
            print("-" * 30)
            
            with create_span_context("test.weather_delegation", {
                "test.type": "weather",
                "request.city": "Seattle"
            }) as weather_span:
                
                start = time.time()
                response = ""
                print("Sending: What's the weather in Seattle?")
                
                async for part in orchestrator_agent.invoke(messages="What's the weather in Seattle?"):
                    if hasattr(part, 'content') and part.content:
                        response += str(part.content)
                
                duration = time.time() - start
                
                # Record telemetry
                operation = {
                    "type": "weather_delegation",
                    "request": "What's the weather in Seattle?",
                    "response_preview": response[:200] + "..." if len(response) > 200 else response,
                    "duration_seconds": round(duration, 2),
                    "delegation_found": "weather information specialist" in response,
                    "timestamp": datetime.now().isoformat()
                }
                telemetry_data["operations"].append(operation)
                
                print(f"Response: {operation['response_preview']}")
                print(f"Duration: {duration:.2f}s")
                print(f"Delegation: {'YES' if operation['delegation_found'] else 'NO'}")
                
                if weather_span:
                    add_span_attributes(weather_span, {
                        "response.length": len(response),
                        "response.duration": duration,
                        "delegation.success": operation['delegation_found']
                    })
            
            # Test 2: Calculator
            print("\n[TEST 2] Calculator Request")
            print("-" * 30)
            
            with create_span_context("test.calculator_delegation", {
                "test.type": "calculator",
                "operation": "multiplication"
            }) as calc_span:
                
                start = time.time()
                response = ""
                print("Sending: What is 789 times 456?")
                
                async for part in orchestrator_agent.invoke(messages="What is 789 times 456?"):
                    if hasattr(part, 'content') and part.content:
                        response += str(part.content)
                
                duration = time.time() - start
                
                # Record telemetry
                operation = {
                    "type": "calculator_delegation",
                    "request": "What is 789 times 456?",
                    "response_preview": response[:200] + "..." if len(response) > 200 else response,
                    "duration_seconds": round(duration, 2),
                    "delegation_found": "mathematical" in response.lower(),
                    "result_found": "359784" in response,
                    "timestamp": datetime.now().isoformat()
                }
                telemetry_data["operations"].append(operation)
                
                print(f"Response: {operation['response_preview']}")
                print(f"Duration: {duration:.2f}s")
                print(f"Delegation: {'YES' if operation['delegation_found'] else 'NO'}")
                print(f"Correct Result: {'YES' if operation['result_found'] else 'NO'}")
                
                if calc_span:
                    add_span_attributes(calc_span, {
                        "response.length": len(response),
                        "response.duration": duration,
                        "delegation.success": operation['delegation_found'],
                        "calculation.correct": operation['result_found']
                    })
            
            # Test 3: Greeting
            print("\n[TEST 3] Greeting Request")
            print("-" * 30)
            
            with create_span_context("test.greeting_delegation", {
                "test.type": "greeting"
            }) as greet_span:
                
                start = time.time()
                response = ""
                print("Sending: Give me an enthusiastic greeting!")
                
                async for part in orchestrator_agent.invoke(messages="Give me an enthusiastic greeting!"):
                    if hasattr(part, 'content') and part.content:
                        response += str(part.content)
                
                duration = time.time() - start
                
                # Record telemetry
                operation = {
                    "type": "greeting_delegation",
                    "request": "Give me an enthusiastic greeting!",
                    "response_preview": response[:200] + "..." if len(response) > 200 else response,
                    "duration_seconds": round(duration, 2),
                    "delegation_found": "greeting specialist" in response,
                    "timestamp": datetime.now().isoformat()
                }
                telemetry_data["operations"].append(operation)
                
                print(f"Response: {operation['response_preview']}")
                print(f"Duration: {duration:.2f}s")
                print(f"Delegation: {'YES' if operation['delegation_found'] else 'NO'}")
                
                if greet_span:
                    add_span_attributes(greet_span, {
                        "response.length": len(response),
                        "response.duration": duration,
                        "delegation.success": operation['delegation_found']
                    })
    
    telemetry_data["end_time"] = datetime.now().isoformat()
    telemetry_data["total_duration"] = sum(op["duration_seconds"] for op in telemetry_data["operations"])
    
    # Save telemetry data
    filename = f"telemetry_capture_{telemetry_data['test_id']}.json"
    with open(filename, 'w') as f:
        json.dump(telemetry_data, f, indent=2)
    
    print(f"\n{'='*50}")
    print("TELEMETRY SUMMARY")
    print(f"{'='*50}")
    print(f"Total Operations: {len(telemetry_data['operations'])}")
    print(f"Total Duration: {telemetry_data['total_duration']:.2f}s")
    print(f"Telemetry saved to: {filename}")
    
    # Display telemetry details
    print(f"\n{'='*50}")
    print("TELEMETRY DETAILS")
    print(f"{'='*50}")
    print(json.dumps(telemetry_data, indent=2))

if __name__ == "__main__":
    asyncio.run(capture_telemetry_test())