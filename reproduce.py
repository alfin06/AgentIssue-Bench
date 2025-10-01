import json
import os
import shutil
import subprocess
import git # GitPython
import docker # Docker SDK
import requests
import time
from urllib.parse import urlparse
import re
import stat # For shutil.rmtree onerror
from dotenv import load_dotenv

load_dotenv(override=True)

# --- Configuration ---
REPORT_FILE = "results.json" # Your input file
WORKSPACE_DIR = "reproduction_workspace2"
OUTPUT_STATUS_FILE = "reproduction_status.json"
FAILURE_TESTS_DIR = os.path.join(WORKSPACE_DIR, "failure_triggering_tests")
DOCKER_CLIENT = docker.from_env()
DOCKER_HUB_USERNAME = os.environ.get("DOCKER_HUB_USERNAME")

# --- NEW: GPT-4o Code Generation Configuration ---
# Set this to True to use GPT-4o to GENERATE failure-triggering tests from natural language.
USE_GPT4O_CODE_GENERATION = True 
# For this to work, you must set the OPENAI_API_KEY environment variable.
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
MODEL_NAME = os.environ.get('MODEL_NAME', 'gpt-4o')

# It's highly recommended to use environment variables for secrets
GITHUB_PAT = os.environ.get("GITHUB_PAT")

# --- Shell Script Content for Benchmark Docker Image ---
RUN_TEST_ENTRYPOINT_SH_CONTENT = """#!/bin/bash
set -eo pipefail

# This script is the universal test runner for a benchmark image.
# It intelligently runs a .sh or .py test script.

CODE_DIR="/app/source_code_buggy"
PYTHON_CMD="${PYTHON_CMD:-python}"
# Define paths for potential test scripts inside the container
REPRO_COMMAND_SH="/opt/repro_command.sh"
REPRO_SCRIPT_PY="/opt/repro_script.py"

cd "${CODE_DIR}"

run_test() {
    echo "--- Running Test ---"
    
    # Check for shell script first, then python script
    if [ -f "${REPRO_COMMAND_SH}" ]; then
        echo "Found repro_command.sh. Executing with bash..."
        chmod +x "${REPRO_COMMAND_SH}"
        if bash "${REPRO_COMMAND_SH}"; then
            echo "--- Test script executed successfully (exit code 0) ---"
        else
            echo "--- Test script failed (exit code $?) ---"
        fi
    elif [ -f "${REPRO_SCRIPT_PY}" ]; then
        echo "Found repro_script.py. Executing with python..."
        if ${PYTHON_CMD} "${REPRO_SCRIPT_PY}"; then
            echo "--- Test script executed successfully (exit code 0) ---"
        else
            echo "--- Test script failed (exit code $?) ---"
        fi
    else
        echo "--- FATAL ERROR: No reproduction script found! ---"
        echo "Looked for ${REPRO_COMMAND_SH} and ${REPRO_SCRIPT_PY}"
        exit 127
    fi
}

case "$1" in
    test_buggy)
        echo "=== Testing BUGGY Version (Commit: ${BUGGY_COMMIT}) ==="
        echo "Checking out buggy commit..."
        git -c advice.detachedHead=false checkout "${BUGGY_COMMIT}" --force
        run_test
        ;;
    test_fixed)
        if [ -z "${FIXED_COMMIT}" ] || [ "${FIXED_COMMIT}" == "N/A" ]; then
            echo "ERROR: FIXED_COMMIT not set." >&2; exit 1;
        fi
        echo "=== Testing FIXED Version (Commit: ${FIXED_COMMIT}) ==="
        git -c advice.detachedHead=false checkout "${FIXED_COMMIT}" --force
        run_test
        ;;
    show_diff)
        if [ -z "${FIXED_COMMIT}" ] || [ "${FIXED_COMMIT}" == "N/A" ]; then
             echo "ERROR: FIXED_COMMIT not set." >&2; exit 1;
        fi
        echo "=== Diff between BUGGY (${BUGGY_COMMIT}) and FIXED (${FIXED_COMMIT}) ==="
        git diff "${BUGGY_COMMIT}" "${FIXED_COMMIT}" --
        ;;
    inspect_buggy)
        echo "Setting up BUGGY environment (commit: ${BUGGY_COMMIT})..."
        git -c advice.detachedHead=false checkout "${BUGGY_COMMIT}" --force
        echo "Use 'docker exec -it <container_id> bash' to explore."
        tail -f /dev/null
        ;;
    bash)
        echo "Entering bash shell. Defaulting to BUGGY commit (${BUGGY_COMMIT})."
        git -c advice.detachedHead=false checkout "${BUGGY_COMMIT}" --force
        /bin/bash
        ;;
    help|*)
        echo "Usage: docker run <image_name> [test_buggy|test_fixed|show_diff|inspect_buggy|bash|help]"
        if [ "$1" != "help" ] && [ ! -z "$1" ]; then exit 1; fi
        ;;
esac
"""

