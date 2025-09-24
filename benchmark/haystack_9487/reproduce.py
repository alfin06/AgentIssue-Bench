import os
import uuid
from unittest.mock import patch, MagicMock

from haystack_integrations.tools.mcp import MCPToolset, StdioServerInfo

# --- Test Configuration ---

SECRET_VALUE = f"test-secret-{uuid.uuid4()}"

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
    print(f"\nFAILURE: The script failed unexpectedly during MCPToolset initialization: {e}")
    exit(0)

# --- Verification Logic ---
print("\n--- Serializing the MCPToolset to a dictionary using to_dict() ---")
try:
    serialized_data = tools.to_dict()
    import json
    print("Serialized data (what gets logged):")
    print(json.dumps(serialized_data, indent=2))

except Exception as e:
    print(f"\nFAILURE: The script failed unexpectedly during serialization: {e}")
    exit(0)


serialized_string = str(serialized_data)

if SECRET_VALUE in serialized_string:
    print("\nSUCCESS: The bug is reproduced.")
    print(f"The secret value '{SECRET_VALUE}' was found as plain text in the serialized output.")
    exit(1)
else:
    print("\nFAILURE: The bug was NOT reproduced.")
    print("The secret value was correctly masked in the serialized output.")
    exit(0)
