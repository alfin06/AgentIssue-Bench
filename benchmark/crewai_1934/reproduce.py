import os
import sys
import time
import signal
import threading
import traceback

def test_crew_hang(version="buggy"):
    """Test if crew.kickoff() hangs when LLM call fails"""
    
    # Set a fake OpenAI API key to force authentication error
    os.environ["OPENAI_API_KEY"] = "sk-fake"
    
    # Import after setting env vars
    from crewai import Agent, Crew, Task
    
    print("Creating Agent and Task...")
    simple_agent = Agent(
        role="City Selection Expert",
        goal="Select the best city based on weather, season, and prices",
        backstory="An expert in analyzing travel data to pick ideal destinations",
        tools=[],
        llm="gpt-4",
    )

    task = Task(
        description="Analyze and select the best city for the trip",
        agent=simple_agent,
        expected_output="Detailed report on the chosen city",
    )

    crew = Crew(agents=[simple_agent], tasks=[task])
    
    # Use a flag to track if the function completes
    completed = threading.Event()
    error_message = [None]
    
    def run_kickoff():
        try:
            print("Starting crew.kickoff()...")
            crew.kickoff()
            print("Crew.kickoff() completed!")
            completed.set()
        except Exception as e:
            print(f"Caught exception: {e}")
            error_message[0] = str(e)
            completed.set()
            
    # Start the kickoff in a separate thread
    thread = threading.Thread(target=run_kickoff)
    thread.daemon = True
    thread.start()
    
    # Wait for the thread to complete or timeout
    timeout_seconds = 20
    print(f"Waiting for up to {timeout_seconds} seconds...")
    is_completed = completed.wait(timeout_seconds)
    
    if is_completed:
        print("Test completed within the timeout period")
        if error_message[0] is not None:
            print(f"Error occurred: {error_message[0]}")
            # For buggy version, we don't expect to get here (it should hang)
            # For fixed version, we expect an auth error
            if "auth" in error_message[0].lower() or "api key" in error_message[0].lower():
                if version == "fixed" or version == "patched":
                    print("✅ BUG FIXED: crew.kickoff() properly raised an authentication error")
                    return 0
                else:
                    print("❌ UNEXPECTED: Buggy version should hang but raised an error")
                    return 1
            else:
                print("❌ UNEXPECTED: Error is not authentication related")
                return 1
        else:
            print("❌ UNEXPECTED: Execution completed without error, even with an invalid API key")
            return 1
    else:
        # If we're testing the buggy version, a hang is expected
        if version == "buggy":
            print("✅ BUG REPRODUCED: crew.kickoff() hung as expected with invalid API key")
            return 0
        else:
            print("❌ BUG NOT FIXED: crew.kickoff() still hangs with invalid API key")
            return 1

if __name__ == "__main__":
    version = sys.argv[1] if len(sys.argv) > 1 else "buggy"
    sys.exit(test_crew_hang(version))