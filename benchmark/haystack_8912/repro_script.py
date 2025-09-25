import os
from unittest.mock import patch, MagicMock

# Import the necessary Haystack components
from haystack.components.generators.chat.openai import OpenAIChatGenerator
from haystack.dataclasses.chat_message import ChatMessage
from haystack.components.websearch import SerperDevWebSearch
from haystack.tools import ComponentTool

# --- Setup ---
# 1. Set dummy API keys to satisfy the __init__ methods of the real components.
#os.environ["OPENAI_API_KEY"] = "DUMMY_KEY"
#os.environ["SERPERDEV_API_KEY"] = "DUMMY_KEY"

print("--- Initializing OpenAIChatGenerator with tools_strict=True ---")

# 2. Instantiate the real components needed for the test.
web_search_component = SerperDevWebSearch()
search_tool = ComponentTool(component=web_search_component, name="web_search")

# 3. Initialize the generator with the strict tools flag enabled.
generator = OpenAIChatGenerator(model="gpt-4o", tools=[search_tool], tools_strict=True)

# 4. Define the target for our mock: the generator's internal method for preparing the API call.
#    This allows us to inspect the generated data without running the full API call cycle.
patch_target = "haystack.components.generators.chat.openai.OpenAIChatGenerator._prepare_api_call"


# --- Verification Logic ---
print("--- Calling generator.run() to trigger internal schema creation. ---")

try:
    # We patch the generator's internal method.
    with patch(patch_target, new_callable=MagicMock) as mock_prepare_api_call:
        # We need the mock to return a valid dictionary so the rest of the
        # `run` method doesn't crash, even though we will exit before it finishes.
        mock_prepare_api_call.return_value = {"messages": [], "model": "gpt-4o"}

        # This call will now trigger our mock.
        generator.run(messages=[ChatMessage.from_user("some query")])

        # --- Verification of the Bug ---
        # Get the keyword arguments that were passed to our mock.
        if not mock_prepare_api_call.called:
             raise AssertionError("The generator's _prepare_api_call method was not called.")
        
        # The arguments passed to our mock are what we need to inspect.
        # The full tool payload is generated and passed within these arguments.
        call_kwargs = mock_prepare_api_call.call_args.kwargs
        
        # The tool schemas are in the 'tools' keyword argument.
        tools_payload = call_kwargs.get("tools", [])
        
        if not tools_payload:
            raise AssertionError("The 'tools' payload was not generated and passed to _prepare_api_call.")

        # Find the function parameters for our specific tool
        tool_function_params = tools_payload[0].get("function", {}).get("parameters", {})

        print("\n--- Analyzing the generated tool schema ---")
        print(f"Generated Schema: {tool_function_params}")

        # The bug is that 'additionalProperties' is MISSING from the schema.
        if "additionalProperties" not in tool_function_params:
            print("\nSUCCESS: The bug is reproduced.")
            print("The 'additionalProperties' key was NOT found in the tool's function schema.")
            exit(1)
        else:
            print("\nFAILURE: The bug was NOT reproduced.")
            print("The 'additionalProperties' key was found in the schema.")
            exit(0)

except Exception as e:
    print(f"\nFAILURE: The script failed with an unexpected error: {type(e).__name__}: {e}")
    exit(0)