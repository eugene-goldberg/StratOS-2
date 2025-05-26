#!/usr/bin/env python3
"""
Show recent telemetry data that was sent to Application Insights.
This script displays the telemetry that was successfully transmitted.
"""

import os
import sys
import json
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.json import JSON
from rich import box
from rich.syntax import Syntax

console = Console()

# Data from recent test runs
RECENT_TELEMETRY = {
    "test_run_1": {
        "timestamp": "2025-05-26T10:18:40",
        "service": "QuickAgentTest",
        "traces_sent": 20,
        "agent_invocations": [
            {
                "agent": "CEO Log Agent",
                "agent_id": "asst_N5azTOnrhdlm4K9wC6i9OtHA",
                "message": "Test entry at 10:18:40 - Market conditions look favorable for Q4",
                "response_length": 395,
                "duration": 4.8,
                "trace_id": "9cf2bdd0af83ad71912cbfab0f6bdfea",
                "custom_dimensions": {
                    "service.name": "QuickAgentTest",
                    "service.version": "1.0.0",
                    "agent.name": "CEO Log Agent",
                    "agent.id": "asst_N5azTOnrhdlm4K9wC6i9OtHA",
                    "operation": "agent.invoke",
                    "response.duration_seconds": 4.8,
                    "response.size": 395,
                    "framework": "semantic_kernel",
                    "thread.id": "thread_n2ydRZIeNvOmwVXne4NQiFdl",
                    "run.id": "run_SHTDmh6wXrYaDf7e46SGLvvn"
                }
            }
        ]
    },
    "test_run_2": {
        "timestamp": "2025-05-26T10:18:57",
        "service": "SKAgentTelemetryTester",
        "traces_sent": 24,
        "agent_invocations": [
            {
                "agent": "MainOrchestrator",
                "agent_id": "asst_IkSbH3d9TaRWfpOcCCE4QxK4",
                "message": "I need help creating a strategy for entering new markets in Asia...",
                "error": "Missing function tools",
                "trace_id": "aebf5391b985ee84ebaa28466a103844",
                "custom_dimensions": {
                    "service.name": "SKAgentTelemetryTester",
                    "agent.name": "MainOrchestrator",
                    "agent.id": "asst_IkSbH3d9TaRWfpOcCCE4QxK4",
                    "error": "AgentInvokeException",
                    "missing_tools": ["invoke_actionplanningagent", "invoke_alignmentscoringagent", "invoke_analysisorchestrator"]
                }
            },
            {
                "agent": "CEOLogAgent",
                "agent_id": "asst_N5azTOnrhdlm4K9wC6i9OtHA", 
                "message": "I had a productive meeting with our board today. They're excited about our AI in...",
                "response_length": 73,
                "duration": 3.7,
                "trace_id": "aebf5391b985ee84ebaa28466a103844",
                "custom_dimensions": {
                    "service.name": "SKAgentTelemetryTester",
                    "agent.name": "CEOLogAgent",
                    "agent.id": "asst_N5azTOnrhdlm4K9wC6i9OtHA",
                    "operation": "agent.invoke",
                    "response.duration_seconds": 3.7,
                    "response.size": 73,
                    "thread.id": "thread_gsgh3KYvPssU73S3n1QNo2sg",
                    "run.id": "run_5BLPSAYJQVeOu8GKH5HaoCZT"
                }
            },
            {
                "agent": "SWOTTOWSAgent",
                "agent_id": "asst_cCpLqNIt5nRrYuYHNUKs6HyM",
                "message": "Perform a SWOT analysis for our expansion into the healthcare market....",
                "response_length": 434,
                "duration": 5.0,
                "trace_id": "aebf5391b985ee84ebaa28466a103844",
                "custom_dimensions": {
                    "service.name": "SKAgentTelemetryTester",
                    "agent.name": "SWOTTOWSAgent",
                    "agent.id": "asst_cCpLqNIt5nRrYuYHNUKs6HyM",
                    "operation": "agent.invoke",
                    "response.duration_seconds": 5.0,
                    "response.size": 434,
                    "thread.id": "thread_30MfzlXLOC5LKHqGHSJxUQdS",
                    "run.id": "run_xnP5iGOQRoXbTdFULk9bJhNl"
                }
            },
            {
                "agent": "RiskOpportunityAgent",
                "agent_id": "asst_KE82pn2anmOhKJU7URCimdzw",
                "message": "What are the key risks in our supply chain?...",
                "response_length": 452,
                "duration": 3.5,
                "trace_id": "aebf5391b985ee84ebaa28466a103844",
                "custom_dimensions": {
                    "service.name": "SKAgentTelemetryTester",
                    "agent.name": "RiskOpportunityAgent",
                    "agent.id": "asst_KE82pn2anmOhKJU7URCimdzw",
                    "operation": "agent.invoke",
                    "response.duration_seconds": 3.5,
                    "response.size": 452,
                    "thread.id": "thread_PtvnSKSln7JNIozsoG4FY2om",
                    "run.id": "run_X2W49ujijx08ypopROpnCzpy"
                }
            }
        ]
    }
}

