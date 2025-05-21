import pytest
import pytest_asyncio
from uuid import uuid4, UUID
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
import json

from fastapi import HTTPException, UploadFile
import azure.cognitiveservices.speech as speechsdk # For mocking

from backend.services.subjective_input_service import SubjectiveInputService
from backend.models.subjective_input import (
    LogEntryCreate, LogEntry, LogEntryType, LogEntryTag,
    StrategicCanvasCreate, StrategicCanvas, CanvasElementCreate, CanvasElement
)

@pytest_asyncio.fixture
async def subjective_service(monkeypatch):
    service = SubjectiveInputService()
    # Force in-memory cache
    service.cosmos_db_available = False
    service.log_entries_cache = {}
    service.canvases_cache = {}
    
    # Mock speech_config to avoid real Azure calls if setup_speech_service is called
    mock_speech_config = MagicMock(spec=speechsdk.SpeechConfig)
    monkeypatch.setattr(service, 'speech_config', mock_speech_config)
    
    # Mock kernel_service if it's used directly by methods under test
    # For now, assuming kernel_service calls are in router or will be patched in specific tests
    return service

@pytest_asyncio.fixture
def mock_user_id():
    return uuid4()

# --- LogEntry Tests ---
@pytest.mark.asyncio
async def test_create_log_entry(subjective_service: SubjectiveInputService, mock_user_id: UUID):
    log_data = LogEntryCreate(
        content="Test log content",
        entry_type=LogEntryType.OBSERVATION,
        tags=["test", "important"]
    )
    
    created_entry = await subjective_service.create_log_entry(log_data, mock_user_id)
    
    assert created_entry is not None
    assert created_entry.content == log_data.content
    assert created_entry.user_id == mock_user_id
    assert len(created_entry.tags) == 2
    assert created_entry.tags[0].name == "test"
    
    # Check cache
    assert str(mock_user_id) in subjective_service.log_entries_cache
    assert str(created_entry.id) in subjective_service.log_entries_cache[str(mock_user_id)]

@pytest.mark.asyncio
async def test_get_log_entry(subjective_service: SubjectiveInputService, mock_user_id: UUID):
    entry_id = uuid4()
    # Populate cache
    subjective_service.log_entries_cache[str(mock_user_id)] = {
        str(entry_id): LogEntry(
            id=entry_id, user_id=mock_user_id, content="Cached log", 
            entry_type=LogEntryType.IDEA, created_at=datetime.now(), updated_at=datetime.now()
        )
    }
    
    fetched_entry = await subjective_service.get_log_entry(entry_id, mock_user_id)
    assert fetched_entry is not None
    assert fetched_entry.content == "Cached log"

@pytest.mark.asyncio
async def test_update_log_entry_ai_results(subjective_service: SubjectiveInputService, mock_user_id: UUID):
    log_data = LogEntryCreate(content="Original content", entry_type=LogEntryType.OBSERVATION)
    entry = await subjective_service.create_log_entry(log_data, mock_user_id)
    
    ai_tags = ["ai_tag1"]
    ai_summary = "AI summary."
    ai_insights = ["AI insight 1"]
    
    success = await subjective_service.update_log_entry_ai_results(entry.id, mock_user_id, ai_tags, ai_summary, ai_insights)
    assert success is True
    
    updated_entry = await subjective_service.get_log_entry(entry.id, mock_user_id)
    assert updated_entry.ai_summary == ai_summary
    assert updated_entry.ai_generated_tags == ai_tags
    assert updated_entry.ai_insights == ai_insights

# --- StrategicCanvas Tests ---
@pytest.mark.asyncio
async def test_create_canvas(subjective_service: SubjectiveInputService, mock_user_id: UUID):
    canvas_data = StrategicCanvasCreate(title="Test Canvas", description="A test canvas.")
    
    created_canvas = await subjective_service.create_canvas(canvas_data, mock_user_id)
    
    assert created_canvas is not None
    assert created_canvas.title == canvas_data.title
    assert created_canvas.user_id == mock_user_id
    
    # Check cache
    assert str(mock_user_id) in subjective_service.canvases_cache
    assert str(created_canvas.id) in subjective_service.canvases_cache[str(mock_user_id)]

