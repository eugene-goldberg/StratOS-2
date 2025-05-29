"""
Pydantic models for CEO Log entries in Cosmos DB
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid


class SentimentType(str, Enum):
    """Sentiment types for log entries"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class LogEntryContent(BaseModel):
    """Content of a CEO log entry"""
    content: str = Field(..., max_length=5000, description="The actual log content")
    sentiment: Optional[SentimentType] = Field(SentimentType.NEUTRAL, description="Sentiment analysis result")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score for sentiment")


class LogMetadata(BaseModel):
    """Metadata for a CEO log entry"""
    source: Optional[str] = Field(None, description="Source of the log (voice, text, meeting)")
    duration: Optional[int] = Field(None, description="Duration in seconds for voice entries")
    location: Optional[str] = Field(None, description="Location where the log was created")
    device: Optional[str] = Field(None, description="Device used to create the log")
    sessionId: Optional[str] = Field(None, description="Session ID for grouping related logs")


class LogAnalysis(BaseModel):
    """AI-generated analysis of the log entry"""
    keyInsights: List[str] = Field(default_factory=list, description="Key insights from the log")
    actionItems: List[str] = Field(default_factory=list, description="Action items identified")
    riskFactors: List[str] = Field(default_factory=list, description="Risk factors identified")
    opportunities: List[str] = Field(default_factory=list, description="Opportunities identified")


class CEOLogEntry(BaseModel):
    """Complete CEO log entry model for Cosmos DB"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier")
    userId: str = Field(..., description="User identifier (partition key)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the log was created")
    logEntry: LogEntryContent = Field(..., description="The main log content")
    tags: List[str] = Field(default_factory=list, description="User-defined tags")
    strategicThemes: List[str] = Field(default_factory=list, description="AI-identified strategic themes")
    metadata: Optional[LogMetadata] = Field(None, description="Additional metadata")
    analysis: Optional[LogAnalysis] = Field(None, description="AI-generated analysis")
    createdBy: str = Field(default="CEOLogAgent", description="System that created the entry")
    createdAt: datetime = Field(default_factory=datetime.utcnow, description="Server timestamp when created")
    modifiedAt: datetime = Field(default_factory=datetime.utcnow, description="Server timestamp when modified")
    version: int = Field(default=1, description="Document version number")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def dict_for_cosmos(self) -> dict:
        """Convert to dictionary format for Cosmos DB"""
        data = self.dict()
        # Convert datetime objects to ISO format strings
        for field in ['timestamp', 'createdAt', 'modifiedAt']:
            if field in data and isinstance(data[field], datetime):
                data[field] = data[field].isoformat()
        return data


class CEOLogUpdate(BaseModel):
    """Model for updating CEO log entries"""
    logEntry: Optional[LogEntryContent] = None
    tags: Optional[List[str]] = None
    strategicThemes: Optional[List[str]] = None
    metadata: Optional[LogMetadata] = None
    analysis: Optional[LogAnalysis] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LogSearchQuery(BaseModel):
    """Model for search queries"""
    userId: str = Field(..., description="User ID to search within")
    searchTerm: Optional[str] = Field(None, description="Search term for content")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    strategicThemes: Optional[List[str]] = Field(None, description="Filter by strategic themes")
    sentiment: Optional[SentimentType] = Field(None, description="Filter by sentiment")
    startDate: Optional[datetime] = Field(None, description="Start date for date range")
    endDate: Optional[datetime] = Field(None, description="End date for date range")
    limit: int = Field(100, ge=1, le=1000, description="Maximum results to return")
    offset: int = Field(0, ge=0, description="Offset for pagination")


class LogSummaryResponse(BaseModel):
    """Response model for log summaries"""
    totalLogs: int = Field(..., description="Total number of logs")
    dateRange: Dict[str, str] = Field(..., description="Date range of logs")
    sentimentCounts: Dict[str, int] = Field(..., description="Count by sentiment")
    topTags: List[Dict[str, Any]] = Field(..., description="Most frequent tags")
    topThemes: List[Dict[str, Any]] = Field(..., description="Most frequent themes")
    recentLogs: List[CEOLogEntry] = Field(..., description="Recent log entries")
    insights: Dict[str, Any] = Field(default_factory=dict, description="Additional insights")