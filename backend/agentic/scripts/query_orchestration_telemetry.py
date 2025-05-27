#!/usr/bin/env python3
"""
Query Application Insights to retrieve and display the full orchestration telemetry.
This shows the complete evidence of agent delegation flows.
"""

import os
import sys
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any
import asyncio

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from azure.monitor.query import LogsQueryClient, LogsQueryStatus
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import HttpResponseError
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich import box

console = Console()

class OrchestrationTelemetryQuerier:
    def __init__(self):
        """Initialize the telemetry querier."""
        self.credential = DefaultAzureCredential()
        self.client = LogsQueryClient(self.credential)
        self.workspace_id = "b318971e-7337-4649-947f-891c69c60ecb"  # From earlier
        
    async def query_orchestration_traces(self) -> Dict[str, Any]:
        """Query traces for orchestration telemetry proof."""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=1)
        
        # Query for all telemetry from our service
        query = """
        AppTraces
        | where TimeGenerated > ago(1h)
        | where AppRoleName == "OrchestrationTelemetryProof"
        | project TimeGenerated, Message, SeverityLevel, Properties
        | order by TimeGenerated desc
        | limit 100
        """
        
        traces = []
        try:
            response = self.client.query_workspace(
                workspace_id=self.workspace_id,
                query=query,
                timespan=(start_time, end_time)
            )
            
            if response.status == LogsQueryStatus.SUCCESS:
                for table in response.tables:
                    for row in table.rows:
                        trace = {}
                        for i, column in enumerate(table.columns):
                            trace[column.name] = row[i]
                        traces.append(trace)
                console.print(f"[green]✓ Found {len(traces)} traces from OrchestrationTelemetryProof[/green]")
            else:
                console.print(f"[yellow]Query returned status: {response.status}[/yellow]")
                
        except Exception as e:
            console.print(f"[red]Error querying traces: {str(e)}[/red]")
            
        return {"traces": traces}
    
    async def query_dependencies(self) -> Dict[str, Any]:
        """Query dependency calls (agent invocations)."""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=1)
        
        query = """
        AppDependencies
        | where TimeGenerated > ago(1h)
        | where AppRoleName == "OrchestrationTelemetryProof"
        | project TimeGenerated, Name, Target, DurationMs, Success, ResultCode, Properties
        | order by TimeGenerated desc
        | limit 50
        """
        
        dependencies = []
        try:
            response = self.client.query_workspace(
                workspace_id=self.workspace_id,
                query=query,
                timespan=(start_time, end_time)
            )
            
            if response.status == LogsQueryStatus.SUCCESS:
                for table in response.tables:
                    for row in table.rows:
                        dep = {}
                        for i, column in enumerate(table.columns):
                            dep[column.name] = row[i]
                        dependencies.append(dep)
                console.print(f"[green]✓ Found {len(dependencies)} dependency calls[/green]")
                
        except Exception as e:
            console.print(f"[red]Error querying dependencies: {str(e)}[/red]")
            
        return {"dependencies": dependencies}
    
    async def query_custom_events(self) -> Dict[str, Any]:
        """Query custom events with agent details."""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=1)
        
        query = """
        AppEvents
        | where TimeGenerated > ago(1h)
        | where AppRoleName == "OrchestrationTelemetryProof"
        | extend 
            TestName = tostring(Properties["test.name"]),
            ExpectedAgent = tostring(Properties["test.expected_agent"]),
            OrchestratorThread = tostring(Properties["orchestrator.thread_id"]),
            ToolCallFunction = tostring(Properties["tool_call.function"]),
            SpecialistName = tostring(Properties["specialist.name"]),
            SpecialistThread = tostring(Properties["specialist.thread_id"]),
            ResponseLength = toint(Properties["specialist.response_length"])
        | project TimeGenerated, Name, TestName, ExpectedAgent, OrchestratorThread, 
                  ToolCallFunction, SpecialistName, SpecialistThread, ResponseLength
        | order by TimeGenerated desc
        | limit 50
        """
        
        events = []
        try:
            response = self.client.query_workspace(
                workspace_id=self.workspace_id,
                query=query,
                timespan=(start_time, end_time)
            )
            
            if response.status == LogsQueryStatus.SUCCESS:
                for table in response.tables:
                    for row in table.rows:
                        event = {}
                        for i, column in enumerate(table.columns):
                            event[column.name] = row[i]
                        events.append(event)
                console.print(f"[green]✓ Found {len(events)} custom events[/green]")
                
        except Exception as e:
            console.print(f"[red]Error querying custom events: {str(e)}[/red]")
            
        return {"custom_events": events}
    
    def display_orchestration_flow(self, data: Dict[str, Any]):
        """Display the orchestration flow from telemetry."""
        console.print(Panel.fit(
            "[bold cyan]Orchestration Telemetry Evidence[/bold cyan]\n"
            "Complete flow from Application Insights",
            box=box.DOUBLE
        ))
        
        # Group events by test
        test_flows = {}
        for event in data.get("custom_events", []):
            test_name = event.get("TestName", "Unknown")
            if test_name not in test_flows:
                test_flows[test_name] = []
            test_flows[test_name].append(event)
        
        # Display each test flow
        for test_name, events in test_flows.items():
            tree = Tree(f"[bold yellow]{test_name}[/bold yellow]")
            
            # Find orchestrator thread
            orch_thread = None
            for event in events:
                if event.get("OrchestratorThread"):
                    orch_thread = event["OrchestratorThread"]
                    orch_node = tree.add(f"[cyan]Orchestrator Thread: {orch_thread}[/cyan]")
                    break
            
            # Find tool call
            for event in events:
                if event.get("ToolCallFunction"):
                    tool_node = orch_node.add(f"[green]Tool Call: {event['ToolCallFunction']}[/green]")
                    
                    # Find specialist invocation
                    if event.get("SpecialistName"):
                        spec_node = tool_node.add(f"[yellow]Specialist: {event['SpecialistName']}[/yellow]")
                        if event.get("SpecialistThread"):
                            spec_node.add(f"Thread: {event['SpecialistThread']}")
                        if event.get("ResponseLength"):
                            spec_node.add(f"Response: {event['ResponseLength']} chars")
            
            console.print(tree)
            console.print("─" * 60)

