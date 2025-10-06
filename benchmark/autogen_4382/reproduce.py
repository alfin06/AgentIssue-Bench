import sys

def run_buggy_test():
    try:
        import grpc
        print("❌ grpc module exists (bug not reproduced)")
        return 1
    except ModuleNotFoundError:
        print("✅ Bug reproduced: No module named 'grpc'")
        return 0

def run_fixed_test():
    try:
        import grpc
        print("✅ Fixed: grpc module exists")
        return 0
    except ModuleNotFoundError:
        print("❌ Bug still present: No module named 'grpc'")
        return 1

def main():
    if len(sys.argv) < 2:
        print("Usage: python reproduce.py [buggy|fixed|patched]")
        sys.exit(2)
    version = sys.argv[1]
    if version == "buggy":
        sys.exit(run_buggy_test())
    elif version in ("fixed", "patched"):
        sys.exit(run_fixed_test())
    else:
        print(f"Unknown version: {version}")
        sys.exit(2)

if __name__ == "__main__":
    main()