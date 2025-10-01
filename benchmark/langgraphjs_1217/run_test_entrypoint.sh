#!/bin/bash
set -ex

# The code repository is located at /app/source_code_buggy
CODE_DIR="/app/source_code_buggy"
# The test environment with our script and configs is at /opt/test-env
TEST_DIR="/opt/test-env"

# This function runs the test.
run_test() {
    local version=$1
    echo "--- Running Test for ${version} version ---"
    
    # Set an environment variable so the test knows which version it's testing
    export TEST_VERSION="${version}"
    
    # Navigate to the test directory
    cd "${TEST_DIR}"

    # Use Jest to run the test script.
    npx jest
    return $?
}

# Main control flow
case "$1" in
    test_buggy)
        echo "=== Testing BUGGY Version (Commit: ${BUGGY_COMMIT}) ==="
        cd "${CODE_DIR}"
        git -c advice.detachedHead=false checkout "${BUGGY_COMMIT}" --force
        
        # For the buggy version, we expect the test to PASS because it catches the expected error
        if run_test "buggy"; then
            echo
            echo "✅ BUG REPRODUCED: The test passed, correctly detecting the bindTools error."
            exit 0  # Success for test_buggy means we reproduced the bug
        else
            echo
            echo "❌ BUG NOT REPRODUCED: The test failed, meaning the bindTools error wasn't detected."
            exit 1
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
        
        # For the fixed version, we also expect the test to PASS, but for a different reason
        if run_test "fixed"; then
            echo
            echo "✅ FIX VERIFIED: The test passed, confirming the bindTools error is fixed."
            exit 0  # Success for test_fixed means the fix worked
        else
            echo
            echo "❌ FIX FAILED: The test failed, meaning the fix didn't work."
            exit 1
        fi
        ;;
    apply_patch)
        PATCH_FILE="$2"
        if [ -z "$PATCH_FILE" ] || [ ! -f "$PATCH_FILE" ]; then
            echo "ERROR: Patch file not found or not specified: $PATCH_FILE"
            exit 1
        fi
        
        echo "=== Applying Patch to Buggy Version (Commit: ${BUGGY_COMMIT}) ==="
        cd "${CODE_DIR}"
        git -c advice.detachedHead=false checkout "${BUGGY_COMMIT}" --force
        
        # Apply the patch file to the buggy version
        echo "Applying patch: $PATCH_FILE"
        if git apply "$PATCH_FILE"; then
            echo "✅ Patch applied successfully."
            exit 0
        else
            echo "❌ Failed to apply patch."
            exit 1
        fi
        ;;
    test_patched)
        echo "=== Testing PATCHED Version (Buggy + Patch) ==="
        cd "${CODE_DIR}"
        
        # For the patched version, we expect the test to PASS because the patch should fix the issue
        if run_test "fixed"; then
            echo
            echo "✅ PATCH VERIFIED: The test passed, confirming the patch fixes the bindTools error."
            exit 0
        else
            echo
            echo "❌ PATCH FAILED: The test failed, meaning the patch didn't work."
            exit 1
        fi
        ;;
    show_diff)
        if [ -z "${FIXED_COMMIT}" ]; then
            echo "ERROR: FIXED_COMMIT not set."
            exit 1
        fi
        echo "=== Showing Diff Between Buggy and Fixed Commits ==="
        cd "${CODE_DIR}"
        git -c advice.detachedHead=false checkout "${BUGGY_COMMIT}" --force
        echo
        echo "--- Diff between ${BUGGY_COMMIT} and ${FIXED_COMMIT} ---"
        git diff "${BUGGY_COMMIT}" "${FIXED_COMMIT}"
        exit 0
        ;;
    *)
        echo "Usage: docker run <image_name> [test_buggy|test_fixed|apply_patch <path>|test_patched|show_diff]"
        exit 1
        ;;
esac