from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request, WebSocket
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from uuid import UUID

from ..models.user import UserResponse
from ..dependencies import get_current_active_user
import json
import base64
from ..models.subjective_input import (
    LogEntry,
    LogEntryCreate,
    LogEntryUpdate,
    LogEntryType,
    StrategicCanvas,
    StrategicCanvasCreate,
    CanvasElementCreate
)
from ..services.subjective_input_service import SubjectiveInputService
from ..ai.kernel_service import kernel_service

router = APIRouter(dependencies=[Depends(get_current_active_user)])
input_service = SubjectiveInputService()

# CEO's Log Endpoints

@router.post("/log", response_model=LogEntry, status_code=status.HTTP_201_CREATED)
async def create_log_entry(entry_data: LogEntryCreate, user_id: UUID):
    """
    Create a new CEO Log entry with text/voice input
    """
    # Create the log entry
    entry = await input_service.create_log_entry(entry_data, user_id)
    
    # Process with AI for tagging and insights
    await process_log_entry_with_ai(entry.id)
    
    return entry

@router.get("/log/{entry_id}", response_model=LogEntry)
async def get_log_entry(entry_id: UUID):
    """
    Get a CEO Log entry by ID
    """
    entry = await input_service.get_log_entry(entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Log entry not found")
    return entry

@router.get("/log", response_model=List[LogEntry])
async def list_log_entries(
    user_id: UUID,
    limit: int = 20,
    offset: int = 0,
    entry_type: Optional[str] = None,
    tag: Optional[str] = None
):
    """
    List CEO Log entries with optional filtering
    """
    return await input_service.list_log_entries(user_id, limit, offset, entry_type, tag)

@router.put("/log/{entry_id}", response_model=LogEntry)
async def update_log_entry(entry_id: UUID, entry_data: LogEntryUpdate):
    """
    Update a CEO Log entry
    """
    updated = await input_service.update_log_entry(entry_id, entry_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Log entry not found")
    
    # Re-process with AI
    await process_log_entry_with_ai(entry_id)
    
    return updated

@router.delete("/log/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_log_entry(entry_id: UUID):
    """
    Delete a CEO Log entry
    """
    deleted = await input_service.delete_log_entry(entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Log entry not found")
    return {"status": "success"}

@router.post("/log/voice", response_model=LogEntry, status_code=status.HTTP_201_CREATED)
async def create_voice_log_entry(audio_file: UploadFile = File(...), user_id: UUID = None):
    """
    Create a new CEO Log entry from voice input (file upload)
    """
    # Process audio to text using Azure Speech Services
    text_content = await input_service.process_voice_to_text(audio_file)
    
    # Create entry
    entry_data = LogEntryCreate(content=text_content)
    entry = await input_service.create_log_entry(entry_data, user_id)
    
    # Process with AI
    await process_log_entry_with_ai(entry.id)
    
    return entry

@router.post("/voice-note/stream/start")
async def start_voice_streaming(request: Request, user_id: UUID):
    """
    Start a voice streaming session for real-time transcription
    
    Returns a stream ID that should be used for subsequent audio chunk uploads
    """
    try:
        # Parse request body
        body = await request.json()
        sample_rate = body.get("sampleRate", 16000)
        bits_per_sample = body.get("bitsPerSample", 16)
        channels = body.get("channels", 1)
        
        # Initialize stream via Semantic Kernel skill
        result = await kernel_service.invoke_semantic_function(
            skill_name="VoiceInput",
            function_name="process_streaming_audio",
            input_text="",
            variables={
                "sample_rate": str(sample_rate),
                "bits_per_sample": str(bits_per_sample),
                "channels": str(channels)
            }
        )
        
        # Parse result
        stream_data = json.loads(result)
        
        return JSONResponse(content=stream_data)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "status": "failed"}
        )

@router.post("/voice-note/stream/chunk")
async def process_voice_chunk(request: Request):
    """
    Process a chunk of audio data in an active streaming session
    """
    try:
        # Parse request body
        body = await request.json()
        stream_id = body.get("streamId")
        audio_chunk = body.get("audioChunk")  # Base64 encoded audio data
        is_final = body.get("isFinal", False)
        
        if not stream_id or not audio_chunk:
            return JSONResponse(
                status_code=400,
                content={"error": "Missing streamId or audioChunk", "status": "failed"}
            )
        
        # Process chunk via Semantic Kernel skill
        result = await kernel_service.invoke_semantic_function(
            skill_name="VoiceInput",
            function_name="process_audio_chunk",
            input_text=audio_chunk,
            variables={
                "stream_id": stream_id,
                "is_final": str(is_final).lower()
            }
        )
        
        # Parse result
        chunk_result = json.loads(result)
        
        # If this was the final chunk and we have transcribed text, create a log entry
        if is_final and chunk_result.get("status") == "completed" and chunk_result.get("text"):
            transcribed_text = chunk_result["text"]
            
            # Create a log entry with the transcribed text
            entry_data = LogEntryCreate(
                content=transcribed_text,
                entry_type=LogEntryType.OTHER
            )
            
            # Get user_id from the query parameters (this would come from auth in production)
            user_id = request.query_params.get("userId")
            if user_id:
                user_id = UUID(user_id)
                
                # Create the log entry
                entry = await input_service.create_log_entry(entry_data, user_id)
                
                # Process with AI
                await process_log_entry_with_ai(entry.id)
                
                # Add entry ID to the response
                chunk_result["entryId"] = str(entry.id)
        
        return JSONResponse(content=chunk_result)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "status": "failed"}
        )

