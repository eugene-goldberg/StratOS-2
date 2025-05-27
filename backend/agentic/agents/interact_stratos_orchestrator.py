#!/usr/bin/env python3
"""
Interact with StratOS orchestrated agents where the main orchestrator routes to specialist agents.
"""

import os
import sys
import json
import time
from openai import AzureOpenAI
from dotenv import load_dotenv

# Add the project root to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
sys.path.insert(0, project_root)

class StratOSOrchestrationClient:
    """Client for interacting with StratOS orchestrated agents"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Get Azure OpenAI settings
        self.endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        
        # Check required variables
        if not all([self.endpoint, self.api_key]):
            raise ValueError("Missing required environment variables for Azure OpenAI")
        
        # Initialize OpenAI client
        self.client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version
        )
        
        # Load agent IDs
        self.agents = self.load_deployed_agents()
        self.current_thread_id = None
        
        # Print API info
        print(f"Connected to Azure OpenAI at: {self.endpoint}")
    
    def load_deployed_agents(self):
        """Load deployed agent IDs from file"""
        try:
            with open("stratos_deployment_info.json", "r") as f:
                deployment_info = json.load(f)
            
            agents = {
                "orchestrator": deployment_info.get("main_orchestrator_agent_id"),
                "ceo_log": deployment_info.get("ceo_log_agent_id"),
                "north_star": deployment_info.get("north_star_agent_id"),
                "memory_recall": deployment_info.get("memory_recall_agent_id"),
                "preference_learning": deployment_info.get("preference_learning_agent_id"),
                "swot_tows": deployment_info.get("swot_tows_agent_id"),
                "risk_opportunity": deployment_info.get("risk_opportunity_agent_id"),
                "so_linkage": deployment_info.get("so_linkage_agent_id"),
                "alignment_scoring": deployment_info.get("alignment_scoring_agent_id"),
                "initiative_generation": deployment_info.get("initiative_generation_agent_id"),
                "resource_optimization": deployment_info.get("resource_optimization_agent_id"),
                "action_planning": deployment_info.get("action_planning_agent_id"),
                "canvas_visualization": deployment_info.get("canvas_visualization_agent_id")
            }
            
            print(f"Loaded {len(agents)} StratOS agents")
            print(f"Main Orchestrator: {agents['orchestrator']}")
            return agents
        except Exception as e:
            print(f"Error loading agents: {str(e)}")
            return {}
    
    def list_available_assistants(self):
        """List all available assistants"""
        try:
            assistants = self.client.beta.assistants.list(limit=100)
            print(f"\nFound {len(assistants.data)} assistants:")
            
            for assistant in assistants.data:
                print(f"  - {assistant.name} (ID: {assistant.id})")
            
            return True
        except Exception as e:
            print(f"Error listing assistants: {str(e)}")
            return False
    
    def create_thread(self):
        """Create a new thread"""
        try:
            thread = self.client.beta.threads.create()
            self.current_thread_id = thread.id
            print(f"Created thread with ID: {self.current_thread_id}")
            return True
        except Exception as e:
            print(f"Error creating thread: {str(e)}")
            return False
    
    def handle_stratos_tool_calls(self, tool_calls):
        """Handle StratOS agent routing tool calls"""
        tool_outputs = []
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            query = function_args.get("query", "")
            
            # Map function names to agent IDs
            agent_mapping = {
                "RouteToCEOLogAgent": "ceo_log",
                "RouteToNorthStarAgent": "north_star",
                "RouteToMemoryRecallAgent": "memory_recall",
                "RouteToPreferenceLearningAgent": "preference_learning",
                "RouteToSWOTTOWSAgent": "swot_tows",
                "RouteToRiskOpportunityAgent": "risk_opportunity",
                "RouteToSOLinkageAgent": "so_linkage",
                "RouteToAlignmentScoringAgent": "alignment_scoring",
                "RouteToInitiativeGenerationAgent": "initiative_generation",
                "RouteToResourceOptimizationAgent": "resource_optimization",
                "RouteToActionPlanningAgent": "action_planning",
                "RouteToCanvasVisualizationAgent": "canvas_visualization"
            }
            
            agent_key = agent_mapping.get(function_name)
            
            if agent_key and agent_key in self.agents:
                try:
                    agent_id = self.agents[agent_key]
                    agent_name = function_name.replace("RouteTo", "").replace("Agent", " Agent")
                    print(f"\n🔄 Routing to {agent_name}: '{query}'")
                    
                    # Create a new thread for the specialist agent
                    specialist_thread = self.client.beta.threads.create()
                    
                    # Add message to specialist thread
                    self.client.beta.threads.messages.create(
                        thread_id=specialist_thread.id,
                        role="user",
                        content=query
                    )
                    
                    # Run the specialist agent
                    specialist_run = self.client.beta.threads.runs.create(
                        thread_id=specialist_thread.id,
                        assistant_id=agent_id
                    )
                    
                    # Wait for completion
                    while True:
                        run_status = self.client.beta.threads.runs.retrieve(
                            thread_id=specialist_thread.id,
                            run_id=specialist_run.id
                        )
                        
                        if run_status.status in ["completed", "failed", "cancelled", "expired"]:
                            break
                        
                        time.sleep(1)
                    
                    if run_status.status == "completed":
                        # Get messages
                        messages = self.client.beta.threads.messages.list(
                            thread_id=specialist_thread.id
                        )
                        
                        # Find the assistant's response
                        for message in messages.data:
                            if message.role == "assistant":
                                result = message.content[0].text.value
                                print(f"✅ {agent_name} Response received")
                                
                                # Add to tool outputs
                                tool_outputs.append({
                                    "tool_call_id": tool_call.id,
                                    "output": result
                                })
                                break
                    else:
                        error_message = f"Agent run failed with status: {run_status.status}"
                        print(f"❌ {error_message}")
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": error_message
                        })
                        
                except Exception as e:
                    error_message = f"Error processing request: {str(e)}"
                    print(f"❌ {error_message}")
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": error_message
                    })
            else:
                error_msg = f"Unknown function or missing agent: {function_name}"
                print(f"❌ {error_msg}")
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": error_msg
                })
        
        return tool_outputs
    
    def send_message(self, message_text):
        """Send a message to the orchestrator agent"""
        if not self.current_thread_id:
            print("No active thread. Creating one...")
            if not self.create_thread():
                return False
        
        if not self.agents.get("orchestrator"):
            print("No orchestrator agent found. Please check deployment.")
            return False
        
        try:
            # Add message to thread
            message = self.client.beta.threads.messages.create(
                thread_id=self.current_thread_id,
                role="user",
                content=message_text
            )
            
            # Run the assistant
            run = self.client.beta.threads.runs.create(
                thread_id=self.current_thread_id,
                assistant_id=self.agents["orchestrator"]
            )
            
            # Process the run, handling any required tool calls
            while True:
                run_status = self.client.beta.threads.runs.retrieve(
                    thread_id=self.current_thread_id,
                    run_id=run.id
                )
                
                if run_status.status == "requires_action":
                    # Handle tool calls
                    tool_calls = run_status.required_action.submit_tool_outputs.tool_calls
                    print(f"\n🎯 Orchestrator is routing to specialist agents...")
                    
                    # Process tool calls
                    tool_outputs = self.handle_stratos_tool_calls(tool_calls)
                    
                    # Submit tool outputs
                    self.client.beta.threads.runs.submit_tool_outputs(
                        thread_id=self.current_thread_id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )
                elif run_status.status in ["completed", "failed", "cancelled", "expired"]:
                    break
                
                time.sleep(1)
            
            if run_status.status != "completed":
                print(f"Run failed with status: {run_status.status}")
                return False
            
            # Get messages
            messages = self.client.beta.threads.messages.list(
                thread_id=self.current_thread_id
            )
            
            # Find the latest assistant message
            assistant_messages = [m for m in messages.data if m.role == "assistant"]
            
            if assistant_messages:
                latest_message = assistant_messages[0]  # First is most recent
                content = latest_message.content[0].text.value if latest_message.content else "No content"
                print(f"\n🤖 Orchestrator: {content}")
                return True
            else:
                print("No response from orchestrator found.")
                return False
                
        except Exception as e:
            print(f"Error sending message: {str(e)}")
            return False
    
    def interactive_chat(self):
        """Start an interactive chat session"""
        print("\n" + "="*60)
        print("🚀 StratOS Multi-Agent System")
        print("="*60)
        print("\nAvailable specialist agents:")
        print("- CEO Log Agent: Personal observations and insights")
        print("- North Star Agent: Vision, mission, and values")
        print("- Memory Recall Agent: Historical context and patterns")
        print("- Preference Learning Agent: Personalization")
        print("- SWOT/TOWS Agent: Strategic analysis")
        print("- Risk/Opportunity Agent: Risk and opportunity assessment")
        print("- SO Linkage Agent: Subjective-objective linking")
        print("- Alignment Scoring Agent: Strategic alignment")
        print("- Initiative Generation Agent: Strategic initiatives")
        print("- Resource Optimization Agent: Resource management")
        print("- Action Planning Agent: Task planning and tracking")
        print("- Canvas Visualization Agent: Visual planning")
        print("\nType 'exit' to quit or 'clear' to start a new thread.")
        print("="*60)
        
        while True:
            try:
                user_input = input("\n💬 You: ")
            except (KeyboardInterrupt, EOFError):
                print("\nExiting chat...")
                break
            
            if user_input.lower() == "exit":
                print("Exiting chat...")
                break
            elif user_input.lower() == "clear":
                if self.create_thread():
                    print("Started a new conversation thread.")
                continue
            elif user_input.lower() == "help":
                print("\nExample queries:")
                print("- 'I noticed our customer satisfaction scores are dropping'")
                print("- 'What is our company vision?'")
                print("- 'Analyze our market position with SWOT'")
                print("- 'Create an initiative to improve customer experience'")
                print("- 'What resources do we need for Q2 projects?'")
                continue
            
            self.send_message(user_input)

def main():
    """Main entry point"""
    try:
        client = StratOSOrchestrationClient()
        
        # Check if agents are loaded
        if not client.agents:
            print("No agents found. Please deploy StratOS agents first using deploy_stratos_agents.py")
            return
        
        # Create initial thread
        client.create_thread()
        
        # Start interactive chat
        client.interactive_chat()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()