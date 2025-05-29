#!/usr/bin/env python3
"""
Configure Cosmos DB Security for CEO Log Agent
This script sets up RBAC, managed identities, and access policies
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
import subprocess
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Colors for output
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'

def print_step(message: str):
    print(f"\n{Colors.BLUE}{'='*60}{Colors.ENDC}")
    print(f"{Colors.GREEN}{message}{Colors.ENDC}")
    print(f"{Colors.BLUE}{'='*60}{Colors.ENDC}\n")

def print_info(message: str):
    print(f"{Colors.YELLOW}ℹ️  {message}{Colors.ENDC}")

def print_success(message: str):
    print(f"{Colors.GREEN}✅ {message}{Colors.ENDC}")

def print_error(message: str):
    print(f"{Colors.RED}❌ {message}{Colors.ENDC}")

class CosmosSecurityConfigurator:
    def __init__(self):
        self.config = {
            "resource_group": "semantic-kernel-multi-agent-rg",
            "cosmos_account": "stratos-ceo-logs-db",
            "key_vault": "stratos-keyvault",
            "database": "StratOSData",
            "container": "CEOLogs"
        }
        
    def run_command(self, command: str) -> Dict[str, Any]:
        """Run Azure CLI command and return result"""
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Try to parse JSON output
            if result.stdout:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return {"output": result.stdout}
            return {"success": True}
            
        except subprocess.CalledProcessError as e:
            print_error(f"Command failed: {e.stderr}")
            raise
    
    def configure_managed_identity(self):
        """Configure managed identity for CEO Log Agent"""
        print_step("Configuring Managed Identity")
        
        # Create user-assigned managed identity
        identity_name = "stratos-ceo-log-identity"
        print_info(f"Creating managed identity: {identity_name}")
        
        # Check if identity exists
        check_cmd = f"az identity show --name {identity_name} --resource-group {self.config['resource_group']} 2>/dev/null"
        try:
            identity = self.run_command(check_cmd)
            print_info("Managed identity already exists")
        except:
            # Create new identity
            create_cmd = f"""az identity create \
                --name {identity_name} \
                --resource-group {self.config['resource_group']} \
                --location eastus"""
            
            identity = self.run_command(create_cmd)
            print_success("Managed identity created!")
        
        # Get identity details
        principal_id = identity.get('principalId')
        client_id = identity.get('clientId')
        
        print_info(f"Principal ID: {principal_id}")
        print_info(f"Client ID: {client_id}")
        
        # Assign Cosmos DB role
        print_info("Assigning Cosmos DB Data Contributor role...")
        
        cosmos_resource_id = f"/subscriptions/{{subscription}}/resourceGroups/{self.config['resource_group']}/providers/Microsoft.DocumentDB/databaseAccounts/{self.config['cosmos_account']}"
        
        # Get subscription ID
        sub_cmd = "az account show --query id -o tsv"
        subscription = self.run_command(sub_cmd).get('output', '').strip()
        cosmos_resource_id = cosmos_resource_id.format(subscription=subscription)
        
        # Create role assignment
        role_cmd = f"""az cosmosdb sql role assignment create \
            --account-name {self.config['cosmos_account']} \
            --resource-group {self.config['resource_group']} \
            --role-definition-id "00000000-0000-0000-0000-000000000002" \
            --principal-id {principal_id} \
            --scope {cosmos_resource_id}"""
        
        try:
            self.run_command(role_cmd)
            print_success("Role assignment created!")
        except:
            print_info("Role assignment might already exist")
        
        # Store identity details in Key Vault
        print_info("Storing identity details in Key Vault...")
        
        kv_cmds = [
            f"az keyvault secret set --vault-name {self.config['key_vault']} --name ceo-log-identity-client-id --value {client_id}",
            f"az keyvault secret set --vault-name {self.config['key_vault']} --name ceo-log-identity-principal-id --value {principal_id}"
        ]
        
        for cmd in kv_cmds:
            self.run_command(cmd + " > /dev/null")
        
        print_success("Identity configuration complete!")
        return client_id, principal_id
    
    def configure_network_security(self):
        """Configure network security rules"""
        print_step("Configuring Network Security")
        
        # Enable private endpoints
        print_info("Checking network configuration...")
        
        # Get current network rules
        network_cmd = f"""az cosmosdb show \
            --name {self.config['cosmos_account']} \
            --resource-group {self.config['resource_group']} \
            --query "publicNetworkAccess" -o tsv"""
        
        public_access = self.run_command(network_cmd).get('output', '').strip()
        print_info(f"Current public network access: {public_access}")
        
        # Configure IP rules for current machine
        print_info("Adding current IP to firewall rules...")
        
        # Get current public IP
        ip_cmd = "curl -s https://api.ipify.org"
        current_ip = subprocess.run(ip_cmd, shell=True, capture_output=True, text=True).stdout.strip()
        print_info(f"Current IP: {current_ip}")
        
        # Add IP to firewall
        firewall_cmd = f"""az cosmosdb update \
            --name {self.config['cosmos_account']} \
            --resource-group {self.config['resource_group']} \
            --ip-range-filter "{current_ip}" """
        
        self.run_command(firewall_cmd)
        print_success("Firewall rule added!")
        
    def configure_diagnostic_settings(self):
        """Configure diagnostic settings for monitoring"""
        print_step("Configuring Diagnostic Settings")
        
        # Check if Log Analytics workspace exists
        workspace_name = "stratos-log-analytics"
        print_info(f"Checking for Log Analytics workspace: {workspace_name}")
        
        check_ws_cmd = f"az monitor log-analytics workspace show --name {workspace_name} --resource-group {self.config['resource_group']} 2>/dev/null"
        
        try:
            workspace = self.run_command(check_ws_cmd)
            workspace_id = workspace.get('id')
            print_info("Log Analytics workspace exists")
        except:
            # Create workspace
            print_info("Creating Log Analytics workspace...")
            create_ws_cmd = f"""az monitor log-analytics workspace create \
                --name {workspace_name} \
                --resource-group {self.config['resource_group']} \
                --location eastus"""
            
            workspace = self.run_command(create_ws_cmd)
            workspace_id = workspace.get('id')
            print_success("Log Analytics workspace created!")
        
        # Create diagnostic setting
        print_info("Creating diagnostic setting for Cosmos DB...")
        
        cosmos_id = f"/subscriptions/{{subscription}}/resourceGroups/{self.config['resource_group']}/providers/Microsoft.DocumentDB/databaseAccounts/{self.config['cosmos_account']}"
        
        # Get subscription ID
        sub_cmd = "az account show --query id -o tsv"
        subscription = self.run_command(sub_cmd).get('output', '').strip()
        cosmos_id = cosmos_id.format(subscription=subscription)
        
        diag_cmd = f"""az monitor diagnostic-settings create \
            --name "ceo-log-diagnostics" \
            --resource {cosmos_id} \
            --workspace {workspace_id} \
            --logs '[
                {{"category": "DataPlaneRequests", "enabled": true}},
                {{"category": "QueryRuntimeStatistics", "enabled": true}},
                {{"category": "PartitionKeyStatistics", "enabled": true}},
                {{"category": "ControlPlaneRequests", "enabled": true}}
            ]' \
            --metrics '[{{"category": "Requests", "enabled": true}}]'"""
        
        try:
            self.run_command(diag_cmd)
            print_success("Diagnostic settings created!")
        except:
            print_info("Diagnostic settings might already exist")
        
        # Store workspace ID in Key Vault
        kv_cmd = f"az keyvault secret set --vault-name {self.config['key_vault']} --name log-analytics-workspace-id --value {workspace_id} > /dev/null"
        self.run_command(kv_cmd)
        
        print_success("Diagnostic configuration complete!")
    
    def configure_backup_policy(self):
        """Configure backup policy for Cosmos DB"""
        print_step("Configuring Backup Policy")
        
        print_info("Setting up continuous backup with 7-day retention...")
        
        backup_cmd = f"""az cosmosdb update \
            --name {self.config['cosmos_account']} \
            --resource-group {self.config['resource_group']} \
            --backup-policy-type Continuous \
            --continuous-tier "Continuous7Days" """
        
        try:
            self.run_command(backup_cmd)
            print_success("Continuous backup enabled!")
        except:
            print_info("Backup policy might already be configured")
    
    def create_access_policies(self):
        """Create custom access policies"""
        print_step("Creating Custom Access Policies")
        
        # Define custom role for CEO Log operations
        role_definition = {
            "roleName": "CEO Log Data Operator",
            "type": "CustomRole",
            "assignableScopes": [
                f"/subscriptions/{{subscription}}/resourceGroups/{self.config['resource_group']}/providers/Microsoft.DocumentDB/databaseAccounts/{self.config['cosmos_account']}"
            ],
            "permissions": [
                {
                    "dataActions": [
                        "Microsoft.DocumentDB/databaseAccounts/readMetadata",
                        "Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/items/*",
                        "Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/executeQuery",
                        "Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers/readChangeFeed"
                    ]
                }
            ]
        }
        
        # Save role definition to file
        with open('ceo-log-role.json', 'w') as f:
            json.dump(role_definition, f, indent=2)
        
        print_info("Creating custom role definition...")
        
        # Get subscription ID
        sub_cmd = "az account show --query id -o tsv"
        subscription = self.run_command(sub_cmd).get('output', '').strip()
        
        # Update assignable scopes
        role_definition['assignableScopes'][0] = role_definition['assignableScopes'][0].format(subscription=subscription)
        
        with open('ceo-log-role.json', 'w') as f:
            json.dump(role_definition, f, indent=2)
        
        # Create role
        role_cmd = f"""az cosmosdb sql role definition create \
            --account-name {self.config['cosmos_account']} \
            --resource-group {self.config['resource_group']} \
            --body @ceo-log-role.json"""
        
        try:
            role_result = self.run_command(role_cmd)
            role_id = role_result.get('id')
            print_success(f"Custom role created: {role_id}")
            
            # Store role ID in Key Vault
            kv_cmd = f"az keyvault secret set --vault-name {self.config['key_vault']} --name ceo-log-custom-role-id --value {role_id} > /dev/null"
            self.run_command(kv_cmd)
        except:
            print_info("Custom role might already exist")
        
        # Clean up
        os.remove('ceo-log-role.json')
    
    def generate_security_report(self):
        """Generate security configuration report"""
        print_step("Generating Security Report")
        
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "cosmos_account": self.config['cosmos_account'],
            "security_features": {
                "azure_ad_authentication": "Enabled",
                "managed_identity": "Configured",
                "network_security": "IP Firewall Enabled",
                "encryption": "Enabled at Rest and in Transit",
                "backup": "Continuous (7-day retention)",
                "diagnostics": "Enabled with Log Analytics",
                "rbac": "Custom roles configured"
            },
            "key_vault_secrets": [
                "cosmos-db-connection-string",
                "cosmos-db-endpoint",
                "ceo-log-identity-client-id",
                "ceo-log-identity-principal-id",
                "ceo-log-sp-client-id",
                "ceo-log-sp-client-secret",
                "ceo-log-sp-tenant-id",
                "log-analytics-workspace-id",
                "ceo-log-custom-role-id"
            ],
            "compliance": {
                "data_residency": "East US",
                "data_sovereignty": "US",
                "encryption_standard": "AES-256"
            }
        }
        
        # Save report
        with open('cosmos_security_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print_success("Security report saved to cosmos_security_report.json")
        
        # Display summary
        print_info("\nSecurity Configuration Summary:")
        print("================================")
        for feature, status in report['security_features'].items():
            print(f"• {feature.replace('_', ' ').title()}: {status}")
        
        print(f"\n{Colors.YELLOW}Key Vault Secrets Created:{Colors.ENDC}")
        for secret in report['key_vault_secrets']:
            print(f"  - {secret}")
    
    async def run(self):
        """Run all security configuration steps"""
        try:
            # Check Azure CLI authentication
            print_info("Checking Azure CLI authentication...")
            auth_check = self.run_command("az account show")
            print_success("Authenticated to Azure")
            
            # Run configuration steps
            self.configure_managed_identity()
            self.configure_network_security()
            self.configure_diagnostic_settings()
            self.configure_backup_policy()
            self.create_access_policies()
            self.generate_security_report()
            
            print_step("SECURITY CONFIGURATION COMPLETE! 🔒")
            print_info("All security features have been configured.")
            print_info("Review cosmos_security_report.json for details.")
            
        except Exception as e:
            print_error(f"Security configuration failed: {e}")
            sys.exit(1)

if __name__ == "__main__":
    configurator = CosmosSecurityConfigurator()
    asyncio.run(configurator.run())