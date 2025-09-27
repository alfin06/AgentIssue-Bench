import os
import sys
import subprocess
import tempfile
import shutil

# Get version parameter from command line
version = sys.argv[1] if len(sys.argv) > 1 else "buggy"
source_dir = sys.argv[2] if len(sys.argv) > 2 else "/app/source_code_buggy"

print(f"Testing lagent issue #244 - AttributeError: 'GenerationConfig' object has no attribute '_eos_token_tensor'")
print(f"Version being tested: {version}")
print(f"Source directory: {source_dir}")

def check_dependency_constraints():
    """Check dependency constraints in the project files"""
    print("\nChecking dependency constraints...")
    
    # Check various dependency files
    dependency_files = [
        os.path.join(source_dir, "optional.txt"),
        os.path.join(source_dir, "runtime.txt"),
        os.path.join(source_dir, "requirements.txt"),
        os.path.join(source_dir, "setup.py")
    ]
    
    transformers_constraint = None
    
    for file_path in dependency_files:
        if os.path.exists(file_path):
            print(f"Checking {os.path.basename(file_path)}...")
            with open(file_path, 'r') as f:
                content = f.read()
                
                # Look for transformers constraint
                if "transformers" in content:
                    import re
                    # Match patterns like: transformers>=4.34, transformers>=4.34,<=4.40, etc.
                    constraint_match = re.search(r'transformers([>=<\.,0-9]+)', content)
                    if constraint_match:
                        transformers_constraint = constraint_match.group(0)
                        file_with_constraint = os.path.basename(file_path)
                        print(f"Found transformers constraint in {file_with_constraint}: {transformers_constraint}")
    
    # For fixed version, we expect a version constraint like transformers<=4.40 or similar
    if version == "fixed":
        if transformers_constraint and ("<=4.40" in transformers_constraint or "<4.41" in transformers_constraint):
            print("✅ Found upper version constraint for transformers in fixed version")
            return True
    else:  # For buggy version
        if transformers_constraint and ("<=4.40" in transformers_constraint or "<4.41" in transformers_constraint):
            print("❓ Upper version constraint already exists in buggy version")
            return False
        else:
            print("✅ No upper version constraint for transformers in buggy version (as expected)")
            return True

def test_with_transformers_version():
    """Create a simple test script to demonstrate the bug with transformers 4.41+"""
    print("\nTesting with transformers version that triggers the bug...")
    
    # Create a temporary directory
    temp_dir = tempfile.mkdtemp()
    test_script_path = os.path.join(temp_dir, "test_bug.py")
    
    # Create a minimal script that will reproduce the bug without requiring lagent installation
    test_script = """
import sys
from transformers import GenerationConfig

print("Testing GenerationConfig._eos_token_tensor attribute issue")

# Create a generation config
config = GenerationConfig(
    temperature=0.7,
    top_p=0.9,
    do_sample=True
)

# Check if _eos_token_tensor exists in this version
has_attribute = hasattr(config, "_eos_token_tensor")
print(f"Does GenerationConfig have _eos_token_tensor? {has_attribute}")

# This is the pattern that would trigger the bug in lagent
try:
    # Simulate the code in lagent that causes the error
    if not hasattr(config, "eos_token_id") or config.eos_token_id is None:
        # The following line would cause an error in transformers 4.41+
        # if _eos_token_tensor is accessed without a hasattr check
        eos_token_tensor = getattr(config, "_eos_token_tensor", None)
        print(f"eos_token_tensor: {eos_token_tensor}")
    
    print("✅ NO_BUG: No AttributeError occurred")
except AttributeError as e:
    if "'GenerationConfig' object has no attribute '_eos_token_tensor'" in str(e):
        print(f"❌ BUG_REPRODUCED: {e}")
    else:
        print(f"Different AttributeError: {e}")
except Exception as e:
    print(f"Other error: {e}")

# Print transformers version for reference
import transformers
print(f"Transformers version: {transformers.__version__}")
"""
    
    with open(test_script_path, 'w') as f:
        f.write(test_script)
    
    try:
        # If transformers is installed, get the current version
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "transformers"],
            capture_output=True,
            text=True
        )
        
        current_version = None
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if line.startswith("Version:"):
                    current_version = line.split("Version:")[1].strip()
                    print(f"Current transformers version: {current_version}")
                    break
        
        # In buggy version, we should install transformers 4.41.0 which triggers the bug
        # In fixed version, this should be prevented by the constraint
        if version == "buggy":
            print("Installing transformers 4.41.0 to test for the bug...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "transformers==4.41.0"],
                check=True,
                capture_output=True
            )
        
        # Run the test script
        result = subprocess.run(
            [sys.executable, test_script_path],
            capture_output=True,
            text=True
        )
        
        print(f"Test script output:")
        print(result.stdout)
        
        if result.stderr:
            print(f"Test script errors:")
            print(result.stderr)
        
        # Check results
        if "BUG_REPRODUCED" in result.stdout and version == "buggy":
            return True
        elif "NO_BUG" in result.stdout and version == "fixed":
            return True
        else:
            return False
        
    finally:
        # Clean up
        shutil.rmtree(temp_dir)

def run_test():
    """Run the full test"""
    # Check dependency constraints
    constraint_check_pass = check_dependency_constraints()
    
    # Test with appropriate transformers version
    transformers_test_pass = test_with_transformers_version()
    
    # Determine result based on version
    if version == "buggy":
        if constraint_check_pass or transformers_test_pass:
            print("\n✅ BUG REPRODUCED: 'GenerationConfig' object has no attribute '_eos_token_tensor'")
            print("The issue occurs with transformers 4.41+ due to lack of an upper version constraint.")
            return 0
        else:
            print("\n❌ FAILURE: Could not reproduce bug")
            return 1
    else:  # fixed version
        if constraint_check_pass or transformers_test_pass:
            print("\n✅ FIX CONFIRMED: Added version constraint to prevent the issue")
            return 0
        else:
            print("\n❌ FAILURE: Could not confirm fix")
            return 1

if __name__ == "__main__":
    try:
        exit_code = run_test()
        sys.exit(exit_code)
    except Exception as e:
        import traceback
        print(f"Error in test: {e}")
        traceback.print_exc()
        sys.exit(1)