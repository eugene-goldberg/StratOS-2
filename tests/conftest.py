# Import conftest_helper first to set up proper mocks
import conftest_helper

import pytest
from unittest.mock import patch, MagicMock
import os # Keep os import if used by other fixtures, but not for env patching here

@pytest.fixture(scope="session", autouse=True)
def mock_kernel_service_initialization(session_mocker):
    """
    Prevents the actual KernelService.initialize_kernel_components from running
    during the test session. Methods that would trigger it will use a KernelService
    that hasn't fully initialized its Azure components.
    Individual tests or fixtures for services that use kernel_service
    will need to mock specific kernel_service methods (e.g., generate_completion, recall).
    """
    
    # Mock the method that performs full, Azure-dependent initialization
    # The new kernel service doesn't have initialize_kernel_components, so we skip this
    
    # Also, ensure that if _ensure_initialized is called, it doesn't try to re-init if the above mock fails
    # or if it needs to set self.kernel and self.memory to mocks.
    def mock_ensure_initialized(self_ks):
        if not hasattr(self_ks, 'kernel') or self_ks.kernel is None:
            self_ks.kernel = MagicMock()
            # Mock common kernel methods that might be accessed after _ensure_initialized
            self_ks.kernel.add_service = MagicMock()
            self_ks.kernel.get_service = MagicMock(return_value=MagicMock())
            self_ks.kernel.import_skill = MagicMock()
            self_ks.kernel.import_semantic_skill_from_directory = MagicMock()
            self_ks.kernel.skills.get_function = MagicMock()
            self_ks.kernel.create_new_context = MagicMock()
            self_ks.kernel.run_async = MagicMock()

        if not hasattr(self_ks, 'memory') or self_ks.memory is None:
            self_ks.memory = MagicMock()
            self_ks.memory.save_information_async = MagicMock()
            self_ks.memory.search_async = MagicMock(return_value=[])
        
        if not hasattr(self_ks, 'logger') or self_ks.logger is None:
            self_ks.logger = MagicMock()

        self_ks._initialized_components = True # Pretend it's initialized

    # The new kernel service doesn't have _ensure_initialized method
    # session_mocker.patch('backend.ai.kernel_service.KernelService._ensure_initialized', mock_ensure_initialized)


@pytest.fixture(scope="session") # Changed to session scope
def session_mocker(pytestconfig):
    """
    A session-scoped mocker.
    """
    from unittest.mock import patch as _patch
    
    class SessionMocker:
        def __init__(self):
            self.patches = []

        def patch(self, *args, **kwargs):
            # For class or method patching, new_callable might be needed for async mocks
            # For simple return_value=None or MagicMock(), this is usually fine.
            p = _patch(*args, **kwargs)
            self.patches.append(p)
            started_patch = p.start()
            return started_patch

        def stop_all(self):
            for p in reversed(self.patches):
                p.stop()
            self.patches = []

    mocker_instance = SessionMocker()
    yield mocker_instance
    mocker_instance.stop_all()
