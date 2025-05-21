from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from uuid import UUID, uuid4
from enum import Enum

class DataSourceType(str, Enum):
    UPLOAD = "upload"
    MANUAL = "manual"
    API = "api"
    WEB = "web"

class DataCategory(str, Enum):
    FINANCIAL = "financial"
    SALES = "sales"
    MARKETING = "marketing"
    OPERATIONS = "operations"
    HR = "human_resources"
    CUSTOMER = "customer"
    MARKET = "market"
    COMPETITOR = "competitor"
    OTHER = "other"

class KPI(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    category: DataCategory
    current_value: float
    target_value: Optional[float] = None
    unit: Optional[str] = None
    trend: Optional[str] = None  # "up", "down", "stable"
    time_period: Optional[str] = None
    source: Optional[str] = None
    linked_goals: List[UUID] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class KPICreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: DataCategory
    current_value: float
    target_value: Optional[float] = None
    unit: Optional[str] = None
    time_period: Optional[str] = None
    source: Optional[str] = None
    linked_goals: List[str] = []

class DataSet(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    description: Optional[str] = None
    category: DataCategory
    source_type: DataSourceType
    source_details: Optional[Dict[str, Any]] = None
    file_path: Optional[str] = None
    data_format: Optional[str] = None  # "csv", "json", "xlsx", etc.
    tags: List[str] = Field(default_factory=list) # Added tags
    linked_strategic_elements: List[Dict[str, str]] = Field(default_factory=list) # Added links: e.g. [{"type": "goal", "id": "uuid_str"}]
    import_date: datetime = Field(default_factory=datetime.now)
    last_refreshed: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    insights: List[str] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
class DataSetCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category: DataCategory
    source_type: DataSourceType
    source_details: Optional[Dict[str, Any]] = None
    data_format: Optional[str] = None
    tags: List[str] = Field(default_factory=list) # Added tags
    linked_strategic_elements: List[Dict[str, str]] = Field(default_factory=list) # Added links

class DataPoint(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    dataset_id: UUID
    timestamp: datetime
    dimension: Dict[str, str]  # e.g., {"region": "North", "product": "Widget A"}
    metrics: Dict[str, Union[float, int, str]]  # e.g., {"revenue": 10000, "units": 500}
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

class DataPointCreate(BaseModel):
    dataset_id: str
    timestamp: datetime
    dimension: Dict[str, str]
    metrics: Dict[str, Union[float, int, str]]
