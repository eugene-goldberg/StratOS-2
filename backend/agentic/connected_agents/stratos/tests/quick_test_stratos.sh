#!/bin/bash

# Quick Test Script for StratOS Connected Agents
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

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           StratOS Agents Quick Test Suite                  ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"

# Run CEO Log simple test
echo -e "\n${GREEN}Running CEO Log Agent Test...${NC}"
cd "$SCRIPT_DIR"
python3 test_ceo_simple.py

if [ $? -eq 0 ]; then
    print_success "CEO Log test passed"
else
    print_error "CEO Log test failed"
    exit 1
fi

echo -e "\n${GREEN}Running North Star Agent Test...${NC}"
python3 test_north_star_simple.py

if [ $? -eq 0 ]; then
    print_success "North Star test passed"
else
    print_error "North Star test failed"
    exit 1
fi

echo -e "\n${BLUE}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Quick test completed successfully at: $(date)${NC}"
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}\n"