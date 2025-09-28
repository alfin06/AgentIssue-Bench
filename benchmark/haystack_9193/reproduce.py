import os
import sys
from unittest.mock import patch, MagicMock

def test_agent_messages_output_bug(version: str) -> int:
    """
    Tests for the bug where the Agent component does not have a 'messages' output.
    - The 'buggy' version is expected to raise a PipelineConnectError.
    - The 'fixed' version is expected to connect successfully.
    """
    print(f"--- Running test for '{version}' version ---")

    # Set dummy API keys to satisfy __init__ methods
    os.environ["OPENAI_API_KEY"] = "DUMMY_KEY"
    os.environ["SERPERDEV_API_KEY"] = "DUMMY_KEY"

    # --- Dynamic Imports ---
    from haystack import Pipeline
    from haystack.components.agents import Agent
    from haystack.components.joiners import ListJoiner
    from haystack.dataclasses import ChatMessage
    from typing import List
    from haystack.components.generators.chat import OpenAIChatGenerator
    from haystack.components.websearch import SerperDevWebSearch
    from haystack.tools import ComponentTool

    print("--- Setting up pipeline with Agent and attempting to connect 'messages' output ---")
    try:
        chat_generator = OpenAIChatGenerator()
        web_search_component = SerperDevWebSearch()
        search_tool = ComponentTool(component=web_search_component)
        agent = Agent(chat_generator=chat_generator, tools=[search_tool])

        pipeline = Pipeline()
        pipeline.add_component("agent", agent)
        pipeline.add_component("joiner", ListJoiner(List[ChatMessage]))

        # This should fail in the buggy version
        pipeline.connect("agent.messages", "joiner.values")

        if version == "buggy":
            print("\n❌ BUG NOT REPRODUCED: The connection was made successfully, but it was expected to fail.")
            return 1
        else:
            print("\n✅ FIX CONFIRMED: The connection was made successfully.")
    except Exception as e:
        print(f"   Error: {e}")
        # Check for the expected error message/type
        expected_error_text = "agent.messages does not exist"
        if version == "buggy" and "PipelineConnectError" in type(e).__name__ and expected_error_text in str(e):
            print("\n✅ BUG REPRODUCED: Caught the expected PipelineConnectError, which confirms the bug.")
            return 0
        elif version == "fixed":
            print("\n❌ FIX NOT CONFIRMED: An error was raised unexpectedly in the fixed version.")
            return 1
        else:
            print("\n❌ BUG NOT REPRODUCED: The error did not match the expected bug.")
            return 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reproduce.py [buggy|fixed]", file=sys.stderr)
        sys.exit(1)
    
    version_arg = sys.argv[1]
    if version_arg not in ["buggy", "fixed"]:
        print(f"Invalid argument: '{version_arg}'. Please use 'buggy' or 'fixed'.", file=sys.stderr)
        sys.exit(1)

    exit_code = test_agent_messages_output_bug(version_arg)
    sys.exit(exit_code)