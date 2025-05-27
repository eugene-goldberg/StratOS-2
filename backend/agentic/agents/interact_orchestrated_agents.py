#!/usr/bin/env python3
"""
Interact with orchestrated agents where the main agent can delegate to weather agent.
"""

import os
import sys
import json
import time
from openai import AzureOpenAI
from dotenv import load_dotenv

# Add the project root to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, project_root)

from src.config.settings import (
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_API_KEY
)
from src.services.weather_service import WeatherService

class OrchestrationClient:
    """Client for interacting with orchestrated agents"""
    
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Try to load from .env.deploy if it exists, but don't fail if it doesn't
        try:
            if os.path.exists(".env.deploy"):
                with open(".env.deploy", "r") as f:
                    for line in f:
                        if line.strip() and not line.startswith("#"):
                            key, value = line.strip().split("=", 1)
                            os.environ[key] = value
        except Exception as e:
            print(f"Note: Could not load .env.deploy: {str(e)}. Using environment variables instead.")
        
        # Check required variables
        if not all([AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY]):
            raise ValueError("Missing required environment variables for Azure OpenAI")
        
        # Initialize OpenAI client
        self.client = AzureOpenAI(
            azure_endpoint=AZURE_OPENAI_ENDPOINT,
            api_key=AZURE_OPENAI_API_KEY,
            api_version="2024-02-15-preview"  # Use version that works with Azure
        )
        
        # Initialize weather service for function calls
        self.weather_service = WeatherService()
        
        # Load agent IDs
        self.agents = self.load_deployed_agents()
        self.current_thread_id = None
        
        # Print API info
        print(f"Connected to Azure OpenAI at: {AZURE_OPENAI_ENDPOINT}")
    
    def load_deployed_agents(self):
        """Load deployed agent IDs from file"""
        try:
            with open("orchestration_deployment_info.json", "r") as f:
                deployment_info = json.load(f)
            
            agents = {
                "orchestrator": deployment_info.get("orchestrator_agent_id"),
                "weather": deployment_info.get("weather_agent_id")
            }
            
            print(f"Loaded agents: Orchestrator={agents['orchestrator']}, Weather={agents['weather']}")
            return agents
        except Exception as e:
            print(f"Error loading agents: {str(e)}")
            return {"orchestrator": None, "weather": None}
    
    def list_available_assistants(self):
        """List all available assistants"""
        try:
            assistants = self.client.beta.assistants.list(limit=100)
            print(f"Found {len(assistants.data)} assistants:")
            
            for assistant in assistants.data:
                print(f"  - {assistant.name} (ID: {assistant.id})")
                
                # Update agents dictionary with matching assistants
                if assistant.name.lower() == "orchestratoragent":
                    self.agents["orchestrator"] = assistant.id
                elif assistant.name.lower() == "weatheragent":
                    self.agents["weather"] = assistant.id
            
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
    
    def handle_weather_tool_calls(self, tool_calls):
        """Handle weather function tool calls"""
        tool_outputs = []
        
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            if function_name == "get_weather":
                location = function_args.get("location")
                weather_type = function_args.get("type", "current")
                
                try:
                    print(f"\nDelegating to Weather Agent: get_weather({location}, {weather_type})")
                    # Call weather agent with a new thread
                    weather_thread = self.client.beta.threads.create()
                    
                    # Add message to weather thread
                    weather_prompt = f"What's the {weather_type} weather in {location}?"
                    self.client.beta.threads.messages.create(
                        thread_id=weather_thread.id,
                        role="user",
                        content=weather_prompt
                    )
                    
                    # Run the weather agent
                    weather_run = self.client.beta.threads.runs.create(
                        thread_id=weather_thread.id,
                        assistant_id=self.agents["weather"]
                    )
                    
                    # Wait for completion
                    while True:
                        weather_status = self.client.beta.threads.runs.retrieve(
                            thread_id=weather_thread.id,
                            run_id=weather_run.id
                        )
                        
                        if weather_status.status in ["completed", "failed", "cancelled", "expired"]:
                            break
                        
                        print(f"Weather agent run status: {weather_status.status}, waiting...")
                        time.sleep(1)
                    
                    if weather_status.status == "completed":
                        # Get messages
                        weather_messages = self.client.beta.threads.messages.list(
                            thread_id=weather_thread.id
                        )
                        
                        # Find the assistant's response
                        for message in weather_messages.data:
                            if message.role == "assistant":
                                weather_result = message.content[0].text.value
                                print(f"Weather Agent Response: {weather_result}")
                                
                                # Add to tool outputs
                                tool_outputs.append({
                                    "tool_call_id": tool_call.id,
                                    "output": weather_result
                                })
                                break
                    else:
                        error_message = f"Weather agent run failed with status: {weather_status.status}"
                        print(error_message)
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": error_message
                        })
                        
                except Exception as e:
                    error_message = f"Error processing weather request: {str(e)}"
                    print(error_message)
                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "output": error_message
                    })
            else:
                tool_outputs.append({
                    "tool_call_id": tool_call.id,
                    "output": f"Unknown function: {function_name}"
                })
        
        return tool_outputs
    
    def send_message(self, message_text):
        """Send a message to the orchestrator agent"""
        if not self.current_thread_id:
            print("No active thread. Creating one...")
            if not self.create_thread():
                return False
        
        if not self.agents["orchestrator"]:
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
                    print(f"Run requires action. Processing {len(tool_calls)} tool calls...")
                    
                    # Process tool calls
                    tool_outputs = self.handle_weather_tool_calls(tool_calls)
                    
                    # Submit tool outputs
                    self.client.beta.threads.runs.submit_tool_outputs(
                        thread_id=self.current_thread_id,
                        run_id=run.id,
                        tool_outputs=tool_outputs
                    )
                elif run_status.status in ["completed", "failed", "cancelled", "expired"]:
                    break
                
                print(f"Run status: {run_status.status}, waiting...")
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
                print(f"\nOrchestrator: {content}")
                return True
            else:
                print("No response from orchestrator found.")
                return False
                
        except Exception as e:
            print(f"Error sending message: {str(e)}")
            return False
    
    def interactive_chat(self):
        """Start an interactive chat session"""
        print(f"Starting interactive chat with orchestrated agents...")
        print("Type 'exit' to quit or 'clear' to start a new thread.")
        
        while True:
            try:
                user_input = input("\nYou: ")
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
            
            self.send_message(user_input)

def main():
    """Main entry point"""
    try:
        client = OrchestrationClient()
        
        # First try to load from deployment info
        if None in client.agents.values():
            # If that fails, try to discover agents
            if not client.list_available_assistants():
                print("No assistants found. Please deploy orchestrated assistants first.")
                return
        
        # Create initial thread
        client.create_thread()
        
        # Start interactive chat
        client.interactive_chat()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()