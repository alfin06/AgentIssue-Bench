#!/bin/bash
set -eo pipefail

# Define paths for test script
REPRO_SCRIPT_PY="/opt/reproduce.py"

# Function to test a specific version (buggy or fixed)
test_version() {
  local version=$1
  local commit_var="${version^^}_COMMIT"  # Convert to uppercase for env var
  local commit_hash="${!commit_var}"
  local source_dir="/app/source_code_$version"
  
  echo "Testing $version version from commit: $commit_hash"
  
  # Clone the repository if it doesn't exist
  if [ ! -d "$source_dir" ]; then
    echo "Cloning repository for $version version..."
    git clone "https://github.com/FoundationAgents/MetaGPT.git" "$source_dir"
    cd "$source_dir"
    git fetch origin "$commit_hash"
    git checkout "$commit_hash"
    
    # Create a modified setup.py or requirements.txt to skip problematic dependencies
    echo "Creating modified requirements to skip llama-cpp-python..."
    
    if [ -f "requirements.txt" ]; then
      # Remove llama-cpp-python from requirements
      grep -v "llama-cpp-python" requirements.txt > requirements.modified.txt
      mv requirements.modified.txt requirements.txt
    fi
    
    if [ -f "setup.py" ]; then
      # Backup original
      cp setup.py setup.py.orig
      # Remove llama-cpp-python from dependencies
      sed -i 's/"llama-cpp-python[^"]*"[,]*//' setup.py
      sed -i "s/'llama-cpp-python[^']*'[,]*//" setup.py
    fi
    

    
    python -m pip install --upgrade pip && pip install --editable .
    
    # Install only required dependencies
    pip install requests
    
    cd /app
  fi

  # Set PYTHONPATH to include the source directory
  export PYTHONPATH="$source_dir:$PYTHONPATH"

  # Execute the Python test script with the version parameter
  if [ -f "${REPRO_SCRIPT_PY}" ]; then
    echo "Running reproduction script for $version version..."
    python "${REPRO_SCRIPT_PY}" "$version"
    local exit_code=$?
    
    # Interpretation of exit code
    if [ $exit_code -eq 0 ]; then
      if [ "$version" == "buggy" ]; then
        echo "✅ BUG REPRODUCED"
      else
        echo "✅ FIX CONFIRMED"
      fi
    else
      if [ "$version" == "buggy" ]; then
        echo "❌ BUG NOT REPRODUCED"
      else
        echo "❌ FIX NOT WORKING"
      fi
    fi
    
    return $exit_code
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
  
  # Make sure the buggy version is cloned
  local source_dir="/app/source_code_buggy"
  if [ ! -d "$source_dir" ]; then
    echo "Cloning repository for buggy version first..."
    test_version "buggy" > /dev/null || true
  fi
  
  # Apply the patch
  cd "$source_dir"
  echo "Applying patch from $patch_file..."
  patch -p1 < "$patch_file"
  
  if [ $? -eq 0 ]; then
    echo "✅ Patch applied successfully"
    
    # Reinstall if needed
    echo "Reinstalling the patched package..."
    pip install --no-deps -e .
    
    echo "You can now test your patched version with: docker run ... test_patched"
  else
    echo "❌ Failed to apply patch"
    exit 1
  fi
}

# Function to test the patched version
test_patched() {
  echo "Testing PATCHED version (based on buggy with applied patch)"
  
  # Set the source dir to the buggy version which should have the patch applied
  local source_dir="/app/source_code_buggy"
  
  if [ ! -d "$source_dir" ]; then
    echo "Error: Patched source directory not found. Run 'apply_patch' first."
    exit 1
  fi

  # Set PYTHONPATH to include the source directory
  export PYTHONPATH="$source_dir:$PYTHONPATH"
  
  # Execute the Python test script with the "patched" parameter
  if [ -f "${REPRO_SCRIPT_PY}" ]; then
    echo "Running reproduction script for patched version..."
    python "${REPRO_SCRIPT_PY}" "patched"
    local exit_code=$?
    
    # Interpretation of exit code
    if [ $exit_code -eq 0 ]; then
      echo "✅ PATCH SUCCEEDED: The patched version properly handles boolean values"
    else
      echo "❌ PATCH FAILED: The bug still exists in the patched version"
    fi
    
    return $exit_code
  else
    echo "--- FATAL ERROR: No reproduction script found! ---"
    echo "Looked for ${REPRO_SCRIPT_PY}"
    exit 127
  fi
}

# Main execution
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
      echo "Usage: docker run -v \$(pwd):/patches IMAGE apply_patch /patches/my_patch.patch"
      exit 1
    fi
    apply_patch "$2"
    ;;
  test_patched)
    test_patched
    ;;
  show_diff)
    echo "=== Diff between BUGGY and FIXED versions ==="
    diff -u /app/source_code_buggy/agixt/extensions/voice_chat.py /app/source_code_fixed/agixt/extensions/voice_chat.py || true
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
    echo "                  Example: docker run -v \$(pwd):/patches IMAGE apply_patch /patches/fix.patch"
    echo "  test_patched    Test the buggy version with your applied patch"
    echo "  show_diff       Show the diff between buggy and fixed versions"
    echo "  bash            Start a bash shell"
    echo "  help            Show this help message"
    if [ "$1" != "help" ] && [ ! -z "$1" ]; then exit 1; fi
    ;;
esac

exit $?