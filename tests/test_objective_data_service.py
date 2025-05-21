import pytest
import pytest_asyncio
from uuid import uuid4, UUID
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException, UploadFile
from azure.cosmos.aio import DatabaseProxy, ContainerProxy # Added imports

from backend.services.objective_data_service import ObjectiveDataService
from backend.models.objective_data import (
    DataSetCreate, DataSet, 
    KPICreate, KPI, 
    DataPointCreate, DataPoint,
    DataSourceType, DataCategory
)

@pytest_asyncio.fixture
async def objective_service(monkeypatch: pytest.MonkeyPatch): # Added monkeypatch as arg
    service = ObjectiveDataService()
    # Mock Azure clients
    service.blob_service_client = AsyncMock()
    service.blob_container_client = AsyncMock()
    
    service.cosmos_client = AsyncMock()
    # These are the mock objects that the tests will configure (e.g., set return_value for read_item)
    # The service's own self.datasets_container will be pointed to these by the mocked init.
    mock_datasets_container = AsyncMock(spec=ContainerProxy)
    mock_kpis_container = AsyncMock(spec=ContainerProxy)
    mock_datapoints_container = AsyncMock(spec=ContainerProxy)

    # Mock the database proxy that get_container_client is called on
    mock_db_proxy = AsyncMock(spec=DatabaseProxy)
    
    # This side effect ensures that when the service calls self.database.get_container_client,
    # it receives our specific mock container instances.
    def get_container_client_side_effect(container_id):
        if container_id == service.cosmos_datasets_container: # service.cosmos_datasets_container holds the name
            return mock_datasets_container
        elif container_id == service.cosmos_kpis_container:
            return mock_kpis_container
        elif container_id == service.cosmos_datapoints_container:
            return mock_datapoints_container
        return AsyncMock(spec=ContainerProxy) # Default for any other unexpected calls

    mock_db_proxy.get_container_client = MagicMock(side_effect=get_container_client_side_effect)

    # This is the function that will run when service.initialize_cosmos_db() is called
    # It sets up the service's internal self.database and self.xyz_container attributes
    # to point to our mocks.
    async def actual_mock_init_cosmos(self_service_instance): # 'self_service_instance' is the service instance
        self_service_instance.cosmos_client = AsyncMock() # Mock the client on the instance
        self_service_instance.database = mock_db_proxy   # Assign our mocked db_proxy
        
        # Call the service's own _init_container method, which will now use the mocked get_container_client
        # This ensures self.datasets_container etc. on the service instance are set to our mocks.
        await self_service_instance._init_container(self_service_instance.cosmos_datasets_container, "/id")
        await self_service_instance._init_container(self_service_instance.cosmos_kpis_container, "/id")
        await self_service_instance._init_container(self_service_instance.cosmos_datapoints_container, "/dataset_id")
        
        self_service_instance.cosmos_db_initialized = True
        return True

    async def actual_mock_init_blob(self_service_instance):
        self_service_instance.blob_service_client = AsyncMock()
        self_service_instance.blob_container_client = self_service_instance.blob_service_client.get_container_client.return_value
        self_service_instance.blob_storage_initialized = True
        return True

    # Patch the initialize methods on the class to use our wrappers
    monkeypatch.setattr(ObjectiveDataService, 'initialize_blob_storage', actual_mock_init_blob)
    monkeypatch.setattr(ObjectiveDataService, 'initialize_cosmos_db', actual_mock_init_cosmos)
    
    # Now, when the service instance is created and its __init__ calls initialize_*, 
    # or when methods call initialize_*, they will use our patched versions.
    # We still need to call them once on the created 'service' instance to ensure it's set up
    # with our mocks before being yielded to the test.
    await service.initialize_blob_storage() # This will use the patched actual_mock_init_blob
    await service.initialize_cosmos_db()  # This will use the patched actual_mock_init_cosmos

    # The tests will then further mock methods on service.datasets_container etc.
    # e.g. service.datasets_container.read_item = async_def_returning_dict
    return service

# --- DataSet Tests ---
@pytest.mark.asyncio
async def test_create_dataset_manual(objective_service: ObjectiveDataService):
    dataset_data = DataSetCreate(
        name="Manual Dataset",
        category=DataCategory.FINANCIAL,
        source_type=DataSourceType.MANUAL,
        tags=["manual", "finance"]
    )
    
    objective_service.datasets_container.create_item = AsyncMock()
    
    created_dataset = await objective_service.create_dataset(dataset_data)
    
    assert created_dataset is not None
    assert created_dataset.name == dataset_data.name
    objective_service.datasets_container.create_item.assert_called_once()

@pytest.mark.asyncio
async def test_get_dataset_found(objective_service: ObjectiveDataService):
    dataset_id = uuid4()
    mock_item_dict = { # Ensure this is a plain dict
        "id": str(dataset_id), "name": "Found Dataset", "category": "sales", 
        "source_type": "upload", "created_at": datetime.now().isoformat(), 
        "updated_at": datetime.now().isoformat(), "tags": [], "linked_strategic_elements": []
    }
    # Replace with an AsyncMock instance that returns the dict
    objective_service.datasets_container.read_item = AsyncMock(return_value=mock_item_dict)
    
    dataset = await objective_service.get_dataset(dataset_id)
    
    assert dataset is not None
    assert dataset.id == dataset_id
    objective_service.datasets_container.read_item.assert_called_with(item=str(dataset_id), partition_key=str(dataset_id))

