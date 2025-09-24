import asyncio
import sys
from unittest.mock import patch, MagicMock

# --- Test Setup ---
try:
    from agixt.endpoints.GQL import Query
except ImportError as e:
    print(f"FATAL: Could not import the necessary module. Check the installation. Error: {e}")
    sys.exit(1)

print("--- Testing the 'chain' GraphQL resolver's unpacking logic. ---")
print("--- This is expected to raise a ValueError in the buggy version. ---")

patch_target = "agixt.endpoints.GQL.get_user_from_context"

async def run_test():
    try:
        with patch(patch_target, return_value=("user", "auth", "magical")):
            
            query_resolver = Query()

            mock_info = MagicMock()

            # This is the line that will trigger the bug.
            # We call the 'chain' method, which contains the faulty unpacking logic.
            await query_resolver.chain(info=mock_info, chain_name="Any Chain Name")

        print("\n--- SCRIPT FINISHED ---")
        print("The bug was NOT reproduced. The resolver executed successfully.")
        sys.exit(0)

    except ValueError as e:
        print(f"\nThe script failed with a ValueError as expected.")
        print(f"Error Message: {e}")

        expected_error_text = "too many values to unpack"
        if expected_error_text in str(e):
            print("\nVerification successful: The error message matches the bug report.")
            sys.exit(1)
        else:
            print("\nVerification failed: The ValueError message did not match the expected bug.")
            sys.exit(0)
    except Exception as e:
        print(f"\nFAILURE: An unexpected error occurred: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(run_test())
