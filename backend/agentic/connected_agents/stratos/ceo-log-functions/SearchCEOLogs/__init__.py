"""
SearchCEOLogs Azure Function
Searches CEO log entries with advanced filtering and caching
"""
import json
import logging
import time
import azure.functions as func

# Add parent directory to path for imports
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.cosmos_client import get_log_container, query_items
from shared.cache import get_cache, set_cache, generate_cache_key
from shared.analytics import calculate_relevance
from shared.validation import validate_search_request


def main(req: func.HttpRequest) -> func.HttpResponse:
    """Main function entry point"""
    start_time = time.time()
    logging.info('SearchCEOLogs function processing request')
    
    try:
        # Get parameters from query string or body
        if req.method == 'GET':
            params = dict(req.params)
            # Convert string values to appropriate types
            if 'limit' in params:
                params['limit'] = int(params['limit'])
            if 'offset' in params:
                params['offset'] = int(params['offset'])
        else:
            params = req.get_json()
        
        # Validate request
        validated_request = validate_search_request(params)
        
        # Generate cache key
        cache_key = generate_cache_key(
            "search",
            validated_request.userId,
            {
                "query": validated_request.query,
                "category": validated_request.category,
                "tags": validated_request.tags,
                "dateRange": validated_request.dateRange,
                "limit": validated_request.limit,
                "offset": validated_request.offset
            }
        )
        
        # Check cache
        cached_result = get_cache(cache_key)
        if cached_result:
            logging.info("Cache hit for search query")
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
        
        # Build Cosmos DB query
        query = "SELECT * FROM c WHERE c.userId = @userId"
        parameters = [{"name": "@userId", "value": validated_request.userId}]
        
        # Add search conditions
        if validated_request.query:
            query += " AND (CONTAINS(LOWER(c.logEntry.content), LOWER(@query))"
            query += " OR CONTAINS(LOWER(c.analysis.summary), LOWER(@query)))"
            parameters.append({"name": "@query", "value": validated_request.query})
        
        if validated_request.category:
            query += " AND c.category = @category"
            parameters.append({"name": "@category", "value": validated_request.category})
        
        if validated_request.tags:
            tag_conditions = []
            for i, tag in enumerate(validated_request.tags):
                tag_conditions.append(f"ARRAY_CONTAINS(c.tags, @tag{i})")
                parameters.append({"name": f"@tag{i}", "value": tag})
            query += f" AND ({' OR '.join(tag_conditions)})"
        
        if validated_request.dateRange:
            if validated_request.dateRange.get('start'):
                query += " AND c.timestamp >= @startDate"
                parameters.append({"name": "@startDate", "value": validated_request.dateRange['start']})
            if validated_request.dateRange.get('end'):
                query += " AND c.timestamp <= @endDate"
                parameters.append({"name": "@endDate", "value": validated_request.dateRange['end']})
        
        # Add ordering
        query += " ORDER BY c.timestamp DESC"
        
        # Execute query
        container = get_log_container()
        all_results = query_items(container, query, parameters)
        
        # Apply pagination
        start_idx = validated_request.offset
        end_idx = start_idx + validated_request.limit
        paginated_results = all_results[start_idx:end_idx]
        
        # Calculate relevance scores and format results
        results = []
        for entry in paginated_results:
            relevance_score = calculate_relevance(entry, validated_request.query)
            
            results.append({
                "id": entry['id'],
                "summary": entry['analysis']['summary'],
                "category": entry['category'],
                "tags": entry['tags'][:3],  # Top 3 tags
                "timestamp": entry['timestamp'],
                "relevanceScore": round(relevance_score, 2),
                "metadata": {
                    "hasActionItems": entry['analysis']['hasActionItems'],
                    "isUrgent": entry['analysis']['isUrgent'],
                    "sentiment": entry['logEntry']['sentiment'],
                    "wordCount": entry['metadata']['wordCount']
                }
            })
        
        # Sort by relevance if search query provided
        if validated_request.query:
            results.sort(key=lambda x: x['relevanceScore'], reverse=True)
        
        # Prepare response
        response_data = {
            "query": validated_request.query or "",
            "category": validated_request.category,
            "tags": validated_request.tags,
            "totalResults": len(all_results),
            "resultsReturned": len(results),
            "offset": validated_request.offset,
            "limit": validated_request.limit,
            "results": results,
            "searchCompletedAt": datetime.utcnow().isoformat()
        }
        
        # Cache the result
        set_cache(cache_key, response_data, ttl_seconds=300)
        
        # Track performance
        duration_ms = (time.time() - start_time) * 1000
        logging.info(f"SearchCEOLogs completed in {duration_ms:.0f}ms, found {len(all_results)} total results")
        
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
        logging.error(f"Error in SearchCEOLogs: {str(e)}")
        return func.HttpResponse(
            body=json.dumps({"success": False, "error": "Failed to search CEO log entries"}),
            status_code=500,
            headers={"Content-Type": "application/json"}
        )


# Import datetime at the top
from datetime import datetime