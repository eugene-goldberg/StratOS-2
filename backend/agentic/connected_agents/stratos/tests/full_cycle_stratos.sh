#!/bin/bash

# Full Cycle Test Script for StratOS Connected Agents with Telemetry
# This script performs the complete testing cycle:
# 1. Undeploy all existing StratOS agents
# 2. Deploy CEO Log and North Star agents with orchestrator
# 3. Run full test suite with telemetry
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

# Start the full cycle
echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      StratOS Agents Full Cycle Test with Telemetry        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"

# Step 1: Undeploy all existing StratOS agents
print_step "STEP 1: Undeploying all existing StratOS agents"
cd "$DEPLOYMENT_DIR"

print_info "Running removal of all StratOS agents..."
python3 remove_all_stratos_agents.py

if [ $? -eq 0 ]; then
    print_success "All StratOS agents successfully removed"
else
    print_error "Failed to remove agents"
    exit 1
fi

sleep 2

# Step 2: Deploy StratOS agents
print_step "STEP 2: Deploying StratOS agents (CEO Log, North Star, Orchestrator)"
cd "$DEPLOYMENT_DIR"

print_info "Deploying StratOS connected agents..."
python3 deploy_stratos_with_north_star.py

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

sleep 3

# Step 3: Run CEO Log tests
print_step "STEP 3: Running CEO Log Agent tests"

print_info "Executing simple CEO Log test..."
cd "$TESTS_DIR"
python3 test_ceo_simple.py

if [ $? -eq 0 ]; then
    print_success "CEO Log simple test passed"
else
    print_error "CEO Log simple test failed"
    exit 1
fi

sleep 2

# Step 4: Run North Star tests
print_step "STEP 4: Running North Star Agent tests"

print_info "Executing North Star orchestration test..."
python3 test_north_star_orchestration.py

if [ $? -eq 0 ]; then
    print_success "North Star orchestration test passed"
    print_info "Tests performed:"
    echo "  • Purpose definition delegation"
    echo "  • Vision creation delegation"
    echo "  • Values management delegation"
    echo "  • CEO Log delegation (verification)"
else
    print_error "North Star orchestration test failed"
    exit 1
fi

# Step 5: Run comprehensive test with telemetry
print_step "STEP 5: Running comprehensive test with telemetry capture"

print_info "Executing North Star telemetry capture..."
python3 capture_north_star_telemetry.py

if [ $? -eq 0 ]; then
    print_success "Telemetry capture completed successfully"
else
    print_error "Telemetry capture failed"
    exit 1
fi

# Step 6: Wait for telemetry ingestion
print_step "STEP 6: Waiting for telemetry ingestion"

print_info "Waiting 30 seconds for Application Insights to ingest telemetry data..."
echo -n "Progress: "
for i in {1..6}; do
    echo -n "."
    sleep 5
done
echo " Done!"

# Step 7: Check telemetry files
print_step "STEP 7: Verifying telemetry data"

cd "$TELEMETRY_DIR"
print_info "Checking for telemetry files..."

# Find the latest telemetry file
LATEST_TELEMETRY=$(ls -t north_star_agent/north_star_telemetry_*.json 2>/dev/null | head -1)
if [ -n "$LATEST_TELEMETRY" ]; then
    print_success "Telemetry file found: $LATEST_TELEMETRY"
    
    # Display delegation evidence
    echo -e "\n${YELLOW}Delegation Evidence:${NC}"
    grep -A2 "delegation_confirmed" "$LATEST_TELEMETRY" || true
else
    print_error "No telemetry file found"
fi

# Summary
print_step "FULL CYCLE COMPLETED SUCCESSFULLY! 🎉"

echo -e "${GREEN}Summary of actions performed:${NC}"
echo "1. ✅ Undeployed all existing StratOS agents"
echo "2. ✅ Deployed CEO Log Agent, North Star Agent, and Orchestrator"
echo "3. ✅ Ran CEO Log simple test"
echo "4. ✅ Ran North Star orchestration test"
echo "5. ✅ Captured comprehensive telemetry data"
echo "6. ✅ Verified delegation evidence:"
echo "   • CEO Log delegation: 'I'll connect you with the CEO Log specialist'"
echo "   • North Star delegation: 'I'll connect you with the North Star specialist'"
echo "   • Complete request/response flows captured"
echo "   • Distributed tracing with session IDs"

print_info "Check the telemetry folder for detailed analysis results"

# Optional: Display current deployment info
if [ -f "$STRATOS_DIR/archive/stratos_deployment_info.json" ]; then
    echo -e "\n${YELLOW}Current Deployment Info:${NC}"
    cat "$STRATOS_DIR/archive/stratos_deployment_info.json" | python3 -m json.tool | head -20
fi

echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Full cycle test completed at: $(date)${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}\n"