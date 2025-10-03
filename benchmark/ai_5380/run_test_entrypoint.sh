#!/bin/bash
set -eo pipefail

CODE_DIR="/app/source_code_buggy"
NODE_CMD="${NODE_CMD:-node}"
REPRO_SCRIPT_JS="/opt/reproduce.js"

cd "${CODE_DIR}"

build_project() {
    echo "--- Building project from source ---"
    rm -rf node_modules packages/*/dist
    pnpm install
    pnpm build
    echo "--- Build complete ---"
    cd /opt
    echo '{"type": "module"}' > package.json
    # Remove the problematic line below:
    # npm install /app/source_code_buggy/packages/core
    cd "${CODE_DIR}"
}

run_test() {
    echo "--- Running Test ---"
    if [ -f "${REPRO_SCRIPT_JS}" ]; then
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
        CODE_DIR="/app/source_code_buggy"
        echo "=== Testing BUGGY Version (Commit: ${BUGGY_COMMIT}) ==="
        cd "${CODE_DIR}"
        git -c advice.detachedHead=false checkout "${BUGGY_COMMIT}" --force
        VERSION="buggy" run_test
        ;;
    test_fixed)
        CODE_DIR="/app/source_code_fixed"
        echo "=== Testing FIXED Version (Commit: ${FIXED_COMMIT}) ==="
        cd "${CODE_DIR}"
        git -c advice.detachedHead=false checkout "${FIXED_COMMIT}" --force
        VERSION="fixed" run_test
        ;;
    test_patched)
        echo "=== Testing PATCHED Version (Buggy + Your Patch) ==="
        git -c advice.detachedHead=false checkout "${BUGGY_COMMIT}" --force
        if [ -f "/patches/patch.diff" ]; then
            echo "--- Applying patch from /patches/patch.diff ---"
            git apply /patches/patch.diff
        else
            echo "ERROR: Patch file /patches/patch.diff not found." >&2; exit 1;
        fi
        build_project
        run_test
        ;;
    apply_patch)
        if [ -z "$2" ]; then
            echo "Usage: docker run -v \$(pwd):/patches IMAGE apply_patch /patches/your_patch.diff"
            exit 1
        fi
        echo "--- Applying patch from $2 ---"
        git apply "$2"
        ;;
    show_diff)
        echo "=== Diff between BUGGY (${BUGGY_COMMIT}) and FIXED (${FIXED_COMMIT}) ==="
        git diff "${BUGGY_COMMIT}" "${FIXED_COMMIT}"
        ;;
    *)
        echo "Usage: docker run <image_name> [test_buggy|test_fixed|test_patched|apply_patch|show_diff]"
        if [ "$1" != "help" ] && [ ! -z "$1" ]; then exit 1; fi
        ;;
esac