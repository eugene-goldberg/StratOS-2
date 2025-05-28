"""
Display Detailed Telemetry for StratOS Agents
Shows all captured events including invocations, tool use, announcements, Q&A, etc.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import argparse
from collections import defaultdict

# ANSI color codes for better readability
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

def find_recent_telemetry_files(telemetry_dir: Path, minutes: int = 30) -> List[Path]:
    """Find telemetry files created in the last N minutes"""
    telemetry_files = []
    
    # Check all agent subdirectories
    for agent_dir in telemetry_dir.iterdir():
        if agent_dir.is_dir() and not agent_dir.name.startswith('__'):
            for file_path in agent_dir.glob('*_telemetry_*.json'):
                # Check if file is recent
                file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                time_diff = datetime.now() - file_time
                if time_diff.total_seconds() < (minutes * 60):
                    telemetry_files.append(file_path)
    
    return sorted(telemetry_files, key=lambda x: x.stat().st_mtime, reverse=True)

def format_timestamp(timestamp: str) -> str:
    """Format timestamp for display"""
    try:
        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        return dt.strftime("%H:%M:%S.%f")[:-3]  # HH:MM:SS.mmm
    except:
        return timestamp

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text with ellipsis if too long"""
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text

def display_event_details(event: Dict[str, Any], index: int):
    """Display detailed information for a single event"""
    event_type = event.get('event_type', 'unknown')
    timestamp = format_timestamp(event.get('timestamp', ''))
    data = event.get('data', {})
    
    # Event header with color coding
    color = Colors.GREEN
    icon = "📌"
    
    event_icons = {
        'telemetry_configured': ('⚙️', Colors.BLUE),
        'deployment_loaded': ('🚀', Colors.CYAN),
        'orchestrator_fetch_start': ('🔍', Colors.YELLOW),
        'orchestrator_fetch_complete': ('✅', Colors.GREEN),
        'query_sent': ('📤', Colors.BLUE),
        'response_received': ('📥', Colors.GREEN),
        'delegation_confirmed': ('🔀', Colors.CYAN),
        'error': ('❌', Colors.RED),
        'test_complete': ('🏁', Colors.GREEN),
        'tool_invocation': ('🔧', Colors.YELLOW),
        'agent_announcement': ('📢', Colors.CYAN)
    }
    
    if event_type in event_icons:
        icon, color = event_icons[event_type]
    
    print(f"\n{color}{icon} Event #{index}: {event_type}{Colors.END}")
    print(f"   ⏰ Time: {timestamp}")
    
    # Display event-specific details
    if event_type == 'telemetry_configured':
        print(f"   📊 App Insights: {'Enabled' if data.get('app_insights') else 'Disabled'}")
    
    elif event_type == 'deployment_loaded':
        print(f"   🆔 Orchestrator ID: {data.get('orchestrator_id', 'N/A')}")
        agents = data.get('agents', [])
        if agents:
            print(f"   👥 Connected Agents: {', '.join(agents)}")
    
    elif event_type == 'orchestrator_fetch_start':
        print(f"   🔍 Fetching Orchestrator: {data.get('orchestrator_id', 'N/A')}")
    
    elif event_type == 'orchestrator_fetch_complete':
        print(f"   ✅ Orchestrator ID: {data.get('orchestrator_id', 'N/A')}")
        print(f"   🔧 Tools Count: {data.get('tools_count', 0)}")
        tools = data.get('tools', [])
        if tools:
            print("   📦 Available Tools:")
            for tool in tools:
                print(f"      - {tool.get('name', 'unknown')} (ID: {tool.get('id', 'N/A')[:12]}...)")
    
    elif event_type == 'query_sent':
        query = data.get('query', '')
        scenario = data.get('scenario', 'unknown')
        print(f"   🎯 Scenario: {Colors.YELLOW}{scenario}{Colors.END}")
        print(f"   ❓ Query: {Colors.CYAN}\"{truncate_text(query, 150)}\"{Colors.END}")
    
    elif event_type == 'response_received':
        response_len = data.get('response_length', 0)
        delegation = data.get('delegation_detected', False)
        response_preview = data.get('response_preview', '')
        scenario = data.get('scenario', 'N/A')
        
        print(f"   📏 Response Length: {response_len} chars")
        print(f"   🎯 Scenario: {scenario}")
        print(f"   🔀 Delegation Detected: {Colors.GREEN if delegation else Colors.RED}{'Yes' if delegation else 'No'}{Colors.END}")
        print(f"   💬 Response Preview:")
        print(f"      {Colors.CYAN}\"{truncate_text(response_preview, 200)}\"{Colors.END}")
    
    elif event_type == 'delegation_confirmed':
        agent_type = data.get('type', 'unknown')
        scenario = data.get('scenario', 'unknown')
        print(f"   ➡️  Delegated to: {Colors.GREEN}{agent_type}{Colors.END}")
        print(f"   🎯 For scenario: {Colors.YELLOW}{scenario}{Colors.END}")
    
    elif event_type == 'error':
        message = data.get('message', 'Unknown error')
        print(f"   {Colors.RED}⚠️  Error: {message}{Colors.END}")
        if 'context' in data:
            print(f"   📋 Context: {data['context']}")
    
    elif event_type == 'test_complete':
        tests_run = data.get('tests_run', 0)
        delegations = data.get('delegations', 0)
        print(f"   📊 Tests Run: {tests_run}")
        print(f"   ✅ Successful Delegations: {delegations}")
        print(f"   📈 Success Rate: {Colors.GREEN if delegations == tests_run else Colors.YELLOW}{delegations}/{tests_run} ({delegations/tests_run*100:.1f}%){Colors.END}")
    
    elif event_type == 'tool_invocation':
        tool_name = data.get('tool_name', 'unknown')
        parameters = data.get('parameters', {})
        print(f"   🔧 Tool: {Colors.YELLOW}{tool_name}{Colors.END}")
        if parameters:
            print("   📝 Parameters:")
            for key, value in parameters.items():
                print(f"      - {key}: {truncate_text(str(value), 100)}")
    
    elif event_type == 'agent_announcement':
        agent = data.get('agent', 'unknown')
        message = data.get('message', '')
        print(f"   👤 Agent: {Colors.CYAN}{agent}{Colors.END}")
        print(f"   📢 Announcement: \"{truncate_text(message, 200)}\"")
    
    else:
        # Generic data display for unknown event types
        if data:
            print("   📋 Data:")
            for key, value in data.items():
                if isinstance(value, (list, dict)):
                    print(f"      - {key}: {json.dumps(value, indent=8)[:200]}...")
                else:
                    print(f"      - {key}: {truncate_text(str(value), 100)}")

