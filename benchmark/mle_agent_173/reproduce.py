import os
import sys
import json
from unittest.mock import patch, MagicMock

def test_json_decode_bug(version: str) -> int:
    """
    Tests for a JSONDecodeError when an LLM response includes extra text.
    - The 'buggy' version is expected to raise a JSONDecodeError.
    - The 'fixed' version is expected to parse the JSON and run successfully.
    """
    print(f"--- Running test for '{version}' version ---")

    # --- Dynamic Imports ---
    # Import components here to ensure the correct version (buggy or fixed) is loaded.
    try:
        from mle.agents.advisor import AdviseAgent
    except ImportError as e:
        print(f"FATAL: Could not import 'mle' components. Check dependencies. Error: {e}", file=sys.stderr)
        return 1

    # --- Test Setup & Mocks ---
    # This is the problematic response from the bug report with leading/trailing text.
    BUGGY_LLM_RESPONSE = """
    Here's an analysis of your dataset and a suggestion for the best ML task/model/algorithm to use.

    ```json
    {
    "task": "Text Classification"
    }
    Please let me know if this meets your expectations!
    """
    # Create a mock LLM instance that will return the malformed response.
    mock_model = MagicMock()
    mock_model.query.return_value = BUGGY_LLM_RESPONSE
    print("[SETUP] Created mock model that returns a non-JSON string.")

    # --- Version-Specific Verification ---
    try:
        # We patch get_config to prevent errors during agent initialization.
        with patch('mle.agents.advisor.get_config', return_value={}):
            advisor = AdviseAgent(model=mock_model)
            print("[SETUP] AdviseAgent created with the mock model.")

            print("\n[EXECUTION] Calling advisor.suggest()...")
            advisor.suggest("dummy requirement")
        
        # --- Analysis for when NO error is raised ---
        if version == "buggy":
            print("\n❌ BUG NOT REPRODUCED: Agent ran without the expected JSONDecodeError.")
            return 1
        else: # version == "fixed"
            print("\n✅ FIX CONFIRMED: Agent successfully parsed the JSON, as expected for the fixed version.")
            return 0

    except json.JSONDecodeError:
        # --- Analysis for when a JSONDecodeError IS raised ---
        if version == "buggy":
            print(f"\n✅ BUG REPRODUCED: Caught the expected JSONDecodeError, which confirms the bug.")
            return 0
        else: # version == "fixed"
            print(f"\n❌ FIX NOT CONFIRMED: A JSONDecodeError was raised unexpectedly in the fixed version.")
            return 1

    except Exception as e:
        # --- Analysis for any other unexpected errors ---
        print(f"\n❌ TEST FAILED: An unexpected error occurred for '{version}' version: {type(e).__name__}: {e}")
        return 1
    
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reproduce.py [buggy|fixed]", file=sys.stderr)
        sys.exit(1)

    version = sys.argv[1]
    if version not in ["buggy", "fixed"]:
        print("Invalid argument. Please use 'buggy' or 'fixed'.", file=sys.stderr)
        sys.exit(1)

    version_arg = sys.argv[1]
    if version_arg not in ["buggy", "fixed"]:
        print(f"Invalid argument: '{version_arg}'. Please use 'buggy' or 'fixed'.", file=sys.stderr)
        sys.exit(1)

    # The exit code determines the success (0) or failure (1) of the test run.
    exit_code = test_json_decode_bug(version_arg)
    sys.exit(exit_code)