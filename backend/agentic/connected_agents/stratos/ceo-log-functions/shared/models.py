"""
Data models for CEO Log entries
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
import uuid


class SentimentType(str, Enum):
    """Sentiment types for log entries"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class LogEntryContent(BaseModel):
    """Content of a CEO log entry"""
    content: str = Field(..., max_length=5000)
    sentiment: SentimentType = SentimentType.NEUTRAL
    confidence: float = Field(0.5, ge=0.0, le=1.0)


class LogMetadata(BaseModel):
    """Metadata for a CEO log entry"""
    source: Optional[str] = None
    duration: Optional[int] = None
    location: Optional[str] = None
    device: Optional[str] = None
    sessionId: Optional[str] = None
    isVoice: bool = False
    wordCount: int = 0


class LogAnalysis(BaseModel):
    """AI-generated analysis of the log entry"""
    summary: str
    keyInsights: List[str] = Field(default_factory=list)
    actionItems: List[str] = Field(default_factory=list)
    riskFactors: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    hasActionItems: bool = False
    isUrgent: bool = False
    involvesRisk: bool = False
    strategicRelevance: bool = False


class CEOLogEntry(BaseModel):
    """Complete CEO log entry model for Cosmos DB"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    userId: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    logEntry: LogEntryContent
    category: str = "general"
    tags: List[str] = Field(default_factory=list)
    strategicThemes: List[str] = Field(default_factory=list)
    metadata: LogMetadata
    analysis: LogAnalysis
    createdBy: str = "CEOLogAgent"
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    modifiedAt: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1
    
    def dict_for_cosmos(self) -> dict:
        """Convert to dictionary format for Cosmos DB"""
        data = self.model_dump()
        # Convert datetime objects to ISO format strings
        for field in ['timestamp', 'createdAt', 'modifiedAt']:
            if field in data and isinstance(data[field], datetime):
                data[field] = data[field].isoformat()
        return data


class SaveCEOLogRequest(BaseModel):
    """Request model for saving CEO log"""
    userId: str
    content: str = Field(..., max_length=5000)
    category: Optional[str] = "general"
    tags: Optional[List[str]] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class SearchCEOLogsRequest(BaseModel):
    """Request model for searching CEO logs"""
    userId: str
    query: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    dateRange: Optional[Dict[str, str]] = None
    limit: int = Field(10, ge=1, le=100)
    offset: int = Field(0, ge=0)


class AnalyzeLogsRequest(BaseModel):
    """Request model for analyzing CEO logs"""
    userId: str
    timeframe: str = Field("month", pattern="^(week|month|quarter|year|all)$")
    focusArea: str = Field("general", pattern="^(risks|opportunities|team|market|general)$")


class AIAnalysisResult(BaseModel):
    """Result of AI content analysis"""
    sentiment: SentimentType
    confidence: float
    summary: str
    generatedTags: List[str]
    themes: List[str]
    insights: List[str]
    actionItems: List[str]
    risks: List[str]
    opportunities: List[str]
    isUrgent: bool