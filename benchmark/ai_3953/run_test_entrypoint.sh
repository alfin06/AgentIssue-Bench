#!/bin/bash
set -eo pipefail

PYTHON_CMD="${PYTHON_CMD:-python}"
NODE_CMD="${NODE_CMD:-node}"

REPRO_SCRIPT_JS="/opt/reproduce.js"

run_test() {
    local version=$1
    echo "--- Running Test for ${version} version ---"
    
    # Use the correct code directory based on version
    local CODE_DIR
    if [ "${version}" == "buggy" ]; then
        CODE_DIR="/app/source_code_buggy"
    elif [ "${version}" == "patched" ]; then
        CODE_DIR="/app/source_code_buggy"
    else
        CODE_DIR="/app/source_code_fixed"
    fi
    
    cd "${CODE_DIR}"
    
    # Run the test script from /opt with VERSION environment variable
    cd /opt
    if [ -f "${REPRO_SCRIPT_JS}" ]; then
        echo "Found reproduce.js. Executing with node..."
        if VERSION="${version}" ${NODE_CMD} "${REPRO_SCRIPT_JS}"; then
            echo "--- Test script executed successfully (exit code 0) ---"
            exit 0
        else
            echo "--- Test script failed (exit code $?) ---"
            # For this test, exit code 1 is expected for the buggy version
            if [ "${version}" == "buggy" ] && [ $? -eq 1 ]; then
                echo "--- This is the expected failure for the buggy version ---"
                exit 0
            fi
            exit 1
        fi
    else
        echo "--- FATAL ERROR: No reproduction script found! ---"
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
    apply_patch)
        if [ -z "$2" ]; then
            echo "Usage: docker run -v \$(pwd):/patches IMAGE apply_patch /patches/my_patch.patch"
            exit 1
        fi
        echo "Applying patch to buggy version..."
        cd /app/source_code_buggy
        patch -p1 < "$2"
        if [ $? -eq 0 ]; then
            echo "✅ Patch applied successfully. Re-installing dependencies..."
            pnpm install
            echo "Rebuilding the patched version..."
            pnpm build
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
        git diff "${BUGGY_COMMIT}" "${FIXED_COMMIT}" --
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