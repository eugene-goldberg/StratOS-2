"""
Run test_analysis_service.py::test_discover_so_linkages_basic directly
"""
import pytest
import sys
import os

# Import conftest_helper before any other imports to set up mocks
import tests.conftest_helper

if __name__ == "__main__":
    # Run the test
    sys.exit(pytest.main(["-xvs", "tests/test_analysis_service.py::test_discover_so_linkages_basic"]))