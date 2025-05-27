#!/usr/bin/env python3
"""
Query Application Insights telemetry data to retrieve and display actual telemetry.

This script queries the traces table in Application Insights to retrieve telemetry
data for a specific operation, showing the complete orchestration flow with all details.
"""

import os
import sys
from datetime import datetime, timedelta
from azure.identity import DefaultAzureCredential
from azure.monitor.query import LogsQueryClient, LogsQueryStatus
from azure.core.exceptions import HttpResponseError
import json
from typing import Optional

# Application Insights configuration
WORKSPACE_ID = "b318971e-7337-4649-947f-891c69c60ecb"  # Log Analytics workspace ID
DEFAULT_OPERATION_ID = "99b23ab32f026d74e71e9eab2a44c5ae"


def format_custom_dimensions(custom_dims: str) -> dict:
    """Parse and format custom dimensions from JSON string."""
    try:
        return json.loads(custom_dims) if custom_dims else {}
    except json.JSONDecodeError:
        return {"raw": custom_dims}


def display_trace_details(row: dict) -> None:
    """Display a single trace row with all details."""
    print("\n" + "=" * 80)
    print(f"Timestamp: {row.get('TimeGenerated', 'N/A')}")
    print(f"Severity Level: {row.get('SeverityLevel', 'N/A')}")
    print(f"Message: {row.get('Message', 'N/A')}")
    print(f"Operation ID: {row.get('OperationId', 'N/A')}")
    print(f"Operation Name: {row.get('OperationName', 'N/A')}")
    
    # Parse and display properties (custom dimensions)
    properties = format_custom_dimensions(row.get('Properties', '{}'))
    if properties:
        print("\nProperties/Custom Dimensions:")
        for key, value in properties.items():
            if isinstance(value, dict):
                print(f"  {key}:")
                for sub_key, sub_value in value.items():
                    print(f"    {sub_key}: {sub_value}")
            else:
                print(f"  {key}: {value}")
    
    # Display any additional fields
    standard_fields = {'TimeGenerated', 'SeverityLevel', 'Message', 'OperationId', 
                      'OperationName', 'Properties'}
    additional_fields = {k: v for k, v in row.items() if k not in standard_fields}
    if additional_fields:
        print("\nAdditional Fields:")
        for key, value in additional_fields.items():
            print(f"  {key}: {value}")


def query_telemetry_data(operation_id: Optional[str] = None, time_range_minutes: int = 10):
    """
    Query Application Insights for telemetry data.
    
    Args:
        operation_id: The operation ID to filter by. If None, shows all recent traces.
        time_range_minutes: Number of minutes to look back (default: 10)
    """
    # Initialize the logs query client
    credential = DefaultAzureCredential()
    client = LogsQueryClient(credential)
    
    # Calculate time range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=time_range_minutes)
    
    # Build KQL query - using AppTraces table for Application Insights
    if operation_id:
        query = f"""
        AppTraces
        | where TimeGenerated >= datetime({start_time.isoformat()})
        | where TimeGenerated <= datetime({end_time.isoformat()})
        | where OperationId == '{operation_id}'
        | order by TimeGenerated asc
        """
    else:
        query = f"""
        AppTraces
        | where TimeGenerated >= datetime({start_time.isoformat()})
        | where TimeGenerated <= datetime({end_time.isoformat()})
        | order by TimeGenerated desc
        | take 50
        """
    
    print(f"Querying Application Insights...")
    print(f"Time Range: {start_time.isoformat()} to {end_time.isoformat()}")
    if operation_id:
        print(f"Operation ID: {operation_id}")
    print(f"\nKQL Query:\n{query}\n")
    
    try:
        # Execute the query
        response = client.query_workspace(
            workspace_id=WORKSPACE_ID,
            query=query,
            timespan=(start_time, end_time)
        )
        
        if response.status == LogsQueryStatus.SUCCESS:
            print(f"Query successful! Found {len(response.tables[0].rows)} traces.\n")
            
            if response.tables[0].rows:
                # Get column names
                if hasattr(response.tables[0].columns[0], 'name'):
                    column_names = [col.name for col in response.tables[0].columns]
                else:
                    # If columns are strings, use them directly
                    column_names = response.tables[0].columns
                
                # Display each trace with full details
                for row in response.tables[0].rows:
                    row_dict = dict(zip(column_names, row))
                    display_trace_details(row_dict)
                
                # Summary statistics
                print("\n" + "=" * 80)
                print(f"\nSummary:")
                print(f"Total traces found: {len(response.tables[0].rows)}")
                
                # Group by severity level
                severity_counts = {}
                for row in response.tables[0].rows:
                    row_dict = dict(zip(column_names, row))
                    severity = row_dict.get('SeverityLevel', 'Unknown')
                    severity_counts[severity] = severity_counts.get(severity, 0) + 1
                
                print("\nTraces by Severity Level:")
                for severity, count in sorted(severity_counts.items()):
                    print(f"  {severity}: {count}")
            else:
                print("No traces found for the specified criteria.")
                print("\nTips:")
                print("- The telemetry might take a few minutes to appear in Application Insights")
                print("- Try increasing the time range with --time-range parameter")
                print("- Check if the operation ID is correct")
                
        elif response.status == LogsQueryStatus.PARTIAL:
            print("Query partially successful")
            print(f"Partial error: {response.partial_error}")
            
        else:
            print("Query failed")
            
    except HttpResponseError as e:
        print(f"Error querying Application Insights: {e}")
        print(f"Error details: {e.response.text if hasattr(e.response, 'text') else 'No details'}")
    except Exception as e:
        print(f"Unexpected error: {type(e).__name__}: {e}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Query Application Insights telemetry data")
    parser.add_argument(
        "--operation-id",
        help=f"Operation ID to filter by (default: {DEFAULT_OPERATION_ID})",
        default=DEFAULT_OPERATION_ID
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Show all recent traces without filtering by operation ID"
    )
    parser.add_argument(
        "--time-range",
        type=int,
        default=10,
        help="Time range in minutes to look back (default: 10)"
    )
    
    args = parser.parse_args()
    
    # Query telemetry data
    if args.all:
        query_telemetry_data(operation_id=None, time_range_minutes=args.time_range)
    else:
        query_telemetry_data(operation_id=args.operation_id, time_range_minutes=args.time_range)


if __name__ == "__main__":
    main()