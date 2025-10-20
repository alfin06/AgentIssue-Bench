#!/bin/bash
set -eo pipefail

REPO_URL="https://github.com/InternLM/lagent.git"
REPRO_SCRIPT_PY="/opt/reproduce.py"

test_version() {
  local version=$1
  local commit_var="${version^^}_COMMIT"
  local commit_hash="${!commit_var}"
  local source_dir="/app/source_code_$version"

  echo "Testing $version version from commit: $commit_hash"

  # Clone if missing
  if [ ! -d "$source_dir" ]; then
    echo "Cloning repository for $version version..."
    git clone "$REPO_URL" "$source_dir"
    cd "$source_dir"
    git checkout "$commit_hash"
    pip install -e .
    cd /app
  fi

  export PYTHONPATH="$source_dir:$PYTHONPATH"

  if [ -f "${REPRO_SCRIPT_PY}" ]; then
    echo "Running reproduction script for $version version..."
    python "${REPRO_SCRIPT_PY}" "$version" "$source_dir"
    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
      if [ "$version" == "buggy" ]; then
        echo "✅ BUG REPRODUCED: tenacity is missing in buggy version"
      else
        echo "✅ FIX CONFIRMED: tenacity is present in fixed version"
      fi
    else
      if [ "$version" == "buggy" ]; then
        echo "❌ BUG NOT REPRODUCED: tenacity is present in buggy version"
      else
        echo "❌ FIX NOT VERIFIED: tenacity is missing in fixed version"
      fi
    fi
    return $exit_code
  else
    echo "--- FATAL ERROR: No reproduction script found! ---"
    exit 127
  fi
}

apply_patch() {
  local patch_file=$1
  local source_dir="/app/source_code_buggy"

  if [ ! -f "$patch_file" ]; then
    echo "Error: Patch file not found at $patch_file"
    exit 1
  fi

  if [ ! -d "$source_dir" ]; then
    echo "Cloning repository for buggy version first..."
    test_version "buggy" > /dev/null || true
  fi

  cd "$source_dir"
  echo "Applying patch from $patch_file..."
  patch -p1 < "$patch_file"
  if [ $? -eq 0 ]; then
    echo "✅ Patch applied successfully"
    echo "Reinstalling the patched package..."
    pip install -e .
    echo "You can now test your patched version with: docker run ... test_patched"
  else
    echo "❌ Failed to apply patch"
    exit 1
  fi
  cd /app
}

test_patched() {
  local source_dir="/app/source_code_buggy"
  if [ ! -d "$source_dir" ]; then
    echo "Error: Patched source directory not found. Run 'apply_patch' first."
    exit 1
  fi
  export PYTHONPATH="$source_dir:$PYTHONPATH"
  if [ -f "${REPRO_SCRIPT_PY}" ]; then
    echo "Running reproduction script for patched version..."
    python "${REPRO_SCRIPT_PY}" "patched" "$source_dir"
    local exit_code=$?
    if [ $exit_code -eq 0 ]; then
      echo "✅ PATCH SUCCESSFULLY VERIFIED: tenacity is present after patch"
    else
      echo "❌ PATCH NOT VERIFIED: tenacity is missing after patch"
    fi
    return $exit_code
  else
    echo "--- FATAL ERROR: No reproduction script found! ---"
    exit 127
  fi
}

case "$1" in
  test_buggy)
    test_version "buggy"
    ;;
  test_fixed)
    test_version "fixed"
    ;;
  apply_patch)
    if [ -z "$2" ]; then
      echo "Error: Patch file path required"
      echo "Usage: docker run -v \$(pwd):/patches IMAGE apply_patch /patches/{tag_name}/patch.patch"
      exit 1
    fi
    apply_patch "$2"
    ;;
  test_patched)
    test_patched
    ;;
  show_diff)
    echo "=== Diff between BUGGY and FIXED versions ==="
    diff -u /app/source_code_buggy/requirements/runtime.txt /app/source_code_fixed/requirements/runtime.txt || true
    ;;
  bash)
    echo "Starting bash shell..."
    exec /bin/bash
    ;;
  help|*)
    echo "Usage: docker run [OPTIONS] IMAGE [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  test_buggy      Test if the bug exists in the buggy version"
    echo "  test_fixed      Test if the fix works in the fixed version"
    echo "  apply_patch     Apply a patch file to the buggy version (requires mounted volume)"
    echo "                  Example: docker run -v \$(pwd):/patches IMAGE apply_patch /patches/{tag_name}/patch.patch"
    echo "  test_patched    Test the buggy version with your applied patch"
    echo "  show_diff       Show the diff between buggy and fixed versions"
    echo "  bash            Start a bash shell"
    echo "  help            Show this help message"
    if [ "$1" != "help" ] && [ ! -z "$1" ]; then exit 1; fi
    ;;
esac

exit $?