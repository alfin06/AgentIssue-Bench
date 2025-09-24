import os
import json
from openapi_spec_validator import validate

# --- Test Configuration ---
SPEC_FILE_PATH = "/app/source_code_buggy/server/swagger/openapi.json"

print(f"--- Attempting to validate OpenAPI spec at: {SPEC_FILE_PATH} ---")

# --- Verification Logic ---

# 1. Check if the file exists
if not os.path.exists(SPEC_FILE_PATH):
    print(f"FAILURE: The OpenAPI spec file was not found at the expected path.")
    exit(0)

# 2. Try to validate the file
try:
    with open(SPEC_FILE_PATH, 'r') as f:
        spec_dict = json.load(f)

    validate(spec_dict)

    print("\n--- SCRIPT FINISHED UNEXPECTEDLY ---")
    print("FAILURE: The OpenAPI spec was successfully validated, which means the bug was NOT reproduced.")
    exit(0)

except Exception as e:
    print(f"\nSUCCESS: The bug was reproduced. The validator raised an error as expected.")
    print(f"Error Type: {type(e).__name__}")
    print(f"Error Message: {e}")

    exit(1)