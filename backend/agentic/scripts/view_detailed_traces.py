#!/usr/bin/env python3
"""
View detailed telemetry traces from Application Insights.
This script retrieves and displays all trace details including custom dimensions,
measurements, and full message content.
"""

import os
import sys
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
import asyncio

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from azure.monitor.query import LogsQueryClient, LogsQueryStatus
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import HttpResponseError
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.json import JSON
from rich.syntax import Syntax
from rich import box
from rich.tree import Tree
from rich.text import Text

console = Console()

class DetailedTraceViewer:
    def __init__(self):
        """Initialize the detailed trace viewer."""
        self.credential = DefaultAzureCredential()
        self.client = LogsQueryClient(self.credential)
        
        # Get workspace ID from environment or use default
        self.workspace_id = os.getenv("APPLICATION_INSIGHTS_WORKSPACE_ID", 
                                     "b318971e-7337-4649-947f-891c69c60ecb")
        
    async def get_all_telemetry_data(self, hours_back: int = 1) -> Dict[str, List[Dict[str, Any]]]:
        """Get all telemetry data from different tables."""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours_back)
        
        telemetry_data = {
            "traces": [],
            "customEvents": [],
            "customMetrics": [],
            "dependencies": [],
            "requests": [],
            "exceptions": []
        }
        
        # Query each table separately
        queries = {
            "traces": """
                traces
                | where timestamp > ago(1h)
                | project-away itemId, _ItemId, _TimeReceived, _BilledSize
                | order by timestamp desc
                | limit 100
            """,
            "customEvents": """
                customEvents
                | where timestamp > ago(1h)
                | project-away itemId, _ItemId, _TimeReceived, _BilledSize
                | order by timestamp desc
                | limit 100
            """,
            "customMetrics": """
                customMetrics
                | where timestamp > ago(1h)
                | project-away itemId, _ItemId, _TimeReceived, _BilledSize
                | order by timestamp desc
                | limit 100
            """,
            "dependencies": """
                dependencies
                | where timestamp > ago(1h)
                | project-away itemId, _ItemId, _TimeReceived, _BilledSize
                | order by timestamp desc
                | limit 100
            """,
            "requests": """
                requests
                | where timestamp > ago(1h)
                | project-away itemId, _ItemId, _TimeReceived, _BilledSize
                | order by timestamp desc
                | limit 100
            """,
            "exceptions": """
                exceptions
                | where timestamp > ago(1h)
                | project-away itemId, _ItemId, _TimeReceived, _BilledSize
                | order by timestamp desc
                | limit 50
            """
        }
        
        for table_name, query in queries.items():
            console.print(f"\n[cyan]Querying {table_name} table...[/cyan]")
            try:
                response = self.client.query_workspace(
                    workspace_id=self.workspace_id,
                    query=query,
                    timespan=(start_time, end_time)
                )
                
                if response.status == LogsQueryStatus.SUCCESS:
                    for table in response.tables:
                        for row in table.rows:
                            row_dict = {}
                            for i, column in enumerate(table.columns):
                                value = row[i]
                                # Convert datetime objects to string for JSON serialization
                                if isinstance(value, datetime):
                                    value = value.isoformat()
                                row_dict[column.name] = value
                            telemetry_data[table_name].append(row_dict)
                    
                    console.print(f"[green]✓ Found {len(telemetry_data[table_name])} {table_name}[/green]")
                else:
                    console.print(f"[yellow]⚠ Query for {table_name} returned status: {response.status}[/yellow]")
                    
            except HttpResponseError as e:
                console.print(f"[red]✗ Error querying {table_name}: {e.message}[/red]")
            except Exception as e:
                console.print(f"[red]✗ Unexpected error querying {table_name}: {str(e)}[/red]")
        
        return telemetry_data
    
    def display_trace_details(self, trace: Dict[str, Any], trace_type: str):
        """Display detailed information about a single trace."""
        # Create a tree structure for the trace
        tree = Tree(f"[bold cyan]{trace_type}[/bold cyan] - {trace.get('timestamp', 'N/A')}")
        
        # Basic info
        basic_info = tree.add("[yellow]Basic Information[/yellow]")
        if 'message' in trace:
            basic_info.add(f"Message: {trace['message'][:100]}...")
        if 'severityLevel' in trace:
            basic_info.add(f"Severity: {trace['severityLevel']}")
        if 'cloud_RoleName' in trace:
            basic_info.add(f"Service: {trace['cloud_RoleName']}")
        if 'operation_Name' in trace:
            basic_info.add(f"Operation: {trace['operation_Name']}")
        
        # Custom dimensions
        if 'customDimensions' in trace and trace['customDimensions']:
            custom_dims = tree.add("[green]Custom Dimensions[/green]")
            try:
                dims = json.loads(trace['customDimensions']) if isinstance(trace['customDimensions'], str) else trace['customDimensions']
                for key, value in dims.items():
                    if value is not None and str(value).strip():
                        custom_dims.add(f"{key}: {value}")
            except:
                custom_dims.add(f"Raw: {trace['customDimensions']}")
        
        # Measurements
        if 'customMeasurements' in trace and trace['customMeasurements']:
            measurements = tree.add("[magenta]Measurements[/magenta]")
            try:
                meas = json.loads(trace['customMeasurements']) if isinstance(trace['customMeasurements'], str) else trace['customMeasurements']
                for key, value in meas.items():
                    if value is not None:
                        measurements.add(f"{key}: {value}")
            except:
                measurements.add(f"Raw: {trace['customMeasurements']}")
        
        # Additional fields based on trace type
        if trace_type == "dependencies":
            deps = tree.add("[blue]Dependency Details[/blue]")
            for field in ['target', 'data', 'duration', 'success', 'resultCode']:
                if field in trace and trace[field] is not None:
                    deps.add(f"{field}: {trace[field]}")
        
        elif trace_type == "requests":
            reqs = tree.add("[blue]Request Details[/blue]")
            for field in ['name', 'url', 'duration', 'success', 'resultCode', 'source']:
                if field in trace and trace[field] is not None:
                    reqs.add(f"{field}: {trace[field]}")
        
        elif trace_type == "exceptions":
            excs = tree.add("[red]Exception Details[/red]")
            for field in ['problemId', 'handledAt', 'type', 'message', 'assembly', 'method']:
                if field in trace and trace[field] is not None:
                    excs.add(f"{field}: {trace[field]}")
            if 'details' in trace and trace['details']:
                details_node = excs.add("Stack Trace")
                # Truncate long stack traces
                stack = str(trace['details'])[:500] + "..." if len(str(trace['details'])) > 500 else trace['details']
                details_node.add(Text(stack, style="dim"))
        
        console.print(tree)
        console.print("─" * 80)
    
    def display_summary_table(self, telemetry_data: Dict[str, List[Dict[str, Any]]]):
        """Display a summary table of all telemetry data."""
        table = Table(title="Telemetry Summary", box=box.ROUNDED)
        table.add_column("Type", style="cyan")
        table.add_column("Count", style="green")
        table.add_column("Latest", style="yellow")
        table.add_column("Key Services", style="blue")
        
        for trace_type, traces in telemetry_data.items():
            if traces:
                latest = traces[0].get('timestamp', 'N/A')
                if isinstance(latest, str) and 'T' in latest:
                    latest = latest.split('T')[1].split('.')[0]
                
                # Get unique services
                services = set()
                for trace in traces:
                    if 'cloud_RoleName' in trace and trace['cloud_RoleName']:
                        services.add(trace['cloud_RoleName'])
                    elif 'customDimensions' in trace:
                        try:
                            dims = json.loads(trace['customDimensions']) if isinstance(trace['customDimensions'], str) else trace['customDimensions']
                            if isinstance(dims, dict) and 'service.name' in dims:
                                services.add(dims['service.name'])
                        except:
                            pass
                
                services_str = ", ".join(list(services)[:3])
                if len(services) > 3:
                    services_str += f" (+{len(services)-3})"
                
                table.add_row(
                    trace_type,
                    str(len(traces)),
                    latest,
                    services_str or "N/A"
                )
        
        console.print(table)
    
    def filter_agent_traces(self, telemetry_data: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        """Filter traces related to agent operations."""
        agent_traces = []
        
        for trace_type, traces in telemetry_data.items():
            for trace in traces:
                # Check if this trace is agent-related
                is_agent_trace = False
                agent_info = {"type": trace_type}
                
                # Check custom dimensions
                if 'customDimensions' in trace:
                    try:
                        dims = json.loads(trace['customDimensions']) if isinstance(trace['customDimensions'], str) else trace['customDimensions']
                        if isinstance(dims, dict):
                            if 'agent.name' in dims or 'agent.id' in dims:
                                is_agent_trace = True
                                agent_info['agent_name'] = dims.get('agent.name', 'Unknown')
                                agent_info['agent_id'] = dims.get('agent.id', 'Unknown')
                            elif 'service.name' in dims and ('Agent' in dims['service.name'] or 'agent' in dims['service.name']):
                                is_agent_trace = True
                    except:
                        pass
                
                # Check message content
                if 'message' in trace and trace['message']:
                    message_lower = str(trace['message']).lower()
                    if any(keyword in message_lower for keyword in ['agent', 'orchestrat', 'invoke', 'telemetry']):
                        is_agent_trace = True
                
                # Check operation name
                if 'operation_Name' in trace and trace['operation_Name']:
                    op_lower = str(trace['operation_Name']).lower()
                    if any(keyword in op_lower for keyword in ['agent', 'invoke', 'orchestrat']):
                        is_agent_trace = True
                
                if is_agent_trace:
                    trace['_agent_info'] = agent_info
                    agent_traces.append(trace)
        
        return agent_traces

async def main():
    """Main function to view detailed traces."""
    console.print(Panel.fit(
        "[bold cyan]Application Insights Detailed Trace Viewer[/bold cyan]\n"
        "Retrieving all telemetry data with full details...",
        box=box.DOUBLE
    ))
    
    viewer = DetailedTraceViewer()
    
    # Get all telemetry data
    console.print("\n[bold]Fetching telemetry data from Application Insights...[/bold]")
    telemetry_data = await viewer.get_all_telemetry_data(hours_back=2)
    
    # Display summary
    console.print("\n[bold]📊 Telemetry Summary[/bold]")
    viewer.display_summary_table(telemetry_data)
    
    # Filter agent-related traces
    agent_traces = viewer.filter_agent_traces(telemetry_data)
    console.print(f"\n[bold]🤖 Found {len(agent_traces)} agent-related traces[/bold]")
    
    # Display detailed agent traces
    if agent_traces:
        console.print("\n[bold]📋 Detailed Agent Traces (Most Recent First)[/bold]\n")
        
        # Sort by timestamp
        agent_traces.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        # Display up to 20 most recent agent traces
        for i, trace in enumerate(agent_traces[:20]):
            viewer.display_trace_details(trace, trace['_agent_info']['type'])
            
            if i < len(agent_traces) - 1 and i < 19:
                if console.input("\n[yellow]Press Enter to see next trace, or 'q' to quit: [/yellow]").lower() == 'q':
                    break
    
    # Display all traces option
    if console.input("\n[yellow]View ALL traces regardless of type? (y/n): [/yellow]").lower() == 'y':
        console.print("\n[bold]📜 All Recent Traces[/bold]\n")
        
        all_traces = []
        for trace_type, traces in telemetry_data.items():
            for trace in traces:
                trace['_trace_type'] = trace_type
                all_traces.append(trace)
        
        all_traces.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        for i, trace in enumerate(all_traces[:30]):
            viewer.display_trace_details(trace, trace['_trace_type'])
            
            if i < len(all_traces) - 1 and i < 29:
                if i % 5 == 4:  # Pause every 5 traces
                    if console.input("\n[yellow]Press Enter to continue, or 'q' to quit: [/yellow]").lower() == 'q':
                        break
    
    # Export option
    if console.input("\n[yellow]Export all data to JSON file? (y/n): [/yellow]").lower() == 'y':
        filename = f"telemetry_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(telemetry_data, f, indent=2, default=str)
        console.print(f"[green]✅ Data exported to {filename}[/green]")
    
    console.print("\n[bold green]✨ Trace viewing complete![/bold green]")

if __name__ == "__main__":
    asyncio.run(main())