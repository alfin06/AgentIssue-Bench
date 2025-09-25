#!/bin/bash
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
