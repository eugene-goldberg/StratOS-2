#!/usr/bin/env python3
"""
Performance benchmarking script for StratOS agents.
Measures response times, throughput, and concurrent request handling.
"""

import os
import sys
import asyncio
import json
import time
import statistics
from datetime import datetime
from typing import Dict, List, Any, Tuple
from colorama import init, Fore, Style
import matplotlib.pyplot as plt
import numpy as np

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.agent_interaction_client import StratosAgentClient

# Initialize colorama
init()

class AgentPerformanceBenchmark:
    """Performance benchmarking for StratOS agents."""
    
    def __init__(self):
        self.results = {
            "response_times": {},
            "throughput": {},
            "concurrency": {},
            "error_rates": {}
        }
        
        # Benchmark configurations
        self.iterations_per_test = 10
        self.concurrency_levels = [1, 5, 10]
        self.test_messages = [
            "What is our strategy?",  # Short query
            "Analyze the market trends and provide detailed insights about opportunities and risks we should consider for the next quarter.",  # Medium query
            "Create a comprehensive plan that includes resource allocation, timeline, key milestones, risk mitigation strategies, and success metrics for launching a new product line in the European market. Consider regulatory requirements, cultural differences, and competitive landscape."  # Long query
        ]
        
    def print_header(self, title: str):
        """Print a section header."""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{title}")
        print(f"{'='*60}{Style.RESET_ALL}\n")
        
    async def measure_response_time(
        self, 
        client: StratosAgentClient, 
        agent_name: str, 
        message: str
    ) -> Tuple[float, bool]:
        """Measure response time for a single request."""
        start_time = time.time()
        
        try:
            response = await client.chat_with_agent(agent_name, message)
            elapsed_time = time.time() - start_time
            
            success = "error" not in response
            return elapsed_time, success
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            return elapsed_time, False
            
    async def benchmark_response_times(self):
        """Benchmark response times for each agent."""
        self.print_header("Response Time Benchmarks")
        
        client = StratosAgentClient()
        agents = await client.list_agents()
        
        for agent_name in agents:
            print(f"{Fore.YELLOW}Testing {agent_name}...{Style.RESET_ALL}")
            
            agent_times = {
                "short": [],
                "medium": [],
                "long": []
            }
            
            query_types = ["short", "medium", "long"]
            
            for i, message in enumerate(self.test_messages):
                query_type = query_types[i]
                
                for iteration in range(self.iterations_per_test):
                    response_time, success = await self.measure_response_time(
                        client, agent_name, message
                    )
                    
                    if success:
                        agent_times[query_type].append(response_time)
                        
                    # Progress indicator
                    print(f"\r  {query_type}: {iteration + 1}/{self.iterations_per_test}", 
                          end='', flush=True)
                    
                print()  # New line after progress
                
            # Calculate statistics
            self.results["response_times"][agent_name] = {}
            
            for query_type, times in agent_times.items():
                if times:
                    self.results["response_times"][agent_name][query_type] = {
                        "mean": statistics.mean(times),
                        "median": statistics.median(times),
                        "std_dev": statistics.stdev(times) if len(times) > 1 else 0,
                        "min": min(times),
                        "max": max(times),
                        "p95": np.percentile(times, 95),
                        "samples": len(times)
                    }
                    
            # Print summary
            if agent_name in self.results["response_times"]:
                print(f"{Fore.GREEN}Results:{Style.RESET_ALL}")
                for query_type in ["short", "medium", "long"]:
                    if query_type in self.results["response_times"][agent_name]:
                        stats = self.results["response_times"][agent_name][query_type]
                        print(f"  {query_type}: avg={stats['mean']:.2f}s, "
                              f"p95={stats['p95']:.2f}s, "
                              f"samples={stats['samples']}")
                              
            print()  # Blank line between agents
            
        await client.close()
        
    async def benchmark_throughput(self):
        """Benchmark throughput (requests per second) for each agent."""
        self.print_header("Throughput Benchmarks")
        
        client = StratosAgentClient()
        agents = await client.list_agents()
        
        # Test a subset of agents for throughput
        test_agents = [
            "StrategicContextRouter",
            "AnalysisOrchestrator",
            "PlanningCoordinator"
        ]
        
        for agent_name in test_agents:
            if agent_name not in agents:
                continue
                
            print(f"{Fore.YELLOW}Testing throughput for {agent_name}...{Style.RESET_ALL}")
            
            # Send multiple requests and measure total time
            num_requests = 20
            start_time = time.time()
            successful_requests = 0
            
            tasks = []
            for i in range(num_requests):
                message = self.test_messages[i % len(self.test_messages)]
                task = self.measure_response_time(client, agent_name, message)
                tasks.append(task)
                
            # Execute all tasks concurrently
            results = await asyncio.gather(*tasks)
            
            total_time = time.time() - start_time
            successful_requests = sum(1 for _, success in results if success)
            
            # Calculate throughput
            throughput = successful_requests / total_time if total_time > 0 else 0
            
            self.results["throughput"][agent_name] = {
                "requests_per_second": throughput,
                "total_requests": num_requests,
                "successful_requests": successful_requests,
                "total_time": total_time,
                "success_rate": successful_requests / num_requests
            }
            
            print(f"{Fore.GREEN}Results:{Style.RESET_ALL}")
            print(f"  Throughput: {throughput:.2f} req/s")
            print(f"  Success Rate: {successful_requests}/{num_requests} "
                  f"({successful_requests/num_requests*100:.1f}%)")
            print()
            
        await client.close()
        
    async def benchmark_concurrency(self):
        """Benchmark concurrent request handling."""
        self.print_header("Concurrency Benchmarks")
        
        # Test router agents with different concurrency levels
        test_agents = [
            "StrategicContextRouter",
            "AnalysisOrchestrator",
            "PlanningCoordinator"
        ]
        
        for agent_name in test_agents:
            print(f"{Fore.YELLOW}Testing concurrency for {agent_name}...{Style.RESET_ALL}")
            
            agent_concurrency_results = {}
            
            for concurrency_level in self.concurrency_levels:
                # Create multiple clients for concurrent requests
                clients = [StratosAgentClient() for _ in range(concurrency_level)]
                
                print(f"  Concurrency level: {concurrency_level}")
                
                # Prepare concurrent tasks
                tasks = []
                for i in range(concurrency_level * 5):  # 5 requests per client
                    client_idx = i % concurrency_level
                    message = self.test_messages[i % len(self.test_messages)]
                    task = self.measure_response_time(
                        clients[client_idx], agent_name, message
                    )
                    tasks.append(task)
                    
                # Execute concurrent requests
                start_time = time.time()
                results = await asyncio.gather(*tasks)
                total_time = time.time() - start_time
                
                # Analyze results
                response_times = [t for t, success in results if success]
                successful = sum(1 for _, success in results if success)
                
                if response_times:
                    agent_concurrency_results[concurrency_level] = {
                        "mean_response_time": statistics.mean(response_times),
                        "p95_response_time": np.percentile(response_times, 95),
                        "total_requests": len(tasks),
                        "successful_requests": successful,
                        "success_rate": successful / len(tasks),
                        "total_time": total_time,
                        "effective_throughput": successful / total_time
                    }
                    
                # Cleanup clients
                for client in clients:
                    await client.close()
                    
            self.results["concurrency"][agent_name] = agent_concurrency_results
            
            # Print summary
            print(f"{Fore.GREEN}Results:{Style.RESET_ALL}")
            for level, stats in agent_concurrency_results.items():
                print(f"  Concurrency {level}: "
                      f"avg={stats['mean_response_time']:.2f}s, "
                      f"throughput={stats['effective_throughput']:.2f} req/s, "
                      f"success={stats['success_rate']*100:.1f}%")
            print()
            
    def generate_performance_charts(self):
        """Generate performance visualization charts."""
        # Response time comparison chart
        if self.results["response_times"]:
            plt.figure(figsize=(12, 6))
            
            agents = list(self.results["response_times"].keys())[:10]  # Top 10 agents
            short_times = []
            medium_times = []
            long_times = []
            
            for agent in agents:
                agent_data = self.results["response_times"][agent]
                short_times.append(agent_data.get("short", {}).get("mean", 0))
                medium_times.append(agent_data.get("medium", {}).get("mean", 0))
                long_times.append(agent_data.get("long", {}).get("mean", 0))
                
            x = np.arange(len(agents))
            width = 0.25
            
            plt.bar(x - width, short_times, width, label='Short Query')
            plt.bar(x, medium_times, width, label='Medium Query')
            plt.bar(x + width, long_times, width, label='Long Query')
            
            plt.xlabel('Agents')
            plt.ylabel('Response Time (seconds)')
            plt.title('Agent Response Times by Query Length')
            plt.xticks(x, agents, rotation=45, ha='right')
            plt.legend()
            plt.tight_layout()
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            plt.savefig(f'agent_response_times_{timestamp}.png')
            print(f"{Fore.GREEN}Response time chart saved: agent_response_times_{timestamp}.png{Style.RESET_ALL}")
            
    def generate_report(self):
        """Generate comprehensive performance report."""
        self.print_header("Performance Benchmark Summary")
        
        # Response Time Summary
        if self.results["response_times"]:
            print(f"{Fore.YELLOW}Response Time Performance:{Style.RESET_ALL}")
            
            all_times = []
            for agent_data in self.results["response_times"].values():
                for query_data in agent_data.values():
                    if isinstance(query_data, dict) and "mean" in query_data:
                        all_times.append(query_data["mean"])
                        
            if all_times:
                print(f"  Overall Average: {statistics.mean(all_times):.2f}s")
                print(f"  Best Average: {min(all_times):.2f}s")
                print(f"  Worst Average: {max(all_times):.2f}s")
                
                # Find fastest agents
                fastest_agents = []
                for agent, data in self.results["response_times"].items():
                    avg_time = statistics.mean([
                        v.get("mean", float('inf')) 
                        for v in data.values() 
                        if isinstance(v, dict)
                    ])
                    fastest_agents.append((agent, avg_time))
                    
                fastest_agents.sort(key=lambda x: x[1])
                
                print(f"\n  Top 3 Fastest Agents:")
                for agent, avg_time in fastest_agents[:3]:
                    print(f"    - {agent}: {avg_time:.2f}s avg")
                    
        # Throughput Summary
        if self.results["throughput"]:
            print(f"\n{Fore.YELLOW}Throughput Performance:{Style.RESET_ALL}")
            
            for agent, data in self.results["throughput"].items():
                print(f"  {agent}: {data['requests_per_second']:.2f} req/s "
                      f"(success rate: {data['success_rate']*100:.1f}%)")
                      
        # Concurrency Summary
        if self.results["concurrency"]:
            print(f"\n{Fore.YELLOW}Concurrency Performance:{Style.RESET_ALL}")
            
            for agent, levels in self.results["concurrency"].items():
                print(f"  {agent}:")
                for level, data in levels.items():
                    print(f"    {level} concurrent: "
                          f"{data['effective_throughput']:.2f} req/s, "
                          f"{data['mean_response_time']:.2f}s avg response")
                          
        # Save detailed results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"performance_benchmark_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump({
                "timestamp": timestamp,
                "configuration": {
                    "iterations_per_test": self.iterations_per_test,
                    "concurrency_levels": self.concurrency_levels,
                    "test_message_lengths": ["short", "medium", "long"]
                },
                "results": self.results
            }, f, indent=2)
            
        print(f"\n{Fore.GREEN}Detailed results saved to: {filename}{Style.RESET_ALL}")
        
    async def run_benchmarks(self):
        """Run all performance benchmarks."""
        print(f"{Fore.CYAN}StratOS Agent Performance Benchmarks{Style.RESET_ALL}")
        print("This may take several minutes...\n")
        
        # Run individual benchmarks
        await self.benchmark_response_times()
        await self.benchmark_throughput()
        await self.benchmark_concurrency()
        
        # Generate visualizations and report
        try:
            self.generate_performance_charts()
        except Exception as e:
            print(f"{Fore.YELLOW}Could not generate charts: {e}{Style.RESET_ALL}")
            
        self.generate_report()


async def main():
    """Main entry point."""
    benchmark = AgentPerformanceBenchmark()
    await benchmark.run_benchmarks()


if __name__ == "__main__":
    asyncio.run(main())