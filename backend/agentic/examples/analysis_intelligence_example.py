"""
Example usage of the Analysis & Intelligence System agents
"""

import asyncio
import json
from agents.analysis_intelligence import (
    AnalysisOrchestrator,
    SwotTowsAgent,
    RiskOpportunityAgent,
    SOLinkageAgent
)


async def example_analysis_routing():
    """Example of using the Analysis Orchestrator to route requests"""
    
    print("\n=== Analysis & Intelligence System Example ===\n")
    
    # Initialize the orchestrator
    orchestrator = AnalysisOrchestrator()
    
    # Example 1: SWOT Analysis Request
    print("1. SWOT Analysis Request:")
    swot_request = {
        "query": "Generate a SWOT analysis for our new product launch based on recent market data and team feedback",
        "context": {
            "data_sources": {
                "subjective": {
                    "team_feedback": "Team is excited but concerned about timeline",
                    "ceo_notes": "Market timing is critical, competitors are moving fast"
                },
                "objective": {
                    "market_size": "$2.5B and growing 15% annually",
                    "competitor_count": "3 major players, 2 preparing launches",
                    "team_capacity": "85% utilized, some key skills gaps"
                }
            },
            "topic": "New Product Launch - Q3 2025"
        },
        "user_id": "user123"
    }
    
    result = await orchestrator.process(swot_request)
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Example 2: Risk Detection Request
    print("\n2. Risk Detection Request:")
    risk_request = {
        "query": "Identify key risks in our current strategy based on market trends and internal metrics",
        "context": {
            "category": "strategic",
            "time_horizon": "short_term",
            "data_sources": {
                "market_trends": "Shift to subscription models accelerating",
                "internal_metrics": "Customer acquisition cost up 30%, churn rate stable"
            }
        },
        "user_id": "user123"
    }
    
    result = await orchestrator.process(risk_request)
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Example 3: S+O Linkage Discovery
    print("\n3. Subjective-Objective Linkage Request:")
    linkage_request = {
        "query": "Find connections between CEO observations about team morale and our productivity metrics",
        "context": {
            "subjective_data": {
                "ceo_logs": [
                    "Team seems energized after all-hands meeting",
                    "Noticed more collaboration in engineering",
                    "Some burnout signs in customer success"
                ]
            },
            "objective_data": {
                "productivity": {
                    "engineering_velocity": "Up 15% this sprint",
                    "support_ticket_resolution": "Down 10% this week",
                    "deployment_frequency": "Increased 2x"
                }
            }
        },
        "user_id": "user123"
    }
    
    result = await orchestrator.process(linkage_request)
    print(f"Result: {json.dumps(result, indent=2)}")


async def example_direct_agent_usage():
    """Example of using agents directly without routing"""
    
    print("\n\n=== Direct Agent Usage Examples ===\n")
    
    # Example 1: Direct SWOT/TOWS Agent
    print("1. Direct SWOT/TOWS Agent - Guided Session:")
    swot_agent = SwotTowsAgent()
    
    session_request = {
        "query": "Start a guided SWOT analysis session for our digital transformation initiative",
        "context": {
            "session_type": "swot",
            "focus_area": "digital transformation"
        },
        "user_id": "user123"
    }
    
    result = await swot_agent.process(session_request)
    print(f"Session Started: {json.dumps(result, indent=2)}")
    
    # Example 2: Direct Risk/Opportunity Agent
    print("\n2. Direct Risk/Opportunity Agent - Alert Generation:")
    risk_agent = RiskOpportunityAgent()
    
    alert_request = {
        "query": "Generate alerts for critical risks detected in the last 24 hours",
        "context": {
            "window": "24h",
            "types": ["risk", "opportunity"]
        },
        "user_id": "user123"
    }
    
    result = await risk_agent.process(alert_request)
    print(f"Alerts: {json.dumps(result, indent=2)}")
    
    # Example 3: Direct S+O Linkage Agent
    print("\n3. Direct S+O Linkage Agent - Theme Tracking:")
    linkage_agent = SOLinkageAgent()
    
    theme_request = {
        "query": "Track emerging themes across our subjective and objective data",
        "context": {
            "time_period": "30d",
            "categories": ["strategic", "operational", "customer"],
            "min_occurrences": 3
        },
        "user_id": "user123"
    }
    
    result = await linkage_agent.process(theme_request)
    print(f"Themes: {json.dumps(result, indent=2)}")


async def example_complex_analysis_workflow():
    """Example of a complex multi-agent analysis workflow"""
    
    print("\n\n=== Complex Analysis Workflow Example ===\n")
    
    orchestrator = AnalysisOrchestrator()
    
    # Step 1: Generate SWOT Analysis
    print("Step 1: Generating SWOT Analysis...")
    swot_request = {
        "query": "Generate comprehensive SWOT analysis for Q3 planning",
        "context": {
            "data_sources": {
                "subjective": {"source": "Leadership team input and market observations"},
                "objective": {"source": "Q2 performance metrics and market data"}
            }
        },
        "user_id": "user123"
    }
    
    swot_result = await orchestrator.process(swot_request)
    
    # Step 2: Detect Risks from SWOT Weaknesses and Threats
    print("\nStep 2: Detecting Risks from SWOT...")
    risk_request = {
        "query": "Identify and assess risks based on the SWOT analysis weaknesses and threats",
        "context": {
            "swot_data": swot_result.get("data", {}),
            "category": "all",
            "time_horizon": "medium_term"
        },
        "user_id": "user123"
    }
    
    risk_result = await orchestrator.process(risk_request)
    
    # Step 3: Find S+O Linkages for Validation
    print("\nStep 3: Validating with S+O Linkages...")
    validation_request = {
        "query": "Validate our top risks and opportunities by finding supporting connections in our data",
        "context": {
            "risks": risk_result.get("data", {}).get("risks", [])[:3],
            "opportunities": swot_result.get("data", {}).get("items", []),
            "validation_focus": "high_priority_items"
        },
        "user_id": "user123"
    }
    
    validation_result = await orchestrator.process(validation_request)
    
    # Summary
    print("\n=== Workflow Summary ===")
    print(f"SWOT Items Generated: {swot_result.get('data', {}).get('summary', {})}")
    print(f"Risks Identified: {risk_result.get('data', {}).get('summary', {})}")
    print(f"Linkages Found: {validation_result.get('data', {}).get('summary', {})}")
    
    return {
        "swot": swot_result,
        "risks": risk_result,
        "validation": validation_result
    }


async def main():
    """Run all examples"""
    
    # Run routing examples
    await example_analysis_routing()
    
    # Run direct agent examples
    await example_direct_agent_usage()
    
    # Run complex workflow
    workflow_result = await example_complex_analysis_workflow()
    
    print("\n\n=== All Examples Completed ===")
    print("\nThe Analysis & Intelligence System provides:")
    print("1. SWOT/TOWS analysis and strategy generation")
    print("2. Risk and opportunity detection with alerts")
    print("3. Subjective-Objective linkage discovery")
    print("4. Guided analysis sessions")
    print("5. Pattern recognition and theme tracking")
    print("\nUse the orchestrator for automatic routing or agents directly for specific tasks.")


if __name__ == "__main__":
    asyncio.run(main())