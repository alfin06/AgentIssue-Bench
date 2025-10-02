#!/bin/bash
set -eo pipefail

REPRO_SCRIPT="/opt/reproduce.js"
METADATA_FILE="/opt/metadata.json"

if [ -f "$METADATA_FILE" ]; then
    export BUGGY_COMMIT=$(node -p "require('$METADATA_FILE').buggy_commit")
    export FIXED_COMMIT=$(node -p "require('$METADATA_FILE').fixed_commit")
else
    echo "FATAL: metadata.json not found!"
    exit 1
fi

run_test() {
    local version=$1
    local CODE_DIR
    if [ "$version" == "buggy" ] || [ "$version" == "patched" ]; then
        CODE_DIR="/app/source_code_buggy"
    else
        CODE_DIR="/app/source_code_fixed"
    fi
    cd "${CODE_DIR}"
    VERSION="${version}" node "${REPRO_SCRIPT}"
    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
        if [ "$version" == "buggy" ]; then
            echo "✅ BUG SUCCESSFULLY REPRODUCED: Evo does not explain its personas or expertise."
        elif [ "$version" == "patched" ]; then
            echo "✅ PATCH SUCCESSFULLY VERIFIED: Evo now explains its personas and expertise."
        else
            echo "✅ FIX CONFIRMED: Evo now explains its personas and expertise."
        fi
        return 0
    else
        if [ "$version" == "buggy" ]; then
            echo "❌ BUG NOT REPRODUCED: Evo explainer or persona expertise found in buggy version."
        elif [ "$version" == "patched" ]; then
            echo "❌ PATCH NOT VERIFIED: Evo explainer or persona expertise missing after patch."
        else
            echo "❌ FIX NOT VERIFIED: Evo explainer or persona expertise missing in fixed version."
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
    bash)
        /bin/bash
        ;;
    help|*)
        echo "Usage: docker run [OPTIONS] IMAGE [COMMAND]"
        echo "  test_buggy       Test if the bug exists in the buggy version"
        echo "  test_fixed       Test if the fix works in the fixed version"
        echo "  test_patched     Test the buggy version with your applied patch"
        echo "  apply_patch      Apply a patch file to the buggy version"
        echo "  bash             Start a bash shell"
        echo "  help             Show this help message"
        ;;
esac

exit $?