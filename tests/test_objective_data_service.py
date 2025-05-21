import pytest
import pytest_asyncio
from uuid import uuid4, UUID
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import HTTPException, UploadFile

from backend.services.objective_data_service import ObjectiveDataService
from backend.models.objective_data import (
    DataSetCreate, DataSet, 
    KPICreate, KPI, 
    DataPointCreate, DataPoint,
    DataSourceType, DataCategory
)

@pytest_asyncio.fixture
async def objective_service():
    service = ObjectiveDataService()
    # Mock Azure clients and ensure in-memory behavior if not already default
    # For service-level tests, we often mock the direct client calls.
    # The service already has initialize_blob_storage and initialize_cosmos_db
    # which set up client proxies. We'll mock these to prevent actual Azure calls.
    
    service.blob_service_client = AsyncMock()
    service.blob_container_client = AsyncMock()
    
    service.cosmos_client = AsyncMock()
    service.database = AsyncMock()
    service.datasets_container = AsyncMock(spec_set=['read_item', 'query_items', 'create_item', 'replace_item', 'delete_item'])
    service.kpis_container = AsyncMock(spec_set=['read_item', 'query_items', 'create_item', 'replace_item', 'delete_item'])
    service.datapoints_container = AsyncMock(spec_set=['read_item', 'query_items', 'create_item', 'replace_item', 'delete_item'])

    # Simulate successful initialization for tests that don't focus on init itself
    service.blob_storage_initialized = True
    service.cosmos_db_initialized = True
    
    # Mock the initialize methods to prevent them from running real connections
    # and to ensure they return True for tests that might call them.
    # Also, ensure the container attributes are set.
    async def mock_init_blob():
        service.blob_service_client = AsyncMock()
        service.blob_container_client = service.blob_service_client.get_container_client.return_value
        return True
    
    async def mock_init_cosmos():
        service.cosmos_client = AsyncMock()
        service.database = service.cosmos_client.get_database_client.return_value
        service.datasets_container = service.database.get_container_client.return_value
        service.kpis_container = service.database.get_container_client.return_value
        service.datapoints_container = service.database.get_container_client.return_value
        return True

    monkeypatch = pytest.MonkeyPatch() # Using monkeypatch from pytest
    monkeypatch.setattr(service, 'initialize_blob_storage', mock_init_blob)
    monkeypatch.setattr(service, 'initialize_cosmos_db', mock_init_cosmos)
    
    # Call them once to set up the mocks if service logic depends on these being called
    await service.initialize_blob_storage()
    await service.initialize_cosmos_db()

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
    
    # Mock the create_item call on the datasets_container
    objective_service.datasets_container.create_item = AsyncMock()
    
    created_dataset = await objective_service.create_dataset(dataset_data)
    
    assert created_dataset is not None
    assert created_dataset.name == dataset_data.name
    assert created_dataset.category == DataCategory.FINANCIAL
    assert created_dataset.source_type == DataSourceType.MANUAL
    assert "manual" in created_dataset.tags
    objective_service.datasets_container.create_item.assert_called_once()

@pytest.mark.asyncio
async def test_get_dataset_found(objective_service: ObjectiveDataService):
    dataset_id = uuid4()
    mock_item = {
        "id": str(dataset_id), "name": "Found Dataset", "category": "sales", 
        "source_type": "upload", "created_at": datetime.now().isoformat(), 
        "updated_at": datetime.now().isoformat(), "tags": [], "linked_strategic_elements": []
    }
    objective_service.datasets_container.read_item = AsyncMock(return_value=mock_item)
    
    dataset = await objective_service.get_dataset(dataset_id)
    
    assert dataset is not None
    assert dataset.id == dataset_id
    assert dataset.name == "Found Dataset"
    objective_service.datasets_container.read_item.assert_called_with(item=str(dataset_id), partition_key=str(dataset_id))

