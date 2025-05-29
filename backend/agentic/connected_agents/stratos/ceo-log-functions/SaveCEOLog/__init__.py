"""
SaveCEOLog Azure Function
Saves CEO log entries to Cosmos DB with AI analysis
"""
import json
import logging
import time
from datetime import datetime
import azure.functions as func

# Add parent directory to path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.models import CEOLogEntry, LogEntryContent, LogMetadata, LogAnalysis
from shared.cosmos_client import get_log_container, create_item
from shared.cache import invalidate_cache
from shared.analytics import analyze_content_with_ai
from shared.validation import validate_save_request


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Main function entry point"""
    start_time = time.time()
    logging.info('SaveCEOLog function processing request')
    
    try:
        # Parse request body
        req_body = req.get_json()
        
        # Validate request
        validated_request = validate_save_request(req_body)
        
        # Analyze content with AI
        analysis = analyze_content_with_ai(validated_request.content)
        
        # Create log entry
        entry = CEOLogEntry(
            userId=validated_request.userId,
            timestamp=datetime.utcnow(),
            logEntry=LogEntryContent(
                content=validated_request.content,
                sentiment=analysis.sentiment,
                confidence=analysis.confidence
            ),
            category=validated_request.category,
            tags=[*validated_request.tags, *analysis.generatedTags],
            strategicThemes=analysis.themes,
            metadata=LogMetadata(
                source=validated_request.metadata.get('source'),
                duration=validated_request.metadata.get('duration'),
                location=validated_request.metadata.get('location'),
                device=validated_request.metadata.get('device'),
                sessionId=validated_request.metadata.get('sessionId'),
                isVoice=validated_request.metadata.get('isVoice', False),
                wordCount=len(validated_request.content.split())
            ),
            analysis=LogAnalysis(
                summary=analysis.summary,
                keyInsights=analysis.insights,
                actionItems=analysis.actionItems,
                riskFactors=analysis.risks,
                opportunities=analysis.opportunities,
                hasActionItems=len(analysis.actionItems) > 0,
                isUrgent=analysis.isUrgent,
                involvesRisk=len(analysis.risks) > 0,
                strategicRelevance=len(analysis.themes) > 0
            )
        )
        
        # Add temporal tags
        now = datetime.utcnow()
        entry.tags.extend([
            f"week_{now.isocalendar()[1]}",
            f"month_{now.strftime('%B').lower()}",
            f"q{(now.month - 1) // 3 + 1}_{now.year}"
        ])
        
        # Remove duplicate tags
        entry.tags = list(set(entry.tags))
        
        # Save to Cosmos DB
        container = get_log_container()
        saved_entry = create_item(container, entry.dict_for_cosmos())
        
        # Invalidate relevant caches
        invalidate_cache(validated_request.userId, ["summary", "analytics"])
        
        # Track performance
        duration_ms = (time.time() - start_time) * 1000
        logging.info(f"SaveCEOLog completed in {duration_ms:.0f}ms")
        
        # Prepare response
        response_data = {
            "success": True,
            "entryId": saved_entry['id'],
            "message": f"CEO log entry saved successfully in category: {entry.category}",
            "summary": analysis.summary,
            "tags": entry.tags[:5],  # Top 5 tags
            "metadata": {
                "wordCount": entry.metadata.wordCount,
                "hasActionItems": entry.analysis.hasActionItems,
                "isUrgent": entry.analysis.isUrgent,
                "involvesRisk": entry.analysis.involvesRisk
            }
        }
        
        return func.HttpResponse(
            body=json.dumps(response_data),
            status_code=201,
            headers={"Content-Type": "application/json"}
        )
        
    except ValueError as e:
        logging.error(f"Validation error: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"success": False, "error": str(e)}),
            status_code=400,
            headers={"Content-Type": "application/json"}
        )
        
    except Exception as e:
        import traceback
        error_details = {
            "success": False,
            "error": "Failed to save CEO log entry",
            "details": str(e),
            "type": type(e).__name__
        }
        logging.error(f"Error in SaveCEOLog: {str(e)}")
        logging.error(traceback.format_exc())
        
        # Add more details in debug mode
        if os.environ.get("DEBUG_MODE"):
            error_details["traceback"] = traceback.format_exc()
        
        return func.HttpResponse(
            body=json.dumps(error_details),
            status_code=500,
            headers={"Content-Type": "application/json"}
        )