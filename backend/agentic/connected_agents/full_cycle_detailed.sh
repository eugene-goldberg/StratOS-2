#!/bin/bash

# Full Cycle Test Script for Connected Agents with Telemetry - Detailed Version
# This script provides comprehensive testing with options and detailed logging

set -e  # Exit on error

# Default values
WAIT_TIME=120  # 2 minutes default wait for telemetry
SKIP_UNDEPLOY=false
SKIP_DEPLOY=false
SKIP_TEST=false
SKIP_TELEMETRY=false
VERBOSE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help           Show this help message"
    echo "  -w, --wait TIME      Wait time for telemetry ingestion in seconds (default: 120)"
    echo "  -s, --skip STEP      Skip a specific step: undeploy|deploy|test|telemetry"
    echo "  -v, --verbose        Enable verbose output"
    echo "  --quick              Quick mode with 30 second telemetry wait"
    echo ""
    echo "Examples:"
    echo "  $0                   # Run full cycle with defaults"
    echo "  $0 --quick           # Run with shortened wait time"
    echo "  $0 -s undeploy       # Skip undeploy step (use existing agents)"
    echo "  $0 -w 180 -v         # Wait 3 minutes with verbose output"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            usage
            exit 0
            ;;
        -w|--wait)
            WAIT_TIME="$2"
            shift 2
            ;;
        -s|--skip)
            case "$2" in
                undeploy)
                    SKIP_UNDEPLOY=true
                    ;;
                deploy)
                    SKIP_DEPLOY=true
                    ;;
                test)
                    SKIP_TEST=true
                    ;;
                telemetry)
                    SKIP_TELEMETRY=true
                    ;;
                *)
                    echo "Invalid skip option: $2"
                    usage
                    exit 1
                    ;;
            esac
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --quick)
            WAIT_TIME=30
            shift
            ;;
        *)
            echo "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Function to print colored output
print_step() {
    echo -e "\n${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║ ${GREEN}$1${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}\n"
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

print_debug() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${CYAN}🔍 $1${NC}"
    fi
}

# Function to check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed"
        exit 1
    fi
    
    # Check .env file
    if [ ! -f "$(dirname "$0")/.env" ]; then
        print_error ".env file not found in connected_agents directory"
        exit 1
    fi
    
    # Check Application Insights connection string
    if ! grep -q "APPLICATIONINSIGHTS_CONNECTION_STRING" "$(dirname "$0")/.env"; then
        print_error "APPLICATIONINSIGHTS_CONNECTION_STRING not found in .env"
        exit 1
    fi
    
    print_success "All prerequisites met"
}

# Function to capture current agent state
capture_agent_state() {
    local state_file="$1"
    print_debug "Capturing current agent state to $state_file"
    
    cd "$SCRIPTS_DIR"
    python3 list_all_deployed_agents.py > "$state_file" 2>&1 || true
}

# Function to wait with progress indicator
wait_with_progress() {
    local duration=$1
    local message=$2
    
    echo -ne "${YELLOW}$message ${NC}"
    
    local elapsed=0
    local interval=5
    
    while [ $elapsed -lt $duration ]; do
        echo -n "."
        sleep $interval
        elapsed=$((elapsed + interval))
        
        # Show percentage every 20 seconds
        if [ $((elapsed % 20)) -eq 0 ]; then
            local percent=$((elapsed * 100 / duration))
            echo -ne " ${percent}% "
        fi
    done
    
    echo " Done!"
}

# Get directories
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
AGENTIC_DIR="$( cd "$SCRIPT_DIR/.." &> /dev/null && pwd )"
SCRIPTS_DIR="$AGENTIC_DIR/scripts"
LOG_DIR="$SCRIPT_DIR/logs"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Create log directory
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/full_cycle_${TIMESTAMP}.log"

# Start logging
exec > >(tee -a "$LOG_FILE")
exec 2>&1

# Start the full cycle
echo -e "${PURPLE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║     Connected Agents Full Cycle Test with Telemetry       ║${NC}"
echo -e "${PURPLE}║                   $(date +'%Y-%m-%d %H:%M:%S')                    ║${NC}"
echo -e "${PURPLE}╚════════════════════════════════════════════════════════════╝${NC}"

# Check prerequisites
check_prerequisites

# Step 1: Undeploy all existing agents
if [ "$SKIP_UNDEPLOY" = false ]; then
    print_step "STEP 1: Undeploying all existing agents"
    
    # Capture initial state
    capture_agent_state "$LOG_DIR/agents_before_undeploy_${TIMESTAMP}.txt"
    
    cd "$SCRIPTS_DIR"
    print_info "Running force removal of all deployed agents..."
    
    if python3 remove_all_deployed_agents_force.py; then
        print_success "All agents successfully removed"
    else
        print_error "Failed to remove agents"
        exit 1
    fi
    
    sleep 2
else
    print_info "Skipping undeploy step as requested"
fi

# Step 2: Redeploy all connected agents
if [ "$SKIP_DEPLOY" = false ]; then
    print_step "STEP 2: Redeploying all connected agents"
    cd "$SCRIPT_DIR"
    
    print_info "Deploying connected agents..."
    print_debug "Agents to deploy: Greeter, Calculator, Weather, Orchestrator"
    
    if python3 deploy_connected_agents.py; then
        print_success "All agents successfully deployed"
        
        # Capture deployment state
        capture_agent_state "$LOG_DIR/agents_after_deploy_${TIMESTAMP}.txt"
        
        # Save deployment info with timestamp
        if [ -f "deployment_info.json" ]; then
            cp deployment_info.json "$LOG_DIR/deployment_info_${TIMESTAMP}.json"
            print_debug "Deployment info saved to logs"
        fi
    else
        print_error "Failed to deploy agents"
        exit 1
    fi
    
    sleep 3
