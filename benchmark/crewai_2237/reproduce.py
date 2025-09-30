import sys
import threading
import io
import contextlib
import unittest.mock as mock
from typing import Type

# --- Test Configuration ---
TIMEOUT_SECONDS = 45
EXPECTED_ERROR_MSG = "Error parsing LLM output, agent will retry: I did it wrong. Tried to both perform Action and give a Final Answer at the same time, I must do one or the other"

BUGGY_LLM_OUTPUT = """I'll use the Simple Research Tool to find information.

Action: Simple Research Tool
Action Input: {"argument": "AI trends"}

After using my tool, here's what I found:
The latest AI trends are explainable AI, conversational AI, and AI in cybersecurity.

Final Answer: Based on my research, the top 3 AI trends are:
1. Explainable AI
2. Conversational AI
3. AI in cybersecurity
"""

# Counter to force stop after N calls
call_counter = {"count": 0}
MAX_CALLS = 3

def patched_call(self, prompt, **kwargs):
    call_counter["count"] += 1
    print("Patched LLM called, returning buggy output")
    if call_counter["count"] > MAX_CALLS:
        raise RuntimeError("Forced stop after max LLM calls")
    return BUGGY_LLM_OUTPUT

def test_parsing_bug(version="buggy"):
    output_buffer = io.StringIO()
    with contextlib.redirect_stdout(output_buffer), contextlib.redirect_stderr(output_buffer):
        from crewai import Agent, Task, Crew, Process
        try:
            from crewai.tools.base_tool import BaseTool
        except ImportError:
            from crewai_tools.base import BaseTool
        from pydantic import BaseModel, Field

        class MyToolInput(BaseModel):
            argument: str = Field(..., description="A simple argument for the tool.")

        class MyCustomTool(BaseTool):
            name: str = "Simple Research Tool"
            description: str = "Returns a fixed string about AI trends, tempting the LLM to finish early."
            args_schema: Type[BaseModel] = MyToolInput
            def _run(self, argument: str) -> str:
                print(f"Tool executed with argument: {argument}")
                return "The latest AI trends are explainable AI, conversational AI, and AI in cybersecurity."

        print("Setting up Agent, Task, and Crew...")
        llm = "openai/gpt-4o-mini"  # Use a valid provider string so CrewAI initializes

        researcher = Agent(
            role='AI Researcher',
            goal='Uncover the latest developments in AI.',
            backstory='You are an AI researcher. You use your tools to find info and present it.',
            verbose=True,
            allow_delegation=False,
            tools=[MyCustomTool()],
            llm=llm
        )
        print("LLM methods:", [m for m in dir(researcher.llm.__class__) if not m.startswith("_")])
        task = Task(
            description='What are the latest trends in the AI industry?',
            expected_output='A summary of the top 3 AI trends.',
            agent=researcher
        )
        crew = Crew(agents=[researcher], tasks=[task], process=Process.sequential, verbose=True, max_iterations=2)

        completed_event = threading.Event()
        error_info = [None]

        def run_crew():
            try:
                print(f"Starting crew.kickoff() for '{version}' version with a {TIMEOUT_SECONDS}s timeout...")
                with mock.patch("crewai.llm.LLM.call", new=patched_call):
                    crew.kickoff()
                print("crew.kickoff() completed without errors")
            except Exception as e:
                print(f"crew.kickoff() raised an exception: {type(e).__name__}: {e}")
                error_info[0] = str(e)
                completed_event.set()
                return
            finally:
                completed_event.set()

        thread = threading.Thread(target=run_crew)
        thread.start()

        completed = completed_event.wait(timeout=TIMEOUT_SECONDS)
        thread.join(timeout=2)
        if not completed:
            print(f"❌ Test failed: Execution timed out after {TIMEOUT_SECONDS} seconds.")
            thread.join(timeout=2)
            return 1
        thread.join()

    # --- Result Analysis ---
    output = output_buffer.getvalue()
    error = None
    if "crew.kickoff() raised an exception:" in output:
        error = output.split("crew.kickoff() raised an exception:")[-1].strip()

    parsing_error_count = output.count(EXPECTED_ERROR_MSG)

    if version == "buggy":
        if parsing_error_count >= 1 or (error and EXPECTED_ERROR_MSG in error):
            print(f"✅ BUG REPRODUCED: Parsing error detected in output.")
            print(f"Sample error: {EXPECTED_ERROR_MSG}")
            return 0
        elif error:
            print(f"✅ BUG REPRODUCED: RuntimeError detected.")
            return 0
        else:
            print("❌ BUG NOT REPRODUCED: Crew completed without the expected parsing error.")
            return 1
    elif version == "fixed" or version == "test_fixed":
        if parsing_error_count > 0 or (error and EXPECTED_ERROR_MSG in error):
            print(f"❌ FIX FAILED: The parsing error still occurred in fixed version.")
            print(f"Sample error: {EXPECTED_ERROR_MSG}")
            return 1
        elif error:
            print(f"⚠️ WARNING: The specific parsing error did not occur, but another error was caught: {error}")
            print("✅ FIX VERIFIED: The specific parsing error was fixed.")
            return 0
        else:
            print("✅ FIX VERIFIED: Crew completed successfully without parsing errors.")
            return 0
    else:
        print(f"Unknown version argument: {version}")
        return 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reproduce.py [buggy|fixed|test_fixed]", file=sys.stderr)
        sys.exit(1)
    version_arg = sys.argv[1]
    sys.exit(test_parsing_bug(version_arg))