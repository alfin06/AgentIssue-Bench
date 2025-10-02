#!/bin/bash
set -eo pipefail

REPRO_SCRIPT_JS="/opt/reproduce.js"
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
    else
        CODE_DIR="/app/source_code_fixed"
    fi
    
    echo "Switching to directory: ${CODE_DIR}"
    cd "${CODE_DIR}"
    echo "Current directory: $(pwd)"

    echo "Analyzing source code for the bug fix..."
    VERSION="${version}" node "${REPRO_SCRIPT_JS}"
    local exit_code=$?

    if [ $exit_code -eq 0 ]; then
        if [ "$version" == "buggy" ]; then
            echo "✅ BUG SUCCESSFULLY REPRODUCED: Source code analysis confirms the bug exists."
        else
            echo "✅ FIX CONFIRMED / PATCH SUCCEEDED: Source code analysis confirms the fix is present."
        fi
        return 0
    else
        if [ "$version" == "buggy" ]; then
            echo "❌ BUG NOT REPRODUCED: Source code analysis did not find the expected buggy pattern."
        else
            echo "❌ FIX NOT CONFIRMED / PATCH FAILED: Source code analysis did not find the fix pattern."
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
        echo "✅ Patch applied successfully."
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
        echo "  apply_patch      Apply a patch file to the buggy version"
        echo "  test_patched     Test the buggy version with your applied patch"
        echo "  show_diff        Show the git diff between buggy and fixed versions"
        echo "  bash             Start a bash shell"
        echo "  help             Show this help message"
        echo ""
        if [ "$1" != "help" ] && [ ! -z "$1" ]; then exit 1; fi
        ;;
esac

exit $?