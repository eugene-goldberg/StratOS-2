"""
GetInsights Azure Function
Provides quick insights and summaries for CEO log entries
"""
import json
import logging
import time
from datetime import datetime, timedelta
import azure.functions as func

# Add parent directory to path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.cosmos_client import get_log_container, query_items
from shared.cache import get_cache, set_cache, generate_cache_key


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Main function entry point"""
    start_time = time.time()
    logging.info('GetInsights function processing request')
    
    try:
        # Get parameters
        user_id = req.params.get('userId')
        insight_type = req.params.get('type', 'summary')  # summary, recent, urgent
        
        if not user_id:
            return func.HttpResponse(
                body=json.dumps({"error": "userId is required"}),
                status_code=400,
                headers={"Content-Type": "application/json"}
            )
        
        # Generate cache key
        cache_key = generate_cache_key("insights", user_id, {"type": insight_type})
        
        # Check cache
        cached_result = get_cache(cache_key)
        if cached_result:
            return func.HttpResponse(
                body=json.dumps(cached_result),
                status_code=200,
                headers={"Content-Type": "application/json", "X-Cache": "HIT"}
            )
        
        container = get_log_container()
        
        if insight_type == "summary":
            # Get summary of recent activity
            result = get_activity_summary(container, user_id)
        elif insight_type == "recent":
            # Get most recent entries
            result = get_recent_entries(container, user_id)
        elif insight_type == "urgent":
            # Get urgent items
            result = get_urgent_items(container, user_id)
        else:
            return func.HttpResponse(
                body=json.dumps({"error": "Invalid insight type"}),
                status_code=400,
                headers={"Content-Type": "application/json"}
            )
        
        # Cache result
        set_cache(cache_key, result, ttl_seconds=600)  # 10 minute cache
        
        duration_ms = (time.time() - start_time) * 1000
        logging.info(f"GetInsights completed in {duration_ms:.0f}ms")
        
        return func.HttpResponse(
            body=json.dumps(result),
            status_code=200,
            headers={"Content-Type": "application/json", "X-Cache": "MISS"}
        )
        
    except Exception as e:
        logging.error(f"Error in GetInsights: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"error": "Failed to get insights"}),
            status_code=500,
            headers={"Content-Type": "application/json"}
        )


def get_activity_summary(container, user_id: str) -> dict:
    """Get activity summary for the user"""
    # Query last 30 days
    start_date = (datetime.utcnow() - timedelta(days=30)).isoformat()
    
    query = "SELECT * FROM c WHERE c.userId = @userId AND c.timestamp >= @startDate"
    parameters = [
        {"name": "@userId", "value": user_id},
        {"name": "@startDate", "value": start_date}
    ]
    
    logs = query_items(container, query, parameters)
    
    # Calculate summary metrics
    total_entries = len(logs)
    
    if total_entries == 0:
        return {
            "type": "summary",
            "period": "last_30_days",
            "metrics": {
                "totalEntries": 0,
                "avgEntriesPerWeek": 0,
                "sentimentBreakdown": {"positive": 0, "negative": 0, "neutral": 0},
                "topCategories": [],
                "urgentItems": 0,
                "actionItems": 0
            },
            "message": "No log entries found in the last 30 days"
        }
    
    # Sentiment breakdown
    sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
    category_counts = {}
    urgent_count = 0
    action_count = 0
    
    for log in logs:
        sentiment_counts[log['logEntry']['sentiment']] += 1
        
        category = log.get('category', 'general')
        category_counts[category] = category_counts.get(category, 0) + 1
        
        if log['analysis']['isUrgent']:
            urgent_count += 1
        if log['analysis']['hasActionItems']:
            action_count += 1
    
    # Top categories
    top_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    
    return {
        "type": "summary",
        "period": "last_30_days",
        "metrics": {
            "totalEntries": total_entries,
            "avgEntriesPerWeek": round(total_entries / 4.3, 1),
            "sentimentBreakdown": sentiment_counts,
            "topCategories": [{"name": cat, "count": count} for cat, count in top_categories],
            "urgentItems": urgent_count,
            "actionItems": action_count
        },
        "insights": generate_summary_insights(logs, sentiment_counts, urgent_count)
    }


def get_recent_entries(container, user_id: str, limit: int = 5) -> dict:
    """Get most recent log entries"""
    query = "SELECT * FROM c WHERE c.userId = @userId ORDER BY c.timestamp DESC"
    parameters = [{"name": "@userId", "value": user_id}]
    
    all_logs = query_items(container, query, parameters)
    recent_logs = all_logs[:limit]
    
    entries = []
    for log in recent_logs:
        entries.append({
            "id": log['id'],
            "timestamp": log['timestamp'],
            "category": log['category'],
            "summary": log['analysis']['summary'],
            "sentiment": log['logEntry']['sentiment'],
            "tags": log['tags'][:3],
            "isUrgent": log['analysis']['isUrgent'],
            "hasActionItems": log['analysis']['hasActionItems']
        })
    
    return {
        "type": "recent",
        "entries": entries,
        "totalAvailable": len(all_logs)
    }


def get_urgent_items(container, user_id: str) -> dict:
    """Get urgent items requiring attention"""
    query = """
    SELECT * FROM c 
    WHERE c.userId = @userId 
    AND c.analysis.isUrgent = true 
    ORDER BY c.timestamp DESC
    """
    parameters = [{"name": "@userId", "value": user_id}]
    
    urgent_logs = query_items(container, query, parameters)
    
    items = []
    for log in urgent_logs[:10]:  # Limit to 10 most recent urgent items
        items.append({
            "id": log['id'],
            "timestamp": log['timestamp'],
            "category": log['category'],
            "summary": log['analysis']['summary'],
            "actionItems": log['analysis']['actionItems'][:3],
            "tags": log['tags'][:3]
        })
    
    return {
        "type": "urgent",
        "count": len(urgent_logs),
        "items": items,
        "recommendation": "Review and address these urgent items in your next leadership meeting"
    }


def generate_summary_insights(logs: list, sentiment_counts: dict, urgent_count: int) -> list:
    """Generate insights from summary data"""
    insights = []
    
    total = len(logs)
    
    # Sentiment insights
    if sentiment_counts['positive'] > total * 0.6:
        insights.append("Predominantly positive sentiment indicates strong momentum")
    elif sentiment_counts['negative'] > total * 0.4:
        insights.append("High concentration of concerns requires attention")
    
    # Urgency insights
    if urgent_count > total * 0.2:
        insights.append(f"{urgent_count} urgent items need immediate attention")
    
    # Activity insights
    if total < 10:
        insights.append("Low activity - consider more frequent strategic reflections")
    elif total > 50:
        insights.append("High engagement with strategic logging")
    
    return insights