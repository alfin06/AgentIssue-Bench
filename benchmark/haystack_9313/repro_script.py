import os
from unittest.mock import patch, MagicMock

from haystack.components.agents import Agent
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.dataclasses import ChatMessage, ToolCall, ToolCallResult
from haystack.tools import ComponentTool, tool

# --- Mocking and Setup ---
# 1. Set a dummy API key to satisfy component initializations
#os.environ["OPENAI_API_KEY"] = "DUMMY_KEY"

# 2. Define simple mock tools for the inner 'math_agent'
@tool
def add(a: int, b: int) -> int:
    """Adds two integers."""
    return a + b

@tool
def subtract(a: int, b: int) -> int:
    """Subtracts two integers."""
    return a - b

# 3. Instantiate real OpenAIChatGenerator components.
#    This ensures they have all the necessary internal Haystack attributes.
#    We will patch their 'run' method later to control their output.
main_llm = OpenAIChatGenerator()
math_llm = OpenAIChatGenerator()

# --- Agent and Tool Definition from Bug Report ---

# 1. Create the inner agent that will be used as a tool.
math_agent = Agent(
    chat_generator=math_llm,
    system_prompt="You are a math agent.",
    tools=[add, subtract]
)

# 2. Wrap the 'math_agent' in a ComponentTool.
math_agent_tool = ComponentTool(
    component=math_agent,
    description="Use this tool to make math calculations",
    name="math_agent"
)

# 3. Create the main agent that uses the 'math_agent_tool'.
#    The agent will loop until the LLM stops producing tool calls, which is fine for this test.
main_agent = Agent(
    chat_generator=main_llm,
    tools=[math_agent_tool]
)

# --- Verification Logic ---
print("--- Running main_agent with a math question. ---")
print("--- This is expected to trigger an internal error and loop. ---")

# Use patching to mock the `run` methods of the real LLM components.
with patch.object(main_llm, 'run', return_value={"replies": [ChatMessage.from_assistant(tool_calls=[ToolCall(tool_name="math_agent", arguments={"messages": "What is 2+2?"})])]}):
    with patch.object(math_llm, 'run', return_value={"replies": [ChatMessage.from_assistant(tool_calls=[ToolCall(tool_name="add", arguments={"a": 2, "b": 2})])]}):
        # This call will now run until the agent loop finishes or times out.
        result = main_agent.run(messages=[ChatMessage.from_user("What is 2+2?")])

# --- CORRECTED VERIFICATION ---
# Instead of a try/except, we inspect the output for the specific error message.
# The bug is that the ComponentTool passes a string to the sub-agent, causing a
# TypeError that the agent catches and reports in a ToolCallResult.

print("\n--- Verifying the result for the specific error message ---")
error_found = False
expected_error_text = "can only concatenate list (not \"str\") to list"

# The result is a dictionary containing the list of messages from the conversation.
if "messages" in result:
    for message in result["messages"]:
        # We are looking for a message from the TOOL role
        if isinstance(message, ChatMessage) and message.is_from(role="tool"):
            # The content of a tool message is a list of ToolCallResult objects.
            # In this version of Haystack, it's stored in the internal _content attribute.
            for tool_result in message._content:
                if isinstance(tool_result, ToolCallResult) and expected_error_text in tool_result.result:
                    error_found = True
                    break
        if error_found:
            break

if error_found:
    print(f"\nSUCCESS: The bug is reproduced.")
    print(f"The ToolCallResult contained the expected error: '{expected_error_text}'")
    exit(1)
else:
    print("\nFAILURE: The bug was NOT reproduced.")
    print("The expected error message was not found in the agent's output.")
    exit(0)
