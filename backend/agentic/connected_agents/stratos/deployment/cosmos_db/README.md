# Cosmos DB Setup Scripts for CEO Log Agent

This directory contains all the scripts needed to provision and configure Azure Cosmos DB for the CEO Log connected agent.

## 🚀 Quick Start

Run the complete setup with a single command:

```bash
# Install dependencies
pip install -r requirements.txt

# Run complete setup
./setup_cosmos_db_complete.sh
```

This will automatically:
1. Provision Cosmos DB infrastructure
2. Configure security (Azure AD, RBAC, Key Vault)
3. Create schema and stored procedures
4. Test the connection and validate setup

## 📋 Prerequisites

Before running these scripts, ensure you have:

1. **Azure CLI installed and logged in**:
   ```bash
   az login
   ```

2. **Required permissions**:
   - Contributor access to the resource group
   - Key Vault Secrets Officer role
   - User Access Administrator (for RBAC assignments)

3. **Python 3.8+ with required packages**:
   ```bash
   pip install azure-cosmos azure-identity azure-keyvault-secrets
   ```

## 🚀 Quick Start

Run the scripts in this order:

### 1. Provision Cosmos DB Infrastructure
```bash
chmod +x provision_cosmos_db.sh
./provision_cosmos_db.sh
```

This script will:
- ✅ Create Cosmos DB account with SQL API
- ✅ Create database `StratOSData`
- ✅ Create container `CEOLogs` with `/userId` partition key
- ✅ Configure Azure AD authentication
- ✅ Store credentials in Key Vault
- ✅ Create service principal for the agent

**Expected duration**: 5-10 minutes

### 2. Configure Security Settings
```bash
python configure_cosmos_security.py
```

This script will:
- ✅ Set up managed identity for CEO Log Agent
- ✅ Configure RBAC permissions
- ✅ Enable diagnostic logging
- ✅ Set up continuous backup
- ✅ Create custom access policies

**Output files**:
- `cosmos_security_report.json` - Security configuration summary

### 3. Create Schema and Stored Procedures
```bash
python create_schema_stored_procedures.py
```

This script will:
- ✅ Create stored procedures for complex operations
- ✅ Set up validation triggers
- ✅ Create sample documents for testing
- ✅ Generate schema documentation

**Output files**:
- `ceo_log_schema_documentation.json` - Complete schema reference
- `CEO_LOG_SCHEMA_README.md` - Human-readable documentation

### 4. Test the Connection
```bash
python test_cosmos_connection.py
```

This script will:
- ✅ Verify Key Vault access
- ✅ Test Cosmos DB connection
- ✅ Validate CRUD operations
- ✅ Test stored procedures
- ✅ Check query performance

**Output files**:
- `cosmos_db_test_results.json` - Detailed test results

## 📁 Script Details

### `provision_cosmos_db.sh`
Main provisioning script that creates all Azure resources. Key features:
- Idempotent (safe to run multiple times)
- Automatic retry on transient failures
- Comprehensive error handling
- Progress indicators

### `configure_cosmos_security.py`
Security configuration script that sets up:
- Managed identities
- RBAC roles and assignments
- Network security rules
- Diagnostic settings
- Backup policies

### `create_schema_stored_procedures.py`
Schema management script that creates:
- **Stored Procedures**:
  - `bulkCreateLogs` - Bulk insert CEO log entries
  - `getLogsSummary` - Generate usage statistics
  - `searchLogsWithHighlights` - Full-text search with highlighting
  - `aggregateStrategicInsights` - Analyze themes and patterns

- **Triggers**:
  - `validateLogEntry` - Pre-create validation
  - `updateModifiedTime` - Pre-update timestamp management

### `test_cosmos_connection.py`
Comprehensive testing script that validates:
- Authentication and authorization
- Database connectivity
- CRUD operations
- Stored procedure execution
- Query performance

## 🔐 Security Configuration

After running all scripts, the following security measures will be in place:

1. **Authentication**: Azure AD with managed identities
2. **Authorization**: RBAC with custom roles
3. **Encryption**: At rest and in transit
4. **Network**: IP firewall rules
5. **Backup**: Continuous with 7-day retention
6. **Monitoring**: Azure Monitor integration

## 📊 Document Schema

The CEO Log documents follow this structure:

```json
{
  "id": "unique-guid",
  "userId": "user-identifier",
  "timestamp": "2025-05-28T20:30:00Z",
  "logEntry": {
    "content": "CEO log text content",
    "sentiment": "positive|negative|neutral",
    "confidence": 0.85
  },
  "tags": ["tag1", "tag2"],
  "strategicThemes": ["theme1", "theme2"],
  "metadata": {
    "source": "voice|text|meeting",
    "duration": 120,
    "location": "office"
  },
  "analysis": {
    "keyInsights": ["insight1", "insight2"],
    "actionItems": ["action1", "action2"],
    "riskFactors": ["risk1"]
  },
  "createdBy": "CEOLogAgent",
  "createdAt": "2025-05-28T20:30:00Z",
  "modifiedAt": "2025-05-28T20:30:00Z",
  "version": 1
}
```

## 🔧 Configuration Files

After successful setup, you'll have:

1. **cosmos_db_config.json** - Database configuration details
2. **cosmos_security_report.json** - Security audit report
3. **ceo_log_schema_documentation.json** - Complete schema reference
4. **cosmos_db_test_results.json** - Connection test results

## 🚨 Troubleshooting

### Common Issues

1. **Authentication Errors**:
   ```bash
   az account show  # Verify you're logged in
   az account set --subscription <subscription-id>  # Switch subscriptions
   ```

2. **Permission Errors**:
   Ensure your account has the required roles:
   ```bash
   az role assignment list --assignee $(az ad signed-in-user show --query id -o tsv)
   ```

3. **Key Vault Access**:
   ```bash
   az keyvault secret list --vault-name stratos-keyvault
   ```

4. **Network Issues**:
   The scripts automatically add your current IP to the firewall. If your IP changes:
   ```bash
   az cosmosdb update --name stratos-ceo-logs-db \
     --resource-group semantic-kernel-multi-agent-rg \
     --ip-range-filter "$(curl -s https://api.ipify.org)"
   ```

## 📈 Monitoring

After setup, monitor your Cosmos DB instance:

1. **Azure Portal**: Navigate to your Cosmos DB account
2. **Metrics**: View RU consumption, latency, and availability
3. **Diagnostics**: Check Log Analytics for query patterns
4. **Alerts**: Set up alerts for high RU usage or errors

## 🔄 Maintenance

Regular maintenance tasks:

1. **Monitor RU usage** and scale as needed
2. **Review security permissions** quarterly
3. **Update IP firewall rules** as needed
4. **Check backup retention** settings
5. **Analyze query patterns** for optimization

## 📞 Support

For issues or questions:
1. Check the test results in `cosmos_db_test_results.json`
2. Review logs in Azure Monitor
3. Consult the schema documentation
4. Contact the StratOS team

## ✅ Next Steps

After successful setup:

1. Update the CEO Log Agent configuration with the Key Vault URL
2. Deploy the updated agent with Cosmos DB integration
3. Test the agent with sample queries
4. Monitor performance and adjust RU allocation as needed

Happy logging! 🎉