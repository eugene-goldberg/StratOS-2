"""
Mock KernelService for Testing
"""
from unittest.mock import MagicMock, AsyncMock

class KernelService:
    def __init__(self):
        self.kernel = None
        self.memory = None
        self.logger = MagicMock()
        self._initialized_components = False

    def _ensure_initialized(self):
        pass

    def initialize_kernel_components(self):
        pass

    def get_skill(self, skill_name):
        return MagicMock()

    def create_new_context(self):
        return MagicMock()

    async def run_async(self, function, input_vars=None):
        mock_result = MagicMock()
        mock_result.result = "Mocked result"
        return mock_result

    async def generate_completion(self, prompt, max_tokens=None):
        return "Mocked completion"

    async def invoke_semantic_function(self, skill_name, function_name, input_text):
        return "Mocked semantic function response"

# Create a singleton instance
kernel_service = KernelService()
