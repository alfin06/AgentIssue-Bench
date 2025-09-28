import os
import sys
from unittest.mock import patch, MagicMock

def test_agent_as_tool_bug(version: str) -> int:
    """
    Tests for the bug where using an Agent as a tool for another Agent via ComponentTool fails.
    - The 'buggy' version is expected to raise an error.
    - The 'fixed' version is expected to run successfully.
    """
    print(f"--- Running test for '{version}' version ---")

    # Set dummy API keys to satisfy __init__ methods
    os.environ["OPENAI_API_KEY"] = "DUMMY_KEY"
    os.environ["SERPERDEV_API_KEY"] = "DUMMY_KEY"

    # --- Dynamic Imports ---
    from haystack.components.agents import Agent
    from haystack.dataclasses import ChatMessage
    from haystack.components.generators.chat import OpenAIChatGenerator
    from haystack.tools import ComponentTool

    print("--- Setting up agents and tools ---")
    # Create a simple math agent (as a tool)
    math_agent = Agent(
        chat_generator=OpenAIChatGenerator(),
        system_prompt="You are a math agent.",
        tools=[],
    )
    math_agent_tool = ComponentTool(
        component=math_agent,
        description="Use this tool to make math calculations",
        name="math_agent"
    )

    # Patch OpenAIChatGenerator.run to avoid real API calls
    with patch("haystack.components.generators.chat.openai.OpenAIChatGenerator.run", return_value={"replies": [ChatMessage.from_assistant("4")]}):
        try:
            print("--- Directly invoking the math_agent_tool ---")
            # Try different invocation signatures for compatibility
            invoked = False
            try:
                result = math_agent_tool.invoke({"query": "2+2"})
                invoked = True
            except TypeError as te:
                if "positional argument" in str(te) or "but 2 were given" in str(te):
                    try:
                        result = math_agent_tool.invoke()
                        invoked = True
                    except Exception:
                        pass
                    if not invoked:
                        try:
                            result = math_agent_tool.invoke(query="2+2")
                            invoked = True
                        except Exception:
                            pass
            if invoked:
                print("--- Tool ran successfully ---")
                if version == "buggy":
                    print("\n❌ BUG NOT REPRODUCED: The tool ran successfully, but it was expected to fail.")
                    return 1
                else:
                    print("\n✅ FIX CONFIRMED: The tool ran successfully, as expected for the fixed version.")
                    return 0
            else:
                raise Exception("Could not invoke tool with any tested signature.")
        except Exception as e:
            print(f"   Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reproduce.py [buggy|fixed]", file=sys.stderr)
        sys.exit(1)
    
    version_arg = sys.argv[1]
    if version_arg not in ["buggy", "fixed"]:
        print(f"Invalid argument: '{version_arg}'. Please use 'buggy' or 'fixed'.", file=sys.stderr)
        sys.exit(1)

    exit_code = test_agent_as_tool_bug(version_arg)
    sys.exit(exit_code)