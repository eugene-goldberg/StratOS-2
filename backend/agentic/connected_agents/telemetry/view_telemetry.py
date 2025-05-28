#!/usr/bin/env python3
"""
View telemetry data from Application Insights for connected agents.
Shows the full flow of delegations and tool calls.
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from azure.monitor.query import LogsQueryClient
from azure.identity import DefaultAzureCredential
from azure.core.exceptions import HttpResponseError

# Rich formatting
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()

async def query_connected_agents_telemetry():
    """Query and display telemetry for connected agents."""
    
    credential = DefaultAzureCredential()
    client = LogsQueryClient(credential)
    
    # Application Insights workspace ID
    workspace_id = os.getenv("APPLICATION_INSIGHTS_WORKSPACE_ID", "b318971e-7337-4649-947f-891c69c60ecb")
    
    # Query for recent traces
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=1)
    
    # KQL query for connected agents
    query = """
    traces
    | where timestamp > ago(1h)
    | where cloud_RoleName contains "connected-agents" or message contains "connected_agents" or message contains "delegation"
    | project timestamp, operation_Name, message, severityLevel, customDimensions
    | order by timestamp desc
    | take 50
    """
    
    try:
        response = await client.query_workspace(
            workspace_id=workspace_id,
            query=query,
            timespan=(start_time, end_time)
        )
        
        # Create table
        table = Table(title="Connected Agents Telemetry", box=box.ROUNDED)
        table.add_column("Timestamp", style="cyan")
        table.add_column("Operation", style="green")
        table.add_column("Message", style="yellow")
        table.add_column("Level", style="magenta")
        
        if response.tables:
            for row in response.tables[0].rows:
                timestamp = row[0].strftime("%H:%M:%S") if row[0] else "N/A"
                operation = str(row[1])[:30] if row[1] else "N/A"
                message = str(row[2])[:60] if row[2] else "N/A"
                level = str(row[3]) if row[3] else "N/A"
                
                table.add_row(timestamp, operation, message, level)
        
        console.print(table)
        
        # Query for delegation flows
        delegation_query = """
        traces
        | where timestamp > ago(1h)
        | where message contains "delegation" or message contains "specialist" or message contains "weather" or message contains "calculator"
        | project timestamp, message, severityLevel, customDimensions
        | order by timestamp desc
        | take 20
        """
        
        response2 = await client.query_workspace(
            workspace_id=workspace_id,
            query=delegation_query,
            timespan=(start_time, end_time)
        )
        
        if response2.tables and response2.tables[0].rows:
            console.print("\n[bold cyan]Delegation Traces:[/bold cyan]")
            for row in response2.tables[0].rows:
                timestamp = row[0].strftime("%H:%M:%S") if row[0] else "N/A"
                message = str(row[1])[:100] if row[1] else "N/A"
                console.print(f"[dim]{timestamp}[/dim] {message}")
        
        # Show Application Insights portal link
        console.print("\n[bold green]View in Azure Portal:[/bold green]")
        console.print(f"https://portal.azure.com/#@/resource/subscriptions/514bd6d3-2c02-45c6-a86f-29cf262a379a/resourceGroups/semantic-kernel-multi-agent-rg/providers/microsoft.insights/components/stratos-multi-agent-appinsights/overview")
        
    except HttpResponseError as e:
        console.print(f"[red]Error querying Application Insights: {e}[/red]")
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")

if __name__ == "__main__":
    asyncio.run(query_connected_agents_telemetry())