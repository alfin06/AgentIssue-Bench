import subprocess
import sys

def main():
    try:
        print("Running: crewai reset-memories -a")
        result = subprocess.run(
            ["crewai", "reset-memories", "-a"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        stdout = result.stdout
        stderr = result.stderr

        if "disk I/O error" in stderr.lower():
            print("❌ BUG REPRODUCED: Disk I/O error occurred during memory reset.")
            print(stderr)
            sys.exit(1)
        elif result.returncode != 0:
            print("❌ Non-zero exit code, but no disk error found.")
            print(stderr)
            sys.exit(2)
        else:
            print("✅ Memory reset succeeded.")
            print(stdout)
            sys.exit(0)

    except FileNotFoundError:
        print("❌ 'crewai' CLI tool not found in PATH.")
        sys.exit(3)
    except Exception as e:
        print("❌ Unexpected error occurred:", e)
        sys.exit(4)

if __name__ == "__main__":
    main()
