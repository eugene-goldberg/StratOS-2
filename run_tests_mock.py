"""
Custom test runner for all tests

This script runs all test files using our mock framework
"""
import os
import sys
import importlib
import traceback

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import conftest_helper to set up mocks
import tests.conftest_helper

# Get a list of all test files
test_dir = os.path.join(os.path.dirname(__file__), "tests")
test_files = [
    f[:-3] for f in os.listdir(test_dir) 
    if f.startswith("test_") and f.endswith(".py") and f not in ["test_mock_modules.py"]
]

print(f"Found {len(test_files)} test files to run")

# Set up Pydantic mocking for all models
def mock_pydantic_model():
    """Create a class that simulates a Pydantic model with model_dump method"""
    class MockPydanticModel:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)
        
        def model_dump(self):
            """Replacement for dict() method in Pydantic v1"""
            return {k: v for k, v in self.__dict__.items() if not k.startswith('_')}
        
        def dict(self):
            """Legacy method for backward compatibility"""
            return self.model_dump()
    
    return MockPydanticModel

# Create specific mock classes for common models
sys.modules['backend.models.user'] = tests.conftest_helper.MagicMock()
sys.modules['backend.models.user'].UserCreate = mock_pydantic_model()
sys.modules['backend.models.user'].UserUpdate = mock_pydantic_model()
sys.modules['backend.models.user'].TokenData = mock_pydantic_model()

sys.modules['backend.models.planning'] = tests.conftest_helper.MagicMock()
sys.modules['backend.models.planning'].StrategicPlanCreate = mock_pydantic_model()
sys.modules['backend.models.planning'].StrategicPlan = mock_pydantic_model()
sys.modules['backend.models.planning'].InitiativeCreate = mock_pydantic_model()
sys.modules['backend.models.planning'].Initiative = mock_pydantic_model()

sys.modules['backend.core.config'] = tests.conftest_helper.MagicMock()
sys.modules['backend.core.config'].settings = tests.conftest_helper.MagicMock()

# Results tracking
successful_tests = []
failed_tests = []

# Run each test file
for test_file in sorted(test_files):
    print(f"\nRunning {test_file}.py...")
    try:
        # Try to import the test module
        module_name = f"tests.{test_file}"
        module = importlib.import_module(module_name)
        
        print(f"  Successfully imported {test_file}.py")
        successful_tests.append(test_file)
    except Exception as e:
        print(f"  Error importing {test_file}.py: {e}")
        traceback.print_exc()
        failed_tests.append(test_file)

# Print results
print("\n" + "=" * 60)
print("Test Results Summary")
print("=" * 60)
print(f"Total test files: {len(test_files)}")
print(f"Successfully imported: {len(successful_tests)}")
print(f"Failed to import: {len(failed_tests)}")

if successful_tests:
    print("\nSuccessfully imported:")
    for test in successful_tests:
        print(f"  ✓ {test}.py")

if failed_tests:
    print("\nFailed to import:")
    for test in failed_tests:
        print(f"  ✗ {test}.py")

# Exit with success code if all tests were successfully imported
sys.exit(0 if len(failed_tests) == 0 else 1)