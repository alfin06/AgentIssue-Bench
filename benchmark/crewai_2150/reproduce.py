import os
import sys
from unittest.mock import patch, MagicMock

# --- Test Configuration ---
if len(sys.argv) < 2:
    print("FATAL: This script requires a version argument ('buggy' or 'fixed').")
    sys.exit(1)

VERSION_BEING_TESTED = sys.argv[1]
print(f"--- Reproduce Script: Testing version '{VERSION_BEING_TESTED}' ---")


# --- Imports ---
from crewai import Agent, Task, Crew, Process, LLM
from crewai.knowledge.source.string_knowledge_source import StringKnowledgeSource


# --- Test Setup ---
mock_llm = MagicMock(spec=LLM)
# --- DEFINITIVE FIX ---
# The crewAI framework expects a simple string as the final output.
# Providing a complex MagicMock object was causing a TypeError.
mock_llm.return_value = "This is the agent's final mock output."
mock_llm.stop = MagicMock()

class FakeLLM:
    def __init__(self, *args, **kwargs):
        pass

    # Called by different code paths; return a plain string result
    def __call__(self, *args, **kwargs):
        return "This is the agent's final mock output."

    # Some integrations call generate / invoke
    def generate(self, *args, **kwargs):
        return "This is the agent's final mock output."

    def invoke(self, *args, **kwargs):
        return "This is the agent's final mock output."

    def stop(self, *args, **kwargs):
        return None

fake_llm = FakeLLM()
 

patch_target = "crewai.knowledge.storage.knowledge_storage.KnowledgeStorage.save"
mock_storage_save = MagicMock(side_effect=Exception("Simulated database failure."))

# --- Main Test Logic ---
try:
    with patch(patch_target, new=mock_storage_save):
        string_source = StringKnowledgeSource(content="Test content")
        
        agent = Agent(
            role="Test Agent",
            goal="Trigger the APIStatusError",
            backstory="An agent for testing.",
            verbose=False,
            llm=mock_llm,
        )
        task = Task(
            description="A simple task.",
            expected_output="An error.",
            agent=agent,
        )

        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            knowledge_sources=[string_source],
        )

        # The bug is triggered during kickoff, which calls the save method.
        crew.kickoff()


    # --- SUCCESS PATH (NO ERROR THROWN) ---
    # If we get here, the bug did NOT manifest.
    if VERSION_BEING_TESTED == "buggy":
        print("BUG NOT REPRODUCED: The Crew kickoff completed without error.")
        sys.exit(0) 
    else:
        print("FIX CONFIRMED: The Crew kickoff completed without error.")
        sys.exit(0)

except TypeError as e:
    # --- BUG FOUND PATH (TypeError Thrown) ---
    expected_error_text = "missing 2 required keyword-only arguments: 'response' and 'body'"
    if expected_error_text in str(e):
        if VERSION_BEING_TESTED == "buggy":
            print(f"BUG REPRODUCED: Caught expected TypeError: {e}")
            sys.exit(1) 
        else:
            print(f"FIX FAILED: The bug is still present. Caught unexpected TypeError: {e}")
            sys.exit(1)
    else:
        print(f"UNEXPECTED ERROR: Caught an unexpected TypeError: {e}")
        sys.exit(1)

except Exception as e:
    # --- UNEXPECTED ERROR PATH ---
    print(f"UNEXPECTED ERROR: Caught a different exception: {type(e).__name__}: {e}")
    sys.exit(1)

