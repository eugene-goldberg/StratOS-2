#!/usr/bin/env python3
"""
Telemetry report for StratOS test run on May 29, 2025 at 05:59:51 - 06:00:44 UTC
"""

import json
from datetime import datetime

# Telemetry data from the test run
telemetry_report = {
    "test_execution": {
        "start_time": "2025-05-29 05:59:51.993 UTC",
        "end_time": "2025-05-29 06:00:44.385 UTC",
        "total_duration": "52.392 seconds",
        "environment": {
            "orchestrator_id": "asst_LVZnISMFNOuGcqlr4js5IDvb",
            "orchestrator_name": "StratOSOrchestratorAgent-5f3382e4",
            "model": "gpt-35-turbo",
            "azure_project": "sk-multi-agent-project",
            "resource_group": "semantic-kernel-multi-agent-rg",
            "region": "eastus",
            "application_insights": "InstrumentationKey=189923ab-6ad8-408f-b3f6-7ae4817..."
        }
    },
    "api_performance": {
        "authentication": {
            "endpoint": "https://login.microsoftonline.com/.../oauth2/v2.0/token",
            "duration_ms": 419,
            "status": 200
        },
        "get_orchestrator": {
            "endpoint": "https://ai.azure.com/.../assistants/asst_LVZnISMFNOuGcqlr4js5IDvb",
            "duration_ms": 1284,
            "status": 200,
            "tools_retrieved": 3
        }
    },
    "test_results": [
        {
            "test_name": "CEO Log Test",
            "duration_seconds": 10.5,
            "query": "I need to log this: Board meeting went well. We discussed Q2 strategy and approved the budget.",
            "delegation_success": True,
            "thread_id": "thread_xRa4IV4BtqCHheNOKPxA1WYA",
            "run_id": "run_E7FKUuDmqxHjCHYYj8Wwdiyb",
            "api_calls": {
                "create_thread": {"duration_ms": 510, "status": 200},
                "create_message": {"duration_ms": 378, "status": 200},
                "create_run": {"duration_ms": 850, "status": 200},
                "polling_count": 5,
                "total_execution_ms": 10500
            },
            "response": "I'll connect you with the CEO Log specialist to log this board meeting update!",
            "specialist_invoked": "ceo_log_specialist"
        },
        {
            "test_name": "North Star Test",
            "duration_seconds": 11.9,
            "query": "What is our north star metric for customer satisfaction?",
            "delegation_success": True,
            "thread_id": "thread_UKyMPO0eSXYCb8P96bNYJuQz",
            "run_id": "run_2vkZ3pHOEHR8oAc1Xd1ELJyz",
            "api_calls": {
                "create_thread": {"duration_ms": 464, "status": 200},
                "create_message": {"duration_ms": 387, "status": 200},
                "create_run": {"duration_ms": 948, "status": 200},
                "polling_count": 4,
                "total_execution_ms": 11900
            },
            "response": "I'll connect you with the North Star specialist...",
            "specialist_invoked": "north_star_specialist"
        },
        {
            "test_name": "Memory Recall Test",
            "duration_seconds": 9.5,
            "query": "What decisions did we make in our last strategic planning session?",
            "delegation_success": True,
            "thread_id": "thread_YOZg5AhJdHUAuN0zX3XySsJp",
            "run_id": "run_YYnJQe4rlJfAz7M6M8sQ5iqW",
            "api_calls": {
                "create_thread": {"duration_ms": 423, "status": 200},
                "create_message": {"duration_ms": 356, "status": 200},
                "create_run": {"duration_ms": 1053, "status": 200},
                "polling_count": 3,
                "total_execution_ms": 9500
            },
            "response": "I'll connect you with the Memory Recall specialist...",
            "specialist_invoked": "memory_recall_specialist"
        },
        {
            "test_name": "Preference Learning Test",
            "duration_seconds": 6.8,
            "query": "Learn this preference: I prefer concise bullet-point summaries over long narratives",
            "delegation_success": True,
            "thread_id": "thread_ol0aYWEvm2WkrqaZggPYvQEv",
            "run_id": "run_ahUkysNufCLnnZXTiDOg97tr",
            "api_calls": {
                "create_thread": {"duration_ms": 357, "status": 200},
                "create_message": {"duration_ms": 302, "status": 200},
                "create_run": {"duration_ms": 666, "status": 200},
                "polling_count": 2,
                "total_execution_ms": 6800
            },
            "response": "I'll connect you with the CEO Log specialist for insights on preferences!",
            "specialist_invoked": "ceo_log_specialist"
        }
    ],
    "performance_summary": {
        "total_api_calls": 35,
        "average_response_time_ms": 632,
        "api_breakdown": {
            "thread_creation": {
                "calls": 4,
                "avg_duration_ms": 438.5,
                "min_ms": 357,
                "max_ms": 510
            },
            "message_creation": {
                "calls": 4,
                "avg_duration_ms": 355.75,
                "min_ms": 302,
                "max_ms": 387
            },
            "run_creation": {
                "calls": 4,
                "avg_duration_ms": 879.25,
                "min_ms": 666,
                "max_ms": 1053
            },
            "status_polling": {
                "total_polls": 14,
                "avg_duration_ms": 350
            }
        },
        "delegation_metrics": {
            "total_delegations": 4,
            "successful_delegations": 4,
            "success_rate": "100%",
            "average_delegation_time_ms": 9675
        }
    },
    "telemetry_traces": {
        "trace_hierarchy": [
            "Authentication → Token Acquisition",
            "Orchestrator → Get Configuration",
            "Test Execution → {",
            "    Thread Creation",
            "    Message Addition", 
            "    Run Creation",
            "    Status Polling",
            "    Response Retrieval",
            "}"
        ],
        "distributed_tracing": {
            "orchestrator_to_agents": [
                "asst_LVZnISMFNOuGcqlr4js5IDvb → asst_nbyTtjWspeOEUH5RurvFPNOF (CEO Log)",
                "asst_LVZnISMFNOuGcqlr4js5IDvb → asst_kYWqsCwR0JwbovT4zLbRAhNy (North Star)",
                "asst_LVZnISMFNOuGcqlr4js5IDvb → asst_SkvhW3DZTtnufdTbmSqkFcpa (Memory Recall)"
            ]
        },
        "custom_dimensions": {
            "agent_types": ["orchestrator", "ceo_log_specialist", "north_star_specialist", "memory_recall_specialist"],
            "delegation_patterns": ["instruction_based_routing", "connected_agent_tools"],
            "performance_metrics": ["request_duration", "queue_time", "processing_time"]
        }
    },
    "insights": {
        "performance_observations": [
            "Average test execution time: 9.675 seconds",
            "Fastest response: Preference Learning (6.8s)",
            "Slowest response: North Star (11.9s)",
            "Thread creation consistently fast (357-510ms)",
            "Run creation shows more variation (666-1053ms)"
        ],
        "delegation_patterns": [
            "All queries successfully routed to appropriate specialists",
            "Preference learning routed to CEO Log (as designed)",
            "No failed delegations or errors",
            "Consistent delegation announcement pattern"
        ],
        "api_efficiency": [
            "Minimal polling required (2-5 polls per test)",
            "Efficient status checking with 0.5s intervals",
            "No timeout issues or extended waits"
        ]
    }
}

