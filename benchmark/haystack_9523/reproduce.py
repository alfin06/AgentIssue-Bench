import os
import sys
from unittest.mock import patch, MagicMock
from test_helpers import doc_to_string, MockChatGenerator


def test_deserialization_bug(version: str) -> int:
    """
    Tests for a DeserializationError when loading a Pipeline with an Agent.
    - The 'buggy' version is expected to raise a DeserializationError.
    - The 'fixed' version is expected to load successfully.
    """
    print(f"--- Running test for '{version}' version ---")

    # --- Dynamic Imports ---
    from haystack.components.agents import Agent
    from haystack.dataclasses import ChatMessage
    from haystack.components.generators.chat import OpenAIChatGenerator
    from haystack import Pipeline
    from haystack.tools import ComponentTool
    from haystack.components.websearch import SerperDevWebSearch

    # --- Common Setup for both versions ---
    print("--- Setting up pipeline with the agent and tools ---")
    with patch("haystack.components.websearch.SerperDevWebSearch", new=MagicMock()):
        web_search = ComponentTool(
            component=SerperDevWebSearch(),
            name="web_search",
            description="Search the web",
            outputs_to_string={"source": "documents", "handler": doc_to_string},
        )
        wiki_search = ComponentTool(
            component=SerperDevWebSearch(),
            name="wiki_search",
            description="Search Wikipedia",
            outputs_to_string={"source": "documents", "handler": doc_to_string},
        )

    research_agent = Agent(
        chat_generator=MockChatGenerator(),
        system_prompt="You are a research agent.",
        tools=[web_search, wiki_search],
    )

    pipeline = Pipeline()
    pipeline.add_component("research_agent", research_agent)

    print("--- Serializing the pipeline using .dumps() ---")
    pipeline_dumps = pipeline.dumps()
    print("Pipeline serialized successfully.")

    # --- Version-Specific Verification ---
    try:
        print("\n--- Attempting to deserialize the pipeline using .loads() ---")
        Pipeline.loads(pipeline_dumps)
        
        # --- Analysis for when NO error is raised ---
        if version == "buggy":
            print("\n❌ BUG NOT REPRODUCED: Pipeline loaded successfully, but it was expected to fail.")
            return 1
        else: # version == "fixed"
            print("\n✅ FIX CONFIRMED: Pipeline loaded successfully, as expected for the fixed version.")
            return 0

    except Exception as e:
        # --- Analysis for when a DeserializationError IS raised ---
        if version == "buggy":
            print(f"   Error: {e}")
            print(f"\n✅ BUG REPRODUCED: Caught the expected DeserializationError, which confirms the bug.")
            return 0
        else: # version == "fixed"
            print(f"   Error: {e}")
            print(f"\n❌ FIX NOT CONFIRMED: A DeserializationError was raised unexpectedly in the fixed version.")
            return 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reproduce.py [buggy|fixed]", file=sys.stderr)
        sys.exit(1)
    
    version_arg = sys.argv[1]
    if version_arg not in ["buggy", "fixed"]:
        print(f"Invalid argument: '{version_arg}'. Please use 'buggy' or 'fixed'.", file=sys.stderr)
        sys.exit(1)

    # The exit code determines the success (0) or failure (1) of the test run.
    exit_code = test_deserialization_bug(version_arg)
    sys.exit(exit_code)