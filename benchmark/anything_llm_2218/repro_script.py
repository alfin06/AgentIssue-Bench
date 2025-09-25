import os
import json
from openapi_spec_validator import validate

# --- Test Configuration ---
# The path to the OpenAPI spec file within the checked-out source code
SPEC_FILE_PATH = "/app/source_code_buggy/server/swagger/openapi.json"

print(f"--- Attempting to validate OpenAPI spec at: {SPEC_FILE_PATH} ---")

# --- Verification Logic ---

# 1. Check if the file exists
if not os.path.exists(SPEC_FILE_PATH):
    print(f"FAILURE: The OpenAPI spec file was not found at the expected path.")
    exit(0) # Exit with 0 because the test itself failed, not that the bug was found

# 2. Try to validate the file
try:
    # The `validate` function takes a spec dictionary, so we load the JSON file first
    with open(SPEC_FILE_PATH, 'r') as f:
        spec_dict = json.load(f)

    # This function will raise an exception if the spec is invalid
    validate(spec_dict)

    # If the line above does not raise an exception, the file is valid,
    # meaning the bug was NOT reproduced.
    print("\n--- SCRIPT FINISHED UNEXPECTEDLY ---")
    print("FAILURE: The OpenAPI spec was successfully validated, which means the bug was NOT reproduced.")
    exit(0)

except Exception as e:
    # Any exception during validation is considered a successful reproduction of the bug.
    # The specific error could be a JSON parsing error or a spec validation error.
    print(f"\nSUCCESS: The bug was reproduced. The validator raised an error as expected.")
    print(f"Error Type: {type(e).__name__}")
    print(f"Error Message: {e}")

    # Exit with a non-zero code to signal that the bug was successfully found.
    exit(1)