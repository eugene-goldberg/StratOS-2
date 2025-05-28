#!/usr/bin/env python3
"""
Simple telemetry query that works with the actual Application Insights structure
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
    """Get telemetry from the last 2 hours"""
    
    # Initialize client
    credential = DefaultAzureCredential()
    client = LogsQueryClient(credential)
    
    # Workspace ID
    workspace_id = "b318971e-7337-4649-947f-891c69c60ecb"
    
    # Time range - last 2 hours
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=2)
    
    print(f"Querying telemetry from {start_time} to {end_time}")
    
    # Query for traces containing agent-related keywords
    query = """
    AppTraces
    | where TimeGenerated > ago(2h)
    | where Message contains "agent" 
        or Message contains "Agent"
        or Message contains "delegation" 
        or Message contains "orchestrat"
        or Message contains "invoke"
        or Message contains "specialist"
        or Properties contains "agent"
        or AppRoleName contains "agent"
    | project TimeGenerated, Message, SeverityLevel, Properties, OperationId, AppRoleName
    | order by TimeGenerated desc
    | limit 100
    """
    
    results = []
    
    try:
        print("\nQuerying AppTraces for agent activity...")
        response = client.query_workspace(
            workspace_id=workspace_id,
            query=query,
            timespan=(start_time, end_time)
        )
        
        if response.status == LogsQueryStatus.SUCCESS:
            for table in response.tables:
                print(f"\nFound {len(table.rows)} agent-related traces")
                
                # Process each row
                for row_idx, row in enumerate(table.rows):
                    trace = {
                        "TimeGenerated": str(row[0]),
                        "Message": str(row[1]),
                        "SeverityLevel": str(row[2]),
                        "Properties": str(row[3]),
                        "OperationId": str(row[4]),
                        "AppRoleName": str(row[5])
                    }
                    results.append(trace)
                    
                    # Display first 10 traces
                    if row_idx < 10:
                        print(f"\n--- Trace {row_idx + 1} ---")
                        print(f"Time: {trace['TimeGenerated']}")
                        print(f"Service: {trace['AppRoleName']}")
                        print(f"Message: {trace['Message'][:200]}...")
                        if trace['Properties'] and trace['Properties'] != 'None':
                            print(f"Properties: {trace['Properties'][:200]}...")
                        print(f"OperationId: {trace['OperationId']}")
        else:
            print(f"Query failed with status: {response.status}")
            
    except Exception as e:
        print(f"Error: {type(e).__name__}: {str(e)}")
    
    # Also try a simpler query to see any recent activity
    simple_query = """
    AppTraces
    | where TimeGenerated > ago(30m)
    | project TimeGenerated, Message, AppRoleName
    | order by TimeGenerated desc
    | limit 20
    """
    
    try:
        print("\n\nChecking recent traces (last 30 minutes)...")
        simple_response = client.query_workspace(
            workspace_id=workspace_id,
            query=simple_query,
            timespan=(start_time, end_time)
        )
        
        if simple_response.status == LogsQueryStatus.SUCCESS:
            recent_count = 0
            for table in simple_response.tables:
                recent_count = len(table.rows)
                print(f"Found {recent_count} traces in the last 30 minutes")
                
                if recent_count > 0:
                    print("\nMost recent traces:")
                    for i, row in enumerate(table.rows[:5]):
                        print(f"{i+1}. [{row[0]}] {row[2]}: {str(row[1])[:100]}...")
        
    except Exception as e:
        print(f"Simple query error: {e}")
    
    # Save results
    if results:
        filename = f"agent_telemetry_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump({
                "query_time": datetime.now().isoformat(),
                "trace_count": len(results),
                "traces": results
            }, f, indent=2)
        print(f"\n✅ Saved {len(results)} agent traces to {filename}")
    else:
        print("\n❌ No agent-related traces found in the last 2 hours")
    
    # Check for telemetry transmission confirmations
    telemetry_query = """
    AppTraces
    | where TimeGenerated > ago(2h)
    | where Message contains "Telemetry transmission"
        or Message contains "telemetry items"
        or Message contains "OpenTelemetry"
    | project TimeGenerated, Message, Properties
    | order by TimeGenerated desc
    | limit 20
    """
    
    try:
        print("\n\nChecking for telemetry transmission logs...")
        tel_response = client.query_workspace(
            workspace_id=workspace_id,
            query=telemetry_query,
            timespan=(start_time, end_time)
        )
        
        if tel_response.status == LogsQueryStatus.SUCCESS:
            for table in tel_response.tables:
                if len(table.rows) > 0:
                    print(f"Found {len(table.rows)} telemetry transmission logs:")
                    for row in table.rows[:5]:
                        print(f"  [{row[0]}] {row[1]}")
                else:
                    print("No telemetry transmission logs found")
    except Exception as e:
        print(f"Telemetry query error: {e}")

if __name__ == "__main__":
    get_recent_telemetry()