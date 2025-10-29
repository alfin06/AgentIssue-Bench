import os
import subprocess

PATCHES_ROOT = "Patches"
DOCKER_IMAGE_BASE = "alfin06/agentissue-bench"
LOG_FILE = "patch_eval.log"

global_success = 0
global_total = 0
grand_total_avg = 0

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
            docker_volumes = [
                "-v", f"{os.path.dirname(patch_path)}:/patches"
            ]
            if tag == "agixt_1369":
                # Special command for agixt_1369
                cmd = [
                    "docker", "run", "--rm",
                    "--network", "host",
                    "--entrypoint", "bash",
                    *docker_volumes,
                    "-e", "OPENAI_API_KEY=api-key",
                    "-e", "OPENAI_API_BASE=api-base-url",
                    docker_image,
                    "-c", f"/usr/local/bin/run_test_entrypoint.sh apply_patch /patches/{patch_file} && /usr/local/bin/run_test_entrypoint.sh test_patched"
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
                output = result.stdout if result.stdout is not None else ""
                #print(output)
                #log.write(output + "\n")
                if "FAILED" in result.stdout or result.returncode != 0:
                    msg = f"❌ Patch {patch_file}: FAILED"
                    print(msg)
                    log.write(msg + "\n")
                    continue
                if ("PATCH SUCCEEDED" in result.stdout or 
                    "PATCH SUCCESSFULLY VERIFIED" in result.stdout or 
                    "FIX SUCCESSFULLY VERIFIED" in result.stdout or
                    "NO BUG" in result.stdout or
                    "FIX CONFIRMED" in result.stdout or
                    "PATCH VERIFIED" in result.stdout or
                    "patched succeeded" in result.stdout):
                    msg = f"✅ Patch {patch_file}: SUCCESS"
                    print(msg)
                    log.write(msg + "\n")
                    success_count += 1
                else:
                    msg = f"❌ Patch {patch_file}: FAILED"
                    print(msg)
                    log.write(msg + "\n")
            else:
                cmd = [
                    "docker", "run", "--rm",
                    "--entrypoint", "bash",
                    *docker_volumes,
                    "-e", "OPENAI_API_KEY=api-key",
                    "-e", "OPENAI_API_BASE=api-base-url",
                    docker_image,
                    "-c", f"/usr/local/bin/run_test_entrypoint.sh apply_patch /patches/{patch_file} && /usr/local/bin/run_test_entrypoint.sh test_patched"
                ]
                
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", timeout=300)
                    output = result.stdout if result.stdout is not None else ""
                    #print(output)
                    #log.write(output + "\n")
                
                    if "FAILED" in result.stdout or result.returncode != 0:
                        msg = f"❌ Patch {patch_file}: FAILED"
                        print(msg)
                        log.write(msg + "\n")
                        continue
                    
                    if ("PATCH SUCCEEDED" in result.stdout or 
                        "PATCH SUCCESSFULLY VERIFIED" in result.stdout or 
                        "FIX SUCCESSFULLY VERIFIED" in result.stdout or
                        "NO BUG" in result.stdout or
                        "FIX CONFIRMED" in result.stdout or
                        "PATCH VERIFIED" in result.stdout):
                        msg = f"✅ Patch {patch_file}: SUCCESS"
                        print(msg)
                        log.write(msg + "\n")
                        success_count += 1
                    else:
                        msg = f"❌ Patch {patch_file}: FAILED"
                        print(msg)
                        log.write(msg + "\n")
                except subprocess.TimeoutExpired:
                    msg = f"❌ Patch {patch_file}: FAILED"
                    print(msg)
                    log.write(msg + "\n")
                    container_ids = subprocess.check_output("docker ps -q", shell=True, text=True).splitlines()
                    for cid in container_ids:
                        if cid.strip():
                            subprocess.run(["docker", "rm", "-f", cid], check=False)
                    continue

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
        avg_score = success_count / total_count if total_count > 0 else 0
        msg = f"Plausible score: {avg_score:.2f}"
        print(msg)
        log.write(msg + "\n")
        grand_total_avg += avg_score
        msg = f"\n---------------------------------------------"
        print(msg)
        log.write(msg + "\n")

        global_success += success_count
        global_total += total_count

        # Remove the docker image for this tag and its containers
        subprocess.run(["docker", "rmi", "-f", docker_image], check=False)

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
    msg = f"Plausible score: {grand_total_avg:.2f}"
    print(msg)
    log.write(msg + "\n")