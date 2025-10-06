#!/bin/bash
set -eo pipefail

SOURCE_BUGGY="/app/source_code_buggy"
SOURCE_FIXED="/app/source_code_fixed"
SOURCE_PATCHED="/app/source_code_patched"
REPRO_SCRIPT="/opt/reproduce.py"
PATCH_FILE="/opt/patch.diff"

run_test() {
  local version=$1
  local dir=$2
  cp "$REPRO_SCRIPT" "$dir/reproduce.py"
  cd "$dir"
  python3 reproduce.py "$version"
  local exit_code=$?
  cd /app
  return $exit_code
}

apply_patch() {
  local base_dir=$1
  local patch_file=$2
  local patched_dir=$3
  echo "Applying patch to $base_dir..."
  rm -rf "$patched_dir"
  cp -r "$base_dir" "$patched_dir"
  cd "$patched_dir"
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
    if [ $? -eq 0 ]; then
      echo "✅ BUG SUCCESSFULLY REPRODUCED"
    else
      echo "❌ BUG NOT REPRODUCED"
    fi
    ;;
  test_fixed)
    echo "=== Testing FIXED Version (Commit: ${FIXED_COMMIT}) ==="
    run_test "fixed" "$SOURCE_FIXED"
    if [ $? -eq 0 ]; then
      echo "✅ FIX SUCCESSFULLY VERIFIED"
    else
      echo "❌ FIX NOT VERIFIED"
    fi
    ;;
  apply_patch)
    echo "=== Applying PATCH to BUGGY Version ==="
    apply_patch "$SOURCE_BUGGY" "$PATCH_FILE" "$SOURCE_PATCHED"
    ;;
  test_patched)
    echo "=== Testing PATCHED Version ==="
    if [ ! -d "$SOURCE_PATCHED" ]; then
      echo "Patched source directory not found. Run apply_patch first."
      exit 2
    fi
    run_test "patched" "$SOURCE_PATCHED"
    if [ $? -eq 0 ]; then
      echo "✅ PATCH SUCCESSFULLY VERIFIED"
    else
      echo "❌ PATCH NOT VERIFIED"
    fi
    ;;
  bash)
    exec /bin/bash
    ;;
  help|*)
    echo "Usage: docker run <image_name> [test_buggy|test_fixed|apply_patch|test_patched|bash|help]"
    ;;
esac