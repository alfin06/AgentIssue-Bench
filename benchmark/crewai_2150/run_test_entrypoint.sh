#!/bin/bash
set -eo pipefail

CODE_DIR="/app/source_code_buggy"
REPRO_SCRIPT_PY="/opt/reproduce.py"

# This function runs the test.
run_test() {
    local version_to_test=$1
    echo "--- Running Test ---"
    
    if [ -f "${REPRO_SCRIPT_PY}" ]; then
        echo "Found reproduce.py. Executing with python..."
        # We pass the version ('buggy' or 'fixed') as an argument to the python script
        # The script's exit code will tell us if the test passed or failed.
        if python "${REPRO_SCRIPT_PY}" "${version_to_test}"; then
            return 0 # Python script exited 0. For our logic, this means PASS.
        else
            return 1 # Python script exited non-zero. For our logic, this means FAIL.
        fi
    else
        echo "--- FATAL ERROR: No reproduction script found! ---"
        exit 127
    fi
}

# Main execution logic
case "$1" in
    test_buggy)
        CODE_DIR="/app/source_code_buggy"
        echo "=== Testing BUGGY Version (Commit: ${BUGGY_COMMIT}) ==="
        cd "${CODE_DIR}"
        git -c advice.detachedHead=false checkout "${BUGGY_COMMIT}" --force
        pip install -e . # Reinstall dependencies for the buggy version

        # For the buggy version, we expect the test script to FAIL (exit 1)
        if run_test "buggy"; then
            echo "--- Test script PASSED (exit 0), but was expected to FAIL. ---"
            echo "❌ FAILURE: The bug was NOT reproduced."
            exit 1
        else
            echo "--- Test script FAILED (non-zero exit) as expected. ---"
            echo "✅ BUG REPRODUCED: The bug was reproduced. APIStatusError.__init__() found. "
            exit 0
        fi
        ;;
    test_fixed)
        CODE_DIR="/app/source_code_fixed"
        if [ -z "${FIXED_COMMIT}" ] || [ "${FIXED_COMMIT}" == "N/A" ]; then
            echo "ERROR: FIXED_COMMIT not set." >&2; exit 1;
        fi
        echo "=== Testing FIXED Version (Commit: ${FIXED_COMMIT}) ==="
        cd "${CODE_DIR}"
        git -c advice.detachedHead=false checkout "${FIXED_COMMIT}" --force
        pip install -e . # Re-install the project from the fixed source

        # For the fixed version, we expect the test script to PASS (exit 0)
        if run_test "fixed"; then
            echo "--- Test script PASSED (exit 0) as expected. ---"
            echo "✅ FIX VERIFIED: The fix is confirmed."
            exit 0
        else
            echo "--- Test script FAILED (non-zero exit), but was expected to PASS. ---"
            echo "❌ FAILURE: The fix did not work."
            exit 1
        fi
        ;;
    apply_patch)
        PATCH_FILE=$2
        if [ -z "$PATCH_FILE" ] || [ ! -f "$PATCH_FILE" ]; then
            echo "Error: Patch file not found at '$PATCH_FILE'" >&2
            echo "Usage: docker run -v \$(pwd)/my.patch:${PATCH_FILE} IMAGE apply_patch ${PATCH_FILE}" >&2
            exit 1
        fi
        echo "=== Applying patch from ${PATCH_FILE} to BUGGY version ==="
        cd "${CODE_DIR}"
        echo "1. Checking out buggy commit..."
        git -c advice.detachedHead=false checkout "${BUGGY_COMMIT}" --force
        echo "2. Applying patch..."
        git apply "${PATCH_FILE}"
        echo "3. Re-installing patched project..."
        pip install -e .
        echo "✅ Patch applied and project re-installed. You can now run 'test_patched'."
        # Keep the container running for the user to exec into
        echo "Container is running. Use 'docker exec -it <container_id> bash' or 'docker exec <container_id> run_test_entrypoint.sh test_patched'."
        tail -f /dev/null
        ;;
    test_patched)
        echo "=== Testing PATCHED Version ==="
        # Assumes the user has already run 'apply_patch'
        cd "${CODE_DIR}"
        # Pass "patched" to the run_test function
        if run_test "patched"; then
            echo "--- Test script PASSED (exit 0), but was expected to FAIL (as bug should be fixed). ---"
            echo "❌ FAILURE: The patch did not work."
            exit 1
        else
            echo "--- Test script FAILED (non-zero exit) as expected. ---"
            echo "✅ SUCCESS: The patch successfully fixed the bug."
            exit 0
        fi
        ;;
    show_diff)
        if [ -z "${FIXED_COMMIT}" ] || [ "${FIXED_COMMIT}" == "N/A" ]; then
            echo "ERROR: FIXED_COMMIT not set." >&2; exit 1;
        fi
        echo "=== Diff between BUGGY (${BUGGY_COMMIT}) and FIXED (${FIXED_COMMIT}) ==="
        cd "${CODE_DIR}"
        # We fetch the fixed commit to ensure it's available for diffing
        git fetch origin "${FIXED_COMMIT}"
        git diff "${BUGGY_COMMIT}" "${FIXED_COMMIT}" --
        ;;
    inspect_buggy)
        echo "Entering buggy environment (commit: ${BUGGY_COMMIT})..."
        cd "${CODE_DIR}"
        git -c advice.detachedHead=false checkout "${BUGGY_COMMIT}" --force
        pip install -e .
        echo "Use 'docker exec -it <container_id> bash' to explore."
        tail -f /dev/null
        ;;
    bash)
        echo "Entering bash shell in buggy environment..."
        cd "${CODE_DIR}"
        git -c advice.detachedHead=false checkout "${BUGGY_COMMIT}" --force
        pip install -e .
        /bin/bash
        ;;
    help|*)
        echo "Usage: docker run [OPTIONS] IMAGE [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  test_buggy           Run the test against the original buggy code."
        echo "  test_fixed           Run the test against the official fixed code."
        echo "  show_diff            Show the official code changes between the buggy and fixed commits."
        echo "  apply_patch <FILE>   Apply a patch file to the buggy code and keep the container running."
        echo "  test_patched         Run the test on the code that was previously patched by 'apply_patch'."
        echo "  inspect_buggy        Start the container with the buggy code for interactive inspection."
        echo "  bash                 Start a bash shell in the buggy environment."
        echo "  help                 Show this help message."
        if [ "$1" != "help" ] && [ ! -z "$1" ]; then exit 1; fi
        ;;
esac