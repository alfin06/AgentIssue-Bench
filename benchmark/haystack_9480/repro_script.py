import json
import multiprocessing
import time
import sys

from haystack.components.tools import ToolInvoker
from haystack.dataclasses import ToolCall, ChatMessage
from haystack.tools import tool
# It's possible the import path changed in newer versions, but we'll try this first.
# If this fails, we may need to adjust the Dockerfile to install a specific version.
from haystack_integrations.tools.mcp import MCPToolset, SSEServerInfo

# This needs to be a top-level function for multiprocessing to pickle it.
def start_mcp_server():
    # mcp is a heavy import, so we do it inside the function
    from mcp.server import FastMCP
    mcp = FastMCP("Demo")

    @mcp.tool()
    def get_weather() -> str:
        '''get weather'''
        return json.dumps({"today": "sunny", "tomorrow": "sunny"})

    # This will block until the process is terminated
    mcp.run(transport="sse")

def run_demo_and_verify():
    """
    This function contains the core logic for invoking the tools and verifying the bug.
    """
    @tool
    def get_weather() -> str:
        '''get weather'''
        return json.dumps({"today": "sunny", "tomorrow": "sunny"})

    mcptoolset = MCPToolset(SSEServerInfo(base_url="http://localhost:8000"))

    tool_call = ToolCall(tool_name="get_weather", arguments={})
    message = ChatMessage.from_assistant(tool_calls=[tool_call])

    # --- Invoke the standard tool ---
    invoker_standard = ToolInvoker(tools=[get_weather])
    result_standard = invoker_standard.run(messages=[message])['tool_messages'][0].tool_call_result.result

    # --- Invoke the MCP tool ---
    invoker_mcp = ToolInvoker(tools=mcptoolset)
    result_mcp = invoker_mcp.run(messages=[message])['tool_messages'][0].tool_call_result.result

    print("--- Verification ---")
    print(f"Standard Tool Result: {result_standard}")
    print(f"MCP Toolset Result  : {result_mcp}")

    # --- Verification Logic ---
    # The bug is that the MCP result is a string representation of a complex object,
    # not the clean JSON string returned by the standard tool.
    if result_standard != result_mcp:
        print("\nSUCCESS: The bug is reproduced.")
        print("The MCPToolset result is different from the standard tool result.")
        # Exit with 1 to signal success to the test runner
        sys.exit(1)
    else:
        print("\nFAILURE: The bug was not reproduced.")
        print("The MCPToolset result was the same as the standard tool result.")
        sys.exit(0)

if __name__ == "__main__":
    # Start MCP server in a separate process
    mcp_process = multiprocessing.Process(target=start_mcp_server)
    mcp_process.start()

    # Give the server a moment to start up
    print("Waiting for MCP server to start...")
    time.sleep(3)

    try:
        # Run the demo script which now contains the verification logic
        run_demo_and_verify()
    except Exception as e:
        print(f"\nAn unexpected error occurred during the demo run: {e}")
    finally:
        # Terminate the MCP server process
        print("Shutting down MCP server...")
        mcp_process.terminate()
        mcp_process.join()