# --- Helper Functions ---

def handle_remove_readonly(func, path, exc_info):
    if not os.access(path, os.W_OK): os.chmod(path, stat.S_IWUSR); func(path)
    else: raise

def get_repo_url_and_commit_from_pr(pr_url, headers):
    if not pr_url: return None, None, None
    parsed_url = urlparse(pr_url)
    path_parts = parsed_url.path.strip('/').split('/')
    if len(path_parts) < 4 or path_parts[2] != 'pull': return None, None, None
    owner, repo, pr_number = path_parts[0], path_parts[1], path_parts[3]
    api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls/{pr_number}"
    try:
        response = requests.get(api_url, headers=headers, timeout=30)
        response.raise_for_status()
        pr_data = response.json()
        
        repo_clone_url = pr_data['base']['repo']['clone_url']
        fixed_commit = pr_data.get('merge_commit_sha')

        if pr_data.get('merged') and fixed_commit:
            buggy_commit = pr_data['base']['sha']
            return repo_clone_url, buggy_commit, fixed_commit

        return repo_clone_url, pr_data['base']['sha'], pr_data['head']['sha']
    except Exception as e:
        print(f"      Error fetching PR data for {pr_url}: {e}")
        return None, None, None

def setup_workspace(sanitized_issue_id_str):
    issue_ws = os.path.join(WORKSPACE_DIR, str(sanitized_issue_id_str))
    if os.path.exists(issue_ws):
        shutil.rmtree(issue_ws, onerror=handle_remove_readonly)
        time.sleep(0.1)
    os.makedirs(issue_ws)
    return issue_ws

def checkout_code(repo_url, commit_hash, target_dir):
    print(f"      Cloning {repo_url} and checking out {commit_hash}...")
    os.environ["GIT_HTTP_LOW_SPEED_LIMIT"] = "1000"
    os.environ["GIT_HTTP_LOW_SPEED_TIME"] = "120"
    for attempt in range(10):  # Increase retries
        try:
            repo = git.Repo.clone_from(repo_url, target_dir, depth=1)
            repo.git.checkout(commit_hash, force=True)
            print(f"      Checked out commit {commit_hash}")
            return True
        except git.exc.GitCommandError as e:
            if 'timed out' in str(e).lower() and attempt < 9:
                print(f"        Network timeout (Attempt {attempt + 1}/10). Retrying..."); time.sleep(5)
            else:
                print(f"      GitCommandError: {e.stderr}"); return False
        except Exception as e:
            print(f"      Unexpected checkout error: {e}"); return False
    return False

def build_docker_image(image_tag, context_path):
    print(f"      Building Docker image {image_tag} from context: {context_path}...")
    if os.path.exists(os.path.join(context_path, "Dockerfile")):
        print("        Found existing project Dockerfile. Using it.")
        try:
            DOCKER_CLIENT.images.build(path=context_path, tag=image_tag, rm=True)
            return image_tag, ["# Deps managed by original Dockerfile"], "existing_image"
        except Exception as e:
            print(f"      Error building from existing Dockerfile: {e}"); return None, [], None

    print("        No Dockerfile found. Generating one with heuristics...")
    base_image_str = "python:3.11-slim"
    dep_lines = []
    
    poetry_toml_path = os.path.join(context_path, "pyproject.toml")
    if os.path.exists(poetry_toml_path):
        print("        Found pyproject.toml. Analyzing for Python version.")
        try:
            with open(poetry_toml_path, 'r', encoding='utf-8') as f:
                toml_content = f.read()
            
            match = re.search(r"python\s*=\s*[\"']\^?(\d+\.\d+)", toml_content)
            if match:
                py_version = max(py_version, 10)
                print(f"        Project requires Python {py_version}. Adjusting base image.")
                base_image_str = f"python:{py_version}-slim"
        except Exception as e:
            print(f"        Could not parse pyproject.toml for Python version, using default. Error: {e}")

    if os.path.exists(os.path.join(context_path, "poetry.lock")):
        poetry_install_command = "poetry install --no-interaction --no-ansi --sync"
        dep_lines.extend([
            "RUN pip install --no-cache-dir -U pip poetry", 
            f"RUN poetry config virtualenvs.create false && {poetry_install_command}"
        ])
    elif os.path.exists(os.path.join(context_path, "requirements.txt")):
        dep_lines.append("RUN pip install --no-cache-dir -r requirements.txt")
    
    # Add common tools that might be needed by a user's repro script
    common_tools_install = "RUN pip install --no-cache-dir python-dotenv"
    dep_lines.append(common_tools_install)

    gen_df_name = "Dockerfile.repro.generated"
    with open(os.path.join(context_path, gen_df_name), "w") as f:
        f.write(f"FROM {base_image_str}\nWORKDIR /app\nCOPY . /app\n" + "\n".join(dep_lines))
    
    try:
        DOCKER_CLIENT.images.build(path=context_path, dockerfile=gen_df_name, tag=image_tag, rm=True)
        return image_tag, dep_lines, base_image_str
    except docker.errors.BuildError as e:
        log_lines = []
        for line in e.build_log:
            log_lines.append(line.get('stream', '').strip())
        print(f"      Error building generated Dockerfile: {e}\nBuild Log:\n{''.join(log_lines)}");
        return None, dep_lines, base_image_str
    except Exception as e:
        print(f"      Unexpected error building Docker image: {e}"); return None, [], base_image_str

