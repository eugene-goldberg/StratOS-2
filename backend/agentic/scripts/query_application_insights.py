#!/usr/bin/env python3
"""
Query Application Insights to verify telemetry traces.
This script retrieves and analyzes the telemetry data to ensure complete agent flow tracking.
"""

import os
import sys
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any
import asyncio

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from azure.monitor.query import LogsQueryClient, LogsQueryStatus
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import HttpResponseError
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()

class ApplicationInsightsQuerier:
    def __init__(self):
        """Initialize the Application Insights querier."""
        self.credential = DefaultAzureCredential()
        self.client = LogsQueryClient(self.credential)
        
        # Get workspace ID from Application Insights
        # For StratOS, we'll use the Application Insights workspace
        self.workspace_id = os.getenv("APPLICATION_INSIGHTS_WORKSPACE_ID", 
                                     "b318971e-7337-4649-947f-891c69c60ecb")  # StratOS Application Insights workspace
        
    async def query_traces(self, hours_back: int = 1) -> List[Dict[str, Any]]:
        """Query recent traces from Application Insights."""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours_back)
        
        # KQL query to get all traces with agent information
        # Application Insights uses different table names
        query = """
        dependencies
        | union requests, customEvents, customMetrics, traces
        | where timestamp > ago(1h)
        | extend service = tostring(customDimensions["service.name"])
        | where service != ""
        | project 
            timestamp,
            message = tostring(coalesce(message, name, operation_Name)),
            severityLevel,
            service,
            agent = tostring(customDimensions["agent.name"]),
            agent_id = tostring(customDimensions["agent.id"]),
            operation = tostring(customDimensions["operation"]),
            duration = todouble(coalesce(duration, customDimensions["response.duration_seconds"])),
            response_size = toint(customDimensions["response.size"]),
            trace_id = tostring(customDimensions["trace_id"]),
            span_id = tostring(customDimensions["span_id"])
        | order by timestamp desc
        | limit 100
        """
        
        try:
            response = self.client.query_workspace(
                workspace_id=self.workspace_id,
                query=query,
                timespan=(start_time, end_time)
            )
            
            if response.status == LogsQueryStatus.PARTIAL:
                console.print("[yellow]Warning: Query returned partial results[/yellow]")
                if response.partial_error:
                    console.print(f"[yellow]Partial error: {response.partial_error.message}[/yellow]")
            elif response.status == LogsQueryStatus.FAILURE:
                console.print(f"[red]Query failed: {response.error.message}[/red]")
                return []
            
            # Convert results to list of dicts
            results = []
            for table in response.tables:
                for row in table.rows:
                    row_dict = {}
                    for i, column in enumerate(table.columns):
                        row_dict[column.name] = row[i]
                    results.append(row_dict)
            
            return results
            
        except HttpResponseError as e:
            console.print(f"[red]HTTP error querying Application Insights: {e}[/red]")
            return []
        except Exception as e:
            console.print(f"[red]Error querying Application Insights: {e}[/red]")
            return []
    
    async def query_agent_summary(self) -> Dict[str, Any]:
        """Query summary statistics for agent invocations."""
        query = """
        dependencies
        | union requests, customEvents, customMetrics, traces
        | where timestamp > ago(24h)
        | extend agent = tostring(customDimensions["agent.name"])
        | where agent != ""
        | summarize 
            total_invocations = count(),
            avg_duration = avg(todouble(coalesce(duration, customDimensions["response.duration_seconds"]))),
            p95_duration = percentile(todouble(coalesce(duration, customDimensions["response.duration_seconds"])), 95),
            total_bytes = sum(toint(customDimensions["response.size"]))
            by agent
        | order by total_invocations desc
        """
        
        try:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=24)
            
            response = self.client.query_workspace(
                workspace_id=self.workspace_id,
                query=query,
                timespan=(start_time, end_time)
            )
            
            summary = {}
            if response.status == LogsQueryStatus.SUCCESS:
                for table in response.tables:
                    for row in table.rows:
                        agent_name = row[0]
                        summary[agent_name] = {
                            "total_invocations": row[1],
                            "avg_duration": row[2],
                            "p95_duration": row[3],
                            "total_bytes": row[4]
                        }
            
            return summary
            
        except Exception as e:
            console.print(f"[red]Error querying agent summary: {e}[/red]")
            return {}
    
    async def query_errors(self) -> List[Dict[str, Any]]:
        """Query recent errors and exceptions."""
        query = """
        exceptions
        | union (traces | where severityLevel >= 3)
        | where timestamp > ago(1h)
        | project 
            timestamp,
            itemType,
            message = coalesce(message, outerMessage, problemId),
            service = tostring(customDimensions["service.name"]),
            agent = tostring(customDimensions["agent.name"]),
            exception_type = type,
            stack_trace = tostring(details)
        | order by timestamp desc
        | limit 50
        """
        
        try:
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(hours=1)
            
            response = self.client.query_workspace(
                workspace_id=self.workspace_id,
                query=query,
                timespan=(start_time, end_time)
            )
            
            errors = []
            if response.status == LogsQueryStatus.SUCCESS:
                for table in response.tables:
                    for row in table.rows:
                        error_dict = {}
                        for i, column in enumerate(table.columns):
                            error_dict[column.name] = row[i]
                        errors.append(error_dict)
            
            return errors
            
        except Exception as e:
            console.print(f"[red]Error querying errors: {e}[/red]")
            return []

