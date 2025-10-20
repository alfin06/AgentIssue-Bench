import sys
import subprocess

version = sys.argv[1] if len(sys.argv) > 1 else "buggy"
source_dir = sys.argv[2] if len(sys.argv) > 2 else "/app/source_code_buggy"

print(f"--- Reproducing InternLM/lagent issue #279: Missing tenacity dependency ---")
print(f"Testing version: {version}")
print(f"Source directory: {source_dir}")

def install_lagent():
    print(f"\n[STEP] Installing lagent from {source_dir} ...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True)
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", source_dir], check=True)
        print("[OK] lagent installed.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to install lagent: {e}")
        return False

def check_tenacity_installed():
    print("\n[STEP] Checking if tenacity is installed ...")
    try:
        import tenacity
        print("✅ tenacity is installed and importable.")
        return True
    except ImportError:
        print("❌ tenacity is NOT installed.")
        return False

def main():
    if version == "patched":
        print("\n[STEP] Testing patched code, assuming it is already installed ...")
        tenacity_exists = check_tenacity_installed()
        if tenacity_exists:
            print("\n✅ PATCH SUCCESSFULLY VERIFIED: tenacity is present after patch.")
            sys.exit(0)
        else:
            print("\n❌ PATCH NOT VERIFIED: tenacity is missing after patch.")
            sys.exit(1)
    else:
        success_install = install_lagent()
        tenacity_exists = check_tenacity_installed()
        if version == "buggy":
            if not tenacity_exists:
                print("\n✅ BUG REPRODUCED: tenacity is missing after installing lagent (buggy version).")
                sys.exit(0)
            else:
                print("\n❌ BUG NOT REPRODUCED: tenacity is present in buggy version.")
                sys.exit(1)
        else:
            if tenacity_exists:
                print("\n✅ FIX CONFIRMED: tenacity is present after installing lagent (fixed version).")
                sys.exit(0)
            else:
                print("\n❌ FIX NOT VERIFIED: tenacity is missing in fixed version.")
                sys.exit(1)

if __name__ == "__main__":
    main()