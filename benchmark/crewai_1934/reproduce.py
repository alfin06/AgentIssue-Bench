import os
import logging
import litellm
import concurrent.futures
from crewai import Agent, Crew, Task
from io import StringIO

# Disable LiteLLM logs
logging.getLogger("litellm").setLevel(logging.CRITICAL)
logging.getLogger("litellm").propagate = False

# Step 1: Disable retries through both ENV and Python
os.environ["OPENAI_API_KEY"] = ""  # Force auth failure
os.environ["LITELLM_NUM_RETRIES"] = "0"
litellm.num_retries = 0

# Step 2: Capture logging output to detect loop
log_capture_string = StringIO()
logging.basicConfig(stream=log_capture_string, level=logging.ERROR)

# Step 3: Create a minimal agent + task
agent = Agent(
    role="City Selection Expert",
    goal="Select the best city based on weather, season, and prices",
    backstory="An expert in analyzing travel data to pick ideal destinations",
    tools=[],
    llm="gpt-4",  # Forces LLM usage triggering LiteLLM
)

task = Task(
    description="Analyze and select the best city for the trip",
    agent=agent,
    expected_output="Detailed report on the chosen city",
)

def run_crew():
    crew = Crew(agents=[agent], tasks=[task])
    return crew.kickoff()

def check_logs_for_loop():
    logs = log_capture_string.getvalue()
    if "LiteLLM call failed" in logs:
        raise RuntimeError("LiteLLM failure loop detected — aborting.")

try:
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(run_crew)
        for _ in range(10):  # Check log output for 10 seconds max
            try:
                result = future.result(timeout=1)
                print("✅ Crew result:", result)
                break
            except concurrent.futures.TimeoutError:
                check_logs_for_loop()
except RuntimeError as e:
    print(f"\n❌ Caught log-based error: {e}")
except Exception as e:
    print(f"\n❌ Other exception: {e}")
