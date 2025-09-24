import sys
import os
from unittest.mock import MagicMock

# --- Test Setup ---
try:
    from gpt_engineer.core.default.steps import salvage_correct_hunks
    from gpt_engineer.core.chat_to_files import parse_diffs, Hunk, Diff
except ImportError as e:
    print(f"FATAL: Could not import necessary modules. Check installation. Error: {e}")
    sys.exit(1)

print("--- Testing the 'salvage_correct_hunks' function. ---")
print("--- Providing a mock LLM response that references a non-existent file. ---")
print("--- This is expected to raise a KeyError in the buggy version. ---")

initial_files = {
    "src/main/resources/application.yml": "spring:\n  profiles:\n    active: default",
    "run.sh": "#!/bin/bash\njava -jar myapp.jar"
}

mock_llm_response = """
I have created the new files as requested.

```diff
--- src/main/resources/application-stage.yml
+++ src/main/resources/application-stage.yml
@@ -1,3 +1,3 @@
 spring:
   datasource:
-    url: jdbc:mysql://stage-db-url
+    url: jdbc:mysql://new-stage-db-url
```
"""

class MockMessage:
    def __init__(self, content):
        self.content = content

mock_messages = [MockMessage(mock_llm_response)]

# --- Verification Logic ---
try:
    salvage_correct_hunks(mock_messages, initial_files, MagicMock())

    print("\n--- SCRIPT FINISHED UNEXPECTEDLY ---")
    print("FAILURE: The bug was NOT reproduced. The KeyError was not raised.")
    sys.exit(0)

except KeyError as e:
    print(f"\nSUCCESS: The script failed with a KeyError as expected.")
    print(f"Error Message: {e}")

    expected_key = "'src/main/resources/application-stage.yml'"
    if expected_key in str(e):
        print(f"\nVerification successful: The KeyError for {expected_key} was raised, which confirms the bug.")
        sys.exit(1)
    else:
        print("\nVerification failed: The KeyError did not match the expected file.")
        sys.exit(0)
except Exception as e:
    print(f"\nFAILURE: An unexpected error occurred: {type(e).__name__}: {e}")
    sys.exit(0)