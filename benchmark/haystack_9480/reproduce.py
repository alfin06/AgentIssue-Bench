import json
import multiprocessing
import time
import sys
from unittest.mock import patch

import haystack.tools
if not hasattr(haystack.tools, "Toolset"):
    class Toolset:
        pass
    haystack.tools.Toolset = Toolset

from haystack.components.tools import ToolInvoker
from haystack.dataclasses import ToolCall, ChatMessage
from haystack.tools import tool, Toolset
from haystack_integrations.tools.mcp import MCPToolset, SSEServerInfo

def start_mcp_server():
    # Import inside the function to avoid issues with multiprocessing pickling
    from mcp.server import FastMCP
    mcp = FastMCP("Demo")

    @mcp.tool()
    def get_weather() -> str:
        '''get weather'''
        return json.dumps({"today": "sunny", "tomorrow": "sunny"})

    mcp.run(transport="sse")

def test_mcp_tool_result_bug(version: str) -> int:
    """
    Failure-triggering test for Haystack issue #9480:
    MCPToolset should return the same JSON string as a standard tool, but instead returns
    a string representation of a complex object.
    """
    print(f"--- Running test for '{version}' version ---")

    @tool
    def get_weather() -> str:
        '''get weather'''
        return json.dumps({"today": "sunny", "tomorrow": "sunny"})

    mcptoolset = MCPToolset(SSEServerInfo(base_url="http://127.0.0.1:8000"))

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
        if version == "buggy":
            print("\n✅ BUG REPRODUCED: The MCPToolset result is different from the standard tool result (bug present).")
            return 1
        else:
            print("\n❌ FIX NOT VERIFIED: The MCPToolset result is still different from the standard tool result (should be fixed).")
            return 2
    else:
        if version == "fixed":
            print("\n✅ FIX VERIFIED: The MCPToolset result matches the standard tool result (bug fixed).")
            return 0
        else:
            print("\n❌ BUG NOT REPRODUCED: The MCPToolset result matches the standard tool result (should be buggy).")
            return 2

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python reproduce.py [buggy|fixed]", file=sys.stderr)
        sys.exit(2)
    version_arg = sys.argv[1]
    if version_arg not in ["buggy", "fixed"]:
        print(f"Invalid argument: '{version_arg}'. Please use 'buggy' or 'fixed'.", file=sys.stderr)
        sys.exit(2)

    # Start MCP server in a separate process
    mcp_process = multiprocessing.Process(target=start_mcp_server)
    mcp_process.start()

    # Give the server a moment to start up
    print("Waiting for MCP server to start...")
    time.sleep(3)

    try:
        exit_code = test_mcp_tool_result_bug(version_arg)
        sys.exit(exit_code)
    except Exception as e:
        print(f"\n❌ TEST FAILED: Unexpected error: {type(e).__name__}: {e}")
        sys.exit(2)
    finally:
        print("Shutting down MCP server...")
        mcp_process.terminate()
        mcp_process.join()