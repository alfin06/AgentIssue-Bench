import sys
import os

def find_buggy_input_logic(repo_dir):
    target_file = "LRunControl.js"
    for root, dirs, files in os.walk(repo_dir):
        for file in files:
            if file == target_file:
                path = os.path.join(root, file)
                with open(path, encoding="utf-8") as f:
                    content = f.read()
                    if 'defaultValue=""' in content:
                        print(f"Found buggy input logic in {path}")
                        return True
    return False

def find_fixed_input_logic(repo_dir):
    """
    Look for fixed input logic in React source files.
    """
    for root, dirs, files in os.walk(repo_dir):
        for file in files:
            if file.endswith(".jsx") or file.endswith(".js"):
                path = os.path.join(root, file)
                with open(path, encoding="utf-8") as f:
                    content = f.read()
                    # Fixed: input resets properly, e.g. uses key prop or useEffect to reset
                    if (
                        ("defaultValue={runConfigDefault.environment.environment_setup.script_path.script_path}" in content
                         or "defaultValue=\"\"" in content)
                        and ("key={" in content or "useEffect" in content or "reset" in content)
                    ):
                        print(f"Found fixed input logic in {path}")
                        return True
    return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python reproduce.py [buggy|fixed|patched]")
        sys.exit(2)
    version = sys.argv[1]
    repo_dir = {
        "buggy": "/app/source_code_buggy",
        "fixed": "/app/source_code_fixed",
        "patched": "/app/source_code_patched"
    }.get(version)
    if not repo_dir or not os.path.isdir(repo_dir):
        print(f"Source directory {repo_dir} not found.")
        sys.exit(2)
    if version == "buggy":
        if find_buggy_input_logic(repo_dir):
            sys.exit(0)
        else:
            sys.exit(1)
    elif version in ("fixed", "patched"):
        if find_fixed_input_logic(repo_dir):
            sys.exit(0)
        else:
            sys.exit(1)
    else:
        print(f"Unknown version: {version}")
        sys.exit(2)

if __name__ == "__main__":
    main()