else
    print_info "Skipping deploy step as requested"
fi

# Step 3: Run full test with telemetry
if [ "$SKIP_TEST" = false ]; then
    print_step "STEP 3: Running full test with telemetry"
    
    print_info "Executing test_quick_deployed.py..."
    cd "$AGENTIC_DIR"
    
    # Capture test output
    TEST_OUTPUT="$LOG_DIR/test_output_${TIMESTAMP}.txt"
    
    if python3 connected_agents/test_quick_deployed.py > "$TEST_OUTPUT" 2>&1; then
        print_success "All tests completed successfully"
        
        # Extract key results from test output
        if grep -q "Greeting Request" "$TEST_OUTPUT"; then
            print_success "Greeting delegation tested"
        fi
        if grep -q "Calculator Request" "$TEST_OUTPUT"; then
            print_success "Calculator delegation tested"
        fi
        if grep -q "Weather Request" "$TEST_OUTPUT"; then
            print_success "Weather delegation tested"
        fi
        
        print_debug "Full test output saved to $TEST_OUTPUT"
    else
        print_error "Tests failed"
        cat "$TEST_OUTPUT"
        exit 1
    fi
else
    print_info "Skipping test step as requested"
fi

# Step 4: Collect and analyze telemetry
if [ "$SKIP_TELEMETRY" = false ]; then
    print_step "STEP 4: Waiting for telemetry ingestion"
    
    print_info "Waiting $WAIT_TIME seconds for Application Insights ingestion..."
    wait_with_progress $WAIT_TIME "Processing telemetry"
    
    print_step "STEP 5: Collecting telemetry data"
    
    cd "$SCRIPT_DIR"
    print_info "Querying Application Insights for agent activity..."
    
    # Run telemetry collection
    TELEMETRY_OUTPUT="$LOG_DIR/telemetry_collection_${TIMESTAMP}.txt"
    
    if python3 telemetry/get_telemetry_simple.py > "$TELEMETRY_OUTPUT" 2>&1; then
        print_success "Telemetry data collected successfully"
        
        # Find and process the latest telemetry file
        LATEST_TELEMETRY=$(ls -t agent_telemetry_*.json 2>/dev/null | head -1)
        if [ -n "$LATEST_TELEMETRY" ]; then
            print_info "Telemetry saved to: $LATEST_TELEMETRY"
            
            # Copy to telemetry folder and logs
            cp "$LATEST_TELEMETRY" telemetry/ 2>/dev/null || true
            cp "$LATEST_TELEMETRY" "$LOG_DIR/" 2>/dev/null || true
            
            # Extract summary info
            TRACE_COUNT=$(grep -o "trace_count" "$LATEST_TELEMETRY" | wc -l)
            print_debug "Collected traces: $TRACE_COUNT"
        fi
    else
        print_error "Failed to collect telemetry"
        cat "$TELEMETRY_OUTPUT"
    fi
    
    print_step "STEP 6: Analyzing telemetry data"
    
    cd "$SCRIPT_DIR/telemetry"
    ANALYSIS_OUTPUT="$LOG_DIR/telemetry_analysis_${TIMESTAMP}.txt"
    
    if python3 analyze_telemetry_traces.py > "$ANALYSIS_OUTPUT" 2>&1; then
        print_success "Telemetry analysis completed"
        
        # Extract key metrics
        if grep -q "Connected agent delegations:" "$ANALYSIS_OUTPUT"; then
            DELEGATIONS=$(grep "Connected agent delegations:" "$ANALYSIS_OUTPUT" | awk '{print $4}')
            print_success "Found $DELEGATIONS connected agent delegations"
        fi
        
        print_debug "Full analysis saved to $ANALYSIS_OUTPUT"
        
        # Show summary from analysis
        echo -e "\n${CYAN}Analysis Summary:${NC}"
        grep -A 10 "SUMMARY" "$ANALYSIS_OUTPUT" | tail -n +2 || true
    else
        print_error "Failed to analyze telemetry"
    fi
else
    print_info "Skipping telemetry collection as requested"
fi

# Final Summary
print_step "FULL CYCLE COMPLETED! 🎉"

echo -e "${GREEN}Summary of actions performed:${NC}"
[ "$SKIP_UNDEPLOY" = false ] && echo "1. ✅ Undeployed all existing agents"
[ "$SKIP_DEPLOY" = false ] && echo "2. ✅ Redeployed connected agents"
[ "$SKIP_TEST" = false ] && echo "3. ✅ Ran full test suite"
[ "$SKIP_TELEMETRY" = false ] && echo "4. ✅ Collected and analyzed telemetry"

echo -e "\n${YELLOW}Logs and outputs saved to: $LOG_DIR${NC}"
echo -e "${YELLOW}Main log file: $LOG_FILE${NC}"

# Display current deployment if available
if [ -f "$SCRIPT_DIR/deployment_info.json" ] && [ "$VERBOSE" = true ]; then
    echo -e "\n${CYAN}Current Deployment:${NC}"
    python3 -m json.tool "$SCRIPT_DIR/deployment_info.json" | head -20
fi

echo -e "\n${PURPLE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Completed at: $(date +'%Y-%m-%d %H:%M:%S')${NC}"
echo -e "${PURPLE}════════════════════════════════════════════════════════════${NC}\n"