#!/usr/bin/env python3
"""
Retrieve all secrets from Azure Key Vault
"""

import asyncio
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv(Path(__file__).parent.parent / '.env')

# Color codes for output
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
CYAN = '\033[0;36m'
RED = '\033[0;31m'
NC = '\033[0m'  # No Color


def retrieve_all_secrets():
    """Retrieve all secrets from Azure Key Vault"""
    
    key_vault_name = "stratos-keyvault"
    vault_url = f"https://{key_vault_name}.vault.azure.net/"
    
    print(f"{YELLOW}Retrieving secrets from Azure Key Vault: {key_vault_name}{NC}\n")
    
    try:
        # Initialize the Key Vault client
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=vault_url, credential=credential)
        
        print(f"{CYAN}Listing all secrets...{NC}\n")
        
        # List all secrets
        secrets_properties = client.list_properties_of_secrets()
        
        secrets_found = []
        for secret_property in secrets_properties:
            secret_name = secret_property.name
            print(f"{GREEN}Found secret:{NC} {secret_name}")
            
            # Retrieve the secret value
            try:
                secret = client.get_secret(secret_name)
                secrets_found.append({
                    'name': secret_name,
                    'value': secret.value,
                    'enabled': secret_property.enabled,
                    'created': secret_property.created_on,
                    'updated': secret_property.updated_on
                })
                print(f"  Status: {'Enabled' if secret_property.enabled else 'Disabled'}")
                print(f"  Created: {secret_property.created_on}")
                print(f"  Updated: {secret_property.updated_on}")
                print(f"  Value: {secret.value[:50]}..." if len(secret.value) > 50 else f"  Value: {secret.value}")
                print()
            except Exception as e:
                print(f"{RED}  Error retrieving value: {e}{NC}\n")
        
        # Display summary
        print(f"\n{YELLOW}{'='*60}{NC}")
        print(f"{GREEN}SUMMARY: Found {len(secrets_found)} secrets{NC}")
        print(f"{YELLOW}{'='*60}{NC}\n")
        
        # Display all secrets with their values
        print(f"{CYAN}All Secrets and Values:{NC}\n")
        for secret in secrets_found:
            print(f"{GREEN}{secret['name']}:{NC}")
            print(f"  {secret['value']}")
            print()
        
        # Check for Cosmos DB related secrets
        print(f"\n{CYAN}Checking for Cosmos DB related secrets...{NC}\n")
        cosmos_secrets = [s for s in secrets_found if 'cosmos' in s['name'].lower()]
        
        if cosmos_secrets:
            print(f"{GREEN}Found {len(cosmos_secrets)} Cosmos DB related secrets:{NC}")
            for secret in cosmos_secrets:
                print(f"  - {secret['name']}")
                
            # Check if we have the connection string
            connection_string_secret = next((s for s in cosmos_secrets if 'connection-string' in s['name']), None)
            if connection_string_secret:
                print(f"\n{GREEN}✅ Cosmos DB connection string found:{NC}")
                print(f"  Name: {connection_string_secret['name']}")
                print(f"  Value preview: {connection_string_secret['value'][:80]}...")
                
                # Parse the connection string to get endpoint and key
                conn_str = connection_string_secret['value']
                if 'AccountEndpoint=' in conn_str and 'AccountKey=' in conn_str:
                    endpoint_start = conn_str.find('AccountEndpoint=') + len('AccountEndpoint=')
                    endpoint_end = conn_str.find(';', endpoint_start)
                    endpoint = conn_str[endpoint_start:endpoint_end]
                    
                    key_start = conn_str.find('AccountKey=') + len('AccountKey=')
                    key_end = conn_str.find(';', key_start)
                    key = conn_str[key_start:key_end]
                    
                    print(f"\n{CYAN}Parsed from connection string:{NC}")
                    print(f"  Endpoint: {endpoint}")
                    print(f"  Key: {key[:20]}...")
            
            # Check for endpoint and key secrets
            endpoint_secret = next((s for s in cosmos_secrets if 'endpoint' in s['name']), None)
            if endpoint_secret:
                print(f"\n{GREEN}Cosmos DB endpoint found:{NC}")
                print(f"  Name: {endpoint_secret['name']}")
                print(f"  Value: {endpoint_secret['value']}")
        else:
            print(f"{YELLOW}No Cosmos DB related secrets found in Key Vault{NC}")
        
        # Create .env file with the secrets
        print(f"\n{CYAN}Creating .env file with retrieved secrets...{NC}")
        env_file_path = Path(__file__).parent / 'cosmos_secrets.env'
        
        with open(env_file_path, 'w') as f:
            f.write("# Azure Key Vault Secrets\n")
            f.write(f"# Retrieved from: {key_vault_name}\n")
            f.write(f"# Generated on: {datetime.now().isoformat()}\n\n")
            
            # Write Cosmos DB specific variables if found
            if cosmos_secrets:
                f.write("# Cosmos DB Configuration\n")
                for secret in cosmos_secrets:
                    env_var_name = secret['name'].upper().replace('-', '_')
                    f.write(f"{env_var_name}=\"{secret['value']}\"\n")
                
                # If we parsed endpoint and key, add them as well
                if connection_string_secret and 'AccountEndpoint=' in connection_string_secret['value']:
                    f.write("\n# Parsed from connection string\n")
                    f.write(f"CEO_LOGS_COSMOS_ENDPOINT=\"{endpoint}\"\n")
                    f.write(f"CEO_LOGS_COSMOS_KEY=\"{key}\"\n")
                    f.write(f"DEFAULT_COSMOS_ENDPOINT=\"{endpoint}\"\n")
                    f.write(f"DEFAULT_COSMOS_KEY=\"{key}\"\n")
            
            f.write("\n# All other secrets\n")
            for secret in secrets_found:
                if secret not in cosmos_secrets:
                    env_var_name = secret['name'].upper().replace('-', '_')
                    f.write(f"{env_var_name}=\"{secret['value']}\"\n")
        
        print(f"{GREEN}✅ Secrets saved to: {env_file_path}{NC}")
        
    except Exception as e:
        print(f"{RED}Error accessing Key Vault: {e}{NC}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    from datetime import datetime
    retrieve_all_secrets()