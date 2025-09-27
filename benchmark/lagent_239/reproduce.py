import os
import sys
import subprocess
import tempfile
import shutil

# Get version parameter from command line
version = sys.argv[1] if len(sys.argv) > 1 else "buggy"
source_dir = sys.argv[2] if len(sys.argv) > 2 else "/app/source_code_buggy"

print(f"Testing lagent issue #239 - ModuleNotFoundError: No module named 'griffe.enumerations'")
print(f"Version being tested: {version}")
print(f"Source directory: {source_dir}")

def check_dependency_files():
    """Check all possible dependency files for griffe version constraint"""
    print("\nChecking dependency files for griffe version constraint...")
    
    files_to_check = [
        "runtime.txt",
        "requirements.txt",
        "setup.py",
        "pyproject.toml"
    ]
    
    found_constraint = False
    constraint_file = None
    constraint_text = None
    
    for filename in files_to_check:
        file_path = os.path.join(source_dir, filename)
        if os.path.exists(file_path):
            print(f"Checking {filename}...")
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Check for various constraint patterns
            constraints = ["griffe<1", "griffe < 1", "griffe<=0", "griffe <= 0"]
            for constraint in constraints:
                if constraint in content:
                    found_constraint = True
                    constraint_file = filename
                    constraint_text = constraint
                    print(f"✅ Found constraint '{constraint}' in {filename}")
                    
                    # Find the context around the constraint
                    lines = content.splitlines()
                    for i, line in enumerate(lines):
                        if constraint in line:
                            print(f"  Line {i+1}: {line.strip()}")
                    
                    break
            
            # Also look for exact version specifications
            import re
            version_match = re.search(r'griffe==0\.\d+\.\d+', content)
            if version_match and not found_constraint:
                found_constraint = True
                constraint_file = filename
                constraint_text = version_match.group(0)
                print(f"✅ Found exact version '{constraint_text}' in {filename}")
        else:
            print(f"{filename} not found")
    
    return found_constraint, constraint_file, constraint_text

def test_install_behavior():
    """Install lagent and test its behavior with griffe"""
    print("\nTesting installation behavior...")
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Create a simple test script
        test_script = """
import sys
import subprocess
import os

# Install lagent
print(f"Installing lagent from {sys.argv[1]}...")
try:
    # First, try installing with pip
    proc = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-e", sys.argv[1]], 
        capture_output=True,
        text=True
    )
    
    if proc.returncode != 0:
        print(f"Installation failed with exit code {proc.returncode}")
        if proc.stderr:
            print(f"Error output: {proc.stderr}")
        if proc.stdout:
            print(f"Standard output: {proc.stdout}")
    else:
        print("Installation completed successfully")
    
    # Check what griffe version was installed
    result = subprocess.run(
        [sys.executable, "-m", "pip", "show", "griffe"], 
        capture_output=True,
        text=True
    )
    
    griffe_version = "Unknown"
    if result.returncode == 0:
        for line in result.stdout.splitlines():
            if line.startswith("Version:"):
                griffe_version = line.split("Version:")[1].strip()
                break
        
        print(f"Griffe version installed: {griffe_version}")
        
        # Check if version is >= 1.0
        major_version = int(griffe_version.split('.')[0])
        if major_version >= 1:
            print("Using griffe 1.x (lacks enumerations module)")
        else:
            print("Using griffe 0.x (should have enumerations module)")
    else:
        print("Griffe not installed")
    
    # Try importing the enumerations module directly
    try:
        import griffe.enumerations
        print("griffe.enumerations exists")
    except ImportError:
        print("griffe.enumerations not found")
    
    # Try importing lagent modules
    try:
        print("Attempting to import lagent...")
        import lagent
        print("Successfully imported lagent")
        
        print("Attempting to import lagent.schema...")
        from lagent import schema
        print("Successfully imported lagent.schema")
        print("IMPORT_SUCCESS")
        
    except ImportError as e:
        print(f"Import error: {e}")
        if "griffe.enumerations" in str(e):
            print("GRIFFE_ENUM_ERROR")
        else:
            print("OTHER_IMPORT_ERROR")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
"""

        test_path = os.path.join(temp_dir, "test.py")
        with open(test_path, 'w') as f:
            f.write(test_script)
        
        # Run the test script
        print("\nInstalling lagent and testing imports...")
        result = subprocess.run(
            [sys.executable, test_path, source_dir],
            capture_output=True,
            text=True
        )
        
        # Print the output
        stdout = result.stdout.strip()
        print(stdout)
        if result.stderr:
            print(f"STDERR: {result.stderr}")
        
        # Analyze results
        griffe_version = "Unknown"
        for line in stdout.splitlines():
            if "Griffe version installed:" in line:
                griffe_version = line.split("Griffe version installed:")[1].strip()
                break
        
        is_griffe_1x = False
        if griffe_version != "Unknown":
            try:
                is_griffe_1x = int(griffe_version.split('.')[0]) >= 1
            except:
                pass
                
        has_enum_error = "GRIFFE_ENUM_ERROR" in stdout
        import_success = "IMPORT_SUCCESS" in stdout
        
        results = {
            "griffe_version": griffe_version,
            "is_griffe_1x": is_griffe_1x,
            "has_enum_error": has_enum_error,
            "import_success": import_success
        }
        
        print(f"\nTest results: {results}")
        
        return results
    
    finally:
        # Clean up
        try:
            shutil.rmtree(temp_dir)
        except:
            pass

def run_test():
    """Run the test based on version"""
    # First check dependency files
    has_constraint, constraint_file, constraint_text = check_dependency_files()
    
    # Test actual installation behavior
    install_results = test_install_behavior()
    
    if version == "buggy":
        if install_results["has_enum_error"] or (install_results["is_griffe_1x"] and not install_results["import_success"]):
            print("\n✅ BUG REPRODUCED: Issue with griffe.enumerations")
            return 0
        elif has_constraint:
            print(f"\n✅ BUG REPRODUCED: The issue exists but version constraint ({constraint_text}) already prevents it in {constraint_file}")
            return 0
        elif not install_results["is_griffe_1x"]:
            print("\n❓ Lagent installs griffe < 1.0 even without explicit constraint")
            print("This is unexpected but means the bug wasn't triggered.")
            return 1
        else:
            print("\n❌ FAILURE: Could not reproduce bug")
            return 1
    else:
        # For fixed version, check if constraint was added OR if it installs a compatible griffe version
        if has_constraint:
            print(f"\n✅ FIX CONFIRMED: Version constraint ({constraint_text}) added in {constraint_file}")
            return 0
        elif not install_results["is_griffe_1x"]:
            print("\n✅ FIX CONFIRMED: Lagent now installs griffe < 1.0 (version with enumerations module)")
            return 0
        elif install_results["is_griffe_1x"] and install_results["import_success"]:
            print("\n✅ FIX CONFIRMED: Lagent works with griffe 1.x (fixed differently than expected)")
            return 0
        else:
            print("\n❌ FAILURE: Could not confirm fix")
            return 1

if __name__ == "__main__":
    try:
        print("Starting test execution...")
        exit_code = run_test()
        print(f"Test completed with exit code: {exit_code}")
        sys.exit(exit_code)
    except Exception as e:
        print(f"Error in main test execution: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)