import os
import sys
import time
import tempfile
import subprocess
from pathlib import Path

def run_test(version):
    print(f"\n--- Testing CrewAI Issue #1370 - Slow import time ---")
    print(f"--- Version: {version.upper()} ---")
    
    # Create a temporary file to test import time
    fd, path = tempfile.mkstemp(suffix='.py')
    
    try:
        with os.fdopen(fd, 'w') as f:
            f.write("""
import time
import sys

start = time.time()
print("Starting crewai import...")

try:
    import crewai
    end = time.time()
    import_time = end - start
    print(f"Import completed in {import_time:.2f} seconds")
    
    # Success threshold set to 10 seconds (original issue mentioned 25+ seconds)
    # For buggy version, success means it's slow (>10 seconds)
    # For fixed version, success means it's fast (<10 seconds)
    is_slow = import_time > 10.0
    
    if sys.argv[1] == "buggy":
        # For buggy version, we expect it to be slow
        if is_slow:
            print(f"✓ BUG CONFIRMED: Import took {import_time:.2f} seconds (>10 seconds)")
            sys.exit(0)  # Success for buggy version
        else:
            print(f"✗ BUG NOT REPRODUCED: Import only took {import_time:.2f} seconds (<10 seconds)")
            sys.exit(1)  # Failure for buggy version
    else:
        # For fixed version, we expect it to be fast
        if not is_slow:
            print(f"✓ FIX CONFIRMED: Import only took {import_time:.2f} seconds (<10 seconds)")
            sys.exit(0)  # Success for fixed version
        else:
            print(f"✗ FIX NOT CONFIRMED: Import still took {import_time:.2f} seconds (>10 seconds)")
            sys.exit(1)  # Failure for fixed version
            
except ImportError as e:
    print(f"Error importing crewai: {e}")
    sys.exit(2)
""")
        
        # Run the test script with the version argument
        print("\nRunning import time test...")
        start_time = time.time()
        result = subprocess.run(['python', path, version], capture_output=True, text=True)
        elapsed = time.time() - start_time
        
        # Print the output
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
            
        print(f"Total process runtime: {elapsed:.2f} seconds")
        
        # Return the exit code from the test script
        return result.returncode == 0
        
    except Exception as e:
        print(f"\nError during test: {e}")
        return False
    finally:
        # Clean up
        try:
            os.unlink(path)
        except:
            pass

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reproduce.py [buggy|fixed]")
        sys.exit(2)
    
    version = sys.argv[1]
    if version not in ["buggy", "fixed"]:
        print(f"Invalid version: {version}")
        sys.exit(2)
    
    success = run_test(version)
    if success:
        sys.exit(0)  # Success - test passed
    else:
        sys.exit(1)  # Failure - test failed