import os
import json
import subprocess
from pathlib import Path

# CONFIG
SWE_BENCH_FILE = "agent_issue.json"
OUTPUT_DIR = "results"
MODEL_TEMP = "0.2"
MAIN_SCRIPT = "app/main.py"

# Prompt for inputs if not already in environment
MODEL_NAME = os.getenv("MODEL_NAME") or input("Enter the model name: ")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL") or input("Enter the OPENAI_BASE_URL: ")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") or input("Enter the OPENAI_API_KEY: ")

# Set environment variables
os.environ["OPENAI_BASE_URL"] = OPENAI_BASE_URL
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

def run_local_issue(task):
    instance_id = task["instance_id"]
    repo_name = instance_id.split("__")[1]
    repo_path = f"repo/{repo_name}"
    tmp_issue_file = Path(f"tmp_issue_{repo_name}.json")

    tmp_issue_file.write_text(json.dumps([task], indent=2), encoding="utf-8")

    command = [
        "python", MAIN_SCRIPT, "local-issue",
        "--output-dir", OUTPUT_DIR + "/",  # with trailing slash
        "--model", MODEL_NAME,
        "--model-temperature", MODEL_TEMP,
        "--local-repo", repo_path,
        "--issue-file", str(tmp_issue_file),
        "--task-id", instance_id
    ]

    command_str = "PYTHONPATH=. " + " ".join(command)
    print(f"▶ Running: {command_str}")
    result = subprocess.run(command_str, shell=True)

    if result.returncode != 0:
        print(f"❌ Task {instance_id} failed!")
    else:
        print(f"✅ Task {instance_id} completed!")

    tmp_issue_file.unlink()

def main():
    with open(SWE_BENCH_FILE) as f:
        tasks = json.load(f)

    for task in tasks:
        try:
            run_local_issue(task)
        except Exception as e:
            print(f"⚠️ Task {task['instance_id']} failed with exception: {e}")

if __name__ == "__main__":
    main()
