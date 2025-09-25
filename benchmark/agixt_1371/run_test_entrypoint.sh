#!/bin/bash
# filepath: d:\Projects\AgentIssue-Bench\reproduction_workspace\failure_triggering_tests\agixt_1371\run_test_entrypoint.sh
set -eo pipefail

# Define paths for potential test scripts inside the container
REPRO_SCRIPT_PY="/opt/repro_script.py"

run_test() {
    local version=$1
    echo "--- Running Test for ${version} version ---"
    
    if [ "$version" == "buggy" ]; then
        CODE_DIR="/app/source_code_buggy"
        export PYTHONPATH="/app/source_code_buggy:$PYTHONPATH"
    else
        CODE_DIR="/app/source_code_fixed"
        export PYTHONPATH="/app/source_code_fixed:$PYTHONPATH"
    fi
    
    cd "${CODE_DIR}"
    
    # Execute the Python test script with the version parameter
    if [ -f "${REPRO_SCRIPT_PY}" ]; then
        echo "Found repro_script.py. Executing with python..."
        python "${REPRO_SCRIPT_PY}" "$version"
        local exit_code=$?
        
        if [ $exit_code -eq 0 ]; then
            if [ "$version" == "buggy" ]; then
                echo "✅ BUG SUCCESSFULLY REPRODUCED: Test script confirmed the bug exists."
                return 0  # Success exit code
            else
                echo "✅ FIX CONFIRMED: Test script verified the fix is working."
                return 0  # Success exit code
            fi
        else
            if [ "$version" == "buggy" ]; then
                echo "❌ BUG NOT REPRODUCED: Test script could not confirm the bug."
                return 1  # Failure exit code
            else
                echo "❌ FIX NOT CONFIRMED: Test script could not verify the fix."
                return 1  # Failure exit code
            fi
        fi
    else
        echo "--- FATAL ERROR: No reproduction script found! ---"
        echo "Looked for ${REPRO_SCRIPT_PY}"
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
    show_diff)
        if [ -z "${FIXED_COMMIT}" ] || [ "${FIXED_COMMIT}" == "N/A" ]; then
             echo "ERROR: FIXED_COMMIT not set." >&2; exit 1;
        fi
        echo "=== Diff between BUGGY (${BUGGY_COMMIT}) and FIXED (${FIXED_COMMIT}) ==="
        cd /app/source_code_buggy
        git diff "${BUGGY_COMMIT}" "${FIXED_COMMIT}" --
        ;;
    inspect_buggy)
        echo "Entering buggy environment (commit: ${BUGGY_COMMIT})..."
        cd /app/source_code_buggy
        export PYTHONPATH="/app/source_code_buggy:$PYTHONPATH"
        echo "Use 'docker exec -it <container_id> bash' to explore."
        tail -f /dev/null
        ;;
    bash)
        echo "Entering bash shell. Use 'cd /app/source_code_buggy' or 'cd /app/source_code_fixed'"
        /bin/bash
        ;;
    help|*)
        echo "Usage: docker run <image_name> [test_buggy|test_fixed|show_diff|inspect_buggy|bash|help]"
        echo ""
        echo "  test_buggy     Test if the bug exists in the buggy version"
        echo "  test_fixed     Test if the fix works in the fixed version"
        echo "  show_diff      Show the diff between the buggy and fixed versions"
        echo "  inspect_buggy  Keep container running for inspection of the buggy version"
        echo "  bash           Start a bash shell"
        echo "  help           Show this help message"
        if [ "$1" != "help" ] && [ ! -z "$1" ]; then exit 1; fi
        ;;
esac