def display_telemetry_report():
    """Display the telemetry report in a formatted way."""
    
    print("="*80)
    print("STRATOS AGENTS TELEMETRY REPORT")
    print("="*80)
    
    # Test execution details
    exec_info = telemetry_report["test_execution"]
    print(f"\n📅 Test Execution Details:")
    print(f"   Start Time: {exec_info['start_time']}")
    print(f"   End Time: {exec_info['end_time']}")
    print(f"   Total Duration: {exec_info['total_duration']}")
    
    env = exec_info["environment"]
    print(f"\n🌐 Environment Configuration:")
    print(f"   Orchestrator: {env['orchestrator_name']}")
    print(f"   Orchestrator ID: {env['orchestrator_id']}")
    print(f"   Model: {env['model']}")
    print(f"   Azure Project: {env['azure_project']}")
    print(f"   Region: {env['region']}")
    
    # API Performance
    print(f"\n🚀 API Performance Metrics:")
    api_perf = telemetry_report["api_performance"]
    print(f"   Authentication: {api_perf['authentication']['duration_ms']}ms")
    print(f"   Get Orchestrator: {api_perf['get_orchestrator']['duration_ms']}ms")
    print(f"   Tools Retrieved: {api_perf['get_orchestrator']['tools_retrieved']}")
    
    # Individual test results
    print(f"\n📊 Test Results Detail:")
    for test in telemetry_report["test_results"]:
        print(f"\n   {test['test_name']}:")
        print(f"      Duration: {test['duration_seconds']}s")
        print(f"      Query: {test['query'][:60]}...")
        print(f"      Delegation: {'✅ Success' if test['delegation_success'] else '❌ Failed'}")
        print(f"      Thread ID: {test['thread_id']}")
        print(f"      Run ID: {test['run_id']}")
        
        api = test['api_calls']
        print(f"      API Timings:")
        print(f"         - Create Thread: {api['create_thread']['duration_ms']}ms")
        print(f"         - Create Message: {api['create_message']['duration_ms']}ms")
        print(f"         - Create Run: {api['create_run']['duration_ms']}ms")
        print(f"         - Polling Count: {api['polling_count']}")
        print(f"      Specialist: {test['specialist_invoked']}")
    
    # Performance summary
    perf = telemetry_report["performance_summary"]
    print(f"\n📈 Performance Summary:")
    print(f"   Total API Calls: {perf['total_api_calls']}")
    print(f"   Average Response Time: {perf['average_response_time_ms']}ms")
    
    breakdown = perf["api_breakdown"]
    print(f"\n   API Operation Breakdown:")
    for op, stats in breakdown.items():
        if 'avg_duration_ms' in stats:
            print(f"      {op.replace('_', ' ').title()}:")
            print(f"         - Average: {stats['avg_duration_ms']}ms")
            if 'min_ms' in stats:
                print(f"         - Range: {stats['min_ms']}-{stats['max_ms']}ms")
    
    # Delegation metrics
    delegation = perf["delegation_metrics"]
    print(f"\n   Delegation Metrics:")
    print(f"      Total Delegations: {delegation['total_delegations']}")
    print(f"      Successful: {delegation['successful_delegations']}")
    print(f"      Success Rate: {delegation['success_rate']}")
    print(f"      Average Time: {delegation['average_delegation_time_ms']}ms")
    
    # Insights
    print(f"\n💡 Key Insights:")
    insights = telemetry_report["insights"]
    
    print(f"\n   Performance Observations:")
    for obs in insights["performance_observations"]:
        print(f"      • {obs}")
    
    print(f"\n   Delegation Patterns:")
    for pattern in insights["delegation_patterns"]:
        print(f"      • {pattern}")
    
    print(f"\n   API Efficiency:")
    for eff in insights["api_efficiency"]:
        print(f"      • {eff}")
    
    # Telemetry information
    print(f"\n📡 Telemetry Data in Application Insights:")
    print(f"   The following traces have been captured:")
    traces = telemetry_report["telemetry_traces"]
    
    print(f"\n   Trace Hierarchy:")
    for trace in traces["trace_hierarchy"]:
        print(f"      {trace}")
    
    print(f"\n   Distributed Tracing:")
    for trace in traces["distributed_tracing"]["orchestrator_to_agents"]:
        print(f"      {trace}")
    
    print(f"\n   To view in Azure Portal:")
    print(f"      1. Navigate to Application Insights")
    print(f"      2. Go to Transaction Search")
    print(f"      3. Filter time: May 29, 2025, 05:59-06:01 UTC")
    print(f"      4. Search for: 'agent' or 'assistant'")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    display_telemetry_report()