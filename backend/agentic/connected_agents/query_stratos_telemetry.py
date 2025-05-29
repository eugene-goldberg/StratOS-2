#!/usr/bin/env python3
"""
Query and display detailed telemetry data from Application Insights
for the StratOS agents test run.
"""

import os
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from azure.monitor.query import LogsQueryClient, LogsQueryStatus
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import HttpResponseError

# Load environment variables
load_dotenv()

# Configure logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_workspace_id_from_connection_string(connection_string):
    """Extract workspace ID from Application Insights connection string."""
    # Connection string format: InstrumentationKey=xxx;IngestionEndpoint=xxx;...
    # We need to get the resource from Azure
    # For now, use the known workspace ID
    return os.getenv("LOG_ANALYTICS_WORKSPACE_ID", "2c8c86e5-9c23-4f01-b54a-7e0d9c1e7c5b")


def query_telemetry():
    """Query Application Insights for recent telemetry data."""
    
    # Get connection details
    connection_string = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
    if not connection_string:
        logger.error("APPLICATIONINSIGHTS_CONNECTION_STRING not found")
        return
    
    workspace_id = get_workspace_id_from_connection_string(connection_string)
    logger.info(f"Using Log Analytics Workspace ID: {workspace_id}")
    
    # Create client
    credential = DefaultAzureCredential()
    client = LogsQueryClient(credential)
    
    # Query for recent traces (last hour)
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)
    
    # Queries to run
    queries = [
        {
            "name": "All Traces",
            "query": """
            traces
            | where timestamp > ago(1h)
            | where message contains "stratos" or message contains "agent" or message contains "orchestrator"
            | project timestamp, message, severityLevel, customDimensions
            | order by timestamp desc
            | limit 50
            """
        },
        {
            "name": "Request Summary",
            "query": """
            requests
            | where timestamp > ago(1h)
            | where name contains "agent" or url contains "agent" or url contains "assistant"
            | project timestamp, name, url, duration, resultCode, success
            | order by timestamp desc
            | limit 50
            """
        },
        {
            "name": "Dependencies",
            "query": """
            dependencies
            | where timestamp > ago(1h)
            | where name contains "agent" or target contains "ai.azure.com"
            | project timestamp, name, target, duration, resultCode, success
            | order by timestamp desc
            | limit 50
            """
        },
        {
            "name": "Custom Events",
            "query": """
            customEvents
            | where timestamp > ago(1h)
            | where name contains "agent" or name contains "delegation"
            | project timestamp, name, customDimensions
            | order by timestamp desc
            | limit 50
            """
        },
        {
            "name": "Exceptions",
            "query": """
            exceptions
            | where timestamp > ago(1h)
            | project timestamp, message, type, method, assembly
            | order by timestamp desc
            | limit 20
            """
        }
    ]
    
    # Execute queries
    for query_info in queries:
        logger.info(f"\n{'='*80}")
        logger.info(f"Query: {query_info['name']}")
        logger.info(f"{'='*80}")
        
        try:
            response = client.query_workspace(
                workspace_id=workspace_id,
                query=query_info['query'],
                timespan=(start_time, end_time)
            )
            
            if response.status == LogsQueryStatus.PARTIAL:
                logger.warning(f"Query returned partial results: {response.partial_error}")
            elif response.status == LogsQueryStatus.FAILED:
                logger.error(f"Query failed: {response.error}")
                continue
            
            # Display results
            if response.tables:
                for table in response.tables:
                    logger.info(f"\nColumns: {[col.name for col in table.columns]}")
                    logger.info(f"Rows found: {len(table.rows)}")
                    
                    if table.rows:
                        logger.info("\nSample data (first 10 rows):")
                        for i, row in enumerate(table.rows[:10]):
                            logger.info(f"\nRow {i+1}:")
                            for j, col in enumerate(table.columns):
                                value = row[j]
                                # Format JSON data nicely
                                if isinstance(value, str) and value.startswith('{'):
                                    try:
                                        value = json.dumps(json.loads(value), indent=2)
                                    except:
                                        pass
                                logger.info(f"  {col.name}: {value}")
            else:
                logger.info("No results found")
                
        except HttpResponseError as e:
            logger.error(f"Query failed with HTTP error: {e}")
        except Exception as e:
            logger.error(f"Query failed: {e}")
    
    # Also query for specific agent operations
    logger.info(f"\n{'='*80}")
    logger.info("Agent-Specific Operations")
    logger.info(f"{'='*80}")
    
    agent_query = """
    union traces, requests, dependencies, customEvents
    | where timestamp > ago(1h)
    | where 
        message contains "CEO Log" or
        message contains "North Star" or
        message contains "Memory Recall" or
        message contains "Preference Learning" or
        message contains "StratOS" or
        url contains "/assistants/" or
        name contains "agent"
    | project timestamp, itemType, message = coalesce(message, name, url), details = coalesce(customDimensions, "")
    | order by timestamp desc
    | limit 100
    """
    
    try:
        response = client.query_workspace(
            workspace_id=workspace_id,
            query=agent_query,
            timespan=(start_time, end_time)
        )
        
        if response.status == LogsQueryStatus.SUCCESS and response.tables:
            table = response.tables[0]
            logger.info(f"\nAgent operations found: {len(table.rows)}")
            
            # Group by operation type
            by_type = {}
            for row in table.rows:
                item_type = row[1]
                if item_type not in by_type:
                    by_type[item_type] = []
                by_type[item_type].append(row)
            
            for item_type, rows in by_type.items():
                logger.info(f"\n{item_type} ({len(rows)} items):")
                for row in rows[:5]:  # First 5 of each type
                    timestamp = row[0]
                    message = row[2]
                    details = row[3]
                    logger.info(f"  {timestamp}: {message[:100]}...")
                    if details and isinstance(details, str) and details.startswith('{'):
                        try:
                            details_json = json.loads(details)
                            if 'agent' in str(details_json).lower():
                                logger.info(f"    Details: {json.dumps(details_json, indent=4)}")
                        except:
                            pass
    
    except Exception as e:
        logger.error(f"Agent query failed: {e}")


if __name__ == "__main__":
    # Check if we have the necessary environment variables
    if not os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING"):
        logger.error("APPLICATIONINSIGHTS_CONNECTION_STRING not set")
        logger.info("Please set this in your .env file")
    else:
        query_telemetry()