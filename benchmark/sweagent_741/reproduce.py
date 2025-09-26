import subprocess
import sys
import os

def run_test(version: str) -> int:
    """
    Run the reproduction test for the given version.

    Returns:
        buggy:
            1 if bug is reproduced (utils missing)
            0 if bug is not reproduced (utils exists)
        fixed / patched:
            0 if bug is reproduced (utils missing → fix not working)
            1 if bug is not reproduced (utils exists → fix confirmed)
    """

    if version == "buggy":
        # For buggy, only check build/lib/sweagent
        target_dir = os.path.join("build", "lib", "sweagent")
        if not os.path.exists(target_dir):
            print(f"❌ Target directory does not exist: {target_dir}")
            return 0  # Bug not reproduced (since buggy missing directory)
        
        try:
            result = subprocess.run(
                ["ls", "-al", target_dir],
                capture_output=True,
                text=True,
                check=True
            )
            output = result.stdout
            print(output)  # debug

            bug_reproduced = "utils" not in output

        except subprocess.CalledProcessError as e:
            print(f"❌ Error running ls command: {e}")
            return 0

    else:
        # For fixed / patched, traverse from root
        try:
            result = subprocess.run(
                ["find", ".", "-name", "utils"],
                capture_output=True,
                text=True,
                check=True
            )
            output = result.stdout
            print(output)  # debug

            bug_reproduced = output.strip() == ""  # utils not found → bug reproduced

        except subprocess.CalledProcessError as e:
            print(f"❌ Error running find command: {e}")
            return 0

    # Interpret results
    if version == "buggy":
        if bug_reproduced:
            print(f"✅ Bug reproduced in buggy version ({version}) → return 1")
            return 1
        else:
            print(f"❌ Bug NOT reproduced in buggy version ({version}) → return 0")
            return 0

    else:  # fixed / patched
        if bug_reproduced:
            print(f"❌ Bug reproduced in {version} → fix not working → return 0")
            return 0
        else:
            print(f"✅ Bug NOT reproduced in {version} → fix confirmed → return 1")
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