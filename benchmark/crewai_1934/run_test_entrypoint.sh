#!/bin/bash
set -eo pipefail

reproduce_PY="/opt/reproduce.py"

run_test() {
    local version=$1
    echo "--- Running Test for ${version} version ---"
    
    # Check if OpenAI API key is provided
    if [ -z "${OPENAI_API_KEY}" ]; then
        echo "WARNING: OPENAI_API_KEY environment variable not set. This is expected for this test."
    fi
    
    # Check if OPENAI_BASE_URL is provided
    if [ ! -z "${OPENAI_BASE_URL}" ]; then
        echo "Using custom OPENAI_BASE_URL: ${OPENAI_BASE_URL}"
        export OPENAI_BASE_URL
    fi
    
    if [ "$version" == "buggy" ] || [ "$version" == "patched" ]; then
        CODE_DIR="/app/source_code_buggy"
        export PYTHONPATH="${CODE_DIR}:${PYTHONPATH}"
    else
        CODE_DIR="/app/source_code_fixed"
        # Reinstall the fixed version
        cd ${CODE_DIR}
        pip install -e .
        export PYTHONPATH="${CODE_DIR}:${PYTHONPATH}"
    fi
    
    cd "${CODE_DIR}"
    
    # Execute the Python test script with the version parameter
    if [ -f "${reproduce_PY}" ]; then
        echo "Found reproduce.py. Executing with python..."
        python "${reproduce_PY}" "$version"
        local exit_code=$?
        
        if [ $exit_code -eq 0 ]; then
            if [ "$version" == "buggy" ]; then
                echo "✅ BUG SUCCESSFULLY REPRODUCED: kickoff hangs when LLM call fails"
                return 0
            elif [ "$version" == "patched" ]; then
                echo "✅ PATCH SUCCEEDED: kickoff properly handles LLM call failures"
                return 0
            else
                echo "✅ FIX CONFIRMED: kickoff properly handles LLM call failures"
                return 0
            fi
        else
            if [ "$version" == "buggy" ]; then
                echo "❌ BUG NOT REPRODUCED: kickoff did not hang (unexpected)"
                return 1
            elif [ "$version" == "patched" ]; then
                echo "❌ PATCH FAILED: kickoff still hangs when LLM call fails"
                return 1
            else
                echo "❌ FIX NOT CONFIRMED: kickoff still hangs when LLM call fails"
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
    
    echo "Applying patch to buggy version..."
    
    # Set the source dir to the buggy version
    local source_dir="/app/source_code_buggy"
    cd "${source_dir}"
    
    echo "Applying patch from $patch_file..."
    patch -p1 < "$patch_file"
    
    if [ $? -eq 0 ]; then
        echo "✅ Patch applied successfully"
        
        # Reinstall the patched package
        echo "Reinstalling the patched package..."
        pip install -e .
        
        echo "You can now test your patched version with: docker run -e OPENAI_API_KEY=\"sk-your-key\" ... test_patched"
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
        git diff "${BUGGY_COMMIT}" "${FIXED_COMMIT}"
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
        echo ""
        echo "Required environment variables:"
        echo "  OPENAI_API_KEY   Not actually needed for this test (we use a fake key)"
        echo ""
        echo "Optional environment variables:"
        echo "  OPENAI_BASE_URL  Custom OpenAI API base URL (if using a proxy or custom endpoint)"
        echo "  Example: docker run --rm -it -e OPENAI_BASE_URL=\"https://api.proxy.com/v1\" IMAGE test_buggy"
        if [ "$1" != "help" ] && [ ! -z "$1" ]; then exit 1; fi
        ;;
esac

exit $?