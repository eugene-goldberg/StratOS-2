"""Debug version of SaveCEOLog"""
import json
import logging
import azure.functions as func
import traceback

def main(req: func.HttpRequest) -> func.HttpResponse:
    """Debug save function"""
    logging.info('DebugSave function called')
    
    try:
        # Get request body
        req_body = req.get_json()
        logging.info(f"Request body: {json.dumps(req_body)}")
        
        # Import modules to test
        try:
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            
            from shared.models import SaveCEOLogRequest
            logging.info("Successfully imported models")
            
            # Try to validate
            request = SaveCEOLogRequest(**req_body)
            logging.info(f"Validation successful: {request}")
            
            # Try to import analytics
            from shared.analytics import analyze_content_with_ai
            logging.info("Successfully imported analytics")
            
            # Try to analyze
            result = analyze_content_with_ai(request.content)
            logging.info(f"Analysis result: {result}")
            
            return func.HttpResponse(
                json.dumps({
                    "success": True,
                    "debug": "All imports and basic operations work",
                    "analysis": {
                        "sentiment": result.sentiment,
                        "summary": result.summary[:100] + "..." if len(result.summary) > 100 else result.summary
                    }
                }),
                status_code=200
            )
            
        except Exception as e:
            logging.error(f"Import/validation error: {str(e)}")
            logging.error(traceback.format_exc())
            return func.HttpResponse(
                json.dumps({
                    "success": False,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                }),
                status_code=500
            )
            
    except Exception as e:
        logging.error(f"Outer error: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "success": False,
                "error": str(e),
                "type": type(e).__name__
            }),
            status_code=500
        )