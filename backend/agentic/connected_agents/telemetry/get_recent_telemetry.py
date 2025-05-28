#!/usr/bin/env python3
"""
Get recent telemetry data from Application Insights with correct table names
"""
import os
import sys
import json
from datetime import datetime, timedelta, timezone
from azure.monitor.query import LogsQueryClient
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import HttpResponseError

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_recent_telemetry():
    """Get telemetry from the last 30 minutes"""
    
    # Initialize client
    credential = DefaultAzureCredential()
    client = LogsQueryClient(credential)
    
    # Workspace ID from environment
    workspace_id = "b318971e-7337-4649-947f-891c69c60ecb"
    
    # Time range - last 30 minutes
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(minutes=30)
    
    print(f"Querying telemetry from {start_time} to {end_time}")
    
    # Query for AppTraces (the correct table name)
    query = """
    AppTraces
    | where TimeGenerated > ago(30m)
    | where AppRoleName contains "agent" or Message contains "agent" or Message contains "delegation"
    | project TimeGenerated, AppRoleName, OperationId, ParentId, Message, SeverityLevel, Properties
    | order by TimeGenerated desc
    | limit 100
    """
    
    try:
        print("\nQuerying AppTraces...")
        response = client.query_workspace(
            workspace_id=workspace_id,
            query=query,
            timespan=(start_time, end_time)
        )
        
        traces = []
        if response.status.value == "Success" and response.tables:
            for table in response.tables:
                for row in table.rows:
                    trace = {}
                    for i, column in enumerate(table.columns):
                        trace[column.name] = row[i]
                    traces.append(trace)
            
            print(f"Found {len(traces)} traces")
            
            # Display traces
            for i, trace in enumerate(traces[:20]):  # Show first 20
                print(f"\n--- Trace {i+1} ---")
                print(f"Time: {trace.get('TimeGenerated', 'N/A')}")
                print(f"Service: {trace.get('AppRoleName', 'N/A')}")
                print(f"Message: {trace.get('Message', 'N/A')[:200]}...")
                if trace.get('Properties'):
                    print(f"Properties: {trace.get('Properties')[:200]}...")
                print(f"OperationId: {trace.get('OperationId', 'N/A')}")
                
        else:
            print("No traces found")
            
    except HttpResponseError as e:
        print(f"HTTP Error: {e.message}")
        print(f"Error details: {e.error}")
    except Exception as e:
        print(f"Error: {type(e).__name__}: {str(e)}")
    
    # Also query AppDependencies for agent invocations
    dep_query = """
    AppDependencies
    | where TimeGenerated > ago(30m)
    | where Name contains "agent" or Target contains "agent" or Data contains "agent"
    | project TimeGenerated, Name, Target, Data, Duration, Success, ResultCode
    | order by TimeGenerated desc
    | limit 50
    """
    
    try:
        print("\n\nQuerying AppDependencies...")
        dep_response = client.query_workspace(
            workspace_id=workspace_id,
            query=dep_query,
            timespan=(start_time, end_time)
        )
        
        dependencies = []
        if dep_response.status.value == "Success" and dep_response.tables:
            for table in dep_response.tables:
                for row in table.rows:
                    dep = {}
                    for i, column in enumerate(table.columns):
                        dep[column.name] = row[i]
                    dependencies.append(dep)
            
            print(f"Found {len(dependencies)} dependencies")
            
            # Display dependencies
            for i, dep in enumerate(dependencies[:10]):
                print(f"\n--- Dependency {i+1} ---")
                print(f"Time: {dep.get('TimeGenerated', 'N/A')}")
                print(f"Name: {dep.get('Name', 'N/A')}")
                print(f"Target: {dep.get('Target', 'N/A')}")
                print(f"Duration: {dep.get('Duration', 'N/A')}ms")
                print(f"Success: {dep.get('Success', 'N/A')}")
                
        else:
            print("No dependencies found")
            
    except Exception as e:
        print(f"Error querying dependencies: {str(e)}")
    
    # Save results
    results = {
        "query_time": datetime.now().isoformat(),
        "traces": traces,
        "dependencies": dependencies
    }
    
    filename = f"telemetry_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ Results saved to {filename}")

if __name__ == "__main__":
    get_recent_telemetry()