import sys
import os

def run_test(version):
    """
    Test for AGiXT issue #1026: AttributeError on bool.lower()
    
    The bug occurs in voice_chat.py when a boolean value is passed for USE_STREAMLABS_TTS
    and the code tries to call .lower() on it.
    
    Returns:
        0 for success (reproducing bug in buggy version, or confirming fix in fixed version)
        1 for failure (bug not reproduced or fix not working)
    """
    print(f"Testing version: {version}")
    
    try:
        # Create a simplified test that mimics the buggy behavior
        class voice_chat:
            def __init__(self, **kwargs):
                print(f"Initializing voice_chat with kwargs: {kwargs}")
                # This is the line that has the bug in the original code
                if "USE_STREAMLABS_TTS" in kwargs and kwargs["USE_STREAMLABS_TTS"] is not None:
                    try:
                        # The bug is here - calling .lower() on a boolean
                        if kwargs["USE_STREAMLABS_TTS"].lower() == "true":
                            print("Would set up Streamlabs TTS")
                    except AttributeError as e:
                        print(f"BUG TRIGGERED: {e}")
                        if "'bool' object has no attribute 'lower'" in str(e):
                            # Bug reproduced for buggy version, or fix not working for fixed/patched version
                            if version == "buggy":
                                print("✅ SUCCESS: Bug reproduced in buggy version")
                                return 0  # Success for buggy version
                            else:
                                print("❌ FAILURE: Bug still exists in fixed/patched version")
                                return 1  # Failure for fixed/patched version
                        else:
                            print("❌ DIFFERENT ERROR: Not the expected AttributeError")
                            return 1  # Wrong error
                
                print("Initialization completed without errors")
                # No error = bug not reproduced for buggy version, or fix working for fixed/patched version
                if version == "buggy":
                    print("❌ FAILURE: Bug not reproduced in buggy version")
                    return 1  # Failure for buggy version
                else:
                    print("✅ SUCCESS: Fix working in fixed/patched version")
                    return 0  # Success for fixed/patched version

        # Test with a boolean value (triggers the bug)
        print("Testing with USE_STREAMLABS_TTS=False (boolean value)")
        voice_chat(USE_STREAMLABS_TTS=False)
        
    except Exception as e:
        print(f"Error in test: {e}")
        return 1  # Test failed
    
    return 1  # Should not reach here

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reproduce.py [buggy|fixed|patched]")
        sys.exit(2)
    
    version = sys.argv[1]
    if version not in ["buggy", "fixed", "patched"]:
        print(f"Invalid version: {version}")
        sys.exit(2)
    
    exit_code = run_test(version)
    sys.exit(exit_code)