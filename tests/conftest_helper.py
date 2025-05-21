"""
Helper module to make test discovery and execution easier
"""
from unittest.mock import MagicMock, AsyncMock
import sys

# Mock all external dependencies
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
sys.modules['dotenv'] = MagicMock()