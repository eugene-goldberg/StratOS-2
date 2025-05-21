# Test Results

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
