import importlib.util
import traceback

def check_submodule(module_path: str):
    try:
        __import__(module_path)
        print(f"✅ '{module_path}' is available.")
    except ModuleNotFoundError as e:
        print(f"❌ ModuleNotFoundError: {e}")
    except Exception:
        print(f"❌ Unexpected error when checking '{module_path}':")
        traceback.print_exc()

def main():
    print("Checking for 'griffe.enumerations' submodule...\n")
    check_submodule("griffe.enumerations")

if __name__ == "__main__":
    main()