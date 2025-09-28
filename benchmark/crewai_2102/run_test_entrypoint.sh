#!/bin/bash
set -eo pipefail

# This is the universal test runner for a benchmark image. It handles
# checking out code, applying patches, and running tests for Python projects.

CODE_DIR="/app/source_code_buggy"
REPRO_SCRIPT_PY="/opt/reproduce.py"

# This function runs the test. The calling context will interpret its exit code.
run_test() {
    echo "--- Running Test ---"
    
    if [ -f "${REPRO_SCRIPT_PY}" ]; then
        echo "Found reproduce.py. Executing with python..."
        # Execute the script. We pass the exit code up to the caller.
        python "${REPRO_SCRIPT_PY}"
    else
        echo "--- FATAL ERROR: No reproduction script found! ---"
        exit 127
    fi
}

# Main execution logic
case "$1" in
    test_buggy)
        echo "=== Testing BUGGY Version (Commit: ${BUGGY_COMMIT}) ==="
        cd "${CODE_DIR}"
        git -c advice.detachedHead=false checkout "${BUGGY_COMMIT}" --force
        pip install -e . # Ensure correct version is installed
        
        if run_test; then
            echo "--- Test script PASSED (exit 0), but was expected to FAIL. ---"
            echo "❌ FAILURE: The bug was NOT reproduced."
            exit 1
        else
            echo "--- Test script FAILED (non-zero exit) as expected. ---"
            echo "✅ SUCCESS: The bug was reproduced."
            exit 0
        fi
        ;;
    test_fixed)
        if [ -z "${FIXED_COMMIT}" ] || [ "${FIXED_COMMIT}" == "N/A" ]; then
            echo "ERROR: FIXED_COMMIT not set." >&2; exit 1;
        fi
        echo "=== Testing FIXED Version (Commit: ${FIXED_COMMIT}) ==="
        cd "${CODE_DIR}"
        git -c advice.detachedHead=false checkout "${FIXED_COMMIT}" --force
        pip install -e . # Re-install the fixed version
        
        if run_test; then
            echo "--- Test script PASSED (exit 0) as expected. ---"
            echo "✅ SUCCESS: The fix is confirmed."
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
        if run_test; then
            echo "--- Test script PASSED (exit 0) as expected. ---"
            echo "✅ SUCCESS: The patch successfully fixed the bug."
            exit 0
        else
            echo "--- Test script FAILED (non-zero exit), but was expected to PASS. ---"
            echo "❌ FAILURE: The patch did not fix the bug."
            exit 1
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
        echo "  test_buggy                Run the test against the original buggy code."
        echo "  test_fixed                Run the test against the official fixed code."
        echo "  show_diff                 Show the official code changes between the buggy and fixed commits."
        echo "  apply_patch <PATCH_FILE>  Apply a patch file to the buggy code and keep the container running."
        echo "  test_patched              Run the test on the code that was previously patched by 'apply_patch'."
        echo "  inspect_buggy             Start the container with the buggy code for interactive inspection."
        echo "  bash                      Start a bash shell in the buggy environment."
        echo "  help                      Show this help message."
        if [ "$1" != "help" ] && [ ! -z "$1" ]; then exit 1; fi
        ;;
esac

