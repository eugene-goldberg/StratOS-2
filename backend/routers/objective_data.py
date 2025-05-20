from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import List, Optional, Dict, Any
from uuid import UUID

from ..models.user import UserResponse
from ..dependencies import get_current_active_user
from ..models.objective_data import (
    KPI,
    KPICreate,
    DataSet,
    DataSetCreate,
    DataPoint,
    DataPointCreate,
    DataCategory,
    DataSourceType
)
from ..services.objective_data_service import ObjectiveDataService

router = APIRouter(dependencies=[Depends(get_current_active_user)])
data_service = ObjectiveDataService()

# KPI Endpoints

@router.post("/kpis", response_model=KPI, status_code=status.HTTP_201_CREATED)
async def create_kpi(kpi_data: KPICreate):
    """
    Create a new KPI
    """
    return await data_service.create_kpi(kpi_data)

@router.get("/kpis/{kpi_id}", response_model=KPI)
async def get_kpi(kpi_id: UUID):
    """
    Get a KPI by ID
    """
    kpi = await data_service.get_kpi(kpi_id)
    if not kpi:
        raise HTTPException(status_code=404, detail="KPI not found")
    return kpi

@router.get("/kpis", response_model=List[KPI])
async def list_kpis(
    limit: int = 20,
    offset: int = 0,
    category: Optional[DataCategory] = None,
    goal_id: Optional[UUID] = None
):
    """
    List KPIs with optional filtering
    """
    return await data_service.list_kpis(limit, offset, category, goal_id)

@router.put("/kpis/{kpi_id}", response_model=KPI)
async def update_kpi(kpi_id: UUID, kpi_data: dict):
    """
    Update a KPI
    """
    updated = await data_service.update_kpi(kpi_id, kpi_data)
    if not updated:
        raise HTTPException(status_code=404, detail="KPI not found")
    return updated

@router.delete("/kpis/{kpi_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_kpi(kpi_id: UUID):
    """
    Delete a KPI
    """
    deleted = await data_service.delete_kpi(kpi_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="KPI not found")
    return {"status": "success"}

# Data Set Endpoints

@router.post("/datasets", response_model=DataSet, status_code=status.HTTP_201_CREATED)
async def create_dataset(dataset_data: DataSetCreate):
    """
    Create a new dataset record
    """
    return await data_service.create_dataset(dataset_data)

@router.get("/datasets/{dataset_id}", response_model=DataSet)
async def get_dataset(dataset_id: UUID):
    """
    Get a dataset by ID
    """
    dataset = await data_service.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return dataset

@router.get("/datasets", response_model=List[DataSet])
async def list_datasets(
    limit: int = 20,
    offset: int = 0,
    category: Optional[DataCategory] = None,
    source_type: Optional[DataSourceType] = None
):
    """
    List datasets with optional filtering
    """
    return await data_service.list_datasets(limit, offset, category, source_type)

@router.put("/datasets/{dataset_id}", response_model=DataSet)
async def update_dataset(dataset_id: UUID, dataset_data: dict):
    """
    Update a dataset
    """
    updated = await data_service.update_dataset(dataset_id, dataset_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return updated

@router.delete("/datasets/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(dataset_id: UUID):
    """
    Delete a dataset
    """
    deleted = await data_service.delete_dataset(dataset_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Dataset not found")
    return {"status": "success"}

@router.post("/datasets/upload", response_model=DataSet)
async def upload_dataset(
    file: UploadFile = File(...),
    name: str = None,
    description: Optional[str] = None,
    category: DataCategory = None
):
    """
    Upload a file and create a new dataset
    """
    if not name or not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Name and category are required"
        )
        
    # Determine file format
    file_format = None
    filename = file.filename.lower()
    if filename.endswith('.csv'):
        file_format = 'csv'
    elif filename.endswith('.xlsx') or filename.endswith('.xls'):
        file_format = 'excel'
    elif filename.endswith('.json'):
        file_format = 'json'
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file format. Supported formats: CSV, Excel, JSON"
        )
    
    # Create dataset record
    dataset_data = DataSetCreate(
        name=name,
        description=description,
        category=category,
        source_type=DataSourceType.UPLOAD,
        data_format=file_format
    )
    
    # Process and save the file
    return await data_service.process_uploaded_file(file, dataset_data)

@router.post("/datasets/{dataset_id}/analysis", response_model=Dict[str, Any])
async def analyze_dataset(dataset_id: UUID):
    """
    Analyze a dataset and generate insights
    """
    dataset = await data_service.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    analysis_results = await data_service.analyze_dataset(dataset_id)
    return analysis_results

# Data Point Endpoints

@router.post("/datapoints", response_model=DataPoint, status_code=status.HTTP_201_CREATED)
async def create_datapoint(datapoint_data: DataPointCreate):
    """
    Create a new data point
    """
    return await data_service.create_datapoint(datapoint_data)

@router.get("/datapoints", response_model=List[DataPoint])
async def list_datapoints(
    dataset_id: UUID,
    limit: int = 100,
    offset: int = 0
):
    """
    List data points for a dataset
    """
    return await data_service.list_datapoints(dataset_id, limit, offset)

@router.post("/datasets/{dataset_id}/batch-datapoints", status_code=status.HTTP_201_CREATED)
async def create_batch_datapoints(dataset_id: UUID, datapoints: List[Dict[str, Any]]):
    """
    Create multiple data points in batch
    """
    return await data_service.create_batch_datapoints(dataset_id, datapoints)