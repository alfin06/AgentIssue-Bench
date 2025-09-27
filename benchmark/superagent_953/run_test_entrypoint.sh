#!/bin/bash
# filepath: d:\Projects\AgentIssue-Bench\reproduction_workspace\failure_triggering_tests\superagent_953\run_test_entrypoint.sh
set -eo pipefail

# Define paths for test script
PYTHON_CMD="${PYTHON_CMD:-python3}"
REPRO_SCRIPT_PY="/opt/reproduce.py"

run_test() {
    local version=$1
    echo "--- Running Test for ${version} version ---"
    
    if [ "$version" == "buggy" ] || [ "$version" == "patched" ]; then
        SOURCE_DIR="/app/source_code_buggy"
    else
        SOURCE_DIR="/app/source_code_fixed"
    fi
    
    cd "${SOURCE_DIR}"
    
    # Check if Python is available and script exists
    if command -v ${PYTHON_CMD} &> /dev/null && [ -f "${REPRO_SCRIPT_PY}" ]; then
        echo "Found reproduce.py and Python. Executing with python..."
        ${PYTHON_CMD} "${REPRO_SCRIPT_PY}" "${version}" "${SOURCE_DIR}" | tee /tmp/test_output.log
        local exit_code=${PIPESTATUS[0]}
        
        if [ $exit_code -eq 0 ]; then
            if grep -q "BUG REPRODUCED" /tmp/test_output.log && [ "$version" == "buggy" ]; then
                echo "✅ SUCCESS: Bug reproduced in buggy version"
                return 0
            elif grep -q "FIX CONFIRMED" /tmp/test_output.log && [ "$version" != "buggy" ]; then
                echo "✅ SUCCESS: Fix working in ${version} version"
                return 0
            else
                echo "❓ INDETERMINATE: Test completed but no clear bug status found"
                return 1
            fi
        else
            echo "❌ TEST FAILED: Script returned exit code $exit_code"
            return 1
        fi
    else
        # Fallback to shell-based test if Python is not available or script not found
        echo "Python or reproduce.py not found. Running shell-based test..."
        if [ "$version" == "buggy" ]; then
            test_buggy_shell
        else
            test_fixed_shell
        fi
    fi
}

test_buggy_shell() {
    echo "Testing buggy version (v0.2.28)..."
    cd /app/source_code_buggy/ui
    
    # Check if package.json exists and has the supabase:docker:push script
    if [ -f "package.json" ]; then
        echo "Checking package.json for supabase script..."
        if grep -q "supabase:docker:push" package.json; then
            echo "Found supabase:docker:push script in package.json"
            
            # Check if supabase is in dependencies or devDependencies
            if grep -q '"supabase":' package.json; then
                echo "❌ UNEXPECTED: supabase is listed in dependencies"
                return 1
            else
                echo "✅ BUG REPRODUCED: supabase command used but not listed in dependencies"
                return 0
            fi
        else
            echo "❌ UNEXPECTED: supabase:docker:push script not found in package.json"
            return 1
        fi
    else
        echo "❌ ERROR: package.json not found"
        return 1
    fi
}

test_fixed_shell() {
    echo "Testing fixed version..."
    cd /app/source_code_fixed/ui
    
    # Check if package.json exists and has the supabase:docker:push script
    if [ -f "package.json" ]; then
        echo "Checking package.json for supabase script..."
        
        # Check if supabase is in dependencies or devDependencies
        if grep -q '"supabase":' package.json; then
            echo "✅ FIX CONFIRMED: supabase is now listed in dependencies"
            return 0
        elif ! grep -q "supabase:docker:push" package.json; then
            echo "✅ FIX CONFIRMED: supabase:docker:push script removed or modified"
            return 0
        else
            echo "❌ FAILURE: Fix not confirmed - supabase still not in dependencies"
            return 1
        fi
    else
        echo "❌ ERROR: package.json not found"
        return 1
    fi
}

# Function to apply a patch to the buggy version
apply_patch() {
    local patch_file=$1
    
    if [ ! -f "$patch_file" ]; then
        echo "Error: Patch file not found at $patch_file"
        exit 1
    fi
    
    echo "Applying patch to buggy version..."
    
    # Set the source dir to the buggy version
    local source_dir="/app/source_code_buggy"
    cd "${source_dir}"
    
    echo "Applying patch from $patch_file..."
    patch -p1 < "$patch_file"
    
    if [ $? -eq 0 ]; then
        echo "✅ Patch applied successfully"
    else
        echo "❌ Failed to apply patch"
        exit 1
    fi
}

case "$1" in
    test_buggy)
        echo "=== Testing BUGGY Version (Commit: ${BUGGY_COMMIT}) ==="
        cd "/app/source_code_buggy"
        git -c advice.detachedHead=false checkout "${BUGGY_COMMIT}" --force
        run_test "buggy"
        ;;
    test_fixed)
        if [ -z "${FIXED_COMMIT}" ] || [ "${FIXED_COMMIT}" == "N/A" ]; then
            echo "ERROR: FIXED_COMMIT not set." >&2; exit 1;
        fi
        echo "=== Testing FIXED Version (Commit: ${FIXED_COMMIT}) ==="
        cd "/app/source_code_fixed"
        git -c advice.detachedHead=false checkout "${FIXED_COMMIT}" --force
        run_test "fixed"
        ;;
    apply_patch)
        if [ -z "$2" ]; then
            echo "Error: Patch file path required"
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
        if [ -z "${FIXED_COMMIT}" ] || [ "${FIXED_COMMIT}" == "N/A" ]; then
             echo "ERROR: FIXED_COMMIT not set." >&2; exit 1;
        fi
        echo "=== Diff between BUGGY (${BUGGY_COMMIT}) and FIXED (${FIXED_COMMIT}) ==="
        cd "/app/source_code_buggy"
        git diff "${BUGGY_COMMIT}" "${FIXED_COMMIT}" -- ui/package.json
        ;;
    inspect_buggy)
        echo "Setting up buggy environment (commit: ${BUGGY_COMMIT})..."
        cd "/app/source_code_buggy"
        git -c advice.detachedHead=false checkout "${BUGGY_COMMIT}" --force
        echo "Use 'docker exec -it <container_id> bash' to explore."
        tail -f /dev/null
        ;;
    bash)
        echo "Entering bash shell. Use 'cd /app/source_code_buggy' or 'cd /app/source_code_fixed'"
        /bin/bash
        ;;
    help|*)
        echo "Usage: docker run [OPTIONS] IMAGE [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  test_buggy      Test if the bug exists in the buggy version"
        echo "  test_fixed      Test if the fix works in the fixed version"
        echo "  apply_patch     Apply a patch file to the buggy version (requires mounted volume)"
        echo "                  Example: docker run -v \$(pwd):/patches IMAGE apply_patch /patches/my_patch.patch"
        echo "  test_patched    Test the buggy version with your applied patch"
        echo "  show_diff       Show the diff between buggy and fixed versions"
        echo "  inspect_buggy   Keep container running for inspection of the buggy version"
        echo "  bash            Start a bash shell"
        echo "  help            Show this help message"
        if [ "$1" != "help" ] && [ ! -z "$1" ]; then exit 1; fi
        ;;
esac

exit $?