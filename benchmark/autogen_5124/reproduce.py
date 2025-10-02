import sys
from pathlib import Path

TARGET = Path("python/samples/core_grpc_worker_runtime/run_host.py")


def run_test(version: str) -> int:
    if not TARGET.exists():
        print(f"Target file not found: {TARGET}")
        return 1

    content = TARGET.read_text()

    has_stop_when_signal = "await service.stop_when_signal()" in content
    has_event_wait = "await asyncio.Event().wait()" in content

    if version == "buggy":
        if has_stop_when_signal and not has_event_wait:
            return 0
        else:
            return 1
    elif version in ["fixed", "patched"]:
        if has_stop_when_signal and has_event_wait:
            return 0
        else:
            return 1
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