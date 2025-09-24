import asyncio
import sys

# --- Test Setup ---
try:
    from agixt.Websearch import Websearch
except ImportError as e:
    print(f"FATAL: Could not import the necessary module. Check the installation. Error: {e}")
    sys.exit(1)

buggy_websearch_depth_as_string = "3"

print("--- Initializing the Websearch class. ---")
try:
    # We create an instance of the class. The __init__ method requires an agent_name
    # and a config dictionary. We provide minimal values to satisfy it.
    websearch_instance = Websearch(
        agent_name="TestAgent",
        agent_config={"provider": "mock", "settings": {"WEBSEARCH_DEPTH": buggy_websearch_depth_as_string}}
    )
except Exception as e:
    print(f"Failed to initialize Websearch class. Error: {e}")
    sys.exit(0)


print("--- Calling the websearch_agent method with a string for websearch_depth. ---")
print("--- This is expected to raise a TypeError in the buggy version. ---")

async def run_test():
    try:
        await websearch_instance.websearch_agent(
            user_input="search for something",
            websearch_depth=buggy_websearch_depth_as_string
        )

        print("\n--- SCRIPT FINISHED UNEXPECTEDLY ---")
        print("FAILURE: The bug was NOT reproduced. The method executed successfully.")
        sys.exit(0)

    except TypeError as e:
        print(f"\nSUCCESS: The script failed with a TypeError as expected.")
        print(f"Error Message: {e}")

        expected_error_text = "'>' not supported between instances of 'str' and 'int'"
        if expected_error_text in str(e):
            print("\nVerification successful: The error message matches the bug report.")
            sys.exit(1)
        else:
            print("\nVerification failed: The TypeError message did not match the expected bug.")
            sys.exit(0)
    except Exception as e:
        print(f"\nFAILURE: An unexpected error occurred: {type(e).__name__}: {e}")
        sys.exit(0)

if __name__ == "__main__":
    asyncio.run(run_test())