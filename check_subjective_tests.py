#!/usr/bin/env python3
"""
Script to check test_subjective_input_service.py
"""
import sys
import os
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from uuid import UUID, uuid4

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import conftest_helper to set up mocks
import tests.conftest_helper

# Create mock azure cognitive services speech
sys.modules['azure.cognitiveservices.speech'] = MagicMock()

# Mock essential subjective input models
class LogEntry:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', uuid4())
        self.user_id = kwargs.get('user_id', uuid4())
        self.content = kwargs.get('content', 'Test entry')
        self.entry_type = kwargs.get('entry_type', 'observation')
        self.tags = kwargs.get('tags', [])
        self.ai_summary = kwargs.get('ai_summary')
        self.ai_generated_tags = kwargs.get('ai_generated_tags', [])
        self.ai_insights = kwargs.get('ai_insights', [])
        self.created_at = kwargs.get('created_at', datetime.now())
        self.updated_at = kwargs.get('updated_at', datetime.now())
    
    def model_dump(self, **kwargs):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'content': self.content,
            'entry_type': self.entry_type,
            'tags': self.tags,
            'ai_summary': self.ai_summary,
            'ai_generated_tags': self.ai_generated_tags,
            'ai_insights': self.ai_insights,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

class LogEntryCreate:
    def __init__(self, **kwargs):
        self.content = kwargs.get('content', 'New entry')
        self.entry_type = kwargs.get('entry_type', 'observation')
        self.tags = kwargs.get('tags', [])

class LogEntryTag:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', uuid4())
        self.name = kwargs.get('name', 'test-tag')

class StrategicCanvas:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', uuid4())
        self.user_id = kwargs.get('user_id', uuid4())
        self.title = kwargs.get('title', 'Test Canvas')
        self.description = kwargs.get('description', '')
        self.elements = kwargs.get('elements', [])
        self.created_at = kwargs.get('created_at', datetime.now())
        self.updated_at = kwargs.get('updated_at', datetime.now())
    
    def model_dump(self, **kwargs):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'elements': self.elements,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

class StrategicCanvasCreate:
    def __init__(self, **kwargs):
        self.title = kwargs.get('title', 'New Canvas')
        self.description = kwargs.get('description', '')

class CanvasElement:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id', uuid4())
        self.element_type = kwargs.get('element_type', 'text_node')
        self.content = kwargs.get('content', {})
        self.position = kwargs.get('position', {'x': 0, 'y': 0})
        self.created_at = kwargs.get('created_at', datetime.now())
        self.updated_at = kwargs.get('updated_at', datetime.now())
    
    def model_dump(self, **kwargs):
        return {
            'id': self.id,
            'element_type': self.element_type,
            'content': self.content,
            'position': self.position,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }

class CanvasElementCreate:
    def __init__(self, **kwargs):
        self.element_type = kwargs.get('element_type', 'text_node')
        self.content = kwargs.get('content', {})
        self.position = kwargs.get('position', {'x': 0, 'y': 0})

# Mock UploadFile for voice-to-text tests
class MockUploadFile:
    def __init__(self, filename="test.wav", content_type="audio/wav"):
        self.filename = filename
        self.content_type = content_type
        self._file = MagicMock()
    
    async def read(self):
        return b"mock audio data"
    
    async def close(self):
        pass

# Set up mock models
sys.modules['backend.models.subjective_input'] = MagicMock()
sys.modules['backend.models.subjective_input'].LogEntryCreate = LogEntryCreate
sys.modules['backend.models.subjective_input'].LogEntry = LogEntry
sys.modules['backend.models.subjective_input'].LogEntryType = MagicMock()
sys.modules['backend.models.subjective_input'].LogEntryTag = LogEntryTag
sys.modules['backend.models.subjective_input'].StrategicCanvasCreate = StrategicCanvasCreate
sys.modules['backend.models.subjective_input'].StrategicCanvas = StrategicCanvas
sys.modules['backend.models.subjective_input'].CanvasElementCreate = CanvasElementCreate
sys.modules['backend.models.subjective_input'].CanvasElement = CanvasElement

