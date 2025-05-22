"""
Celery tasks for periodic risk and opportunity analysis
"""
import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from uuid import UUID

from celery import shared_task
from celery.utils.log import get_task_logger

from ..core.celery_app import celery_app
from ..models.alerts import (
    Alert, AlertCreate, AlertType, AlertSeverity,
    RiskOpportunityDetectionConfig, RiskCategory, OpportunityCategory
)
from ..services.analysis_service import AnalysisService
from ..services.subjective_input_service import SubjectiveInputService
from ..services.objective_data_service import ObjectiveDataService
from ..services.alert_service import AlertService
from ..ai.kernel_service import kernel_service

logger = get_task_logger(__name__)

@celery_app.task(name="backend.tasks.analysis_tasks.scan_for_risks_and_opportunities")
def scan_for_risks_and_opportunities():
    """
    Periodic task to scan for risks and opportunities across all users
    """
    try:
        logger.info("Starting periodic risk/opportunity scan")
        
        # Get all active users (simplified - in production you'd have user service)
        # For now, we'll scan for a specific user or all users with recent activity
        
        # Initialize services
        analysis_service = AnalysisService()
        subjective_service = SubjectiveInputService()
        objective_service = ObjectiveDataService()
        alert_service = AlertService()
        
        # Get detection config (could be customized per user)
        config = RiskOpportunityDetectionConfig()
        
        # For each user, analyze their recent data
        # This is simplified - in production you'd iterate through active users
        users_to_scan = []  # Would get from user service
        
        for user_id in users_to_scan:
            try:
                analyze_user_risks_opportunities.delay(str(user_id), config.dict())
            except Exception as e:
                logger.error(f"Error queuing analysis for user {user_id}: {str(e)}")
        
        logger.info("Completed queuing risk/opportunity scans")
        
    except Exception as e:
        logger.error(f"Error in periodic scan: {str(e)}")
        raise

@celery_app.task(name="backend.tasks.analysis_tasks.analyze_user_risks_opportunities")
async def analyze_user_risks_opportunities(user_id: str, config_dict: Dict[str, Any]):
    """
    Analyze risks and opportunities for a specific user
    """
    try:
        logger.info(f"Analyzing risks/opportunities for user {user_id}")
        
        # Initialize services
        analysis_service = AnalysisService()
        subjective_service = SubjectiveInputService()
        objective_service = ObjectiveDataService()
        alert_service = AlertService()
        
        config = RiskOpportunityDetectionConfig(**config_dict)
        user_uuid = UUID(user_id)
        
        # Gather recent data
        lookback_date = datetime.utcnow() - timedelta(days=config.lookback_days)
        
        data = {
            "subjective_entries": [],
            "objective_data": [],
            "insights": [],
            "swot_items": []
        }
        
        # Get recent subjective entries
        if config.include_subjective:
            entries = await subjective_service.list_entries(
                user_id=user_uuid,
                start_date=lookback_date,
                limit=50
            )
            data["subjective_entries"] = [entry.dict() for entry in entries]
        
        # Get recent objective data
        if config.include_objective:
            datasets = await objective_service.list_datasets(user_id=user_uuid)
            for dataset in datasets[:5]:  # Limit to recent 5 datasets
                entries = await objective_service.list_entries(
                    dataset_id=dataset.id,
                    limit=20
                )
                data["objective_data"].extend([entry.dict() for entry in entries])
        
        # Get recent insights
        insights = await analysis_service.list_insights(
            user_id=user_uuid,
            created_after=lookback_date
        )
        data["insights"] = [insight.dict() for insight in insights]
        
        # Get SWOT items if configured
        if config.include_swot:
            analyses = await analysis_service.list_swot_analyses(user_id=user_uuid)
            for analysis in analyses[:2]:  # Recent 2 analyses
                items = await analysis_service.list_swot_items(analysis_id=analysis.id)
                data["swot_items"].extend([item.dict() for item in items])
        
        # Detect risks
        risks = await detect_risks(data, config_dict)
        
        # Detect opportunities
        opportunities = await detect_opportunities(data, config_dict)
        
        # Create alerts for significant findings
        await create_alerts_from_findings(
            user_uuid, 
            risks, 
            opportunities, 
            alert_service
        )
        
        logger.info(
            f"Completed analysis for user {user_id}: "
            f"{len(risks)} risks, {len(opportunities)} opportunities detected"
        )
        
    except Exception as e:
        logger.error(f"Error analyzing user {user_id}: {str(e)}")
        raise

