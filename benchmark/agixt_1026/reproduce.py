import sys
import os
import traceback

def test_voice_chat_extension(version):
    print(f"--- Testing AGiXT Issue #1026 with {version.upper()} version ---")
    print("Problem: bool object has no attribute 'lower' in voice_chat extension")
    print("-" * 60)
    
    source_dir = f"/app/source_code_{version}"
    if source_dir not in sys.path:
        sys.path.insert(0, source_dir)
    
    # Add the agixt subdirectory to the path if it exists
    agixt_dir = os.path.join(source_dir, "agixt")
    if os.path.exists(agixt_dir) and agixt_dir not in sys.path:
        sys.path.insert(0, agixt_dir)
    
    print(f"Python path: {sys.path}")
    
    # Try to locate the voice_chat.py file directly
    voice_chat_file = os.path.join(agixt_dir, "extensions", "voice_chat.py")
    if not os.path.exists(voice_chat_file):
        print(f"ERROR: voice_chat.py not found at {voice_chat_file}")
        for root, dirs, files in os.walk(source_dir):
            if "voice_chat.py" in files:
                print(f"Found voice_chat.py at {os.path.join(root, 'voice_chat.py')}")
                break
        return 2
    else:
        print(f"Found voice_chat.py at {voice_chat_file}")
    
    # These are the keyword arguments that the AGiXT application builds.
    # After the user saves their settings, the "true" string becomes a boolean.
    test_kwargs = {
        "USE_STREAMLABS_TTS": False,  # This boolean value is the cause of the bug
        "STREAMLABS_TTS_VOICE": "Joanna",
        "USE_GTTS": "false",
        "USE_HUGGINGFACE_TTS": "false",
    }
    
    print("\n--- Attempting to initialize the voice_chat extension with a boolean config value. ---")
    
    try:
        # Clear any previous imports
        if 'agixt.extensions.voice_chat' in sys.modules:
            del sys.modules['agixt.extensions.voice_chat']
        
        sys.path.insert(0, os.path.dirname(os.path.dirname(voice_chat_file)))
        from extensions.voice_chat import voice_chat
        print("Successfully imported voice_chat module")
    except ImportError as e:
        print(f"Import error with standard approach: {e}")
        
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("voice_chat", voice_chat_file)
            voice_chat_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(voice_chat_module)
            voice_chat = voice_chat_module.voice_chat
            print("Successfully imported voice_chat using importlib")
        except Exception as e:
            print(f"FATAL: Could not import voice_chat module: {e}")
            print(traceback.format_exc())
            return 2
    
    try:
        print("Creating voice_chat instance with kwargs:", test_kwargs)
        vc_extension = voice_chat(**test_kwargs)
        
        if version == "buggy":
            print("\n--- UNEXPECTED SUCCESS ---")
            print("❌ BUG NOT REPRODUCED: The extension initialized successfully with a boolean value.")
            return 1
        else:
            print("\n--- SUCCESS ---")
            print("✓ FIX VERIFIED: The extension now handles boolean values correctly.")
            return 0 
            
    except AttributeError as e:
        print(f"\n--- ERROR OCCURRED ---")
        print(f"Error Message: {e}")
        print(traceback.format_exc())
        
        expected_error_text = "'bool' object has no attribute 'lower'"
        if expected_error_text in str(e):
            if version == "buggy":
                print("\n✓ BUG SUCCESSFULLY REPRODUCED: 'bool' object has no attribute 'lower'")
                return 0
            else:
                print("\n❌ FIX FAILED: The AttributeError still occurs in the fixed version.")
                return 1
        else:
            print("\n❌ UNEXPECTED ERROR: The AttributeError message did not match the expected bug.")
            return 1
            
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {type(e).__name__}: {e}")
        print(traceback.format_exc())
        return 1

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python repro_script.py [buggy|fixed]")
        sys.exit(2)
    
    version = sys.argv[1]
    if version not in ["buggy", "fixed"]:
        print(f"Invalid version: {version}")
        sys.exit(2)
    
    exit_code = test_voice_chat_extension(version)
    sys.exit(exit_code)