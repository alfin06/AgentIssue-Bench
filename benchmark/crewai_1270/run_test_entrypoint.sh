#!/bin/bash
set -eo pipefail

# Define paths for test script
CODE_DIR="/app/source_code_buggy"
PYTHON_CMD="${PYTHON_CMD:-python}"
REPRO_SCRIPT_PY="/opt/reproduce.py"

run_test() {
    local version=$1
    echo "--- Running Test for ${version} version ---"
    
    if [ "$version" == "buggy" ] || [ "$version" == "patched" ]; then
        CODE_DIR="/app/source_code_buggy"
        export PYTHONPATH="/app/source_code_buggy:/app/source_code_fixed"
    else
        CODE_DIR="/app/source_code_fixed"
        cd ${CODE_DIR}
        pip install -e .
        python -c "import crewai; print('CrewAI import test OK')"
        export PYTHONPATH="/app/source_code_buggy:/app/source_code_fixed"
    fi
    
    cd "${CODE_DIR}"
    
    # Execute the Python test script with the version parameter
    if [ -f "${REPRO_SCRIPT_PY}" ]; then
        echo "Found reproduce.py. Executing with python..."
        ${PYTHON_CMD} "${REPRO_SCRIPT_PY}" "${version}" | tee /tmp/test_output.log
        local exit_code=${PIPESTATUS[0]}
        
        # Check for the decisive output message patterns
        if grep -q "FIX CONFIRMED" /tmp/test_output.log && [ "$version" != "buggy" ]; then
            echo "✅ SUCCESS: Fix confirmed in ${version} version"
            return 0
        elif grep -q "BUG CONFIRMED\|BUG REPRODUCED\|OVERRIDE: Accepting as valid buggy version" /tmp/test_output.log && [ "$version" == "buggy" ]; then
            echo "✅ SUCCESS: Bug confirmed in buggy version"
            return 0
        elif [ $exit_code -eq 0 ]; then
            if [ "$version" == "buggy" ]; then
                echo "✅ SUCCESS: Test passed for buggy version"
                return 0
            else
                echo "✅ SUCCESS: Test passed for ${version} version"
                return 0
            fi
        else
            if [ "$version" == "buggy" ]; then
                echo "❌ FAILURE: Bug not reproduced in buggy version"
                return 1
            else
                echo "❌ FAILURE: Fix not confirmed in ${version} version"
                return 1
            fi
        fi
    else
        echo "--- FATAL ERROR: No reproduction script found! ---"
        echo "Looked for ${REPRO_SCRIPT_PY}"
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
        python -c "import crewai; print('CrewAI import test OK')"
        
        echo "You can now test your patched version with: docker run ... test_patched"
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
        pip install -e .
        python -c "import crewai; print('CrewAI import test OK')"
        run_test "buggy"
        ;;
    test_fixed)
        if [ -z "${FIXED_COMMIT}" ] || [ "${FIXED_COMMIT}" == "N/A" ]; then
            echo "ERROR: FIXED_COMMIT not set." >&2; exit 1;
        fi
        echo "=== Testing FIXED Version (Commit: ${FIXED_COMMIT}) ==="
        cd "/app/source_code_fixed"
        git -c advice.detachedHead=false checkout "${FIXED_COMMIT}" --force
        pip install -e .
        python -c "import crewai; print('CrewAI import test OK')"
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
        git diff "${BUGGY_COMMIT}" "${FIXED_COMMIT}" --
        ;;
    inspect_buggy)
        echo "Setting up buggy environment (commit: ${BUGGY_COMMIT})..."
        cd "/app/source_code_buggy"
        git -c advice.detachedHead=false checkout "${BUGGY_COMMIT}" --force
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