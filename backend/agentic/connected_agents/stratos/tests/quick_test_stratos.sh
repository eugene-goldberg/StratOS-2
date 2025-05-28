#!/bin/bash

# Quick Test Script for StratOS Connected Agents with Unified Telemetry
# This script runs a quick smoke test without deployment

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Activate virtual environment
if [ -f "$STRATOS_DIR/.venv/bin/activate" ]; then
    source "$STRATOS_DIR/.venv/bin/activate"
    print_info "Activated virtual environment"
else
    print_error "Virtual environment not found at $STRATOS_DIR/.venv"
    print_info "Please run: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      StratOS Agents Quick Test with Unified Telemetry     ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"

# Check if deployment exists
DEPLOYMENT_INFO="$STRATOS_DIR/archive/stratos_deployment_info.json"
if [ ! -f "$DEPLOYMENT_INFO" ]; then
    print_error "No deployment found. Please run deployment script first."
    exit 1
fi

# Run unified simple test for all agents
echo -e "\n${GREEN}Running unified simple test for all agents...${NC}"
cd "$SCRIPT_DIR"
python test_all_agents_unified.py --agent all --type simple

if [ $? -eq 0 ]; then
    print_success "All agent tests completed"
else
    print_info "Some tests may have failed - check individual results"
fi

# Quick telemetry check
echo -e "\n${GREEN}Checking for recent telemetry files...${NC}"
TELEMETRY_COUNT=$(find "$STRATOS_DIR/telemetry" -name "*_telemetry_*.json" -mmin -5 2>/dev/null | wc -l)
if [ "$TELEMETRY_COUNT" -gt 0 ]; then
    print_success "Found $TELEMETRY_COUNT recent telemetry files"
    echo -e "${YELLOW}Recent files:${NC}"
    find "$STRATOS_DIR/telemetry" -name "*_telemetry_*.json" -mmin -5 -exec basename {} \; 2>/dev/null
else
    print_info "No recent telemetry files found"
fi

echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Quick test completed at: $(date)${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}\n"