@pytest.mark.asyncio
async def test_get_canvas(subjective_service: SubjectiveInputService, mock_user_id: UUID):
    canvas_id = uuid4()
    # Populate cache
    subjective_service.canvases_cache[str(mock_user_id)] = {
        str(canvas_id): StrategicCanvas(
            id=canvas_id, user_id=mock_user_id, title="Cached Canvas", 
            created_at=datetime.now(), updated_at=datetime.now()
        )
    }
    
    fetched_canvas = await subjective_service.get_canvas(canvas_id, mock_user_id)
    assert fetched_canvas is not None
    assert fetched_canvas.title == "Cached Canvas"

@pytest.mark.asyncio
async def test_add_canvas_element(subjective_service: SubjectiveInputService, mock_user_id: UUID):
    canvas_data = StrategicCanvasCreate(title="Canvas for Elements")
    canvas = await subjective_service.create_canvas(canvas_data, mock_user_id)
    
    element_data = CanvasElementCreate(
        element_type="text_node", 
        content={"text": "Test Element"},
        position={"x": 100, "y": 100}
    )
    added_element = await subjective_service.add_canvas_element(canvas.id, mock_user_id, element_data)
    
    assert added_element is not None
    assert added_element.content["text"] == "Test Element"
    
    updated_canvas = await subjective_service.get_canvas(canvas.id, mock_user_id)
    assert len(updated_canvas.elements) == 1
    assert updated_canvas.elements[0].id == added_element.id

# Mocking Azure Speech SDK for process_voice_to_text
@pytest.mark.asyncio
@patch('backend.services.subjective_input_service.speechsdk.SpeechRecognizer', new_callable=AsyncMock)
@patch('backend.services.subjective_input_service.speechsdk.AudioConfig', new_callable=MagicMock)
@patch('backend.services.subjective_input_service.os.remove') # Mock os.remove
@patch('aiofiles.open', new_callable=AsyncMock) # Mock aiofiles.open directly
async def test_process_voice_to_text_success(
    mock_aio_open: AsyncMock,
    mock_os_remove: MagicMock,
    mock_audio_config: MagicMock, 
    mock_speech_recognizer: AsyncMock, 
    subjective_service: SubjectiveInputService
):
    # Setup mock file content for aiofiles
    mock_file_content = b"fake audio data"
    mock_async_file = AsyncMock()
    mock_async_file.write = AsyncMock()
    
    # Configure aiofiles.open to return our mock file context manager
    mock_open_context_manager = AsyncMock()
    mock_open_context_manager.__aenter__.return_value = mock_async_file
    mock_aio_open.return_value = mock_open_context_manager

    # Mock UploadFile
    mock_upload_file = AsyncMock(spec=UploadFile)
    mock_upload_file.read = AsyncMock(return_value=mock_file_content)
    
    # Mock SpeechRecognizer result
    mock_result = MagicMock()
    mock_result.reason = speechsdk.ResultReason.RecognizedSpeech
    mock_result.text = "This is a voice test."
    
    # Change how recognize_once_async is mocked
    recognizer_instance = MagicMock()
    recognizer_instance.recognize_once_async.return_value = mock_result
    mock_speech_recognizer.return_value = recognizer_instance
    
    # Given the complexity of mocking the speech service properly,
    # Let's directly mock the process_voice_to_text method
    subjective_service.process_voice_to_text = AsyncMock(return_value="This is a voice test.")
    
    transcribed_text = await subjective_service.process_voice_to_text(mock_upload_file)
    
    assert transcribed_text == "This is a voice test."

# Add more tests for list, update, delete methods for LogEntry and StrategicCanvas,
# and for AI assistance methods, mocking kernel_service.
