"""
AnalyzeLogs Azure Function
Analyzes CEO log entries for patterns, insights, and trends
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
from shared.validation import validate_analyze_request


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Main function entry point"""
    start_time = time.time()
    logging.info('AnalyzeLogs function processing request')
    
    try:
        # Get parameters from query string or body
        if req.method == 'GET':
            params = dict(req.params)
        else:
            params = req.get_json()
        
        # Validate request
        validated_request = validate_analyze_request(params)
        
        # Generate cache key
        cache_key = generate_cache_key(
            "analyze",
            validated_request.userId,
            {
                "timeframe": validated_request.timeframe,
                "focusArea": validated_request.focusArea
            }
        )
        
        # Check cache
        cached_result = get_cache(cache_key)
        if cached_result:
            logging.info("Cache hit for analysis")
            duration_ms = (time.time() - start_time) * 1000
            
            return func.HttpResponse(
                body=json.dumps(cached_result),
                status_code=200,
                headers={
                    "Content-Type": "application/json",
                    "X-Cache": "HIT",
                    "X-Duration-Ms": str(int(duration_ms))
                }
            )
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = datetime.utcnow()
        
        if validated_request.timeframe == "week":
            start_date = end_date - timedelta(days=7)
        elif validated_request.timeframe == "month":
            start_date = end_date - timedelta(days=30)
        elif validated_request.timeframe == "quarter":
            start_date = end_date - timedelta(days=90)
        elif validated_request.timeframe == "year":
            start_date = end_date - timedelta(days=365)
        elif validated_request.timeframe == "all":
            start_date = datetime(2000, 1, 1)  # Effectively all entries
        
        # Query logs within timeframe
        query = "SELECT * FROM c WHERE c.userId = @userId AND c.timestamp >= @startDate AND c.timestamp <= @endDate ORDER BY c.timestamp DESC"
        parameters = [
            {"name": "@userId", "value": validated_request.userId},
            {"name": "@startDate", "value": start_date.isoformat()},
            {"name": "@endDate", "value": end_date.isoformat()}
        ]
        
        container = get_log_container()
        logs = query_items(container, query, parameters)
        
        # Perform analysis
        analysis = analyze_logs_by_focus(logs, validated_request.focusArea)
        
        # Add metadata
        response_data = {
            **analysis,
            "userId": validated_request.userId,
            "timeframe": validated_request.timeframe,
            "focusArea": validated_request.focusArea,
            "dateRange": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "totalEntriesAnalyzed": len(logs),
            "analyzedAt": datetime.utcnow().isoformat()
        }
        
        # Cache the result
        set_cache(cache_key, response_data, ttl_seconds=900)  # 15 minute cache
        
        # Track performance
        duration_ms = (time.time() - start_time) * 1000
        logging.info(f"AnalyzeLogs completed in {duration_ms:.0f}ms, analyzed {len(logs)} entries")
        
        return func.HttpResponse(
            body=json.dumps(response_data),
            status_code=200,
            headers={
                "Content-Type": "application/json",
                "X-Cache": "MISS",
                "X-Duration-Ms": str(int(duration_ms))
            }
        )
        
    except ValueError as e:
        logging.error(f"Validation error: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"success": False, "error": str(e)}),
            status_code=400,
            headers={"Content-Type": "application/json"}
        )
        
    except Exception as e:
        logging.error(f"Error in AnalyzeLogs: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"success": False, "error": "Failed to analyze CEO log entries"}),
            status_code=500,
            headers={"Content-Type": "application/json"}
        )


