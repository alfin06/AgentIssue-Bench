import sys
import os
from enum import Enum
import json

def main(version="buggy"):
    try:
        print(f"Testing CrewAI issue #1753 - Enum JSON serialization bug...")
        
        # Import crewai components
        from crewai.task import Task
        from crewai.agent import Agent
        from crewai.crew import Crew
        from crewai.utilities.crew_json_encoder import CrewJSONEncoder
        
        # Create the Enum class that will cause the error
        class CrewStatus(Enum):
            TODO = "To Do"
            SUCCESSFUL = "Successful"
            FAILED = "Failed"
        
        # Create a test instance of the enum
        status = CrewStatus.SUCCESSFUL
        
        # Try to serialize it using CrewJSONEncoder
        try:
            json_result = json.dumps(status, cls=CrewJSONEncoder)
            print(f"Serialized enum to JSON: {json_result}")
            print(f"✅ TEST PASSED: Successfully serialized Enum using CrewJSONEncoder")
            return 0
        except TypeError as e:
            if "is not JSON serializable" in str(e):
                print(f"✅ BUG REPRODUCED: {e}")
                print("This matches the expected error in issue #1753")
                return 0 if version == "buggy" else 1
            else:
                print(f"❌ UNEXPECTED ERROR: {e}")
                return 1
                
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return 1

if __name__ == "__main__":
    version = sys.argv[1] if len(sys.argv) > 1 else "buggy"
    sys.exit(main(version))