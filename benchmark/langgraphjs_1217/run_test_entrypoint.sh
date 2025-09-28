#!/bin/bash
set -ex

# The code repository is located at /app/source_code_buggy
CODE_DIR="/app/source_code_buggy"
# The test environment with our script and configs is at /opt/test-env
TEST_DIR="/opt/test-env"

# This function runs the test.
run_test() {
    echo "--- Running Test ---"
    
    # Navigate to the test directory
    cd "${TEST_DIR}"

    # Use Jest to run the test script.
    # The return value of this command will be used to determine the outcome.
    npx jest
}

# Main control flow
case "$1" in
    test_buggy)
        echo "=== Testing BUGGY Version (Commit: ${BUGGY_COMMIT}) ==="
        cd "${CODE_DIR}"
        git -c advice.detachedHead=false checkout "${BUGGY_COMMIT}" --force
        
        # In the buggy version, we EXPECT the test to pass because the
        # repro_script.ts is designed to catch the specific error.
        if run_test; then
            echo
            echo "✅ REPRODUCTION SUCCESSFUL"
            echo "The test suite PASSED, which correctly indicates that the expected 'bindTools' error was successfully caught and verified."
        else
            echo
            echo "❌ REPRODUCTION FAILED"
            echo "The test suite FAILED. This is unexpected and means either the bug was not triggered or a different error occurred."
        fi
        ;;
    test_fixed)
        if [ -z "${FIXED_COMMIT}" ]; then
            echo "ERROR: FIXED_COMMIT not set."
            exit 1
        fi
        echo "=== Testing FIXED Version (Commit: ${FIXED_COMMIT}) ==="
        cd "${CODE_DIR}"
        git -c advice.detachedHead=false checkout "${FIXED_COMMIT}" --force
        
        # In the fixed version, we EXPECT the test to fail because the
        # repro_script.ts will no longer catch the 'bindTools' error,
        # and its 'fail()' call will be triggered.
        if run_test; then
            echo
            echo "❌ VERIFICATION FAILED"
            echo "The test suite PASSED. This is unexpected for the fixed version and may indicate the bug is still present."
        else
            echo
            echo "✅ VERIFICATION SUCCESSFUL"
            echo "The test suite FAILED as expected for the fixed version, because the 'bindTools' error was no longer thrown."
        fi
        ;;
    *)
        echo "Usage: docker run <image_name> [test_buggy|test_fixed]"
        ;;
esac