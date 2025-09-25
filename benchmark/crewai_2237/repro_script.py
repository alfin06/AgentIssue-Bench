import os
import sys
from crewai import Agent, Task, Crew, Process
from crewai.tools.base_tool import BaseTool
from pydantic import BaseModel, Field
from typing import Type

# --- Setup: Mock dependencies to make the script self-contained ---
os.environ["OPENAI_API_KEY"] = os.environ.get("OPENAI_API_KEY", "dummy_key")

# --- Mock LLM to force the error ---
class MockLLM:
    def __init__(self):
        self.call_count = 0
    def invoke(self, *args, **kwargs):
        self.call_count += 1
        if self.call_count == 1:
            return "Thought: I should use my custom tool.\nAction: Name of my tool\nAction Input: {'argument': 'test'}"
        else:
            return "Thought: Now I have the result.\nFinal Answer: The result is tool.\nAction: Name of my tool\nAction Input: {'argument': 'this should not happen'}"
    def __call__(self, *args, **kwargs):
        return self.invoke(args, kwargs)

# --- Tool Definition ---
class MyToolInput(BaseModel):
    argument: str = Field(..., description="Description of the argument.")
class MyCustomTool(BaseTool):
    name: str = "Name of my tool"
    description: str = "What this tool does."
    args_schema: Type[BaseModel] = MyToolInput
    def _run(self, argument: str) -> str:
        return "tool"

# --- Agent and Crew Setup ---
my_tool = MyCustomTool()
mock_llm = MockLLM()
tool_agent = Agent(role='Tool User', goal='Use the custom tool', backstory='I use tools.', llm=mock_llm, tools=[my_tool], verbose=True)
tool_task = Task(description='Use your tool.', expected_output='The word "tool".', agent=tool_agent)
crew = Crew(agents=[tool_agent], tasks=[tool_task], process=Process.sequential, verbose=True)

# --- Execute and Verify the Bug ---
print("\n--- Kicking off crew. This is expected to trigger the parsing error. ---", flush=True)

try:
    result = crew.kickoff()
    print("\n\n--- SCRIPT FINISHED UNEXPECTEDLY ---", flush=True)
    print("FAILURE: Bug NOT reproduced.", flush=True)
    exit(0)
except Exception as e:
    print("\n\n----------------- SCRIPT CAUGHT AN ERROR -----------------", flush=True)

    # --- FINAL: ISOLATED INSPECTION ---
    # We will print each piece of the error separately to find the broken part.
    print("Inspecting the exception object piece by piece...", flush=True)
    
    # 1. Inspect the type
    error_type_str = ""
    try:
        error_type_str = str(type(e).__name__)
        print("Error Type:", error_type_str, flush=True)
    except:
        print("Could not get error type.", flush=True)

    # 2. Inspect the 'repr'
    error_repr_str = ""
    try:
        error_repr_str = repr(e)
        print("Error Repr:", error_repr_str, flush=True)
    except:
        print("Could not get error repr.", flush=True)
    
    # 3. Inspect the arguments
    error_args_str = ""
    try:
        error_args_str = str(e.args)
        print("Error Args:", error_args_str, flush=True)
    except:
        print("Could not get error args.", flush=True)

    # --- ROBUST VERIFICATION ---
    full_error_details = f"{error_type_str} {error_repr_str} {error_args_str}"
    expected_error_text = "Tried to both perform Action and give a Final Answer"
    
    if expected_error_text in full_error_details:
        print("\nVerification successful: The bug was reproduced.", flush=True)
        exit(1)
    else:
        print(f"\nVerification failed: The error details did not contain the expected bug text ('{expected_error_text}').", flush=True)
        exit(0)