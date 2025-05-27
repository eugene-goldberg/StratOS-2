#!/usr/bin/env python3
"""
Query telemetry for the comprehensive test run.
"""

import os
from datetime import datetime, timedelta
from azure.identity import DefaultAzureCredential
from azure.monitor.query import LogsQueryClient, LogsQueryStatus
import json

# Configuration
WORKSPACE_ID = "b318971e-7337-4649-947f-891c69c60ecb"
TEST_ID = "test_20250526_130737_43a7c242"

def main():
    credential = DefaultAzureCredential()
    client = LogsQueryClient(credential)
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=20)
    
    # Query for all traces from our test
    query = f"""
    AppTraces
    | where TimeGenerated >= datetime({start_time.isoformat()})
    | where TimeGenerated <= datetime({end_time.isoformat()})
    | where Properties contains '{TEST_ID}'
    | order by TimeGenerated asc
    """
    
    print(f"Querying telemetry for test ID: {TEST_ID}")
    print(f"Time range: {start_time.isoformat()} to {end_time.isoformat()}")
    
    response = client.query_workspace(
        workspace_id=WORKSPACE_ID,
        query=query,
        timespan=(start_time, end_time)
    )
    
    if response.status == LogsQueryStatus.SUCCESS and response.tables:
        # Get column names
        if hasattr(response.tables[0].columns[0], 'name'):
            column_names = [col.name for col in response.tables[0].columns]
        else:
            column_names = response.tables[0].columns
        
        traces = []
        for row in response.tables[0].rows:
            trace = dict(zip(column_names, row))
            # Convert datetime objects
            for key, value in trace.items():
                if isinstance(value, datetime):
                    trace[key] = value.isoformat()
            traces.append(trace)
        
        print(f"\nFound {len(traces)} telemetry traces")
        
        # Group by agent
        agent_traces = {}
        for trace in traces:
            props = json.loads(trace.get('Properties', '{}'))
            agent_name = props.get('agent.name', 'Unknown')
            if agent_name not in agent_traces:
                agent_traces[agent_name] = []
            agent_traces[agent_name].append({
                'timestamp': trace['TimeGenerated'],
                'message': trace['Message'],
                'properties': props
            })
        
        # Show summary
        print("\nAgent telemetry summary:")
        for agent, agent_trace_list in agent_traces.items():
            print(f"\n{agent}: {len(agent_trace_list)} traces")
            for t in agent_trace_list[:3]:  # Show first 3 traces
                print(f"  - {t['message']}")
        
        # Save full results
        output = {
            "test_id": TEST_ID,
            "query_time": datetime.now().isoformat(),
            "trace_count": len(traces),
            "agents": list(agent_traces.keys()),
            "raw_traces": traces
        }
        
        filename = f"test_telemetry_{TEST_ID}.json"
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\nFull telemetry saved to: {filename}")
    else:
        print("No telemetry found for this test ID")

if __name__ == "__main__":
    main()