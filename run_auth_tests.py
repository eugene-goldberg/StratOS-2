#!/usr/bin/env python3
"""
Run test_auth_service.py tests
"""
import sys
import os
import asyncio
import inspect
from unittest.mock import AsyncMock, MagicMock

# Add project root to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import conftest_helper to set up mocks
import tests.conftest_helper

# Build a mock environment for tests
def run_auth_service_tests():
    """Run all tests in test_auth_service.py"""
    # Import the test module
    from tests import test_auth_service
    
    # Find all test functions
    test_functions = []
    for name, func in inspect.getmembers(test_auth_service):
        if name.startswith('test_') and inspect.isfunction(func):
            test_functions.append((name, func))
    
    print(f"Found {len(test_functions)} test functions")
    
    # Create a fake monkeypatch fixture
    class MockMonkeypatch:
        def setattr(self, obj, name, value):
            setattr(obj, name, value)
    
    # Setup the auth_service fixture
    async def setup_auth_service():
        # Call the fixture function with our mock monkeypatch
        monkeypatch = MockMonkeypatch()
        auth_service = await test_auth_service.auth_service(monkeypatch)
        return auth_service
    
    # Run each test
    async def run_tests():
        successful_tests = []
        failed_tests = []
        
        auth_service_fixture = await setup_auth_service()
        
        for name, func in test_functions:
            print(f"Running {name}... ", end='', flush=True)
            try:
                if inspect.iscoroutinefunction(func):
                    # For async functions
                    await func(auth_service_fixture)
                else:
                    # For sync functions
                    func(auth_service_fixture)
                print("✓")
                successful_tests.append(name)
            except Exception as e:
                print(f"✗ - {e}")
                failed_tests.append((name, str(e)))
        
        # Print summary
        print("\nTest Summary:")
        print(f"Total tests: {len(test_functions)}")
        print(f"Successful: {len(successful_tests)}")
        print(f"Failed: {len(failed_tests)}")
        
        if failed_tests:
            print("\nFailed tests:")
            for name, error in failed_tests:
                print(f"  {name}: {error}")
    
    # Run the tests
    asyncio.run(run_tests())

if __name__ == "__main__":
    run_auth_service_tests()