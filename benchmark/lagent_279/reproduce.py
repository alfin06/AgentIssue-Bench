import importlib.util
import subprocess
import sys

def check_module(name):
    spec = importlib.util.find_spec(name)
    if spec is None:
        print(f"❌ Missing dependency: {name}")
    else:
        print(f"✅ {name} is installed.")

def main():
    print("Installing lagent in current environment...")
    subprocess.run([sys.executable, "-m", "pip", "install", "lagent"], check=True)

    print("\nChecking for 'tenacity' dependency...")
    check_module("tenacity")

if __name__ == "__main__":
    main()
