#!/usr/bin/env python3
"""
Get recent telemetry data from Application Insights
"""
import os
import sys
import json
from datetime import datetime, timedelta, timezone
from azure.monitor.query import LogsQueryClient, LogsQueryStatus
from azure.identity import DefaultAzureCredential

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_recent_telemetry():
    """Get telemetry from the last hour"""
    
    # Initialize client
    credential = DefaultAzureCredential()
    client = LogsQueryClient(credential)
    
    # Workspace ID
    workspace_id = "b318971e-7337-4649-947f-891c69c60ecb"
    
    # Time range - last hour
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=1)
    
    print(f"Querying telemetry from {start_time} to {end_time}")
    
    # First, let's see what columns are available in AppTraces
    schema_query = """
    AppTraces
    | take 1
    | getschema
    """
    
    try:
        print("\nChecking AppTraces schema...")
        schema_response = client.query_workspace(
            workspace_id=workspace_id,
            query=schema_query,
            timespan=(start_time, end_time)
        )
        
        if schema_response.status == LogsQueryStatus.SUCCESS:
            print("Available columns in AppTraces:")
            for table in schema_response.tables:
                for row in table.rows:
                    print(f"  - {row[0]}: {row[1]}")
    except Exception as e:
        print(f"Could not get schema: {e}")
    
    # Query for all recent traces
    traces_query = """
    AppTraces
    | where TimeGenerated > ago(1h)
    | order by TimeGenerated desc
    | limit 50
    """
    
    traces = []
    dependencies = []
    
    try:
        print("\n\nQuerying AppTraces...")
        response = client.query_workspace(
            workspace_id=workspace_id,
            query=traces_query,
            timespan=(start_time, end_time)
        )
        
        if response.status == LogsQueryStatus.SUCCESS:
            for table in response.tables:
                print(f"Found {len(table.rows)} traces")
                
                # Get column names
                columns = [col.name for col in table.columns]
                print(f"Columns: {columns[:10]}...")  # Show first 10 columns
                
                for row in table.rows:
                    trace = {}
                    for i, column in enumerate(table.columns):
                        value = row[i]
                        if isinstance(value, datetime):
                            value = value.isoformat()
                        trace[column.name] = value
                    traces.append(trace)
            
            # Display traces related to agents
            print("\n=== Agent-Related Traces ===")
            agent_traces = []
            for trace in traces:
                message = str(trace.get('Message', '')).lower()
                properties = str(trace.get('Properties', '')).lower()
                
                if any(keyword in message or keyword in properties for keyword in ['agent', 'delegation', 'orchestrat', 'invoke']):
                    agent_traces.append(trace)
            
            print(f"Found {len(agent_traces)} agent-related traces")
            
            for i, trace in enumerate(agent_traces[:10]):
                print(f"\n--- Trace {i+1} ---")
                print(f"Time: {trace.get('TimeGenerated', 'N/A')}")
                print(f"Message: {trace.get('Message', 'N/A')[:200]}...")
                if trace.get('Properties'):
                    print(f"Properties: {str(trace.get('Properties'))[:200]}...")
                print(f"OperationId: {trace.get('OperationId', 'N/A')}")
                print(f"SeverityLevel: {trace.get('SeverityLevel', 'N/A')}")
                
        else:
            print(f"Query status: {response.status}")
            
    except Exception as e:
        print(f"Error querying traces: {type(e).__name__}: {str(e)}")
    
    # Try AppDependencies with correct columns
    dep_query = """
    AppDependencies
    | where TimeGenerated > ago(1h)
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
        
        if dep_response.status == LogsQueryStatus.SUCCESS:
            for table in dep_response.tables:
                print(f"Found {len(table.rows)} dependencies")
                
                # Get column names
                columns = [col.name for col in table.columns]
                print(f"Columns: {columns[:10]}...")
                
                for row in table.rows:
                    dep = {}
                    for i, column in enumerate(table.columns):
                        value = row[i]
                        if isinstance(value, datetime):
                            value = value.isoformat()
                        dep[column.name] = value
                    dependencies.append(dep)
            
            # Display agent-related dependencies
            print("\n=== Agent Dependencies ===")
            for i, dep in enumerate(dependencies[:10]):
                if 'agent' in str(dep).lower():
                    print(f"\n--- Dependency {i+1} ---")
                    for key, value in dep.items():
                        if value and key in ['TimeGenerated', 'Name', 'Target', 'Data', 'DurationMs', 'Success']:
                            print(f"{key}: {str(value)[:100]}")
                
        else:
            print(f"Query status: {dep_response.status}")
            
    except Exception as e:
        print(f"Error querying dependencies: {str(e)}")
    
    # Save all results
    results = {
        "query_time": datetime.now().isoformat(),
        "trace_count": len(traces),
        "dependency_count": len(dependencies),
        "traces": traces[:20],  # Save first 20
        "dependencies": dependencies[:20]  # Save first 20
    }
    
    filename = f"telemetry_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n✅ Results saved to {filename}")
    print(f"📊 Summary: {len(traces)} traces, {len(dependencies)} dependencies")

if __name__ == "__main__":
    get_recent_telemetry()