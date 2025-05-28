#!/usr/bin/env python3
"""
Show telemetry from all agents with tool invocations
"""

import json
from pathlib import Path
from datetime import datetime

def display_agent_telemetry(agent_name, telemetry_file):
    """Display telemetry for a single agent"""
    
    with open(telemetry_file, 'r') as f:
        data = json.load(f)
    
    print(f"\n{'='*80}")
    print(f"{agent_name.upper()} - TOOL INVOCATIONS")
    print(f"{'='*80}")
    
    # Count events
    queries = 0
    delegations = 0
    
    for event in data.get('events', []):
        if event.get('event_type') == 'query_sent':
            queries += 1
            query_data = event.get('data', {})
            print(f"\n📤 Query: {query_data.get('query', '')[:80]}...")
            
        elif event.get('event_type') == 'response_received':
            response_data = event.get('data', {})
            if response_data.get('delegation_detected'):
                print(f"✅ Delegation: {response_data.get('response_preview', '')[:80]}...")
                
        elif event.get('event_type') == 'delegation_confirmed':
            delegations += 1
            delegation_data = event.get('data', {})
            print(f"🔀 Routed to: {delegation_data.get('type')}_specialist")
    
    print(f"\n📊 Results: {delegations}/{queries} successful delegations")
    
    return queries, delegations

def main():
    """Display telemetry for all agents"""
    
    telemetry_base = Path(__file__).parent.parent / "telemetry"
    
    print("\n" + "="*80)
    print("STRATOS CONNECTED AGENTS - COMPLETE TELEMETRY SUMMARY")
    print("="*80)
    
    # Find and display telemetry for each agent
    agents = {
        "CEO Log Agent": "ceo_log_agent",
        "North Star Agent": "north_star_agent", 
        "Memory Recall Agent": "memory_recall_agent",
        "Preference Learning Agent": "preference_learning_agent"
    }
    
    total_queries = 0
    total_delegations = 0
    
    for agent_name, agent_dir in agents.items():
        agent_path = telemetry_base / agent_dir
        if agent_path.exists():
            # Find most recent telemetry file
            files = list(agent_path.glob("*.json"))
            if files:
                latest_file = sorted(files)[-1]
                queries, delegations = display_agent_telemetry(agent_name, latest_file)
                total_queries += queries
                total_delegations += delegations
            else:
                print(f"\n{agent_name}: No telemetry files found")
        else:
            print(f"\n{agent_name}: Directory not found")
    
    # Overall summary
    print(f"\n{'='*80}")
    print(f"OVERALL SYSTEM PERFORMANCE")
    print(f"{'='*80}")
    print(f"Total Queries: {total_queries}")
    print(f"Successful Delegations: {total_delegations}")
    print(f"Overall Success Rate: {total_delegations}/{total_queries} ({total_delegations/total_queries*100:.0f}%)")
    
    # Show orchestrator configuration
    deployment_file = Path(__file__).parent.parent.parent / "stratos/archive/stratos_deployment_info.json"
    if deployment_file.exists():
        with open(deployment_file, 'r') as f:
            deployment = json.load(f)
        
        print(f"\n🎯 ORCHESTRATOR CONFIGURATION:")
        print(f"ID: {deployment['orchestrator']['id']}")
        print(f"Name: {deployment['orchestrator']['name']}")
        print(f"Connected Agents: {', '.join(deployment['orchestrator']['connected_agents'])}")

if __name__ == "__main__":
    main()