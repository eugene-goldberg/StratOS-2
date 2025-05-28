#!/usr/bin/env python3
"""
Analyze telemetry traces to show actual delegations and tool calls
"""
import json
from datetime import datetime

def analyze_traces():
    """Analyze the captured telemetry traces"""
    
    # Load the telemetry data
    import glob
    import os
    
    # Find the most recent telemetry file
    telemetry_files = glob.glob('agent_telemetry_*.json')
    if not telemetry_files:
        print("No telemetry files found!")
        return
    
    latest_file = max(telemetry_files, key=os.path.getmtime)
    print(f"Loading telemetry from: {latest_file}")
    
    with open(latest_file, 'r') as f:
        data = json.load(f)
    
    print(f"Analyzing {data['trace_count']} traces from {data['query_time']}\n")
    
    # Group traces by thread and analyze
    threads = {}
    
    for trace in data['traces']:
        props = json.loads(trace['Properties'])
        thread_id = props.get('gen_ai.thread.id', 'unknown')
        
        if thread_id not in threads:
            threads[thread_id] = {
                'traces': [],
                'agent_id': props.get('gen_ai.agent.id', 'unknown'),
                'start_time': trace['TimeGenerated']
            }
        
        threads[thread_id]['traces'].append({
            'time': trace['TimeGenerated'],
            'message': trace['Message'],
            'properties': props
        })
    
    # Analyze each thread
    for thread_id, thread_data in threads.items():
        print(f"\n{'='*60}")
        print(f"Thread: {thread_id}")
        print(f"Agent: {thread_data['agent_id']}")
        print(f"Start: {thread_data['start_time']}")
        print(f"Traces: {len(thread_data['traces'])}")
        
        # Sort traces by time
        thread_data['traces'].sort(key=lambda x: x['time'])
        
        # Analyze the flow
        for trace in thread_data['traces']:
            msg_type = trace['message']
            props = trace['properties']
            
            if msg_type == "gen_ai.user.message":
                print(f"\n📥 USER MESSAGE")
                content = props.get('gen_ai.event.content', '')
                print(f"   Content: {content}")
                
            elif msg_type == "gen_ai.run_step.tool_calls":
                print(f"\n🔧 TOOL CALLS")
                content = props.get('gen_ai.event.content', '')
                if content:
                    try:
                        tool_data = json.loads(content)
                        for tool_call in tool_data.get('tool_calls', []):
                            print(f"   Tool: {tool_call.get('type', 'unknown')}")
                            print(f"   ID: {tool_call.get('id', 'unknown')}")
                            if tool_call.get('type') == 'connected_agent':
                                print(f"   ✅ DELEGATION TO CONNECTED AGENT!")
                    except:
                        print(f"   Raw: {content}")
                
                # Show token usage
                input_tokens = props.get('gen_ai.usage.input_tokens', 'N/A')
                output_tokens = props.get('gen_ai.usage.output_tokens', 'N/A')
                print(f"   Tokens: {input_tokens} in / {output_tokens} out")
                
            elif msg_type == "gen_ai.run_step.message_creation":
                print(f"\n💬 MESSAGE CREATION")
                msg_id = props.get('gen_ai.message.id', 'unknown')
                print(f"   Message ID: {msg_id}")
                
                # Show timing
                start = props.get('gen_ai.run_step.start.timestamp', '')
                end = props.get('gen_ai.run_step.end.timestamp', '')
                if start and end:
                    try:
                        start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                        end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
                        duration = (end_dt - start_dt).total_seconds()
                        print(f"   Duration: {duration:.2f} seconds")
                    except:
                        pass
    
    # Summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"- Total threads: {len(threads)}")
    
    # Count delegations
    delegations = 0
    for trace in data['traces']:
        if 'connected_agent' in trace.get('Properties', ''):
            delegations += 1
    
    print(f"- Connected agent delegations: {delegations}")
    
    # Show unique agents
    agents = set()
    for trace in data['traces']:
        props = json.loads(trace['Properties'])
        agent_id = props.get('gen_ai.agent.id')
        if agent_id:
            agents.add(agent_id)
    
    print(f"- Unique agents: {len(agents)}")
    for agent in agents:
        print(f"  • {agent}")

if __name__ == "__main__":
    analyze_traces()