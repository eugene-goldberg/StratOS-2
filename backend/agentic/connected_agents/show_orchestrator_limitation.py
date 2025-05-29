"""Demonstrate the orchestrator limitation - it only shows delegation announcements, not actual responses"""

import asyncio
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential
from datetime import datetime
import json

# Environment configuration
subscription_id = "fce3ed09-9636-4ead-b7f0-53581559f0ee"
resource_group_name = "rg-multi-agent"
ai_project_name = "ai-project-multi-agent"
ai_foundry_endpoint = "https://aistudiousecentral123.api.azureml.ms"

async def demonstrate_limitation():
    """Show that orchestrator only returns delegation announcements"""
    
    credential = DefaultAzureCredential()
    
    # Create AI Project client
    project_client = AIProjectClient(
        subscription_id=subscription_id,
        resource_group_name=resource_group_name,
        ai_foundry_project_name=ai_project_name,
        endpoint=ai_foundry_endpoint,
        credential=credential
    )
    
    # Get the orchestrator
    orchestrator_id = "asst_DvAoA85m6eCsWdOT2bsTxE6i"
    orchestrator_agent = await project_client.agents.get_agent(orchestrator_id)
    
    print("="*80)
    print("DEMONSTRATING ORCHESTRATOR LIMITATION")
    print("="*80)
    print("\nThis shows that the orchestrator only returns delegation announcements,")
    print("not the actual responses from the specialized agents.\n")
    
    # Test queries
    test_queries = [
        {
            "name": "CEO Log Request",
            "query": "Log our Q4 board meeting: Revenue exceeded targets by 15%, approved new R&D budget"
        },
        {
            "name": "North Star Query",
            "query": "What are our current strategic goals?"
        },
        {
            "name": "Memory Recall",
            "query": "What decisions were made in the last board meeting?"
        }
    ]
    
    results = []
    
    for test in test_queries:
        print(f"\n{'='*60}")
        print(f"Test: {test['name']}")
        print(f"Query: {test['query']}")
        print("-"*60)
        
        try:
            # Invoke orchestrator
            response = ""
            response_parts = []
            
            async for part in orchestrator_agent.invoke(messages=test['query']):
                if hasattr(part, 'content') and part.content:
                    response += str(part.content)
                    response_parts.append(str(part.content))
            
            print("\nOrchestrator Response:")
            print(response)
            
            # Analyze response
            has_delegation = "I'll connect you with" in response
            has_specialist_response = any(keyword in response.lower() for keyword in [
                "logged", "recorded", "stored", "goals are", "objectives include", 
                "decisions included", "our strategy", "here's what"
            ])
            
            print(f"\nAnalysis:")
            print(f"✓ Contains delegation announcement: {'Yes' if has_delegation else 'No'}")
            print(f"✓ Contains actual specialist response: {'Yes' if has_specialist_response else 'No'}")
            print(f"✓ Response length: {len(response)} characters")
            
            results.append({
                "test": test['name'],
                "query": test['query'],
                "response": response,
                "has_delegation": has_delegation,
                "has_specialist_response": has_specialist_response,
                "response_length": len(response)
            })
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            results.append({
                "test": test['name'],
                "error": str(e)
            })
    
    # Summary
    print("\n\n" + "="*80)
    print("SUMMARY - ORCHESTRATOR LIMITATION")
    print("="*80)
    
    successful_tests = [r for r in results if 'error' not in r]
    delegation_only_responses = [r for r in successful_tests if r['has_delegation'] and not r['has_specialist_response']]
    
    print(f"\nTotal tests: {len(test_queries)}")
    print(f"Successful: {len(successful_tests)}")
    print(f"Delegation-only responses: {len(delegation_only_responses)}")
    
    if delegation_only_responses:
        print("\n⚠️  LIMITATION CONFIRMED:")
        print(f"  {len(delegation_only_responses)}/{len(successful_tests)} responses contain ONLY delegation announcements")
        print("  The orchestrator is NOT showing the actual responses from specialized agents")
        
    print("\n📝 What this means:")
    print("  1. The orchestrator correctly routes to specialized agents")
    print("  2. The specialized agents process the requests")
    print("  3. BUT the orchestrator doesn't include their responses in its output")
    print("  4. Users only see 'I'll connect you with...' but not the actual answer")
    
    print("\n🔧 Solutions:")
    print("  1. Modify orchestrator instructions to explicitly include tool results")
    print("  2. Use thread-based API to capture complete conversation")
    print("  3. Invoke agents directly to bypass orchestrator limitation")
    print("  4. Build custom response aggregation on top of orchestrator")
    
    # Save report
    report = {
        "demonstration_time": datetime.now().isoformat(),
        "limitation": "Orchestrator returns only delegation announcements, not agent responses",
        "test_results": results,
        "statistics": {
            "total_tests": len(test_queries),
            "delegation_only": len(delegation_only_responses),
            "percentage": f"{len(delegation_only_responses)/len(successful_tests)*100:.0f}%" if successful_tests else "N/A"
        }
    }
    
    filename = f"orchestrator_limitation_demo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved to: {filename}")
    
    await credential.close()
    await project_client.close()

if __name__ == "__main__":
    asyncio.run(demonstrate_limitation())