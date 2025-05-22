"""
Tests for Celery analysis tasks
"""
import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import patch, AsyncMock, Mock
import json

from backend.tasks.analysis_tasks import (
    scan_for_risks_and_opportunities,
    analyze_user_risks_opportunities,
    detect_risks,
    detect_opportunities,
    create_alerts_from_findings
)
from backend.models.alerts import AlertCreate, AlertType, AlertSeverity, RiskOpportunityDetectionConfig


class TestAnalysisTasks:
    """Test background analysis tasks"""
    
    @patch('backend.tasks.analysis_tasks.analyze_user_risks_opportunities.delay')
    def test_scan_for_risks_and_opportunities(self, mock_analyze):
        """Test the periodic scan task"""
        # Mock user list (empty for test)
        with patch('backend.tasks.analysis_tasks.logger') as mock_logger:
            scan_for_risks_and_opportunities()
            
            # Verify logging
            mock_logger.info.assert_called()
            assert "Starting periodic risk/opportunity scan" in str(mock_logger.info.call_args_list[0])
    
    @pytest.mark.asyncio
    @patch('backend.tasks.analysis_tasks.AlertService')
    @patch('backend.tasks.analysis_tasks.SubjectiveInputService')
    @patch('backend.tasks.analysis_tasks.ObjectiveDataService')
    @patch('backend.tasks.analysis_tasks.AnalysisService')
    async def test_analyze_user_risks_opportunities(
        self, mock_analysis_svc, mock_objective_svc, mock_subjective_svc, mock_alert_svc
    ):
        """Test analyzing risks/opportunities for a user"""
        user_id = str(uuid4())
        config = RiskOpportunityDetectionConfig()
        
        # Mock service responses
        mock_subjective_svc.return_value.list_entries = AsyncMock(return_value=[])
        mock_objective_svc.return_value.list_datasets = AsyncMock(return_value=[])
        mock_objective_svc.return_value.list_entries = AsyncMock(return_value=[])
        mock_analysis_svc.return_value.list_insights = AsyncMock(return_value=[])
        mock_analysis_svc.return_value.list_swot_analyses = AsyncMock(return_value=[])
        
        # Mock risk/opportunity detection
        with patch('backend.tasks.analysis_tasks.detect_risks', new_callable=AsyncMock) as mock_detect_risks:
            with patch('backend.tasks.analysis_tasks.detect_opportunities', new_callable=AsyncMock) as mock_detect_opps:
                with patch('backend.tasks.analysis_tasks.create_alerts_from_findings', new_callable=AsyncMock) as mock_create_alerts:
                    mock_detect_risks.return_value = []
                    mock_detect_opps.return_value = []
                    
                    await analyze_user_risks_opportunities(user_id, config.dict())
                    
                    # Verify services were called
                    mock_subjective_svc.return_value.list_entries.assert_called_once()
                    mock_detect_risks.assert_called_once()
                    mock_detect_opps.assert_called_once()
                    mock_create_alerts.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('backend.tasks.analysis_tasks.kernel_service')
    async def test_detect_risks(self, mock_kernel):
        """Test risk detection"""
        data = {
            "subjective_entries": [
                {"content": "Concerned about rising costs", "entry_date": "2024-01-01"}
            ],
            "objective_data": [
                {"name": "Operating Costs", "value": 150000, "data_type": "financial"}
            ]
        }
        config = RiskOpportunityDetectionConfig()
        
        # Mock kernel response
        mock_skill = Mock()
        mock_context = {}  # Use a dict instead of Mock since the code assigns to it
        mock_result = Mock()
        mock_result.result = json.dumps([
            {
                "title": "Rising Operating Costs",
                "description": "Operating costs have increased significantly",
                "category": "financial",
                "impact_score": 80,
                "likelihood_score": 90,
                "confidence_score": 85
            }
        ])
        
        mock_kernel.import_skill.return_value = {"detect_risks": mock_skill, "calculate_risk_scores": mock_skill}
        mock_kernel.create_new_context.return_value = mock_context
        mock_kernel.run_async = AsyncMock(return_value=mock_result)
        
        risks = await detect_risks(data, config.dict())
        
        assert len(risks) > 0
        assert mock_kernel.run_async.called
    
    @pytest.mark.asyncio
    @patch('backend.tasks.analysis_tasks.kernel_service')
    async def test_detect_opportunities(self, mock_kernel):
        """Test opportunity detection"""
        data = {
            "subjective_entries": [
                {"content": "Seeing increased customer interest", "entry_date": "2024-01-01"}
            ],
            "insights": [
                {"title": "Market Growth", "content": "25% growth in target segment"}
            ]
        }
        config = RiskOpportunityDetectionConfig()
        
        # Mock kernel response
        mock_skill = Mock()
        mock_context = {}  # Use a dict instead of Mock since the code assigns to it
        mock_result = Mock()
        mock_result.result = json.dumps([
            {
                "title": "Market Expansion Opportunity",
                "description": "Strong growth in target market segment",
                "category": "market_expansion",
                "impact_score": 85,
                "likelihood_score": 75,
                "confidence_score": 80
            }
        ])
        
        mock_kernel.import_skill.return_value = {"detect_opportunities": mock_skill}
        mock_kernel.create_new_context.return_value = mock_context
        mock_kernel.run_async = AsyncMock(return_value=mock_result)
        
        opportunities = await detect_opportunities(data, config.dict())
        
        assert len(opportunities) > 0
        assert mock_kernel.run_async.called
    
    @pytest.mark.asyncio
    async def test_create_alerts_from_findings(self):
        """Test creating alerts from detected risks and opportunities"""
        user_id = uuid4()
        
        risks = [
            {
                "title": "Test Risk",
                "description": "Test risk description",
                "severity": "high",
                "category": "operational",
                "impact_score": 80,
                "likelihood_score": 70,
                "confidence_score": 85,
                "indicators": ["indicator1"],
                "recommendations": ["action1"],
                "time_horizon": "short_term"
            }
        ]
        
        opportunities = [
            {
                "title": "Test Opportunity",
                "description": "Test opportunity description",
                "category": "revenue_growth",
                "impact_score": 90,
                "likelihood_score": 60,
                "confidence_score": 75,
                "indicators": ["indicator2"],
                "recommendations": ["action2"],
                "resource_requirements": "medium"
            }
        ]
        
        mock_alert_service = Mock()
        mock_alert_service.create_alert = AsyncMock()
        
        await create_alerts_from_findings(user_id, risks, opportunities, mock_alert_service)
        
        # Verify alerts were created
        assert mock_alert_service.create_alert.call_count == 2
        
        # Check risk alert
        risk_call = mock_alert_service.create_alert.call_args_list[0][0][0]
        assert risk_call.alert_type == AlertType.RISK
        assert risk_call.title == "Test Risk"
        assert risk_call.impact_score == 80
        
        # Check opportunity alert
        opp_call = mock_alert_service.create_alert.call_args_list[1][0][0]
        assert opp_call.alert_type == AlertType.OPPORTUNITY
        assert opp_call.title == "Test Opportunity"
        assert opp_call.impact_score == 90
    
    @pytest.mark.asyncio
    async def test_create_alerts_filters_low_confidence(self):
        """Test that low confidence findings are filtered out"""
        user_id = uuid4()
        
        risks = [
            {
                "title": "Low Confidence Risk",
                "confidence_score": 50,  # Below threshold
                "severity": "medium"
            }
        ]
        
        mock_alert_service = Mock()
        mock_alert_service.create_alert = AsyncMock()
        
        await create_alerts_from_findings(user_id, risks, [], mock_alert_service)
        
        # Verify no alerts were created for low confidence
        assert mock_alert_service.create_alert.call_count == 0