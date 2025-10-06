import sys
import asyncio
import os

def run_buggy_test():
    try:
        from autogen_ext.runtimes.grpc._worker_runtime_host import GrpcWorkerAgentRuntimeHost
        host = GrpcWorkerAgentRuntimeHost(address="0.0.0.0:50051")
        host.start()  # Should fail in buggy version
        print("❌ No error triggered (bug not reproduced)")
        return 1
    except RuntimeError as e:
        if "no running event loop" in str(e):
            print("✅ Bug reproduced: RuntimeError - no running event loop")
            return 0
        else:
            print(f"❌ Unexpected RuntimeError: {e}")
            return 1
    except Exception as e:
        print(f"❌ Unexpected exception: {e}")
        return 1

async def run_fixed_async():
    try:
        from autogen_ext.runtimes.grpc._worker_runtime_host import GrpcWorkerAgentRuntimeHost
        host = GrpcWorkerAgentRuntimeHost(address="0.0.0.0:50051")
        print(os.name)
        host.start()  # Should succeed in fixed version

        # Mimic the fixed sample usage, but with a timeout to avoid hanging
        try:
            if os.name == "nt":
                # On Windows, wait for a new event with timeout
                try:
                    await asyncio.wait_for(asyncio.Event().wait(), timeout=3)
                except asyncio.TimeoutError:
                    print("Timed out waiting for event (Windows)")
            else:
                # On Unix, try to call stop_when_signal if available, else wait with timeout
                if hasattr(host, "stop_when_signal"):
                    try:
                        await asyncio.wait_for(host.stop_when_signal(), timeout=3)
                    except asyncio.TimeoutError:
                        print("Timed out waiting for signal (Unix)")
                else:
                    try:
                        await asyncio.wait_for(asyncio.Event().wait(), timeout=3)
                    except asyncio.TimeoutError:
                        print("Timed out waiting for event (Unix)")
        except KeyboardInterrupt:
            print("Stopping service...")
        finally:
            if hasattr(host, "stop"):
                try:
                    await host.stop()
                except Exception as e:
                    print(f"Host stop error: {e}")
        print("✅ Fixed: host started and waited without event loop error")
        return 0
    except RuntimeError as e:
        if "no running event loop" in str(e):
            print("❌ Bug still present in fixed version")
            return 1
        else:
            print(f"❌ Unexpected RuntimeError: {e}")
            return 1
    except Exception as e:
        print(f"❌ Unexpected exception: {e}")
        return 1

def run_fixed_test():
    try:
        asyncio.run(run_fixed_async())
    except Exception as e:
        print(f"❌ Unexpected exception in asyncio.run: {e}")
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