async def main():
    """Main function to query and display telemetry."""
    querier = OrchestrationTelemetryQuerier()
    
    console.print("[bold]Querying Application Insights for Orchestration Telemetry...[/bold]\n")
    
    # Query different telemetry types
    traces_data = await querier.query_orchestration_traces()
    deps_data = await querier.query_dependencies()
    events_data = await querier.query_custom_events()
    
    # Combine all data
    all_data = {
        "traces": traces_data.get("traces", []),
        "dependencies": deps_data.get("dependencies", []),
        "custom_events": events_data.get("custom_events", [])
    }
    
    # Display orchestration flow
    if any(all_data.values()):
        querier.display_orchestration_flow(all_data)
        
        # Save raw data
        output_file = f"telemetry_query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w') as f:
            json.dump(all_data, f, indent=2, default=str)
        console.print(f"\n[green]💾 Raw telemetry data saved to: {output_file}[/green]")
        
        # Display summary
        console.print("\n[bold]📊 Telemetry Summary:[/bold]")
        table = Table(box=box.ROUNDED)
        table.add_column("Type", style="cyan")
        table.add_column("Count", style="green")
        
        table.add_row("Traces", str(len(all_data["traces"])))
        table.add_row("Dependencies", str(len(all_data["dependencies"])))
        table.add_row("Custom Events", str(len(all_data["custom_events"])))
        
        console.print(table)
        
        console.print("\n[bold green]✅ Telemetry evidence retrieved successfully![/bold green]")
    else:
        console.print("[yellow]⚠️  No telemetry data found. Data may take 2-5 minutes to appear.[/yellow]")
        console.print("Try running this script again in a few minutes.")

if __name__ == "__main__":
    asyncio.run(main())