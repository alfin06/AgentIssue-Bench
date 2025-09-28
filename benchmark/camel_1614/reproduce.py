#!/usr/bin/env python3
import os
import sys

def run_test(version: str) -> int:
    """
    Checks if the DeepSeek reasoner code contains the <think> removal logic.

    Args:
        version (str): One of 'buggy', 'fixed', 'patched'

    Returns:
        int: Exit code according to the reproduction logic
            - Buggy: 1 if bug not reproduced, 0 if bug reproduced
            - Fixed/Patched: 0 if fix confirmed, 1 if fix failed
    """
    # 1. Build file path
    root = f"/app/source_code_{version}"
    file_path = os.path.join(root, "camel", "models", "deepseek_model.py")

    # 2. Check file existence
    if not os.path.exists(file_path):
        print(f"Error: file not found: {file_path}")
        return 1  # treat as failure

    # 3. Read file content
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 4. The snippet to search for
    search_snippet = (
        "messages = [\n"
        "                {  # type: ignore[misc]\n"
        "                    **msg,\n"
        "                    'content': re.sub(\n"
        "                        r'<think>.*?</think>',"
    )

    found = search_snippet in content

    # 5. Determine exit code according to version
    if version == "buggy":
        # Buggy: issue should be reproducible
        return 0 if found else 1
    elif version in ["fixed", "patched"]:
        # Fixed or patched: issue should NOT be reproducible
        return 0 if not found else 1

    # Default failure
    return 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reproduce.py [buggy|fixed|patched]")
        sys.exit(2)

    version = sys.argv[1]
    if version not in ["buggy", "fixed", "patched"]:
        print(f"Invalid version: {version}")
        sys.exit(2)

    exit_code = run_test(version)
    sys.exit(exit_code)