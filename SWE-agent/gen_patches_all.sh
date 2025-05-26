#!/bin/bash

export OPENAI_API_KEY=""
export GITHUB_TOKEN=""
export OPENAI_API_BASE=""

declare -a MODELS=("gpt-4o" "claude-3-5-sonnet-20241022")

declare -a PROJECTS=(
    "autogen:microsoft/autogen:4733"
    "autogen:microsoft/autogen:3361"
    "autogen:microsoft/autogen:4197"
    "autogen:microsoft/autogen:5124"
    "autogen:microsoft/autogen:1174"
    "autogen:microsoft/autogen:1844"
    "autogen:microsoft/autogen:4382"
    "autogen:microsoft/autogen:4785"
    "autogen:microsoft/autogen:5012"
    "autogen:microsoft/autogen:5007"
    "metagpt:geekan/MetaGPT:1313"
    "swe_agent:princeton-nlp/SWE-agent:741"
    "swe_agent:princeton-nlp/SWE-agent:333"
    "swe_agent:princeton-nlp/SWE-agent:362"
    "chatDev:OpenBMB/ChatDev:318"
    "chatDev:OpenBMB/ChatDev:413"
    "chatDev:OpenBMB/ChatDev:465"
    "Camel-ai:camel-ai/camel:1145"
    "Camel-ai:camel-ai/camel:1309"
    "Camel-ai:camel-ai/camel:1273"
    "Camel-ai:camel-ai/camel:88"
    "Camel-ai:camel-ai/camel:1614"
    "crewAI:crewAIInc/crewAI:1270"
    "crewAI:crewAIInc/crewAI:1323"
    "crewAI:crewAIInc/crewAI:1370"
    "crewAI:crewAIInc/crewAI:1463"
    "crewAI:crewAIInc/crewAI:1532"
    "crewAI:crewAIInc/crewAI:1723"
    "crewAI:crewAIInc/crewAI:1753"
    "crewAI:crewAIInc/crewAI:1824"
    "crewAI:crewAIInc/crewAI:1934"
    "AGiXT:Josh-XT/AGiXT:1026"
    "AGiXT:Josh-XT/AGiXT:1030"
    "AGiXT:Josh-XT/AGiXT:1253"
    "AGiXT:Josh-XT/AGiXT:1256"
    "AGiXT:Josh-XT/AGiXT:1369"
    "AGiXT:Josh-XT/AGiXT:1371"
    "evoninja:agentcoinorg/evo.ninja:443"
    "evoninja:agentcoinorg/evo.ninja:505"
    "evoninja:agentcoinorg/evo.ninja:549"
    "evoninja:agentcoinorg/evo.ninja:640"
    "evoninja:agentcoinorg/evo.ninja:641"
    "evoninja:agentcoinorg/evo.ninja:652"
    "Lagent:InternLM/lagent:239"
    "Lagent:InternLM/lagent:244"
    "Lagent:InternLM/lagent:29"
    "Pythagora:Pythagora-io/pythagora:55"
    "Superagent-AI:superagent-ai/superagent:953"
    "gpt-engineer:AntonOsika/gpt-engineer:1197"
    "GPT-Researcher:assafelovic/gpt-researcher:1027"
)

for MODEL_NAME in "${MODELS[@]}"; do
    echo "Using model: $MODEL_NAME"

    for PROJECT in "${PROJECTS[@]}"; do
        IFS=':' read -r PROJECT_NAME REPO_PATH ISSUE_NUMBER <<< "$PROJECT"
        echo "Processing $PROJECT_NAME - Issue #$ISSUE_NUMBER"
        
        REPO_URL="https://github.com/$REPO_PATH.git"
        ISSUE_URL="https://github.com/$REPO_PATH/issues/$ISSUE_NUMBER"
        path=""
        OUTPUT_DIR="trajectories/${path}/anthropic_filemap__${MODEL_NAME}__t-0.00__p-1.00__c-0.99___${REPO_PATH//\//__}-i$ISSUE_NUMBER"
        PATCH_DIR="Patches_Test/$PROJECT_NAME/$ISSUE_NUMBER"
        echo "REPO_URL: ", $REPO_URL
        echo "ISSUE_URL: ", $ISSUE_URL

        mkdir -p "$PATCH_DIR"

        for i in $(seq -w 1 3); do
            echo "Running iteration $i..."

            PATCH_PATH=$(find "$OUTPUT_DIR" -mindepth 1 -maxdepth 1 -type d | head -n 1)
            
            if [ -n "$PATCH_PATH" ] && [ -d "$PATCH_PATH" ]; then
                NEW_PATCH_PATH="$PATCH_DIR/$(basename "$PATCH_PATH")_patch_$i"
                mv "$PATCH_PATH" "$NEW_PATCH_PATH"
                echo "Patch $i already exists, moving patch to $NEW_PATCH_PATH"
            else

                sweagent run \
                  --agent.model.name="$MODEL_NAME" \
                  --agent.model.per_instance_cost_limit=0.99 \
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
    done
done 