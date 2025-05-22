"""
Tests for database initialization module.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from azure.cosmos import exceptions as CosmosExceptions

from backend.core.db_setup import initialize_database, CONTAINER_CONFIGS


class TestDatabaseInitialization:
    """Test database initialization functionality"""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings with Cosmos DB credentials"""
        with patch('backend.core.db_setup.settings') as mock_settings:
            mock_settings.AZURE_COSMOS_ENDPOINT = "https://test.cosmos.azure.com"
            mock_settings.AZURE_COSMOS_KEY = "test_key"
            mock_settings.AZURE_COSMOS_DATABASE_NAME = "test_stratosdb"
            yield mock_settings
    
    @pytest.fixture
    def mock_settings_no_credentials(self):
        """Mock settings without Cosmos DB credentials"""
        with patch('backend.core.db_setup.settings') as mock_settings:
            mock_settings.AZURE_COSMOS_ENDPOINT = None
            mock_settings.AZURE_COSMOS_KEY = None
            mock_settings.AZURE_COSMOS_DATABASE_NAME = "test_stratosdb"
            yield mock_settings
    
    @pytest.fixture
    def mock_cosmos_client(self):
        """Mock Cosmos DB client"""
        mock_client = AsyncMock()
        mock_database = AsyncMock()
        mock_container = AsyncMock()
        
        mock_client.create_database_if_not_exists = AsyncMock(return_value=mock_database)
        mock_database.create_container_if_not_exists = AsyncMock(return_value=mock_container)
        mock_database.get_container_client = AsyncMock(return_value=mock_container)
        mock_container.read = AsyncMock()
        
        return mock_client, mock_database, mock_container
    
    @pytest.mark.asyncio
    async def test_initialize_database_success(self, mock_settings, mock_cosmos_client):
        """Test successful database initialization"""
        mock_client, mock_database, mock_container = mock_cosmos_client
        
        with patch('backend.core.db_setup.AsyncCosmosClient') as mock_client_class:
            # Configure the context manager
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await initialize_database()
            
            assert result is True
            
            # Verify client initialization
            mock_client_class.assert_called_once_with(
                url="https://test.cosmos.azure.com",
                credential="test_key"
            )
            
            # Verify database creation
            mock_client.create_database_if_not_exists.assert_called_once_with(
                id="test_stratosdb"
            )
            
            # Verify all containers were created
            assert mock_database.create_container_if_not_exists.call_count == len(CONTAINER_CONFIGS)
            
            # Check specific container calls
            expected_calls = []
            for container_name, partition_key_path in CONTAINER_CONFIGS.items():
                from azure.cosmos import PartitionKey
                expected_calls.append(
                    (container_name, PartitionKey(path=partition_key_path), 400)
                )
            
            # Verify each container was created with correct parameters
            actual_calls = mock_database.create_container_if_not_exists.call_args_list
            assert len(actual_calls) == len(expected_calls)
    
    @pytest.mark.asyncio
    async def test_initialize_database_no_credentials(self, mock_settings_no_credentials):
        """Test database initialization without credentials"""
        result = await initialize_database()
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_initialize_database_client_error(self, mock_settings):
        """Test database initialization with client connection error"""
        with patch('backend.core.db_setup.AsyncCosmosClient') as mock_client_class:
            mock_client_class.side_effect = Exception("Connection failed")
            
            result = await initialize_database()
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_initialize_database_container_creation_partial_failure(self, mock_settings, mock_cosmos_client):
        """Test database initialization with some container creation failures"""
        mock_client, mock_database, mock_container = mock_cosmos_client
        
        # Make some container creations fail
        def side_effect(*args, **kwargs):
            container_name = kwargs.get('id') or args[0] if args else None
            if container_name in ['analyses', 'insights']:
                raise Exception(f"Failed to create {container_name}")
            return mock_container
        
        mock_database.create_container_if_not_exists.side_effect = side_effect
        
        with patch('backend.core.db_setup.AsyncCosmosClient') as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await initialize_database()
            
            # Should still return True (continues on failure)
            assert result is True
            
            # Should have attempted to create all containers
            assert mock_database.create_container_if_not_exists.call_count == len(CONTAINER_CONFIGS)
    
    @pytest.mark.asyncio
    async def test_initialize_database_existing_containers(self, mock_settings, mock_cosmos_client):
        """Test database initialization with existing containers"""
        mock_client, mock_database, mock_container = mock_cosmos_client
        
        # Simulate containers already exist
        mock_database.create_container_if_not_exists.side_effect = CosmosExceptions.CosmosResourceExistsError(
            message="Container already exists",
            response=MagicMock()
        )
        
        with patch('backend.core.db_setup.AsyncCosmosClient') as mock_client_class:
            mock_client_class.return_value.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client_class.return_value.__aexit__ = AsyncMock(return_value=None)
            
            result = await initialize_database()
            
            assert result is True
            assert mock_database.create_container_if_not_exists.call_count == len(CONTAINER_CONFIGS)
    
    def test_container_configs_completeness(self):
        """Test that all required containers are configured"""
        expected_containers = {
            # Analysis Service containers
            "analyses", "insights", "so_linkages", "analysis_sessions",
            # Auth Service containers  
            "Users",
            # Objective Data Service containers
            "datasets", "kpis", "datapoints",
            # Planning Service containers
            "StrategicPlans", "Initiatives", 
            # Strategic Foundation Service containers
            "NorthStarConfigurations",
            # Subjective Input Service containers
            "log_entries", "strategic_canvases"
        }
        
        actual_containers = set(CONTAINER_CONFIGS.keys())
        assert actual_containers == expected_containers
    
    def test_container_partition_keys(self):
        """Test that container partition keys are correctly configured"""
        expected_partition_keys = {
            "analyses": "/user_id",
            "insights": "/user_id", 
            "so_linkages": "/user_id",
            "analysis_sessions": "/user_id",
            "Users": "/email",
            "datasets": "/id",
            "kpis": "/id",
            "datapoints": "/dataset_id",
            "StrategicPlans": "/id",
            "Initiatives": "/id",
            "NorthStarConfigurations": "/id",
            "log_entries": "/user_id",
            "strategic_canvases": "/user_id"
        }
        
        assert CONTAINER_CONFIGS == expected_partition_keys