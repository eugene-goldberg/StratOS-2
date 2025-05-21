# Outstanding Test Work as of 2025-05-21

This document outlines the tests that still require attention to ensure full coverage and stability of the backend services.

## 1. `tests/test_analysis_service.py`

*   **Failing Test:** `test_discover_so_linkages_basic`
    *   **Issue:** Currently fails with an `IndexError: tuple index out of range` within the `mock_run_async_replacement` function used to mock `kernel_service.run_async`.
    *   **Reason:** The mock function incorrectly assumes the structure of arguments passed to `kernel_service.run_async`. The `run_async` method in `KernelService` is called with `(sk_function_object, input_vars=context_vars)`, meaning `args[0]` is the function object and `args[1]` does not exist, leading to the `IndexError`.
    *   **Required Action:**
        1.  Correct the `mock_run_async_replacement` in `tests/test_analysis_service.py`.
            *   It should expect `args[0]` to be the Semantic Kernel function object (or its name, based on the current `get_function` mock).
            *   It needs to correctly identify the function being called (e.g., "fetch_relevant_subjective_notes", "FindPotentialLinkages") based on `args[0]`.
            *   The mock should return a `MagicMock` instance whose `.result` attribute contains the expected string output, to simulate `SKContext.result`.
        2.  Ensure the `mock_ks.create_new_context` correctly simulates SKContext variable assignment if methods rely on setting variables on the context object.
    *   **Last Attempt to Fix:** A `replace_in_file` operation to correct this mock was denied by the user, so the file `tests/test_analysis_service.py` contains the version with the error.

## 2. Untested Service Test Files

The following test files for services have not yet been executed in the current testing session. They need to be run, and any failures or issues (similar to those encountered with `AuthService`, `ObjectiveDataService`, and `AnalysisService`) need to be addressed. This will likely involve:
    *   Updating Pydantic V1 usage (`.dict()` to `.model_dump()`, `Config` to `model_config`, etc.).
    *   Ensuring Semantic Kernel V1.x compatibility if these services use `kernel_service`.
    *   Refining test mocks for Azure services (Cosmos DB, Blob Storage) and `kernel_service` interactions.

*   **`tests/test_planning_service.py`**
*   **`tests/test_subjective_input_service.py`**

## 3. General Test Warnings and Improvements

Across all test files, the following general warnings and potential improvements should be addressed:

*   **PyPDF2 Deprecation:**
    *   **Warning:** `DeprecationWarning: PyPDF2 is deprecated. Please move to the pypdf library instead.`
    *   **Action:** Plan and execute the migration from `PyPDF2` to `pypdf` in `backend/services/objective_data_service.py` (and any other relevant places) to resolve this warning.
*   **Pydantic `__get_pydantic_core_schema__` Deprecation:**
    *   **Warning:** `PydanticDeprecatedSince211: The \`__get_pydantic_core_schema__\` method of the \`BaseModel\` class is deprecated.`
    *   **Action:** This is a general Pydantic V2 warning. While it doesn't break functionality now, investigate if any custom models are unnecessarily overriding this or if it's an internal Pydantic warning that can be ignored for now or addressed by a future Pydantic update.
*   **Unawaited Coroutine in `ObjectiveDataService` Tests:**
    *   **Warning:** `RuntimeWarning: coroutine 'ObjectiveDataService._process_file_background' was never awaited` in `test_process_uploaded_file_flow`.
    *   **Action:**
        *   Decide if the completion of `_process_file_background` is relevant to the assertions in `test_process_uploaded_file_flow`.
        *   If relevant, the test needs to await this background task. This might involve capturing the task object created by `asyncio.create_task` and awaiting it.
        *   If not relevant for this specific test's assertions, consider if the warning can be safely ignored for this test or if the task should be explicitly managed (e.g., cancelled in test teardown if it were a long-running task, though likely not an issue here).
*   **Review `model_config` for Pydantic Models:**
    *   Ensure all Pydantic models (e.g., in `backend/models/`) are correctly using `model_config = SettingsConfigDict(protected_namespaces=())` or similar, instead of the old `class Config: protected_namespaces = ()`, if they have protected namespaces and are not settings models. This was done for `backend/core/config.py` but needs checking elsewhere.

## 4. Test Coverage
*   Once all existing tests are passing, review test coverage for all services and add missing tests to cover more scenarios, edge cases, and error conditions.
