import os
import subprocess
import re

PATCHES_ROOT = "Patches"
DOCKER_IMAGE_BASE = "alfin06/agentissue-bench"

global_success = 0
global_total = 0

for tag in os.listdir(PATCHES_ROOT):
    patch_dir = os.path.join(PATCHES_ROOT, tag)
    if not os.path.isdir(patch_dir):
        continue

    patch_files = [f for f in os.listdir(patch_dir) if f.endswith(".patch")]
    if not patch_files:
        print(f"Patch directory {patch_dir} has no .patch files, skipping.")
        continue

    print(f"\n===== Evaluating patches for tag: {tag} =====")
    docker_image = f"{DOCKER_IMAGE_BASE}:{tag}"

    print(f"Pulling docker image: {docker_image}")
    subprocess.run(["docker", "pull", docker_image], check=True)

    success_count = 0
    total_count = len(patch_files)

    for patch_file in patch_files:
        patch_path = os.path.abspath(os.path.join(patch_dir, patch_file))
        print(f"\n=== Testing patch: {patch_file} ===")

        # Run apply_patch and test_patched in the same container session
        cmd = [
            "docker", "run", "--rm",
            "--entrypoint", "bash",
            "-v", f"{os.path.dirname(patch_path)}:/patches",
            docker_image,
            "-c", f"/usr/local/bin/run_test_entrypoint.sh apply_patch /patches/{patch_file} && /usr/local/bin/run_test_entrypoint.sh test_patched"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        
        # Check if there was an error in applying the patch
        if "FAILED" in result.stdout or result.returncode != 0:
            print(f"❌ Patch {patch_file}: FAILED")
            continue
        
        # Check if test was successful
        if "PATCH SUCCEEDED" in result.stdout or "PATCH SUCCESSFULLY VERIFIED" in result.stdout or "FIX SUCCESSFULLY VERIFIED" in result.stdout:
            print(f"✅ Patch {patch_file}: SUCCESS")
            success_count += 1
        else:
            print(f"❌ Patch {patch_file}: FAILED")

    print(f"\n=== Patch Testing Summary for {tag} ===")
    print(f"Total patches tested: {total_count}")
    print(f"Successful patches: {success_count}")
    print(f"Failed patches: {total_count - success_count}")

    global_success += success_count
    global_total += total_count

print("\n=== Global Patch Testing Summary ===")
print(f"Total patches tested: {global_total}")
print(f"Successful patches: {global_success}")
print(f"Failed patches: {global_total - global_success}")