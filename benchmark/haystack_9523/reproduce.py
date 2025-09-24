import os
from unittest.mock import patch, MagicMock

from haystack.components.agents import Agent
from haystack.dataclasses import ChatMessage
from haystack.components.generators.chat import OpenAIChatGenerator
from haystack import Pipeline
from haystack.tools import ComponentTool
from haystack.components.websearch import SerperDevWebSearch

# --- Setup ---
os.environ["OPENAI_API_KEY"] = input("Please enter an OpenAI API key: ")
os.environ["SERPERDEV_API_KEY"] = input("Please enter a SerperDev API key: ")

def mock_print_streaming_chunk(chunk):
    pass

class MockChatGenerator:
    """A mock chat generator that satisfies the Agent's validation."""
    def run(self, messages, tools=None, **kwargs):
        """This method's signature includes the 'tools' parameter."""
        return {"replies": [ChatMessage.from_assistant("Mocked final answer.")]}

def doc_to_string(documents) -> str:
    """Handles the tool output before conversion to ChatMessage."""
    return "documents processed"

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

mock_chat_generator = MockChatGenerator()

research_agent = Agent(
    chat_generator=mock_chat_generator,
    system_prompt="You are a research agent.",
    tools=[web_search, wiki_search],
    streaming_callback=mock_print_streaming_chunk,
)

# --- Verification Logic ---
print("--- Setting up pipeline with the agent and tools ---")
pipeline = Pipeline()
pipeline.add_component("research_agent", research_agent)

print("--- Serializing the pipeline using .dumps() ---")
pipeline_dumps = pipeline.dumps()
print("Pipeline serialized successfully.")

print("\n--- Attempting to deserialize the pipeline using .loads() ---")
print("--- This is the step that is expected to fail. ---")

try:
    load_pipeline = Pipeline.loads(pipeline_dumps)
    print("\n--- SCRIPT FINISHED UNEXPECTEDLY ---")
    print("FAILURE: The bug was NOT reproduced. The pipeline was loaded successfully.")
    exit(0)

except Exception as e:
    print(f"\nSUCCESS: The script failed with an error as expected.")
    print(f"Error Type: {type(e).__name__}")
    print(f"Error Message: {e}")

    if type(e).__name__ == "DeserializationError":
        print("\nVerification successful: A DeserializationError was caught, which confirms the bug.")
        exit(1)
    else:
        print("\nVerification failed: The error caught was not the expected DeserializationError.")
        exit(0)
