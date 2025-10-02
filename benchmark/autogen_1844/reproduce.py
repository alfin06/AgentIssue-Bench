import sys
from autogen.retrieve_utils import split_text_to_chunks

TEXT_LINES = [f"Line{i}" for i in range(20)]
TEXT = "\n".join(TEXT_LINES)
MAX_TOKENS = 12
OVERLAP = 2

def run_test(version: str) -> int:
    chunks = split_text_to_chunks(TEXT, max_tokens=MAX_TOKENS, overlap=OVERLAP)
    overlap_detected = False
    for i in range(1, len(chunks)):
        prev_lines = chunks[i-1].split("\n")
        curr_lines = chunks[i].split("\n")
        if len(prev_lines) < OVERLAP or len(curr_lines) < OVERLAP:
            continue
        prev_overlap = prev_lines[-OVERLAP:]
        curr_overlap = curr_lines[:OVERLAP]
        if prev_overlap == curr_overlap:
            overlap_detected = True
            break

    if version == "buggy":
        return 1 if overlap_detected else 0
    else:
        return 0 if overlap_detected else 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reproduce.py [buggy|fixed|patched]")
        sys.exit(2)

    version = sys.argv[1].lower()
    if version not in ["buggy", "fixed", "patched"]:
        print(f"Invalid version: {version}")
        sys.exit(2)

    exit_code = run_test(version)
    sys.exit(exit_code)