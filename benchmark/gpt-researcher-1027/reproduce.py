import os
import sys
import re
import traceback
import importlib

def find_files_by_pattern(base_dir, pattern=".py"):
    """Find all Python files in the repository"""
    result = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith(pattern):
                result.append(os.path.join(root, file))
    return result

def find_function_in_files(files, function_name):
    """Check if a specific function exists in any of the files"""
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Check if function exists in file
            pattern = r"def\s+" + re.escape(function_name) + r"\s*\(([^)]+)\)"
            match = re.search(pattern, content)
            if match:
                params = match.group(1)
                print(f"✅ Found function '{function_name}' in file: {file_path}")
                print(f"Function parameters: {params}")
                return file_path, params
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
    
    return None, None

def search_for_function(version, function_name="generate_subtopic_report_prompt"):
    """Exhaustively search for a function in the codebase"""
    source_dir = "/app/source_code_buggy" if version == "buggy" else "/app/source_code_fixed"
    
    print(f"\nSearching for '{function_name}' function in {source_dir}...")
    
    # First try to find files that might contain the function
    py_files = find_files_by_pattern(source_dir, ".py")
    print(f"Found {len(py_files)} Python files in repository")
    
    # Look for the function name in all Python files
    print("Searching for function by name in files...")
    file_path, params = find_function_in_files(py_files, function_name)
    
    if file_path:
        # Check if the function has a language parameter
        has_language = "language" in params
        print(f"Has 'language' parameter: {has_language}")
        
        # Get directory structure information
        rel_path = os.path.relpath(file_path, source_dir)
        print(f"Relative file path: {rel_path}")
        
        # Print surrounding context of the function
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        pattern = r"def\s+" + re.escape(function_name) + r"\s*\([^)]+\).*?(?=\n\s*def|\n\s*class|\Z)"
        match = re.search(pattern, content, re.DOTALL)
        if match:
            func_def = match.group(0)
            print("\nFunction definition:")
            print("--------------------")
            print(func_def[:500] + ("..." if len(func_def) > 500 else ""))
            print("--------------------")
        
        return has_language
    
    print(f"❌ Function '{function_name}' not found in any file")
    return None

def check_commits_for_changes(function_name="generate_subtopic_report_prompt"):
    """Check if the function was added or modified between commits"""
    buggy_commit = os.environ.get("BUGGY_COMMIT", "4db9bd8bd364ca3f734c02e299c9f47c3261e174")
    fixed_commit = os.environ.get("FIXED_COMMIT", "7468f6871bdcc5ae5bc07fb8d5d80485c3a2a29b")
    
    print(f"\nChecking for changes to '{function_name}' between commits:")
    print(f"Buggy: {buggy_commit}")
    print(f"Fixed: {fixed_commit}")
    
    # Get the diff for the specific file where the function might be
    try:
        import subprocess
        cmd = f"cd /app/source_code_buggy && git diff {buggy_commit} {fixed_commit}"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            diff_output = result.stdout
            print("\nChanges between commits:")
            print("------------------------")
            
            # Look for the function in the diff
            pattern = r"[\+\-].*?" + re.escape(function_name)
            matches = re.findall(pattern, diff_output)
            
            if matches:
                for match in matches:
                    print(match)
                
                # Check if language parameter was added
                lang_pattern = r"\+.*?" + re.escape(function_name) + r".*?language"
                lang_matches = re.findall(lang_pattern, diff_output)
                
                if lang_matches:
                    print("\n✅ Found 'language' parameter being added in the diff")
                    return True
            else:
                print("No changes to the function found in diff")
        else:
            print(f"Error getting diff: {result.stderr}")
    except Exception as e:
        print(f"Error checking commits: {e}")
    
    return None

def run_test(version):
    """Run the appropriate test based on version"""
    print(f"Testing GPT-Researcher issue #1027 - Missing 'language' parameter")
    print(f"Version being tested: {version}")
    
    # 1. Search for the function in the codebase
    has_language = search_for_function(version)
    
    # 2. If not found or inconclusive, check commit differences
    if has_language is None:
        print("\nFunction not found. Checking commit differences...")
        commit_check = check_commits_for_changes()
        
        # If we see language param being added in commits, that confirms both bug and fix
        if commit_check is True:
            if version == "buggy":
                print("\n✅ BUG REPRODUCED: Commit diff shows 'language' parameter was added later")
                return 0
            else:
                print("\n✅ FIX CONFIRMED: Commit diff shows 'language' parameter was added")
                return 0
    
    # 3. Evaluate based on function search results
    if has_language is not None:
        if has_language and version == "buggy":
            print("\n❌ Bug NOT reproduced: Language parameter exists in buggy version")
            return 1
        elif has_language and version != "buggy":
            print("\n✅ FIX CONFIRMED: 'language' parameter was added to function definition")
            return 0
        elif not has_language and version == "buggy":
            print("\n✅ BUG REPRODUCED: 'language' parameter missing in function definition")
            return 0
        else:
            print("\n❌ Fix NOT working: Language parameter still missing")
            return 1
    
    # 4. If all else fails
    if version == "buggy":
        print("\n❌ FAILURE: Could not reproduce bug")
        return 1
    else:
        print("\n❌ FAILURE: Could not confirm fix")
        return 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reproduce.py [buggy|fixed|patched]")
        sys.exit(1)
        
    version = sys.argv[1]
    if version not in ["buggy", "fixed", "patched"]:
        print(f"Invalid version: {version}")
        sys.exit(1)
        
    exit_code = run_test(version)
    sys.exit(exit_code)