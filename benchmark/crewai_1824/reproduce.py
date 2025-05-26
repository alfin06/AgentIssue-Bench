import subprocess
import sys

def verify_tiktoken():
    try:
        from importlib.metadata import version
        ver = version("tiktoken")
        print(f"🔍 tiktoken version installed: {ver}")
    except Exception:
        print("❌ tiktoken is not installed or import failed.")

def run_install():
    try:
        print("🔄 Attempting to install crewai (and tiktoken==0.7.0)...")
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "crewai==0.84.0"],
            capture_output=True,
            text=True,
            check=True
        )
        print("Installation finish")
        verify_tiktoken()
    except subprocess.CalledProcessError as e:
        print("❌ Installation failed!")
        print("❌ tiktoken is not installed or import failed.")

if __name__ == "__main__":
    run_install()
