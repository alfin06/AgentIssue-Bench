#!/bin/bash
# filepath: d:\Projects\AgentIssue-Bench\reproduction_workspace\failure_triggering_tests\agixt_1369\run_test_entrypoint.sh
set -eo pipefail

# Function to test chain name validation
test_chain_validation() {
  local version=$1
  local source_dir="/app/source_code_$version"
  
  echo "Testing $version version from commit: $(cd $source_dir && git rev-parse HEAD)"
  
  # Look for chain name validation in the relevant file
  echo "Checking for chain name validation in Chain.py..."
  
  # Extract and examine the create_chain method
  grep -A 50 "def create_chain" $source_dir/agixt/Chain.py | grep -B 5 -A 5 "chain_name" || true
  
  echo "Running direct test script for $version version..."
  # Make sure we pass the version parameter to the Python script
  python /app/repro_script.py "$version"
  return $?
}

# Main execution
if [ "$1" = "test_buggy" ]; then
  test_chain_validation "buggy"
  exit_code=$?
  if [ $exit_code -eq 1 ]; then
    echo "✓ BUG SUCCESSFULLY REPRODUCED: Empty chain names are accepted in the buggy version."
  else
    echo "✗ BUG NOT REPRODUCED: Unexpected behavior in buggy version."
  fi
  exit $exit_code
elif [ "$1" = "test_fixed" ]; then
  test_chain_validation "fixed"
  exit_code=$?
  if [ $exit_code -eq 0 ]; then
    echo "✓ FIX CONFIRMED: Empty chain names are rejected in the fixed version."
  else
    echo "✗ FIX FAILED: Empty chain names are still accepted in the supposedly fixed version."
  fi
  exit $exit_code
else
  echo "Usage: $0 {test_buggy|test_fixed}"
  echo "  test_buggy - Test the buggy version"
  echo "  test_fixed - Test the fixed version"
  exit 1
fi