async def detect_risks(data: Dict[str, Any], config_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Use AI to detect risks from the data
    """
    try:
        # Initialize the risk detection skill
        skill = kernel_service.import_skill(
            "RiskOpportunityDetectionSkill",
            "analysis_skills"
        )
        
        # Run risk detection
        context = kernel_service.create_new_context()
        context["data"] = json.dumps(data)
        context["config"] = json.dumps(config_dict)
        
        result = await kernel_service.run_async(
            skill["detect_risks"],
            input_context=context
        )
        
        # Parse results
        risks = json.loads(result.result)
        
        # Calculate risk scores
        context["risks"] = json.dumps(risks)
        score_result = await kernel_service.run_async(
            skill["calculate_risk_scores"],
            input_context=context
        )
        
        scored_risks = json.loads(score_result.result)
        
        return scored_risks
        
    except Exception as e:
        logger.error(f"Error detecting risks: {str(e)}")
        return []

async def detect_opportunities(data: Dict[str, Any], config_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Use AI to detect opportunities from the data
    """
    try:
        # Initialize the risk detection skill
        skill = kernel_service.import_skill(
            "RiskOpportunityDetectionSkill",
            "analysis_skills"
        )
        
        # Run opportunity detection
        context = kernel_service.create_new_context()
        context["data"] = json.dumps(data)
        context["config"] = json.dumps(config_dict)
        
        result = await kernel_service.run_async(
            skill["detect_opportunities"],
            input_context=context
        )
        
        # Parse results
        opportunities = json.loads(result.result)
        
        return opportunities
        
    except Exception as e:
        logger.error(f"Error detecting opportunities: {str(e)}")
        return []

async def create_alerts_from_findings(
    user_id: UUID,
    risks: List[Dict[str, Any]],
    opportunities: List[Dict[str, Any]],
    alert_service: AlertService
):
    """
    Create alerts from detected risks and opportunities
    """
    config = RiskOpportunityDetectionConfig()
    
    # Create alerts for risks
    for risk in risks:
        if risk.get("confidence_score", 0) >= config.min_confidence_score:
            alert_data = AlertCreate(
                user_id=user_id,
                alert_type=AlertType.RISK,
                severity=risk.get("severity", AlertSeverity.MEDIUM),
                title=risk.get("title", "Detected Risk"),
                description=risk.get("description", ""),
                category=risk.get("category"),
                impact_score=risk.get("impact_score"),
                likelihood_score=risk.get("likelihood_score"),
                source_type="periodic_analysis",
                source_details={
                    "indicators": risk.get("indicators", []),
                    "time_horizon": risk.get("time_horizon", "medium_term"),
                    "related_data_points": risk.get("related_data_points", [])
                },
                detection_method="ai_analysis",
                detection_details={
                    "model": "risk_detection_skill",
                    "confidence": risk.get("confidence_score")
                },
                confidence_score=risk.get("confidence_score"),
                recommendations=risk.get("recommendations", [])
            )
            
            try:
                await alert_service.create_alert(alert_data)
            except Exception as e:
                logger.error(f"Error creating risk alert: {str(e)}")
    
    # Create alerts for opportunities
    for opportunity in opportunities:
        if opportunity.get("confidence_score", 0) >= config.min_confidence_score:
            alert_data = AlertCreate(
                user_id=user_id,
                alert_type=AlertType.OPPORTUNITY,
                severity=AlertSeverity.HIGH if opportunity.get("impact_score", 0) > 80 else AlertSeverity.MEDIUM,
                title=opportunity.get("title", "Detected Opportunity"),
                description=opportunity.get("description", ""),
                category=opportunity.get("category"),
                impact_score=opportunity.get("impact_score"),
                likelihood_score=opportunity.get("likelihood_score"),
                source_type="periodic_analysis",
                source_details={
                    "indicators": opportunity.get("indicators", []),
                    "time_horizon": opportunity.get("time_horizon", "medium_term"),
                    "resource_requirements": opportunity.get("resource_requirements", "medium"),
                    "related_data_points": opportunity.get("related_data_points", [])
                },
                detection_method="ai_analysis",
                detection_details={
                    "model": "opportunity_detection_skill",
                    "confidence": opportunity.get("confidence_score")
                },
                confidence_score=opportunity.get("confidence_score"),
                recommendations=opportunity.get("recommendations", [])
            )
            
            try:
                await alert_service.create_alert(alert_data)
            except Exception as e:
                logger.error(f"Error creating opportunity alert: {str(e)}")

@celery_app.task(name="backend.tasks.analysis_tasks.analyze_single_entry")
async def analyze_single_entry(entry_type: str, entry_id: str, user_id: str):
    """
    Analyze a single new entry (subjective or objective) for immediate risks/opportunities
    """
    try:
        logger.info(f"Analyzing single {entry_type} entry {entry_id} for user {user_id}")
        
        # This would analyze just the new entry for immediate risks/opportunities
        # Implementation would be similar but focused on single entry
        
        pass
        
    except Exception as e:
        logger.error(f"Error analyzing single entry: {str(e)}")
        raise