import sys
import os

def find_conversable_agent(base_dir):
    print(f"Searching for conversable_agent.py in {base_dir}")
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file == "conversable_agent.py":
                file_path = os.path.join(root, file)
                print(f"Found conversable_agent.py at {file_path}")
                return file_path
    print("conversable_agent.py not found in source tree.")
    return None

def check_buggy_patterns(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    buggy_pattern1 = '[self._str_for_tool_response(tool_return["content"]) for tool_return in tool_returns]'
    buggy_pattern2 = 'response = {"role": "user", "content": reply, "tool_responses": tool_returns}'
    return buggy_pattern1 in content or buggy_pattern2 in content

def check_fixed_patterns(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    fixed_pattern1 = '[self._str_for_tool_response(tool_return) for tool_return in tool_returns]'
    fixed_pattern2 = 'response = {"role": "user", "content": reply}'
    # Also check that tool_responses is only added if tool_returns
    conditional_tool_responses = 'if tool_returns:\n                response["tool_responses"] = tool_returns'
    return fixed_pattern1 in content and fixed_pattern2 in content and conditional_tool_responses in content

def run_test(version: str) -> int:
    base_dir = "/app/source_code_buggy" if version == "buggy" else "/app/source_code_fixed"
    file_path = find_conversable_agent(base_dir)
    if not file_path:
        print("conversable_agent.py not found in source tree.")
        return 1
    if version == "buggy":
        if check_buggy_patterns(file_path):
            print("✅ Buggy code pattern detected (bug reproduced)")
            return 0
        else:
            print("❌ Buggy code pattern not found (bug not reproduced)")
            return 1
    elif version in ["fixed", "patched"]:
        if check_fixed_patterns(file_path):
            print("✅ Fixed code pattern detected (fix verified)")
            return 0
        else:
            print("❌ Fixed code pattern not found (fix not verified)")
            return 1
    else:
        print(f"Unknown version: {version}")
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