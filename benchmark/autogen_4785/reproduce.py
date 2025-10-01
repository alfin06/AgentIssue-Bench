import os
import sys
from autogen_ext.models import OpenAIChatCompletionClient


def run_test(version: str) -> int:
    try:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        base_url = os.environ.get("BASE_URL", "")

        client = OpenAIChatCompletionClient(
            model="llama3-groq-70b-8192-tool-use-preview",
            base_url=base_url,
            api_key=api_key,
        )
        _ = client.model

    except Exception as e:
        if "llama3-groq-70b-8192-tool-use-preview" in str(e):
            return 0 if version == "buggy" else 1
        else:
            return 0 if version != "buggy" else 1
    else:

        return 0 if version in ["fixed", "patched"] else 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reproduce.py [buggy|fixed|patched]")
        sys.exit(2)

    version = sys.argv[1].lower()
    if version not in ["buggy", "fixed", "patched"]:
        print(f"Invalid version: {version}")
        sys.exit(2)

    exit_code = run_test(version)
    sys.exit(exit_code)