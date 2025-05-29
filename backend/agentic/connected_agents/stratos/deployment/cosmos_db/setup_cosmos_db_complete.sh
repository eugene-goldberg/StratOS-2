#!/bin/bash

# Setup Complete Cosmos DB Infrastructure for CEO Log Agent
# This script orchestrates all Cosmos DB setup steps in the correct order

set -e  # Exit on error

echo "=================================================="
echo "StratOS CEO Log Agent - Cosmos DB Complete Setup"
echo "=================================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
RESOURCE_GROUP="${RESOURCE_GROUP:-semantic-kernel-multi-agent-rg}"
KEY_VAULT_NAME="${KEY_VAULT_NAME:-stratos-kv-$(openssl rand -hex 4)}"
COSMOS_ACCOUNT_NAME="${COSMOS_ACCOUNT_NAME:-stratos-ceo-logs-db}"
DATABASE_NAME="StratOSData"
CONTAINER_NAME="CEOLogs"

echo -e "${YELLOW}Configuration:${NC}"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Key Vault: $KEY_VAULT_NAME"
echo "  Cosmos Account: $COSMOS_ACCOUNT_NAME"
echo "  Database: $DATABASE_NAME"
echo "  Container: $CONTAINER_NAME"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check Azure CLI
if ! command -v az &> /dev/null; then
    echo -e "${RED}Error: Azure CLI is not installed${NC}"
    echo "Please install: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

# Check Azure login
if ! az account show &> /dev/null; then
    echo -e "${RED}Error: Not logged into Azure${NC}"
    echo "Please run: az login"
    exit 1
fi

echo -e "${GREEN}Prerequisites check passed!${NC}"
echo ""

# Function to run step with error handling
run_step() {
    local step_name=$1
    local command=$2
    
    echo -e "${YELLOW}Starting: $step_name${NC}"
    if eval "$command"; then
        echo -e "${GREEN}✓ Completed: $step_name${NC}"
        echo ""
        return 0
    else
        echo -e "${RED}✗ Failed: $step_name${NC}"
        return 1
    fi
}

# Step 1: Provision Cosmos DB Infrastructure
run_step "Step 1: Provisioning Cosmos DB Infrastructure" \
    "./provision_cosmos_db.sh"

# Step 2: Configure Security
run_step "Step 2: Configuring Security (Azure AD, RBAC, Key Vault)" \
    "python3 configure_cosmos_security.py"

# Step 3: Create Schema and Stored Procedures
run_step "Step 3: Creating Schema and Stored Procedures" \
    "python3 create_schema_stored_procedures.py"

# Step 4: Test Connection and Validate Setup
run_step "Step 4: Testing Connection and Validating Setup" \
    "python3 test_cosmos_connection.py"

# Final Summary
echo "=================================================="
echo -e "${GREEN}Cosmos DB Setup Complete!${NC}"
echo "=================================================="
echo ""
echo "Next Steps:"
echo "1. Review the generated reports in the current directory:"
echo "   - cosmos_security_audit_*.json"
echo "   - cosmos_test_report_*.json"
echo "   - cosmos_schema_documentation_*.json"
echo ""
echo "2. Update the CEO Log Agent configuration with:"
echo "   - Cosmos DB endpoint from Key Vault"
echo "   - Database name: $DATABASE_NAME"
echo "   - Container name: $CONTAINER_NAME"
echo ""
echo "3. Deploy the updated CEO Log Agent with Cosmos DB integration"
echo ""
echo "For troubleshooting, check the README.md file"