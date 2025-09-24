import os
from unittest.mock import patch

from haystack import Pipeline
from haystack.components.agents import Agent
from haystack.components.joiners import ListJoiner
from haystack.dataclasses import ChatMessage
from typing import List

from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.components.websearch import SerperDevWebSearch
from haystack.tools import ComponentTool

# --- Setup ---
os.environ["OPENAI_API_KEY"] = input("Please enter an OpenAI API key: ")
os.environ["SERPERDEV_API_KEY"] = input("Please enter a SerperDev API key: ")


# --- Verification Logic ---
print("--- Attempting to connect to the 'agent.messages' output socket. ---")
print("--- This is expected to fail with a PipelineConnectError. ---")

try:
    chat_generator = OpenAIChatGenerator()
    web_search_component = SerperDevWebSearch()

    search_tool = ComponentTool(component=web_search_component)
    agent = Agent(chat_generator=chat_generator, tools=[search_tool])

    pipeline = Pipeline()
    pipeline.add_component("agent", agent)
    pipeline.add_component("joiner", ListJoiner(List[ChatMessage]))

    pipeline.connect("agent.messages", "joiner.values")

    print("\n--- SCRIPT FINISHED ---")
    print("FAILURE: The bug was NOT reproduced. The connection was made successfully.")
    exit(0)

except Exception as e:
    print(f"\nSUCCESS: The script failed with an error as expected.")
    print(f"Error Type: {type(e).__name__}")
    print(f"Error Message: {e}")

    expected_error_text = "agent.messages does not exist"
    if "PipelineConnectError" in type(e).__name__ and expected_error_text in str(e):
        print("\nVerification successful: The error message matches the bug report.")
        exit(1)
    else:
        print("\nVerification failed: The error did not match the expected bug.")
        exit(0)
