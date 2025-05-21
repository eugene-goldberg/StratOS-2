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
async def create_log_entry(
    entry_data: LogEntryCreate,
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Create a new CEO Log entry with text/voice input
    """
    # Create the log entry
    entry = await input_service.create_log_entry(entry_data, current_user_id)
    
    # Process with AI for tagging and insights
    await process_log_entry_with_ai(entry.id)
    
    return entry

@router.get("/log/{entry_id}", response_model=LogEntry)
async def get_log_entry(entry_id: UUID, current_user_id: UUID = Depends(get_current_user_id)):
    """
    Get a CEO Log entry by ID
    """
    entry = await input_service.get_log_entry(entry_id, current_user_id) # Pass user_id
    if not entry:
        raise HTTPException(status_code=404, detail="Log entry not found")
    return entry

@router.get("/log", response_model=List[LogEntry])
async def list_log_entries(
    limit: int = 20,
    offset: int = 0,
    entry_type: Optional[str] = None,
    tag: Optional[str] = None,
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    List CEO Log entries with optional filtering
    """
    return await input_service.list_log_entries(current_user_id, limit, offset, entry_type, tag)

@router.put("/log/{entry_id}", response_model=LogEntry)
async def update_log_entry(entry_id: UUID, entry_data: LogEntryUpdate, current_user_id: UUID = Depends(get_current_user_id)):
    """
    Update a CEO Log entry
    """
    updated = await input_service.update_log_entry(entry_id, entry_data, current_user_id) # Pass user_id
    if not updated:
        raise HTTPException(status_code=404, detail="Log entry not found")
    
    # Re-process with AI
    await process_log_entry_with_ai(entry_id, current_user_id) # Pass user_id
    
    return updated

@router.delete("/log/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_log_entry(entry_id: UUID, current_user_id: UUID = Depends(get_current_user_id)):
    """
    Delete a CEO Log entry
    """
    deleted = await input_service.delete_log_entry(entry_id, current_user_id) # Pass user_id
    if not deleted:
        raise HTTPException(status_code=404, detail="Log entry not found")
    return {"status": "success"}

@router.post("/log/voice", response_model=LogEntry, status_code=status.HTTP_201_CREATED)
async def create_voice_log_entry(
    audio_file: UploadFile = File(...),
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Create a new CEO Log entry from voice input (file upload)
    """
    # Process audio to text using Azure Speech Services
    text_content = await input_service.process_voice_to_text(audio_file)
    
    # Create entry
    entry_data = LogEntryCreate(content=text_content)
    entry = await input_service.create_log_entry(entry_data, current_user_id)
    
    # Process with AI
    await process_log_entry_with_ai(entry.id)
    
    return entry

@router.post("/voice-note/stream/start")
async def start_voice_streaming(
    request: Request,
    current_user_id: UUID = Depends(get_current_user_id)
):
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
async def process_voice_chunk(
    request: Request,
    current_user_id: UUID = Depends(get_current_user_id)
):
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
            
            # Use authenticated user id
            if current_user_id:
                entry = await input_service.create_log_entry(entry_data, current_user_id)
                
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
async def create_canvas(
    canvas_data: StrategicCanvasCreate,
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    Create a new Strategic Canvas
    """
    return await input_service.create_canvas(canvas_data, current_user_id)

@router.get("/canvas/{canvas_id}", response_model=StrategicCanvas)
async def get_canvas(canvas_id: UUID, current_user_id: UUID = Depends(get_current_user_id)):
    """
    Get a Strategic Canvas by ID
    """
    canvas = await input_service.get_canvas(canvas_id, current_user_id) # Pass user_id
    if not canvas:
        raise HTTPException(status_code=404, detail="Canvas not found")
    return canvas

@router.get("/canvas", response_model=List[StrategicCanvas])
async def list_canvases(
    limit: int = 10,
    offset: int = 0,
    current_user_id: UUID = Depends(get_current_user_id)
):
    """
    List Strategic Canvases
    """
    return await input_service.list_canvases(current_user_id, limit, offset)

@router.post("/canvas/{canvas_id}/elements", status_code=status.HTTP_201_CREATED)
async def add_canvas_element(canvas_id: UUID, element_data: CanvasElementCreate, current_user_id: UUID = Depends(get_current_user_id)):
    """
    Add an element to a Strategic Canvas
    """
    # Service's get_canvas now expects user_id, but add_canvas_element also needs it.
    # The get_canvas call here is just for validation, can be removed if add_canvas_element handles not found.
    # For now, let's assume add_canvas_element will call get_canvas internally with user_id.
    return await input_service.add_canvas_element(canvas_id, current_user_id, element_data)

@router.put("/canvas/{canvas_id}/elements/{element_id}")
async def update_canvas_element(canvas_id: UUID, element_id: UUID, element_data: dict, current_user_id: UUID = Depends(get_current_user_id)):
    """
    Update a canvas element
    """
    updated = await input_service.update_canvas_element(canvas_id, current_user_id, element_id, element_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Canvas element not found")
    return updated

@router.delete("/canvas/{canvas_id}/elements/{element_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_canvas_element(canvas_id: UUID, element_id: UUID, current_user_id: UUID = Depends(get_current_user_id)):
    """
    Delete a canvas element
    """
    deleted = await input_service.delete_canvas_element(canvas_id, current_user_id, element_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Canvas element not found")
    return {"status": "success"}

@router.post("/canvas/{canvas_id}/ai-assist")
async def get_canvas_ai_assistance(canvas_id: UUID, prompt: str, current_user_id: UUID = Depends(get_current_user_id)):
    """
    Get AI assistance for the Strategic Canvas
    """
    # Service method now takes user_id
    response = await input_service.get_canvas_ai_assistance(canvas_id, current_user_id, prompt)
    return {"response": response}

# Helper functions

async def process_log_entry_with_ai(entry_id: UUID, user_id: UUID): # Added user_id
    """
    Process a log entry with AI for tagging, summarization, and insights
    """
    entry = await input_service.get_log_entry(entry_id, user_id) # Pass user_id
    if not entry:
        return False
    
    try:
        # Fetch strategic elements (e.g., from NorthStar service for the user_id)
        # This part needs actual implementation to fetch user-specific strategic context.
        # Placeholder:
        user_strategic_context = f"User {user_id}'s strategic context (purpose, vision, goals) would be fetched here."
        
        # Generate tags
        tags_response = await kernel_service.invoke_semantic_function(
            skill_name="SubjectiveLog", function_name="GenerateTags",
            input_text=entry.content, variables={"user_context": user_strategic_context}
        )
        ai_tags = json.loads(str(tags_response)) if str(tags_response) else []

        # Generate summary
        summary_response = await kernel_service.invoke_semantic_function(
            skill_name="SubjectiveLog", function_name="GenerateSummary", input_text=entry.content
        )
        ai_summary = str(summary_response).strip()

        # Generate insights
        insights_response = await kernel_service.invoke_semantic_function(
            skill_name="SubjectiveLog", function_name="GenerateInsights", input_text=entry.content
        )
        ai_insights = [i.strip() for i in str(insights_response).split('\n') if i.strip()]
        
        # Update the entry with AI results using the service (passing user_id)
        await input_service.update_log_entry_ai_results(
            entry_id, user_id, ai_tags, ai_summary, ai_insights
        )
        
        # The redundant call to LogManagement skill is removed.
        # The service method update_log_entry_ai_results should handle persistence.
        
        # Store in Semantic Memory
        await kernel_service.remember(
            collection_name=f"ceo_log_entries_user_{user_id}", # User-specific collection
            key=str(entry_id),
            text=entry.content,
            description=ai_summary # Or more detailed metadata
        )
        return True
    except Exception as e:
        logging.error(f"Error processing log entry {entry_id} with AI for user {user_id}: {str(e)}")
        return False
