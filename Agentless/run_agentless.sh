#!/bin/bash

# Prompt for user input
read -p "Enter the model name: " MODEL
read -p "Enter the OPENAI_BASE_URL: " OPENAI_BASE_URL
read -p "Enter the OPENAI_API_KEY: " OPENAI_API_KEY
read -p "Enter the backend (e.g., openai, anthropic): " BACKEND

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export PYTHONPATH=$PYTHONPATH:$(pwd)
export OPENAI_BASE_URL="$OPENAI_BASE_URL"
export OPENAI_API_KEY="$OPENAI_API_KEY"

# Run the pipeline
python agentless/fl/localize.py --file_level --output_folder results-agentissue/swe-bench-lite/file_level --num_threads 1 --skip_existing --backend "$BACKEND" --model "$MODEL" --dataset_json agent_issue.json

python agentless/fl/localize.py --file_level --irrelevant --output_folder results-agentissue/swe-bench-lite/file_level_irrelevant --num_threads 1 --skip_existing --backend "$BACKEND" --model "$MODEL" --dataset_json agent_issue.json

python agentless/fl/retrieve.py --index_type simple --filter_type given_files --filter_file results-agentissue/swe-bench-lite/file_level_irrelevant/loc_outputs.jsonl --output_folder results-agentissue/swe-bench-lite/retrievel_embedding --persist_dir embedding/swe-bench_simple --num_threads 1 --dataset_json agent_issue.json

python agentless/fl/combine.py --retrieval_loc_file results-agentissue/swe-bench-lite/retrievel_embedding/retrieve_locs.jsonl --model_loc_file results-agentissue/swe-bench-lite/file_level/loc_outputs.jsonl --top_n 3 --output_folder results-agentissue/swe-bench-lite/file_level_combined

python agentless/fl/localize.py --related_level --output_folder results-agentissue/swe-bench-lite/related_elements --top_n 3 --compress_assign --compress --start_file results-agentissue/swe-bench-lite/file_level_combined/combined_locs.jsonl --num_threads 1 --skip_existing --backend "$BACKEND" --model "$MODEL" --dataset_json agent_issue.json

python agentless/fl/localize.py --fine_grain_line_level --output_folder results-agentissue/swe-bench-lite/edit_location_samples --top_n 3 --compress --temperature 0.8 --num_samples 1 --start_file results-agentissue/swe-bench-lite/related_elements/loc_outputs.jsonl --num_threads 1 --skip_existing --backend "$BACKEND" --model "$MODEL" --dataset_json agent_issue.json

python agentless/fl/localize.py --merge --output_folder results-agentissue/swe-bench-lite/edit_location_individual --top_n 3 --num_samples 1 --start_file results-agentissue/swe-bench-lite/edit_location_samples/loc_outputs.jsonl --backend "$BACKEND" --model "$MODEL" --dataset_json agent_issue.json

python agentless/repair/repair.py --loc_file results-agentissue/swe-bench-lite/edit_location_individual/loc_merged_0-0_outputs.jsonl --output_folder results-agentissue/swe-bench-lite/repair_sample_1 --loc_interval --top_n=3 --context_window=10 --max_samples 1 --cot --diff_format --gen_and_process --num_threads 2 --backend "$BACKEND" --model "$MODEL" --dataset_json agent_issue.json