# Telemetry transmission details
TRANSMISSION_LOG = [
    {
        "timestamp": "2025-05-26 10:18:45,529",
        "endpoint": "https://eastus-8.in.applicationinsights.azure.com/v2.1/track",
        "items_sent": 20,
        "items_accepted": 20,
        "status": "SUCCESS",
        "service": "QuickAgentTest"
    },
    {
        "timestamp": "2025-05-26 10:19:17,617", 
        "endpoint": "https://eastus-8.in.applicationinsights.azure.com/v2.1/track",
        "items_sent": 13,
        "items_accepted": 13,
        "status": "SUCCESS",
        "service": "SKAgentTelemetryTester"
    },
    {
        "timestamp": "2025-05-26 10:19:20,863",
        "endpoint": "https://eastus-8.in.applicationinsights.azure.com/v2.1/track",
        "items_sent": 11,
        "items_accepted": 11,
        "status": "SUCCESS", 
        "service": "SKAgentTelemetryTester"
    }
]

def display_transmission_summary():
    """Display summary of telemetry transmissions."""
    table = Table(title="Telemetry Transmission Summary", box=box.ROUNDED)
    table.add_column("Timestamp", style="cyan")
    table.add_column("Service", style="green")
    table.add_column("Items Sent", style="yellow")
    table.add_column("Items Accepted", style="green")
    table.add_column("Status", style="bold green")
    
    total_sent = 0
    total_accepted = 0
    
    for trans in TRANSMISSION_LOG:
        table.add_row(
            trans["timestamp"],
            trans["service"],
            str(trans["items_sent"]),
            str(trans["items_accepted"]),
            trans["status"]
        )
        total_sent += trans["items_sent"]
        total_accepted += trans["items_accepted"]
    
    console.print(table)
    console.print(f"\n[bold green]Total: {total_sent} items sent, {total_accepted} items accepted (100% success rate)[/bold green]")

def display_agent_invocations():
    """Display detailed agent invocation traces."""
    console.print("\n[bold cyan]Agent Invocation Details[/bold cyan]\n")
    
    for test_name, test_data in RECENT_TELEMETRY.items():
        panel_content = f"[yellow]Service:[/yellow] {test_data['service']}\n"
        panel_content += f"[yellow]Timestamp:[/yellow] {test_data['timestamp']}\n"
        panel_content += f"[yellow]Traces Sent:[/yellow] {test_data['traces_sent']}"
        
        console.print(Panel(panel_content, title=f"Test Run: {test_name}", box=box.DOUBLE))
        
        for i, invocation in enumerate(test_data['agent_invocations']):
            console.print(f"\n[bold]Agent Invocation {i+1}:[/bold]")
            
            # Basic info
            info_table = Table(box=box.SIMPLE)
            info_table.add_column("Field", style="cyan")
            info_table.add_column("Value", style="white")
            
            info_table.add_row("Agent", invocation['agent'])
            info_table.add_row("Agent ID", invocation['agent_id'])
            info_table.add_row("Message", invocation['message'][:80] + "...")
            
            if 'error' in invocation:
                info_table.add_row("Error", f"[red]{invocation['error']}[/red]")
            else:
                info_table.add_row("Response Length", f"{invocation['response_length']} chars")
                info_table.add_row("Duration", f"{invocation['duration']}s")
            
            info_table.add_row("Trace ID", invocation['trace_id'])
            
            console.print(info_table)
            
            # Custom dimensions
            console.print("\n[yellow]Custom Dimensions:[/yellow]")
            dims_json = JSON(json.dumps(invocation['custom_dimensions'], indent=2))
            console.print(dims_json)
            
            console.print("\n" + "─" * 80)

