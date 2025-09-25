#!/bin/bash
set -ex

# The code repository is located at /app
CODE_DIR="/app"
# The test script is at /opt/repro_script.py
REPRO_SCRIPT_PATH="/opt/repro_script.py"

# This function runs the test.
run_test() {
    echo "--- Running Test ---"
    
    # This is the key fix: Move to a neutral directory before running the test.
    # This ensures Python uses the globally installed 'mle' package from site-packages
    # instead of the local source files in /app, which resolves the import error.
    cd /
    
    # Execute the script using the system's python.
    python "${REPRO_SCRIPT_PATH}"
}

# Main control flow
case "$1" in
    test_buggy)
        echo "=== Testing BUGGY Version (Commit: ${BUGGY_COMMIT}) ==="
        cd "${CODE_DIR}"
        git -c advice.detachedHead=false checkout "${BUGGY_COMMIT}" --force
        
        # Re-install dependencies and the project itself in case they changed between commits
        pip install -r requirements.txt
        pip install .
        
        # In the buggy version, we EXPECT the test to pass (exit code 0),
        # which means the JSONDecodeError was successfully caught.
        if run_test; then
            echo
            echo "✅ REPRODUCTION SUCCESSFUL"
            echo "The bug was reproduced, which correctly indicates that the expected JSONDecodeError was caught."
        else
            echo
            echo "❌ REPRODUCTION FAILED"
            echo "The bug was not reproduced. This means the bug was not triggered as expected."
        fi
        ;;
    test_fixed)
        if [ -z "${FIXED_COMMIT}" ]; then
            echo "ERROR: FIXED_COMMIT not set." >&2; exit 1;
        fi
        echo "=== Testing FIXED Version (Commit: ${FIXED_COMMIT}) ==="
        cd "${CODE_DIR}"
        git -c advice.detachedHead=false checkout "${FIXED_COMMIT}" --force
        
        # Re-install dependencies and the project itself
        pip install -r requirements.txt
        pip install .
        
        # In the fixed version, we EXPECT the test to fail (exit code 1),
        # because the JSONDecodeError will no longer be raised.
        if run_test; then
            echo
            echo "❌ VERIFICATION FAILED"
            echo "The test suite PASSED. This is unexpected for the fixed version and may indicate the bug is still present."
        else
            echo
            echo "✅ VERIFICATION SUCCESSFUL"
            echo "The test suite FAILED as expected for the fixed version, because the JSONDecodeError was no longer thrown."
        fi
        ;;
    *)
        echo "Usage: docker run <image_name> [test_buggy|test_fixed]"
        ;;
esac
