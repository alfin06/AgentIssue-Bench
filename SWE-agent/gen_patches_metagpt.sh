#!/bin/bash

# Ensure that the script is executed with the correct argument
if [ $# -ne 1 ]; then
    echo "Usage: bash gen_patch_script <ISSUE_NUMBER>"
    exit 1
fi

# Get the issue number from the command line argument
ISSUE_NUMBER=$1
MODEL_NAME=""

# Set other environment variables
export OPENAI_API_KEY=""
export GITHUB_TOKEN=""

REPO_URL="https://github.com/geekan/MetaGPT.git"
ISSUE_URL="https://github.com/geekan/MetaGPT/issues/$ISSUE_NUMBER"

path=""
OUTPUT_DIR="trajectories/${path}/anthropic_filemap__${MODEL_NAME}__t-0.00__p-1.00__c-0.50___geekan__MetaGPT-i$ISSUE_NUMBER"
PATCH_DIR="Patches/metagpt/$ISSUE_NUMBER"

# Create the PATCH_DIR if it doesn't exist
mkdir -p "$PATCH_DIR"

for i in $(seq -w 1 3); do
    echo "Running iteration $i..."

    # Check if PATCH_DIR already has a patch directory, if yes, skip sweagent
    PATCH_PATH=$(find "$OUTPUT_DIR" -mindepth 1 -maxdepth 1 -type d | head -n 1)
    
    if [ -n "$PATCH_PATH" ] && [ -d "$PATCH_PATH" ]; then
        NEW_PATCH_PATH="$PATCH_DIR/$(basename "$PATCH_PATH")_patch_$i"
        mv "$PATCH_PATH" "$NEW_PATCH_PATH"
        echo "Patch $i already exists, moving patch to $NEW_PATCH_PATH"
    else
        # If the patch does not exist, run sweagent to generate it
        proxy_on
        sweagent run \
          --agent.model.name="$MODEL_NAME" \
          --agent.model.per_instance_cost_limit=0.50 \
          --env.repo.github_url="$REPO_URL" \
          --problem_statement.github_url="$ISSUE_URL"
        
        PATCH_PATH=$(find "$OUTPUT_DIR" -mindepth 1 -maxdepth 1 -type d | head -n 1)
        if [ -n "$PATCH_PATH" ] && [ -d "$PATCH_PATH" ]; then
            NEW_PATCH_PATH="$PATCH_DIR/$(basename "$PATCH_PATH")_patch_$i"
            mv "$PATCH_PATH" "$NEW_PATCH_PATH"
            echo "Patch $i saved to $NEW_PATCH_PATH"
        else
            echo "Patch $i not found, skipping..."
        fi
    fi

done
