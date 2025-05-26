from transformers import GenerationConfig

def main():
    try:
        print("Creating GenerationConfig...")
        config = GenerationConfig()
        
        print("Accessing _eos_token_tensor (should fail)...")
        print(config._eos_token_tensor)  # This is the problematic line
        print(f"✅ No failure.")

    except AttributeError as e:
        print(f"❌ AttributeError: {e}")
    except Exception as e:
        print(f"❌ Unexpected Exception: {e}")

if __name__ == "__main__":
    main()
