#!/bin/bash
set -eo pipefail

reproduce_PY="/opt/reproduce.py"

run_test() {
    local version=$1
    echo "--- Running Test for ${version} version ---"
    
    if [ "$version" == "buggy" ] || [ "$version" == "patched" ]; then
        # For buggy version, we'll use pip to install crewai directly
        # as the issue is with PyPI package and its tiktoken dependency
        cd /tmp
    else
        # For fixed version, we'll use the cloned repo
        cd /app/source_code_fixed
        export PYTHONPATH="/app/source_code_fixed:${PYTHONPATH}"
    fi
    
    # Execute the Python test script with the version parameter
    if [ -f "${reproduce_PY}" ]; then
        echo "Found reproduce.py. Executing with python..."
        python "${reproduce_PY}" "$version"
        local exit_code=$?
        
        if [ $exit_code -eq 0 ]; then
            if [ "$version" == "buggy" ]; then
                echo "✅ BUG SUCCESSFULLY REPRODUCED: tiktoken fails to build on Python 3.12+"
                return 0
            elif [ "$version" == "patched" ]; then
                echo "✅ PATCH SUCCEEDED: tiktoken now builds successfully"
                return 0
            else
                echo "✅ FIX CONFIRMED: tiktoken now builds successfully"
                return 0
            fi
        else
            if [ "$version" == "buggy" ]; then
                echo "❌ BUG NOT REPRODUCED: tiktoken built successfully (unexpected)"
                return 1
            elif [ "$version" == "patched" ]; then
                echo "❌ PATCH FAILED: tiktoken still fails to build"
                return 1
            else
                echo "❌ FIX NOT CONFIRMED: tiktoken still fails to build"
                return 1
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
    
    echo "Creating patched environment..."
    
    # Create temporary directory for patched version
    mkdir -p /app/source_code_patched
    cd /app/source_code_patched
    
    # Install patched version of crewai
    pip install crewai==0.84.0
    
    # Apply patch to the site-packages
    echo "Applying patch from $patch_file..."
    cd /usr/local/lib/python3.12/site-packages
    patch -p1 < "$patch_file"
    
    if [ $? -eq 0 ]; then
        echo "✅ Patch applied successfully"
        echo "You can now test your patched version with: docker run ... test_patched"
    else
        echo "❌ Failed to apply patch"
        exit 1
    fi
}

# Function to test the patched version
test_patched() {
    echo "Testing PATCHED version (PyPI + your patch)"
    run_test "patched"
    return $?
}

case "$1" in
    test_buggy)
        echo "=== Testing BUGGY Version (crewai==0.84.0) ==="
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
        echo "=== Testing PATCHED Version (crewai==0.84.0 + Your Patch) ==="
        test_patched
        ;;
    show_diff)
        echo "=== Diff between PyPI version and FIXED version ==="
        echo "Cannot show diff - PyPI version and Git version are different sources"
        echo "See the PR with the fix instead: https://github.com/crewAI/crewAI/pull/1825"
        ;;
    bash)
        echo "Entering bash shell. Use 'cd /app/source_code_fixed'"
        /bin/bash
        ;;
    help|*)
        echo "Usage: docker run [OPTIONS] IMAGE [COMMAND]"
        echo ""
        echo "Commands:"
        echo "  test_buggy      Test if the bug exists (using PyPI version)"
        echo "  test_fixed      Test if the fix works in the fixed version"
        echo "  apply_patch     Apply a patch file to the PyPI version"
        echo "                  Example: docker run -v \$(pwd):/patches IMAGE apply_patch /patches/my_patch.patch"
        echo "  test_patched    Test the PyPI version with your applied patch"
        echo "  bash            Start a bash shell"
        echo "  help            Show this help message"
        echo ""
        if [ "$1" != "help" ] && [ ! -z "$1" ]; then exit 1; fi
        ;;
esac

exit $?