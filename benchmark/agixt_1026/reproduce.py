# reproduce.py

# Simulate kwargs passed into the voice_chat.py extension
def simulate_voice_chat_extension(kwargs):
    # This mimics the faulty line in AGiXT's /agixt/extensions/voice_chat.py
    # which assumes the value is a string.
    if kwargs["USE_STREAMLABS_TTS"].lower() == "true":
        print("TTS is enabled via Streamlabs")
    else:
        print("TTS is disabled")

if __name__ == "__main__":
    # Case 1: API returns or stores this as a proper string (expected behavior)
    try:
        print("Simulating with string input:")
        simulate_voice_chat_extension({"USE_STREAMLABS_TTS": "false"})
    except Exception as e:
        print("Error:", e)

    print()

    # Case 2: Buggy behavior - the value is a boolean (happens after save in AGiXT UI)
    try:
        print("Simulating with boolean input (as happens in AGiXT after save):")
        simulate_voice_chat_extension({"USE_STREAMLABS_TTS": False})  # This will cause AttributeError
    except Exception as e:
        print("Error:", e)
