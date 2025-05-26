import json
import subprocess
from pathlib import Path
import shutil

RESULTS_DIR = Path("results")

def run_reproduce_script(repo_path: Path) -> bool:
    """Run reproduce.py in the given repo path."""
    reproduce_path = repo_path / "reproduce.py"
    if not reproduce_path.exists():
        print("❌ reproduce.py not found.")
        return False

    try:
        result = subprocess.run(
            ["python", "reproduce.py"],
            cwd=repo_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60
        )
        print(result.stdout.decode())
        if result.returncode != 0:
            print(f"❌ reproduce.py failed:\n{result.stderr.decode()}")
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running reproduce.py: {e}")
        return False

def save_repo_state(repo_path: Path):
    """Create a clean backup of the repo to restore later."""
    backup_path = repo_path.parent / f"{repo_path.name}_backup"
    if backup_path.exists():
        shutil.rmtree(backup_path)
    shutil.copytree(repo_path, backup_path)
    return backup_path

def restore_repo_state(repo_path: Path, backup_path: Path):
    """Restore repo to original state."""
    if repo_path.exists():
        shutil.rmtree(repo_path)
    shutil.copytree(backup_path, repo_path)
    shutil.rmtree(backup_path)

def refactor_project(repo_path: Path):
    """Optional: Run formatting or refactoring tools here."""
    try:
        subprocess.run(["black", "."], cwd=repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["isort", "."], cwd=repo_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        print(f"⚠️ Refactor failed (continuing): {e}")

def apply_patch_and_check(task_dir: Path):
    meta_path = task_dir / "meta.json"
    patch_path = task_dir / "output_0" / "extracted_patch_0.diff"

    if not patch_path.exists():
        print(f"❌ No patch found at {patch_path}")
        return False

    if not meta_path.exists():
        print(f"❌ No meta.json found in {task_dir}")
        return False

    with meta_path.open() as f:
        meta = json.load(f)

    repo_path = Path(meta["setup_info"]["repo_path"])
    print(f"\n📌 Evaluating {task_dir.name}")

    backup_path = save_repo_state(repo_path)

    try:
        print(f"📎 Applying patch: {patch_path.name}")
        subprocess.run(["git", "apply", str(patch_path.resolve())], check=True, cwd=repo_path)

        print("🛠️ Refactoring project...")
        refactor_project(repo_path)

        print("🚀 Running reproduce.py...")
        plausible = run_reproduce_script(repo_path)

    except subprocess.CalledProcessError as e:
        print(f"❌ Patch application failed: {e}")
        plausible = False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        plausible = False
    finally:
        print("🔄 Restoring repo to original state...")
        restore_repo_state(repo_path, backup_path)

    if plausible:
        print(f"✅ Patch plausible for {task_dir.name}")
    else:
        print(f"⚠️ Patch NOT plausible for {task_dir.name}")
    return plausible

def main():
    task_dirs = sorted(RESULTS_DIR.glob("*_*"))
    total = len(task_dirs)
    passed = 0

    for task_dir in task_dirs:
        if apply_patch_and_check(task_dir):
            passed += 1

    print(f"\n📊 {passed}/{total} plausible patches")

if __name__ == "__main__":
    main()
