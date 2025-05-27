#!/usr/bin/env python3
"""
Save raw telemetry data to a file for inspection.
"""

import os
import sys
from datetime import datetime, timedelta
from azure.identity import DefaultAzureCredential
from azure.monitor.query import LogsQueryClient, LogsQueryStatus
import json

# Application Insights configuration
WORKSPACE_ID = "b318971e-7337-4649-947f-891c69c60ecb"
OPERATION_ID = "99b23ab32f026d74e71e9eab2a44c5ae"

def main():
    credential = DefaultAzureCredential()
    client = LogsQueryClient(credential)
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=15)
    
    query = f"""
    AppTraces
    | where TimeGenerated >= datetime({start_time.isoformat()})
    | where TimeGenerated <= datetime({end_time.isoformat()})
    | where OperationId == '{OPERATION_ID}'
    | order by TimeGenerated asc
    """
    
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
        
        # Convert to list of dictionaries
        traces = []
        for row in response.tables[0].rows:
            trace = dict(zip(column_names, row))
            # Convert datetime objects to strings
            for key, value in trace.items():
                if isinstance(value, datetime):
                    trace[key] = value.isoformat()
            traces.append(trace)
        
        # Save to file
        output = {
            "query": query,
            "operation_id": OPERATION_ID,
            "trace_count": len(traces),
            "traces": traces
        }
        
        filename = f"raw_telemetry_{OPERATION_ID}.json"
        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"Raw telemetry saved to: {filename}")
        print(f"Total traces: {len(traces)}")
        
        # Also print to console
        print("\n" + "="*80)
        print("RAW TELEMETRY DATA:")
        print("="*80)
        print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()