def run_in_docker(image_tag, command_str, code_dir_abs_path):
    print(f"      Running in Docker ({image_tag}): {command_str}")
    try:
        output = DOCKER_CLIENT.containers.run(image_tag, command_str, volumes={code_dir_abs_path: {'bind': '/app', 'mode': 'rw'}}, working_dir="/app", stderr=True, remove=True)
        return output.decode('utf-8', errors='replace'), 0
    except docker.errors.ContainerError as e:
        return e.stderr.decode('utf-8', errors='replace'), e.exit_status
    except Exception as e:
        return str(e), -1

# --- NEW: GPT-4o Code Generation Function ---
def generate_repro_script_with_gpt4o(description):
    if not USE_GPT4O_CODE_GENERATION: return None, None
    if not OPENAI_API_KEY:
        print(f"        OPENAI_API_KEY environment variable not set. Skipping {MODEL_NAME} code generation.")
        return None, None

    print(f"        Attempting to generate repro script using {MODEL_NAME}...")
    
    prompt = (
        "You are an expert software developer and QA tester. Your goal is to write a Python script that reproduces the bug "
        "described in the following GitHub issue. Read the entire issue description, including the user's problem, the "
        "expected behavior, and any error messages. Write a single, complete, and executable Python script (`repro_script.py`) "
        "that demonstrates the bug. The script must include all necessary imports and setup. If the user mentions specific "
        "inputs, tools, or models (e.g., 'claude-3-haiku-20240307', 'tavily tool'), you MUST use them in the script. "
        "Your output must be ONLY the raw Python code. Do not include any explanations, markdown, or anything else. "
        "If you determine that it is impossible to write a script from the given description, respond with the exact string 'STR_NOT_AUTOMATABLE'."
    )

    try:
        response = requests.post(
            "https://openkey.cloud/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
            json={"model": MODEL_NAME, "messages": [{"role": "system", "content": prompt}, {"role": "user", "content": description}], "temperature": 0.0},
            timeout=90,
        )
        response.raise_for_status()
        data = response.json()
        
        script_content = data["choices"][0]["message"]["content"].strip()
        script_content = re.sub(r"^```python\s*\n", "", script_content).strip()
        script_content = re.sub(r"\n```$", "", script_content).strip()

        if script_content and "STR_NOT_AUTOMATABLE" not in script_content:
            print("        GPT-4o successfully generated a script.")
            return "repro_script.py", script_content
        else:
            print("        GPT-4o determined no runnable script could be generated.")
            return None, None
    except Exception as e:
        print(f"        Error during GPT-4o API call: {e}")
        return None, None

