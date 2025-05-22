"""
Service for managing alerts and notifications
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID, uuid4

from azure.cosmos.aio import ContainerProxy
from azure.cosmos import exceptions as CosmosExceptions
from fastapi import HTTPException

from ..models.alerts import (
    Alert, AlertCreate, AlertUpdate, AlertFilter,
    AlertType, AlertSeverity, AlertStatus,
    RiskOpportunityDetectionConfig
)
# Database imports handled in service initialization

logger = logging.getLogger(__name__)

class AlertService:
    """Service for managing alerts with Cosmos DB integration"""
    
    def __init__(self):
        self.container_name = "alerts"
        self._container: Optional[ContainerProxy] = None
        
        # In-memory cache as fallback
        self.alerts_cache: Dict[str, Alert] = {}
    
    async def get_container(self) -> Optional[ContainerProxy]:
        """Get or create the alerts container"""
        # For now, return None to use in-memory storage
        # In production, this would connect to Cosmos DB
        return None
    
    async def create_alert(self, alert_data: AlertCreate) -> Alert:
        """Create a new alert"""
        try:
            # Calculate risk score if not provided
            if alert_data.alert_type == AlertType.RISK and not alert_data.impact_score:
                if alert_data.impact_score and alert_data.likelihood_score:
                    risk_score = (alert_data.impact_score * alert_data.likelihood_score) / 100
                else:
                    risk_score = None
            else:
                risk_score = None
            
            # Create the alert
            alert = Alert(
                **alert_data.model_dump(),
                risk_score=risk_score
            )
            
            # Store in Cosmos DB
            container = await self.get_container()
            if container:
                try:
                    alert_dict = alert.model_dump()
                    alert_dict["id"] = str(alert.id)
                    alert_dict["user_id"] = str(alert.user_id)
                    alert_dict["created_at"] = alert.created_at.isoformat()
                    alert_dict["updated_at"] = alert.updated_at.isoformat()
                    
                    if alert.source_id:
                        alert_dict["source_id"] = str(alert.source_id)
                    
                    if alert.related_alerts:
                        alert_dict["related_alerts"] = [str(aid) for aid in alert.related_alerts]
                    
                    await container.create_item(body=alert_dict)
                    logger.info(f"Created alert {alert.id} in Cosmos DB")
                except Exception as e:
                    logger.error(f"Error storing alert in Cosmos DB: {e}")
                    # Fall back to cache
                    self.alerts_cache[str(alert.id)] = alert
            else:
                # Use cache if Cosmos DB is not available
                self.alerts_cache[str(alert.id)] = alert
            
            return alert
            
        except Exception as e:
            logger.error(f"Error creating alert: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create alert: {str(e)}")
    
    async def get_alert(self, alert_id: UUID, user_id: Optional[UUID] = None) -> Alert:
        """Get an alert by ID"""
        try:
            container = await self.get_container()
            if container:
                try:
                    query = "SELECT * FROM c WHERE c.id = @alert_id"
                    parameters = [{"name": "@alert_id", "value": str(alert_id)}]
                    
                    if user_id:
                        query += " AND c.user_id = @user_id"
                        parameters.append({"name": "@user_id", "value": str(user_id)})
                    
                    items = []
                    async for item in container.query_items(
                        query=query,
                        parameters=parameters,
                        enable_cross_partition_query=True
                    ):
                        items.append(item)
                    
                    if items:
                        return self._item_to_alert(items[0])
                except Exception as e:
                    logger.error(f"Error retrieving alert from Cosmos DB: {e}")
            
            # Check cache
            if str(alert_id) in self.alerts_cache:
                alert = self.alerts_cache[str(alert_id)]
                if not user_id or alert.user_id == user_id:
                    return alert
            
            raise HTTPException(status_code=404, detail="Alert not found")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting alert: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get alert: {str(e)}")
    
    async def update_alert(self, alert_id: UUID, update_data: AlertUpdate, user_id: Optional[UUID] = None) -> Alert:
        """Update an alert"""
        try:
            # Get existing alert
            alert = await self.get_alert(alert_id, user_id)
            
            # Update fields
            update_dict = update_data.model_dump(exclude_unset=True)
            
            # Handle status updates
            if "status" in update_dict:
                new_status = update_dict["status"]
                if new_status == AlertStatus.VIEWED and not alert.viewed_at:
                    alert.viewed_at = datetime.utcnow()
                elif new_status == AlertStatus.ACKNOWLEDGED and not alert.acknowledged_at:
                    alert.acknowledged_at = datetime.utcnow()
                elif new_status == AlertStatus.RESOLVED and not alert.resolved_at:
                    alert.resolved_at = datetime.utcnow()
            
            # Update other fields
            for key, value in update_dict.items():
                if hasattr(alert, key):
                    setattr(alert, key, value)
            
            alert.updated_at = datetime.utcnow()
            
            # Recalculate risk score if needed
            if alert.alert_type == AlertType.RISK and alert.impact_score and alert.likelihood_score:
                alert.risk_score = (alert.impact_score * alert.likelihood_score) / 100
            
            # Update in Cosmos DB
            container = await self.get_container()
            if container:
                try:
                    alert_dict = alert.model_dump()
                    alert_dict["id"] = str(alert.id)
                    alert_dict["user_id"] = str(alert.user_id)
                    self._serialize_dates(alert_dict)
                    
                    await container.upsert_item(body=alert_dict)
                    logger.info(f"Updated alert {alert.id} in Cosmos DB")
                except Exception as e:
                    logger.error(f"Error updating alert in Cosmos DB: {e}")
            
            # Update cache
            self.alerts_cache[str(alert.id)] = alert
            
            return alert
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating alert: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to update alert: {str(e)}")
    
    async def list_alerts(self, filter_params: AlertFilter) -> List[Alert]:
        """List alerts with filtering"""
        try:
            container = await self.get_container()
            alerts = []
            
            if container:
                try:
                    # Build query
                    query = "SELECT * FROM c WHERE 1=1"
                    parameters = []
                    
                    if filter_params.user_id:
                        query += " AND c.user_id = @user_id"
                        parameters.append({"name": "@user_id", "value": str(filter_params.user_id)})
                    
                    if filter_params.alert_type:
                        query += " AND c.alert_type = @alert_type"
                        parameters.append({"name": "@alert_type", "value": filter_params.alert_type})
                    
                    if filter_params.severity:
                        query += " AND ARRAY_CONTAINS(@severities, c.severity)"
                        parameters.append({"name": "@severities", "value": filter_params.severity})
                    
                    if filter_params.status:
                        query += " AND ARRAY_CONTAINS(@statuses, c.status)"
                        parameters.append({"name": "@statuses", "value": filter_params.status})
                    
                    if filter_params.category:
                        query += " AND c.category = @category"
                        parameters.append({"name": "@category", "value": filter_params.category})
                    
                    if filter_params.min_risk_score is not None:
                        query += " AND c.risk_score >= @min_risk_score"
                        parameters.append({"name": "@min_risk_score", "value": filter_params.min_risk_score})
                    
                    if filter_params.max_risk_score is not None:
                        query += " AND c.risk_score <= @max_risk_score"
                        parameters.append({"name": "@max_risk_score", "value": filter_params.max_risk_score})
                    
                    if filter_params.created_after:
                        query += " AND c.created_at >= @created_after"
                        parameters.append({"name": "@created_after", "value": filter_params.created_after.isoformat()})
                    
                    if filter_params.created_before:
                        query += " AND c.created_at <= @created_before"
                        parameters.append({"name": "@created_before", "value": filter_params.created_before.isoformat()})
                    
                    # Order by created_at descending
                    query += " ORDER BY c.created_at DESC"
                    
                    # Add pagination
                    query += f" OFFSET {filter_params.offset} LIMIT {filter_params.limit}"
                    
                    async for item in container.query_items(
                        query=query,
                        parameters=parameters,
                        enable_cross_partition_query=True
                    ):
                        alerts.append(self._item_to_alert(item))
                    
                except Exception as e:
                    logger.error(f"Error querying alerts from Cosmos DB: {e}")
                    # Fall back to cache
                    alerts = self._filter_cached_alerts(filter_params)
            else:
                # Use cache
                alerts = self._filter_cached_alerts(filter_params)
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error listing alerts: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to list alerts: {str(e)}")
    
    async def delete_alert(self, alert_id: UUID, user_id: Optional[UUID] = None) -> None:
        """Delete an alert"""
        try:
            # Verify alert exists and user has access
            alert = await self.get_alert(alert_id, user_id)
            
            container = await self.get_container()
            if container:
                try:
                    await container.delete_item(
                        item=str(alert_id),
                        partition_key=str(alert.user_id)
                    )
                    logger.info(f"Deleted alert {alert_id} from Cosmos DB")
                except Exception as e:
                    logger.error(f"Error deleting alert from Cosmos DB: {e}")
            
            # Remove from cache
            if str(alert_id) in self.alerts_cache:
                del self.alerts_cache[str(alert_id)]
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting alert: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to delete alert: {str(e)}")
    
    async def get_alert_stats(self, user_id: UUID) -> Dict[str, Any]:
        """Get alert statistics for a user"""
        try:
            container = await self.get_container()
            stats = {
                "total_alerts": 0,
                "by_type": {},
                "by_severity": {},
                "by_status": {},
                "unread_count": 0,
                "critical_count": 0
            }
            
            if container:
                try:
                    # Get counts by type
                    query = """
                    SELECT 
                        c.alert_type,
                        c.severity,
                        c.status,
                        COUNT(1) as count
                    FROM c
                    WHERE c.user_id = @user_id
                    GROUP BY c.alert_type, c.severity, c.status
                    """
                    
                    async for item in container.query_items(
                        query=query,
                        parameters=[{"name": "@user_id", "value": str(user_id)}],
                        enable_cross_partition_query=True
                    ):
                        stats["total_alerts"] += item["count"]
                        
                        # By type
                        if item["alert_type"] not in stats["by_type"]:
                            stats["by_type"][item["alert_type"]] = 0
                        stats["by_type"][item["alert_type"]] += item["count"]
                        
                        # By severity
                        if item["severity"] not in stats["by_severity"]:
                            stats["by_severity"][item["severity"]] = 0
                        stats["by_severity"][item["severity"]] += item["count"]
                        
                        # By status
                        if item["status"] not in stats["by_status"]:
                            stats["by_status"][item["status"]] = 0
                        stats["by_status"][item["status"]] += item["count"]
                        
                        # Unread count
                        if item["status"] == AlertStatus.NEW:
                            stats["unread_count"] += item["count"]
                        
                        # Critical count
                        if item["severity"] == AlertSeverity.CRITICAL:
                            stats["critical_count"] += item["count"]
                    
                except Exception as e:
                    logger.error(f"Error getting alert stats from Cosmos DB: {e}")
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting alert stats: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to get alert stats: {str(e)}")
    
    def _item_to_alert(self, item: Dict[str, Any]) -> Alert:
        """Convert Cosmos DB item to Alert model"""
        # Convert string UUIDs back to UUID objects
        if "user_id" in item:
            item["user_id"] = UUID(item["user_id"])
        if "source_id" in item and item["source_id"]:
            item["source_id"] = UUID(item["source_id"])
        if "related_alerts" in item and item["related_alerts"]:
            item["related_alerts"] = [UUID(aid) for aid in item["related_alerts"]]
        
        # Convert ISO format strings to datetime
        for date_field in ["created_at", "updated_at", "viewed_at", "acknowledged_at", "resolved_at"]:
            if date_field in item and item[date_field]:
                item[date_field] = datetime.fromisoformat(item[date_field])
        
        return Alert(**item)
    
    def _serialize_dates(self, alert_dict: Dict[str, Any]):
        """Serialize datetime fields to ISO format"""
        for date_field in ["created_at", "updated_at", "viewed_at", "acknowledged_at", "resolved_at"]:
            if date_field in alert_dict and alert_dict[date_field]:
                alert_dict[date_field] = alert_dict[date_field].isoformat()
    
    def _filter_cached_alerts(self, filter_params: AlertFilter) -> List[Alert]:
        """Filter alerts from cache"""
        filtered = []
        
        for alert in self.alerts_cache.values():
            # Apply filters
            if filter_params.user_id and alert.user_id != filter_params.user_id:
                continue
            if filter_params.alert_type and alert.alert_type != filter_params.alert_type:
                continue
            if filter_params.severity and alert.severity not in filter_params.severity:
                continue
            if filter_params.status and alert.status not in filter_params.status:
                continue
            if filter_params.category and alert.category != filter_params.category:
                continue
            if filter_params.min_risk_score is not None and (alert.risk_score or 0) < filter_params.min_risk_score:
                continue
            if filter_params.max_risk_score is not None and (alert.risk_score or 0) > filter_params.max_risk_score:
                continue
            if filter_params.created_after and alert.created_at < filter_params.created_after:
                continue
            if filter_params.created_before and alert.created_at > filter_params.created_before:
                continue
            
            filtered.append(alert)
        
        # Sort by created_at descending
        filtered.sort(key=lambda a: a.created_at, reverse=True)
        
        # Apply pagination
        return filtered[filter_params.offset:filter_params.offset + filter_params.limit]