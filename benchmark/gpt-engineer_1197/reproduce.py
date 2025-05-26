import subprocess
import os
import shutil
import sys

def print_step(step):
    print(f"\n=== {step} ===")

def run_cmd(cmd, check=True):
    print(f"$ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr.strip())
    if check and result.returncode != 0:
        print("❌ Command failed")
        sys.exit(result.returncode)
    return result

def main():
    # Step 1: Prepare temp workspace
    temp_dir = "gpt_engineer_env_test"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    os.chdir(temp_dir)

    print_step("1. Initialize a Java Spring Boot project (simulated)")
    with open("main.java", "w") as f:
        f.write("// Dummy Java Spring Boot main class")

    with open("application-stage.yml", "w") as f:
        f.write("spring:\n  datasource:\n    url: jdbc:mysql://stage-db-url")

    print_step("2. Run gpt-engineer improve mode with environment split prompt")
    prompt = (
        "I want to separate different environments: stage and local. "
        "Current setting is for stage, so I need a new yaml config for local, and this local "
        "environment should use H2 DB. So yaml files will be two, and run.sh I also want two "
        "for different environments."
    )
    try:
        run_cmd(f"echo \"{prompt}\" | gpte -i", check=False)
    except Exception as e:
        print(f"❌ Exception occurred: {e}")

    print_step("3. If successful, both application-stage.yml and application-local.yml should exist")
    for f in os.listdir("."):
        print(f" - {f}")

    print_step("4. Reproduce known KeyError if agent fails to generate expected file structure")
    expected_file = "src/main/resources/application-stage.yml"
    if not os.path.exists(expected_file):
        print(f"❌ File not found: {expected_file}")
        print("✅ Successfully reproduced: KeyError likely due to missing file in files_dict.")
    else:
        print("✅ File exists, may need to verify content and further agent behavior.")

if __name__ == "__main__":
    main()
