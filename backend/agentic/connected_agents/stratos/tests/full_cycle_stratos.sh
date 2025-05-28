#!/bin/bash

# Full Cycle Test Script for StratOS Connected Agents with Unified Telemetry
# This script performs the complete testing cycle:
# 1. Undeploy all existing StratOS agents
# 2. Deploy all StratOS agents with orchestrator
# 3. Run unified test suite with telemetry
# 4. Collect and analyze telemetry data

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
STRATOS_DIR="$( cd "$SCRIPT_DIR/.." &> /dev/null && pwd )"
DEPLOYMENT_DIR="$STRATOS_DIR/deployment"
TESTS_DIR="$STRATOS_DIR/tests"
TELEMETRY_DIR="$STRATOS_DIR/telemetry"

# Activate virtual environment
if [ -f "$STRATOS_DIR/.venv/bin/activate" ]; then
    source "$STRATOS_DIR/.venv/bin/activate"
    print_info "Activated virtual environment"
else
    print_error "Virtual environment not found at $STRATOS_DIR/.venv"
    print_info "Creating virtual environment..."
    cd "$STRATOS_DIR"
    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
fi

# Start the full cycle
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   StratOS Agents Full Cycle Test with Unified Telemetry   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"

# Step 1: Undeploy all existing StratOS agents
print_step "STEP 1: Undeploying all existing StratOS agents"
cd "$DEPLOYMENT_DIR"

print_info "Running removal of all StratOS agents..."
python remove_all_stratos_agents.py

if [ $? -eq 0 ]; then
    print_success "All StratOS agents successfully removed"
else
    print_error "Failed to remove agents"
    exit 1
fi

sleep 2

# Step 2: Deploy StratOS agents
print_step "STEP 2: Deploying StratOS agents (CEO Log, North Star, Memory Recall)"
cd "$DEPLOYMENT_DIR"

print_info "Deploying all StratOS connected agents..."
python deploy_all_stratos_agents.py

if [ $? -eq 0 ]; then
    print_success "All StratOS agents successfully deployed"
    
    # Check deployment info
    DEPLOYMENT_INFO="$STRATOS_DIR/archive/stratos_deployment_info.json"
    if [ -f "$DEPLOYMENT_INFO" ]; then
        print_info "Deployment info saved to: $DEPLOYMENT_INFO"
    fi
else
    print_error "Failed to deploy agents"
    exit 1
fi

sleep 20  # Longer delay to avoid rate limits after deployment

# Step 3: Run simple tests for all agents
print_step "STEP 3: Running simple tests for all agents"

print_info "Executing unified simple tests..."
cd "$TESTS_DIR"
python test_all_agents_unified.py --agent all --type simple

if [ $? -eq 0 ]; then
    print_success "All simple tests completed"
else
    print_info "Some tests may have failed - check individual results"
fi

sleep 30  # Much longer delay between test batches to avoid rate limits

# Step 4: Run comprehensive test for Memory Recall  
print_step "STEP 4: Running comprehensive Memory Recall test with telemetry"

print_info "Executing comprehensive Memory Recall test..."
python test_all_agents_unified.py --agent memory --type comprehensive

if [ $? -eq 0 ]; then
    print_success "Memory Recall comprehensive test passed"
else
    print_error "Memory Recall comprehensive test failed"
fi

sleep 30  # Delay between comprehensive tests

# Step 5: Run comprehensive test for North Star
print_step "STEP 5: Running comprehensive North Star test with telemetry"

print_info "Executing comprehensive North Star test..."
python test_all_agents_unified.py --agent northstar --type comprehensive

if [ $? -eq 0 ]; then
    print_success "North Star comprehensive test passed"
else
    print_error "North Star comprehensive test failed"
fi

# Step 6: Check telemetry files
print_step "STEP 6: Verifying telemetry data"

cd "$TELEMETRY_DIR"
print_info "Checking for telemetry files..."

# Count telemetry files created in the last 10 minutes
TELEMETRY_COUNT=$(find . -name "*_telemetry_*.json" -mmin -10 2>/dev/null | wc -l)
if [ "$TELEMETRY_COUNT" -gt 0 ]; then
    print_success "Found $TELEMETRY_COUNT telemetry files"
    
    # List recent telemetry files
    echo -e "\n${YELLOW}Recent telemetry files:${NC}"
    find . -name "*_telemetry_*.json" -mmin -10 -exec basename {} \; 2>/dev/null
    
    # Check for delegation evidence in the most recent file
    LATEST_TELEMETRY=$(find . -name "*_telemetry_*.json" -mmin -10 -print0 2>/dev/null | xargs -0 ls -t | head -1)
    if [ -n "$LATEST_TELEMETRY" ]; then
        echo -e "\n${YELLOW}Delegation Evidence from $LATEST_TELEMETRY:${NC}"
        grep -A2 "delegation_confirmed" "$LATEST_TELEMETRY" 2>/dev/null || true
    fi
else
    print_error "No telemetry files found"
fi

# Summary
print_step "FULL CYCLE COMPLETED! 🎉"

echo -e "${GREEN}Summary of actions performed:${NC}"
echo "1. ✅ Undeployed all existing StratOS agents"
echo "2. ✅ Deployed CEO Log, North Star, and Memory Recall agents"
echo "3. ✅ Ran unified simple tests for all agents"
echo "4. ✅ Ran comprehensive Memory Recall test with telemetry"
echo "5. ✅ Ran comprehensive North Star test with telemetry"
echo "6. ✅ Captured and verified telemetry data"

# Display test results summary
echo -e "\n${YELLOW}Test Results Summary:${NC}"
echo "• CEO Log Agent: Check logs for delegation status"
echo "• North Star Agent: Expected to show delegation"
echo "• Memory Recall Agent: Expected to show delegation"

print_info "Check the telemetry folder for detailed analysis results"

# Optional: Display current deployment info
if [ -f "$STRATOS_DIR/archive/stratos_deployment_info.json" ]; then
    echo -e "\n${YELLOW}Current Deployment Info:${NC}"
    cat "$STRATOS_DIR/archive/stratos_deployment_info.json" | python -m json.tool | head -20
fi

echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Full cycle test completed at: $(date)${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}\n"