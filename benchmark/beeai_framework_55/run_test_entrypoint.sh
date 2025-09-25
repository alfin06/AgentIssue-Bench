#!/bin/bash
set -eo pipefail

# This script is the universal test runner for a benchmark image.
# It handles building a yarn project and running a .ts test script with tsx.

CODE_DIR="/app/source_code_buggy"
REPRO_SCRIPT_TS_SOURCE="/opt/repro_script.ts"
# The script will be copied here to be run
REPRO_SCRIPT_TS_DEST="${CODE_DIR}/repro_script.ts"

# This function handles building the project
build_project() {
    echo "--- Building project from source with yarn ---"
    # Ensure all dependencies are installed for the checked-out version
    yarn install
    # Compile the TypeScript source code
    yarn build
    echo "--- Build complete ---"
}

# This function runs the test script
run_test() {
    echo "--- Running Test ---"
    
    if [ -f "${REPRO_SCRIPT_TS_SOURCE}" ]; then
        # --- DEFINITIVE FIX ---
        # Copy the script into the workspace root to ensure correct module resolution.
        cp "${REPRO_SCRIPT_TS_SOURCE}" "${REPRO_SCRIPT_TS_DEST}"

        echo "Found repro_script.ts. Executing with 'yarn tsx' from within the project..."
        # We run the script from the project root.
        # 'yarn tsx' will use the locally installed tsx package and correctly
        # resolve all project modules, including 'beeai-framework'.
        if yarn tsx "${REPRO_SCRIPT_TS_DEST}"; then
            echo "--- Test script executed successfully (exit code 0) ---"
        else
            echo "--- Test script failed (exit code $?) ---"
        fi
        
        # Clean up the copied script
        rm "${REPRO_SCRIPT_TS_DEST}"
    else
        echo "--- FATAL ERROR: No reproduction script found! ---"
        echo "Looked for ${REPRO_SCRIPT_TS_SOURCE}"
        exit 127
    fi
}

# Main execution logic
case "$1" in
    test_buggy)
        echo "=== Testing BUGGY Version (Commit: ${BUGGY_COMMIT}) ==="
        echo "Checking out buggy commit..."
        cd "${CODE_DIR}"
        git -c advice.detachedHead=false checkout "${BUGGY_COMMIT}" --force
        build_project
        run_test
        ;;
    test_fixed)
        if [ -z "${FIXED_COMMIT}" ] || [ "${FIXED_COMMIT}" == "N/A" ]; then
            echo "ERROR: FIXED_COMMIT not set." >&2; exit 1;
        fi
        echo "=== Testing FIXED Version (Commit: ${FIXED_COMMIT}) ==="
        cd "${CODE_DIR}"
        git -c advice.detachedHead=false checkout "${FIXED_COMMIT}" --force
        build_project
        run_test
        ;;
    *)
        echo "Usage: docker run <image_name> [test_buggy|test_fixed]"
        if [ "$1" != "help" ] && [ ! -z "$1" ]; then exit 1; fi
        ;;
esac