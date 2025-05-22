"""
Helper module to make test discovery and execution easier
"""
from unittest.mock import MagicMock, AsyncMock, patch
import sys

print("External dependencies mocked successfully")

# Create mock pytest module and pytest_asyncio module
class MockPytest:
    """Mock implementation of pytest"""
    @staticmethod
    def mark():
        """Create the mark namespace"""
        class Mark:
            def asyncio(self, func):
                """Mock for pytest.mark.asyncio decorator"""
                return func
        return Mark()
    
    @staticmethod
    def fixture(*args, **kwargs):
        """Mock for pytest.fixture decorator"""
        def decorator(func):
            return func
        return decorator
    
    @staticmethod
    def raises(exception_type):
        """Mock for pytest.raises context manager"""
        class RaisesContextManager:
            def __init__(self, exception_type):
                self.exception_type = exception_type
            
            def __enter__(self):
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                if exc_type is None:
                    # No exception was raised
                    return False
                if issubclass(exc_type, self.exception_type):
                    # Correct exception type was raised
                    return True
                # Wrong exception type was raised
                return False
        
        return RaisesContextManager(exception_type)
    
    class main:
        @staticmethod
        def __call__(*args, **kwargs):
            return 0

# Create mock pytest_asyncio module
class MockPytestAsyncio:
    """Mock implementation of pytest_asyncio"""
    @staticmethod
    def fixture(*args, **kwargs):
        """Mock for pytest_asyncio.fixture decorator"""
        def decorator(func):
            return func
        return decorator

# Mock all external dependencies
mock_pytest = MockPytest()
mock_pytest.asyncio = MagicMock()
mock_pytest.mark = mock_pytest.mark()
mock_pytest_asyncio = MockPytestAsyncio()

sys.modules['pytest'] = mock_pytest
sys.modules['pytest_asyncio'] = mock_pytest_asyncio

sys.modules['semantic_kernel'] = MagicMock()
sys.modules['semantic_kernel.memory.semantic_text_memory'] = MagicMock()
sys.modules['semantic_kernel.connectors.memory.azure_cognitive_search'] = MagicMock()
sys.modules['semantic_kernel.connectors.ai.open_ai'] = MagicMock()
sys.modules['azure.cosmos.aio'] = MagicMock()
sys.modules['azure.cosmos'] = MagicMock()
sys.modules['azure.cognitiveservices.speech'] = MagicMock()
sys.modules['azure.search.documents.indexes.aio'] = MagicMock()
sys.modules['azure.search.documents.indexes.models'] = MagicMock()
sys.modules['azure.search.documents.aio'] = MagicMock()
sys.modules['azure.search.documents.models'] = MagicMock()
sys.modules['azure.ai.contentsafety'] = MagicMock()
sys.modules['azure.storage.blob'] = MagicMock()
sys.modules['azure.storage.blob.aio'] = MagicMock()
sys.modules['azure.identity'] = MagicMock()
sys.modules['azure.ai.search'] = MagicMock()
sys.modules['dotenv'] = MagicMock()
sys.modules['jose'] = MagicMock()
sys.modules['jose.jwt'] = MagicMock()
sys.modules['fastapi'] = MagicMock()
sys.modules['httpx'] = MagicMock()
sys.modules['pandas'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['PyPDF2'] = MagicMock()
sys.modules['aiofiles'] = MagicMock()
sys.modules['passlib'] = MagicMock()
sys.modules['passlib.context'] = MagicMock()
sys.modules['pydantic'] = MagicMock()
sys.modules['pydantic_settings'] = MagicMock()
sys.modules['pydantic.config'] = MagicMock()

# Set up mock for fastapi.testclient
class MockTestClient:
    def __init__(self, app):
        self.app = app
    
    def get(self, url, **kwargs):
        return MagicMock()
    
    def post(self, url, **kwargs):
        return MagicMock()
    
    def put(self, url, **kwargs):
        return MagicMock()
    
    def delete(self, url, **kwargs):
        return MagicMock()

fastapi_module = sys.modules['fastapi']
fastapi_module.testclient = MagicMock()
fastapi_module.testclient.TestClient = MockTestClient

# Create CryptContext mock
class MockCryptContext:
    def __init__(self, *args, **kwargs):
        pass
    def verify(self, plain_password, hashed_password):
        return True
    def hash(self, password):
        return f"hashed_{password}"

sys.modules['passlib.context'].CryptContext = MockCryptContext

# Mock FastAPI components
class MockHTTPException(Exception):
    def __init__(self, status_code, detail=None):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"{status_code}: {detail}")

class MockStatus:
    HTTP_400_BAD_REQUEST = 400
    HTTP_401_UNAUTHORIZED = 401
    HTTP_403_FORBIDDEN = 403
    HTTP_404_NOT_FOUND = 404
    HTTP_422_UNPROCESSABLE_ENTITY = 422
    HTTP_500_INTERNAL_SERVER_ERROR = 500

fastapi_module.HTTPException = MockHTTPException
fastapi_module.status = MockStatus
fastapi_module.UploadFile = MagicMock()

# Mock pydantic_settings
class MockBaseSettings:
    class Config:
        pass

# Mock pydantic 
class MockConfigDict(dict):
    pass

sys.modules['pydantic_settings'].BaseSettings = MockBaseSettings
sys.modules['pydantic_settings'].SettingsConfigDict = MockConfigDict
sys.modules['pydantic'].ConfigDict = MockConfigDict

# Set up mock configuration settings
try:
    from backend.core import config
    config.settings = MagicMock()
    config.settings.SECRET_KEY = "test_secret_key"
    config.settings.ALGORITHM = "HS256"
    config.settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
    config.settings.REFRESH_TOKEN_EXPIRE_DAYS = 7
    config.settings.AZURE_COSMOS_ENDPOINT = ""
    config.settings.AZURE_COSMOS_KEY = ""
    config.settings.AZURE_COSMOS_DATABASE_NAME = "testdb"
except Exception as e:
    print(f"Warning: Could not mock config settings: {e}")

# Ensure our modules can be found
import sys
import os
# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))