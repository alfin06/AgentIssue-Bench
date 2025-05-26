import os
import subprocess
import sys

def print_step(title):
    print(f"\n=== {title} ===")

def run_cmd(command, check=True):
    print(f"$ {command}")
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    print(result.stdout)
    if result.stderr:
        print("✅ STDERR:", result.stderr)
    if check and result.returncode != 0:
        print(f"❌ Command failed: {command}")
        sys.exit(result.returncode)
    return result

def main():
    print_step("1. Clone the repository and checkout v0.2.28")
    run_cmd("git clone https://github.com/superagent-ai/superagent.git")
    os.chdir("superagent")
    run_cmd("git checkout v0.2.28")

    print_step("2. Attempt to start the app with Docker Compose")
    result = run_cmd("docker compose up -d", check=False)

    print_step("3. Check logs of the UI container (superagent-ui)")
    run_cmd("docker logs --tail=50 superagent-ui", check=False)

    print_step("4. Try to access the container shell (should fail if container is not running)")
    result = run_cmd("docker ps -a --filter name=superagent-ui --format '{{.Status}}'", check=False)
    if "Exited" in result.stdout:
        print("❌ Container is not running. Reproduced the issue.")
        print("Likely cause: 'supabase' CLI missing in the container image.")
    else:
        print("✅ Container is running. The issue may be resolved or different on this environment.")

if __name__ == "__main__":
    main()
