#!/bin/bash
set -eo pipefail

SOURCE_BUGGY="/app/source_code_buggy"
SOURCE_FIXED="/app/source_code_fixed"
REPRO_SCRIPT="/opt/reproduce.py"
PATCH_FILE="/opt/patch.diff"

run_test() {
  local version=$1
  local dir=$2

  cp "$REPRO_SCRIPT" "$dir/reproduce.py"
  cd "$dir"

  # Set PYTHONPATH based on version
  if [ "$version" = "buggy" ] || [ "$version" = "patched" ]; then
    export PYTHONPATH="$dir:$dir/python:$dir/python/packages:$PYTHONPATH"
  else
    export PYTHONPATH="$dir:$dir/python/packages/autogen-agentchat/src:$dir/python/packages/autogen-ext/src:$dir/python/packages/autogen-core/src:$PYTHONPATH"
  fi

  python reproduce.py "$version"
  local exit_code=$?

  cd /app
  if [ $exit_code -eq 0 ]; then
    if [ "$version" = "buggy" ]; then
      echo "✅ BUG SUCCESSFULLY REPRODUCED"
    elif [ "$version" = "fixed" ]; then
      echo "✅ FIX SUCCESSFULLY VERIFIED"
    else
      echo "✅ PATCH SUCCESSFULLY VERIFIED"
    fi
  else
    if [ "$version" = "buggy" ]; then
      echo "❌ BUG NOT REPRODUCED"
    elif [ "$version" = "fixed" ]; then
      echo "❌ FIX NOT VERIFIED"
    else
      echo "❌ PATCH NOT VERIFIED"
    fi
  fi

  return $exit_code
}

apply_patch() {
  local base_dir=$1
  local patch_file=$2

  cd "$base_dir"
  if [ -f "$patch_file" ]; then
    git apply "$patch_file"
    echo "Patch applied."
  else
    echo "Patch file $patch_file not found."
    exit 2
  fi
  cd /app
}

case "$1" in
  test_buggy)
    echo "=== Testing BUGGY Version (Commit: ${BUGGY_COMMIT}) ==="
    run_test "buggy" "$SOURCE_BUGGY"
    ;;
  test_fixed)
    echo "=== Testing FIXED Version (Commit: ${FIXED_COMMIT}) ==="
    run_test "fixed" "$SOURCE_FIXED"
    ;;
  apply_patch)
    echo "=== Applying PATCH to BUGGY Version ==="
    apply_patch "$SOURCE_BUGGY" "$PATCH_FILE"
    ;;
  test_patched)
    echo "=== Testing PATCHED Version ==="
    run_test "patched" "$SOURCE_BUGGY"
    ;;
  show_diff)
    cd "$SOURCE_BUGGY"
    echo "=== Diff between BUGGY (${BUGGY_COMMIT}) and FIXED (${FIXED_COMMIT}) ==="
    git diff "${BUGGY_COMMIT}" "${FIXED_COMMIT}" --
    ;;
  inspect_buggy)
    echo "Setting up BUGGY environment (commit: ${BUGGY_COMMIT})..."
    echo "Use 'docker exec -it <container_id> bash' to explore."
    tail -f /dev/null
    ;;
  bash)
    exec /bin/bash
    ;;
  help|*)
    echo "Usage: docker run <image_name> [test_buggy|test_fixed|apply_patch|test_patched|show_diff|inspect_buggy|bash|help]"
    ;;
esac