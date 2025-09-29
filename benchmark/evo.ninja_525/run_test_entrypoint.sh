#!/bin/bash
set -eo pipefail

REPRODUCE_TS="/opt/reproduce.ts"
METADATA_FILE="/opt/metadata.json"

# Load commit hashes from the metadata file.
if [ -f "$METADATA_FILE" ]; then
    export BUGGY_COMMIT=$(node -p "require('$METADATA_FILE').buggy_commit")
    export FIXED_COMMIT=$(node -p "require('$METADATA_FILE').fixed_commit")
else
    echo "FATAL: metadata.json not found!"
    exit 1
fi

run_test() {
    local version=$1
    echo "--- Running Test for ${version} version ---"

    local CODE_DIR
    if [ "$version" == "buggy" ] || [ "$version" == "patched" ]; then
        CODE_DIR="/app/source_code_buggy"
        cd "${CODE_DIR}"
    else
        CODE_DIR="/app/source_code_fixed"
        cd "${CODE_DIR}"
        echo "Preparing fixed version..."
        yarn install > /dev/null
        yarn build --filter=@evo-ninja/agents... > /dev/null
    fi

    local REPRODUCE_TS_DEST="${CODE_DIR}/reproduce.test.ts"
    cp "${REPRODUCE_TS}" "${REPRODUCE_TS_DEST}"

    echo "Executing reproduction script with Jest..."
    # Use yarn to run the jest binary from the local node_modules.
    VERSION=${version} yarn jest "${REPRODUCE_TS_DEST}"
    local exit_code=$?
    
    rm "${REPRODUCE_TS_DEST}"

    if [ $exit_code -eq 0 ]; then
        if [ "$version" == "buggy" ]; then
            echo "✅ BUG SUCCESSFULLY REPRODUCED: The test passed, confirming the buggy behavior."
        else
            echo "✅ FIX CONFIRMED / PATCH SUCCEEDED: The test passed, confirming the correct behavior."
        fi
        return 0
    else
        if [ "$version" == "buggy" ]; then
            echo "❌ BUG NOT REPRODUCED: The test failed, but it was expected to pass."
        else
            echo "❌ FIX NOT CONFIRMED / PATCH FAILED: The test failed unexpectedly."
        fi
        return 1
    fi
}

apply_patch() {
    local patch_file=$1
    if [ ! -f "$patch_file" ]; then
        echo "Error: Patch file not found at $patch_file"
        exit 1
    fi
    echo "Applying patch to buggy version..."
    local source_dir="/app/source_code_buggy"
    cd "${source_dir}"
    patch -p1 < "$patch_file"
    if [ $? -eq 0 ]; then
        echo "✅ Patch applied successfully. Re-installing and rebuilding..."
        yarn install
        yarn build --filter=@evo-ninja/agents...
    else
        echo "❌ Failed to apply patch."
        exit 1
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
        apply_patch "$2"
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