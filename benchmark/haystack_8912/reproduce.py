import os
import sys
from unittest.mock import patch

from haystack.components.generators.chat.openai import OpenAIChatGenerator
from haystack.dataclasses.chat_message import ChatMessage
from haystack.components.websearch import SerperDevWebSearch
from haystack.tools import ComponentTool

def test_tools_strict_schema_bug(version: str) -> int:
    """
    Failure-triggering test for Haystack issue #8912:
    When using ComponentTool and setting tools_strict=True, the OpenAI API complains that
    'additionalProperties' of the schema is not 'false'.
    This test checks if 'additionalProperties': False is present in the generated tool schema.
    """
    print(f"--- Running test for '{version}' version ---")
    print("--- Initializing OpenAIChatGenerator with tools_strict=True ---")

    # Set dummy API keys to satisfy the __init__ methods if needed
    os.environ["OPENAI_API_KEY"] = "DUMMY_KEY"
    os.environ["SERPERDEV_API_KEY"] = "DUMMY_KEY"

    # Instantiate the real components needed for the test.
    web_search_component = SerperDevWebSearch()
    search_tool = ComponentTool(component=web_search_component, name="web_search")

    # Initialize the generator with the strict tools flag enabled.
    generator = OpenAIChatGenerator(model="gpt-4o", tools=[search_tool], tools_strict=True)

    patch_target = "haystack.components.generators.chat.openai.OpenAIChatGenerator._prepare_api_call"

    print("--- Calling generator.run() to trigger internal schema creation. ---")

    try:
        def fake_prepare_api_call(*args, **kwargs):
            tools_payload = kwargs.get("tools", [])
            tool_function_params = tools_payload[0].get("function", {}).get("parameters", {}) if tools_payload else {}
            print("\n--- Analyzing the generated tool schema ---")
            print(f"Generated Schema: {tool_function_params}")
            has_additional_properties = (
                "additionalProperties" in tool_function_params and tool_function_params["additionalProperties"] is False
            )
            if version == "buggy":
                if has_additional_properties:
                    print("\n❌ BUG NOT REPRODUCED: 'additionalProperties': False was found in the buggy version (should be missing).")
                    exit(1)
                else:
                    print("\n✅ BUG REPRODUCED: 'additionalProperties': False is missing in the buggy version as expected.")
                    exit(0)
            else:  # fixed
                if has_additional_properties:
                    print("\n❌ FIX NOT CONFIRMED: 'additionalProperties': False is missing in the fixed version (should be present).")
                    exit(1)
                else:
                    print("\n✅ FIX CONFIRMED: 'additionalProperties': False is present in the fixed version as expected.")
                    exit(0)

        with patch(patch_target, side_effect=fake_prepare_api_call):
            generator.run(messages=[ChatMessage.from_user("How is the weather today in Berlin?")])

    except Exception as e:
        print(f"\n❌ TEST FAILED: Unexpected error: {type(e).__name__}: {e}")
        return 2

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reproduce.py [buggy|fixed]", file=sys.stderr)
        sys.exit(2)
    version_arg = sys.argv[1]
    if version_arg not in ["buggy", "fixed"]:
        print(f"Invalid argument: '{version_arg}'. Please use 'buggy' or 'fixed'.", file=sys.stderr)
        sys.exit(2)
    exit_code = test_tools_strict_schema_bug(version_arg)
    exit(exit_code)