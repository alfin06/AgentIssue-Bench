import sys
from unittest.mock import patch

# --- Test Setup ---
try:
    from agixt.extensions.voice_chat import voice_chat
except ImportError as e:
    print(f"FATAL: Could not import the necessary module. Check the installation. Error: {e}")
    sys.exit(1)

# These are the keyword arguments that the AGiXT application builds.
# After the user saves their settings, the "true" string becomes a boolean.
buggy_kwargs = {
    "USE_STREAMLABS_TTS": False,  # This boolean value is the cause of the bug
    "STREAMLABS_TTS_VOICE": "Joanna",
    "USE_GTTS": "false",
    "USE_HUGGINGFACE_TTS": "false",
}

print("--- Attempting to initialize the voice_chat extension with a boolean config value. ---")
print("--- This is expected to raise an AttributeError in the buggy version. ---")

# --- Verification Logic ---
try:
    vc_extension = voice_chat(**buggy_kwargs)

    print("\n--- SCRIPT FINISHED UNEXPECTEDLY ---")
    print("FAILURE: The bug was NOT reproduced. The extension initialized successfully.")
    sys.exit(0)

except AttributeError as e:
    print(f"\nSUCCESS: The script failed with an AttributeError as expected.")
    print(f"Error Message: {e}")

    expected_error_text = "'bool' object has no attribute 'lower'"
    if expected_error_text in str(e):
        print("\nVerification successful: The error message matches the bug report.")
        sys.exit(1)
    else:
        print("\nVerification failed: The AttributeError message did not match the expected bug.")
        sys.exit(0)
except Exception as e:
    print(f"\nFAILURE: An unexpected error occurred: {type(e).__name__}: {e}")
    sys.exit(0)