@pytest.mark.asyncio
async def test_list_datasets(objective_service: ObjectiveDataService):
    dataset_id1 = uuid4()
    dataset_id2 = uuid4()
    mock_items_list = [ # List of plain dicts
        {"id": str(dataset_id1), "name": "Dataset 1", "category": "marketing", "source_type": "api", "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat(), "tags": [], "linked_strategic_elements": []},
        {"id": str(dataset_id2), "name": "Dataset 2", "category": "operations", "source_type": "manual", "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat(), "tags": [], "linked_strategic_elements": []}
    ]
    
    class MockAsyncIterator:
        def __init__(self, items):
            self._items = iter(items)
        def __aiter__(self):
            return self
        async def __anext__(self):
            try:
                return next(self._items)
            except StopIteration:
                raise StopAsyncIteration
    
    objective_service.datasets_container.query_items = MagicMock(return_value=MockAsyncIterator(mock_items_list))
    
    datasets = await objective_service.list_datasets()
    assert len(datasets) == 2
    assert datasets[0].name == "Dataset 1"

# --- KPI Tests ---
@pytest.mark.asyncio
async def test_create_kpi(objective_service: ObjectiveDataService):
    kpi_data = KPICreate(
        name="Revenue Growth", 
        category=DataCategory.FINANCIAL, 
        current_value=0.15, 
        target_value=0.20, 
        unit="%"
    )
    objective_service.kpis_container.create_item = AsyncMock()
    created_kpi = await objective_service.create_kpi(kpi_data)
    assert created_kpi is not None
    assert created_kpi.name == kpi_data.name
    objective_service.kpis_container.create_item.assert_called_once()

@pytest.mark.asyncio
async def test_get_kpi_found(objective_service: ObjectiveDataService):
    kpi_id = uuid4()
    mock_kpi_item_dict = { # Plain dict
        "id": str(kpi_id), "name": "Found KPI", "category": "sales", 
        "current_value": 100, "created_at": datetime.now().isoformat(), 
        "updated_at": datetime.now().isoformat(), "linked_goals": []
    }
    # Replace with an AsyncMock instance that returns the dict
    objective_service.kpis_container.read_item = AsyncMock(return_value=mock_kpi_item_dict)
    
    kpi = await objective_service.get_kpi(kpi_id)
    assert kpi is not None
    assert kpi.id == kpi_id
    objective_service.kpis_container.read_item.assert_called_with(item=str(kpi_id), partition_key=str(kpi_id))

# --- DataPoint Tests ---
@pytest.mark.asyncio
async def test_create_datapoint(objective_service: ObjectiveDataService):
    dataset_id = uuid4()
    objective_service.get_dataset = AsyncMock(return_value=DataSet(id=dataset_id, name="Test DS", category=DataCategory.OTHER, source_type=DataSourceType.MANUAL))
    datapoint_data = DataPointCreate(
        dataset_id=str(dataset_id), timestamp=datetime.now(),
        dimension={"region": "North"}, metrics={"sales": 1000}
    )
    objective_service.datapoints_container.create_item = AsyncMock()
    created_dp = await objective_service.create_datapoint(datapoint_data)
    assert created_dp is not None
    assert created_dp.dataset_id == dataset_id
    objective_service.datapoints_container.create_item.assert_called_once()

@pytest.mark.asyncio
async def test_list_datapoints(objective_service: ObjectiveDataService):
    dataset_id = uuid4()
    dp_id1 = uuid4()
    mock_dp_items_list = [ # List of plain dicts
        {"id": str(dp_id1), "dataset_id": str(dataset_id), "timestamp": datetime.now().isoformat(), "dimension": {}, "metrics": {"value": 10}, "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()}
    ]
    
    class MockAsyncIteratorDP: # Defined locally for clarity
        def __init__(self, items):
            self._items = iter(items)
        def __aiter__(self):
            return self
        async def __anext__(self):
            try:
                return next(self._items)
            except StopIteration:
                raise StopAsyncIteration
                
    objective_service.datapoints_container.query_items = MagicMock(return_value=MockAsyncIteratorDP(mock_dp_items_list))
    
    datapoints = await objective_service.list_datapoints(dataset_id)
    assert len(datapoints) == 1
    assert datapoints[0].id == dp_id1

# Mocking file processing and AI indexing for a basic test of process_uploaded_file
@pytest.mark.asyncio
@patch('backend.services.objective_data_service.ObjectiveDataService._upload_to_blob_storage', new_callable=AsyncMock)
@patch('backend.services.objective_data_service.asyncio.create_task') # Mock asyncio.create_task
async def test_process_uploaded_file_flow(mock_create_task: MagicMock, mock_upload_blob: AsyncMock, objective_service: ObjectiveDataService):
    mock_upload_blob.return_value = "http://fakeblob.com/file.pdf"
    objective_service.datasets_container.create_item = AsyncMock()
    mock_file = AsyncMock(spec=UploadFile)
    mock_file.filename = "test.pdf"
    mock_file.size = 1024
    dataset_create_data = DataSetCreate(
        name="Uploaded PDF", description="Test PDF upload", category=DataCategory.OTHER,
        source_type=DataSourceType.UPLOAD, data_format="pdf"
    )
    created_dataset = await objective_service.process_uploaded_file(mock_file, dataset_create_data)
    assert created_dataset is not None
    assert created_dataset.name == "Uploaded PDF"
    mock_upload_blob.assert_called_once()
    objective_service.datasets_container.create_item.assert_called_once()
    mock_create_task.assert_called_once()
