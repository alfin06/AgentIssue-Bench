import os
import sys

if len(sys.argv) < 2:
    print("FATAL: This script requires a version argument ('buggy' or 'fixed').")
    sys.exit(1)

VERSION_BEING_TESTED = sys.argv[1]
print(f"--- Reproduce Script: Testing version '{VERSION_BEING_TESTED}' ---")

from crewai import Agent, Task, Crew, Process
from crewai.knowledge.source.string_knowledge_source import StringKnowledgeSource

valid_llm_provider = "openai/gpt-4o-mini"

try:
    # Match the reporter's reproduction steps
    content = "Users name is John. He is 30 years old and lives in San Francisco."
    string_source = StringKnowledgeSource(content=content)
    
    agent = Agent(
        role="About User",
        goal="You know everything about the user.",
        backstory="You are a master at understanding people and their preferences.",
        verbose=True,
        allow_delegation=False,
        llm=valid_llm_provider,
    )
    task = Task(
        description="Answer the following questions about the user: {question}",
        expected_output="An answer to the question.",
        agent=agent,
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=True,
        process=Process.sequential,
        knowledge_sources=[string_source],
    )

    # This should trigger the bug in the buggy version
    result = crew.kickoff(inputs={"question": "What city does John live in and how old is he?"})

    # --- SUCCESS PATH (NO ERROR THROWN) ---
    if VERSION_BEING_TESTED == "buggy":
        sys.exit(1) 
    else:
        sys.exit(0)

except TypeError as e:
    expected_error_text = "missing 2 required keyword-only arguments: 'response' and 'body'"
    if expected_error_text in str(e):
        if VERSION_BEING_TESTED == "buggy":
            sys.exit(0) 
        else:
            sys.exit(1)
    else:
        print(f"UNEXPECTED ERROR: Caught an unexpected TypeError: {e}")
        sys.exit(1)

except Exception as e:
    print(f"UNEXPECTED ERROR: Caught a different exception: {type(e).__name__}: {e}")
    sys.exit(1)