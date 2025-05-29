#!/usr/bin/env python3
"""
Test Cosmos DB Connection and Operations
Verify that everything is configured correctly
"""

import os
import json
import asyncio
from datetime import datetime
from azure.cosmos.aio import CosmosClient
from azure.identity.aio import DefaultAzureCredential
from azure.keyvault.secrets.aio import SecretClient
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CosmosDBTester:
    def __init__(self):
        self.config = {
            "database_name": "StratOSData",
            "container_name": "CEOLogs",
            "key_vault_name": "stratos-keyvault"
        }
        self.test_results = {
            "timestamp": datetime.utcnow().isoformat(),
            "tests": {},
            "summary": {
                "total": 0,
                "passed": 0,
                "failed": 0
            }
        }
    
    def record_test(self, test_name: str, passed: bool, details: str = ""):
        """Record test result"""
        self.test_results["tests"][test_name] = {
            "passed": passed,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.test_results["summary"]["total"] += 1
        if passed:
            self.test_results["summary"]["passed"] += 1
        else:
            self.test_results["summary"]["failed"] += 1
        
        # Print result
        status = "✅ PASS" if passed else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
        if details:
            logger.info(f"      {details}")
    
    async def test_key_vault_access(self):
        """Test Key Vault access"""
        logger.info("\n1️⃣ Testing Key Vault Access...")
        
        try:
            credential = DefaultAzureCredential()
            keyvault_url = f"https://{self.config['key_vault_name']}.vault.azure.net"
            
            async with SecretClient(vault_url=keyvault_url, credential=credential) as client:
                # List secrets
                secrets = []
                async for secret in client.list_properties_of_secrets():
                    secrets.append(secret.name)
                
                required_secrets = [
                    "cosmos-db-connection-string",
                    "cosmos-db-endpoint"
                ]
                
                missing = [s for s in required_secrets if s not in secrets]
                
                if missing:
                    self.record_test(
                        "Key Vault Access",
                        False,
                        f"Missing secrets: {missing}"
                    )
                else:
                    self.record_test(
                        "Key Vault Access",
                        True,
                        f"Found {len(secrets)} secrets"
                    )
                    return True
                    
        except Exception as e:
            self.record_test("Key Vault Access", False, str(e))
            return False
    
    async def test_cosmos_connection(self):
        """Test Cosmos DB connection"""
        logger.info("\n2️⃣ Testing Cosmos DB Connection...")
        
        try:
            credential = DefaultAzureCredential()
            keyvault_url = f"https://{self.config['key_vault_name']}.vault.azure.net"
            
            # Get endpoint from Key Vault
            async with SecretClient(vault_url=keyvault_url, credential=credential) as secret_client:
                endpoint_secret = await secret_client.get_secret("cosmos-db-endpoint")
                endpoint = endpoint_secret.value
            
            # Connect to Cosmos DB
            async with CosmosClient(endpoint, credential=credential) as client:
                # List databases
                databases = []
                async for db in client.list_databases():
                    databases.append(db['id'])
                
                if self.config['database_name'] in databases:
                    self.record_test(
                        "Cosmos DB Connection",
                        True,
                        f"Connected to {endpoint}"
                    )
                    return True
                else:
                    self.record_test(
                        "Cosmos DB Connection",
                        False,
                        f"Database '{self.config['database_name']}' not found"
                    )
                    
        except Exception as e:
            self.record_test("Cosmos DB Connection", False, str(e))
            return False
    
    async def test_container_operations(self):
        """Test container operations"""
        logger.info("\n3️⃣ Testing Container Operations...")
        
        try:
            credential = DefaultAzureCredential()
            keyvault_url = f"https://{self.config['key_vault_name']}.vault.azure.net"
            
            async with SecretClient(vault_url=keyvault_url, credential=credential) as secret_client:
                endpoint_secret = await secret_client.get_secret("cosmos-db-endpoint")
                endpoint = endpoint_secret.value
            
            async with CosmosClient(endpoint, credential=credential) as client:
                database = client.get_database_client(self.config['database_name'])
                container = database.get_container_client(self.config['container_name'])
                
                # Test 1: Create a document
                test_doc = {
                    "id": f"test-{datetime.utcnow().timestamp()}",
                    "userId": "test-user",
                    "timestamp": datetime.utcnow().isoformat(),
                    "logEntry": {
                        "content": "This is a test CEO log entry",
                        "sentiment": "neutral"
                    },
                    "tags": ["test"],
                    "createdAt": datetime.utcnow().isoformat(),
                    "createdBy": "ConnectionTester"
                }
                
                created_doc = await container.create_item(body=test_doc)
                self.record_test(
                    "Create Document",
                    True,
                    f"Created doc ID: {created_doc['id']}"
                )
                
                # Test 2: Read the document
                read_doc = await container.read_item(
                    item=created_doc['id'],
                    partition_key="test-user"
                )
                self.record_test(
                    "Read Document",
                    True,
                    f"Read doc with {len(read_doc)} fields"
                )
                
                # Test 3: Query documents
                query = "SELECT * FROM c WHERE c.userId = @userId"
                parameters = [{"name": "@userId", "value": "test-user"}]
                
                items = []
                async for item in container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=True
                ):
                    items.append(item)
                
                self.record_test(
                    "Query Documents",
                    True,
                    f"Found {len(items)} documents"
                )
                
                # Test 4: Delete test document
                await container.delete_item(
                    item=created_doc['id'],
                    partition_key="test-user"
                )
                self.record_test("Delete Document", True, "Cleanup successful")
                
                return True
                
        except Exception as e:
            self.record_test("Container Operations", False, str(e))
            return False
    
    async def test_stored_procedures(self):
        """Test stored procedures"""
        logger.info("\n4️⃣ Testing Stored Procedures...")
        
        try:
            credential = DefaultAzureCredential()
            keyvault_url = f"https://{self.config['key_vault_name']}.vault.azure.net"
            
            async with SecretClient(vault_url=keyvault_url, credential=credential) as secret_client:
                endpoint_secret = await secret_client.get_secret("cosmos-db-endpoint")
                endpoint = endpoint_secret.value
            
            async with CosmosClient(endpoint, credential=credential) as client:
                database = client.get_database_client(self.config['database_name'])
                container = database.get_container_client(self.config['container_name'])
                
                # List stored procedures
                sprocs = []
                async for sp in container.scripts.list_stored_procedures():
                    sprocs.append(sp['id'])
                
                expected_sprocs = [
                    "bulkCreateLogs",
                    "getLogsSummary",
                    "searchLogsWithHighlights",
                    "aggregateStrategicInsights"
                ]
                
                missing = [sp for sp in expected_sprocs if sp not in sprocs]
                
                if missing:
                    self.record_test(
                        "Stored Procedures",
                        False,
                        f"Missing: {missing}"
                    )
                else:
                    self.record_test(
                        "Stored Procedures",
                        True,
                        f"All {len(expected_sprocs)} procedures found"
                    )
                    
                    # Test executing a stored procedure
                    try:
                        result = await container.scripts.execute_stored_procedure(
                            sproc="getLogsSummary",
                            params=["test-user", 30],
                            partition_key="test-user"
                        )
                        self.record_test(
                            "Execute Stored Procedure",
                            True,
                            "getLogsSummary executed successfully"
                        )
                    except Exception as e:
                        self.record_test(
                            "Execute Stored Procedure",
                            False,
                            str(e)
                        )
                
                return True
                
        except Exception as e:
            self.record_test("Stored Procedures", False, str(e))
            return False
    
    async def test_performance(self):
        """Test query performance"""
        logger.info("\n5️⃣ Testing Query Performance...")
        
        try:
            credential = DefaultAzureCredential()
            keyvault_url = f"https://{self.config['key_vault_name']}.vault.azure.net"
            
            async with SecretClient(vault_url=keyvault_url, credential=credential) as secret_client:
                endpoint_secret = await secret_client.get_secret("cosmos-db-endpoint")
                endpoint = endpoint_secret.value
            
            async with CosmosClient(endpoint, credential=credential) as client:
                database = client.get_database_client(self.config['database_name'])
                container = database.get_container_client(self.config['container_name'])
                
                # Test query performance
                start_time = datetime.utcnow()
                
                query = """
                SELECT TOP 10 * FROM c 
                WHERE c.userId = @userId 
                ORDER BY c.timestamp DESC
                """
                parameters = [{"name": "@userId", "value": "sample-user"}]
                
                items = []
                async for item in container.query_items(
                    query=query,
                    parameters=parameters,
                    enable_cross_partition_query=False  # Use partition key
                ):
                    items.append(item)
                
                elapsed = (datetime.utcnow() - start_time).total_seconds()
                
                if elapsed < 2.0:  # Target: under 2 seconds
                    self.record_test(
                        "Query Performance",
                        True,
                        f"Query completed in {elapsed:.2f}s"
                    )
                else:
                    self.record_test(
                        "Query Performance",
                        False,
                        f"Query took {elapsed:.2f}s (target: <2s)"
                    )
                
                return True
                
        except Exception as e:
            self.record_test("Query Performance", False, str(e))
            return False
    
    def generate_report(self):
        """Generate test report"""
        logger.info("\n" + "="*60)
        logger.info("TEST SUMMARY")
        logger.info("="*60)
        
        summary = self.test_results["summary"]
        logger.info(f"Total Tests: {summary['total']}")
        logger.info(f"Passed: {summary['passed']} ✅")
        logger.info(f"Failed: {summary['failed']} ❌")
        logger.info(f"Success Rate: {(summary['passed']/summary['total']*100):.1f}%")
        
        # Save detailed report
        with open('cosmos_db_test_results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2)
        
        logger.info("\nDetailed results saved to cosmos_db_test_results.json")
        
        # Generate recommendations
        if summary['failed'] > 0:
            logger.info("\n⚠️  RECOMMENDATIONS:")
            for test_name, result in self.test_results["tests"].items():
                if not result["passed"]:
                    logger.info(f"  - Fix: {test_name}")
                    logger.info(f"    Error: {result['details']}")
    
    async def run_all_tests(self):
        """Run all tests"""
        logger.info("🧪 COSMOS DB CONNECTION TESTS")
        logger.info("="*60)
        
        # Run tests in sequence
        await self.test_key_vault_access()
        await self.test_cosmos_connection()
        await self.test_container_operations()
        await self.test_stored_procedures()
        await self.test_performance()
        
        # Generate report
        self.generate_report()
        
        # Return success if all tests passed
        return self.test_results["summary"]["failed"] == 0

async def main():
    """Main test runner"""
    tester = CosmosDBTester()
    success = await tester.run_all_tests()
    
    if success:
        logger.info("\n✅ All tests passed! Cosmos DB is ready for CEO Log Agent.")
    else:
        logger.info("\n❌ Some tests failed. Please review the recommendations above.")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())