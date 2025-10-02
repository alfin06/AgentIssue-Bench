import sys

def run_test(version):

    try:
        from camel.toolkits.math_toolkit import MathToolkit
        print("Hello, World!")
        success = False
    except ModuleNotFoundError as e:
        if "requests_oauthlib" in str(e):
            success = True
        else:
            success = False
    except Exception as e:
        success = False

    if version == "buggy":
        return 1 if success else 0
    elif version in ["fixed", "patched"]:
        return 1 if success else 0
    else:
        return 2

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