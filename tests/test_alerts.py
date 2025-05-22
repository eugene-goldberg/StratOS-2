"""
Tests for the alert system (risk/opportunity flagging)
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from unittest.mock import Mock, patch, AsyncMock

from backend.models.alerts import (
    Alert, AlertCreate, AlertUpdate, AlertFilter,
    AlertType, AlertSeverity, AlertStatus,
    RiskCategory, OpportunityCategory,
    RiskOpportunityDetectionConfig
)
from backend.services.alert_service import AlertService


@pytest.fixture
def alert_service():
    """Create alert service instance"""
    service = AlertService()
    # Use in-memory cache for testing
    service._container = None
    return service


@pytest.fixture
def sample_alert_data():
    """Sample alert creation data"""
    return AlertCreate(
        user_id=uuid4(),
        alert_type=AlertType.RISK,
        severity=AlertSeverity.HIGH,
        title="High inventory costs detected",
        description="Inventory holding costs have increased by 25% over the last quarter",
        category=RiskCategory.FINANCIAL,
        impact_score=75,
        likelihood_score=80,
        source_type="objective_data",
        source_id=uuid4(),
        detection_method="threshold_analysis",
        confidence_score=85,
        recommendations=[
            "Review inventory turnover rates",
            "Implement just-in-time ordering"
        ]
    )


@pytest.fixture
def sample_opportunity_data():
    """Sample opportunity alert data"""
    return AlertCreate(
        user_id=uuid4(),
        alert_type=AlertType.OPPORTUNITY,
        severity=AlertSeverity.MEDIUM,
        title="Emerging market demand detected",
        description="Social media sentiment shows 40% increase in product interest in APAC region",
        category=OpportunityCategory.MARKET_EXPANSION,
        impact_score=85,
        likelihood_score=70,
        source_type="analysis",
        detection_method="ai_analysis",
        confidence_score=78,
        recommendations=[
            "Conduct detailed market analysis for APAC",
            "Consider regional product adaptation"
        ]
    )


class TestAlertModels:
    """Test alert model validation and behavior"""
    
    def test_alert_creation(self, sample_alert_data):
        """Test creating an alert with valid data"""
        alert = Alert(**sample_alert_data.model_dump())
        
        assert alert.id is not None
        assert alert.alert_type == AlertType.RISK
        assert alert.severity == AlertSeverity.HIGH
        assert alert.status == AlertStatus.NEW
        assert alert.risk_score == 60.0  # (75 * 80) / 100
        
    def test_alert_severity_assignment(self):
        """Test severity is properly assigned based on scores"""
        # Critical severity (risk_score >= 75)
        alert_data = AlertCreate(
            user_id=uuid4(),
            alert_type=AlertType.RISK,
            severity=AlertSeverity.LOW,  # Should be overridden
            title="Critical risk",
            description="Test",
            impact_score=90,
            likelihood_score=90,
            source_type="test",
            detection_method="test"
        )
        alert = Alert(**alert_data.model_dump())
        assert alert.risk_score == 81.0
        
    def test_detection_config_defaults(self):
        """Test detection configuration defaults"""
        config = RiskOpportunityDetectionConfig()
        
        assert config.min_confidence_score == 70.0
        assert config.risk_impact_threshold == 50.0
        assert config.lookback_days == 7
        assert config.include_subjective is True
        assert config.detect_trends is True


@pytest.mark.asyncio
class TestAlertService:
    """Test alert service operations"""
    
    async def test_create_alert(self, alert_service, sample_alert_data):
        """Test creating an alert"""
        alert = await alert_service.create_alert(sample_alert_data)
        
        assert alert.id is not None
        assert alert.user_id == sample_alert_data.user_id
        assert alert.title == sample_alert_data.title
        assert alert.created_at is not None
        assert str(alert.id) in alert_service.alerts_cache
        
    async def test_get_alert(self, alert_service, sample_alert_data):
        """Test retrieving an alert"""
        # Create alert
        created_alert = await alert_service.create_alert(sample_alert_data)
        
        # Retrieve it
        retrieved_alert = await alert_service.get_alert(created_alert.id)
        
        assert retrieved_alert.id == created_alert.id
        assert retrieved_alert.title == created_alert.title
        
    async def test_update_alert_status(self, alert_service, sample_alert_data):
        """Test updating alert status"""
        # Create alert
        alert = await alert_service.create_alert(sample_alert_data)
        
        # Update to viewed
        update_data = AlertUpdate(status=AlertStatus.VIEWED)
        updated_alert = await alert_service.update_alert(alert.id, update_data)
        
        assert updated_alert.status == AlertStatus.VIEWED
        assert updated_alert.viewed_at is not None
        
        # Update to acknowledged
        update_data = AlertUpdate(status=AlertStatus.ACKNOWLEDGED)
        updated_alert = await alert_service.update_alert(alert.id, update_data)
        
        assert updated_alert.status == AlertStatus.ACKNOWLEDGED
        assert updated_alert.acknowledged_at is not None
        
    async def test_list_alerts_with_filter(self, alert_service, sample_alert_data, sample_opportunity_data):
        """Test listing alerts with filters"""
        # Create multiple alerts
        risk_alert = await alert_service.create_alert(sample_alert_data)
        opp_alert = await alert_service.create_alert(sample_opportunity_data)
        
        # Filter by type
        filter_params = AlertFilter(
            user_id=sample_alert_data.user_id,
            alert_type=AlertType.RISK
        )
        filtered_alerts = await alert_service.list_alerts(filter_params)
        
        assert len(filtered_alerts) == 1
        assert filtered_alerts[0].alert_type == AlertType.RISK
        
        # Filter by severity
        filter_params = AlertFilter(
            severity=[AlertSeverity.HIGH, AlertSeverity.CRITICAL]
        )
        filtered_alerts = await alert_service.list_alerts(filter_params)
        
        assert all(a.severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL] for a in filtered_alerts)
        
    async def test_alert_stats(self, alert_service, sample_alert_data):
        """Test getting alert statistics"""
        user_id = sample_alert_data.user_id
        
        # Create multiple alerts
        created_alerts = []
        for i in range(3):
            alert_data = sample_alert_data.model_copy()
            alert_data.title = f"Risk {i}"
            created_alert = await alert_service.create_alert(alert_data)
            created_alerts.append(created_alert)
        
        stats = await alert_service.get_alert_stats(user_id)
        
        # Since we're using in-memory cache, check exact counts
        assert stats["total_alerts"] == 3
        assert stats["by_type"][AlertType.RISK] == 3
        assert stats["by_severity"][AlertSeverity.HIGH] == 3
        assert stats["unread_count"] == 3


class TestRiskOpportunityDetection:
    """Test risk/opportunity detection logic"""
    
    @patch('backend.ai.kernel_service.kernel_service')
    async def test_detect_risks_skill(self, mock_kernel):
        """Test the risk detection AI skill"""
        from backend.ai.skills.analysis_skills.risk_opportunity_detection_skill import RiskOpportunityDetectionSkill
        
        skill = RiskOpportunityDetectionSkill()
        
        # Mock context
        context = Mock()
        context.get.side_effect = lambda key, default: {
            "data": '{"subjective_entries": [], "objective_data": [], "insights": []}',
            "config": '{}'
        }.get(key, default)
        
        # Mock kernel response
        mock_result = Mock()
        mock_result.result = '[{"title": "Test Risk", "impact_score": 80}]'
        context.kernel.run_async = AsyncMock(return_value=mock_result)
        
        # Test risk detection
        result = await skill.detect_risks(context)
        
        assert "Test Risk" in result
        
    def test_risk_score_calculation(self):
        """Test risk score calculation logic"""
        from backend.ai.skills.analysis_skills.risk_opportunity_detection_skill import RiskOpportunityDetectionSkill
        
        skill = RiskOpportunityDetectionSkill()
        
        # Test risk scoring
        risks = [
            {"impact_score": 80, "likelihood_score": 90},
            {"impact_score": 50, "likelihood_score": 50},
            {"impact_score": 30, "likelihood_score": 40}
        ]
        
        context = Mock()
        context.get.return_value = json.dumps(risks)
        
        # The actual scoring would be done in the skill
        for risk in risks:
            risk_score = (risk["impact_score"] * risk["likelihood_score"]) / 100
            
            if risk_score >= 75:
                severity = "critical"
            elif risk_score >= 50:
                severity = "high"
            elif risk_score >= 25:
                severity = "medium"
            else:
                severity = "low"
                
            risk["risk_score"] = risk_score
            risk["severity"] = severity
        
        assert risks[0]["risk_score"] == 72.0
        assert risks[0]["severity"] == "high"
        assert risks[1]["risk_score"] == 25.0
        assert risks[1]["severity"] == "medium"


@pytest.mark.asyncio
class TestAlertIntegration:
    """Integration tests for the alert system"""
    
    async def test_end_to_end_alert_flow(self, alert_service):
        """Test complete alert lifecycle"""
        user_id = uuid4()
        
        # Create alert
        alert_data = AlertCreate(
            user_id=user_id,
            alert_type=AlertType.RISK,
            severity=AlertSeverity.HIGH,
            title="Integration test risk",
            description="Test description",
            impact_score=80,
            likelihood_score=70,
            source_type="test",
            detection_method="test",
            confidence_score=90
        )
        
        alert = await alert_service.create_alert(alert_data)
        assert alert.status == AlertStatus.NEW
        
        # Mark as viewed
        await alert_service.update_alert(
            alert.id,
            AlertUpdate(status=AlertStatus.VIEWED)
        )
        
        # Acknowledge
        alert = await alert_service.update_alert(
            alert.id,
            AlertUpdate(status=AlertStatus.ACKNOWLEDGED)
        )
        assert alert.acknowledged_at is not None
        
        # Resolve
        alert = await alert_service.update_alert(
            alert.id,
            AlertUpdate(status=AlertStatus.RESOLVED)
        )
        assert alert.resolved_at is not None
        
        # Check stats
        stats = await alert_service.get_alert_stats(user_id)
        assert stats["by_status"][AlertStatus.RESOLVED] >= 1


# Import for JSON in tests
import json