def display_conversation_flow(events: List[Dict[str, Any]]):
    """Display the conversation flow in a more readable format"""
    print(f"\n{Colors.HEADER}{'='*80}{Colors.END}")
    print(f"{Colors.HEADER}CONVERSATION FLOW{Colors.END}")
    print(f"{Colors.HEADER}{'='*80}{Colors.END}")
    
    conversation_events = [e for e in events if e.get('event_type') in ['query_sent', 'response_received', 'delegation_confirmed']]
    
    current_scenario = None
    for event in conversation_events:
        event_type = event.get('event_type')
        data = event.get('data', {})
        timestamp = format_timestamp(event.get('timestamp', ''))
        
        if event_type == 'query_sent':
            scenario = data.get('scenario', 'unknown')
            if scenario != current_scenario:
                print(f"\n{Colors.BOLD}--- Scenario: {scenario} ---{Colors.END}")
                current_scenario = scenario
            
            query = data.get('query', '')
            print(f"\n⏰ [{timestamp}] {Colors.BLUE}USER QUERY:{Colors.END}")
            print(f"   \"{query}\"")
        
        elif event_type == 'delegation_confirmed':
            agent = data.get('type', 'unknown')
            print(f"\n⏰ [{timestamp}] {Colors.CYAN}DELEGATION:{Colors.END}")
            print(f"   → Routing to {agent} specialist")
        
        elif event_type == 'response_received':
            response = data.get('response_preview', '')
            delegation = data.get('delegation_detected', False)
            print(f"\n⏰ [{timestamp}] {Colors.GREEN}ORCHESTRATOR RESPONSE:{Colors.END}")
            print(f"   \"{response}\"")
            if not delegation:
                print(f"   {Colors.RED}⚠️  No delegation detected in response{Colors.END}")

