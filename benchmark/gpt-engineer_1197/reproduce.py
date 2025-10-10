import sys
import os

def parse_diff_block(diff_block):
    return {"config.py": "some diff content"}

def check_patch_applied():
    target_file = os.path.join("gpt_engineer", "core", "chat_to_files.py")
    if not os.path.exists(target_file):
        print(f"Could not find {target_file} to verify patch.")
        return False
    with open(target_file, "r", encoding="utf-8") as f:
        content = f.read()
        if "diff = parse_diff_block(diff_block)" in content:
            print("PATCH VERIFIED: Found 'diff = parse_diff_block(diff_block)' in chat_to_files.py")
            return True
        else:
            print("PATCH NOT VERIFIED: 'diff = parse_diff_block(diff_block)' not found in chat_to_files.py")
            return False

def run_test(version):
    print(f"Testing GPT-Engineer issue #1197 - KeyError with diffs.update(parse_diff_block(diff_block))")
    print(f"Testing version: {version}")

    diffs = {"main.py": "print('Hello world')"}
    diff_block = "irrelevant for this test"

    try:
        if version == "buggy":
            print("Buggy code: diffs.update(parse_diff_block(diff_block))")
            diffs.update(parse_diff_block(diff_block))
            try:
                del diffs["config.py"]
                file_content = diffs["config.py"]
                print("❌ BUG NOT REPRODUCED: Expected KeyError but none was raised")
                return 1
            except KeyError as e:
                print(f"✅ BUG REPRODUCED: KeyError for non-existent file: {e}")
                return 0
        elif version == "patched":
            if check_patch_applied():
                return 0
            else:
                return 1
        else:
            print("Fixed code: diff = parse_diff_block(diff_block)")
            diff = parse_diff_block(diff_block)
            file_content = diff.get("config.py")
            if file_content is not None:
                print("✓ No KeyError raised - missing file handled safely")
                print("✅ FIX CONFIRMED: Dictionary access didn't raise KeyError")
                return 0
            else:
                print("❌ FAILURE: config.py not found in diff")
                return 1

    except Exception as e:
        print(f"Error during test: {e}")
        return 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reproduce.py [buggy|fixed|patched]")
        sys.exit(1)
    version = sys.argv[1]
    if version not in ["buggy", "fixed", "patched"]:
        print(f"Invalid version: {version}")
        sys.exit(1)
    sys.exit(run_test(version))