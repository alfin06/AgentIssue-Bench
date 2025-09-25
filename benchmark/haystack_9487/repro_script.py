import os
from unittest.mock import patch, MagicMock

# The bug is in how haystack-integrations serializes this specific tool
from haystack_integrations.tools.mcp import MCPToolset, StdioServerInfo

# --- Test Configuration ---

# This is the sensitive value we expect to be masked, not logged.
SECRET_VALUE = "this-is-a-very-secret-api-key"

print("--- Setting up MCPToolset with StdioServerInfo containing a secret env var ---")

# 1. Define the StdioServerInfo object. The command doesn't matter as much now
#    since we will be mocking the process that uses it.
server_info = StdioServerInfo(
    command="cat",
    args=[],
    env={"DEEPSET_API_KEY": SECRET_VALUE},
)

# 2. Create the MCPToolset while mocking its internal session manager.
#    This is the key to preventing the MCPConnectionError. By replacing
#    _MCPClientSessionManager with a mock, we stop the tool from trying
#    to start and connect to a real background process during initialization.
try:
    with patch("haystack_integrations.tools.mcp.mcp_toolset._MCPClientSessionManager", new=MagicMock()):
        tools = MCPToolset(server_info=server_info)
except Exception as e:
    print(f"\nFAILURE: The script failed unexpectedly during MCPToolset initialization: {e}")
    exit(0)

# --- Verification Logic ---

print("\n--- Serializing the MCPToolset to a dictionary using to_dict() ---")
# The to_dict() method is what Haystack uses internally for serialization and logging.
try:
    serialized_data = tools.to_dict()
    # For debugging, we can print the serialized data. In a real scenario, this
    # is what would be sent to a logging service like Langfuse.
    import json
    print("Serialized data (what gets logged):")
    print(json.dumps(serialized_data, indent=2))

except Exception as e:
    print(f"\nFAILURE: The script failed unexpectedly during serialization: {e}")
    exit(0)


# 3. Check for the secret in the serialized data.
# We convert the dictionary to a string to do a simple search.
serialized_string = str(serialized_data)

if SECRET_VALUE in serialized_string:
    # If the plain text secret is found, the bug is reproduced.
    print("\nSUCCESS: The bug is reproduced.")
    print(f"The secret value '{SECRET_VALUE}' was found as plain text in the serialized output.")
    # Exit with 1 to signal to the test runner that the bug was found.
    exit(1)
else:
    # If the secret is not found, it was correctly masked, and the bug is not present.
    print("\nFAILURE: The bug was NOT reproduced.")
    print("The secret value was correctly masked in the serialized output.")
    exit(0)
