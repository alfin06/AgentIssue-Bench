import time
import sys

def main():
    start = time.time()

    try:
        import crewai
    except Exception as e:
        print(f"❌ Import failed with error: {e}")
        sys.exit(1)

    duration = time.time() - start
    print(f"⏱ Import time: {duration:.2f} seconds")

    if duration >= 25:
        print("❌ BUG REPRODUCED: crewai import took too long (>= 25 seconds)")
        sys.exit(1)
    else:
        print("✅ crewai import completed in acceptable time")
        sys.exit(0)

if __name__ == "__main__":
    main()
