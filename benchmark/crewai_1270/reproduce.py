import sys
import os
from dotenv import load_dotenv
from crew import crewaiCrew

def main():
    os.environ["OTEL_SDK_DISABLED"] = "true"
    load_dotenv()

    inputs = {
        'topic': "AI Agents"
    }

    try:
        crewaiCrew().crew().kickoff(inputs=inputs)
        print("✅ Crew ran without error.")
        sys.exit(0)

    except UnicodeDecodeError as e:
        if "'gbk' codec can't decode" in str(e):
            print("❌ BUG REPRODUCED: UnicodeDecodeError due to file encoding.")
            print("Details:", e)
            sys.exit(1)
        else:
            print("❌ Unicode error:", e)
            sys.exit(2)

    except Exception as e:
        print("❌ Unexpected exception occurred:")
        print(e)
        sys.exit(2)

if __name__ == "__main__":
    main()
