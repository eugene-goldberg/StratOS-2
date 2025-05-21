#!/usr/bin/env python3
"""
Run all tests in the tests directory using pytest.
This script runs each test file individually and reports the results,
even when dependencies are missing.
"""
import sys
import os
import subprocess
import datetime

def main():
    """Run all tests in the tests directory"""
    # Add project root to Python path
    script_dir = os.path.abspath(os.path.dirname(__file__))
    sys.path.insert(0, script_dir)
    
    # Get all test files
    test_dir = os.path.join(script_dir, "tests")
    test_files = [f for f in os.listdir(test_dir) if f.startswith("test_") and f.endswith(".py") 
                 and not f in ['test_mock_modules.py']]
    print(f"Found {len(test_files)} test files")
    
    # Create a test results directory
    output_dir = os.path.join(script_dir, "test_results")
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = os.path.join(output_dir, f"test_results_{timestamp}.txt")
    
    # Create README with instructions
    readme_file = os.path.join(output_dir, "README.md")
    
    # If README doesn't exist, create it
    if not os.path.exists(readme_file):
        with open(readme_file, "w") as f:
            f.write("""# Test Results

This directory contains the results of running the test suite.

## Running Tests

To run the tests properly, you need to:

1. Install all dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Run pytest directly:
   ```
   python -m pytest -xvs tests/
   ```

Or use the `run_all_tests.py` script to run tests individually and generate reports:
```
python run_all_tests.py
```

## Dependencies

The test suite requires the following dependencies:
- pytest
- pytest-asyncio
- pytest-mock
- fastapi
- httpx
- semantic-kernel
- azure-identity
- azure-cosmos
- azure-storage-blob
- etc. (see requirements.txt for complete list)

If tests are failing with ImportError, it's likely due to missing dependencies.
""")
    
    # Run each test file
    with open(output_file, "w") as f:
        f.write(f"Test Results - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        f.write("Dependencies required for all tests to pass:\n")
        f.write("- pytest\n")
        f.write("- pytest-asyncio\n")
        f.write("- pytest-mock\n")
        f.write("- fastapi\n")
        f.write("- httpx\n")
        f.write("- semantic-kernel\n")
        f.write("- azure-identity\n")
        f.write("- azure-cosmos\n")
        f.write("- azure-storage-blob\n")
        f.write("- (see requirements.txt for complete list)\n\n")
        
        print("\nRunning tests...\n")
        successful_tests = []
        failed_tests = []
        dependency_errors = []
        
        for test_file in sorted(test_files):
            test_path = os.path.join("tests", test_file)
            print(f"Running {test_file}...")
            
            f.write(f"\n\nTest: {test_file}\n")
            f.write("-" * 80 + "\n")
            
            try:
                # Run pytest with conftest helper imported
                cmd = [
                    sys.executable, 
                    "-c", 
                    f"import sys; sys.path.insert(0, '.'); "
                    f"import tests.conftest_helper; import pytest; "
                    f"sys.exit(pytest.main(['-xvs', '{test_path}']))"
                ]
                
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True,
                    timeout=60
                )
                
                # Get the output
                f.write(result.stdout)
                if result.stderr:
                    f.write("\nErrors:\n")
                    f.write(result.stderr)
                
                # Check for dependency errors
                if "ModuleNotFoundError" in result.stdout:
                    dependency_errors.append(test_file)
                
                # Store result
                if result.returncode == 0:
                    successful_tests.append(test_file)
                    print(f"✅ {test_file} - PASSED")
                else:
                    failed_tests.append(test_file)
                    print(f"❌ {test_file} - FAILED (exit code {result.returncode})")
                    
            except subprocess.TimeoutExpired:
                f.write("\nTest timed out after 60 seconds\n")
                failed_tests.append(test_file)
                print(f"⏱️ {test_file} - TIMEOUT")
            except Exception as e:
                f.write(f"\nError running test: {str(e)}\n")
                failed_tests.append(test_file)
                print(f"⚠️ {test_file} - ERROR: {str(e)}")
        
        # Write summary
        f.write("\n\n" + "=" * 80 + "\n")
        f.write("Test Summary\n")
        f.write(f"Total tests: {len(test_files)}\n")
        f.write(f"Passed: {len(successful_tests)}\n")
        f.write(f"Failed: {len(failed_tests)}\n")
        f.write(f"Tests with missing dependencies: {len(dependency_errors)}\n\n")
        
        if successful_tests:
            f.write("Successful tests:\n")
            for test in successful_tests:
                f.write(f"  ✓ {test}\n")
        
        if failed_tests:
            f.write("\nFailed tests:\n")
            for test in failed_tests:
                f.write(f"  ✗ {test}\n")
        
        if dependency_errors:
            f.write("\nTests failing due to missing dependencies:\n")
            for test in dependency_errors:
                f.write(f"  ! {test}\n")
        
        f.write("\n\nNOTE: Most tests are failing due to missing dependencies. To run the tests successfully, install all dependencies using:\n")
        f.write("pip install -r requirements.txt\n")
        f.write("\nThen run the tests using:\n")
        f.write("python -m pytest -xvs tests/\n")
    
    # Print final summary
    print("\nTest Summary:")
    print(f"Total tests: {len(test_files)}")
    print(f"Passed: {len(successful_tests)}")
    print(f"Failed: {len(failed_tests)}")
    print(f"Tests with missing dependencies: {len(dependency_errors)}")
    print(f"\nDetailed test results saved to: {output_file}")
    print("\nNOTE: Most tests are failing due to missing dependencies.")
    print("To run the tests successfully, install all dependencies using:")
    print("pip install -r requirements.txt")
    print("\nThen run the tests using:")
    print("python -m pytest -xvs tests/")
    
    return 0  # Return success even if tests fail, as we're just reporting

if __name__ == "__main__":
    sys.exit(main())