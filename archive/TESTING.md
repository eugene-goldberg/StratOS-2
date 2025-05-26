# Testing Guide

This document provides guidance for running tests in the StratOS-2 project.

## Test Files

All test files are located in the `tests/` directory. The project uses pytest as the testing framework.

### New C1 Conversational Memory Tests

The following test files have been added for the C1 Conversational Memory implementation:

- `test_conversation_models.py` - Tests for Pydantic models (25 test methods)
- `test_conversation_service.py` - Tests for conversation service layer (40+ test methods)  
- `test_conversation_router.py` - Tests for API endpoints (25+ test methods)
- `test_conversation_ai_skills.py` - Tests for AI skills functionality (25+ test methods)
- `test_conversation_integration.py` - End-to-end integration tests (15+ test methods)

**Total**: 130+ new test methods providing comprehensive coverage of conversational memory functionality.

## Running Tests

There are several ways to run the tests:

### Option 1: Run All Tests with pytest

To run all tests at once:

```bash
python -m pytest -xvs tests/
```

### Option 2: Run Only Conversation Tests

To run only the new conversation memory tests:

```bash
python run_conversation_tests.py
```

Or with pytest:

```bash
python -m pytest tests/test_conversation*.py -v
```

### Option 2: Run Tests with the Custom Runner Script

Use the provided script to run all tests individually and get a detailed report:

```bash
python run_all_tests.py
```

This script will:
- Run each test file separately
- Capture the output of each test
- Generate a report in the `test_results/` directory
- Provide a summary of passing and failing tests
- Identify tests failing due to missing dependencies

### Option 3: Run Specific Tests

To run a single test file:

```bash
python -m pytest -xvs tests/test_auth_service.py
```

To run a specific test function:

```bash
python -m pytest -xvs tests/test_auth_service.py::test_function_name
```

## Dependencies

All the tests require the following packages:

- pytest
- pytest-asyncio
- pytest-mock
- fastapi
- httpx
- semantic-kernel
- azure-identity
- azure-cosmos
- azure-storage-blob

You can install all dependencies using:

```bash
pip install -r requirements.txt
```

## Test Results

The `run_all_tests.py` script saves test results in the `test_results/` directory. Each run creates a timestamped file with detailed output from all test executions.

## Mocks and Fixtures

The tests use:

- `conftest.py` - Contains common pytest fixtures
- `conftest_helper.py` - Mocks external dependencies
- `mock_setup.py` - Additional mock utilities

## Troubleshooting

If tests fail with `ModuleNotFoundError`, check if all dependencies are installed.

For tests that require Azure services, ensure proper mocking is in place to prevent actual API calls during tests.

## Adding New Tests

When adding new tests:

1. Create a new file in the `tests/` directory with a name starting with `test_`
2. Import the required modules and services
3. Use pytest fixtures from `conftest.py` where appropriate
4. Add mock responses for any external services
5. Ensure the test can run without external dependencies