"""
Display Telemetry Summary for StratOS Agents
Shows delegation patterns and test results from captured telemetry
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import argparse

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

def analyze_telemetry_file(file_path: Path) -> Dict:
    """Analyze a single telemetry file"""
    with open(file_path, 'r') as f:
        data = json.load(f)
    
    analysis = {
        'file_name': file_path.name,
        'agent_name': data.get('agent_name', 'Unknown'),
        'session_id': data.get('session_id', ''),
        'capture_time': data.get('capture_time', ''),
        'total_events': len(data.get('events', [])),
        'delegations': [],
        'errors': [],
        'test_results': None
    }
    
    # Analyze events
    for event in data.get('events', []):
        event_type = event.get('event_type', '')
        event_data = event.get('data', {})
        
        if event_type == 'delegation_confirmed':
            analysis['delegations'].append({
                'to_agent': event_data.get('type', 'unknown'),
                'scenario': event_data.get('scenario', 'unknown'),
                'timestamp': event.get('timestamp', '')
            })
        elif event_type == 'error':
            analysis['errors'].append({
                'message': event_data.get('message', ''),
                'timestamp': event.get('timestamp', '')
            })
        elif event_type == 'test_complete':
            analysis['test_results'] = {
                'tests_run': event_data.get('tests_run', 0),
                'delegations': event_data.get('delegations', 0)
            }
    
    return analysis

def display_summary(analyses: List[Dict]):
    """Display summary of all telemetry analyses"""
    print("\n" + "=" * 80)
    print("STRATOS AGENTS TELEMETRY SUMMARY")
    print("=" * 80)
    print(f"\nFound {len(analyses)} telemetry files\n")
    
    total_delegations = 0
    total_errors = 0
    
    for analysis in analyses:
        print(f"📁 {analysis['file_name']}")
        print(f"   Agent: {analysis['agent_name']}")
        print(f"   Session: {analysis['session_id'][:8]}...")
        print(f"   Events: {analysis['total_events']}")
        
        if analysis['delegations']:
            print(f"   ✅ Delegations: {len(analysis['delegations'])}")
            for delegation in analysis['delegations']:
                print(f"      → {delegation['to_agent']} ({delegation['scenario']})")
            total_delegations += len(analysis['delegations'])
        
        if analysis['errors']:
            print(f"   ❌ Errors: {len(analysis['errors'])}")
            for error in analysis['errors']:
                print(f"      → {error['message'][:50]}...")
            total_errors += len(analysis['errors'])
        
        if analysis['test_results']:
            results = analysis['test_results']
            print(f"   📊 Test Results: {results['delegations']}/{results['tests_run']} passed")
        
        print()
    
    # Overall summary
    print("=" * 80)
    print("OVERALL SUMMARY")
    print("=" * 80)
    print(f"Total Delegations: {total_delegations}")
    print(f"Total Errors: {total_errors}")
    
    # Agent performance
    agent_stats = {}
    for analysis in analyses:
        agent = analysis['agent_name']
        if agent not in agent_stats:
            agent_stats[agent] = {'delegations': 0, 'errors': 0, 'tests': 0}
        agent_stats[agent]['delegations'] += len(analysis['delegations'])
        agent_stats[agent]['errors'] += len(analysis['errors'])
        if analysis['test_results']:
            agent_stats[agent]['tests'] += analysis['test_results']['tests_run']
    
    print("\nAgent Performance:")
    for agent, stats in agent_stats.items():
        status = "✅" if stats['errors'] == 0 and stats['delegations'] > 0 else "❌"
        print(f"  {status} {agent}: {stats['delegations']} delegations, {stats['errors']} errors")
    
    print("=" * 80)

def main():
    parser = argparse.ArgumentParser(description="Display telemetry summary for StratOS agents")
    parser.add_argument(
        "--minutes",
        type=int,
        default=30,
        help="Look for telemetry files from the last N minutes (default: 30)"
    )
    parser.add_argument(
        "--dir",
        type=str,
        default=None,
        help="Telemetry directory path (default: current directory)"
    )
    
    args = parser.parse_args()
    
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
    
    # Analyze each file
    analyses = []
    for file_path in telemetry_files:
        try:
            analysis = analyze_telemetry_file(file_path)
            analyses.append(analysis)
        except Exception as e:
            print(f"Error analyzing {file_path}: {e}")
    
    # Display summary
    display_summary(analyses)

if __name__ == "__main__":
    main()