# Create mock SubjectiveInputService
class MockSubjectiveInputService:
    def __init__(self):
        self.log_entries_cache = {}
        self.canvases_cache = {}
        self.cosmos_db_available = False
        self.speech_config = MagicMock()
        
    async def create_log_entry(self, log_data, user_id):
        entry = LogEntry(
            user_id=user_id,
            content=log_data.content,
            entry_type=log_data.entry_type,
            tags=[LogEntryTag(name=tag) for tag in log_data.tags] if log_data.tags else [],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        if str(user_id) not in self.log_entries_cache:
            self.log_entries_cache[str(user_id)] = {}
        
        self.log_entries_cache[str(user_id)][str(entry.id)] = entry
        return entry
    
    async def get_log_entry(self, entry_id, user_id):
        user_entries = self.log_entries_cache.get(str(user_id), {})
        return user_entries.get(str(entry_id))
    
    async def update_log_entry_ai_results(self, entry_id, user_id, ai_tags, ai_summary, ai_insights):
        entry = await self.get_log_entry(entry_id, user_id)
        if not entry:
            return False
        
        entry.ai_generated_tags = ai_tags
        entry.ai_summary = ai_summary
        entry.ai_insights = ai_insights
        entry.updated_at = datetime.now()
        return True
    
    async def create_canvas(self, canvas_data, user_id):
        canvas = StrategicCanvas(
            user_id=user_id,
            title=canvas_data.title,
            description=canvas_data.description,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        if str(user_id) not in self.canvases_cache:
            self.canvases_cache[str(user_id)] = {}
        
        self.canvases_cache[str(user_id)][str(canvas.id)] = canvas
        return canvas
    
    async def get_canvas(self, canvas_id, user_id):
        user_canvases = self.canvases_cache.get(str(user_id), {})
        return user_canvases.get(str(canvas_id))
    
    async def add_canvas_element(self, canvas_id, user_id, element_data):
        canvas = await self.get_canvas(canvas_id, user_id)
        if not canvas:
            return None
        
        element = CanvasElement(
            element_type=element_data.element_type,
            content=element_data.content,
            position=element_data.position
        )
        
        if not hasattr(canvas, 'elements'):
            canvas.elements = []
        
        canvas.elements.append(element)
        canvas.updated_at = datetime.now()
        return element
    
    async def process_voice_to_text(self, file):
        # Mock implementation that just returns a fixed text
        return "This is a transcribed voice message."

# Mock SubjectiveInputService in the backend module
sys.modules['backend.services.subjective_input_service'] = MagicMock()
sys.modules['backend.services.subjective_input_service'].SubjectiveInputService = MockSubjectiveInputService

# Special case for speech recognition
sys.modules['azure.cognitiveservices.speech'].SpeechRecognizer = MagicMock()
sys.modules['azure.cognitiveservices.speech'].AudioConfig = MagicMock()
sys.modules['azure.cognitiveservices.speech'].ResultReason = MagicMock()
sys.modules['azure.cognitiveservices.speech'].ResultReason.RecognizedSpeech = 3

# Try to inspect the test file
def check_subjective_tests():
    try:
        # Import the test module
        from tests import test_subjective_input_service
        
        # Find all test functions
        test_functions = []
        for name in dir(test_subjective_input_service):
            if name.startswith('test_'):
                test_functions.append(name)
        
        print(f"Found {len(test_functions)} test functions in test_subjective_input_service.py")
        print(f"Test functions: {', '.join(test_functions)}")
        
        print("\nCheck complete - all SubjectiveInputService tests could be parsed!")
        
    except Exception as e:
        print(f"Error importing test_subjective_input_service.py: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_subjective_tests()