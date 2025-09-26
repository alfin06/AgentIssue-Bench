def run_reset_memories(scope):
    try:
        result = subprocess.run(
            ["crewai", "reset-memories", scope],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30
        )
        output = result.stdout + result.stderr
        print(output)
        if "disk I/O error" in output:
            print("✅ BUG REPRODUCED: disk I/O error occurred when resetting short-term memory.")
            return 0
        elif (
            "Long term memory has been reset" in output or
            "Short term memory has been reset" in output or
            "All memories have been reset" in output
        ):
            print("✅ TEST PASSED: Memory reset works as expected.")
            return 0
        else:
            print("❌ UNEXPECTED OUTPUT: Did not find expected error or success message.")
            return 1
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return 1