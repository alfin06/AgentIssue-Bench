import sys
import os
import re

FILE_PATH = "python/packages/autogen-core/pyproject.toml"

def get_project_dependencies(debug: bool = False):
    """只提取第一个 [project] 段落里的 dependencies 列表"""
    if not os.path.exists(FILE_PATH):
        print(f"File not found: {FILE_PATH}")
        return []

    with open(FILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    match = re.search(r"\[project\](.*?)(?:\n\[|$)", content, re.S)
    if not match:
        print("No [project] section found.")
        return []

    project_block = match.group(1)

    match = re.search(r"dependencies\s*=\s*\[(.*?)\]", project_block, re.S)
    if not match:
        print("No dependencies block found in [project].")
        return []

    deps_block = match.group(1)

    deps = []
    for line in deps_block.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        dep = line.rstrip(",").strip().strip('"').strip("'")
        if dep:
            deps.append(dep)

    if debug:
        print("📦 Parsed [project] dependencies:", deps)

    return deps


def run_test(version: str) -> int:
    deps = get_project_dependencies(debug=True)  
    grpcio_exists = any(dep.startswith("grpcio") for dep in deps)

    if version == "buggy":
        if not grpcio_exists:
            print("✅ Bug reproduced: grpcio not found in [project] dependencies.")
            return 0
        else:
            print("❌ Bug not reproduced: grpcio found in [project] dependencies.")
            return 1

    elif version in ["fixed", "patched"]:
        if grpcio_exists:
            print("✅ Fix confirmed: grpcio found in [project] dependencies.")
            return 0
        else:
            print("❌ Fix not working: grpcio not found in [project] dependencies.")
            return 1

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