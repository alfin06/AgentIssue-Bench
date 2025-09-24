import os
from unittest.mock import patch, MagicMock

from haystack.components.agents import Agent
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.dataclasses import ChatMessage, ToolCall, ToolCallResult
from haystack.tools import ComponentTool, tool

# --- Setup ---
os.environ["OPENAI_API_KEY"] = input("Please enter an OpenAI API key: ")

@tool
def add(a: int, b: int) -> int:
    """Adds two integers."""
    return a + b

@tool
def subtract(a: int, b: int) -> int:
    """Subtracts two integers."""
    return a - b

main_llm = OpenAIChatGenerator()
math_llm = OpenAIChatGenerator()

math_agent = Agent(
    chat_generator=math_llm,
    system_prompt="You are a math agent.",
    tools=[add, subtract]
)

math_agent_tool = ComponentTool(
    component=math_agent,
    description="Use this tool to make math calculations",
    name="math_agent"
)

main_agent = Agent(
    chat_generator=main_llm,
    tools=[math_agent_tool]
)

# --- Verification Logic ---
print("--- Running main_agent with a math question. ---")

with patch.object(main_llm, 'run', return_value={"replies": [ChatMessage.from_assistant(tool_calls=[ToolCall(tool_name="math_agent", arguments={"messages": "What is 2+2?"})])]}):
    with patch.object(math_llm, 'run', return_value={"replies": [ChatMessage.from_assistant(tool_calls=[ToolCall(tool_name="add", arguments={"a": 2, "b": 2})])]}):
        result = main_agent.run(messages=[ChatMessage.from_user("What is 2+2?")])

print("\n--- Verifying the result for the specific error message ---")
error_found = False
expected_error_text = "can only concatenate list (not \"str\") to list"

if "messages" in result:
    for message in result["messages"]:
        if isinstance(message, ChatMessage) and message.is_from(role="tool"):
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
