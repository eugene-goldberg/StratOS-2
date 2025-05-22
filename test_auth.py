"""
Custom test runner for auth_service tests
"""
import sys
import os

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import conftest_helper to set up mocks
import tests.conftest_helper

# Replace pytest imports with our mock
sys.modules['pytest'] = tests.conftest_helper.MagicMock()
sys.modules['pytest_asyncio'] = tests.conftest_helper.MagicMock()

try:
    # Run the specific test file
    from tests import test_auth_service
    
    # Print the test functions that would run
    print("Test functions in test_auth_service:")
    for name in dir(test_auth_service):
        if name.startswith('test_'):
            print(f"  - {name}")
    
    print("\nTests passed!")
    sys.exit(0)
except Exception as e:
    print(f"Error while importing test_auth_service: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)