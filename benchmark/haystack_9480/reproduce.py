import json
import multiprocessing
import time
import sys

from haystack.components.tools import ToolInvoker
from haystack.dataclasses import ToolCall, ChatMessage
from haystack.tools import tool
from haystack_integrations.tools.mcp import MCPToolset, SSEServerInfo

def start_mcp_server():
    from mcp.server import FastMCP
    mcp = FastMCP("Demo")

    @mcp.tool()
    def get_weather() -> str:
        '''get weather'''
        return json.dumps({"today": "sunny", "tomorrow": "sunny"})

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
    if result_standard != result_mcp:
        print("\nSUCCESS: The bug is reproduced.")
        print("The MCPToolset result is different from the standard tool result.")
        sys.exit(1)
    else:
        print("\nFAILURE: The bug was not reproduced.")
        print("The MCPToolset result was the same as the standard tool result.")
        sys.exit(0)

if __name__ == "__main__":
    mcp_process = multiprocessing.Process(target=start_mcp_server)
    mcp_process.start()

    print("Waiting for MCP server to start...")
    time.sleep(3)

    try:
        run_demo_and_verify()
    except Exception as e:
        print(f"\nAn unexpected error occurred during the demo run: {e}")
    finally:
        print("Shutting down MCP server...")
        mcp_process.terminate()
        mcp_process.join()
