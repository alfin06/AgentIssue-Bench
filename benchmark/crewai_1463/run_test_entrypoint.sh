#!/bin/bash
set -eo pipefail

# Define paths for test script
REPRO_SCRIPT_PY="/opt/reproduce.py"

run_test() {
    local version=$1
    echo "--- Running Test for ${version} version ---"
    
    # Install setuptools for pkg_resources
    pip install setuptools
    
    if [ "$version" == "buggy" ]; then
        CODE_DIR="/app/source_code_buggy"
        export PYTHONPATH="${CODE_DIR}:${PYTHONPATH}"
    else
        CODE_DIR="/app/source_code_fixed"
        # Reinstall the fixed version
        cd ${CODE_DIR}
        pip install -e .
        export PYTHONPATH="${CODE_DIR}:${PYTHONPATH}"
    fi
    
    cd "${CODE_DIR}"
    
    # Execute the Python test script with the version parameter
    if [ -f "${REPRO_SCRIPT_PY}" ]; then
        echo "Found reproduce.py. Executing with python..."
        python "${REPRO_SCRIPT_PY}" "$version"
        local exit_code=$?
        
        if [ $exit_code -eq 0 ]; then
            if [ "$version" == "buggy" ]; then
                echo "✅ BUG SUCCESSFULLY REPRODUCED: Flow @listen with and_() does not execute"
                return 0
            else
                echo "✅ FIX CONFIRMED: Flow @listen with and_() executes correctly"
                return 0
            fi
        else
            if [ "$version" == "buggy" ]; then
                echo "❌ BUG NOT REPRODUCED: Flow @listen with and_() executes correctly"
                return 1
            else
                echo "❌ FIX NOT CONFIRMED: Flow @listen with and_() still doesn't execute"
                return 1
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
        echo "=== Testing FIXED Version (Commit: ${FIXED_COMMIT}) ==="
        run_test "fixed"
        ;;
    show_diff)
        echo "=== Diff between BUGGY (${BUGGY_COMMIT}) and FIXED (${FIXED_COMMIT}) ==="
        cd /app/source_code_buggy
        git diff "${BUGGY_COMMIT}" "${FIXED_COMMIT}" -- "crewai/flow/"
        ;;
    inspect_buggy)
        echo "Entering buggy environment (commit: ${BUGGY_COMMIT})..."
        cd /app/source_code_buggy
        export PYTHONPATH="/app/source_code_buggy:${PYTHONPATH}"
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