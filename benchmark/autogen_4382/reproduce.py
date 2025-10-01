import sys

def run_test(version: str) -> int:
    try:
        import grpc
        grpc_installed = True
    except ImportError as e:
        print(f"❌ Reproduction successful: {e}")
        grpc_installed = False
    if version == "buggy":
        return 0 if not grpc_installed else 1
    elif version in ["fixed", "patched"]:
        return 0 if grpc_installed else 1
    else:
        print(f"Invalid version: {version}")
        return 2


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reproduce.py [buggy|fixed|patched]")
        sys.exit(2)

    version = sys.argv[1].lower()
    if version not in ["buggy", "fixed", "patched"]:
        print(f"Invalid version: {version}")
        sys.exit(2)

    exit_code = run_test(version)
    sys.exit(exit_code)