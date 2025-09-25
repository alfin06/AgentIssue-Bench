#!/bin/bash
set -eo pipefail

# Define path for test script
reproduce_PY="/app/reproduce.py"

run_test() {
    local version=$1
    local source_dir="/app/source_code_$version"
    
    echo "--- Running Test for ${version} version ---"
    echo "Testing $version version from commit: $(cd $source_dir && git rev-parse HEAD)"
    
    # Set PYTHONPATH to include the source directory
    export PYTHONPATH="${source_dir}:${PYTHONPATH}"
    
    # Look for chain name validation in the relevant file
    echo "Checking for chain name validation in Chain.py..."
    
    # Extract and examine the create_chain method
    grep -A 50 "def create_chain" $source_dir/agixt/Chain.py | grep -B 5 -A 5 "chain_name" || true
    
    # Execute the Python test script with the version parameter
    if [ -f "${reproduce_PY}" ]; then
        echo "Running direct test script for $version version..."
        python "${reproduce_PY}" "$version"
        local exit_code=$?
        
        if [ $exit_code -eq 0 ]; then
            if [ "$version" == "buggy" ]; then
                echo "❌ BUG NOT REPRODUCED: Empty chain names are rejected (unexpected)"
                return 1  # Failure for buggy version
            elif [ "$version" == "patched" ]; then
                echo "✅ PATCH SUCCEEDED: Empty chain names are now rejected"
                return 0  # Success for patched version
            else
                echo "✅ FIX CONFIRMED: Empty chain names are rejected in fixed version"
                return 0  # Success for fixed version
            fi
        else
            if [ "$version" == "buggy" ]; then
                echo "✅ BUG REPRODUCED: Empty chain names are accepted in buggy version"
                return 0  # Success for buggy version - bug reproduced
            elif [ "$version" == "patched" ]; then
                echo "❌ PATCH FAILED: Empty chain names are still accepted"
                return 1  # Failure for patched version
            else
                echo "❌ FIX NOT CONFIRMED: Empty chain names are still accepted"
                return 1  # Failure for fixed version
            fi
        fi
    else
        echo "--- FATAL ERROR: No reproduction script found! ---"
        echo "Looked for ${reproduce_PY}"
        exit 127
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
        
        # Reinstall if needed
        echo "Reinstalling the patched package..."
        pip install --no-deps -e . || echo "Skipping reinstall (not needed)"
        
        echo "You can now test your patched version with: docker run ... test_patched"
    else
        echo "❌ Failed to apply patch"
        exit 1
    fi
}

# Function to test the patched version
test_patched() {
    echo "Testing PATCHED version (based on buggy with applied patch)"
    run_test "patched"
    return $?
}

# Main execution
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
            echo "Error: Patch file path required"
            echo "Usage: docker run -v \$(pwd):/patches IMAGE apply_patch /patches/my_patch.patch"
            exit 1
        fi
        apply_patch "$2"
        ;;
    test_patched)
        echo "=== Testing PATCHED Version (Buggy + Your Patch) ==="
        test_patched
        ;;
    show_diff)
        echo "=== Diff between BUGGY (${BUGGY_COMMIT}) and FIXED (${FIXED_COMMIT}) ==="
        cd /app/source_code_buggy
        git diff "${BUGGY_COMMIT}" "${FIXED_COMMIT}" -- agixt/
        ;;
    inspect_buggy)
        echo "Entering buggy environment (commit: ${BUGGY_COMMIT})..."
        cd /app/source_code_buggy
        export PYTHONPATH="/app/source_code_buggy:${PYTHONPATH}"
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