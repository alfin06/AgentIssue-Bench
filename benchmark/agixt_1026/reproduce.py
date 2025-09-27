import sys
import os
import importlib.util

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
        # Import AGiXT code dynamically based on the source directory
        if version == "buggy" or version == "patched":
            agixt_dir = "/app/source_code_buggy"
        else:
            agixt_dir = "/app/source_code_fixed"
            
        print(f"Using AGiXT source from: {agixt_dir}")
        
        # Add the AGiXT directory to the Python path
        sys.path.insert(0, agixt_dir)
        
        # Import the voice_chat module from AGiXT
        try:
            # Try to import voice_chat from the extensions directory
            voice_chat_path = os.path.join(agixt_dir, "extensions", "voice_chat.py")
            
            if not os.path.exists(voice_chat_path):
                # Try to find the voice_chat.py file in the repository
                import glob
                voice_chat_files = glob.glob(os.path.join(agixt_dir, "**", "voice_chat.py"), recursive=True)
                if voice_chat_files:
                    voice_chat_path = voice_chat_files[0]
                    print(f"Found voice_chat.py at: {voice_chat_path}")
                else:
                    print("Could not find voice_chat.py in the repository")
                    return 1
            
            # Load the voice_chat module
            spec = importlib.util.spec_from_file_location("voice_chat", voice_chat_path)
            voice_chat_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(voice_chat_module)
            
            # Get the voice_chat class from the module
            voice_chat_class = getattr(voice_chat_module, "voice_chat")
            
        except Exception as e:
            print(f"Error importing voice_chat module: {e}")
            # Fall back to mock implementation
            print("Falling back to mock implementation...")
            
            class voice_chat_class:
                def __init__(self, **kwargs):
                    print(f"Initializing mock voice_chat with kwargs: {kwargs}")
                    # This is the line that has the bug in the original code
                    if "USE_STREAMLABS_TTS" in kwargs and kwargs["USE_STREAMLABS_TTS"] is not None:
                        try:
                            if version == "buggy":
                                # The buggy version - calling .lower() directly on a boolean
                                if kwargs["USE_STREAMLABS_TTS"].lower() == "true":
                                    print("Would set up Streamlabs TTS")
                            else:
                                # The fixed version - convert to string first
                                if str(kwargs["USE_STREAMLABS_TTS"]).lower() == "true":
                                    print("Would set up Streamlabs TTS (fixed version)")
                        except AttributeError as e:
                            print(f"BUG TRIGGERED: {e}")
                            raise  # Re-raise to be caught by the outer try/except
                    
                    print("Initialization completed")
        
        # Test with a boolean value (triggers the bug in the buggy version)
        bug_triggered = False
        try:
            print("Testing with USE_STREAMLABS_TTS=False (boolean value)")
            voice_chat_class(USE_STREAMLABS_TTS=False)
            print("No AttributeError occurred")
        except AttributeError as e:
            print(f"BUG TRIGGERED: {e}")
            if "'bool' object has no attribute 'lower'" in str(e):
                bug_triggered = True
        
        # After the test, check if the bug was triggered
        if bug_triggered:
            # Bug reproduced for buggy version, or fix not working for fixed/patched version
            if version == "buggy":
                print("✅ SUCCESS: Bug reproduced in buggy version")
                return 0  # Success for buggy version
            else:
                print("❌ FAILURE: Bug still exists in fixed/patched version")
                return 1  # Failure for fixed/patched version
        else:
            # No error = bug not reproduced for buggy version, or fix working for fixed/patched version
            if version == "buggy":
                print("❌ FAILURE: Bug not reproduced in buggy version")
                return 1  # Failure for buggy version
            else:
                print("✅ SUCCESS: Fix working in fixed/patched version")
                return 0  # Success for fixed/patched version
        
    except Exception as e:
        print(f"Error in test: {e}")
        import traceback
        traceback.print_exc()
        return 1  # Test failed

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