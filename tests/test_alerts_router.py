"""
Tests for alert API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from uuid import uuid4
from unittest.mock import patch, AsyncMock

from backend.main import app
from backend.models.alerts import AlertType, AlertSeverity, AlertStatus
from backend.models.user import UserResponse


@pytest.fixture
def client():
    """Create test client"""
    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest.fixture
def authenticated_client(client):
    """Client with mocked authentication"""
    # Mock the get_current_user dependency
    mock_user = UserResponse(
        id=uuid4(),
        email="test@example.com",
        full_name="Test User",
        company_name="Test Company",
        job_title="Developer",
        is_active=True,
        created_at=datetime.now()
    )
    
    with patch('backend.dependencies.get_current_user', return_value=mock_user):
        yield client, mock_user


class TestAlertEndpoints:
    """Test alert API endpoints"""
    
    def test_list_alerts(self, authenticated_client):
        """Test listing alerts endpoint"""
        client, user = authenticated_client
        
        with patch('backend.routers.alerts.alert_service.list_alerts', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = []
            
            response = client.get("/api/alerts")
            
            assert response.status_code == 200
            assert response.json() == []
            
            # Verify filter was passed correctly
            call_args = mock_list.call_args[0][0]
            assert call_args.user_id == user.id
    
    def test_list_alerts_with_filters(self, authenticated_client):
        """Test listing alerts with query parameters"""
        client, user = authenticated_client
        
        with patch('backend.routers.alerts.alert_service.list_alerts', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = []
            
            response = client.get(
                "/api/alerts",
                params={
                    "alert_type": AlertType.RISK,
                    "severity": [AlertSeverity.HIGH, AlertSeverity.CRITICAL],
                    "limit": 10
                }
            )
            
            assert response.status_code == 200
            
            # Verify filters were passed
            call_args = mock_list.call_args[0][0]
            assert call_args.alert_type == AlertType.RISK
            assert AlertSeverity.HIGH in call_args.severity
            assert call_args.limit == 10
    
    def test_get_alert(self, authenticated_client):
        """Test getting a specific alert"""
        client, user = authenticated_client
        alert_id = uuid4()
        
        mock_alert = {
            "id": str(alert_id),
            "user_id": str(user.id),
            "alert_type": AlertType.RISK,
            "severity": AlertSeverity.HIGH,
            "status": AlertStatus.NEW,
            "title": "Test Alert",
            "description": "Test Description",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        with patch('backend.routers.alerts.alert_service.get_alert', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = type('Alert', (), mock_alert)()
            
            response = client.get(f"/api/alerts/{alert_id}")
            
            assert response.status_code == 200
            mock_get.assert_called_once_with(alert_id, user.id)
    
    def test_acknowledge_alert(self, authenticated_client):
        """Test acknowledging an alert"""
        client, user = authenticated_client
        alert_id = uuid4()
        
        with patch('backend.routers.alerts.alert_service.update_alert', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = type('Alert', (), {
                "id": str(alert_id),
                "status": AlertStatus.ACKNOWLEDGED
            })()
            
            response = client.post(f"/api/alerts/{alert_id}/acknowledge")
            
            assert response.status_code == 200
            
            # Verify update was called with correct status
            call_args = mock_update.call_args
            assert call_args[0][1].status == AlertStatus.ACKNOWLEDGED
    
    def test_resolve_alert(self, authenticated_client):
        """Test resolving an alert"""
        client, user = authenticated_client
        alert_id = uuid4()
        
        with patch('backend.routers.alerts.alert_service.update_alert', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = type('Alert', (), {
                "id": str(alert_id),
                "status": AlertStatus.RESOLVED
            })()
            
            response = client.post(
                f"/api/alerts/{alert_id}/resolve",
                json={"notes": "Issue has been addressed"}
            )
            
            assert response.status_code == 200
            
            # Verify update was called
            call_args = mock_update.call_args
            assert call_args[0][1].status == AlertStatus.RESOLVED
    
    def test_dismiss_alert(self, authenticated_client):
        """Test dismissing an alert"""
        client, user = authenticated_client
        alert_id = uuid4()
        
        with patch('backend.routers.alerts.alert_service.update_alert', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = type('Alert', (), {
                "id": str(alert_id),
                "status": AlertStatus.DISMISSED
            })()
            
            response = client.post(
                f"/api/alerts/{alert_id}/dismiss",
                json={"reason": "False positive"}
            )
            
            assert response.status_code == 200
            
            # Verify update was called
            call_args = mock_update.call_args
            assert call_args[0][1].status == AlertStatus.DISMISSED
    
    def test_delete_alert(self, authenticated_client):
        """Test deleting an alert"""
        client, user = authenticated_client
        alert_id = uuid4()
        
        with patch('backend.routers.alerts.alert_service.delete_alert', new_callable=AsyncMock) as mock_delete:
            response = client.delete(f"/api/alerts/{alert_id}")
            
            assert response.status_code == 200
            assert response.json()["message"] == "Alert deleted successfully"
            mock_delete.assert_called_once_with(alert_id, user.id)
    
    def test_get_alert_stats(self, authenticated_client):
        """Test getting alert statistics"""
        client, user = authenticated_client
        
        mock_stats = {
            "total_alerts": 10,
            "by_type": {
                AlertType.RISK: 6,
                AlertType.OPPORTUNITY: 4
            },
            "by_severity": {
                AlertSeverity.HIGH: 3,
                AlertSeverity.MEDIUM: 5,
                AlertSeverity.LOW: 2
            },
            "by_status": {
                AlertStatus.NEW: 4,
                AlertStatus.ACKNOWLEDGED: 3,
                AlertStatus.RESOLVED: 3
            },
            "unread_count": 4,
            "critical_count": 0
        }
        
        with patch('backend.routers.alerts.alert_service.get_alert_stats', new_callable=AsyncMock) as mock_stats_fn:
            mock_stats_fn.return_value = mock_stats
            
            response = client.get("/api/alerts/stats/summary")
            
            assert response.status_code == 200
            assert response.json()["total_alerts"] == 10
            assert response.json()["unread_count"] == 4
    
    def test_trigger_scan(self, authenticated_client):
        """Test triggering a risk/opportunity scan"""
        client, user = authenticated_client
        
        with patch('backend.routers.alerts.analyze_user_risks_opportunities') as mock_task:
            response = client.post("/api/alerts/scan/trigger")
            
            assert response.status_code == 200
            assert response.json()["status"] == "queued"
            assert response.json()["user_id"] == str(user.id)
            
            # Note: In real implementation, this would be called via BackgroundTasks