def analyze_telemetry_file(file_path: Path, show_details: bool = True):
    """Analyze and display a single telemetry file"""
    print(f"\n{Colors.HEADER}{'='*80}{Colors.END}")
    print(f"{Colors.HEADER}📁 TELEMETRY FILE: {file_path.name}{Colors.END}")
    print(f"{Colors.HEADER}{'='*80}{Colors.END}")
    
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    # Basic info
    print(f"\n📋 {Colors.BOLD}Session Information:{Colors.END}")
    print(f"   Agent: {Colors.CYAN}{data.get('agent_name', 'Unknown')}{Colors.END}")
    print(f"   Session ID: {data.get('session_id', 'N/A')}")
    print(f"   Capture Time: {data.get('capture_time', 'N/A')}")
    print(f"   Total Events: {len(data.get('events', []))}")
    
    events = data.get('events', [])
    
    # Event type summary
    event_counts = defaultdict(int)
    for event in events:
        event_counts[event.get('event_type', 'unknown')] += 1
    
    print(f"\n📊 {Colors.BOLD}Event Summary:{Colors.END}")
    for event_type, count in sorted(event_counts.items()):
        print(f"   - {event_type}: {count}")
    
    if show_details:
        # Detailed event display
        print(f"\n📝 {Colors.BOLD}Detailed Event Log:{Colors.END}")
        for i, event in enumerate(events, 1):
            display_event_details(event, i)
        
        # Conversation flow
        display_conversation_flow(events)
    
    # Analysis summary
    print(f"\n📈 {Colors.BOLD}Analysis Summary:{Colors.END}")
    
    # Count delegations
    delegations = [e for e in events if e.get('event_type') == 'delegation_confirmed']
    errors = [e for e in events if e.get('event_type') == 'error']
    queries = [e for e in events if e.get('event_type') == 'query_sent']
    
    print(f"   Total Queries: {len(queries)}")
    print(f"   Successful Delegations: {Colors.GREEN}{len(delegations)}{Colors.END}")
    print(f"   Errors: {Colors.RED if errors else Colors.GREEN}{len(errors)}{Colors.END}")
    
    if delegations:
        print(f"\n   {Colors.BOLD}Delegation Breakdown:{Colors.END}")
        delegation_counts = defaultdict(int)
        for d in delegations:
            agent = d.get('data', {}).get('type', 'unknown')
            delegation_counts[agent] += 1
        
        for agent, count in delegation_counts.items():
            print(f"      - {agent}: {count}")

def main():
    parser = argparse.ArgumentParser(description="Display detailed telemetry for StratOS agents")
    parser.add_argument(
        "--minutes",
        type=int,
        default=60,
        help="Look for telemetry files from the last N minutes (default: 60)"
    )
    parser.add_argument(
        "--dir",
        type=str,
        default=None,
        help="Telemetry directory path (default: current directory)"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show summary only without detailed events"
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Analyze a specific telemetry file"
    )
    
    args = parser.parse_args()
    
    # If specific file is provided
    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            return
        analyze_telemetry_file(file_path, show_details=not args.summary)
        return
    
    # Determine telemetry directory
    if args.dir:
        telemetry_dir = Path(args.dir)
    else:
        telemetry_dir = Path(__file__).parent
    
    if not telemetry_dir.exists():
        print(f"Error: Telemetry directory not found: {telemetry_dir}")
        return
    
    # Find recent telemetry files
    telemetry_files = find_recent_telemetry_files(telemetry_dir, args.minutes)
    
    if not telemetry_files:
        print(f"No telemetry files found in the last {args.minutes} minutes")
        print(f"Searched in: {telemetry_dir}")
        return
    
    print(f"\n{Colors.BOLD}Found {len(telemetry_files)} telemetry file(s) from the last {args.minutes} minutes{Colors.END}")
    
    # Analyze each file
    for file_path in telemetry_files:
        try:
            analyze_telemetry_file(file_path, show_details=not args.summary)
        except Exception as e:
            print(f"\n{Colors.RED}Error analyzing {file_path}: {e}{Colors.END}")
    
    print(f"\n{Colors.HEADER}{'='*80}{Colors.END}")
    print(f"{Colors.HEADER}END OF TELEMETRY REPORT{Colors.END}")
    print(f"{Colors.HEADER}{'='*80}{Colors.END}")

if __name__ == "__main__":
    main()