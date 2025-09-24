import os
from unittest.mock import patch, MagicMock

# Import the necessary Haystack components
from haystack.components.generators.chat.openai import OpenAIChatGenerator
from haystack.dataclasses.chat_message import ChatMessage
from haystack.components.websearch import SerperDevWebSearch
from haystack.tools import ComponentTool

# --- Setup ---
os.environ["OPENAI_API_KEY"] = input("Please enter an OPENAI_API_KEY: ")
os.environ["SERPERDEV_API_KEY"] = input("Please enter a SERPERDEV_API_KEY: ")

print("--- Initializing OpenAIChatGenerator with tools_strict=True ---")

web_search_component = SerperDevWebSearch()
search_tool = ComponentTool(component=web_search_component, name="web_search")

generator = OpenAIChatGenerator(model="gpt-4o", tools=[search_tool], tools_strict=True)

patch_target = "haystack.components.generators.chat.openai.OpenAIChatGenerator._prepare_api_call"


print("--- Calling generator.run() to trigger internal schema creation. ---")

try:
    with patch(patch_target, new_callable=MagicMock) as mock_prepare_api_call:
        mock_prepare_api_call.return_value = {"messages": [], "model": "gpt-4o"}

        generator.run(messages=[ChatMessage.from_user("some query")])

        if not mock_prepare_api_call.called:
             raise AssertionError("The generator's _prepare_api_call method was not called.")
        
        call_kwargs = mock_prepare_api_call.call_args.kwargs
        
        tools_payload = call_kwargs.get("tools", [])
        
        if not tools_payload:
            raise AssertionError("The 'tools' payload was not generated and passed to _prepare_api_call.")

        tool_function_params = tools_payload[0].get("function", {}).get("parameters", {})

        print("\n--- Analyzing the generated tool schema ---")
        print(f"Generated Schema: {tool_function_params}")

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