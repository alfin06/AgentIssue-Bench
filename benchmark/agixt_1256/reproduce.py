# reproduce.py

# Simulated command registry
COMMANDS = {}

def register_command(name, func, command_type="regular"):
    """Mock function to register a command."""
    COMMANDS[name] = {
        "function": func,
        "type": command_type
    }

# Simulate regular command
def say_hello():
    return "Hello!"

register_command("say_hello", say_hello)

# Simulate loading a chain command
# In AGiXT, chain commands should also get registered
def fake_chain_loader():
    # Simulate a command-like structure from a chain
    def chain_cmd():
        return "This is a chain command."
    
    # ❌ Intentionally forget to register it as a regular command
    return chain_cmd  # It's returned but not registered!

# Simulate loading chains
chain_func = fake_chain_loader()

# 🔍 Check registered commands
print("\n=== Registered Commands ===")
for name, meta in COMMANDS.items():
    print(f"{name} ({meta['type']})")

# ✅ Expected: say_hello
# ❌ Missing: chain_cmd should be here if properly registered

# Demonstrate the chain command works but is not registered
print("\nChain command output (manually invoked):", chain_func())

# 🔥 Simulate bug
if "chain_cmd" not in COMMANDS:
    print("\n❌  BUG: chain command was not registered!")
else:
    print("\n✅ chain command registered.")
