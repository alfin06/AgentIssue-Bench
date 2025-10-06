import sys
import os

def has_value_pattern(repo_dir):
    target_file = "LRunControl.js"
    pattern = 'value=""'
    for root, dirs, files in os.walk(repo_dir):
        for file in files:
            if file == target_file and "components" in root and "frontend" in root:
                path = os.path.join(root, file)
                with open(path, encoding="utf-8") as f:
                    content = f.read()
                    if pattern in content:
                        print(f"Found 'value=\"\"' in {path}")
                        return True
    return False

def has_defaultvalue_pattern(repo_dir):
    """
    Check if 'defaultValue=""' exists in frontend/src/components/controls/LRunControl.js
    """
    target_file = "LRunControl.js"
    pattern = 'defaultValue=""'
    for root, dirs, files in os.walk(repo_dir):
        for file in files:
            if file == target_file and "components" in root and "frontend" in root:
                path = os.path.join(root, file)
                with open(path, encoding="utf-8") as f:
                    content = f.read()
                    if pattern in content:
                        print(f"Found 'defaultValue=\"\"' in {path}")
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
    }.get(version)
    if not repo_dir or not os.path.isdir(repo_dir):
        print(f"Source directory {repo_dir} not found.")
        sys.exit(2)
    if version in ("buggy", "patched"):
        if has_value_pattern(repo_dir):
            print("BUG: input uses value=\"\"")
            sys.exit(0)
        else:
            print("NO BUG: input does not use value=\"\"")
            sys.exit(1)
    elif version == "fixed":
        if has_defaultvalue_pattern(repo_dir):
            print("NO BUG: input uses defaultValue=\"\"")
            sys.exit(0)
        else:
            print("BUG: input does not use defaultValue=\"\"")
            sys.exit(1)
    else:
        print(f"Unknown version: {version}")
        sys.exit(2)

if __name__ == "__main__":
    main()