@router.post("/voice-note/stream/cancel")
async def cancel_voice_streaming(request: Request):
    """
    Cancel an active voice streaming session
    """
    try:
        # Parse request body
        body = await request.json()
        stream_id = body.get("streamId")
        
        if not stream_id:
            return JSONResponse(
                status_code=400,
                content={"error": "Missing streamId", "status": "failed"}
            )
        
        # Cancel stream via Semantic Kernel skill
        result = await kernel_service.invoke_semantic_function(
            skill_name="VoiceInput",
            function_name="cancel_streaming",
            input_text=stream_id
        )
        
        # Parse result
        cancel_result = json.loads(result)
        
        return JSONResponse(content=cancel_result)
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "status": "failed"}
        )

@router.websocket("/voice-note/stream/ws")
async def voice_websocket(websocket: WebSocket):
    """
    WebSocket endpoint for real-time voice streaming
    
    This allows for lower-latency voice streaming compared to the HTTP endpoints.
    """
    # Accept the connection
    await websocket.accept()
    
    stream_id = None
    user_id = None
    
    try:
        # Receive initialization message
        init_data = await websocket.receive_json()
        
        # Extract user ID and audio format parameters
        user_id = init_data.get("userId")
        sample_rate = init_data.get("sampleRate", 16000)
        bits_per_sample = init_data.get("bitsPerSample", 16)
        channels = init_data.get("channels", 1)
        
        if not user_id:
            await websocket.send_json({"error": "Missing userId", "status": "failed"})
            await websocket.close()
            return
        
        # Convert user_id to UUID
        try:
            user_id = UUID(user_id)
        except ValueError:
            await websocket.send_json({"error": "Invalid userId format", "status": "failed"})
            await websocket.close()
            return
        
        # Initialize streaming session
        result = await kernel_service.invoke_semantic_function(
            skill_name="VoiceInput",
            function_name="process_streaming_audio",
            input_text="",
            variables={
                "sample_rate": str(sample_rate),
                "bits_per_sample": str(bits_per_sample),
                "channels": str(channels)
            }
        )
        
        # Parse result and extract stream ID
        stream_data = json.loads(result)
        stream_id = stream_data.get("stream_id")
        
        if not stream_id or stream_data.get("status") != "initialized":
            await websocket.send_json({
                "error": "Failed to initialize stream", 
                "status": "failed"
            })
            await websocket.close()
            return
        
        # Send initialization confirmation
        await websocket.send_json({
            "status": "initialized",
            "streamId": stream_id
        })
        
        # Process audio chunks
        while True:
            # Receive message (audio chunk or control message)
            message = await websocket.receive()
            
            # Handle text messages (control commands)
            if message.get("type") == "text":
                command = json.loads(message.get("text", "{}"))
                
                # Handle stop command
                if command.get("command") == "stop":
                    # Final chunk processing
                    result = await kernel_service.invoke_semantic_function(
                        skill_name="VoiceInput",
                        function_name="process_audio_chunk",
                        input_text="",  # Empty chunk
                        variables={
                            "stream_id": stream_id,
                            "is_final": "true"
                        }
                    )
                    
                    # Parse result
                    final_result = json.loads(result)
                    transcribed_text = final_result.get("text", "")
                    
                    # Create log entry if we have text
                    if transcribed_text:
                        # Create entry
                        entry_data = LogEntryCreate(
                            content=transcribed_text,
                            entry_type=LogEntryType.OTHER
                        )
                        entry = await input_service.create_log_entry(entry_data, user_id)
                        
                        # Process with AI
                        await process_log_entry_with_ai(entry.id)
                        
                        # Add entry ID to result
                        final_result["entryId"] = str(entry.id)
                    
                    # Send final result
                    await websocket.send_json(final_result)
                    break
                
                # Handle cancel command
                elif command.get("command") == "cancel":
                    # Cancel the stream
                    result = await kernel_service.invoke_semantic_function(
                        skill_name="VoiceInput",
                        function_name="cancel_streaming",
                        input_text=stream_id
                    )
                    
                    # Parse result
                    cancel_result = json.loads(result)
                    
                    # Send cancel confirmation
                    await websocket.send_json(cancel_result)
                    break
            
            # Handle binary messages (audio data)
            elif message.get("type") == "bytes":
                audio_data = message.get("bytes")
                
                # Encode as Base64 for the function call
                base64_audio = base64.b64encode(audio_data).decode()
                
                # Process the chunk
                result = await kernel_service.invoke_semantic_function(
                    skill_name="VoiceInput",
                    function_name="process_audio_chunk",
                    input_text=base64_audio,
                    variables={
                        "stream_id": stream_id,
                        "is_final": "false"
                    }
                )
                
                # Parse result
                chunk_result = json.loads(result)
                
                # Send processing status
                await websocket.send_json(chunk_result)
    
    except Exception as e:
        # Try to send error message
        try:
            await websocket.send_json({
                "error": str(e),
                "status": "failed"
            })
        except:
            pass
    
    finally:
        # Clean up stream if it was created
        if stream_id:
            try:
                await kernel_service.invoke_semantic_function(
                    skill_name="VoiceInput",
                    function_name="cancel_streaming",
                    input_text=stream_id
                )
            except:
                pass
        
        # Close the WebSocket connection
        await websocket.close()

