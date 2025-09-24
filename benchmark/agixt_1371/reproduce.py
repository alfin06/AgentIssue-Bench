import asyncio
import sys
from unittest.mock import patch, MagicMock

# --- Test Setup ---
# The goal is to import the actual GraphQL Query class and test its 'chain' resolver.
try:
    # This import will work because the Dockerfile correctly installs the package.
    from agixt.endpoints.GQL import Query
except ImportError as e:
    print(f"FATAL: Could not import the necessary module. Check the installation. Error: {e}")
    sys.exit(1)

print("--- Testing the 'chain' GraphQL resolver's unpacking logic. ---")
print("--- This is expected to raise a ValueError in the buggy version. ---")

# The target for our patch: the function that returns too many values.
patch_target = "agixt.endpoints.GQL.get_user_from_context"

async def run_test():
    try:
        # We patch the function to return 3 values, simulating the real function's behavior.
        # The buggy code `user, _ = ...` will fail because it only expects 2.
        with patch(patch_target, return_value=("user", "auth", "magical")):
            
            # Create an instance of the GraphQL Query resolver class
            query_resolver = Query()

            # Create a mock 'info' object, which is required by the resolver method.
            mock_info = MagicMock()

            # This is the line that will trigger the bug.
            # We call the 'chain' method, which contains the faulty unpacking logic.
            await query_resolver.chain(info=mock_info, chain_name="Any Chain Name")

        # If this line is reached, it means no error was thrown.
        print("\n--- SCRIPT FINISHED UNEXPECTEDLY ---")
        print("FAILURE: The bug was NOT reproduced. The resolver executed successfully.")
        sys.exit(0)

    except ValueError as e:
        # We expect a ValueError. Now we verify it's the correct one.
        print(f"\nSUCCESS: The script failed with a ValueError as expected.")
        print(f"Error Message: {e}")

        expected_error_text = "too many values to unpack"
        if expected_error_text in str(e):
            print("\nVerification successful: The error message matches the bug report.")
            # Exit with 1 to signal to the test runner that the bug was found.
            sys.exit(1)
        else:
            print("\nVerification failed: The ValueError message did not match the expected bug.")
            sys.exit(0)
    except Exception as e:
        # Catch any other unexpected errors
        print(f"\nFAILURE: An unexpected error occurred: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(run_test())