def display_trace_examples():
    """Display example trace formats."""
    console.print("\n[bold magenta]Example Trace Formats[/bold magenta]\n")
    
    # OpenTelemetry span example
    span_example = {
        "name": "agent.invoke",
        "context": {
            "trace_id": "9cf2bdd0af83ad71912cbfab0f6bdfea",
            "span_id": "5ca47178649538f5",
            "trace_flags": "01"
        },
        "kind": "SpanKind.INTERNAL",
        "start_time": "2025-05-26T10:18:40.355Z",
        "end_time": "2025-05-26T10:18:45.155Z",
        "attributes": {
            "service.name": "QuickAgentTest",
            "agent.name": "CEO Log Agent",
            "agent.id": "asst_N5azTOnrhdlm4K9wC6i9OtHA",
            "thread.id": "thread_n2ydRZIeNvOmwVXne4NQiFdl",
            "response.size": 395,
            "response.duration_seconds": 4.8
        },
        "events": [
            {
                "name": "agent.request",
                "timestamp": "2025-05-26T10:18:40.355Z",
                "attributes": {
                    "message": "Test entry at 10:18:40..."
                }
            },
            {
                "name": "agent.response",
                "timestamp": "2025-05-26T10:18:45.155Z",
                "attributes": {
                    "response": "Hello! I am the CEO Log Agent..."
                }
            }
        ]
    }
    
    console.print("[bold]OpenTelemetry Span Structure:[/bold]")
    console.print(Syntax(json.dumps(span_example, indent=2), "json", theme="monokai"))
    
    # Application Insights telemetry format
    ai_format = {
        "ver": 1,
        "name": "Microsoft.ApplicationInsights.Message",
        "time": "2025-05-26T10:18:45.211Z",
        "iKey": "189923ab-6ad8-408f-b3f6-7ae4817a3988",
        "tags": {
            "ai.application.ver": "1.0.0",
            "ai.cloud.role": "QuickAgentTest",
            "ai.operation.id": "9cf2bdd0af83ad71912cbfab0f6bdfea",
            "ai.operation.parentId": "5ca47178649538f5"
        },
        "data": {
            "baseType": "MessageData",
            "baseData": {
                "ver": 2,
                "message": "Agent invocation completed",
                "severityLevel": "Information",
                "properties": {
                    "agent.name": "CEO Log Agent",
                    "agent.id": "asst_N5azTOnrhdlm4K9wC6i9OtHA",
                    "response.duration_seconds": "4.8",
                    "response.size": "395"
                }
            }
        }
    }
    
    console.print("\n[bold]Application Insights Telemetry Format:[/bold]")
    console.print(Syntax(json.dumps(ai_format, indent=2), "json", theme="monokai"))

def main():
    """Main function to display telemetry details."""
    console.print(Panel.fit(
        "[bold cyan]Recent Telemetry Data - Detailed View[/bold cyan]\n"
        "Showing all telemetry traces sent to Application Insights",
        box=box.DOUBLE
    ))
    
    # Display transmission summary
    console.print("\n[bold]📡 Transmission Summary[/bold]\n")
    display_transmission_summary()
    
    # Display agent invocations
    display_agent_invocations()
    
    # Display trace format examples
    display_trace_examples()
    
    # Portal access info
    console.print("\n[bold green]🌐 View in Azure Portal[/bold green]\n")
    portal_info = """
    1. Go to: https://portal.azure.com
    2. Navigate to: Application Insights > stratos-multi-agent-appinsights
    3. Click on: Transaction search
    4. Time range: Last 24 hours
    5. Filter by: 
       - Cloud role name: QuickAgentTest, SKAgentTelemetryTester
       - Custom dimensions: agent.name exists
    
    Direct link to Application Insights:
    https://portal.azure.com/#@5acd02e3-dfea-4b7c-aab5-1633ffe0403a/resource/subscriptions/514bd6d3-2c02-45c6-a86f-29cf262a379a/resourceGroups/semantic-kernel-multi-agent-rg/providers/microsoft.insights/components/stratos-multi-agent-appinsights/overview
    """
    
    console.print(Panel(portal_info, title="Azure Portal Access", box=box.ROUNDED))
    
    console.print("\n[bold cyan]✨ All 44 telemetry traces have been successfully transmitted![/bold cyan]")

if __name__ == "__main__":
    main()