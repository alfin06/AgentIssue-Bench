#!/usr/bin/env python3
import os
import sys

def run_test(version: str) -> int:
    root = f"/app/source_code_{version}"
    file_path = os.path.join(root, "camel", "models", "deepseek_model.py")

    if not os.path.exists(file_path):
        print(f"Error: file not found: {file_path}")
        return 1

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    search_snippet = (
        "messages = [\n"
        "                {  # type: ignore[misc]\n"
        "                    **msg,\n"
        "                    'content': re.sub(\n"
        "                        r'<think>.*?</think>',"
    )

    found = search_snippet in content
    if version == "buggy":
        return 0 if found else 1
    elif version in ["fixed", "patched"]:
        return 0 if not found else 1
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