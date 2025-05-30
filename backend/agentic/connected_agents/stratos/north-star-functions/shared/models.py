"""
Data models for North Star functions
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

class PurposeModel(BaseModel):
    statement: str
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    version: int = 1

class VisionModel(BaseModel):
    statement: str
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    version: int = 1

class ValueModel(BaseModel):
    name: str
    description: Optional[str] = ""
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class StrategicGoalModel(BaseModel):
    id: str
    name: str
    description: Optional[str] = ""
    parent_id: Optional[str] = None
    target_date: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    status: str = "active"

class AlignmentValidationModel(BaseModel):
    element_type: str
    element_content: str
    alignment_score: float = 0.0
    alignment_factors: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    is_aligned: bool = False

class NorthStarData(BaseModel):
    id: str
    organizationId: str
    purpose: Optional[Dict[str, Any]] = None
    vision: Optional[Dict[str, Any]] = None
    values: List[Dict[str, Any]] = Field(default_factory=list)
    strategicGoals: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    goalHierarchy: Dict[str, List[str]] = Field(default_factory=dict)