# --- Regex-based extraction function (fallback) ---
def find_repro_script_with_regex(description):
    print("        Falling back to regex-based STR extraction...")
    
    script_name, script_content = None, None
    
    # CORRECTED: Multi-stage regex to handle different code block formats
    # 1. Look for fenced Python block
    python_match = re.search(r"```python\s*\n(.*?)\n```", description, re.DOTALL | re.IGNORECASE)
    if python_match:
        script_content = python_match.group(1).strip()
        script_name = "repro_script.py"
    else:
        # 2. Look for any other fenced block
        any_code_match = re.search(r"```(?:\w*)\s*\n(.*?)\n```", description, re.DOTALL | re.IGNORECASE)
        if any_code_match:
            script_content = any_code_match.group(1).strip()
            script_name = "repro_script.py" if "import " in script_content else "repro_command.sh"
        else:
            # 3. Look for inline code block after 'code:'
            inline_code_match = re.search(r"code:\s*`([^`]+)`", description, re.DOTALL | re.IGNORECASE)
            if inline_code_match:
                script_content = inline_code_match.group(1).strip()
                script_name = "repro_script.py"

    return script_name, script_content

# --- Main STR Execution Orchestrator ---
def execute_str(issue_details, image_tag, code_dir_abs_path):
    print("      Attempting to execute Steps to Reproduce (STR)...")
    description = issue_details.get("description", "")
    
    script_name, script_content = None, None
    
    script_name, script_content = generate_repro_script_with_gpt4o(description)
    
    if not script_content:
        script_name, script_content = find_repro_script_with_regex(description)

    if not script_content:
        return "STR_NOT_AUTOMATABLE", -1, None
    
    cmd_str = f"bash /app/{script_name}" if script_name.endswith(".sh") else f"python /app/{script_name}"
    
    host_script_path = os.path.join(code_dir_abs_path, script_name)
    with open(host_script_path, "w", encoding='utf-8', newline='\n') as f:
        if script_name.endswith(".sh"): f.write("#!/bin/bash\nset -ex\n")
        f.write(script_content)
    
    output, exit_code = run_in_docker(image_tag, cmd_str, code_dir_abs_path)
    return output, exit_code, script_name

def verify_bug_manifestation(output, exit_code, issue_details):
    print("      Verifying bug manifestation...")
    if exit_code != 0 or "traceback" in output.lower() or "error:" in output.lower():
        print("        Verified: Bug manifested (non-zero exit or error string found).")
        return True
    print("        Could not programmatically verify bug manifestation."); return False

# --- Main Orchestration ---
def process_issue(issue_details, sanitized_issue_id, headers):
    print(f"\n--- Processing Issue {sanitized_issue_id} ({issue_details.get('github_url')}) ---")
    status = {"issue_id": sanitized_issue_id, "github_url": issue_details.get("github_url"), "status_message": "Started"}
    issue_ws_path = setup_workspace(sanitized_issue_id)
    
    repo_url, buggy_commit, fixed_commit = get_repo_url_and_commit_from_pr(issue_details.get("linked_pr_url"), headers)
    if not repo_url or not buggy_commit:
        status["status_message"] = "FAILED: Could not get repo/commit info."; return status
    status.update({"repo_url": repo_url, "buggy_commit": buggy_commit, "fixed_commit": fixed_commit})
    status["benchmark_docker_image_name"] = f"{DOCKER_HUB_USERNAME}/agentissue-bench:{sanitized_issue_id}"
    
    code_dir_buggy = os.path.join(issue_ws_path, "code_buggy")
    if not checkout_code(repo_url, buggy_commit, code_dir_buggy):
        status["status_message"] = "FAILED: Could not checkout buggy code."; return status

    image_tag_buggy_local = f"repro_{sanitized_issue_id}_buggy:latest"
    built_image_tag, dep_lines, base_img = build_docker_image(image_tag_buggy_local, code_dir_buggy)
    if not built_image_tag:
        status["status_message"] = "FAILED: Docker build for buggy version failed."; return status

    output, exit_code, script_name_used = execute_str(issue_details, built_image_tag, os.path.abspath(code_dir_buggy))
    if output == "STR_NOT_AUTOMATABLE" or not script_name_used:
        status["status_message"] = "SKIPPED: STR_NOT_AUTOMATABLE"; return status

    if verify_bug_manifestation(output, exit_code, issue_details):
        status.update({"reproduced_bug": True, "status_message": "SUCCESS: Bug reproduced."})
        print(f"  SUCCESS: Bug reproduced for issue {sanitized_issue_id}!")
        
        test_case_dir = os.path.join(FAILURE_TESTS_DIR, sanitized_issue_id)
        try:
            os.makedirs(test_case_dir, exist_ok=True)
            shutil.copytree(code_dir_buggy, os.path.join(test_case_dir, "source_code_buggy"))
            shutil.copy2(os.path.join(code_dir_buggy, script_name_used), os.path.join(test_case_dir, script_name_used))
            with open(os.path.join(test_case_dir, "run_test_entrypoint.sh"), "w", newline='\n') as f: f.write(RUN_TEST_ENTRYPOINT_SH_CONTENT)
            
            base_image_for_benchmark = base_img if base_img != "existing_image" else built_image_tag
            docker_env_setup_cmds = "\n".join(dep_lines) if base_img != "existing_image" else ""
            
            dockerfile_content = f"""
FROM {base_image_for_benchmark}
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
ARG BUGGY_COMMIT FIXED_COMMIT
ENV BUGGY_COMMIT=${{BUGGY_COMMIT}} FIXED_COMMIT=${{FIXED_COMMIT}}
ENV PYTHONPATH="/app"
COPY {script_name_used} /opt/{script_name_used}
COPY run_test_entrypoint.sh /usr/local/bin/run_test_entrypoint.sh
RUN chmod +x /usr/local/bin/run_test_entrypoint.sh
COPY ./source_code_buggy /app/source_code_buggy
WORKDIR /app/source_code_buggy
{docker_env_setup_cmds}
ENTRYPOINT ["/usr/local/bin/run_test_entrypoint.sh"]
CMD ["help"]
"""
            with open(os.path.join(test_case_dir, "Dockerfile.benchmark"), "w") as f: f.write(dockerfile_content)
            
            benchmark_image_name = status['benchmark_docker_image_name']
            build_command = (f'docker build --build-arg BUGGY_COMMIT="{buggy_commit}" --build-arg FIXED_COMMIT="{fixed_commit}" -t "{benchmark_image_name}" -f Dockerfile.benchmark .')
            run_command = f'docker run --rm -it "{benchmark_image_name}" test_buggy'
            
            metadata = {
                "issue_github_url": status["github_url"], "repo_url": status["repo_url"],
                "buggy_commit": buggy_commit, "fixed_commit": fixed_commit,
                "build_command_example": build_command, "run_command_example": run_command,
                "target_dockerhub_image": benchmark_image_name
            }
            with open(os.path.join(test_case_dir, "metadata.json"), "w") as f: json.dump(metadata, f, indent=4)
            print(f"        Saved complete test package to {test_case_dir}")
        except Exception as e: print(f"      Error saving test package: {e}")
    else:
        status.update({"reproduced_bug": False, "status_message": "FAILED: Bug not reproduced."})
    return status