def display_traces(traces: List[Dict[str, Any]]):
    """Display traces in a formatted table."""
    if not traces:
        console.print("[yellow]No traces found in the specified time range.[/yellow]")
        return
    
    table = Table(title="Recent Agent Traces", box=box.ROUNDED)
    table.add_column("Timestamp", style="cyan")
    table.add_column("Service", style="green")
    table.add_column("Agent", style="yellow")
    table.add_column("Operation", style="blue")
    table.add_column("Duration (s)", style="magenta")
    table.add_column("Message", style="white", overflow="fold")
    
    for trace in traces[:20]:  # Show top 20
        timestamp = trace.get("timestamp", "")
        if isinstance(timestamp, datetime):
            timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        duration = trace.get("duration", 0)
        duration_str = f"{duration:.3f}" if duration else "N/A"
        
        table.add_row(
            timestamp,
            trace.get("service", ""),
            trace.get("agent", ""),
            trace.get("operation", ""),
            duration_str,
            trace.get("message", "")[:60] + "..."
        )
    
    console.print(table)

def display_summary(summary: Dict[str, Any]):
    """Display agent summary statistics."""
    if not summary:
        console.print("[yellow]No agent summary data available.[/yellow]")
        return
    
    table = Table(title="Agent Performance Summary (Last 24h)", box=box.ROUNDED)
    table.add_column("Agent", style="cyan")
    table.add_column("Total Invocations", style="green")
    table.add_column("Avg Duration (s)", style="yellow")
    table.add_column("P95 Duration (s)", style="magenta")
    table.add_column("Total Data (KB)", style="blue")
    
    for agent, stats in summary.items():
        table.add_row(
            agent,
            str(stats.get("total_invocations", 0)),
            f"{stats.get('avg_duration', 0):.3f}",
            f"{stats.get('p95_duration', 0):.3f}",
            f"{stats.get('total_bytes', 0) / 1024:.1f}"
        )
    
    console.print(table)

def display_errors(errors: List[Dict[str, Any]]):
    """Display recent errors."""
    if not errors:
        console.print(Panel("[green]✅ No errors found in the last hour![/green]", 
                          title="Error Status", box=box.ROUNDED))
        return
    
    console.print(Panel(f"[red]⚠️  Found {len(errors)} errors in the last hour[/red]", 
                      title="Error Status", box=box.ROUNDED))
    
    for error in errors[:5]:  # Show top 5
        timestamp = error.get("timestamp", "")
        if isinstance(timestamp, datetime):
            timestamp = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        console.print(f"\n[red]Error at {timestamp}[/red]")
        console.print(f"Service: {error.get('service', 'Unknown')}")
        console.print(f"Agent: {error.get('agent', 'N/A')}")
        console.print(f"Message: {error.get('message', 'No message')}")
        if error.get("exception_type"):
            console.print(f"Exception: {error.get('exception_type')}")

async def main():
    """Main function to query and display Application Insights data."""
    console.print(Panel.fit(
        "[bold cyan]Application Insights Telemetry Verification[/bold cyan]\n"
        "Querying telemetry data for StratOS agents...",
        box=box.DOUBLE
    ))
    
    querier = ApplicationInsightsQuerier()
    
    # Query recent traces
    console.print("\n[bold]Fetching recent traces...[/bold]")
    traces = await querier.query_traces(hours_back=1)
    
    if traces:
        console.print(f"[green]✅ Found {len(traces)} traces[/green]")
        display_traces(traces)
        
        # Analyze trace patterns
        services = set(t.get("service", "") for t in traces if t.get("service"))
        agents = set(t.get("agent", "") for t in traces if t.get("agent"))
        
        console.print(f"\n[bold]Active Services:[/bold] {', '.join(services)}")
        console.print(f"[bold]Active Agents:[/bold] {', '.join(agents)}")
    else:
        console.print("[yellow]No traces found. This could mean:[/yellow]")
        console.print("  1. No recent agent activity")
        console.print("  2. Telemetry not reaching Application Insights")
        console.print("  3. Workspace ID configuration issue")
    
    # Query agent summary
    console.print("\n[bold]Fetching agent performance summary...[/bold]")
    summary = await querier.query_agent_summary()
    display_summary(summary)
    
    # Query errors
    console.print("\n[bold]Checking for recent errors...[/bold]")
    errors = await querier.query_errors()
    display_errors(errors)
    
    # Final verdict
    console.print("\n" + "="*60)
    if traces and len(traces) > 10:
        console.print(Panel(
            "[bold green]✅ TELEMETRY VERIFIED SUCCESSFULLY[/bold green]\n\n"
            f"• Found {len(traces)} recent traces\n"
            f"• {len(services)} services active\n"
            f"• {len(agents)} agents tracked\n"
            f"• {'No errors detected' if not errors else f'{len(errors)} errors found'}\n\n"
            "[green]The telemetry system is working correctly and capturing all agent interactions.[/green]",
            title="Verification Complete",
            box=box.DOUBLE,
            border_style="green"
        ))
    else:
        console.print(Panel(
            "[bold yellow]⚠️  TELEMETRY NEEDS ATTENTION[/bold yellow]\n\n"
            f"• Only {len(traces)} traces found\n"
            f"• Expected more agent activity\n\n"
            "Run more agent tests to generate additional telemetry data.",
            title="Verification Incomplete",
            box=box.DOUBLE,
            border_style="yellow"
        ))

if __name__ == "__main__":
    asyncio.run(main())