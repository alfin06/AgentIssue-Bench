#!/bin/bash
set -eo pipefail

# Store script paths
REPRO_SCRIPT_JS="/opt/reproduce.js"
METADATA_FILE="/opt/metadata.json"

# Load commit hashes from the metadata file if it exists
if [ -f "$METADATA_FILE" ]; then
    export BUGGY_COMMIT=$(node -p "require('$METADATA_FILE').buggy_commit")
    export FIXED_COMMIT=$(node -p "require('$METADATA_FILE').fixed_commit")
fi

run_test() {
    local version=$1
    echo "--- Running Test for ${version} version ---"
    
    # Set the VERSION environment variable for the Node.js script
    VERSION="${version}" node "${REPRO_SCRIPT_JS}"
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        if [ "$version" == "buggy" ]; then
            echo "✅ BUG SUCCESSFULLY REPRODUCED: DataCloneError occurs with Vue proxies."
        elif [ "$version" == "patched" ]; then
            echo "✅ PATCH SUCCESSFULLY VERIFIED: DataCloneError no longer occurs with Vue proxies."
        else
            echo "✅ FIX CONFIRMED: DataCloneError no longer occurs with Vue proxies."
        fi
        return 0
    else
        if [ "$version" == "buggy" ]; then
            echo "❌ BUG NOT REPRODUCED: No DataCloneError occurred with Vue proxies."
        elif [ "$version" == "patched" ]; then
            echo "❌ PATCH NOT VERIFIED: DataCloneError still occurs with Vue proxies."
        else
            echo "❌ FIX NOT VERIFIED: DataCloneError still occurs with Vue proxies."
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
    patch -p1 < "$patch_file"
    if [ $? -eq 0 ]; then
        echo "✅ Patch applied successfully."
    else
        echo "❌ Failed to apply patch."
        exit 1
    fi
}

case "$1" in
    test_buggy)
        echo "=== Testing BUGGY Version ==="
        run_test "buggy"
        ;;
    test_fixed)
        echo "=== Testing FIXED Version ==="
        run_test "fixed"
        ;;
    test_patched)
        echo "=== Testing PATCHED Version (Buggy + Your Patch) ==="
        run_test "patched"
        ;;
    apply_patch)
        if [ -z "$2" ]; then
            echo "Usage: docker run -v \$(pwd):/patches IMAGE apply_patch /patches/my_patch.patch"
            exit 1
        fi
        apply_patch "$2"
        ;;
    show_diff)
        echo "=== Diff between BUGGY and FIXED ==="
        if [ -n "${BUGGY_COMMIT}" ] && [ -n "${FIXED_COMMIT}" ]; then
            git diff "${BUGGY_COMMIT}" "${FIXED_COMMIT}"
        else
            echo "❌ Cannot show diff: commit hashes not found in metadata.json"
        fi
        ;;
    bash)
        echo "Entering bash shell"
        /bin/bash
        ;;
    help|*)
        echo "Usage: docker run [OPTIONS] IMAGE [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  test_buggy       Test if the bug exists in the buggy version"
        echo "  test_fixed       Test if the fix works in the fixed version"
        echo "  test_patched     Test the buggy version with your applied patch"
        echo "  apply_patch      Apply a patch file to the buggy version"
        echo "  show_diff        Show the git diff between buggy and fixed versions"
        echo "  bash             Start a bash shell"
        echo "  help             Show this help message"
        echo ""
        if [ "$1" != "help" ] && [ ! -z "$1" ]; then exit 1; fi
        ;;
esac

exit $?