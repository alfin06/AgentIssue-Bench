import os
from unittest.mock import patch

from haystack import Pipeline
from haystack.components.agents import Agent
from haystack.components.joiners import ListJoiner
from haystack.dataclasses import ChatMessage
from typing import List

# Import the actual components we will instantiate
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack.components.websearch import SerperDevWebSearch
from haystack.tools import ComponentTool

# --- Setup ---
# 1. Set dummy API keys to satisfy the __init__ methods of the real components.
#    No network calls will be made, but the components expect these to be present.
os.environ["OPENAI_API_KEY"] = "DUMMY_KEY"
os.environ["SERPERDEV_API_KEY"] = "DUMMY_KEY"


# --- Verification Logic ---
# The try/except block is placed around the code that defines the pipeline,
# as the bug occurs during the pipeline.connect() call.
print("--- Attempting to connect to the 'agent.messages' output socket. ---")
print("--- This is expected to fail with a PipelineConnectError. ---")

try:
    # 1. Instantiate the REAL components. This is the key change. By creating
    #    real instances, they will pass all of Haystack's internal validation
    #    checks (like having a __haystack_input__ attribute) when they are
    #    passed to the Agent constructor.
    chat_generator = OpenAIChatGenerator()
    web_search_component = SerperDevWebSearch()

    # 2. Proceed with the setup from the user's report using the real components.
    #    The Agent will now initialize successfully because it receives a valid generator.
    search_tool = ComponentTool(component=web_search_component)
    agent = Agent(chat_generator=chat_generator, tools=[search_tool])

    pipeline = Pipeline()
    pipeline.add_component("agent", agent)
    pipeline.add_component("joiner", ListJoiner(List[ChatMessage]))

    # 3. This is the exact line that triggers the bug in the faulty version.
    #    The Agent class in this version does not have a 'messages' output socket,
    #    so trying to connect to it will raise a PipelineConnectError.
    pipeline.connect("agent.messages", "joiner.values")

    # If this line is reached, the bug was not reproduced.
    print("\n--- SCRIPT FINISHED UNEXPECTEDLY ---")
    print("FAILURE: The bug was NOT reproduced. The connection was made successfully.")
    exit(0)

except Exception as e:
    print(f"\nSUCCESS: The script failed with an error as expected.")
    print(f"Error Type: {type(e).__name__}")
    print(f"Error Message: {e}")

    # Verify that the error is the specific PipelineConnectError we expect.
    expected_error_text = "agent.messages does not exist"
    if "PipelineConnectError" in type(e).__name__ and expected_error_text in str(e):
        print("\nVerification successful: The error message matches the bug report.")
        # Exit with 1 to signal to the test runner that the bug was found.
        exit(1)
    else:
        print("\nVerification failed: The error did not match the expected bug.")
        exit(0)
