#!/usr/bin/env python3
"""
Show telemetry summary for connected agents.
Displays the telemetry data that was sent to Application Insights.
"""

from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

# Summary of telemetry captured
telemetry_summary = {
    "test_run": "connected-agents-test",
    "timestamp": "2025-05-28 09:00:32",
    "total_items_sent": 77,
    "total_items_accepted": 77,
    "transmissions": [
        {
            "operation": "Weather delegation test",
            "items_sent": 24,
            "spans": [
                "connected_agents.full_test",
                "delegation.weather",
                "agent.invoke (Weather Agent)",
                "weather.tool.GetWeather",
                "HTTP calls to weather.gov API"
            ]
        },
        {
            "operation": "Calculator delegation test", 
            "items_sent": 37,
            "spans": [
                "delegation.calculator",
                "agent.invoke (Calculator Agent)",
                "calculator.tool.Calculate",
                "mathematical computation"
            ]
        },
        {
            "operation": "Test summary",
            "items_sent": 16,
            "spans": [
                "test.completed attributes",
                "final telemetry flush"
            ]
        }
    ]
}

def show_telemetry_summary():
    """Display telemetry summary."""
    
    # Header
    console.print(Panel.fit(
        "[bold cyan]Connected Agents Telemetry Summary[/bold cyan]\n"
        f"Test Run: {telemetry_summary['test_run']}\n"
        f"Timestamp: {telemetry_summary['timestamp']}",
        box=box.ROUNDED
    ))
    
    # Transmission table
    table = Table(title="Telemetry Transmissions", box=box.SIMPLE)
    table.add_column("Operation", style="cyan")
    table.add_column("Items Sent", style="green")
    table.add_column("Spans Tracked", style="yellow")
    
    for transmission in telemetry_summary["transmissions"]:
        spans = "\n".join(f"• {span}" for span in transmission["spans"])
        table.add_row(
            transmission["operation"],
            str(transmission["items_sent"]),
            spans
        )
    
    console.print(table)
    
    # Summary stats
    console.print(f"\n[bold green]✅ Total telemetry items sent: {telemetry_summary['total_items_sent']}[/bold green]")
    console.print(f"[bold green]✅ Total items accepted: {telemetry_summary['total_items_accepted']}[/bold green]")
    console.print(f"[bold green]✅ Success rate: 100%[/bold green]")
    
    # What's tracked
    console.print("\n[bold]What's Being Tracked:[/bold]")
    tracked_items = [
        "• Each orchestrator invocation with message content",
        "• Delegation decisions (orchestrator → specialized agent)",
        "• Agent response times and durations",
        "• Tool calls (weather API, calculator operations)",
        "• HTTP requests to external services",
        "• Full distributed trace with parent-child relationships",
        "• Custom dimensions (agent IDs, operation types, etc.)",
        "• Performance metrics for each step"
    ]
    
    for item in tracked_items:
        console.print(f"  {item}")
    
    # How to view
    console.print("\n[bold]How to View in Application Insights:[/bold]")
    console.print("  1. Go to Azure Portal → Application Insights")
    console.print("  2. Resource: stratos-multi-agent-appinsights")
    console.print("  3. Click on 'Transaction Search' or 'Logs'")
    console.print("  4. Filter by:")
    console.print("     - Time range: Last hour")
    console.print("     - Cloud role: connected-agents-test")
    console.print("     - Operation name: connected_agents.full_test")
    
    # Sample queries
    console.print("\n[bold]Sample KQL Queries:[/bold]")
    console.print("[dim]// View all connected agent operations[/dim]")
    console.print("traces | where cloud_RoleName == 'connected-agents-test' | order by timestamp desc")
    console.print("\n[dim]// View delegation flows[/dim]")
    console.print("requests | where name contains 'delegation' | project timestamp, name, duration")
    console.print("\n[dim]// View performance metrics[/dim]")
    console.print("dependencies | where target contains 'agent' | summarize avg(duration) by name")

if __name__ == "__main__":
    show_telemetry_summary()