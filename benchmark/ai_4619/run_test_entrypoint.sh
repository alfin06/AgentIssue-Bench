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
    
    echo "--- Running Test for ${version} version ---"
    cd "${code_dir}"
    
    if [ -f "${REPRO_SCRIPT_JS}" ]; then
        echo "Found reproduce.js. Executing with node..."
        if VERSION="${version}" NODE_PATH="${code_dir}/node_modules" ${NODE_CMD} "${REPRO_SCRIPT_JS}"; then
            echo "--- Test script executed successfully (exit code 0) ---"
            if [ "${version}" == "fixed" ]; then
                echo "✅ FIX VERIFIED: The issue has been fixed."
                exit 0
            else
                echo "❌ BUG NOT REPRODUCED: The test did not detect the issue in the buggy version."
                exit 1
            fi
        else
            local exit_code=$?
            echo "--- Test script exited with code ${exit_code} ---"
            if [ "${version}" == "buggy" ] || [ "${version}" == "patched" ]; then
                echo "✅ BUG REPRODUCED: The issue was successfully detected in the ${version} version."
                exit 0
            else
                echo "❌ FIX NOT VERIFIED: The issue still exists in the fixed version."
                exit 1
            fi
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
            
            # Rebuild after applying the patch
            echo "Rebuilding with applied patch..."
            pnpm build
            if [ $? -eq 0 ]; then
                echo "✅ Build successful. You can now run 'test_patched' to test your patch."
            else
                echo "❌ Build failed after applying patch."
                exit 1
            fi
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
        echo "  bash             Start a bash shell"
        echo "  help             Show this help message"
        echo ""
        if [ "$1" != "help" ] && [ ! -z "$1" ]; then exit 1; fi
        ;;
esac

exit $?