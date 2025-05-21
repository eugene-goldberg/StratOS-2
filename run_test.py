import os
import sys
import importlib
import unittest
from unittest.mock import patch, MagicMock, AsyncMock

# Mocks for external dependencies
sys.modules['semantic_kernel'] = MagicMock()
sys.modules['semantic_kernel.connectors.ai.open_ai'] = MagicMock()
sys.modules['semantic_kernel.memory.semantic_text_memory'] = MagicMock()
sys.modules['semantic_kernel.connectors.memory.azure_cognitive_search'] = MagicMock()

# Import the test module
from tests.test_analysis_service import test_discover_so_linkages_basic

if __name__ == "__main__":
    # Run the specific test
    test_discover_so_linkages_basic()
    print("Test completed!")