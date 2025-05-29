"""
Request validation utilities
"""
from typing import Dict, Any, List
from .models import SaveCEOLogRequest, SearchCEOLogsRequest, AnalyzeLogsRequest

VALID_CATEGORIES = [
    "strategic_planning",
    "team_leadership",
    "market_analysis",
    "risk_assessment",
    "innovation",
    "operations",
    "financial",
    "customer_insights",
    "general"
]


def validate_save_request(data: Dict[str, Any]) -> SaveCEOLogRequest:
    """Validate save request data"""
    # Validate category
    if data.get('category') and data['category'] not in VALID_CATEGORIES:
        raise ValueError(f"Invalid category. Must be one of: {', '.join(VALID_CATEGORIES)}")
    
    # Sanitize content
    if 'content' in data:
        data['content'] = sanitize_content(data['content'])
    
    return SaveCEOLogRequest(**data)


def validate_search_request(data: Dict[str, Any]) -> SearchCEOLogsRequest:
    """Validate search request data"""
    # Convert single tag to list
    if 'tags' in data and isinstance(data['tags'], str):
        data['tags'] = [data['tags']]
    
    # Validate category
    if data.get('category') and data['category'] not in VALID_CATEGORIES:
        raise ValueError(f"Invalid category. Must be one of: {', '.join(VALID_CATEGORIES)}")
    
    return SearchCEOLogsRequest(**data)


def validate_analyze_request(data: Dict[str, Any]) -> AnalyzeLogsRequest:
    """Validate analyze request data"""
    return AnalyzeLogsRequest(**data)


def sanitize_content(content: str) -> str:
    """Remove potentially malicious content"""
    # Remove script tags and similar
    import re
    content = re.sub(r'<script[^>]*>.*?</script>', '', content, flags=re.IGNORECASE | re.DOTALL)
    content = re.sub(r'<iframe[^>]*>.*?</iframe>', '', content, flags=re.IGNORECASE | re.DOTALL)
    return content.strip()