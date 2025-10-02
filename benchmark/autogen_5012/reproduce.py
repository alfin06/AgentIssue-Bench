import sys
import re
from pathlib import Path

def run_test(version: str) -> int:
    readme_path = Path("README.md")
    if not readme_path.exists():
        print("README.md not found")
        return 1

    content = readme_path.read_text(encoding="utf-8")

    buggy_pattern = re.search(r'print\s*\(\s*agent\.run\(', content)
    fixed_pattern = re.search(r'print\s*\(\s*await\s+agent\.run\(', content)

    if version == "buggy":
        return 0 if buggy_pattern else 1
    elif version in ["fixed", "patched"]:
        return 0 if fixed_pattern else 1
    else:
        print(f"Invalid version: {version}")
        return 2

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