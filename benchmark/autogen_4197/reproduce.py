import sys
import json
import asyncio
from pathlib import Path

NOTEBOOK_PATH = Path("/app/python/packages/autogen-core/docs/src/user-guide/agentchat-user-guide/tutorial/agents.ipynb")
TARGET_HEADING = "### CounterDownAgent"

def extract_agent_code(notebook_path: Path) -> str:
    with notebook_path.open("r", encoding="utf-8") as f:
        nb = json.load(f)

    cells = nb.get("cells", [])
    capture = False
    code_to_run = []

    for cell in cells:
        cell_type = cell.get("cell_type")
        source = "".join(cell.get("source", []))
        if cell_type == "markdown" and TARGET_HEADING in source:
            capture = True
            continue
        if capture and cell_type == "code":
            code_to_run.append(source)
            break  # 只取第一个 code cell
    if not code_to_run:
        raise RuntimeError("Could not find code after the target heading")
    return code_to_run[0]

def run_test(version: str) -> int:
    NOTEBOOK_PATH = Path(f"/app/source_code_{version}/python/packages/autogen-core/docs/src/user-guide/agentchat-user-guide/tutorial/agents.ipynb")
    code = extract_agent_code(NOTEBOOK_PATH)
    try:
        local_vars = {}
        exec(
            f"import asyncio\n"
            f"async def _run():\n"
            + "\n".join([f"    {line}" for line in code.splitlines()])
            + "\nasyncio.run(_run())",
            {}, 
            local_vars
        )
    except NameError as e:
        if "CancellationToken" in str(e):
            return 1 if version == "buggy" else 0
        else:
            raise
    except Exception as e:
        if version == "buggy":
            return 0
        else:
            return 1
    else:
        return 0 if version in ["fixed", "patched"] else 0

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