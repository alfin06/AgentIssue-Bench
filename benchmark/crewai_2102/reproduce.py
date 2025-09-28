import os
import sys
import io
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch, MagicMock

# --- Environment Setup ---
# This setup is crucial for triggering the bug correctly.
os.environ["CREWAI_TRACING_ENABLED"] = "false"
os.environ["AGENTOPS_API_KEY"] = "DUMMY_KEY" # Activates the buggy agentops integration

if not os.getenv("GOOGLE_API_KEY"):
    print("FATAL: GOOGLE_API_KEY environment variable not set.")
    sys.exit(1)
if not os.getenv("SERPER_API_KEY"):
    print("FATAL: SERPER_API_KEY environment variable not set.")
    sys.exit(1)

# --- Imports ---
from crewai import Agent, LLM, Task, Crew, Process
from crewai.tools.base_tool import BaseTool
from dotenv import load_dotenv
load_dotenv()

# --- Dummy Tool for Self-Contained Test ---
class DummyTool(BaseTool):
    name: str = "Dummy Search Tool"
    description: str = "A simple tool that does nothing."
    def _run(self) -> str:
        return "This is a dummy tool."

# --- Test Setup ---
print("--- Setting up an Agent with a Gemini LLM wrapper. ---")

my_llm = LLM(
    api_key=os.getenv("GOOGLE_API_KEY"),
    model="gemini/gemini-1.5-flash",
)
tool = DummyTool() 

test_agent = Agent(
    role="Test Agent",
    goal="Trigger the AttributeError during cleanup.",
    backstory="An agent designed to test a specific bug.",
    tools=[tool],
    llm=my_llm,
    verbose=True,
    allow_delegation=False,
    max_iter=1 
)

test_task = Task(
    description="Run a simple task to trigger the crew kickoff and subsequent cleanup.",
    expected_output="A successful run, which will then log an error during cleanup.",
    agent=test_agent
)

crew = Crew(
    agents=[test_agent],
    tasks=[test_task],
    process=Process.sequential,
)

# --- Verification Logic ---
print("\n--- Running crew.kickoff(). This is expected to LOG an AttributeError during cleanup. ---")

# Capture all console output to check for the logged error.
output_capture = io.StringIO()
with redirect_stdout(output_capture), redirect_stderr(output_capture):
    try:
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_message = MagicMock()
        mock_message.content = "This is the agent's mock final answer."
        mock_choice.message = mock_message
        mock_response.choices = [mock_choice]

        with patch('litellm.completion', return_value=mock_response):
            result = crew.kickoff(inputs={'topic': 'AI in automotive'})
    except Exception as e:
        print(f"\n--- Script crashed unexpectedly ---")
        print(f"ERROR: {type(e).__name__}: {e}")

# Get all the text that was printed to the console.
console_output = output_capture.getvalue()

print("\n--- Verifying the console output for the expected error log ---")

expected_error_text = "'NoneType' object has no attribute 'skip_auto_end_session'"

if expected_error_text in console_output:
    print(f"\nSUCCESS: The bug is reproduced.")
    print(f"The expected error message was found in the application's logs.")
    sys.exit(0)
else:
    print(f"\nFAILURE: The bug was NOT reproduced.")
    print(f"The expected error message was not found in the output.")
    print("\n--- Full Console Output ---")
    print(console_output)
    print("--------------------------")
    sys.exit(1)

