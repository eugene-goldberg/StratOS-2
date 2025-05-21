# Mock setup for external dependencies
from unittest.mock import MagicMock, AsyncMock
import sys
import types

def setup_mocks():
    # Dictionary of modules to mock with their attributes
    modules_to_mock = {
        # FastAPI and related
        'fastapi': {
            'FastAPI': MagicMock,
            'APIRouter': MagicMock,
            'HTTPException': type('HTTPException', (), {
                '__init__': lambda self, status_code=None, detail=None, headers=None: None,
                'status_code': None, 'detail': None
            }),
            'Depends': lambda x: x,
            'Response': MagicMock(),
            'Request': MagicMock(),
            'Form': lambda *args, **kwargs: lambda x: x,
            'File': lambda *args, **kwargs: lambda x: x,
            'UploadFile': MagicMock(),
            'Body': lambda *args, **kwargs: lambda x: x,
            'Path': lambda *args, **kwargs: lambda x: x,
            'Query': lambda *args, **kwargs: lambda x: x,
            'status': type('status', (), {
                'HTTP_400_BAD_REQUEST': 400,
                'HTTP_401_UNAUTHORIZED': 401,
                'HTTP_403_FORBIDDEN': 403,
                'HTTP_404_NOT_FOUND': 404,
                'HTTP_409_CONFLICT': 409,
                'HTTP_500_INTERNAL_SERVER_ERROR': 500,
                'HTTP_200_OK': 200,
                'HTTP_201_CREATED': 201
            })
        },

        # Semantic Kernel
        'semantic_kernel': {},
        'semantic_kernel.memory.semantic_text_memory': {},
        'semantic_kernel.connectors.memory.azure_cognitive_search': {},
        'semantic_kernel.connectors.ai.open_ai': {},
        'semantic_kernel.kernel': {'Kernel': MagicMock},
        'semantic_kernel.functions.kernel_function': {'kernel_function': lambda *args, **kwargs: lambda x: x},

        # Azure services
        'azure.cosmos': {},
        'azure.cosmos.aio': {},
        'azure.identity': {},
        'azure.storage.blob': {},
        'azure.cognitiveservices.speech': {},
        'azure.search.documents': {},
        'azure.search.documents.aio': {},
        'azure.search.documents.models': {},
        'azure.search.documents.indexes.aio': {},
        'azure.search.documents.indexes.models': {},

        # Pydantic
        'pydantic': {
            'BaseModel': type('BaseModel', (), {
                '__init__': lambda self, **kwargs: setattr(self, '__dict__', kwargs),
                'model_dump': lambda self: self.__dict__,
                'dict': lambda self: self.__dict__  # v1 compatibility
            }),
            'Field': lambda *args, **kwargs: None,
            'validator': lambda *args, **kwargs: lambda x: x,
            'field_validator': lambda *args, **kwargs: lambda x: x,
            'root_validator': lambda *args, **kwargs: lambda x: x,
            'ValidationError': type('ValidationError', (Exception,), {}),
            'EmailStr': str,
            'HttpUrl': str
        },

        'pydantic_settings': {
            'BaseSettings': type('BaseSettings', (), {
                '__init__': lambda self, **kwargs: setattr(self, '__dict__', kwargs),
                'model_dump': lambda self: self.__dict__,
                'dict': lambda self: self.__dict__
            }),
            'SettingsConfigDict': lambda **kwargs: {"settings_dict": kwargs}
        },

        # JWT
        'jwt': {
            'encode': lambda *args, **kwargs: "mock.jwt.token",
            'decode': lambda *args, **kwargs: {"sub": "user_id", "exp": 9999999999}
        },

        # Other modules
        'dotenv': {},
        'openai': {}
    }

    # Add FastAPI submodules
    fastapi_submodules = ['testclient', 'responses', 'encoders', 'security']
    for submodule in fastapi_submodules:
        modules_to_mock[f'fastapi.{submodule}'] = {}
    
    # Special case for TestClient
    modules_to_mock['fastapi.testclient']['TestClient'] = type('TestClient', (), {
        '__init__': lambda self, app: setattr(self, 'app', app),
        'get': lambda self, *args, **kwargs: MagicMock(),
        'post': lambda self, *args, **kwargs: MagicMock(),
        'put': lambda self, *args, **kwargs: MagicMock(),
        'delete': lambda self, *args, **kwargs: MagicMock()
    })

    # Set up all the mocks
    for module_name, attributes in modules_to_mock.items():
        # Create nested modules if needed
        parts = module_name.split('.')
        current_module = parts[0]
        
        # Create base module if it doesn't exist
        if current_module not in sys.modules:
            sys.modules[current_module] = types.ModuleType(current_module)
            
        # Create module hierarchy
        for i in range(1, len(parts)):
            parent_module_name = '.'.join(parts[:i])
            current_module_name = '.'.join(parts[:i+1])
            parent_module = sys.modules[parent_module_name]
            
            if current_module_name not in sys.modules:
                new_module = types.ModuleType(current_module_name)
                sys.modules[current_module_name] = new_module
                setattr(parent_module, parts[i], new_module)
        
        # Add attributes to the module
        for attr_name, attr_value in attributes.items():
            setattr(sys.modules[module_name], attr_name, attr_value)

    print("External dependencies mocked successfully")

# Execute when imported
setup_mocks()