@pytest.mark.asyncio
async def test_list_datasets(objective_service: ObjectiveDataService):
    dataset_id1 = uuid4()
    dataset_id2 = uuid4()
    mock_items = [
        {"id": str(dataset_id1), "name": "Dataset 1", "category": "marketing", "source_type": "api", "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat(), "tags": [], "linked_strategic_elements": []},
        {"id": str(dataset_id2), "name": "Dataset 2", "category": "operations", "source_type": "manual", "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat(), "tags": [], "linked_strategic_elements": []}
    ]
    
    # Mock query_items to be an async iterable
    async def mock_query_items_async(*args, **kwargs):
        for item in mock_items:
            yield item
            
    objective_service.datasets_container.query_items = mock_query_items_async
    
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
    assert created_kpi.current_value == 0.15
    objective_service.kpis_container.create_item.assert_called_once()

@pytest.mark.asyncio
async def test_get_kpi_found(objective_service: ObjectiveDataService):
    kpi_id = uuid4()
    mock_item = {
        "id": str(kpi_id), "name": "Found KPI", "category": "sales", 
        "current_value": 100, "created_at": datetime.now().isoformat(), 
        "updated_at": datetime.now().isoformat(), "linked_goals": []
    }
    objective_service.kpis_container.read_item = AsyncMock(return_value=mock_item)
    
    kpi = await objective_service.get_kpi(kpi_id)
    
    assert kpi is not None
    assert kpi.id == kpi_id
    assert kpi.name == "Found KPI"
    objective_service.kpis_container.read_item.assert_called_with(item=str(kpi_id), partition_key=str(kpi_id))

# --- DataPoint Tests ---
@pytest.mark.asyncio
async def test_create_datapoint(objective_service: ObjectiveDataService):
    dataset_id = uuid4()
    # Mock get_dataset to return a valid dataset
    objective_service.get_dataset = AsyncMock(return_value=DataSet(id=dataset_id, name="Test DS", category=DataCategory.OTHER, source_type=DataSourceType.MANUAL))
    
    datapoint_data = DataPointCreate(
        dataset_id=str(dataset_id),
        timestamp=datetime.now(),
        dimension={"region": "North"},
        metrics={"sales": 1000}
    )
    objective_service.datapoints_container.create_item = AsyncMock()
    
    created_dp = await objective_service.create_datapoint(datapoint_data)
    
    assert created_dp is not None
    assert created_dp.dataset_id == dataset_id
    assert created_dp.metrics["sales"] == 1000
    objective_service.datapoints_container.create_item.assert_called_once()

@pytest.mark.asyncio
async def test_list_datapoints(objective_service: ObjectiveDataService):
    dataset_id = uuid4()
    dp_id1 = uuid4()
    mock_items = [
        {"id": str(dp_id1), "dataset_id": str(dataset_id), "timestamp": datetime.now().isoformat(), "dimension": {}, "metrics": {"value": 10}, "created_at": datetime.now().isoformat(), "updated_at": datetime.now().isoformat()}
    ]
    
    async def mock_query_items_async(*args, **kwargs):
        for item in mock_items:
            yield item
            
    objective_service.datapoints_container.query_items = mock_query_items_async
    
    datapoints = await objective_service.list_datapoints(dataset_id)
    assert len(datapoints) == 1
    assert datapoints[0].id == dp_id1

# Mocking file processing and AI indexing for a basic test of process_uploaded_file
@pytest.mark.asyncio
@patch('backend.services.objective_data_service.ObjectiveDataService._upload_to_blob_storage', new_callable=AsyncMock)
@patch('backend.services.objective_data_service.asyncio.create_task') # Mock asyncio.create_task
async def test_process_uploaded_file_flow(mock_create_task: MagicMock, mock_upload_blob: AsyncMock, objective_service: ObjectiveDataService):
    mock_upload_blob.return_value = "http://fakeblob.com/file.pdf"
    
    # Mock the dataset creation in DB
    objective_service.datasets_container.create_item = AsyncMock()
    
    # Mock UploadFile
    mock_file = AsyncMock(spec=UploadFile)
    mock_file.filename = "test.pdf"
    mock_file.size = 1024
    
    dataset_create_data = DataSetCreate(
        name="Uploaded PDF",
        description="Test PDF upload",
        category=DataCategory.OTHER,
        source_type=DataSourceType.UPLOAD,
        data_format="pdf" # This should be set by the router usually
    )
    
    created_dataset = await objective_service.process_uploaded_file(mock_file, dataset_create_data)
    
    assert created_dataset is not None
    assert created_dataset.name == "Uploaded PDF"
    assert created_dataset.file_path == "http://fakeblob.com/file.pdf"
    assert created_dataset.metadata["original_filename"] == "test.pdf"
    
    mock_upload_blob.assert_called_once()
    objective_service.datasets_container.create_item.assert_called_once()
    mock_create_task.assert_called_once() # Check that background processing was initiated
