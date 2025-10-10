import os
import sys
import importlib
import subprocess
import tempfile
import shutil
import pkg_resources

# Get version parameter from command line
version = sys.argv[1] if len(sys.argv) > 1 else "buggy"
source_dir = sys.argv[2] if len(sys.argv) > 2 else "/app/source_code_buggy"

print(f"Testing lagent issue #279 - ModuleNotFoundError: No module named 'tenacity'")
print(f"Version being tested: {version}")
print(f"Source directory: {source_dir}")

def check_runtime_txt_for_tenacity():
    """
    Check if tenacity is listed in runtime.txt
    """
    print("\nChecking runtime.txt for tenacity dependency...")
    runtime_txt_path = os.path.join(source_dir, "runtime.txt")
    if not os.path.exists(runtime_txt_path):
        print(f"❌ runtime.txt not found at {runtime_txt_path}")
        return False
    with open(runtime_txt_path, 'r') as f:
        runtime_content = f.read()
    if "tenacity" in runtime_content:
        print("✅ Found tenacity in runtime.txt")
        lines = runtime_content.splitlines()
        for i, line in enumerate(lines):
            if "tenacity" in line:
                print(f"  Line {i+1}: {line}")
        return True
    else:
        print("❌ tenacity not found in runtime.txt")
        return False

def check_setup_py_for_tenacity():
    """
    Check if tenacity is listed in setup.py
    """
    print("\nChecking setup.py for tenacity dependency...")
    setup_py_path = os.path.join(source_dir, "setup.py")
    if not os.path.exists(setup_py_path):
        print(f"❌ setup.py not found at {setup_py_path}")
        return False
    with open(setup_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    if "tenacity" in content:
        print("✅ Found tenacity in setup.py")
        return True
    else:
        print("❌ tenacity not found in setup.py")
        return False

def check_dependencies_in_code():
    """
    Check if the code imports tenacity
    """
    print("\nChecking code for tenacity imports...")
    found_imports = []
    for root, dirs, files in os.walk(source_dir):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if "import tenacity" in content or "from tenacity" in content:
                            found_imports.append((file_path, content))
                except:
                    pass
    if found_imports:
        print(f"✅ Found {len(found_imports)} files that import tenacity:")
        for file_path, content in found_imports:
            rel_path = os.path.relpath(file_path, source_dir)
            print(f"  - {rel_path}")
            lines = content.splitlines()
            for i, line in enumerate(lines):
                if "tenacity" in line and ("import" in line or "from" in line):
                    print(f"    {line.strip()}")
        return True
    else:
        print("❌ No files found that import tenacity")
        return False

def install_and_check_dependencies():
    """
    Install the package and check if tenacity gets installed
    """
    print("\nInstalling lagent and checking dependencies...")
    temp_dir = tempfile.mkdtemp()
    venv_dir = os.path.join(temp_dir, "venv")
    try:
        print(f"Creating virtual environment in {venv_dir}...")
        subprocess.run([sys.executable, "-m", "venv", venv_dir], check=True)
        if os.name == 'nt':
            pip_path = os.path.join(venv_dir, "Scripts", "pip")
        else:
            pip_path = os.path.join(venv_dir, "bin", "pip")
        print("Upgrading pip...")
        subprocess.run([pip_path, "install", "--upgrade", "pip"], check=True)
        print(f"Installing lagent from {source_dir}...")
        subprocess.run([pip_path, "install", "-e", source_dir], check=True)
        print("Checking installed packages...")
        result = subprocess.run(
            [pip_path, "freeze"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        installed_packages = result.stdout.lower()
        if "tenacity" in installed_packages:
            print("✅ tenacity was installed as a dependency")
            return True
        else:
            print("❌ tenacity was not installed as a dependency")
            print("Installed packages:")
            print(installed_packages)
            return False
    except subprocess.CalledProcessError as e:
        print(f"Error during installation: {e}")
        print(f"Process output: {e.output if hasattr(e, 'output') else 'Not available'}")
        return False
    finally:
        try:
            shutil.rmtree(temp_dir)
        except:
            print(f"Warning: Failed to clean up temporary directory {temp_dir}")

def test_imports():
    """
    Test importing the modules that should use tenacity
    """
    print("\nTesting imports of modules that use tenacity...")
    sys.path.insert(0, source_dir)
    try:
        try:
            importlib.import_module("tenacity")
            tenacity_installed = True
            print("Note: tenacity is already installed in the current environment")
        except ImportError:
            tenacity_installed = False
            print("Note: tenacity is not installed in the current environment")
        try:
            from lagent.actions import AsyncWebBrowser
            print("✅ Successfully imported AsyncWebBrowser")
            if version == "buggy" and not tenacity_installed:
                print("❌ Expected ModuleNotFoundError but import succeeded without tenacity")
                return False
            elif version != "buggy":
                print("✅ FIX CONFIRMED: No error when importing AsyncWebBrowser")
                return True
            else:
                print("⚠️ Import succeeded but tenacity may be installed. Bug may exist but is masked.")
                return False
        except ImportError as e:
            if "No module named 'tenacity'" in str(e) and version == "buggy":
                print(f"✅ BUG REPRODUCED: {str(e)}")
                return True
            elif version != "buggy":
                print(f"❌ Fix not working: Still getting ImportError: {str(e)}")
                return False
            else:
                print(f"Got different ImportError than expected: {str(e)}")
                return False
    except Exception as e:
        print(f"Unexpected error during import test: {str(e)}")
        return False

def run_test():
    """Run the appropriate test based on version"""
    success = False

    if version == "patched":
        setup_check = check_setup_py_for_tenacity()
        if setup_check:
            print("\nPATCH VERIFIED: tenacity is listed in setup.py")
            return 0
        else:
            print("\n❌ PATCH NOT VERIFIED: tenacity is missing from setup.py")
            return 1

    runtime_check = check_runtime_txt_for_tenacity()
    code_check = check_dependencies_in_code()
    import_test = test_imports()
    install_check = install_and_check_dependencies()

    if version == "buggy":
        if (not runtime_check) and code_check and (import_test or not install_check):
            print("\n✅ BUG REPRODUCED: Code requires tenacity but it's not included as a dependency")
            success = True
        else:
            print("\n❌ FAILURE: Could not reproduce bug")
            success = False
    else:
        if runtime_check or install_check:
            print("\n✅ FIX CONFIRMED: tenacity is now included as a dependency")
            success = True
        else:
            print("\n❌ FAILURE: Could not confirm fix")
            success = False

    return 0 if success else 1

if __name__ == "__main__":
    exit_code = run_test()
    sys.exit(exit_code)