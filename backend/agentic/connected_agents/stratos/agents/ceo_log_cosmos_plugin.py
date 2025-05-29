"""
CEO Log Cosmos DB Plugin
Provides tools that call Azure Functions for Cosmos DB operations
"""

import json
import logging
import requests
from typing import Dict, Any, List, Optional
from semantic_kernel import Kernel
from semantic_kernel.functions import kernel_function

logger = logging.getLogger(__name__)

# Azure Functions configuration
AZURE_FUNCTION_BASE = "https://stratos-ceo-log-functions.azurewebsites.net/api"
AZURE_FUNCTION_KEYS = {
    "SaveCEOLog": "I3c897PZMtJp1goBaxPwGlXa3Ni6ZsM09t1F7roTLVZeAzFu69TeKA==",
    "SearchCEOLogs": "uXjWD5crSSJYH_7eL3IcQq_ebEqVqO9D2QaC24UKa_RNAzFuVD7gkg==",
    "AnalyzeLogs": "1ALdM_XHFGwQ5XtC5BBsnJ-_j_w30lef9DsjGWVrpNJfAzFuEHzbmg==",
    "GetInsights": "Rx3WeFi1SoWXpbiZtsOCBVyswP06bUskqSYKK5HdntHBAzFuqJ56aw=="
}

class CEOLogCosmosPlugin:
    """Plugin for CEO Log Cosmos DB operations via Azure Functions"""
    
    @kernel_function(
        name="save_ceo_log",
        description="Save a new CEO log entry to Cosmos DB with AI analysis"
    )
    def save_ceo_log(
        self,
        user_id: str,
        content: str,
        category: str = "general",
        tags: Optional[List[str]] = None,
        source: str = "text"
    ) -> Dict[str, Any]:
        """Save CEO log entry via Azure Function"""
        url = f"{AZURE_FUNCTION_BASE}/saveceolog?code={AZURE_FUNCTION_KEYS['SaveCEOLog']}"
        
        payload = {
            "userId": user_id,
            "content": content,
            "category": category,
            "tags": tags or [],
            "metadata": {
                "source": source,
                "device": "azure-agent",
                "isVoice": source == "voice"
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 201:
                result = response.json()
                return {
                    "success": True,
                    "entryId": result.get("entryId"),
                    "summary": result.get("summary"),
                    "tags": result.get("tags", []),
                    "hasActionItems": result.get("metadata", {}).get("hasActionItems", False),
                    "isUrgent": result.get("metadata", {}).get("isUrgent", False)
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to save: {response.status_code} - {response.text}"
                }
        except Exception as e:
            logger.error(f"Error saving CEO log: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @kernel_function(
        name="search_ceo_logs",
        description="Search CEO log entries in Cosmos DB"
    )
    def search_ceo_logs(
        self,
        user_id: str,
        query: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Search CEO logs via Azure Function"""
        url = f"{AZURE_FUNCTION_BASE}/searchceologs?code={AZURE_FUNCTION_KEYS['SearchCEOLogs']}"
        
        payload = {
            "userId": user_id
        }
        
        if query:
            payload["query"] = query
        if category:
            payload["category"] = category
        if tags:
            payload["tags"] = tags
        if start_date:
            payload["startDate"] = start_date
        if end_date:
            payload["endDate"] = end_date
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "totalResults": result.get("totalResults", 0),
                    "results": result.get("results", [])
                }
            else:
                return {
                    "success": False,
                    "error": f"Search failed: {response.status_code} - {response.text}"
                }
        except Exception as e:
            logger.error(f"Error searching CEO logs: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @kernel_function(
        name="analyze_ceo_logs",
        description="Analyze CEO logs for patterns and insights"
    )
    def analyze_ceo_logs(
        self,
        user_id: str,
        focus_area: str = "general",
        timeframe: str = "week"
    ) -> Dict[str, Any]:
        """Analyze CEO logs via Azure Function"""
        url = f"{AZURE_FUNCTION_BASE}/analyzelogs?code={AZURE_FUNCTION_KEYS['AnalyzeLogs']}"
        
        # Fix focus_area value
        if focus_area == "all":
            focus_area = "general"
        
        payload = {
            "userId": user_id,
            "focusArea": focus_area,
            "timeframe": timeframe
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "insights": result.get("insights", []),
                    "themes": result.get("themes", []),
                    "recommendations": result.get("recommendations", []),
                    "totalAnalyzed": result.get("totalEntriesAnalyzed", 0)
                }
            else:
                return {
                    "success": False,
                    "error": f"Analysis failed: {response.status_code} - {response.text}"
                }
        except Exception as e:
            logger.error(f"Error analyzing CEO logs: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    @kernel_function(
        name="get_ceo_insights",
        description="Get recent insights and metrics from CEO logs"
    )
    def get_ceo_insights(
        self,
        user_id: str
    ) -> Dict[str, Any]:
        """Get insights via Azure Function"""
        url = f"{AZURE_FUNCTION_BASE}/getinsights?code={AZURE_FUNCTION_KEYS['GetInsights']}&userId={user_id}"
        
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "metrics": result.get("metrics", {}),
                    "insights": result.get("insights", [])
                }
            else:
                return {
                    "success": False,
                    "error": f"Get insights failed: {response.status_code} - {response.text}"
                }
        except Exception as e:
            logger.error(f"Error getting CEO insights: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }