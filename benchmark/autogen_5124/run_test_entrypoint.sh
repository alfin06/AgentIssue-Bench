#!/bin/bash
set -eo pipefail

SOURCE_BUGGY="/app/source_code_buggy"
SOURCE_FIXED="/app/source_code_fixed"
REPRO_SCRIPT="/opt/reproduce.py"

run_test() {
  local version=$1
  local dir=$2
  if [ ! -d "$dir" ]; then
    echo "❌ Source directory $dir does not exist!"
    exit 2
  fi
  cp "$REPRO_SCRIPT" "$dir/reproduce.py"
  cd "$dir"
  export PYTHONPATH="$dir:$dir/python/packages/autogen-ext/src:$dir/python/packages/autogen-core/src:$PYTHONPATH"
  python reproduce.py "$version"
  local exit_code=$?
  cd /app
  if [ $exit_code -eq 0 ]; then
    if [ "$version" = "buggy" ]; then
      echo "✅ BUG SUCCESSFULLY REPRODUCED"
    else
      echo "✅ FIX SUCCESSFULLY VERIFIED"
    fi
  else
    if [ "$version" = "buggy" ]; then
      echo "❌ BUG NOT REPRODUCED"
    else
      echo "❌ FIX NOT VERIFIED"
    fi
  fi
  return $exit_code
}

apply_patch() {
  local patch_file="$2"
  if [ ! -d "$SOURCE_BUGGY" ]; then
    echo "Cloning buggy source first..."
    # You may need to add your clone logic here
    exit 2
  fi
  echo "Applying patch: $patch_file"
  cd "$SOURCE_BUGGY"
  git apply "$patch_file"
  cd /app
  echo "✅ Patch applied"
}

test_patched() {
  run_test "patched" "$SOURCE_BUGGY"
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
    apply_patch "$@"
    ;;
  test_patched)
    test_patched
    ;;
  bash)
    exec /bin/bash
    ;;
  help|*)
    echo "Usage: docker run <image_name> [test_buggy|test_fixed|apply_patch <patch_file>|test_patched|bash|help]"
    ;;
esac