"""
Query CEO Log Agent Telemetry from Application Insights
Shows delegation flow and agent interactions
"""

import os
import json
from datetime import datetime, timedelta, timezone
from azure.monitor.query import LogsQueryClient, LogsQueryStatus
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import HttpResponseError
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv(Path(__file__).parent / '.env')
load_dotenv(Path(__file__).parent.parent.parent.parent / '.env')

import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def query_ceo_telemetry():
    """Query telemetry for CEO Log Agent delegation"""
    
    # Get Application Insights details
    app_insights_conn = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING") or os.getenv("APPINSIGHTS_CONNECTION_STRING")
    if not app_insights_conn:
        logger.error("No Application Insights connection string found")
        return
    
    # Extract workspace ID from connection string
    parts = dict(part.split('=', 1) for part in app_insights_conn.split(';') if '=' in part)
    
    # Use the correct workspace ID from working telemetry scripts
    workspace_id = "b318971e-7337-4649-947f-891c69c60ecb"
    
    credential = DefaultAzureCredential()
    client = LogsQueryClient(credential)
    
    # Query for CEO Log related traces
    query = """
    AppTraces
    | where TimeGenerated > ago(15m)
    | where Message contains "CEO" or Message contains "ceo" or Message contains "specialist" or Properties contains "CEO"
    | project TimeGenerated, Message, SeverityLevel, Properties, OperationId
    | order by TimeGenerated desc
    | limit 50
    """
    
    # Alternative query for dependencies (agent calls)
    dependency_query = """
    AppDependencies
    | where TimeGenerated > ago(15m)
    | where Name contains "CEO" or Data contains "CEO" or Target contains "CEO" or Name contains "agent"
    | project TimeGenerated, Name, Target, DurationMs, Success, Data
    | order by TimeGenerated desc
    | limit 20
    """
    
    # Query for all recent agent activity
    all_agent_query = """
    AppTraces
    | where TimeGenerated > ago(15m)
    | where Message contains "agent" or Message contains "orchestrat" or Message contains "delegat" or Message contains "invoke"
    | project TimeGenerated, Message, Properties, SeverityLevel
    | order by TimeGenerated desc
    | limit 100
    """
    
    try:
        # Execute trace query
        logger.info("Querying CEO Log Agent traces...")
        start_time = datetime.now(timezone.utc) - timedelta(minutes=15)
        end_time = datetime.now(timezone.utc)
        
        response = client.query_workspace(
            workspace_id=workspace_id,
            query=query,
            timespan=(start_time, end_time)
        )
        
        if response.status == LogsQueryStatus.SUCCESS:
            traces = []
            for table in response.tables:
                columns = [col.name for col in table.columns]
                logger.info(f"Columns found: {columns}")
                
                for row in table.rows:
                    trace = dict(zip(columns, row))
                    traces.append({
                        'timestamp': str(trace.get('TimeGenerated', '')),
                        'message': trace.get('Message', ''),
                        'severity': trace.get('SeverityLevel', ''),
                        'properties': trace.get('Properties', ''),
                        'operation_id': trace.get('OperationId', '')
                    })
            
            logger.info(f"Found {len(traces)} CEO-related traces")
            
            # Save traces
            if traces:
                with open('ceo_telemetry_traces.json', 'w') as f:
                    json.dump(traces, f, indent=2)
                logger.info("Saved traces to ceo_telemetry_traces.json")
        
        # Execute all agents query
        logger.info("\nQuerying ALL agent activity...")
        all_response = client.query_workspace(
            workspace_id=workspace_id,
            query=all_agent_query,
            timespan=(start_time, end_time)
        )
        
        all_traces = []
        if all_response.status == LogsQueryStatus.SUCCESS:
            for table in all_response.tables:
                for row in table.rows:
                    trace = dict(zip([col.name for col in table.columns], row))
                    all_traces.append(trace)
            
            logger.info(f"Found {len(all_traces)} total agent traces")
            
            # Show recent agent activity
            logger.info("\n=== Recent Agent Activity ===")
            for i, trace in enumerate(all_traces[:10]):
                time = trace.get('TimeGenerated', '')
                msg = trace.get('Message', '')[:150]
                logger.info(f"{i+1}. [{time}] {msg}...")
        
        # Execute dependency query
        logger.info("\nQuerying agent dependencies...")
        dep_response = client.query_workspace(
            workspace_id=workspace_id,
            query=dependency_query,
            timespan=(start_time, end_time)
        )
        
        dependencies = []
        if dep_response.status == LogsQueryStatus.SUCCESS:
            for table in dep_response.tables:
                for row in table.rows:
                    dep = dict(zip([col.name for col in table.columns], row))
                    dependencies.append(dep)
            
            logger.info(f"Found {len(dependencies)} dependency records")
        
        # Summary
        logger.info("\n" + "="*60)
        logger.info("TELEMETRY QUERY SUMMARY")
        logger.info("="*60)
        logger.info(f"✅ CEO-related traces: {len(traces)}")
        logger.info(f"✅ Dependency records: {len(dependencies)}")
        
        # Show delegation evidence
        delegation_found = False
        for trace in traces:
            if 'specialist' in trace['message'].lower() and 'ceo' in trace['message'].lower():
                logger.info(f"\n🎯 DELEGATION EVIDENCE:")
                logger.info(f"   Time: {trace['timestamp']}")
                logger.info(f"   Message: {trace['message'][:100]}...")
                delegation_found = True
                break
        
        if delegation_found:
            logger.info("\n✅ CEO Log Agent delegation confirmed via telemetry!")
        else:
            logger.info("\n⚠️  No explicit delegation traces found (may need to check other queries)")
            
    except HttpResponseError as e:
        logger.error(f"Query failed: {e}")
        logger.info("This is normal if Application Insights data hasn't propagated yet")
    except Exception as e:
        logger.error(f"Error querying telemetry: {e}")
        
    return traces if 'traces' in locals() else []

if __name__ == "__main__":
    query_ceo_telemetry()