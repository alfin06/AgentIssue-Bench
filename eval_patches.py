import os
import subprocess

PATCHES_ROOT = "Patches"
DOCKER_IMAGE_BASE = "alfin06/agentissue-bench"
LOG_FILE = "patch_eval.log"

global_success = 0
global_total = 0

with open(LOG_FILE, "w", encoding="utf-8") as log:
    for tag in os.listdir(PATCHES_ROOT):
        patch_dir = os.path.join(PATCHES_ROOT, tag)
        if not os.path.isdir(patch_dir):
            continue

        patch_files = [f for f in os.listdir(patch_dir) if f.endswith(".patch")]
        if not patch_files:
            msg = f"Patch directory {patch_dir} has no .patch files, skipping."
            print(msg)
            log.write(msg + "\n")
            continue

        msg = f"\n===== Evaluating patches for tag: {tag} ====="
        print(msg)
        log.write(msg + "\n")
        docker_image = f"{DOCKER_IMAGE_BASE}:{tag}"

        msg = f"Pulling docker image: {docker_image}"
        print(msg)
        log.write(msg + "\n")
        subprocess.run(["docker", "pull", docker_image], check=True)

        success_count = 0
        total_count = len(patch_files)

        for patch_file in patch_files:
            patch_path = os.path.abspath(os.path.join(patch_dir, patch_file))
            msg = f"\n=== Testing patch: {patch_file} ==="
            print(msg)
            log.write(msg + "\n")

            cmd = [
                "docker", "run", "--rm",
                "--entrypoint", "bash",
                "-v", f"{os.path.dirname(patch_path)}:/patches",
                docker_image,
                "-c", f"/usr/local/bin/run_test_entrypoint.sh apply_patch /patches/{patch_file} && /usr/local/bin/run_test_entrypoint.sh test_patched"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            print(result.stdout)
            log.write(result.stdout + "\n")
            
            if "FAILED" in result.stdout or result.returncode != 0:
                msg = f"❌ Patch {patch_file}: FAILED"
                print(msg)
                log.write(msg + "\n")
                continue
            
            if ("PATCH SUCCEEDED" in result.stdout or 
                "PATCH SUCCESSFULLY VERIFIED" in result.stdout or 
                "FIX SUCCESSFULLY VERIFIED" in result.stdout):
                msg = f"✅ Patch {patch_file}: SUCCESS"
                print(msg)
                log.write(msg + "\n")
                success_count += 1
            else:
                msg = f"❌ Patch {patch_file}: FAILED"
                print(msg)
                log.write(msg + "\n")

        msg = f"\n=== Patch Testing Summary for {tag} ==="
        print(msg)
        log.write(msg + "\n")
        msg = f"Total patches tested: {total_count}"
        print(msg)
        log.write(msg + "\n")
        msg = f"Successful patches: {success_count}"
        print(msg)
        log.write(msg + "\n")
        msg = f"Failed patches: {total_count - success_count}"
        print(msg)
        log.write(msg + "\n")

        global_success += success_count
        global_total += total_count

    msg = "\n=== Global Patch Testing Summary ==="
    print(msg)
    log.write(msg + "\n")
    msg = f"Total patches tested: {global_total}"
    print(msg)
    log.write(msg + "\n")
    msg = f"Successful patches: {global_success}"
    print(msg)
    log.write(msg + "\n")
    msg = f"Failed patches: {global_total - global_success}"
    print(msg)
    log.write(msg + "\n")