if __name__ == "__main__":
    if USE_GPT4O_CODE_GENERATION and not OPENAI_API_KEY:
        print("Warning: USE_GPT4O_CODE_GENERATION is True, but OPENAI_API_KEY environment variable is not set. The script will fall back to regex.")

    os.makedirs(WORKSPACE_DIR, exist_ok=True)
    os.makedirs(FAILURE_TESTS_DIR, exist_ok=True)
    print(f"--- DEBUG: Script sees GITHUB_PAT: {'Yes' if GITHUB_PAT else 'No'} ---")
    print(GITHUB_PAT)
    headers = {"Authorization": f"Bearer {GITHUB_PAT}"} if GITHUB_PAT else {}

    try:
        with open(REPORT_FILE, 'r', encoding='utf-8') as f:
            issues_to_process = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error: Could not open or parse {REPORT_FILE}: {e}")
        exit(1)

    all_statuses = []
    for i, issue in enumerate(issues_to_process):
        issue_url = issue.get('github_url', '')
        sanitized_id = f"unknown_issue_{i}"
        if issue_url:
            try:
                path_parts = urlparse(issue_url).path.strip('/').split('/')
                if len(path_parts) >= 4 and path_parts[2] == 'issues':
                    repo_name = path_parts[1].lower().replace('-', '_')
                    issue_number = path_parts[3]
                    sanitized_id = f"{repo_name}_{issue_number}"
                else:
                    sanitized_id = re.sub(r'[^a-zA-Z0-9_.-]+', '_', issue_url.split("://")[1])
            except Exception as e:
                print(f"Warning: Could not parse issue URL '{issue_url}' to create clean ID. Using default. Error: {e}")

        status_report = process_issue(issue, sanitized_id, headers)
        all_statuses.append(status_report)
        time.sleep(1)

    with open(OUTPUT_STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_statuses, f, indent=4)

    print(f"\n--- Reproduction Attempt Summary ---")
    for s in all_statuses:
        print(f"  Issue: {s.get('github_url', 'N/A')}, Reproduced: {s.get('reproduced_bug', False)}, Message: {s['status_message']}")
