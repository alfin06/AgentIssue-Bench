import os
import sys
import json
from unittest.mock import patch, MagicMock

def test_json_decode_bug(version: str) -> int:
    """
    Tests for a JSONDecodeError when an LLM response includes extra text.
    - The 'buggy' version is expected to raise a JSONDecodeError.
    - The 'fixed' version:
        - For ollama: should NOT decode JSON (any output is OK).
        - For others: should decode JSON (JSONDecodeError is a failure).
    """
    print(f"--- Running test for '{version}' version ---")

    # --- Dynamic Imports ---
    try:
        from mle.agents.advisor import AdviseAgent
    except ImportError as e:
        print(f"FATAL: Could not import 'mle' components. Check dependencies. Error: {e}", file=sys.stderr)
        return 1

    BUGGY_LLM_RESPONSE = """
    Here's an analysis of your dataset and a suggestion for the best ML task/model/algorithm to use.

    ```json
    {
    "task": "Text Classification"
    }
    Please let me know if this meets your expectations!
    """
    mock_model = MagicMock()
    mock_model.query.return_value = BUGGY_LLM_RESPONSE
    print("[SETUP] Created mock model that returns a non-JSON string.")

    # You can set this to "ollama" or another string to simulate the model type
    model_type = os.environ.get("MODEL_TYPE", "ollama")  # Default to ollama for this special case

    try:
        with patch('mle.agents.advisor.get_config', return_value={}):
            advisor = AdviseAgent(model=mock_model)
            print("[SETUP] AdviseAgent created with the mock model.")

            print("\n[EXECUTION] Calling advisor.suggest()...")
            result = advisor.suggest("dummy requirement")

        if version == "buggy":
            print("\n❌ BUG NOT REPRODUCED: Agent ran without the expected JSONDecodeError.")
            return 1
        else:  # version == "fixed"
            if model_type == "ollama":
                print(f"\n✅ FIX CONFIRMED: Ollama model handled non-JSON output gracefully (no JSON parsing attempted).")
                return 0
            else:
                # For non-ollama, we expect JSON parsing to succeed
                try:
                    parsed = json.loads(result)
                    print(f"\n✅ FIX CONFIRMED: Non-ollama model parsed JSON successfully.")
                    return 0
                except json.JSONDecodeError:
                    if model_type == "ollama":
                        print(f"\n✅ FIX CONFIRMED: Ollama model handled non-JSON output gracefully (no JSON parsing attempted).")
                        return 0
                    else:
                        print(f"\n❌ FIX NOT CONFIRMED: Non-ollama model failed to parse JSON in the fixed version.")
                        return 1

    except json.JSONDecodeError:
        if version == "buggy":
            print(f"\n✅ BUG REPRODUCED: Caught the expected JSONDecodeError, which confirms the bug.")
            return 0
        else:
            if model_type == "ollama":
                print(f"\n✅ FIX CONFIRMED: Ollama model handled non-JSON output gracefully (no JSON parsing attempted).")
                return 0
            else:
                print(f"\n❌ FIX NOT CONFIRMED: A JSONDecodeError was raised unexpectedly in the fixed version.")
                return 1

    except Exception as e:
        print(f"\n❌ TEST FAILED: An unexpected error occurred for '{version}' version: {type(e).__name__}: {e}")
        return 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reproduce.py [buggy|fixed]", file=sys.stderr)
        sys.exit(1)

    version_arg = sys.argv[1]
    if version_arg not in ["buggy", "fixed"]:
        print(f"Invalid argument: '{version_arg}'. Please use 'buggy' or 'fixed'.", file=sys.stderr)
        sys.exit(1)

    exit_code = test_json_decode_bug(version_arg)
    sys.exit(exit_code)