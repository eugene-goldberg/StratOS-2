#!/usr/bin/env python3
"""
Run all tests in the tests directory using pytest
"""
import sys
import os
import subprocess
import datetime

def main():
    """Run all tests in the tests directory"""
    # Add project root to Python path
    sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
    
    # Get all test files
    test_files = [f for f in os.listdir("tests") if f.startswith("test_") and f.endswith(".py") and f != "test_mock_modules.py"]
    print(f"Found {len(test_files)} test files")
    
    # Create a test results directory
    output_dir = "test_results"
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_file = os.path.join(output_dir, f"test_results_{timestamp}.txt")
    
    # Run each test file
    with open(output_file, "w") as f:
        f.write(f"Test Results - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        print("\nRunning tests...\n")
        successful_tests = []
        failed_tests = []
        
        for test_file in sorted(test_files):
            test_path = os.path.join("tests", test_file)
            print(f"Running {test_file}...")
            
            f.write(f"\n\nTest: {test_file}\n")
            f.write("-" * 80 + "\n")
            
            try:
                # Run pytest with conftest helper imported
                result = subprocess.run(
                    ["python", "-c", f"import sys; sys.path.insert(0, '.'); import tests.conftest_helper; import pytest; sys.exit(pytest.main(['-xvs', '{test_path}']))"], 
                    capture_output=True, 
                    text=True,
                    timeout=60
                )
                
                # Get the output
                f.write(result.stdout)
                if result.stderr:
                    f.write("\nErrors:\n")
                    f.write(result.stderr)
                
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
        f.write(f"Failed: {len(failed_tests)}\n\n")
        
        if successful_tests:
            f.write("Successful tests:\n")
            for test in successful_tests:
                f.write(f"  ✓ {test}\n")
        
        if failed_tests:
            f.write("\nFailed tests:\n")
            for test in failed_tests:
                f.write(f"  ✗ {test}\n")
    
    # Print final summary
    print("\nTest Summary:")
    print(f"Total tests: {len(test_files)}")
    print(f"Passed: {len(successful_tests)}")
    print(f"Failed: {len(failed_tests)}")
    print(f"\nDetailed test results saved to: {output_file}")
    
    return 0 if len(failed_tests) == 0 else 1

if __name__ == "__main__":
    sys.exit(main())