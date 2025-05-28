#!/usr/bin/env python3
"""
Extract and display tool invocations from telemetry files
"""

import json
import sys
from pathlib import Path
from datetime import datetime

def display_tool_invocations(telemetry_file):
    """Extract and display tool invocations from telemetry"""
    
    with open(telemetry_file, 'r') as f:
        data = json.load(f)
    
    print(f"\n{'='*80}")
    print(f"TOOL INVOCATIONS AND API TRACES")
    print(f"{'='*80}")
    print(f"Session: {data.get('session_id', 'N/A')}")
    print(f"Agent: {data.get('agent_name', 'N/A')}")
    print(f"{'='*80}\n")
    
    # Extract key events
    orchestrator_tools = None
    queries = []
    responses = []
    delegations = []
    
    for event in data.get('events', []):
        event_type = event.get('event_type')
        event_data = event.get('data', {})
        
        if event_type == 'orchestrator_fetch_complete':
            orchestrator_tools = event_data.get('tools', [])
        elif event_type == 'query_sent':
            queries.append({
                'time': event.get('timestamp'),
                'query': event_data.get('query'),
                'target': event_data.get('target'),
                'function': event_data.get('function')
            })
        elif event_type == 'response_received':
            responses.append({
                'time': event.get('timestamp'),
                'response': event_data.get('response_preview'),
                'length': event_data.get('response_length'),
                'delegation': event_data.get('delegation_detected')
            })
        elif event_type == 'delegation_confirmed':
            delegations.append({
                'time': event.get('timestamp'),
                'type': event_data.get('type'),
                'scenario': event_data.get('scenario')
            })
    
    # Display orchestrator tools
    print("🔧 ORCHESTRATOR CONNECTED AGENT TOOLS:")
    print("-" * 60)
    if orchestrator_tools:
        for tool in orchestrator_tools:
            print(f"Tool Name: {tool.get('name')}")
            print(f"Tool ID: {tool.get('id')}")
            print()
    
    # Display query/response pairs with delegations
    print("\n📡 API INVOCATION FLOW:")
    print("-" * 60)
    
    for i, query in enumerate(queries):
        print(f"\n[{i+1}] QUERY at {query['time']}")
        print(f"To: {query['target']}")
        print(f"Function: {query['function']}")
        print(f"Query: \"{query['query']}\"")
        
        if i < len(responses):
            response = responses[i]
            print(f"\nRESPONSE at {response['time']}")
            print(f"Length: {response['length']} chars")
            print(f"Delegation: {'YES' if response['delegation'] else 'NO'}")
            print(f"Response: \"{response['response']}\"")
            
            # Find matching delegation
            matching_delegations = [d for d in delegations if d['scenario'] == query.get('function')]
            if matching_delegations:
                delegation = matching_delegations[0]
                print(f"\n✅ TOOL INVOKED: {delegation['type']}_specialist")
                print(f"   Scenario: {delegation['scenario']}")
        
        print("-" * 60)
    
    # Summary
    print(f"\n📊 SUMMARY:")
    print(f"Total Queries: {len(queries)}")
    print(f"Total Responses: {len(responses)}")
    print(f"Successful Delegations: {len(delegations)}")
    print(f"Success Rate: {len(delegations)}/{len(queries)} ({len(delegations)/len(queries)*100:.0f}%)")

if __name__ == "__main__":
    # Find most recent telemetry file
    telemetry_dir = Path(__file__).parent.parent
    
    if len(sys.argv) > 1:
        telemetry_file = sys.argv[1]
    else:
        # Find preference learning telemetry
        pref_dir = telemetry_dir / "preference_learning_agent"
        if pref_dir.exists():
            files = list(pref_dir.glob("*.json"))
            if files:
                telemetry_file = sorted(files)[-1]
            else:
                print("No telemetry files found")
                sys.exit(1)
        else:
            print(f"Directory not found: {pref_dir}")
            sys.exit(1)
    
    display_tool_invocations(telemetry_file)