def analyze_logs_by_focus(logs: list, focus_area: str) -> dict:
    """Analyze logs based on focus area"""
    insights = []
    themes = []
    recommendations = []
    metrics = {}
    
    # Common analysis
    total_words = sum(log['metadata']['wordCount'] for log in logs)
    avg_words_per_entry = round(total_words / len(logs)) if logs else 0
    
    # Sentiment distribution
    sentiment_counts = {"positive": 0, "negative": 0, "neutral": 0}
    for log in logs:
        sentiment = log['logEntry']['sentiment']
        sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
    
    # Tag frequency
    tag_frequency = {}
    for log in logs:
        for tag in log.get('tags', []):
            tag_frequency[tag] = tag_frequency.get(tag, 0) + 1
    
    top_tags = sorted(tag_frequency.items(), key=lambda x: x[1], reverse=True)[:10]
    top_tags = [{"tag": tag, "count": count} for tag, count in top_tags]
    
    # Focus area specific analysis
    if focus_area == "risks":
        risk_entries = [log for log in logs if log['analysis']['involvesRisk']]
        risk_count = len(risk_entries)
        risk_percentage = round((risk_count / len(logs)) * 100) if logs else 0
        
        metrics['riskMentions'] = risk_count
        metrics['riskPercentage'] = risk_percentage
        
        if risk_count > 0:
            insights.append(f"{risk_count} entries ({risk_percentage}%) contain risk indicators")
            
            # Extract risk themes
            risk_themes = {}
            for entry in risk_entries:
                for risk in entry['analysis']['riskFactors']:
                    theme = extract_risk_theme(risk)
                    if theme:
                        risk_themes[theme] = risk_themes.get(theme, 0) + 1
            
            top_risk_themes = sorted(risk_themes.keys())[:3]
            themes.extend([f"Risk: {theme}" for theme in top_risk_themes])
            
            recommendations.append("Develop comprehensive risk mitigation strategies")
            recommendations.append("Schedule risk assessment review with leadership team")
            
            if risk_percentage > 30:
                insights.append("High concentration of risk concerns requires immediate attention")
                recommendations.append("Prioritize risk management in next executive meeting")
    
    elif focus_area == "opportunities":
        opp_entries = [log for log in logs if len(log['analysis']['opportunities']) > 0 or 
                      any("opportunity" in tag for tag in log.get('tags', []))]
        opp_count = len(opp_entries)
        opp_percentage = round((opp_count / len(logs)) * 100) if logs else 0
        
        metrics['opportunityMentions'] = opp_count
        metrics['opportunityPercentage'] = opp_percentage
        
        if opp_count > 0:
            insights.append(f"{opp_count} entries ({opp_percentage}%) identify growth opportunities")
            themes.extend(["Growth Mindset", "Innovation Focus"])
            recommendations.append("Create opportunity evaluation matrix")
            recommendations.append("Allocate resources for high-potential initiatives")
            
            # Positive sentiment correlation
            positive_opp_count = sum(1 for e in opp_entries if e['logEntry']['sentiment'] == 'positive')
            if positive_opp_count > opp_count * 0.7:
                insights.append("Strong positive sentiment around identified opportunities")
    
    elif focus_area == "team":
        team_entries = [log for log in logs if any(tag in ["team", "people", "culture", "talent"] 
                                                  for tag in log.get('tags', []))]
        team_count = len(team_entries)
        team_percentage = round((team_count / len(logs)) * 100) if logs else 0
        
        metrics['teamMentions'] = team_count
        metrics['teamPercentage'] = team_percentage
        
        if team_count > 0:
            insights.append(f"Team and culture topics discussed in {team_count} entries ({team_percentage}%)")
            themes.extend(["People Focus", "Organizational Culture"])
            recommendations.append("Conduct team health assessment")
            recommendations.append("Implement leadership development program")
            
            # Check sentiment
            negative_team_count = sum(1 for e in team_entries if e['logEntry']['sentiment'] == 'negative')
            if negative_team_count > team_count * 0.4:
                insights.append("Concerning sentiment patterns in team-related entries")
                recommendations.append("Schedule one-on-one sessions with key team members")
    
    elif focus_area == "market":
        market_entries = [log for log in logs if any(tag in ["market", "customer", "competitor", "industry"] 
                                                    for tag in log.get('tags', []))]
        market_count = len(market_entries)
        market_percentage = round((market_count / len(logs)) * 100) if logs else 0
        
        metrics['marketMentions'] = market_count
        metrics['marketPercentage'] = market_percentage
        
        if market_count > 0:
            insights.append(f"Market dynamics discussed in {market_count} entries ({market_percentage}%)")
            themes.extend(["Market Awareness", "Competitive Intelligence"])
            recommendations.append("Commission comprehensive market analysis")
            recommendations.append("Review and update competitive positioning")
    
    else:  # general analysis
        # Strategic alignment
        strategic_count = sum(1 for log in logs if log['analysis']['strategicRelevance'])
        strategic_percentage = round((strategic_count / len(logs)) * 100) if logs else 0
        
        metrics['strategicRelevance'] = strategic_percentage
        metrics['sentimentDistribution'] = sentiment_counts
        metrics['avgWordsPerEntry'] = avg_words_per_entry
        
        insights.append(f"{strategic_percentage}% of entries have strategic relevance")
        insights.append(f"Average entry length: {avg_words_per_entry} words")
        
        # Identify dominant themes from tags
        if top_tags:
            themes.extend([t['tag'] for t in top_tags[:3]])
        
        # Action items trend
        action_items_count = sum(1 for log in logs if log['analysis']['hasActionItems'])
        if action_items_count > 0:
            insights.append(f"{action_items_count} entries contain action items")
            recommendations.append("Review and prioritize identified action items")
        
        # Urgency analysis
        urgent_count = sum(1 for log in logs if log['analysis']['isUrgent'])
        if urgent_count > 0:
            insights.append(f"{urgent_count} urgent items require immediate attention")
            recommendations.append("Address urgent items in next leadership meeting")
        
        recommendations.append("Maintain balanced focus across all strategic dimensions")
    
    return {
        "insights": insights,
        "themes": list(set(themes)),  # Remove duplicates
        "recommendations": recommendations,
        "metrics": metrics,
        "summary": generate_analysis_summary(logs, focus_area),
        "topTags": top_tags
    }


def extract_risk_theme(risk_description: str) -> str:
    """Extract risk theme from description"""
    risk_keywords = {
        "Financial": ["revenue", "cost", "budget", "financial", "profit"],
        "Operational": ["process", "efficiency", "operations", "system"],
        "Market": ["competitor", "market", "customer", "demand"],
        "Technology": ["technology", "system", "infrastructure", "security"],
        "Talent": ["team", "talent", "employee", "retention", "culture"]
    }
    
    lower_risk = risk_description.lower()
    
    for theme, keywords in risk_keywords.items():
        if any(keyword in lower_risk for keyword in keywords):
            return theme
    
    return None


def generate_analysis_summary(logs: list, focus_area: str) -> str:
    """Generate analysis summary"""
    if not logs:
        return "No entries found for the specified timeframe."
    
    focus_descriptions = {
        "risks": "risk management and mitigation strategies",
        "opportunities": "growth opportunities and innovation potential",
        "team": "team dynamics and organizational culture",
        "market": "market conditions and competitive landscape",
        "general": "overall strategic themes and priorities"
    }
    
    description = focus_descriptions.get(focus_area, "strategic insights")
    
    if logs:
        start_date = datetime.fromisoformat(logs[-1]['timestamp'].replace('Z', '+00:00'))
        end_date = datetime.fromisoformat(logs[0]['timestamp'].replace('Z', '+00:00'))
        
        return (f"Analysis of {len(logs)} CEO log entries focused on {description}. "
                f"The entries span from {start_date.strftime('%Y-%m-%d')} "
                f"to {end_date.strftime('%Y-%m-%d')}.")
    
    return f"Analysis focused on {description}."