#!/usr/bin/env python3
"""
Verify telemetry traces are being recorded and can be queried.
Generates a simple trace and waits for it to appear in Application Insights.
"""

import asyncio
import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
import subprocess
import json

# Add the agentic directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.telemetry import initialize_telemetry, create_span_context, trace_method


class TelemetryVerifier:
    """Verify telemetry is working end-to-end."""
    
    def __init__(self):
        # Load environment
        root_env = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
        if os.path.exists(root_env):
            load_dotenv(root_env, override=True)
        
        # Initialize telemetry
        connection_string = "InstrumentationKey=189923ab-6ad8-408f-b3f6-7ae4817a3988;IngestionEndpoint=https://eastus-8.in.applicationinsights.azure.com/;LiveEndpoint=https://eastus.livediagnostics.monitor.azure.com/;ApplicationId=dfba6d9b-7df1-4bf5-af6a-2fb21f1881b2"
        
        self.tracer = initialize_telemetry(
            service_name="TelemetryVerifier",
            service_version="1.0.0",
            connection_string=connection_string,
            additional_attributes={
                "test.type": "verification",
                "test.purpose": "validate_telemetry"
            }
        )
        
        self.test_id = f"test_{int(time.time())}"
        print(f"✅ Telemetry initialized with test ID: {self.test_id}")
    
    @trace_method("verify.generate_test_trace")
    async def generate_test_trace(self):
        """Generate a test trace with unique identifier."""
        
        with create_span_context("test.verification.trace", {
            "test.id": self.test_id,
            "test.timestamp": datetime.now().isoformat(),
            "test.message": "This is a telemetry verification test"
        }) as span:
            
            print(f"\n📊 Generating test trace with ID: {self.test_id}")
            
            # Simulate some work
            await asyncio.sleep(1)
            
            # Add more attributes
            span.set_attribute("test.status", "completed")
            span.set_attribute("test.duration_ms", 1000)
            
            print("✅ Test trace generated")
            
            return self.test_id
    
    def query_traces(self, wait_minutes=5):
        """Query Application Insights for our test trace."""
        
        print(f"\n🔍 Querying Application Insights for traces...")
        print(f"⏱️  Will check every 30 seconds for up to {wait_minutes} minutes")
        
        start_time = time.time()
        max_wait = wait_minutes * 60
        check_interval = 30
        
        # Queries to try
        queries = [
            # Query 1: Look for our specific test ID
            f"traces | where timestamp > ago(10m) | where message contains '{self.test_id}' or customDimensions contains '{self.test_id}' | take 10",
            
            # Query 2: Look for our service name
            "traces | where timestamp > ago(10m) | where customDimensions.['service.name'] == 'TelemetryVerifier' | take 10",
            
            # Query 3: Count all recent traces
            "traces | where timestamp > ago(10m) | summarize count() by bin(timestamp, 1m)",
            
            # Query 4: Look for any custom dimensions
            "traces | where timestamp > ago(10m) | where isnotempty(customDimensions) | take 5 | project timestamp, message, customDimensions"
        ]
        
        attempt = 0
        while (time.time() - start_time) < max_wait:
            attempt += 1
            print(f"\n📍 Attempt {attempt} at {datetime.now().strftime('%H:%M:%S')}")
            
            for i, query in enumerate(queries, 1):
                print(f"\n   Query {i}: {query[:80]}...")
                
                try:
                    # Run the query
                    result = subprocess.run([
                        'az', 'monitor', 'app-insights', 'query',
                        '--app', 'stratos-multi-agent-appinsights',
                        '-g', 'semantic-kernel-multi-agent-rg',
                        '--analytics-query', query,
                        '-o', 'json'
                    ], capture_output=True, text=True)
                    
                    if result.returncode == 0 and result.stdout:
                        data = json.loads(result.stdout)
                        
                        if isinstance(data, list) and len(data) > 0:
                            print(f"   ✅ Found {len(data)} results!")
                            
                            # Check if we found our test trace
                            for item in data:
                                if isinstance(item, dict):
                                    # Check various fields for our test ID
                                    found = False
                                    
                                    # Check message
                                    if 'message' in item and self.test_id in str(item['message']):
                                        found = True
                                    
                                    # Check customDimensions
                                    if 'customDimensions' in item:
                                        cd_str = str(item['customDimensions'])
                                        if self.test_id in cd_str:
                                            found = True
                                    
                                    if found:
                                        print(f"\n   🎯 FOUND OUR TEST TRACE!")
                                        print(f"   Timestamp: {item.get('timestamp', 'N/A')}")
                                        print(f"   Message: {item.get('message', 'N/A')}")
                                        if 'customDimensions' in item:
                                            print(f"   Custom Dimensions: {json.dumps(item['customDimensions'], indent=6)}")
                                        return True
                            
                            # Show first result even if not our trace
                            print(f"   Sample result: {json.dumps(data[0], indent=6)[:200]}...")
                        else:
                            print(f"   No results yet")
                    else:
                        print(f"   Query failed: {result.stderr}")
                        
                except Exception as e:
                    print(f"   Error running query: {e}")
            
            if attempt < (max_wait / check_interval):
                print(f"\n⏳ Waiting {check_interval} seconds before next check...")
                time.sleep(check_interval)
        
        print(f"\n❌ Test trace not found after {wait_minutes} minutes")
        return False
    
    async def run_verification(self):
        """Run the complete verification process."""
        
        print("\n🚀 Starting Telemetry Verification")
        print("=" * 60)
        print(f"📊 Application Insights: stratos-multi-agent-appinsights")
        print(f"🕐 Start Time: {datetime.now().isoformat()}")
        print("=" * 60)
        
        # Generate test trace
        test_id = await self.generate_test_trace()
        
        # Force flush telemetry
        print("\n📤 Flushing telemetry data...")
        await asyncio.sleep(5)  # Give time for async export
        
        # Query for traces
        print("\n🔍 Starting trace verification...")
        found = self.query_traces(wait_minutes=5)
        
        print("\n" + "=" * 60)
        if found:
            print("✅ TELEMETRY VERIFICATION SUCCESSFUL!")
            print("Traces are being recorded and can be queried from Application Insights")
        else:
            print("⚠️  TELEMETRY VERIFICATION INCOMPLETE")
            print("Traces may still be propagating. Try these queries in Azure Portal:")
            print(f"1. traces | where message contains '{test_id}'")
            print(f"2. traces | where customDimensions.['service.name'] == 'TelemetryVerifier'")
            print(f"3. traces | where timestamp > ago(30m) | order by timestamp desc")
        print("=" * 60)


async def main():
    """Main entry point."""
    verifier = TelemetryVerifier()
    await verifier.run_verification()


if __name__ == "__main__":
    asyncio.run(main())