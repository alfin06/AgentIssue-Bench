import sys
from pathlib import Path

def check_tiktoken_in_pyprojects() -> bool:
    """
    Returns True if any pyproject.toml contains 'tiktoken', False otherwise.
    Prints the path of the file if found.
    """
    pyprojects = Path("python/packages/autogen-studio/").rglob("pyproject.toml")
    for pyproject in pyprojects:
        try:
            content = pyproject.read_text()
        except Exception as e:
            print("Exception:", e)
            continue
        if '"tiktoken"' in content:
            print(f"✅ Found 'tiktoken' in: {pyproject}")
            return True
    return False

def run_test(version: str) -> int:
    tiktoken_found = check_tiktoken_in_pyprojects()
    print("tiktoken_found:", tiktoken_found)
    if version == "buggy":
        return 1 if tiktoken_found else 0
    else:
        return 0 if tiktoken_found else 1

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