"""
API routes for alerts and notifications
"""
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from datetime import datetime

from ..models.alerts import (
    Alert, AlertCreate, AlertUpdate, AlertFilter,
    AlertType, AlertSeverity, AlertStatus
)
from ..models.user import User
from ..services.alert_service import AlertService
from ..dependencies import get_current_user
from ..tasks.analysis_tasks import analyze_user_risks_opportunities

router = APIRouter(prefix="/alerts", tags=["alerts"])

# Initialize service
alert_service = AlertService()

@router.post("/", response_model=Alert)
async def create_alert(
    alert_data: AlertCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new alert (usually done by system, not users)"""
    # Ensure user can only create alerts for themselves
    alert_data.user_id = current_user.id
    
    return await alert_service.create_alert(alert_data)

@router.get("/{alert_id}", response_model=Alert)
async def get_alert(
    alert_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Get a specific alert"""
    return await alert_service.get_alert(alert_id, current_user.id)

@router.put("/{alert_id}", response_model=Alert)
async def update_alert(
    alert_id: UUID,
    update_data: AlertUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update an alert (e.g., mark as viewed, acknowledged)"""
    return await alert_service.update_alert(alert_id, update_data, current_user.id)

@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Delete an alert"""
    await alert_service.delete_alert(alert_id, current_user.id)
    return {"message": "Alert deleted successfully"}

@router.get("/", response_model=List[Alert])
async def list_alerts(
    alert_type: Optional[AlertType] = None,
    severity: Optional[List[AlertSeverity]] = Query(None),
    status: Optional[List[AlertStatus]] = Query(None),
    category: Optional[str] = None,
    min_risk_score: Optional[float] = Query(None, ge=0, le=100),
    max_risk_score: Optional[float] = Query(None, ge=0, le=100),
    created_after: Optional[datetime] = None,
    created_before: Optional[datetime] = None,
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user)
):
    """List alerts with filtering"""
    filter_params = AlertFilter(
        user_id=current_user.id,
        alert_type=alert_type,
        severity=severity,
        status=status,
        category=category,
        min_risk_score=min_risk_score,
        max_risk_score=max_risk_score,
        created_after=created_after,
        created_before=created_before,
        limit=limit,
        offset=offset
    )
    
    return await alert_service.list_alerts(filter_params)

@router.get("/stats/summary")
async def get_alert_stats(
    current_user: User = Depends(get_current_user)
):
    """Get alert statistics for the current user"""
    return await alert_service.get_alert_stats(current_user.id)

@router.post("/{alert_id}/acknowledge", response_model=Alert)
async def acknowledge_alert(
    alert_id: UUID,
    current_user: User = Depends(get_current_user)
):
    """Acknowledge an alert"""
    update_data = AlertUpdate(status=AlertStatus.ACKNOWLEDGED)
    return await alert_service.update_alert(alert_id, update_data, current_user.id)

@router.post("/{alert_id}/resolve", response_model=Alert)
async def resolve_alert(
    alert_id: UUID,
    notes: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Resolve an alert"""
    update_data = AlertUpdate(status=AlertStatus.RESOLVED)
    alert = await alert_service.update_alert(alert_id, update_data, current_user.id)
    
    # Could store resolution notes in a separate model if needed
    
    return alert

@router.post("/{alert_id}/dismiss", response_model=Alert)
async def dismiss_alert(
    alert_id: UUID,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Dismiss an alert"""
    update_data = AlertUpdate(status=AlertStatus.DISMISSED)
    return await alert_service.update_alert(alert_id, update_data, current_user.id)

@router.post("/scan/trigger")
async def trigger_risk_opportunity_scan(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    """Manually trigger a risk/opportunity scan for the current user"""
    # Queue the analysis task
    background_tasks.add_task(
        analyze_user_risks_opportunities,
        str(current_user.id),
        {}  # Default config
    )
    
    return {
        "message": "Risk and opportunity scan triggered",
        "user_id": str(current_user.id),
        "status": "queued"
    }