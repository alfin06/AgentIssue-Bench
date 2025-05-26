import os
import subprocess
import shutil
import json
import tempfile
import glob
from pathlib import Path
import importlib.util

# Configuration
REPAIR_RESULTS_ROOT = "results/swe-bench-lite"
REPO_CLONE_PATH = "repo"
TIMEOUT = 60

def run_static_check(project_path: str) -> bool:
    try:
        for py_file in Path(project_path).rglob("*.py"):
            compile(py_file.read_text(), py_file.name, 'exec')
        return True
    except Exception as e:
        print(f"[Static Error] {e}")
        return False

def run_flake8_check(project_path: str) -> bool:
    try:
        result = subprocess.run(
            ["flake8", "."],
            cwd=project_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=TIMEOUT
        )
        output = result.stdout.decode()
        if output:
            print("[flake8] Issues found:\n" + output)
        return result.returncode == 0
    except Exception as e:
        print(f"[flake8 Error] {e}")
        return False

def run_import_check(project_path: str, edited_files: list) -> bool:
    try:
        for file_path in edited_files:
            abs_path = os.path.join(project_path, file_path)
            if not abs_path.endswith(".py") or not os.path.isfile(abs_path):
                continue
            module_name = Path(file_path).stem
            spec = importlib.util.spec_from_file_location(module_name, abs_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        return True
    except Exception as e:
        print(f"[Import Error] {e}")
        return False

def run_reproduce_script(project_path: str) -> bool:
    reproduce_path = Path(project_path) / "reproduce.py"
    if not reproduce_path.exists():
        print("[reproduce.py] Not found.")
        return False
    try:
        result = subprocess.run(
            ["python", "reproduce.py"],
            cwd=project_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=TIMEOUT
        )
        print(result.stdout.decode())
        if result.returncode != 0:
            print(f"[reproduce.py Error] {result.stderr.decode()}")
        return result.returncode == 0
    except Exception as e:
        print(f"[reproduce.py Exception] {e}")
        return False

def refactor_project(project_path: str):
    try:
        subprocess.run(["black", "."], cwd=project_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["isort", "."], cwd=project_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        print(f"[Refactor Error] {e}")

def is_patch_plausible(project_path: str, edited_files: list) -> bool:
    return (
        run_static_check(project_path) and
        run_flake8_check(project_path) and
        run_import_check(project_path, edited_files) and
        run_reproduce_script(project_path)
    )

def apply_patch_files(repo_path: str, edited_files: list, new_file_contents: list):
    for file_path, new_content in zip(edited_files, new_file_contents):
        full_path = os.path.join(repo_path, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, "w") as f:
            f.write(new_content)

def evaluate_all_patches():
    results = {}

    for sample_dir in os.listdir(REPAIR_RESULTS_ROOT):
        sample_path = os.path.join(REPAIR_RESULTS_ROOT, sample_dir)
        if not os.path.isdir(sample_path):
            continue

        print(f"\n🔍 Evaluating {sample_dir}")
        results[sample_dir] = {}

        processed_files = sorted(glob.glob(os.path.join(sample_path, "output_*_processed.jsonl")))
        for file_path in processed_files:
            with open(file_path) as f:
                for idx, line in enumerate(f):
                    patch_data = json.loads(line)
                    edited_files = patch_data.get("edited_files", [])
                    new_file_content = patch_data.get("new_file_content", [])

                    patch_key = f"{Path(file_path).stem}_patch_{idx}"
                    with tempfile.TemporaryDirectory() as temp_repo:
                        shutil.copytree(REPO_CLONE_PATH, temp_repo, dirs_exist_ok=True)
                        try:
                            apply_patch_files(temp_repo, edited_files, new_file_content)
                            refactor_project(temp_repo)
                            plausible = is_patch_plausible(temp_repo, edited_files)
                            results[sample_dir][patch_key] = plausible
                            print(f"✅ {patch_key}: {'PASS' if plausible else 'FAIL'}")
                        except Exception as e:
                            print(f"❌ Error evaluating patch {patch_key}: {e}")
                            results[sample_dir][patch_key] = False

    print(results)

if __name__ == "__main__":
    evaluate_all_patches()
