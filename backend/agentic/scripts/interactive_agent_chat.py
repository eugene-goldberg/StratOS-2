#!/usr/bin/env python3
"""
Interactive CLI for chatting with deployed StratOS agents.
"""

import os
import sys
import asyncio
import json
from typing import Optional, Dict, Any
from datetime import datetime
import argparse
from colorama import init, Fore, Style

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.agent_interaction_client import StratosAgentClient

# Initialize colorama for cross-platform colored output
init()

class InteractiveAgentChat:
    """Interactive chat interface for StratOS agents."""
    
    def __init__(self):
        self.client = StratosAgentClient()
        self.current_agent = None
        self.current_thread_id = None
        self.conversation_history = []
        
    def print_header(self):
        """Print the application header."""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.CYAN}StratOS Agent Chat Interface")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}\n")
        
    def print_help(self):
        """Print help information."""
        print(f"\n{Fore.YELLOW}Available commands:")
        print(f"  /agents    - List all available agents")
        print(f"  /use <name> - Switch to a specific agent")
        print(f"  /system <name> - Use a system router (strategic/analysis/planning)")
        print(f"  /info      - Show current agent information")
        print(f"  /history   - Show conversation history")
        print(f"  /new       - Start a new conversation thread")
        print(f"  /save      - Save conversation to file")
        print(f"  /help      - Show this help message")
        print(f"  /quit      - Exit the application{Style.RESET_ALL}\n")
        
    async def list_agents(self):
        """List all available agents."""
        agents = await self.client.list_agents()
        
        # Group agents by system
        systems = {
            "Strategic Foundation": [],
            "Analysis & Intelligence": [],
            "Planning & Execution": []
        }
        
        for agent in agents:
            if agent in ["StrategicContextRouter", "CEOLogAgent", "NorthStarAgent", 
                        "MemoryRecallAgent", "PreferenceLearningAgent"]:
                systems["Strategic Foundation"].append(agent)
            elif agent in ["AnalysisOrchestrator", "SWOTTOWSAgent", 
                          "RiskOpportunityAgent", "SOLinkageAgent"]:
                systems["Analysis & Intelligence"].append(agent)
            else:
                systems["Planning & Execution"].append(agent)
        
        print(f"\n{Fore.GREEN}Available Agents:{Style.RESET_ALL}")
        for system, agent_list in systems.items():
            print(f"\n{Fore.CYAN}{system}:{Style.RESET_ALL}")
            for agent in agent_list:
                marker = "→" if agent == self.current_agent else " "
                print(f"  {marker} {agent}")
                
    async def switch_agent(self, agent_name: str):
        """Switch to a different agent."""
        agents = await self.client.list_agents()
        
        if agent_name not in agents:
            print(f"{Fore.RED}Error: Agent '{agent_name}' not found.{Style.RESET_ALL}")
            return False
            
        self.current_agent = agent_name
        self.current_thread_id = None  # Start new thread with new agent
        print(f"{Fore.GREEN}Switched to agent: {agent_name}{Style.RESET_ALL}")
        
        # Get agent info
        info = await self.client.get_agent_info(agent_name)
        if info and "description" in info:
            print(f"{Fore.CYAN}Description: {info['description']}{Style.RESET_ALL}")
            
        return True
        
    async def use_system(self, system_name: str):
        """Use a system router."""
        routers = {
            "strategic": "StrategicContextRouter",
            "analysis": "AnalysisOrchestrator", 
            "planning": "PlanningCoordinator"
        }
        
        router = routers.get(system_name.lower())
        if router:
            await self.switch_agent(router)
        else:
            print(f"{Fore.RED}Error: Unknown system '{system_name}'. Use: strategic, analysis, or planning{Style.RESET_ALL}")
            
    async def show_agent_info(self):
        """Show information about the current agent."""
        if not self.current_agent:
            print(f"{Fore.YELLOW}No agent selected. Use /use <agent> to select one.{Style.RESET_ALL}")
            return
            
        info = await self.client.get_agent_info(self.current_agent)
        if "error" in info:
            print(f"{Fore.RED}Error: {info['error']}{Style.RESET_ALL}")
            return
            
        print(f"\n{Fore.GREEN}Agent Information:{Style.RESET_ALL}")
        print(f"Name: {info.get('name', 'N/A')}")
        print(f"ID: {info.get('id', 'N/A')}")
        print(f"Model: {info.get('model', 'N/A')}")
        print(f"Description: {info.get('description', 'N/A')}")
        
        if info.get('instructions'):
            print(f"\n{Fore.CYAN}Instructions:{Style.RESET_ALL}")
            print(f"{info['instructions'][:200]}..." if len(info.get('instructions', '')) > 200 else info.get('instructions'))
            
    def show_history(self):
        """Show conversation history."""
        if not self.conversation_history:
            print(f"{Fore.YELLOW}No conversation history yet.{Style.RESET_ALL}")
            return
            
        print(f"\n{Fore.GREEN}Conversation History:{Style.RESET_ALL}")
        for entry in self.conversation_history:
            timestamp = entry['timestamp']
            agent = entry['agent']
            print(f"\n{Fore.CYAN}[{timestamp}] {agent}:{Style.RESET_ALL}")
            print(f"{Fore.WHITE}User: {entry['user_message']}{Style.RESET_ALL}")
            print(f"{Fore.GREEN}Agent: {entry['agent_response']}{Style.RESET_ALL}")
            
    def save_conversation(self):
        """Save conversation to file."""
        if not self.conversation_history:
            print(f"{Fore.YELLOW}No conversation to save.{Style.RESET_ALL}")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                "timestamp": timestamp,
                "agent": self.current_agent,
                "thread_id": self.current_thread_id,
                "conversation": self.conversation_history
            }, f, indent=2)
            
        print(f"{Fore.GREEN}Conversation saved to: {filename}{Style.RESET_ALL}")
        
    async def chat_loop(self):
        """Main chat loop."""
        self.print_header()
        self.print_help()
        
        # List available agents
        await self.list_agents()
        
        print(f"\n{Fore.YELLOW}Select an agent with /use <name> or type /help for commands{Style.RESET_ALL}")
        
        while True:
            try:
                # Get user input
                prompt = f"\n{Fore.CYAN}[{self.current_agent or 'No agent'}]>{Style.RESET_ALL} "
                user_input = input(prompt).strip()
                
                if not user_input:
                    continue
                    
                # Handle commands
                if user_input.startswith('/'):
                    parts = user_input.split(maxsplit=1)
                    command = parts[0].lower()
                    args = parts[1] if len(parts) > 1 else ""
                    
                    if command == '/quit':
                        print(f"{Fore.YELLOW}Goodbye!{Style.RESET_ALL}")
                        break
                    elif command == '/help':
                        self.print_help()
                    elif command == '/agents':
                        await self.list_agents()
                    elif command == '/use' and args:
                        await self.switch_agent(args)
                    elif command == '/system' and args:
                        await self.use_system(args)
                    elif command == '/info':
                        await self.show_agent_info()
                    elif command == '/history':
                        self.show_history()
                    elif command == '/new':
                        self.current_thread_id = None
                        print(f"{Fore.GREEN}Started new conversation thread{Style.RESET_ALL}")
                    elif command == '/save':
                        self.save_conversation()
                    else:
                        print(f"{Fore.RED}Unknown command: {command}{Style.RESET_ALL}")
                        
                else:
                    # Chat with agent
                    if not self.current_agent:
                        print(f"{Fore.YELLOW}Please select an agent first with /use <agent>{Style.RESET_ALL}")
                        continue
                        
                    print(f"{Fore.YELLOW}Thinking...{Style.RESET_ALL}", end='', flush=True)
                    
                    # Get agent response
                    response = await self.client.chat_with_agent(
                        self.current_agent,
                        user_input,
                        self.current_thread_id
                    )
                    
                    # Clear "Thinking..." message
                    print("\r" + " " * 20 + "\r", end='')
                    
                    if "error" in response:
                        print(f"{Fore.RED}Error: {response['error']}{Style.RESET_ALL}")
                    else:
                        # Update thread ID
                        if response.get('thread_id'):
                            self.current_thread_id = response['thread_id']
                            
                        # Display response
                        agent_response = response.get('response', 'No response')
                        print(f"{Fore.GREEN}Agent: {agent_response}{Style.RESET_ALL}")
                        
                        # Add to history
                        self.conversation_history.append({
                            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            'agent': self.current_agent,
                            'user_message': user_input,
                            'agent_response': agent_response,
                            'thread_id': self.current_thread_id
                        })
                        
            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Use /quit to exit{Style.RESET_ALL}")
            except Exception as e:
                print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
                
    async def run(self):
        """Run the interactive chat."""
        try:
            await self.chat_loop()
        finally:
            await self.client.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Interactive chat with StratOS agents")
    parser.add_argument(
        "--agent", 
        help="Start with a specific agent",
        default=None
    )
    parser.add_argument(
        "--system",
        help="Start with a system router (strategic/analysis/planning)",
        choices=["strategic", "analysis", "planning"],
        default=None
    )
    
    args = parser.parse_args()
    
    # Create and run chat interface
    chat = InteractiveAgentChat()
    
    # Set initial agent if specified
    async def setup_and_run():
        if args.agent:
            await chat.switch_agent(args.agent)
        elif args.system:
            await chat.use_system(args.system)
            
        await chat.run()
        
    asyncio.run(setup_and_run())


if __name__ == "__main__":
    main()