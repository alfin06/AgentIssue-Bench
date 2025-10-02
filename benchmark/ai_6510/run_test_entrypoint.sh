#!/bin/bash
set -eo pipefail

# This script is the universal test runner for a benchmark image.
# It intelligently runs a .sh, .py, or .js test script.

PYTHON_CMD="${PYTHON_CMD:-python}"
NODE_CMD="${NODE_CMD:-node}"

# Define paths for potential test scripts inside the container
REPRO_COMMAND_SH="/opt/repro_command.sh"
REPRO_SCRIPT_PY="/opt/reproduce.py"
REPRO_SCRIPT_JS="/opt/reproduce.js"

run_test() {
    local version=$1
    echo "--- Running Test for ${version} version ---"
    
    # Always run tests from /opt where dependencies are installed
    cd /opt
    
    # Check for shell, python, or javascript script to run
    if [ -f "${REPRO_COMMAND_SH}" ]; then
        echo "Found repro_command.sh. Executing with bash..."
        chmod +x "${REPRO_COMMAND_SH}"
        if VERSION="${version}" bash "${REPRO_COMMAND_SH}"; then
            echo "--- Test script executed successfully (exit code 0) ---"
        else
            echo "--- Test script failed (exit code $?) ---"
        fi
    elif [ -f "${REPRO_SCRIPT_PY}" ]; then
        echo "Found repro_script.py. Executing with python..."
        if VERSION="${version}" ${PYTHON_CMD} "${REPRO_SCRIPT_PY}"; then
            echo "--- Test script executed successfully (exit code 0) ---"
        else
            echo "--- Test script failed (exit code $?) ---"
        fi
    elif [ -f "${REPRO_SCRIPT_JS}" ]; then
        echo "Found repro_script.js. Executing with node..."
        if VERSION="${version}" ${NODE_CMD} "${REPRO_SCRIPT_JS}"; then
            echo "--- Test script executed successfully (exit code 0) ---"
        else
            echo "--- Test script failed (exit code $?) ---"
        fi
    else
        echo "--- FATAL ERROR: No reproduction script found! ---"
        echo "Looked for ${REPRO_COMMAND_SH}, ${REPRO_SCRIPT_PY}, and ${REPRO_SCRIPT_JS}"
        exit 127
    fi
}

case "$1" in
    test_buggy)
        echo "=== Testing BUGGY Version (Commit: ${BUGGY_COMMIT}) ==="
        run_test "buggy"
        ;;
    test_fixed)
        if [ -z "${FIXED_COMMIT}" ] || [ "${FIXED_COMMIT}" == "N/A" ]; then
            echo "ERROR: FIXED_COMMIT not set." >&2; exit 1;
        fi
        echo "=== Testing FIXED Version (Commit: ${FIXED_COMMIT}) ==="
        run_test "fixed"
        ;;
    apply_patch)
        if [ -z "$2" ]; then
            echo "Usage: docker run -v \$(pwd):/patches IMAGE apply_patch /patches/my_patch.patch"
            exit 1
        fi
        echo "Applying patch to buggy version..."
        local source_dir="/app/source_code_buggy"
        cd "${source_dir}"
        patch -p1 < "$2"
        if [ $? -eq 0 ]; then
            echo "✅ Patch applied successfully. Re-installing dependencies..."
            pnpm install
        else
            echo "❌ Failed to apply patch."
            exit 1
        fi
        ;;
    test_patched)
        echo "=== Testing PATCHED Version (Buggy + Your Patch) ==="
        run_test "patched"
        ;;
    show_diff)
        echo "=== Diff between BUGGY (${BUGGY_COMMIT}) and FIXED (${FIXED_COMMIT}) ==="
        cd /app/source_code_buggy
        git diff "${BUGGY_COMMIT}" "${FIXED_COMMIT}"
        ;;
    inspect_buggy)
        echo "Entering buggy environment (commit: ${BUGGY_COMMIT}). Use 'docker exec' to connect."
        cd /app/source_code_buggy
        tail -f /dev/null
        ;;
    bash)
        echo "Entering bash shell. Buggy code at /app/source_code_buggy, Fixed at /app/source_code_fixed"
        /bin/bash
        ;;
    help|*)
        echo "Usage: docker run [OPTIONS] IMAGE [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  test_buggy       Test if the bug exists in the buggy version"
        echo "  test_fixed       Test if the fix works in the fixed version"
        echo "  apply_patch      Apply a patch file to the buggy version"
        echo "  test_patched     Test the buggy version with your applied patch"
        echo "  show_diff        Show the git diff between buggy and fixed versions"
        echo "  inspect_buggy    Keep container running for inspection of the buggy version"
        echo "  bash             Start a bash shell"
        echo "  help             Show this help message"
        echo ""
        if [ "$1" != "help" ] && [ ! -z "$1" ]; then exit 1; fi
        ;;
esac

exit $?