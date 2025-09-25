#!/bin/bash
# unified_test.sh - Run tests across multiple patched Docker images and count successes

# Directory containing your patches
PATCHES_DIR="./patches"
# File to store results
RESULTS_FILE="patch_results.txt"
# Counter for successful patches
SUCCESS_COUNT=0
TOTAL_COUNT=0

# Clear previous results
echo "# Patch Test Results" > $RESULTS_FILE
echo "$(date)" >> $RESULTS_FILE
echo "-----------------------------------" >> $RESULTS_FILE

# Process each image/issue with corresponding patch
run_test_for_issue() {
    local issue=$1
    local image="alfin06/agentissue-bench:${issue}"
    local patch_file="${PATCHES_DIR}/${issue}_fix.patch"
    
    echo "===== Testing issue: $issue ====="
    echo "* Testing issue: $issue" >> $RESULTS_FILE
    
    # Check if patch file exists
    if [ ! -f "$patch_file" ]; then
        echo "❌ No patch file found for $issue at $patch_file"
        echo "  - ❌ No patch file found" >> $RESULTS_FILE
        return 1
    fi
    
    echo "Applying patch from $patch_file..."
    
    # Apply the patch to the buggy version
    docker run --rm -v "$PATCHES_DIR:/patches" $image apply_patch "/patches/$(basename $patch_file)" > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "❌ Failed to apply patch for $issue"
        echo "  - ❌ Failed to apply patch" >> $RESULTS_FILE
        return 1
    fi
    
    # Test the patched version
    echo "Testing if patch fixes the issue..."
    docker run --rm $image test_patched
    local result=$?
    
    # Count successful patches
    if [ $result -eq 0 ]; then
        echo "✅ Patch for $issue SUCCESSFULLY fixed the issue!"
        echo "  - ✅ SUCCESS: Patch fixed the issue" >> $RESULTS_FILE
        return 0
    else
        echo "❌ Patch for $issue FAILED to fix the issue"
        echo "  - ❌ FAILURE: Patch did not fix the issue" >> $RESULTS_FILE
        return 1
    fi
}

# List of issues to test (you can expand this)
ISSUES=(
    "agixt_1256"
    "agixt_1026"
    "crewai_1323"
    # Add more issues here
)

# Run tests for each issue
for issue in "${ISSUES[@]}"; do
    echo ""
    echo "========================================"
    TOTAL_COUNT=$((TOTAL_COUNT + 1))
    
    if run_test_for_issue $issue; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    fi
    
    echo "========================================"
    echo ""
done

# Display final results
echo ""
echo "========================================"
echo "FINAL RESULTS: $SUCCESS_COUNT out of $TOTAL_COUNT patches were successful"
echo "========================================"

# Save final tally to results file
echo "" >> $RESULTS_FILE
echo "-----------------------------------" >> $RESULTS_FILE
echo "SUMMARY: $SUCCESS_COUNT out of $TOTAL_COUNT patches were successful" >> $RESULTS_FILE

# Exit with success count as exit code (useful for CI/CD)
exit $SUCCESS_COUNT