# Strategic Canvas Endpoints

@router.post("/canvas", response_model=StrategicCanvas, status_code=status.HTTP_201_CREATED)
async def create_canvas(canvas_data: StrategicCanvasCreate, user_id: UUID):
    """
    Create a new Strategic Canvas
    """
    return await input_service.create_canvas(canvas_data, user_id)

@router.get("/canvas/{canvas_id}", response_model=StrategicCanvas)
async def get_canvas(canvas_id: UUID):
    """
    Get a Strategic Canvas by ID
    """
    canvas = await input_service.get_canvas(canvas_id)
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas not found")
    return canvas

@router.get("/canvas", response_model=List[StrategicCanvas])
async def list_canvases(user_id: UUID, limit: int = 10, offset: int = 0):
    """
    List Strategic Canvases
    """
    return await input_service.list_canvases(user_id, limit, offset)

@router.post("/canvas/{canvas_id}/elements", status_code=status.HTTP_201_CREATED)
async def add_canvas_element(canvas_id: UUID, element_data: CanvasElementCreate):
    """
    Add an element to a Strategic Canvas
    """
    canvas = await input_service.get_canvas(canvas_id)
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas not found")
    
    return await input_service.add_canvas_element(canvas_id, element_data)

@router.put("/canvas/{canvas_id}/elements/{element_id}")
async def update_canvas_element(canvas_id: UUID, element_id: UUID, element_data: dict):
    """
    Update a canvas element
    """
    updated = await input_service.update_canvas_element(canvas_id, element_id, element_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Canvas element not found")
    return updated

@router.delete("/canvas/{canvas_id}/elements/{element_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_canvas_element(canvas_id: UUID, element_id: UUID):
    """
    Delete a canvas element
    """
    deleted = await input_service.delete_canvas_element(canvas_id, element_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Canvas element not found")
    return {"status": "success"}

@router.post("/canvas/{canvas_id}/ai-assist")
async def get_canvas_ai_assistance(canvas_id: UUID, prompt: str):
    """
    Get AI assistance for the Strategic Canvas
    """
    canvas = await input_service.get_canvas(canvas_id)
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas not found")
    
    # Process with Semantic Kernel
    response = await input_service.get_canvas_ai_assistance(canvas_id, prompt)
    return {"response": response}

# Helper functions

async def process_log_entry_with_ai(entry_id: UUID):
    """
    Process a log entry with AI for tagging, summarization, and insights
    """
    entry = await input_service.get_log_entry(entry_id)
    if not entry:
        return False
    
    try:
        # Fetch strategic elements to use for tag suggestions
        # In a real implementation, we would fetch WHY/WHAT elements from the database
        # For now, we'll use placeholder data
        strategic_elements = {
            "purpose": "To empower businesses with strategic clarity and data-driven insights for sustainable growth and meaningful impact.",
            "vision": "By 2030, to be the indispensable AI-powered strategic partner for 10,000 leadership teams worldwide.",
            "values": ["Integrity", "Innovation", "Excellence", "Collaboration", "Customer Focus"],
            "strategic_goals": [
                "Achieve 25% market share by Q4 2025",
                "Launch 3 innovative product lines within 18 months",
                "Increase customer retention to 85%"
            ]
        }
        
        # Format strategic elements for the AI
        predefined_elements_list = (
            f"PURPOSE: {strategic_elements['purpose']}\n"
            f"VISION: {strategic_elements['vision']}\n"
            f"VALUES: {', '.join(strategic_elements['values'])}\n"
            f"STRATEGIC GOALS: {'; '.join(strategic_elements['strategic_goals'])}"
        )
        
        # Generate tags using the TaggingSkill
        tags_result = await kernel_service.invoke_semantic_function(
            skill_name="SubjectiveLog",
            function_name="GenerateTags",
            input_text=entry.content,
            variables={"predefined_elements_list": predefined_elements_list}
        )
        
        # Parse tags - should be a JSON array of strings
        try:
            ai_tags = json.loads(tags_result)
            if not isinstance(ai_tags, list):
                ai_tags = [str(tags_result).strip()]
        except json.JSONDecodeError:
            # Fallback in case the JSON parsing fails
            ai_tags = [tag.strip() for tag in tags_result.split(',')]
        
        # Generate summary
        ai_summary = await kernel_service.invoke_semantic_function(
            skill_name="SubjectiveLog",
            function_name="GenerateSummary",
            input_text=entry.content
        )
        
        # Generate insights
        insights_result = await kernel_service.invoke_semantic_function(
            skill_name="SubjectiveLog",
            function_name="GenerateInsights",
            input_text=entry.content
        )
        
        # Split insights into a list, filtering empty lines
        ai_insights = [insight.strip() for insight in insights_result.split('\n') if insight.strip()]
        
        # Update the entry with AI results using the service
        await input_service.update_log_entry_ai_results(
            entry_id, ai_tags, ai_summary, ai_insights
        )
        
        # Also update using the Semantic Kernel skill for database consistency
        await kernel_service.invoke_semantic_function(
            skill_name="LogManagement",
            function_name="update_log_entry_ai_results",
            input_text=str(entry_id),
            variables={
                "ai_tags": json.dumps(ai_tags),
                "ai_summary": ai_summary,
                "ai_insights": json.dumps(ai_insights)
            }
        )
        
        # Store in Semantic Memory for future context and retrieval
        await kernel_service.remember(
            "ceo_log_entries",
            str(entry_id),
            entry.content,
            ai_summary
        )
        
        return True
    except Exception as e:
        # Log the error but don't fail the request
        print(f"Error processing log entry with AI: {str(e)}")
        return False