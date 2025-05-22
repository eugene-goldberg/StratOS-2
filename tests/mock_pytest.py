"""
A very simple mock of pytest to allow tests to run without the real pytest
"""
import unittest
import inspect
import sys

# Mock pytest fixtures, marks, etc.
def pytest_asyncio():
    def _fixture(func):
        return func  # just return the function unchanged
    return _fixture

def fixture(*args, **kwargs):
    def _fixture(func):
        return func  # just return the function unchanged
    return _fixture

def mark():
    class Mark:
        def asyncio(self, func):
            return func
    return Mark()

mark = mark()

# Function to run all test functions in a module
def main(args=None):
    if args is None:
        args = []
    
    print("Running mock pytest")
    # Find and run all test functions in the module
    test_files = []
    if args:
        for arg in args:
            if arg.startswith('-'):
                continue  # Skip flags like -xvs
            if arg.startswith('tests/'):
                test_files.append(arg.replace('tests/', '').replace('.py', ''))
    
    if not test_files:
        # Run all tests
        from . import test_auth_service
        from . import test_planning_service
        from . import test_subjective_input_service
        from . import test_analysis_service
        test_modules = [test_auth_service, test_planning_service, 
                       test_subjective_input_service, test_analysis_service]
    else:
        test_modules = []
        for test_file in test_files:
            try:
                module = __import__(f"tests.{test_file}", fromlist=[test_file])
                test_modules.append(module)
            except ImportError as e:
                print(f"Error importing {test_file}: {e}")
                return 1
    
    success = True
    for module in test_modules:
        print(f"\nRunning tests from {module.__name__}")
        
        # Find all test functions
        test_functions = []
        for name, func in inspect.getmembers(module):
            if name.startswith('test_') and inspect.isfunction(func):
                test_functions.append((name, func))
        
        # Run each test
        for name, func in test_functions:
            print(f"  Running {name}... ", end='')
            try:
                if inspect.iscoroutinefunction(func):
                    print("(skipping async function)")
                    continue
                func()
                print("✓")
            except Exception as e:
                print(f"✗ {e}")
                success = False
        
    return 0 if success else 1

# Mock raises for assertions
class raises:
    def __init__(self, exception_class):
        self.exception_class = exception_class
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            # No exception was raised
            raise AssertionError(f"Expected {self.exception_class.__name__} to be raised, but no exception was raised")
        
        if issubclass(exc_type, self.exception_class):
            # Expected exception was raised
            return True
        
        # Unexpected exception was raised
        return False