import os
import subprocess
import sys

# Set up environment
def setup_env():
    os.environ["LANGUAGE"] = "french"
    os.environ["OPENAI_API_KEY"] = input("Enter OPENAI_API_KEY")

# Simulate prompt call that causes the bug
def reproduce_bug():
    try:
        from gpt_researcher.prompts.prompt import generate_subtopic_report_prompt

        # Simulate arguments passed during runtime
        generate_subtopic_report_prompt(
            current_subtopic="AI ethics",
            existing_headers=[],
            relevant_written_contents=[],
            main_topic="Artificial Intelligence",
            context={},
            report_format="apa",
            max_subsections=3,
            total_words=500,
            tone=None,
            language="french"  # This triggers the bug if not defined in original function
        )
    except TypeError as e:
        print("❌ Bug reproduced: Missing `language` parameter in function signature.")
        print(f"Error:\n{e}")
    except Exception as ex:
        print("❌ Unexpected error:")
        print(ex)
    else:
        print("✅ No error.")

if __name__ == "__main__":
    setup_env()
    reproduce_bug()