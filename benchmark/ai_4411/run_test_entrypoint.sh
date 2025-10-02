#!/bin/bash
set -eo pipefail

NODE_CMD="${NODE_CMD:-node}"
REPRO_SCRIPT_JS="/opt/reproduce.js"

run_test() {
    local version=$1
    local code_dir
    if [ "${version}" == "buggy" ] || [ "${version}" == "patched" ]; then
        code_dir="/app/source_code_buggy"
    else
        code_dir="/app/source_code_fixed"
    fi

    cd "${code_dir}"

    echo "--- Running Test for ${version} version ---"
    if [ -f "${REPRO_SCRIPT_JS}" ]; then
        echo "Found reproduce.js. Executing with node..."
        VERSION="${version}" ${NODE_CMD} "${REPRO_SCRIPT_JS}"
        local exit_code=$?
        echo "--- Test script executed with exit code ${exit_code} ---"
        
        if [ ${exit_code} -eq 0 ]; then
            if [ "${version}" == "buggy" ] || [ "${version}" == "patched" ]; then
                echo "✅ BUG REPRODUCED: Parameter description is lost for optional fields."
            else
                echo "✅ FIX VERIFIED: Parameter description is preserved for optional fields."
            fi
            exit 0
        else
            if [ "${version}" == "buggy" ] || [ "${version}" == "patched" ]; then
                echo "❌ BUG NOT REPRODUCED: Parameter description was preserved (unexpected for buggy version)."
            else
                echo "❌ FIX NOT VERIFIED: Parameter description is still lost in fixed version."
            fi
            exit 1
        fi
    else
        echo "--- FATAL ERROR: No reproduce.js found! ---"
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
        echo "=== Applying patch to buggy version ==="
        cd /app/source_code_buggy
        
        # Check if the patch file exists
        if [ ! -f "$2" ]; then
            echo "❌ ERROR: Patch file $2 not found!"
            exit 1
        fi
        
        # Apply the patch
        echo "Applying patch from $2..."
        if patch -p1 < "$2"; then
            echo "✅ Patch applied successfully."
            echo "Rebuilding with applied patch..."
            npm install
            npm run build
            echo "✅ You can now run 'test_patched' to test your patch."
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
    bash)
        echo "Entering bash shell. Code at /app/source_code_buggy and /app/source_code_fixed"
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