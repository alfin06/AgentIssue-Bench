import subprocess
import sys
import importlib.metadata

def test_tiktoken_build(version="buggy"):
    try:
        print("🔄 Testing if tiktoken==0.7.0 builds successfully...")
        
        # For buggy version, attempt to install tiktoken directly
        if version == "buggy":
            # First install crewai 0.86.0 as mentioned in the issue
            print("Installing crewai==0.86.0...")
            crewai_result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "crewai==0.86.0"],
                capture_output=True,
                text=True
            )
            print(crewai_result.stdout)
            if crewai_result.stderr:
                print("STDERR (crewai install):", crewai_result.stderr)
            
            # Now try to install tiktoken
            print("Attempting to install tiktoken==0.7.0...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "tiktoken==0.7.0", "--force-reinstall"],
                capture_output=True,
                text=True
            )
        else:
            # For fixed version, install from the fixed code and then test tiktoken
            print("Installing fixed crewai version...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "-e", "."],
                check=False,
                capture_output=True
            )
            
            # Now try to install tiktoken
            print("Attempting to install tiktoken==0.7.0...")
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "tiktoken==0.7.0", "--force-reinstall"],
                capture_output=True,
                text=True
            )
            
        print(result.stdout)
        if result.stderr:
            print("STDERR (tiktoken install):", result.stderr)
            
        # Check for dependency conflicts with tiktoken
        has_conflict = False
        full_output = result.stdout + result.stderr
        if "requires tiktoken" in full_output and "which is incompatible" in full_output:
            has_conflict = True
            print("✅ BUG REPRODUCED: Dependency conflict with tiktoken==0.7.0")
            if version == "buggy":
                return 0  # Expected for buggy version
            else:
                return 1  # Not expected for fixed version
            
        # Check if installation failed
        if result.returncode != 0:
            if "error" in full_output.lower() and any(err in full_output.lower() for err in ["build", "compil", "rust"]):
                print("✅ BUG REPRODUCED: Failed to build tiktoken==0.7.0")
                return 0 if version == "buggy" else 1
            else:
                print(f"❌ UNEXPECTED FAILURE: Installation failed but not due to build error")
                return 1
        else:
            # Installation succeeded, check if usable
            try:
                # Get version using importlib.metadata
                tiktoken_version = importlib.metadata.version('tiktoken')
                
                # Try to import tiktoken to verify it's working
                import tiktoken
                enc = tiktoken.get_encoding("cl100k_base") 
                
                if not has_conflict:
                    print(f"✅ TEST PASSED: Successfully installed tiktoken {tiktoken_version} without conflicts")
                    return 0 if version != "buggy" else 1
                else:
                    return 0 if version == "buggy" else 1
            except Exception as e:
                print(f"❌ Error importing or using tiktoken: {e}")
                return 1
                
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return 1

if __name__ == "__main__":
    version = sys.argv[1] if len(sys.argv) > 1 else "buggy"
    sys.exit(test_tiktoken_build(version))