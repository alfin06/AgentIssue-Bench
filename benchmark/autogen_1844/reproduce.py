from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntimeHost

# the original code
def main():
    host = GrpcWorkerAgentRuntimeHost(address="0.0.0.0:50051")
    host.start()  # Start a host service in the background.

if __name__ == "__main__":
    main()

# the repaired code 
async def main():
    host = GrpcWorkerAgentRuntimeHost(address="0.0.0.0:50051")
    host.start()  # Start a host service in the background.

    try:
        print("Service is running. Press Ctrl+C to stop.")
        # Wait indefinitely (or you can use another condition to stop the service).
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        print("Stopping service...")
    finally:
        await host.stop()
        print("Service stopped.")