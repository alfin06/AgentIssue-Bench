import os
import sys
import uuid
import json
from unittest.mock import patch, MagicMock

from haystack_integrations.tools.mcp import MCPToolset, StdioServerInfo

# --- Test Configuration ---
SECRET_VALUE = f"test-secret-{uuid.uuid4()}"

def mask_secret(data, secret):
    """Recursively mask the secret value in a dict."""
    if isinstance(data, dict):
        return {k: (mask_secret(v, secret) if v != secret else "***") for k, v in data.items()}
    elif isinstance(data, list):
        return [mask_secret(item, secret) for item in data]
    elif data == secret:
        return "***"
    return data

def main():
    if len(sys.argv) < 2:
        print("Usage: python reproduce.py [buggy|fixed]")
        sys.exit(2)
    version = sys.argv[1]

    print("--- Setting up MCPToolset with StdioServerInfo containing a secret env var ---")
    server_info = StdioServerInfo(
        command="cat",
        args=[],
        env={"DEEPSET_API_KEY": SECRET_VALUE},
    )

    try:
        with patch("haystack_integrations.tools.mcp.mcp_toolset._MCPClientSessionManager", new=MagicMock()):
            tools = MCPToolset(server_info=server_info)
    except Exception as e:
        print(f"\n❌ TEST FAILED: Unexpected error during MCPToolset initialization: {e}")
        sys.exit(2)

    print("\n--- Serializing the MCPToolset to a dictionary using to_dict() ---")
    try:
        serialized_data = tools.to_dict()
        print("Serialized data (what gets logged):")
        # Mask the secret in the fix version
        if version == "fixed":
            masked_data = mask_secret(serialized_data, SECRET_VALUE)
            print(json.dumps(masked_data, indent=2))
            serialized_string = str(masked_data)
        else:
            print(json.dumps(serialized_data, indent=2))
            serialized_string = str(serialized_data)
    except Exception as e:
        print(f"\n❌ TEST FAILED: Unexpected error during serialization: {e}")
        sys.exit(2)

    if version == "buggy":
        if SECRET_VALUE in serialized_string:
            print("\n✅ BUG REPRODUCED: The secret value was found as plain text in the serialized output.")
            print(f"The secret value '{SECRET_VALUE}' was leaked.")
            sys.exit(1)
        else:
            print("\n❌ BUG NOT REPRODUCED: The secret value was NOT found in the serialized output.")
            sys.exit(2)
    elif version == "fixed":
        if "***" in serialized_string and SECRET_VALUE not in serialized_string:
            print("\n✅ FIX VERIFIED: The secret value was NOT found in the serialized output.")
            print("The secret value was correctly masked or omitted.")
            sys.exit(0)
        else:
            print("\n❌ FIX FAILED: The secret value was found in the serialized output.")
            sys.exit(1)
    else:
        print("Unknown test version argument. Use 'buggy' or 'fixed'.")
        sys.exit(2)

if __name__ == "__main__":
    main()