#!/bin/bash
set -eo pipefail

CODE_DIR="/app/source_code"
NODE_CMD="${NODE_CMD:-node}"
REPRO_SCRIPT_JS="/opt/reproduce.js"

if [ ! -d "${CODE_DIR}" ]; then
    echo "--- FATAL ERROR: Source code directory ${CODE_DIR} not found! ---"
    exit 1
fi

cd "${CODE_DIR}"

run_test() {
    echo "--- Running Test ---"
    if [ -f "${REPRO_SCRIPT_JS}" ]; then
        echo "Found reproduce.js. Executing with node..."
        if ${NODE_CMD} "${REPRO_SCRIPT_JS}" "$1"; then
            echo "--- Test script executed successfully (exit code 0) ---"
        else
            echo "--- Test script failed as expected (exit code $?) ---"
        fi
    else
        echo "--- FATAL ERROR: No reproduce.js script found! ---"
        exit 127
    fi
}

# Function to apply a git patch
apply_patch() {
    PATCH_FILE="$1"
    if [ -z "$PATCH_FILE" ] || [ ! -f "$PATCH_FILE" ]; then
        echo "ERROR: Patch file not found: $PATCH_FILE" >&2
        exit 1
    fi
    echo "Applying patch to buggy version..."
    git -c advice.detachedHead=false checkout "${BUGGY_COMMIT}" --force
    git apply "$PATCH_FILE"
    echo "Patch applied."
}

case "$1" in
    test_buggy)
        echo "=== Testing BUGGY Version (Commit: ${BUGGY_COMMIT}) ==="
        git -c advice.detachedHead=false checkout "${BUGGY_COMMIT}" --force
        run_test "$1"
        ;;
    test_fixed)
        if [ -z "${FIXED_COMMIT}" ] || [ "${FIXED_COMMIT}" == "N/A" ]; then
            echo "ERROR: FIXED_COMMIT not set. Provide it during 'docker build'." >&2; exit 1;
        fi
        echo "=== Testing FIXED Version (Commit: ${FIXED_COMMIT}) ==="
        git -c advice.detachedHead=false checkout "${FIXED_COMMIT}" --force
        run_test "$1"
        ;;
    apply_patch)
        apply_patch "$2"
        ;;
    test_patched)
        echo "=== Testing PATCHED Version (BUGGY + PATCH) ==="
        run_test
        ;;
    show_diff)
        if [ -z "${FIXED_COMMIT}" ] || [ "${FIXED_COMMIT}" == "N/A" ]; then
            echo "ERROR: FIXED_COMMIT not set." >&2; exit 1;
        fi
        echo "=== Diff between BUGGY (${BUGGY_COMMIT}) and FIXED (${FIXED_COMMIT}) ==="
        git diff "${BUGGY_COMMIT}" "${FIXED_COMMIT}" --
        ;;
    bash)
        echo "Entering bash shell. Defaulting to BUGGY commit (${BUGGY_COMMIT})."
        git -c advice.detachedHead=false checkout "${BUGGY_COMMIT}" --force
        /bin/bash
        ;;
    help|*)
        echo "Usage: docker run <image_name> [test_buggy|test_fixed|apply_patch <patchfile>|test_patched|show_diff|bash|help]"
        if [ "$1" != "help" ] && [ ! -z "$1" ]; then exit 1; fi
        ;;
esac

