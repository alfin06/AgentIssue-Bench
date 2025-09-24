import os
import sys
from unittest.mock import MagicMock, patch

# --- Test Setup ---
try:
    from agixt.Agent import Agent
    from agixt.Chain import Chain
except ImportError as e:
    print(f"FATAL: Could not import the necessary module. Check the installation. Error: {e}")
    sys.exit(1)

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine('sqlite:///:memory:')

Session = sessionmaker(bind=engine)

patch_target = "agixt.db.get_session"

print("--- Setting up a test agent with both a standard command and a chain. ---")

# --- Verification Logic ---
try:
    with patch(patch_target, return_value=Session()):
        chain = Chain(name="my_test_chain")
        chain.add_chain("Test Chain")
        print("--- Dummy chain 'my_test_chain' created. ---")

        agent_name = "TestAgent"
        agent = Agent(agent_name)
        
        agent.setup_commands() 
        print(f"--- Agent '{agent_name}' initialized. ---")

        agent_config = {
            "commands": {
                "Standard Command": True,
                "my_test_chain": True,
            }
        }
        
        agent.update_agent_config(agent_config, "commands")
        print("--- Agent configuration saved. It should include 'Standard Command' and 'my_test_chain'. ---")
        
        reloaded_config = agent.get_agent_config()
        enabled_commands = [cmd for cmd, enabled in reloaded_config["commands"].items() if enabled]
        
        print("\n--- Reloaded agent's enabled commands from the database: ---")
        print(enabled_commands)
        
        print("\n--- Verifying Bug ---")
        if "my_test_chain" in enabled_commands:
            print("FAILURE: The bug was NOT reproduced. The chain command was saved correctly.")
            sys.exit(0)
        else:
            print("SUCCESS: The bug is reproduced.")
            print("The 'my_test_chain' command was NOT found in the reloaded configuration.")
            sys.exit(1)
            
except Exception as e:
    print(f"\nFAILURE: An unexpected error occurred: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(0)
