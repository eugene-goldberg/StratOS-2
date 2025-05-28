#!/bin/bash

# Full Cycle Test Script for Connected Agents with Telemetry
# This script replicates the complete testing cycle:
# 1. Undeploy all existing agents
# 2. Redeploy all connected agents
# 3. Run full test with telemetry
# 4. Collect telemetry data
# 5. Display and analyze telemetry

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_step() {
    echo -e "\n${BLUE}============================================================${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${BLUE}============================================================${NC}\n"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
AGENTIC_DIR="$( cd "$SCRIPT_DIR/.." &> /dev/null && pwd )"
SCRIPTS_DIR="$AGENTIC_DIR/scripts"

# Start the full cycle
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║    Connected Agents Full Cycle Test with Telemetry        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"

# Step 1: Undeploy all existing agents
print_step "STEP 1: Undeploying all existing agents"
cd "$SCRIPTS_DIR"

print_info "Running force removal of all deployed agents..."
python3 remove_all_deployed_agents_force.py

if [ $? -eq 0 ]; then
    print_success "All agents successfully removed"
else
    print_error "Failed to remove agents"
    exit 1
fi

sleep 2

# Step 2: Redeploy all connected agents
print_step "STEP 2: Redeploying all connected agents"
cd "$SCRIPT_DIR"

print_info "Deploying connected agents (Greeter, Calculator, Weather, Orchestrator)..."
python3 deploy_connected_agents.py

if [ $? -eq 0 ]; then
    print_success "All agents successfully deployed"
    
    # Save deployment info
    print_info "Deployment info saved to deployment_info.json"
else
    print_error "Failed to deploy agents"
    exit 1
fi

sleep 3

# Step 3: Run full test with telemetry
print_step "STEP 3: Running full test with telemetry"

print_info "Executing test_quick_deployed.py to test all agent delegations..."
cd "$AGENTIC_DIR"
python3 connected_agents/test_quick_deployed.py

if [ $? -eq 0 ]; then
    print_success "All tests completed successfully"
    print_info "Tests performed:"
    echo "  • Greeting delegation"
    echo "  • Calculator delegation (789 × 456)"
    echo "  • Weather delegation (San Francisco)"
else
    print_error "Tests failed"
    exit 1
fi

# Step 4: Wait for telemetry ingestion
print_step "STEP 4: Waiting for telemetry ingestion"

print_info "Waiting 2 minutes for Application Insights to ingest telemetry data..."
echo -n "Progress: "
for i in {1..24}; do
    echo -n "."
    sleep 5
done
echo " Done!"

# Step 5: Collect telemetry data
print_step "STEP 5: Collecting telemetry data from Application Insights"

cd "$SCRIPT_DIR"
print_info "Querying Application Insights for agent activity..."
python3 telemetry/get_telemetry_simple.py

if [ $? -eq 0 ]; then
    print_success "Telemetry data collected successfully"
    
    # Find the latest telemetry file
    LATEST_TELEMETRY=$(ls -t agent_telemetry_*.json 2>/dev/null | head -1)
    if [ -n "$LATEST_TELEMETRY" ]; then
        print_info "Telemetry saved to: $LATEST_TELEMETRY"
        
        # Copy to telemetry folder if not already there
        if [ ! -f "telemetry/$LATEST_TELEMETRY" ]; then
            cp "$LATEST_TELEMETRY" telemetry/
        fi
    fi
else
    print_error "Failed to collect telemetry"
    exit 1
fi

# Step 6: Analyze telemetry
print_step "STEP 6: Analyzing telemetry data"

cd "$SCRIPT_DIR/telemetry"
print_info "Running telemetry analysis..."
python3 analyze_telemetry_traces.py

if [ $? -eq 0 ]; then
    print_success "Telemetry analysis completed"
else
    print_error "Failed to analyze telemetry"
    exit 1
fi

# Summary
print_step "FULL CYCLE COMPLETED SUCCESSFULLY! 🎉"

echo -e "${GREEN}Summary of actions performed:${NC}"
echo "1. ✅ Undeployed all existing agents"
echo "2. ✅ Redeployed 4 connected agents (Greeter, Calculator, Weather, Orchestrator)"
echo "3. ✅ Ran full test suite with all delegation types"
echo "4. ✅ Collected telemetry data from Application Insights"
echo "5. ✅ Analyzed telemetry showing:"
echo "   • Connected agent delegations with tool calls"
echo "   • Token usage tracking"
echo "   • Complete request/response flows"
echo "   • Distributed tracing with trace IDs"

print_info "Check the telemetry folder for detailed analysis results"

# Optional: Display deployment info
if [ -f "$SCRIPT_DIR/deployment_info.json" ]; then
    echo -e "\n${YELLOW}Current Deployment Info:${NC}"
    cat "$SCRIPT_DIR/deployment_info.json" | python3 -m json.tool
fi

echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Full cycle test completed at: $(date)${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}\n"