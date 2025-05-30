"""
North Star Functions Implementation
Following Azure AI Agents function calling pattern
"""

import json
import requests
from typing import Dict, Any, Optional
from datetime import datetime

# Azure Function configuration
AZURE_FUNCTION_BASE = "https://stratos-north-star-functions.azurewebsites.net/api"
AZURE_FUNCTION_KEYS = {
    "ManagePurpose": "gPXyuj42jT_BnlDhImnO1gaV_xayICaGrxf2NoTA1_hVAzFuSjMcqQ==",
    "ManageVision": "hxaRNlD2FmGt9IHzHGXhtVavLrHvlDVkMtDfAe_j3cwyAzFuiAd75Q==",
    "ManageValues": "NliL5fD1aEmXoLSqoa1NSCzDbN2PEeSlCUYZAS6pxcc4AzFujGLDpw==",
    "ManageStrategicGoals": "kaS2TH5L7__RTKaLc8XfoxHDVW9AP8wE2p_Ei3lBQNvzAzFu4mIw4g==",
    "ValidateAlignment": "968fvYsjeBk7tEbv-0Bvt7RniJcynmitd_JR3Y-I5tHnAzFuZxFbwg==",
    "GetNorthStarSummary": "-W8ykJ6kkUyeLQCZXNklZqdoL1fOFhw1dvLQniJtqYvwAzFunTkKNA=="
}


def manage_purpose(organization_id: str, action: str = "get", purpose: Optional[str] = None) -> str:
    """
    Manages the organizational purpose (get or set).
    
    :param organization_id: The organization ID to manage purpose for
    :param action: The action to perform - "get" or "set"
    :param purpose: The purpose text (required for "set" action)
    :return: JSON string with the result
    """
    url = f"{AZURE_FUNCTION_BASE}/ManagePurpose"
    headers = {
        'Content-Type': 'application/json',
        'x-functions-key': AZURE_FUNCTION_KEYS['ManagePurpose']
    }
    
    payload = {
        "organizationId": organization_id,
        "action": action
    }
    
    if action == "set" and purpose:
        payload["purpose"] = purpose
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return json.dumps(response.json())
    except Exception as e:
        return json.dumps({"error": str(e)})


def manage_vision(organization_id: str, action: str = "get", vision: Optional[str] = None) -> str:
    """
    Manages the organizational vision (get or set).
    
    :param organization_id: The organization ID to manage vision for
    :param action: The action to perform - "get" or "set"
    :param vision: The vision text (required for "set" action)
    :return: JSON string with the result
    """
    url = f"{AZURE_FUNCTION_BASE}/ManageVision"
    headers = {
        'Content-Type': 'application/json',
        'x-functions-key': AZURE_FUNCTION_KEYS['ManageVision']
    }
    
    payload = {
        "organizationId": organization_id,
        "action": action
    }
    
    if action == "set" and vision:
        payload["vision"] = vision
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return json.dumps(response.json())
    except Exception as e:
        return json.dumps({"error": str(e)})


def manage_values(organization_id: str, action: str = "list", value: Optional[str] = None, 
                  description: Optional[str] = None) -> str:
    """
    Manages organizational values (add, remove, or list).
    
    :param organization_id: The organization ID to manage values for
    :param action: The action to perform - "add", "remove", or "list"
    :param value: The value name (required for add/remove)
    :param description: The value description (optional for add)
    :return: JSON string with the result
    """
    url = f"{AZURE_FUNCTION_BASE}/ManageValues"
    headers = {
        'Content-Type': 'application/json',
        'x-functions-key': AZURE_FUNCTION_KEYS['ManageValues']
    }
    
    payload = {
        "organizationId": organization_id,
        "action": action
    }
    
    if value:
        payload["value"] = value
    if description:
        payload["description"] = description
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return json.dumps(response.json())
    except Exception as e:
        return json.dumps({"error": str(e)})


def manage_strategic_goals(organization_id: str, action: str = "list", goal_id: Optional[str] = None,
                          title: Optional[str] = None, description: Optional[str] = None,
                          parent_id: Optional[str] = None, timeframe: Optional[str] = None) -> str:
    """
    Manages strategic goals with hierarchy support.
    
    :param organization_id: The organization ID to manage goals for
    :param action: The action to perform - "create", "update", "delete", "get", or "list"
    :param goal_id: The goal ID (required for update/delete/get)
    :param title: The goal title (required for create/update)
    :param description: The goal description
    :param parent_id: Parent goal ID for hierarchy
    :param timeframe: Goal timeframe (e.g., "Q1 2025", "2025-2027")
    :return: JSON string with the result
    """
    url = f"{AZURE_FUNCTION_BASE}/ManageStrategicGoals"
    headers = {
        'Content-Type': 'application/json',
        'x-functions-key': AZURE_FUNCTION_KEYS['ManageStrategicGoals']
    }
    
    payload = {
        "organizationId": organization_id,
        "action": action
    }
    
    if goal_id:
        payload["goalId"] = goal_id
    if title:
        payload["title"] = title
    if description:
        payload["description"] = description
    if parent_id:
        payload["parentId"] = parent_id
    if timeframe:
        payload["timeframe"] = timeframe
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return json.dumps(response.json())
    except Exception as e:
        return json.dumps({"error": str(e)})


def validate_alignment(organization_id: str, element_type: str, element_content: str) -> str:
    """
    Validates if an element aligns with the North Star.
    
    :param organization_id: The organization ID to validate against
    :param element_type: Type of element - "initiative", "decision", "action", or "metric"
    :param element_content: The content to validate
    :return: JSON string with alignment score and recommendations
    """
    url = f"{AZURE_FUNCTION_BASE}/ValidateAlignment"
    headers = {
        'Content-Type': 'application/json',
        'x-functions-key': AZURE_FUNCTION_KEYS['ValidateAlignment']
    }
    
    payload = {
        "organizationId": organization_id,
        "elementType": element_type,
        "elementContent": element_content
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return json.dumps(response.json())
    except Exception as e:
        return json.dumps({"error": str(e)})


def get_north_star_summary(organization_id: str) -> str:
    """
    Gets a complete summary of the North Star for an organization.
    
    :param organization_id: The organization ID to get summary for
    :return: JSON string with complete North Star data
    """
    url = f"{AZURE_FUNCTION_BASE}/GetNorthStarSummary"
    headers = {
        'Content-Type': 'application/json',
        'x-functions-key': AZURE_FUNCTION_KEYS['GetNorthStarSummary']
    }
    
    payload = {
        "organizationId": organization_id
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return json.dumps(response.json())
    except Exception as e:
        return json.dumps({"error": str(e)})


# Define all North Star functions for the agent
north_star_functions = {
    manage_purpose,
    manage_vision,
    manage_values,
    manage_strategic_goals,
    validate_alignment,
    get_north_star_summary
}