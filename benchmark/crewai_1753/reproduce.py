import os
from enum import Enum
from pydantic import BaseModel
from crewai import Agent, Task, Crew, Process
from dotenv import load_dotenv

load_dotenv()
os.environ["OTEL_SDK_DISABLED"] = "true"

# Step 1: Define Enum and Pydantic model
class CrewStatus(Enum):
    TODO = "To Do"
    SUCCESSFUL = "Successful"
    FAILED = "Failed"

class CrewStatusModel(BaseModel):
    status: CrewStatus

# Step 2: Create a minimal task-crew setup
def create_crew():
    agent = Agent(
        role="Minimal Agent",
        goal="Return a status",
        verbose=True,
        memory=True,
        backstory="Test enum serialization issue"
    )

    task = Task(
        description="Return a crew status value",
        expected_output="The output should be one of the CrewStatus enum values",
        agent=agent,
        output_pydantic=CrewStatusModel,
        memory=True,
    )

    crew = Crew(
        agents=[agent],
        tasks=[task],
        process=Process.sequential,
    )

    return crew

if __name__ == "__main__":
    crew = create_crew()
    try:
        result = crew.kickoff()
        print("Crew result:", result)
    except TypeError as e:
        if "is not JSON serializable" in str(e):
            print("❌ BUG REPRODUCED: Enum is not JSON serializable.")
        else:
            print("❌ TypeError occurred:", e)
    except Exception as e:
        print("❌ Unexpected error occurred:", e)
