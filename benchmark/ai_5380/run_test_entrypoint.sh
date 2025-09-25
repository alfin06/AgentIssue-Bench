#!/bin/bash
set -eo pipefail

# This script is the universal test runner for a benchmark image.
# It now handles the build process at runtime to ensure the correct
# version of the code is tested.

CODE_DIR="/app/source_code_buggy"
NODE_CMD="${NODE_CMD:-node}"
REPRO_SCRIPT_JS="/opt/repro_script.js"

cd "${CODE_DIR}"

build_project() {
    echo "--- Building project from source ---"
    # Clean previous builds and dependencies to ensure a fresh state
    rm -rf node_modules packages/*/dist
    pnpm install
    pnpm build
    echo "--- Build complete ---"
    
    # After building, we must set up the test script's environment.
    # This ensures the test script can find the locally built packages.
    echo "--- Setting up test script environment ---"
    cd /opt
    echo '{"type": "module"}' > package.json
    # Install the locally built 'ai' package for the test script
    npm install /app/source_code_buggy/packages/core
    # Go back to the code dir for the test run
    cd "${CODE_DIR}"
}

run_test() {
    echo "--- Running Test ---"
    if [ -f "${REPRO_SCRIPT_JS}" ]; then
        echo "Found repro_script.js. Executing with node..."
        # We set NODE_PATH to ensure Node.js can find the dependencies
        # installed for the test script in the /opt directory.
        export NODE_PATH=/opt/node_modules
        if ${NODE_CMD} "${REPRO_SCRIPT_JS}"; then
            echo "--- Test script executed successfully (exit code 0) ---"
        else
            echo "--- Test script failed (exit code $?) ---"
        fi
    else
        echo "--- FATAL ERROR: No reproduction script found! ---"
        exit 127
    fi
}

case "$1" in
    test_buggy)
        echo "=== Testing BUGGY Version (Commit: ${BUGGY_COMMIT}) ==="
        echo "Checking out buggy commit..."
        git -c advice.detachedHead=false checkout "${BUGGY_COMMIT}" --force
        build_project
        run_test
        ;;
    test_fixed)
        if [ -z "${FIXED_COMMIT}" ] || [ "${FIXED_COMMIT}" == "N/A" ]; then
            echo "ERROR: FIXED_COMMIT not set." >&2; exit 1;
        fi
        echo "=== Testing FIXED Version (Commit: ${FIXED_COMMIT}) ==="
        git -c advice.detachedHead=false checkout "${FIXED_COMMIT}" --force
        build_project
        run_test
        ;;
    *)
        echo "Usage: docker run <image_name> [test_buggy|test_fixed]"
        if [ "$1" != "help" ] && [ ! -z "$1" ]; then exit 1; fi
        ;;
esac
