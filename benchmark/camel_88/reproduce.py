import os
import sys
import subprocess

CHECK_LINE = "self.update_messages(output_messages[0])"

def check_hardcode(file_path):
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return False
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    return CHECK_LINE in content



def run_test(version):
    root = f"/app/source_code_{version}"
    file_path = os.path.join(root, "camel", "agents", "chat_agent.py")

    has_hardcode = check_hardcode(file_path)

    if version == "buggy":
        return 0 if has_hardcode else 1
    else:
        return 1 if has_hardcode else 0
    

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