import os
import sys
import unittest
import json
from unittest.mock import patch, MagicMock

os.environ["OPENAI_API_KEY"] = input("Enter an OPENAI API KEY: ")

try:
    from mle.agents.advisor import AdviseAgent
    from mle.utils import get_config
except ImportError as e:
    print(f"FATAL: Could not import necessary modules. Check dependencies. Error: {e}", flush=True)
    sys.exit(1)

# --- Test Case ---
class TestJsonFormatError(unittest.TestCase):

    # This is the problematic response from the bug report.
    BUGGY_LLM_RESPONSE = """
Here's an analysis of your dataset and a suggestion for the best ML task/model/algorithm to use.

```json
{
  "task": "Text Classification"
}
```
Please let me know if this meets your expectations!
"""

    # We patch the get_config function to prevent an error during agent initialization.
    @patch('mle.agents.advisor.get_config')
    def test_json_decode_error(self, mock_get_config):
        """
        This test verifies that a JSONDecodeError is raised when the LLM
        response contains text before the JSON object.
        """
        print("\n--- Attempting to reproduce the bug from MLE-agent/issues/173 ---", flush=True)
        print("This test will check for a JSONDecodeError.", flush=True)

        # Configure the mock for get_config to return an empty dict.
        mock_get_config.return_value = {}
        print("[SETUP] Patched get_config to prevent initialization error.", flush=True)

        # Create a mock LLM instance manually.
        mock_model = MagicMock()
        mock_model.query.return_value = self.BUGGY_LLM_RESPONSE
        print("[SETUP] Manually created a mock model that returns a non-JSON string.", flush=True)

        # Set up the AdviseAgent, passing our mock model directly.
        advisor = AdviseAgent(model=mock_model)
        print("[SETUP] AdviseAgent created with the mock model.", flush=True)

        # Execute the suggest method and check for the expected error.
        print("\n[EXECUTION] Calling advisor.suggest()... This is expected to fail with JSONDecodeError.", flush=True)
        try:
            advisor.suggest("requirement")
            
            print("\nREPRODUCTION FAILED", flush=True)
            self.fail("The agent did not raise the expected JSONDecodeError. The bug may be fixed.")

        except json.JSONDecodeError as e:
            print("\nREPRODUCTION SUCCESSFUL", flush=True)
            print(f"Successfully caught expected exception: {type(e).__name__}", flush=True)
        
        except Exception as e:
            print("\nREPRODUCTION FAILED", flush=True)
            self.fail(f"An unexpected error occurred: {type(e).__name__}: {e}")


# --- Main execution block ---
if __name__ == '__main__':
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestJsonFormatError))
    runner = unittest.TextTestRunner()
    result = runner.run(suite)

    sys.exit(not result.wasSuccessful())
