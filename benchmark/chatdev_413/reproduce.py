#!/usr/bin/env python3
import sys
import subprocess

def run_test(version: str) -> int:
    """
    Runs `run.py` and checks if KeyError: 'web_spider' occurs.

    Args:
        version (str): One of 'buggy', 'fixed', 'patched'

    Returns:
        int: Exit code according to reproduction logic
            - Buggy: 0 if bug reproduced (KeyError occurs), 1 otherwise
            - Fixed/Patched: 0 if fix confirmed (KeyError does NOT occur), 1 otherwise
    """
    cmd = [
        "python3",
        "run.py",
        "--task", "design a 2048 game",
        "--name", "2048",
        "--org", "THUNLP"
    ]

    try:
        # Run the command
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        stdout = result.stdout
        stderr = result.stderr

        # print("stdout:",stdout)
        # print("stderr:", stderr)

        # Check if KeyError: 'web_spider' occurred
        bug_occurred = "an unexpected keyword argument 'refusal'" in stderr

        # print("bug_occurred = ", bug_occurred)
        
        if version == "buggy":
            # Buggy: issue should be reproducible
            return 0 if bug_occurred else 1
        elif version in ["fixed", "patched"]:
            # Fixed/Patched: issue should NOT be reproducible
            return 0 if not bug_occurred else 1

        

    except Exception as e:
        # print("except Exception as e:",)
        if version == "buggy":
            return 1 if bug_occurred else 0
        elif version in ["fixed", "patched"]:
            return 1 if not bug_occurred else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reproduce.py [buggy|fixed|patched]")
        sys.exit(2)

    version = sys.argv[1]
    if version not in ["buggy", "fixed", "patched"]:
        print(f"Invalid version: {version}")
        sys.exit(2)


    exit_code = run_test(version)
    # print("exit_code", exit_code)
    sys.exit(exit_code)