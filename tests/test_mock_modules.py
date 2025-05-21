"""
Utility module to provide mock modules for testing
"""
from unittest.mock import MagicMock, AsyncMock
import sys
import types
import uuid as real_uuid

class MockedModule:
    @staticmethod
    def create_module_structure(module_name):
        """Create a nested module structure with MagicMock objects"""
        # Skip standard library modules
        if module_name in ['datetime', 'uuid']:
            return sys.modules.get(module_name)
            
        parts = module_name.split('.')
        
        # Ensure the parent module exists
        current_mod_name = parts[0]
        if current_mod_name not in sys.modules:
            sys.modules[current_mod_name] = types.ModuleType(current_mod_name)
            
        # Create the module hierarchy
        for i in range(1, len(parts)):
            parent_mod_name = '.'.join(parts[:i])
            current_mod_name = '.'.join(parts[:i+1])
            parent_mod = sys.modules[parent_mod_name]
            
            if current_mod_name not in sys.modules:
                new_mod = types.ModuleType(current_mod_name)
                sys.modules[current_mod_name] = new_mod
                setattr(parent_mod, parts[i], new_mod)
        
        return sys.modules[module_name]

# List of modules to mock
modules_to_mock = [
    # FastAPI and related
    'fastapi',
    'fastapi.testclient',
    'fastapi.responses',
    'fastapi.encoders',
    'fastapi.security',
    
    # HTTP
    'httpx',
    
    # Semantic Kernel
    'semantic_kernel',
    'semantic_kernel.memory.semantic_text_memory',
    'semantic_kernel.connectors.memory.azure_cognitive_search',
    'semantic_kernel.connectors.ai.open_ai',
    'semantic_kernel.kernel',
    'semantic_kernel.functions.kernel_function',
    
    # Azure services
    'azure.cosmos',
    'azure.cosmos.aio',
    'azure.identity',
    'azure.storage.blob',
    'azure.cognitiveservices.speech',
    'azure.search.documents',
    'azure.search.documents.aio',
    'azure.search.documents.models',
    'azure.search.documents.indexes.aio',
    'azure.search.documents.indexes.models',
    
    # Other dependencies
    'pydantic',
    'pydantic.alias_generators',
    'pydantic.field_validator',
    'pydantic_settings',
    'dotenv',
    'openai',
    'jwt',
]

# Create mock modules
for module_name in modules_to_mock:
    MockedModule.create_module_structure(module_name)
    print(f"Mocked module: {module_name}")

# Set up special mock classes and functions for certain modules

# FastAPI 
sys.modules['fastapi'].FastAPI = MagicMock
sys.modules['fastapi'].APIRouter = MagicMock
sys.modules['fastapi'].HTTPException = type('HTTPException', (), {
    '__init__': lambda self, status_code=None, detail=None, headers=None: None,
    'status_code': None, 
    'detail': None
})
sys.modules['fastapi'].Depends = lambda x: x
sys.modules['fastapi'].Response = MagicMock()
sys.modules['fastapi'].Request = MagicMock()
sys.modules['fastapi'].Form = lambda *args, **kwargs: lambda x: x
sys.modules['fastapi'].File = lambda *args, **kwargs: lambda x: x
sys.modules['fastapi'].UploadFile = MagicMock()
sys.modules['fastapi'].Body = lambda *args, **kwargs: lambda x: x
sys.modules['fastapi'].Path = lambda *args, **kwargs: lambda x: x
sys.modules['fastapi'].Query = lambda *args, **kwargs: lambda x: x
sys.modules['fastapi'].status = MagicMock()
sys.modules['fastapi'].status.HTTP_400_BAD_REQUEST = 400
sys.modules['fastapi'].status.HTTP_401_UNAUTHORIZED = 401
sys.modules['fastapi'].status.HTTP_403_FORBIDDEN = 403
sys.modules['fastapi'].status.HTTP_404_NOT_FOUND = 404
sys.modules['fastapi'].status.HTTP_409_CONFLICT = 409
sys.modules['fastapi'].status.HTTP_500_INTERNAL_SERVER_ERROR = 500
sys.modules['fastapi'].status.HTTP_200_OK = 200
sys.modules['fastapi'].status.HTTP_201_CREATED = 201

# FastAPI TestClient
class MockTestClient:
    def __init__(self, app):
        self.app = app
    
    def get(self, *args, **kwargs):
        return MagicMock()
    
    def post(self, *args, **kwargs):
        return MagicMock()
    
    def put(self, *args, **kwargs):
        return MagicMock()
    
    def delete(self, *args, **kwargs):
        return MagicMock()

sys.modules['fastapi.testclient'].TestClient = MockTestClient

# Pydantic
class BasePydanticMock:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def model_dump(self):
        return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
    
    def dict(self):  # For v1 compatibility
        return self.model_dump()

sys.modules['pydantic'].BaseModel = type('BaseModel', (BasePydanticMock,), {})
sys.modules['pydantic'].Field = lambda *args, **kwargs: None
sys.modules['pydantic'].validator = lambda *args, **kwargs: lambda x: x
sys.modules['pydantic'].field_validator = lambda *args, **kwargs: lambda x: x
sys.modules['pydantic'].root_validator = lambda *args, **kwargs: lambda x: x
sys.modules['pydantic'].ValidationError = type('ValidationError', (Exception,), {})
sys.modules['pydantic'].EmailStr = str
sys.modules['pydantic'].HttpUrl = str
sys.modules['pydantic_settings'].BaseSettings = type('BaseSettings', (BasePydanticMock,), {})
sys.modules['pydantic_settings'].SettingsConfigDict = lambda **kwargs: {"settings_dict": kwargs}

# JWT
sys.modules['jwt'].encode = lambda *args, **kwargs: "mock.jwt.token"
sys.modules['jwt'].decode = lambda *args, **kwargs: {"sub": "user_id", "exp": 9999999999}

# Semantic Kernel
sys.modules['semantic_kernel.functions.kernel_function'].kernel_function = lambda *args, **kwargs: lambda x: x